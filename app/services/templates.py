"""Modelos de etapas versionados.

- ``create_template`` cria o modelo com a versão 1 e a marca como atual.
- ``update_template`` grava uma NOVA versão quando as etapas mudam (versões são imutáveis;
  projetos criados de versões antigas não mudam).
- ``stages_from_version`` devolve a CÓPIA das etapas/atividades da versão, no formato que
  ``services.projects.create_project`` recebe (snapshot).
- ``compare`` mostra o que mudaria no projeto se a versão atual do modelo fosse aplicada;
  ``apply_current_version`` aplica só com a versão confirmada pela pessoa e registra na
  auditoria (aparece no histórico do projeto). Etapas/atividades que saíram do modelo são
  ARQUIVADAS (o histórico continua).

Ids de modelo/versão SEMPRE chegam aqui já resolvidos pela empresa da sessão
(``tenancy.get_or_404``/``scoped``); as funções conferem ``company_id`` de novo por defesa.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select

from app.extensions import db
from app.models import (
    Company,
    Project,
    Stage,
    StageChecklistItem,
    Template,
    TemplateActivity,
    TemplateChecklistItem,
    TemplateStage,
    TemplateVersion,
)
from app.services import audit
from app.services.projects import (
    NewActivity,
    NewStage,
    active_activities,
    active_stages,
    add_activity,
    add_stage,
    create_project,
)
from app.tenancy import scoped


class TemplateError(Exception):
    """Erro de validação de modelo (mensagem pronta para a tela)."""


def _key(name: str) -> str:
    return " ".join((name or "").split()).casefold()


def _check_name(company_id: uuid.UUID, name: str, exclude_id: uuid.UUID | None = None) -> str:
    name = (name or "").strip()
    if not name or len(name) > 160:
        raise TemplateError("Informe o nome do modelo (até 160 caracteres).")
    # Comparação em Python (casefold): lower() do SQLite só conhece ASCII.
    query = select(Template.id, Template.name).where(Template.company_id == company_id)
    if exclude_id is not None:
        query = query.where(Template.id != exclude_id)
    if any(_key(other) == _key(name) for _, other in db.session.execute(query)):
        raise TemplateError("Já existe um modelo com este nome.")
    return name


def _check_stages(stages: list[NewStage]) -> None:
    if not stages:
        raise TemplateError("Inclua pelo menos uma etapa.")


def create_template(
    company: Company,
    name: str,
    stages: list[NewStage],
    created_by_user_id: uuid.UUID | None = None,
    description: str | None = None,
) -> Template:
    name = _check_name(company.id, name)
    _check_stages(stages)
    template = Template(company_id=company.id, name=name, description=description or None)
    db.session.add(template)
    db.session.flush()
    version = add_version(template, stages, created_by_user_id=created_by_user_id)
    template.current_version_id = version.id
    db.session.flush()
    return template


def add_version(
    template: Template, stages: list[NewStage], created_by_user_id: uuid.UUID | None = None, notes: str | None = None
) -> TemplateVersion:
    number = max((v.number for v in template.versions), default=0) + 1
    version = TemplateVersion(
        company_id=template.company_id,
        template_id=template.id,
        number=number,
        created_by_user_id=created_by_user_id,
        notes=notes,
    )
    db.session.add(version)
    db.session.flush()
    for s_pos, new_stage in enumerate(stages):
        stage = TemplateStage(
            company_id=template.company_id, template_version_id=version.id, name=new_stage.name, position=s_pos,
            checklist_required=bool(new_stage.checklist_required),
        )
        db.session.add(stage)
        db.session.flush()
        for i_pos, text in enumerate(new_stage.checklist):
            db.session.add(
                TemplateChecklistItem(company_id=template.company_id, template_stage_id=stage.id, text=text, position=i_pos)
            )
        for a_pos, new_activity in enumerate(new_stage.activities):
            db.session.add(
                TemplateActivity(
                    company_id=template.company_id,
                    template_stage_id=stage.id,
                    name=new_activity.name,
                    ideal_minutes=new_activity.ideal_minutes,
                    position=a_pos,
                )
            )
    db.session.flush()
    db.session.refresh(version)
    db.session.expire(template, ["versions"])
    return version


def stages_from_version(version: TemplateVersion) -> list[NewStage]:
    return [
        NewStage(
            name=stage.name,
            activities=[NewActivity(name=a.name, ideal_minutes=a.ideal_minutes) for a in stage.activities],
            checklist=[i.text for i in stage.checklist_items],
            checklist_required=stage.checklist_required,
        )
        for stage in version.stages
    ]


def _signature(stages: list[NewStage]) -> list:
    return [
        (
            s.name,
            [(a.name, Decimal(a.ideal_minutes).quantize(Decimal("0.01"))) for a in s.activities],
            list(s.checklist),
            bool(s.checklist_required),
        )
        for s in stages
    ]


def update_template(
    template: Template,
    *,
    name: str,
    description: str | None,
    stages: list[NewStage],
    user_id: uuid.UUID | None,
) -> TemplateVersion | None:
    """Renomeia/descreve o modelo e, se as etapas mudaram, cria a próxima versão e a
    torna atual. Devolve a versão nova (ou None se as etapas não mudaram)."""
    template.name = _check_name(template.company_id, name, exclude_id=template.id)
    template.description = description or None
    _check_stages(stages)
    current = template.current_version
    if current is not None and _signature(stages_from_version(current)) == _signature(stages):
        db.session.flush()
        return None
    version = add_version(template, stages, created_by_user_id=user_id)
    template.current_version_id = version.id
    db.session.flush()
    db.session.refresh(template)
    return version


def archive_template(template: Template, user_id: uuid.UUID | None) -> None:
    template.archived_at = datetime.now(timezone.utc)
    db.session.flush()
    audit.record(
        audit.TEMPLATE_ARCHIVED, company_id=template.company_id, actor_user_id=user_id,
        object_type="template", object_id=template.id, details={"name": template.name},
    )


def list_templates() -> list[Template]:
    return list(
        db.session.execute(
            scoped(Template).where(Template.archived_at.is_(None)).order_by(func.lower(Template.name))
        ).scalars()
    )


def projects_using(template: Template) -> int:
    """Projetos ativos (não arquivados) criados de qualquer versão do modelo."""
    return db.session.execute(
        select(func.count())
        .select_from(Project)
        .join(TemplateVersion, TemplateVersion.id == Project.template_version_id)
        .where(
            Project.company_id == template.company_id,
            TemplateVersion.company_id == template.company_id,
            TemplateVersion.template_id == template.id,
            Project.archived_at.is_(None),
        )
    ).scalar_one()


def minutes_per_unit(version: TemplateVersion | None) -> Decimal:
    if version is None:
        return Decimal("0")
    return sum((a.ideal_minutes for s in version.stages for a in s.activities), Decimal("0"))


def create_project_from_template(
    company: Company,
    template: Template,
    *,
    name: str,
    quantity: int,
    start_date: date | None,
    due_date: date | None,
    people: int,
    hours_per_day: Decimal,
    product: str | None = None,
) -> Project:
    """Projeto com a cópia (snapshot) da versão ATUAL do modelo."""
    if template.company_id != company.id or template.archived_at is not None:
        raise TemplateError("Modelo não encontrado.")
    version = template.current_version
    if version is None:  # pragma: no cover - todo modelo nasce com a v1
        raise TemplateError("Modelo sem versão.")
    return create_project(
        company,
        name=name,
        quantity=quantity,
        start_date=start_date,
        due_date=due_date,
        people=people,
        hours_per_day=hours_per_day,
        stages=stages_from_version(version),
        template_version_id=version.id,
        source="template",
        product=product,
    )


# ---------------------------------------------------------------- comparar e aplicar


@dataclass(frozen=True)
class Change:
    kind: str  # stage_added | stage_removed | activity_added | activity_removed | minutes_changed | order_changed | checklist_changed
    stage: str
    activity: str | None = None
    old: Decimal | None = None
    new: Decimal | None = None

    @property
    def label(self) -> str:
        if self.kind == "stage_added":
            return f"Nova etapa “{self.stage}”"
        if self.kind == "stage_removed":
            return f"Etapa “{self.stage}” sai do projeto (fica arquivada com o histórico)"
        if self.kind == "activity_added":
            return f"Nova subatividade “{self.activity}” em “{self.stage}” ({self.new} min)"
        if self.kind == "activity_removed":
            return f"Subatividade “{self.activity}” de “{self.stage}” sai (fica arquivada com o histórico)"
        if self.kind == "checklist_changed":
            return f"Checklist de inspeção de “{self.stage}” muda (itens novos entram; respostas antigas ficam)"
        if self.kind == "minutes_changed":
            return f"Tempo ideal de “{self.activity}” ({self.stage}): {self.old} → {self.new} min"
        return "Ordem das etapas muda"


@dataclass(frozen=True)
class Comparison:
    template: Template | None
    project_version: TemplateVersion | None
    current_version: TemplateVersion | None
    changes: tuple[Change, ...]

    @property
    def up_to_date(self) -> bool:
        return self.current_version is None or (
            self.project_version is not None and self.project_version.id == self.current_version.id
        )


def project_template(project: Project) -> tuple[Template | None, TemplateVersion | None]:
    if project.template_version_id is None:
        return None, None
    version = db.session.execute(
        select(TemplateVersion).where(
            TemplateVersion.id == project.template_version_id, TemplateVersion.company_id == project.company_id
        )
    ).scalar_one_or_none()
    if version is None:  # pragma: no cover - versão de outra empresa: tratada como sem modelo
        return None, None
    return version.template, version


def _match(items: list, name: str, used: set):
    key = _key(name)
    for item in items:
        if item.id not in used and _key(item.name) == key:
            used.add(item.id)
            return item
    return None


def _plan(project: Project, version: TemplateVersion):
    """Pareia etapas/atividades do projeto (ativas) com as da versão, pelo nome."""
    stages = active_stages(project)
    used: set = set()
    pairs = []
    for t_stage in version.stages:
        p_stage = _match(stages, t_stage.name, used)
        acts_used: set = set()
        acts = active_activities(p_stage) if p_stage is not None else []
        act_pairs = [(t_act, _match(acts, t_act.name, acts_used)) for t_act in t_stage.activities]
        leftover_acts = [a for a in acts if a.id not in acts_used]
        pairs.append((t_stage, p_stage, act_pairs, leftover_acts))
    leftover_stages = [s for s in stages if s.id not in used]
    return pairs, leftover_stages


def _project_items(p_stage: Stage) -> list[StageChecklistItem]:
    return list(
        db.session.execute(
            select(StageChecklistItem)
            .where(
                StageChecklistItem.company_id == p_stage.company_id,
                StageChecklistItem.stage_id == p_stage.id,
                StageChecklistItem.archived_at.is_(None),
            )
            .order_by(StageChecklistItem.position)
        ).scalars()
    )


def _checklist_missing(t_stage: TemplateStage, p_stage: Stage) -> list[str]:
    """Itens do modelo que a etapa do projeto ainda não tem (comparação por texto, sem caixa)."""
    have = {_key(i.text) for i in _project_items(p_stage)}
    return [i.text for i in t_stage.checklist_items if _key(i.text) not in have]


def compare(project: Project) -> Comparison:
    template, version = project_template(project)
    current = template.current_version if template is not None else None
    if current is None:
        return Comparison(template, version, current, ())
    pairs, leftover_stages = _plan(project, current)
    changes: list[Change] = []
    for t_stage, p_stage, act_pairs, leftover_acts in pairs:
        if p_stage is None:
            changes.append(Change("stage_added", t_stage.name))
            for t_act, _ in act_pairs:
                changes.append(Change("activity_added", t_stage.name, t_act.name, new=t_act.ideal_minutes))
            continue
        for t_act, p_act in act_pairs:
            if p_act is None:
                changes.append(Change("activity_added", t_stage.name, t_act.name, new=t_act.ideal_minutes))
            elif Decimal(p_act.ideal_minutes) != Decimal(t_act.ideal_minutes):
                changes.append(
                    Change("minutes_changed", t_stage.name, t_act.name, old=p_act.ideal_minutes, new=t_act.ideal_minutes)
                )
        for p_act in leftover_acts:
            changes.append(Change("activity_removed", p_stage.name, p_act.name))
        if _checklist_missing(t_stage, p_stage) or bool(t_stage.checklist_required) != bool(p_stage.checklist_required):
            changes.append(Change("checklist_changed", t_stage.name))
    for p_stage in leftover_stages:
        changes.append(Change("stage_removed", p_stage.name))
    matched = [p.id for _, p, _, _ in pairs if p is not None]
    current_order = [s.id for s in active_stages(project) if s.id in set(matched)]
    if matched != current_order:
        changes.append(Change("order_changed", ""))
    return Comparison(template, version, current, tuple(changes))


def apply_current_version(project: Project, confirmed_version_id: uuid.UUID, user_id: uuid.UUID | None) -> Comparison:
    """Aplica a versão atual do modelo ao projeto. ``confirmed_version_id`` é a versão que a
    pessoa viu na comparação: se o modelo mudou de novo nesse meio tempo → TemplateError."""
    comparison = compare(project)
    current = comparison.current_version
    if current is None:
        raise TemplateError("Este projeto não veio de um modelo.")
    if str(current.id) != str(confirmed_version_id):
        raise TemplateError("O modelo mudou desde a comparação. Confira as diferenças de novo.")
    if comparison.up_to_date and not comparison.changes:
        raise TemplateError("O projeto já está na versão atual do modelo.")
    now = datetime.now(timezone.utc)
    pairs, leftover_stages = _plan(project, current)
    position = 0
    for t_stage, p_stage, act_pairs, leftover_acts in pairs:
        if p_stage is None:
            p_stage = add_stage(
                project, t_stage.name, [], checklist=[i.text for i in t_stage.checklist_items],
                checklist_required=t_stage.checklist_required,
            )
        else:
            # Etapa G: itens novos do modelo entram no fim; nenhum item do projeto é apagado
            # (respostas assinadas apontam para eles).
            next_pos = max((i.position for i in _project_items(p_stage)), default=-1) + 1
            for text in _checklist_missing(t_stage, p_stage):
                db.session.add(StageChecklistItem(
                    company_id=project.company_id, stage_id=p_stage.id, text=text, position=next_pos
                ))
                next_pos += 1
            p_stage.checklist_required = bool(t_stage.checklist_required)
        p_stage.position = position
        position += 1
        a_pos = 0
        for t_act, p_act in act_pairs:
            if p_act is None:
                p_act = add_activity(p_stage, NewActivity(name=t_act.name, ideal_minutes=t_act.ideal_minutes))
            p_act.ideal_minutes = t_act.ideal_minutes
            p_act.position = a_pos
            a_pos += 1
        for p_act in leftover_acts:
            p_act.archived_at = now
            p_act.position = a_pos
            a_pos += 1
    for p_stage in leftover_stages:
        p_stage.archived_at = now
    for p_stage in sorted(project.stages, key=lambda s: s.position):
        if p_stage.archived_at is not None:
            p_stage.position = position
            position += 1
    previous = comparison.project_version
    project.template_version_id = current.id
    db.session.flush()
    db.session.expire(project, ["stages"])
    for stage in db.session.execute(select(Stage).where(Stage.project_id == project.id)).scalars():
        db.session.expire(stage, ["activities"])
    from app.services.projects import _sync_status

    _sync_status(project)
    audit.record(
        audit.TEMPLATE_VERSION_APPLIED,
        company_id=project.company_id,
        actor_user_id=user_id,
        object_type="project",
        object_id=project.id,
        details={
            "template": comparison.template.name,
            "from_version": previous.number if previous else None,
            "to_version": current.number,
            "changes": [c.label for c in comparison.changes],
        },
    )
    return comparison
