"""Casos de uso de projetos. Toda consulta passa por tenancy (company_id da sessão)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import (
    PROGRESS_DETAILED,
    PROGRESS_MODES,
    PROGRESS_SIMPLE,
    PROJECT_ACTIVE,
    PROJECT_DONE,
    Activity,
    Company,
    Project,
    ProgressEntry,
    Stage,
)
from app.services import audit, calc, entitlements, events
from app.services.holidays import holidays_for
from app.tenancy import current_company_id, scoped


class ProgressError(Exception):
    """Erro de validação ao registrar peças (mensagem pronta para a tela)."""


class ConflictError(ProgressError):
    """A atividade mudou desde que a tela foi aberta (controle otimista)."""


class EditError(Exception):
    """Edição inválida (mensagem pronta para a tela)."""


class EditConflict(EditError):
    """Etapa D: o registro mudou desde que a tela foi aberta (``version`` diferente) → 409.

    ``current`` traz o valor ATUAL (para a tela mostrar e pedir confirmação); nada foi gravado."""

    def __init__(self, message: str, current: dict, version: int):
        super().__init__(message)
        self.current = current
        self.version = version


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
    # Etapa G: itens do checklist de inspeção (texto) e se a etapa exige checklist assinado.
    checklist: list[str] = field(default_factory=list)
    checklist_required: bool = False


# R4 — modo simples: a etapa tem UMA atividade interna (nome = nome da etapa). O tempo dela pesa a
# etapa no projeto e dá as horas que faltam; sem tempo informado, vale este padrão.
SIMPLE_DEFAULT_MINUTES = Decimal("60")


def is_simple(project: Project) -> bool:
    return project.progress_mode == PROGRESS_SIMPLE


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
    product: str | None = None,
    progress_mode: str = PROGRESS_DETAILED,
) -> Project:
    """Cria o projeto com as etapas dadas. Vindas de um modelo (``template_version_id``),
    as etapas já são a cópia (snapshot) da versão: ver ``services.templates``.

    Confere o limite de projetos do plano (``PlanLimitError`` → 402) e grava
    ``project.created`` na mesma transação.

    R4: ``progress_mode`` ``"simples"`` exige no máximo uma atividade por etapa; etapa sem
    atividade ganha a atividade interna (nome da etapa, ``SIMPLE_DEFAULT_MINUTES``)."""
    if progress_mode not in PROGRESS_MODES:
        raise ValueError(f"modo de progresso inválido: {progress_mode!r}")
    if progress_mode == PROGRESS_SIMPLE and any(len(s.activities) > 1 for s in stages):
        raise EditError("No modo simples cada etapa tem só o %: no máximo uma atividade por etapa.")
    if check_limits:
        entitlements.check_can_create_project(company)
    project = Project(
        company_id=company.id,
        template_version_id=template_version_id,
        name=name,
        product=(product or "").strip() or None,
        quantity=quantity,
        start_date=start_date,
        due_date=due_date,
        people=people,
        hours_per_day=hours_per_day,
        progress_mode=progress_mode,
    )
    db.session.add(project)
    db.session.flush()
    for s_pos, new_stage in enumerate(stages):
        stage = add_stage(
            project, new_stage.name, new_stage.activities, position=s_pos,
            checklist=new_stage.checklist, checklist_required=new_stage.checklist_required,
        )
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


def add_stage(
    project: Project,
    name: str,
    activities: list[NewActivity],
    position: int | None = None,
    *,
    checklist: list[str] | tuple = (),
    checklist_required: bool = False,
) -> Stage:
    if position is None:
        position = max((s.position for s in project.stages), default=-1) + 1
    if is_simple(project) and not activities:
        activities = [NewActivity(name=name, ideal_minutes=SIMPLE_DEFAULT_MINUTES)]
    stage = Stage(
        company_id=project.company_id, project_id=project.id, name=name, position=position,
        checklist_required=bool(checklist_required),
    )
    db.session.add(stage)
    db.session.flush()
    for a_pos, new_activity in enumerate(activities):
        add_activity(stage, new_activity, position=a_pos)
    if checklist:
        from app.models import StageChecklistItem

        for i_pos, text in enumerate(checklist):
            db.session.add(StageChecklistItem(company_id=project.company_id, stage_id=stage.id, text=text, position=i_pos))
        db.session.flush()
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


def register_progress(
    activity: Activity,
    delta: int,
    expected_version: int | None,
    user_id: uuid.UUID,
    *,
    unit_id: uuid.UUID | None = None,
) -> ProgressEntry:
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
    entry = ProgressEntry(
        company_id=activity.company_id, activity_id=activity.id, user_id=user_id, delta=delta, unit_id=unit_id
    )
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
    if entry.restore_id is not None:
        # R8: lançamento de restauração só sai junto com a restauração inteira.
        raise ProgressError("Este lançamento é de uma restauração: desfaça a restauração inteira.")
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
        unit_id=entry.unit_id,  # Etapa G: o desfazer fica na mesma unidade
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


# ---------------------------------------------------------------- atribuição (Etapa D)


class AssignError(Exception):
    """Responsável inválido: não é membro ATIVO da empresa da atividade (rota → 404)."""


def _assignable_stmt(company_id: uuid.UUID):
    from app.models import Membership, User

    return (
        select(User)
        .join(Membership, Membership.user_id == User.id)
        .where(
            Membership.company_id == company_id,
            Membership.usable(),  # ativo e, se temporário, no prazo
            Membership.is_support.is_(False),  # acesso de suporte da plataforma não é equipe
            User.active.is_(True),
        )
    )


def assignable_members(company_id: uuid.UUID) -> list:
    """Pessoas que podem ser responsáveis (membros ativos da empresa, sem suporte)."""
    from app.models import User

    return list(db.session.execute(_assignable_stmt(company_id).order_by(User.name)).scalars())


def assign_activity(activity: Activity, assignee_id: uuid.UUID | None, user_id: uuid.UUID | None) -> bool:
    """Define (ou tira, com ``None``) o responsável da atividade. Só membro ATIVO da MESMA
    empresa da atividade; qualquer outro id → ``AssignError``. Audita e, ao atribuir, grava o
    evento interno ``activity.assigned`` (só ids). Devolve se mudou algo."""
    from app.models import User

    if assignee_id is not None:
        member = db.session.execute(
            _assignable_stmt(activity.company_id).where(User.id == assignee_id)
        ).scalar_one_or_none()
        if member is None:
            raise AssignError("Pessoa não encontrada na equipe.")
    previous = activity.assignee_id
    if previous == assignee_id:
        return False
    activity.assignee_id = assignee_id
    db.session.flush()
    stage = activity.stage
    audit.record(
        audit.ACTIVITY_ASSIGNED,
        company_id=activity.company_id,
        actor_user_id=user_id,
        object_type="project",
        object_id=stage.project_id,
        details={
            "stage": stage.name,
            "activity": activity.name,
            "de": str(previous) if previous else None,
            "para": str(assignee_id) if assignee_id else None,
        },
    )
    if assignee_id is not None:
        events.emit(
            activity.company_id,
            events.ACTIVITY_ASSIGNED,
            {
                "project_id": stage.project_id,
                "stage_id": stage.id,
                "activity_id": activity.id,
                "assignee_user_id": assignee_id,
                # Etapa F: quem atribuiu (o e-mail não sai quando a pessoa atribui a si mesma).
                "assigned_by_user_id": user_id,
            },
        )
    return True


def clear_assignments(company_id: uuid.UUID, user_id: uuid.UUID) -> int:
    """Pessoa desativada na empresa deixa de ser responsável pelas atividades dela."""
    result = db.session.execute(
        update(Activity)
        .where(Activity.company_id == company_id, Activity.assignee_id == user_id)
        .values(assignee_id=None)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount or 0


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
    product: str | None = None,
) -> None:
    """Edita os dados do projeto. A quantidade não pode ficar abaixo das peças já
    registradas em alguma atividade."""
    most = max((a.units_done for s in project.stages for a in s.activities), default=0)
    if quantity < most:
        raise EditError(f"Já há {most} peças registradas numa atividade: a quantidade não pode ser menor.")
    if due_date and start_date and due_date < start_date:
        raise EditError("O prazo não pode ser antes do início.")
    from app.services.units import count_units

    units = count_units(project)
    if quantity < units:
        raise EditError(f"O projeto tem {units} números de série cadastrados: a quantidade não pode ser menor.")
    before = {"name": project.name, "quantity": project.quantity}
    project.name = name
    project.product = (product or "").strip() or None
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


def _stage_state(stage: Stage) -> dict:
    return {"name": stage.name}


def _activity_state(activity: Activity) -> dict:
    return {"name": activity.name, "ideal_minutes": activity.ideal_minutes, "units_done": activity.units_done}


def _guarded_update(model, obj, expected_version: int | None, values: dict, state, conflict_message: str) -> None:
    """UPDATE condicional por ``version`` (controle otimista, como no registro de peças).

    ``expected_version`` diferente da atual (ou outra gravação entre a leitura e a escrita)
    → ``EditConflict`` com o valor atual; ``None`` = sem conferência (chamadas internas)."""
    if expected_version is not None and expected_version != obj.version:
        raise EditConflict(conflict_message, state(obj), obj.version)
    result = db.session.execute(
        update(model)
        .where(model.id == obj.id, model.company_id == obj.company_id, model.version == obj.version)
        .values(**values, version=model.version + 1)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:  # pragma: no cover - corrida rara entre duas abas
        db.session.refresh(obj)
        raise EditConflict(conflict_message, state(obj), obj.version)
    db.session.refresh(obj)


STAGE_CONFLICT = "Outra pessoa alterou esta etapa enquanto você editava."
ACTIVITY_CONFLICT = "Esta atividade mudou enquanto você editava."


def rename_stage(stage: Stage, name: str, expected_version: int | None = None, user_id: uuid.UUID | None = None) -> None:
    """Renomeia a etapa. ``expected_version`` velha → ``EditConflict`` (409 na rota)."""
    name = _clean_name(name, "etapa")
    before = stage.name
    _guarded_update(Stage, stage, expected_version, {"name": name}, _stage_state, STAGE_CONFLICT)
    if is_simple(stage.project):
        # Modo simples: a atividade interna acompanha o nome da etapa (exportação e histórico).
        for activity in active_activities(stage):
            activity.name = name
        db.session.flush()
    if before != name:
        audit.record(
            audit.STAGE_RENAMED, company_id=stage.company_id, actor_user_id=user_id,
            object_type="project", object_id=stage.project_id, details={"stage": name, "antes": before},
        )


PART_NOTE_MAX = 140
PART_DATE_MIN = date(2000, 1, 1)
PART_DATE_MAX = date(2100, 12, 31)


def set_waiting_part(
    stage: Stage,
    waiting: bool,
    expected_on: date | None,
    note: str | None,
    expected_version: int | None = None,
    user_id: uuid.UUID | None = None,
) -> None:
    """Etapa F: marca/desmarca “aguardando peça”. SÓ SINALIZA — o registro de peças continua
    livre. Desmarcar limpa previsão e observação. ``expected_version`` velha → ``EditConflict``
    (a versão da etapa é a mesma do renomear). Salvar de novo com a marca conta como
    atualização (zera o lembrete de previsão vencida)."""
    note = (note or "").strip() or None
    if note is not None and len(note) > PART_NOTE_MAX:
        raise EditError(f"A observação da peça tem no máximo {PART_NOTE_MAX} caracteres.")
    if expected_on is not None and not (PART_DATE_MIN <= expected_on <= PART_DATE_MAX):
        raise EditError("Previsão de chegada da peça inválida.")
    if not waiting:
        expected_on, note = None, None
    before = {"aguardando": stage.waiting_part, "previsao": stage.part_expected_on.isoformat() if stage.part_expected_on else None}
    _guarded_update(
        Stage,
        stage,
        expected_version,
        {
            "waiting_part": bool(waiting),
            "part_expected_on": expected_on,
            "part_note": note,
            "part_updated_at": _now() if waiting else None,
        },
        _stage_state,
        STAGE_CONFLICT,
    )
    after = {"aguardando": bool(waiting), "previsao": expected_on.isoformat() if expected_on else None}
    audit.record(
        audit.STAGE_WAITING_PART, company_id=stage.company_id, actor_user_id=user_id,
        object_type="project", object_id=stage.project_id,
        details={"stage": stage.name, "antes": before, "depois": after},
    )


def waiting_part_counts(project_ids) -> dict[uuid.UUID, int]:
    """Etapas ativas marcadas “aguardando peça” por projeto (lista de projetos, uma consulta)."""
    ids = list(project_ids)
    if not ids:
        return {}
    rows = db.session.execute(
        select(Stage.project_id, func.count())
        .where(
            Stage.company_id == current_company_id(),
            Stage.project_id.in_(ids),
            Stage.waiting_part.is_(True),
            Stage.archived_at.is_(None),
        )
        .group_by(Stage.project_id)
    ).all()
    return {pid: n for pid, n in rows}


def update_activity(
    activity: Activity,
    name: str,
    ideal_minutes: Decimal | None,
    expected_version: int | None = None,
    user_id: uuid.UUID | None = None,
) -> None:
    """Edita nome e tempo ideal. ``expected_version`` velha (alguém editou, registrou peças
    ou moveu a atividade) → ``EditConflict`` com o valor atual (409 na rota)."""
    name = _clean_name(name, "atividade")
    if ideal_minutes is None or ideal_minutes < 0:
        raise EditError("Tempo ideal inválido.")
    before = {"name": activity.name, "ideal_minutes": str(activity.ideal_minutes)}
    _guarded_update(
        Activity, activity, expected_version, {"name": name, "ideal_minutes": ideal_minutes},
        _activity_state, ACTIVITY_CONFLICT,
    )
    after = {"name": activity.name, "ideal_minutes": str(activity.ideal_minutes)}
    if before != after:
        audit.record(
            audit.ACTIVITY_UPDATED, company_id=activity.company_id, actor_user_id=user_id,
            object_type="project", object_id=activity.stage.project_id,
            details={"activity": activity.name, "antes": before, "depois": after},
        )


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


class OrderConflict(EditError):
    """A lista enviada não bate com as etapas atuais (alguém incluiu/arquivou) → 409."""


def reorder_stages(project: Project, ordered_ids: list, user_id: uuid.UUID | None = None) -> bool:
    """Nova ordem das etapas ativas (lista com TODOS os ids ativos, sem repetir). O navegador
    só manda a ordem; quem decide é aqui: lista diferente das etapas atuais → ``OrderConflict``.
    Arquivadas ficam no fim. Audita quando a ordem muda. Devolve se mudou."""
    live = active_stages(project)
    wanted = [str(i) for i in ordered_ids]
    if len(wanted) != len(set(wanted)) or sorted(wanted) != sorted(str(s.id) for s in live):
        raise OrderConflict("A lista de etapas mudou desde que a tela foi aberta. Confira a ordem atual e tente de novo.")
    before = [str(s.id) for s in live]
    by_id = {str(s.id): s for s in live}
    archived = [s for s in _sorted(project.stages) if s.archived_at is not None]
    for pos, stage in enumerate([by_id[i] for i in wanted] + archived):
        stage.position = pos
    db.session.flush()
    db.session.expire(project, ["stages"])
    changed = before != wanted
    if changed:
        audit.record(
            audit.STAGES_REORDERED, company_id=project.company_id, actor_user_id=user_id,
            object_type="project", object_id=project.id,
            details={"ordem": [by_id[i].name for i in wanted]},
        )
    return changed


def _renumber(stage: Stage, live_order: list[Activity]) -> None:
    archived = [a for a in _sorted(stage.activities) if a.archived_at is not None and a not in live_order]
    for pos, act in enumerate(live_order + archived):
        act.position = pos


def move_activity_to(
    activity: Activity,
    target: Stage,
    position: int,
    expected_version: int | None,
    user_id: uuid.UUID | None = None,
) -> None:
    """Põe a atividade na etapa ``target`` (mesmo projeto) na posição ``position`` (0 = topo;
    acima do fim vai para o fim). Arrastar e o seletor “Mover para” chegam aqui.

    Regras no servidor: etapa de outro projeto → ``EditError`` (rota → 404); ``version`` velha
    → ``EditConflict`` (409); incrementa a versão, renumera origem e destino, audita e
    recalcula o status do projeto (a etapa de destino pode deixar de estar concluída)."""
    source = activity.stage
    if target.project_id != source.project_id or target.company_id != activity.company_id:
        raise EditError("Etapa de destino inválida.")
    if expected_version is not None and expected_version != activity.version:
        raise EditConflict(ACTIVITY_CONFLICT, _activity_state(activity), activity.version)
    old_index = [a.id for a in active_activities(source)].index(activity.id) if activity.archived_at is None else 0
    _guarded_update(Activity, activity, expected_version, {"stage_id": target.id}, _activity_state, ACTIVITY_CONFLICT)
    db.session.expire(source, ["activities"])
    db.session.expire(target, ["activities"])
    others = [a for a in _sorted(target.activities) if a.archived_at is None and a.id != activity.id]
    pos = max(0, min(position, len(others)))
    others.insert(pos, activity)
    _renumber(target, others)
    if source.id != target.id:
        _renumber(source, [a for a in _sorted(source.activities) if a.archived_at is None])
    db.session.flush()
    db.session.expire(source, ["activities"])
    db.session.expire(target, ["activities"])
    project = target.project
    db.session.expire(project, ["stages"])
    _sync_status(project)
    if source.id != target.id or old_index != pos:
        audit.record(
            audit.ACTIVITY_MOVED, company_id=activity.company_id, actor_user_id=user_id,
            object_type="project", object_id=project.id,
            details={"activity": activity.name, "stage": target.name, "de": source.name, "posicao": pos + 1},
        )


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


# ---------------------------------------------------------------- R3: desfazer exclusão


def unarchive_stage(stage: Stage, user_id: uuid.UUID | None) -> None:
    """Desfaz a exclusão (arquivamento) da etapa: ela volta, no fim da lista, com as atividades
    que tinha quando foi excluída. Audita ``stage.unarchived``."""
    if stage.archived_at is None:
        raise EditError("Esta etapa não está excluída.")
    project = stage.project
    stage.archived_at = None
    stage.position = max((s.position for s in project.stages if s.id != stage.id), default=-1) + 1
    db.session.flush()
    db.session.expire(project, ["stages"])
    _sync_status(project)
    audit.record(
        audit.STAGE_UNARCHIVED, company_id=stage.company_id, actor_user_id=user_id,
        object_type="project", object_id=project.id, details={"stage": stage.name},
    )


def unarchive_activity(activity: Activity, user_id: uuid.UUID | None) -> None:
    """Desfaz a exclusão da atividade (volta no fim da etapa, com as peças que tinha).
    Etapa excluída → traga a etapa antes; projeto no modo simples já com atividade → recusa."""
    if activity.archived_at is None:
        raise EditError("Esta atividade não está excluída.")
    stage = activity.stage
    if stage.archived_at is not None:
        raise EditError("A etapa desta atividade também foi excluída: desfaça a exclusão da etapa primeiro.")
    if is_simple(stage.project) and active_activities(stage):
        raise EditError("No modo simples a etapa tem só o %: não dá para trazer uma segunda atividade.")
    activity.archived_at = None
    activity.position = max((a.position for a in stage.activities if a.id != activity.id), default=-1) + 1
    db.session.flush()
    db.session.expire(stage, ["activities"])
    _sync_status(stage.project)
    audit.record(
        audit.ACTIVITY_UNARCHIVED, company_id=activity.company_id, actor_user_id=user_id,
        object_type="project", object_id=stage.project_id,
        details={"stage": stage.name, "activity": activity.name},
    )


def archived_stages(project: Project) -> list[Stage]:
    return [s for s in _sorted(project.stages) if s.archived_at is not None]


def archived_activities(stage: Stage) -> list[Activity]:
    return [a for a in _sorted(stage.activities) if a.archived_at is not None]


# ---------------------------------------------------------------- R3: células de Preencher etapas


def parse_pieces(raw: str | None, quantity: int) -> int:
    """Peças concluídas digitadas na célula: só número inteiro de 0 até as previstas."""
    text = (raw or "").strip().replace(" ", "")
    if not text.isdigit():
        raise ProgressError(f"Use um número inteiro de peças, de 0 a {quantity}.")
    value = int(text)
    if value > quantity:
        raise ProgressError(f"As peças concluídas não podem passar das previstas ({quantity}).")
    return value


def _decimal(raw: str | None) -> Decimal | None:
    text = (raw or "").strip().replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        value = Decimal(text)
    except InvalidOperation:
        return None
    return value if value.is_finite() else None


def parse_minutes(raw: str | None) -> Decimal:
    """Tempo ideal (min por unidade): 0 a 100000, até 2 casas (vírgula ou ponto)."""
    value = _decimal(raw)
    if value is None or value < 0 or value > Decimal("100000") or value != value.quantize(Decimal("0.01")):
        raise EditError("Tempo ideal inválido: use minutos de 0 a 100000, com até 2 casas (ex.: 7,5).")
    return value.quantize(Decimal("0.01"))


def parse_percent(raw: str | None) -> Decimal:
    """% da etapa no modo simples: 0 a 100, inteiro ou 1 casa (aceita “45”, “45,5”, “45%”)."""
    value = _decimal((raw or "").replace("%", ""))
    if value is None or value < 0 or value > 100 or value != value.quantize(Decimal("0.1")):
        raise ProgressError("Use um % de 0 a 100, inteiro ou com 1 casa (ex.: 45 ou 45,5).")
    return value.quantize(Decimal("0.1"))


def set_units_done(
    activity: Activity,
    target: int,
    expected_version: int | None,
    user_id: uuid.UUID,
    *,
    can_decrease: bool,
) -> ProgressEntry | None:
    """Peças concluídas em valor ABSOLUTO (a célula da planilha). Para cima, é um registro como
    outro qualquer (``register_progress``: máximo, versão, eventos). Para baixo, é uma CORREÇÃO:
    lançamento negativo no histórico (append-only), só para quem ``can_decrease`` (supervisor+
    na rota), com auditoria ``progress.corrected``. Igual ao atual → nada muda (``None``)."""
    project = activity.stage.project
    if not 0 <= target <= project.quantity:
        raise ProgressError(f"As peças concluídas vão de 0 a {project.quantity}.")
    if expected_version is not None and expected_version != activity.version:
        raise ConflictError("Esta atividade foi atualizada por outra pessoa. Confira os números e tente de novo.")
    delta = target - activity.units_done
    if delta == 0:
        return None
    if delta > 0:
        return register_progress(activity, delta, expected_version, user_id)
    if not can_decrease:
        raise ProgressError("Para diminuir as peças, peça a um supervisor ou desfaça o lançamento no histórico.")
    result = db.session.execute(
        update(Activity)
        .where(
            Activity.id == activity.id,
            Activity.company_id == activity.company_id,
            Activity.version == activity.version,
            Activity.units_done + delta >= 0,
        )
        .values(units_done=Activity.units_done + delta, version=Activity.version + 1)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:  # pragma: no cover - corrida rara entre duas abas
        db.session.rollback()
        raise ConflictError("Esta atividade foi atualizada por outra pessoa. Confira os números e tente de novo.")
    before = activity.units_done
    entry = ProgressEntry(company_id=activity.company_id, activity_id=activity.id, user_id=user_id, delta=delta)
    db.session.add(entry)
    db.session.flush()
    db.session.refresh(activity)
    # Diminuir nunca conclui etapa nem projeto (como o desfazer).
    _after_progress(activity, entry, stage_before=True, project_before=True)
    audit.record(
        audit.PROGRESS_CORRECTED, company_id=activity.company_id, actor_user_id=user_id,
        object_type="project", object_id=project.id,
        details={"activity": activity.name, "antes": before, "depois": activity.units_done},
    )
    return entry


def simple_activity(stage: Stage) -> Activity:
    """Atividade interna da etapa no modo simples (cria se a etapa ficou sem nenhuma)."""
    live = active_activities(stage)
    if live:
        return live[0]
    activity = add_activity(stage, NewActivity(name=stage.name, ideal_minutes=SIMPLE_DEFAULT_MINUTES))
    db.session.expire(stage, ["activities"])
    return activity


def set_stage_percent(
    stage: Stage, pct: Decimal, expected_version: int | None, user_id: uuid.UUID, *, can_decrease: bool
) -> ProgressEntry | None:
    """Modo simples: o % da etapa vira peças da atividade interna (``calc.pecas_de_percentual``).
    Mesmas regras de ``set_units_done`` (versão, máximo, diminuir só supervisor+)."""
    project = stage.project
    if not is_simple(project):
        raise ProgressError("Este projeto está no modo detalhado: lance as peças de cada subatividade.")
    activity = simple_activity(stage)
    pieces = calc.pecas_de_percentual(float(pct) / 100, project.quantity)
    return set_units_done(activity, pieces, expected_version, user_id, can_decrease=can_decrease)


# ---------------------------------------------------------------- R4: modo de progresso


def set_progress_mode(project: Project, mode: str, user_id: uuid.UUID | None) -> bool:
    """Troca o modo do projeto. Simples → detalhado mantém a atividade de cada etapa (vira a
    primeira subatividade). Detalhado → simples só se cada etapa tiver no máximo UMA atividade
    (``EditError`` com as etapas que impedem); etapa sem atividade ganha a interna."""
    if mode not in PROGRESS_MODES:
        raise EditError("Modo de progresso inválido.")
    if project.progress_mode == mode:
        return False
    stages = active_stages(project)
    if mode == PROGRESS_SIMPLE:
        blocking = [s.name for s in stages if len(active_activities(s)) > 1]
        if blocking:
            names = ", ".join(f"“{n}”" for n in blocking[:5]) + ("…" if len(blocking) > 5 else "")
            raise EditError(
                "Para usar o modo simples, cada etapa pode ter no máximo uma subatividade. "
                f"Têm mais de uma: {names}. Exclua ou junte as subatividades e tente de novo."
            )
    before = project.progress_mode
    project.progress_mode = mode
    db.session.flush()
    if mode == PROGRESS_SIMPLE:
        for stage in stages:
            simple_activity(stage)
        db.session.flush()
        db.session.expire(project, ["stages"])
        _sync_status(project)
    audit.record(
        audit.PROJECT_MODE_CHANGED, company_id=project.company_id, actor_user_id=user_id,
        object_type="project", object_id=project.id, details={"antes": before, "depois": mode},
    )
    return True


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
    from app.services.checklists import active_items

    stages = [
        NewStage(
            name=s.name,
            activities=[NewActivity(name=a.name, ideal_minutes=a.ideal_minutes) for a in active_activities(s)],
            checklist=[i.text for i in active_items(s)],
            checklist_required=s.checklist_required,
        )
        for s in active_stages(project)
    ]
    copy = create_project(
        company,
        name=(name or f"Cópia de {project.name}")[:160],
        product=project.product,
        quantity=project.quantity,
        start_date=project.start_date,
        due_date=project.due_date,
        people=project.people,
        hours_per_day=project.hours_per_day,
        stages=stages,
        template_version_id=project.template_version_id,
        source="duplicate",
        progress_mode=project.progress_mode,
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


PROJECT_FILTERS = ("ativos", "concluidos", "todos")
LIKE_ESCAPE = "\\"


def _like(term: str) -> str:
    """Padrão LIKE com barra invertida, % e _ digitados pelo usuário escapados (busca literal)."""
    for char in (LIKE_ESCAPE, "%", "_"):
        term = term.replace(char, LIKE_ESCAPE + char)
    return "%" + term + "%"


def list_projects(status: str = "todos", q: str | None = None, with_stages: bool = False) -> list[Project]:
    """Projetos não arquivados da empresa. ``status``: ativos | concluidos | todos;
    ``q`` busca (sem diferenciar maiúsculas) no nome e no produto. ``with_stages`` já traz etapas e
    subatividades em duas consultas (telas que somam todos os projetos, sem uma consulta por etapa)."""
    stmt = scoped(Project).where(Project.archived_at.is_(None))
    if with_stages:
        stmt = stmt.options(selectinload(Project.stages).selectinload(Stage.activities))
    if status == "ativos":
        stmt = stmt.where(Project.status == PROJECT_ACTIVE)
    elif status == "concluidos":
        stmt = stmt.where(Project.status == PROJECT_DONE)
    term = (q or "").strip()[:80]
    if term:
        pattern = _like(term)
        stmt = stmt.where(
            or_(Project.name.ilike(pattern, escape=LIKE_ESCAPE), Project.product.ilike(pattern, escape=LIKE_ESCAPE))
        )
    return list(db.session.execute(stmt.order_by(Project.created_at.desc())).scalars())


def count_projects_by_status() -> dict[str, int]:
    """Contagem para as abas da lista (ativos, concluídos, todos), sem arquivados."""
    rows = db.session.execute(
        select(Project.status, func.count())
        .where(Project.company_id == current_company_id(), Project.archived_at.is_(None))
        .group_by(Project.status)
    ).all()
    counts = {status: n for status, n in rows}
    active, done = counts.get(PROJECT_ACTIVE, 0), counts.get(PROJECT_DONE, 0)
    return {"ativos": active, "concluidos": done, "todos": active + done}


def _history_stmt(project: Project | None, activity_id, user_id):
    stmt = (
        scoped(ProgressEntry)
        .join(Activity, Activity.id == ProgressEntry.activity_id)
        .join(Stage, Stage.id == Activity.stage_id)
        .where(Activity.company_id == current_company_id())
    )
    if project is not None:
        stmt = stmt.where(Stage.project_id == project.id)
    if activity_id is not None:
        stmt = stmt.where(ProgressEntry.activity_id == activity_id)
    if user_id is not None:
        stmt = stmt.where(ProgressEntry.user_id == user_id)
    return stmt


def history(project: Project, limit: int = 200) -> list[ProgressEntry]:
    return list(
        db.session.execute(
            _history_stmt(project, None, None).order_by(ProgressEntry.at.desc(), ProgressEntry.id.desc()).limit(limit)
        ).scalars()
    )


def history_page(
    project: Project | None = None,
    *,
    activity_id=None,
    user_id=None,
    page: int = 1,
    per_page: int = 25,
) -> tuple[list[ProgressEntry], int]:
    """Uma página do histórico (mais recente primeiro) e o total com os mesmos filtros.
    ``project=None`` = todos os projetos da empresa. Tudo pela empresa da sessão."""
    stmt = _history_stmt(project, activity_id, user_id)
    total = db.session.execute(select(func.count()).select_from(stmt.order_by(None).subquery())).scalar_one()
    page = max(1, page)
    entries = list(
        db.session.execute(
            stmt.order_by(ProgressEntry.at.desc(), ProgressEntry.id.desc()).limit(per_page).offset((page - 1) * per_page)
        ).scalars()
    )
    return entries, total


def undo_entries(entries: list[ProgressEntry]) -> dict[uuid.UUID, ProgressEntry]:
    """{id do registro desfeito: lançamento que o desfez} (para “desfeito por Fulano”)."""
    if not entries:
        return {}
    rows = db.session.execute(
        scoped(ProgressEntry).where(ProgressEntry.reverts_entry_id.in_([e.id for e in entries]))
    ).scalars()
    return {r.reverts_entry_id: r for r in rows}


def last_entries(project: Project) -> dict[uuid.UUID, ProgressEntry]:
    """Último lançamento de cada atividade do projeto ({activity_id: registro}): autoria na
    linha da atividade (“último: Fulano +2”). Uma consulta, pela empresa da sessão."""
    latest = (
        select(ProgressEntry.activity_id, func.max(ProgressEntry.at).label("at"))
        .join(Activity, Activity.id == ProgressEntry.activity_id)
        .join(Stage, Stage.id == Activity.stage_id)
        .where(ProgressEntry.company_id == current_company_id(), Stage.project_id == project.id)
        .group_by(ProgressEntry.activity_id)
        .subquery()
    )
    rows = db.session.execute(
        scoped(ProgressEntry)
        .join(latest, (latest.c.activity_id == ProgressEntry.activity_id) & (latest.c.at == ProgressEntry.at))
        .order_by(ProgressEntry.id)
    ).scalars()
    return {e.activity_id: e for e in rows}


PEOPLE_PERIODS = {"7": 7, "30": 30, "90": 90, "tudo": None}


@dataclass(frozen=True)
class PersonRow:
    user: object  # User ou None (autor removido)
    result: calc.ProgressoPessoa
    activities: tuple  # ((Activity, saldo), ...) para a tela


def people_progress(project: Project, *, tz: str, today: date, days: int | None) -> list[PersonRow]:
    """Progresso por pessoa no projeto: lançamentos dos últimos ``days`` dias (``None`` = tudo,
    datas no fuso da empresa) e atividades ATIVAS atribuídas. As contas são de
    ``calc.progresso_por_pessoa``; aqui só se lê o banco (empresa da sessão)."""
    from datetime import timedelta

    from app.formatting import local_dt
    from app.models import User

    rows = db.session.execute(
        select(ProgressEntry.user_id, ProgressEntry.activity_id, ProgressEntry.delta, ProgressEntry.at, Activity.ideal_minutes)
        .join(Activity, Activity.id == ProgressEntry.activity_id)
        .join(Stage, Stage.id == Activity.stage_id)
        .where(ProgressEntry.company_id == current_company_id(), Stage.project_id == project.id)
    ).all()
    lancamentos = [
        calc.Lancamento(pessoa=u, atividade=a, delta=d, dia=local_dt(at, tz).date(), ideal_min=float(m or 0))
        for u, a, d, at, m in rows
    ]
    live = [act for stage in active_stages(project) for act in active_activities(stage)]
    atribuidas = [
        calc.AtividadeAtribuida(
            atividade=act.id, responsavel=act.assignee_id, ideal_min=float(act.ideal_minutes or 0),
            pecas=act.units_done, previstas=project.quantity,
        )
        for act in live
        if act.assignee_id is not None
    ]
    inicio = today - timedelta(days=days - 1) if days else None
    results = calc.progresso_por_pessoa(lancamentos, atribuidas, inicio=inicio, fim=today)
    user_ids = [r.pessoa for r in results if r.pessoa is not None]
    users = {u.id: u for u in db.session.execute(select(User).where(User.id.in_(user_ids))).scalars()} if user_ids else {}
    activity_ids = {k for r in results for k, _ in r.por_atividade}
    acts = (
        {a.id: a for a in db.session.execute(scoped(Activity).where(Activity.id.in_(activity_ids))).scalars()}
        if activity_ids
        else {}
    )
    return [
        PersonRow(
            user=users.get(r.pessoa),
            result=r,
            activities=tuple((acts[k], v) for k, v in r.por_atividade if k in acts),
        )
        for r in results
    ]


def running_totals(entries: list[ProgressEntry]) -> dict[uuid.UUID, tuple[int, int]]:
    """{id do registro: (antes, depois)} = peças da atividade antes e depois do lançamento
    (soma acumulada dos lançamentos, desfazeres incluídos). Para o “6 → 7 de 10”."""
    if not entries:
        return {}
    activity_ids = {e.activity_id for e in entries}
    rows = db.session.execute(
        select(ProgressEntry.id, ProgressEntry.activity_id, ProgressEntry.delta)
        .where(ProgressEntry.company_id == current_company_id(), ProgressEntry.activity_id.in_(activity_ids))
        .order_by(ProgressEntry.at.asc(), ProgressEntry.id.asc())
    ).all()
    totals: dict[uuid.UUID, int] = {}
    out: dict[uuid.UUID, tuple[int, int]] = {}
    wanted = {e.id for e in entries}
    for entry_id, activity_id, delta in rows:
        before = totals.get(activity_id, 0)
        totals[activity_id] = before + delta
        if entry_id in wanted:
            out[entry_id] = (before, before + delta)
    return out


def history_users(project: Project | None = None) -> list:
    """Pessoas que já registraram (para o filtro do histórico)."""
    from app.models import User

    stmt = (
        select(User)
        .join(ProgressEntry, ProgressEntry.user_id == User.id)
        .join(Activity, Activity.id == ProgressEntry.activity_id)
        .join(Stage, Stage.id == Activity.stage_id)
        .where(ProgressEntry.company_id == current_company_id())
        .distinct()
        .order_by(User.name)
    )
    if project is not None:
        stmt = stmt.where(Stage.project_id == project.id)
    return list(db.session.execute(stmt).scalars())


def pieces_per_day(
    project: Project | None, *, activity_id=None, user_id=None, tz: str, days: int = 14
) -> list[tuple[date, int]]:
    """Saldo de peças por dia (fuso da empresa) nos últimos ``days`` dias com registro,
    do mais antigo ao mais novo. Desfazeres entram com sinal negativo."""
    from app.formatting import local_dt

    stmt = _history_stmt(project, activity_id, user_id).order_by(ProgressEntry.at.desc(), ProgressEntry.id.desc()).limit(2000)
    totals: dict[date, int] = {}
    for entry in db.session.execute(stmt).scalars():
        day = local_dt(entry.at, tz).date()
        totals[day] = totals.get(day, 0) + entry.delta
    return sorted(totals.items())[-days:]


# ---------------------------------------------------------------- resumo do novo projeto


@dataclass(frozen=True)
class PlanSummary:
    """Prévia do projeto antes de criar (tempo, dias úteis, término e se cabe no prazo)."""

    total_hours: float
    workdays: float | None  # dias úteis necessários (None = equipe sem capacidade)
    end_date: date | None
    fits: bool | None  # None = sem prazo informado
    margin: int  # dias úteis de folga (fits) ou de atraso (not fits)


def plan_summary(
    *,
    minutes_per_unit: Decimal,
    quantity: int,
    people: int,
    hours_per_day: Decimal,
    start: date | None,
    due: date | None,
    company: Company,
    today: date,
) -> PlanSummary:
    """Mesmas contas do projeto criado (calc.py), a partir do tempo por unidade do modelo."""
    total_hours = float(minutes_per_unit) * quantity / 60
    workdays = calc.dias_uteis_restantes(total_hours, people, float(hours_per_day))
    if workdays is None:
        return PlanSummary(total_hours, None, None, None, 0)
    holidays = holidays_for(company.id)
    days = company.workdays()
    begin = max(today, start) if start else today
    end = calc.prazo_em_data(begin, workdays, holidays, days)
    if due is None:
        return PlanSummary(total_hours, workdays, end, None, 0)
    if end <= due:
        return PlanSummary(total_hours, workdays, end, True, calc.dias_uteis_entre(end, due, holidays, days))
    return PlanSummary(total_hours, workdays, end, False, calc.dias_uteis_entre(due, end, holidays, days))
