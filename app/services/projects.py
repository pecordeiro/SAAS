"""Casos de uso de projetos. Toda consulta passa por tenancy (company_id da sessão)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select, update

from app.extensions import db
from app.models import PROJECT_ACTIVE, PROJECT_DONE, Activity, Company, Project, ProgressEntry, Stage
from app.services import audit, calc, entitlements, events
from app.services.holidays import holidays_for
from app.tenancy import current_company_id, scoped


class ProgressError(Exception):
    """Erro de validação ao registrar peças (mensagem pronta para a tela)."""


class ConflictError(ProgressError):
    """A atividade mudou desde que a tela foi aberta (controle otimista)."""


class EditError(Exception):
    """Edição inválida (mensagem pronta para a tela)."""


@dataclass
class NewActivity:
    name: str
    ideal_minutes: Decimal
    units_done: int = 0  # só a importação traz peças já concluídas
    archived: bool = False  # só a importação (round-trip da exportação)


@dataclass
class NewStage:
    name: str
    activities: list[NewActivity] = field(default_factory=list)
    archived: bool = False


def _now() -> datetime:
    return datetime.now(timezone.utc)


def active_stages(project: Project) -> list[Stage]:
    return [s for s in project.stages if s.archived_at is None]


def active_activities(stage: Stage) -> list[Activity]:
    return [a for a in stage.activities if a.archived_at is None]


def create_project(
    company: Company,
    *,
    name: str,
    quantity: int,
    start_date: date | None,
    due_date: date | None,
    people: int,
    hours_per_day: Decimal,
    stages: list[NewStage],
    template_version_id: uuid.UUID | None = None,
    source: str = "manual",
    check_limits: bool = True,
) -> Project:
    """Cria o projeto com as etapas dadas. Vindas de um modelo (``template_version_id``),
    as etapas já são a cópia (snapshot) da versão: ver ``services.templates``.

    Confere o limite de projetos do plano (``PlanLimitError`` → 402) e grava
    ``project.created`` na mesma transação."""
    if check_limits:
        entitlements.check_can_create_project(company)
    project = Project(
        company_id=company.id,
        template_version_id=template_version_id,
        name=name,
        quantity=quantity,
        start_date=start_date,
        due_date=due_date,
        people=people,
        hours_per_day=hours_per_day,
    )
    db.session.add(project)
    db.session.flush()
    for s_pos, new_stage in enumerate(stages):
        stage = add_stage(project, new_stage.name, new_stage.activities, position=s_pos)
        if new_stage.archived:
            stage.archived_at = _now()
    db.session.flush()
    db.session.refresh(project)
    events.emit(
        company.id,
        events.PROJECT_CREATED,
        {"project_id": project.id, "quantity": quantity, "template_version_id": template_version_id, "source": source},
    )
    return project


def add_stage(project: Project, name: str, activities: list[NewActivity], position: int | None = None) -> Stage:
    if position is None:
        position = max((s.position for s in project.stages), default=-1) + 1
    stage = Stage(company_id=project.company_id, project_id=project.id, name=name, position=position)
    db.session.add(stage)
    db.session.flush()
    for a_pos, new_activity in enumerate(activities):
        add_activity(stage, new_activity, position=a_pos)
    return stage


def add_activity(stage: Stage, new_activity: NewActivity, position: int | None = None) -> Activity:
    if position is None:
        position = max((a.position for a in stage.activities), default=-1) + 1
    activity = Activity(
        company_id=stage.company_id,
        stage_id=stage.id,
        name=new_activity.name,
        ideal_minutes=new_activity.ideal_minutes,
        position=position,
        units_done=new_activity.units_done,
        archived_at=_now() if new_activity.archived else None,
    )
    db.session.add(activity)
    db.session.flush()
    return activity


def register_progress(activity: Activity, delta: int, expected_version: int | None, user_id: uuid.UUID) -> ProgressEntry:
    """Soma `delta` peças à atividade, grava o histórico e incrementa a versão.

    Regras: delta ≥ 1; peças concluídas nunca passam das previstas (quantidade do projeto).
    `expected_version` diferente da atual → ConflictError (409). Na mesma transação grava
    ``activity.progress_updated`` (e ``stage.completed``/``project.completed`` na virada).
    """
    if delta < 1:
        raise ProgressError("Informe pelo menos 1 peça.")
    project = activity.stage.project
    previstas = project.quantity
    maximo = max(0, previstas - activity.units_done)
    if expected_version is not None and expected_version != activity.version:
        raise ConflictError("Esta atividade foi atualizada por outra pessoa. Confira os números e tente de novo.")
    if delta > maximo:
        raise ProgressError(f"Máximo {maximo} peça(s) nesta atividade.")
    stage_before = _stage_done(activity.stage)
    project_before = _project_done(project)
    # UPDATE condicional: só grava se ninguém mudou a linha entre a leitura e a escrita.
    result = db.session.execute(
        update(Activity)
        .where(
            Activity.id == activity.id,
            Activity.company_id == activity.company_id,
            Activity.version == activity.version,
            Activity.units_done + delta <= previstas,
        )
        .values(units_done=Activity.units_done + delta, version=Activity.version + 1)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.session.rollback()
        raise ConflictError("Esta atividade foi atualizada por outra pessoa. Confira os números e tente de novo.")
    entry = ProgressEntry(company_id=activity.company_id, activity_id=activity.id, user_id=user_id, delta=delta)
    db.session.add(entry)
    db.session.flush()
    db.session.refresh(activity)
    _after_progress(activity, entry, stage_before, project_before)
    return entry


def _stage_done(stage: Stage) -> bool:
    etapa = calc.Etapa(
        atividades=tuple(
            calc.Atividade(ideal_min=float(a.ideal_minutes or 0), pecas=a.units_done) for a in active_activities(stage)
        ),
        previstas=stage.project.quantity,
    )
    return calc.resumo_etapa(etapa).status == calc.STATUS_CONCLUIDA


def _project_done(project: Project) -> bool:
    stages = active_stages(project)
    return bool(stages) and all(_stage_done(s) for s in stages)


def _after_progress(activity: Activity, entry: ProgressEntry, stage_before: bool, project_before: bool) -> None:
    """Eventos da mudança (mesma transação) e status do projeto."""
    stage = activity.stage
    project = stage.project
    events.emit(
        activity.company_id,
        events.ACTIVITY_PROGRESS_UPDATED,
        {
            "project_id": project.id,
            "stage_id": stage.id,
            "activity_id": activity.id,
            "entry_id": entry.id,
            "delta": entry.delta,
            "units_done": activity.units_done,
            "quantity": project.quantity,
        },
    )
    if not stage_before and _stage_done(stage):
        events.emit(activity.company_id, events.STAGE_COMPLETED, {"project_id": project.id, "stage_id": stage.id})
    project_after = _project_done(project)
    if not project_before and project_after:
        events.emit(activity.company_id, events.PROJECT_COMPLETED, {"project_id": project.id})
    _sync_status(project, project_after)


def _sync_status(project: Project, done: bool | None = None) -> None:
    done = _project_done(project) if done is None else done
    if not done and project.status == PROJECT_DONE:
        # Voltar de concluído para ativo ocupa uma vaga do plano: sem esta checagem,
        # concluir e depois desfazer contornaria max_projects.
        entitlements.check_can_create_project(db.session.get(Company, project.company_id))
    project.status = PROJECT_DONE if done else PROJECT_ACTIVE


# ---------------------------------------------------------------- desfazer (D13)


def undo_progress(entry: ProgressEntry, user_id: uuid.UUID) -> ProgressEntry:
    """Desfaz um registro (supervisor+ na rota) com lançamento COMPENSATÓRIO: delta
    negativo e ``reverts_entry_id``. O registro original fica intacto (append-only).

    Não desfaz um desfazer nem o mesmo registro duas vezes (UNIQUE no banco também)."""
    if entry.reverts_entry_id is not None or entry.delta < 0:
        raise ProgressError("Este lançamento já é um desfazer.")
    if is_undone(entry):
        raise ProgressError("Este registro já foi desfeito.")
    activity = entry.activity
    project = activity.stage.project
    result = db.session.execute(
        update(Activity)
        .where(
            Activity.id == activity.id,
            Activity.company_id == activity.company_id,
            Activity.version == activity.version,
            Activity.units_done - entry.delta >= 0,
        )
        .values(units_done=Activity.units_done - entry.delta, version=Activity.version + 1)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:  # pragma: no cover - corrida rara entre duas abas
        db.session.rollback()
        raise ConflictError("A atividade mudou enquanto você desfazia. Confira e tente de novo.")
    reversal = ProgressEntry(
        company_id=entry.company_id,
        activity_id=activity.id,
        user_id=user_id,
        delta=-entry.delta,
        reverts_entry_id=entry.id,
    )
    db.session.add(reversal)
    db.session.flush()
    db.session.refresh(activity)
    # Desfazer nunca conclui etapa nem projeto: só o evento de progresso (delta negativo).
    _after_progress(activity, reversal, stage_before=True, project_before=True)
    audit.record(
        audit.PROGRESS_UNDONE,
        company_id=entry.company_id,
        actor_user_id=user_id,
        object_type="project",
        object_id=project.id,
        details={
            "entry_id": str(entry.id),
            "activity": activity.name,
            "delta": entry.delta,
            "units_done": activity.units_done,
        },
    )
    return reversal


def is_undone(entry: ProgressEntry) -> bool:
    return (
        db.session.execute(
            select(ProgressEntry.id).where(
                ProgressEntry.company_id == entry.company_id, ProgressEntry.reverts_entry_id == entry.id
            )
        ).first()
        is not None
    )


def undone_ids(entries: list[ProgressEntry]) -> set[uuid.UUID]:
    """Ids dos registros (da lista) que já foram desfeitos."""
    if not entries:
        return set()
    return set(
        db.session.execute(
            select(ProgressEntry.reverts_entry_id).where(
                ProgressEntry.company_id == entries[0].company_id,
                ProgressEntry.reverts_entry_id.in_([e.id for e in entries]),
            )
        ).scalars()
    )


# ---------------------------------------------------------------- edição (Fase 4)


def update_project(
    project: Project,
    *,
    name: str,
    quantity: int,
    start_date: date | None,
    due_date: date | None,
    people: int,
    hours_per_day: Decimal,
    user_id: uuid.UUID | None,
) -> None:
    """Edita os dados do projeto. A quantidade não pode ficar abaixo das peças já
    registradas em alguma atividade."""
    most = max((a.units_done for s in project.stages for a in s.activities), default=0)
    if quantity < most:
        raise EditError(f"Já há {most} peças registradas numa atividade: a quantidade não pode ser menor.")
    if due_date and start_date and due_date < start_date:
        raise EditError("O prazo não pode ser antes do início.")
    before = {"name": project.name, "quantity": project.quantity}
    project.name = name
    project.quantity = quantity
    project.start_date = start_date
    project.due_date = due_date
    project.people = people
    project.hours_per_day = hours_per_day
    db.session.flush()
    _sync_status(project)
    audit.record(
        audit.PROJECT_UPDATED,
        company_id=project.company_id,
        actor_user_id=user_id,
        object_type="project",
        object_id=project.id,
        details={"antes": before, "depois": {"name": name, "quantity": quantity}},
    )


def _clean_name(name: str | None, what: str) -> str:
    name = (name or "").strip()
    if not name or len(name) > 160:
        raise EditError(f"Informe o nome da {what} (até 160 caracteres).")
    return name


def rename_stage(stage: Stage, name: str) -> None:
    stage.name = _clean_name(name, "etapa")
    db.session.flush()


def update_activity(activity: Activity, name: str, ideal_minutes: Decimal | None) -> None:
    name = _clean_name(name, "atividade")
    if ideal_minutes is None or ideal_minutes < 0:
        raise EditError("Tempo ideal inválido.")
    activity.name = name
    activity.ideal_minutes = ideal_minutes
    db.session.flush()


def _sorted(items: list) -> list:
    return sorted(items, key=lambda i: (i.position, i.created_at))


def _swap(items: list, obj, direction: int) -> bool:
    """Normaliza posições (0..n) de todos os irmãos e troca ``obj`` com o vizinho ATIVO."""
    for pos, item in enumerate(items):
        item.position = pos
    live = [i for i in items if i.archived_at is None]
    index = live.index(obj)
    other = index + direction
    if other < 0 or other >= len(live):
        db.session.flush()
        return False
    a, b = live[index], live[other]
    a.position, b.position = b.position, a.position
    db.session.flush()
    return True


def move_stage(stage: Stage, direction: int) -> bool:
    moved = _swap(_sorted(stage.project.stages), stage, direction)
    db.session.expire(stage.project, ["stages"])
    return moved


def move_activity(activity: Activity, direction: int) -> bool:
    moved = _swap(_sorted(activity.stage.activities), activity, direction)
    db.session.expire(activity.stage, ["activities"])
    return moved


def reorder_stages(project: Project, ordered_ids: list) -> None:
    """Nova ordem das etapas ativas (lista com todos os ids ativos, sem repetir)."""
    live = active_stages(project)
    wanted = [str(i) for i in ordered_ids]
    if sorted(wanted) != sorted(str(s.id) for s in live):
        raise EditError("A nova ordem precisa conter todas as etapas do projeto.")
    by_id = {str(s.id): s for s in live}
    archived = [s for s in _sorted(project.stages) if s.archived_at is not None]
    for pos, stage in enumerate([by_id[i] for i in wanted] + archived):
        stage.position = pos
    db.session.flush()
    db.session.expire(project, ["stages"])


def archive_stage(stage: Stage, user_id: uuid.UUID | None) -> None:
    stage.archived_at = _now()
    db.session.flush()
    project = stage.project
    db.session.expire(project, ["stages"])
    _sync_status(project)
    audit.record(
        audit.STAGE_ARCHIVED, company_id=stage.company_id, actor_user_id=user_id,
        object_type="project", object_id=project.id, details={"stage": stage.name},
    )


def archive_activity(activity: Activity, user_id: uuid.UUID | None) -> None:
    activity.archived_at = _now()
    db.session.flush()
    stage = activity.stage
    db.session.expire(stage, ["activities"])
    _sync_status(stage.project)
    audit.record(
        audit.ACTIVITY_ARCHIVED, company_id=activity.company_id, actor_user_id=user_id,
        object_type="project", object_id=stage.project_id,
        details={"stage": stage.name, "activity": activity.name},
    )


def archive_project(project: Project, user_id: uuid.UUID | None) -> None:
    project.archived_at = _now()
    db.session.flush()
    audit.record(
        audit.PROJECT_ARCHIVED, company_id=project.company_id, actor_user_id=user_id,
        object_type="project", object_id=project.id, details={"name": project.name},
    )


def duplicate_project(project: Project, user_id: uuid.UUID | None, name: str | None = None) -> Project:
    """Mesmas etapas/atividades ativas (e mesma origem de modelo), progresso zero."""
    company = db.session.get(Company, project.company_id)
    stages = [
        NewStage(
            name=s.name,
            activities=[NewActivity(name=a.name, ideal_minutes=a.ideal_minutes) for a in active_activities(s)],
        )
        for s in active_stages(project)
    ]
    copy = create_project(
        company,
        name=(name or f"Cópia de {project.name}")[:160],
        quantity=project.quantity,
        start_date=project.start_date,
        due_date=project.due_date,
        people=project.people,
        hours_per_day=project.hours_per_day,
        stages=stages,
        template_version_id=project.template_version_id,
        source="duplicate",
    )
    audit.record(
        audit.PROJECT_DUPLICATED, company_id=project.company_id, actor_user_id=user_id,
        object_type="project", object_id=copy.id, details={"from_project_id": str(project.id)},
    )
    return copy


def record_initial_progress(project: Project, user_id: uuid.UUID | None) -> None:
    """Importação: as peças já concluídas viram 1 registro por atividade no histórico
    (assim a soma do histórico bate com as peças da atividade)."""
    for stage in project.stages:
        for activity in stage.activities:
            if activity.units_done > 0:
                db.session.add(
                    ProgressEntry(
                        company_id=project.company_id, activity_id=activity.id, user_id=user_id, delta=activity.units_done
                    )
                )
    db.session.flush()
    _sync_status(project)


# ---------------------------------------------------------------- leitura


def to_calc(project: Project) -> list[calc.Etapa]:
    return [
        calc.Etapa(
            atividades=tuple(
                calc.Atividade(ideal_min=float(a.ideal_minutes or 0), pecas=a.units_done)
                for a in active_activities(stage)
            ),
            previstas=project.quantity,
        )
        for stage in active_stages(project)
    ]


def summary(project: Project) -> calc.ResultadoProjeto:
    return calc.resumo_projeto(
        to_calc(project),
        quantidade=project.quantity,
        pessoas=project.people,
        horas_dia=float(project.hours_per_day),
    )


def company_holidays() -> list[date]:
    """Feriados nacionais (company_id NULL) + os da empresa da sessão."""
    return holidays_for(current_company_id())


def forecast_end(project: Project, result: calc.ResultadoProjeto, company: Company, today: date) -> date | None:
    """Data prevista de término: dias úteis restantes a partir de hoje (ou do início, se futuro)."""
    if result.dias_uteis_restantes is None:
        return None
    inicio = max(today, project.start_date) if project.start_date else today
    return calc.prazo_em_data(inicio, result.dias_uteis_restantes, holidays_for(company.id), company.workdays())


def delay_workdays(project: Project, forecast: date | None, company: Company) -> int:
    """Atraso previsto em dias úteis (0 se não há prazo, previsão ou atraso)."""
    if not forecast or not project.due_date:
        return 0
    return calc.dias_uteis_entre(project.due_date, forecast, holidays_for(company.id), company.workdays())


def list_projects() -> list[Project]:
    return list(
        db.session.execute(
            scoped(Project).where(Project.archived_at.is_(None)).order_by(Project.created_at.desc())
        ).scalars()
    )


def history(project: Project, limit: int = 200) -> list[ProgressEntry]:
    return list(
        db.session.execute(
            scoped(ProgressEntry)
            .join(Activity, Activity.id == ProgressEntry.activity_id)
            .join(Stage, Stage.id == Activity.stage_id)
            .where(Stage.project_id == project.id, Activity.company_id == project.company_id)
            .order_by(ProgressEntry.at.desc())
            .limit(limit)
        ).scalars()
    )
