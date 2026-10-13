"""Casos de uso de projetos. Toda consulta passa por tenancy (company_id da sessão)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import update

from app.extensions import db
from app.models import Activity, Company, Project, ProgressEntry, Stage
from app.services import calc
from app.services.holidays import holidays_for
from app.tenancy import current_company_id, scoped


class ProgressError(Exception):
    """Erro de validação ao registrar peças (mensagem pronta para a tela)."""


class ConflictError(ProgressError):
    """A atividade mudou desde que a tela foi aberta (controle otimista)."""


@dataclass
class NewActivity:
    name: str
    ideal_minutes: Decimal


@dataclass
class NewStage:
    name: str
    activities: list[NewActivity]


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
) -> Project:
    """Cria o projeto com as etapas dadas. Vindas de um modelo (``template_version_id``),
    as etapas já são a cópia (snapshot) da versão: ver ``services.templates``."""
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
        add_stage(project, new_stage.name, new_stage.activities, position=s_pos)
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
    )
    db.session.add(activity)
    db.session.flush()
    return activity


def register_progress(activity: Activity, delta: int, expected_version: int | None, user_id: uuid.UUID) -> ProgressEntry:
    """Soma `delta` peças à atividade, grava o histórico e incrementa a versão.

    Regras: delta ≥ 1; peças concluídas nunca passam das previstas (quantidade do projeto).
    `expected_version` diferente da atual → ConflictError (409).
    """
    if delta < 1:
        raise ProgressError("Informe pelo menos 1 peça.")
    previstas = activity.stage.project.quantity
    maximo = max(0, previstas - activity.units_done)
    if expected_version is not None and expected_version != activity.version:
        raise ConflictError("Esta atividade foi atualizada por outra pessoa. Confira os números e tente de novo.")
    if delta > maximo:
        raise ProgressError(f"Máximo {maximo} peça(s) nesta atividade.")
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
    return entry


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
