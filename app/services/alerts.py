"""Alertas automáticos por empresa (Etapa F).

Módulo opcional ``alertas`` (R6, ADR-0017): empresa com o módulo desligado é pulada.

A REGRA mora em ``calc.alertas_projeto`` (pura). Aqui só: montar as entradas a partir do
banco (no contexto RLS da empresa), gravar o que saiu com dedupe ``(company_id, dedupe_key,
day)`` e mandar UM e-mail-resumo por pessoa (supervisor/proprietário com ``notify_alerts``).

Repetição de e-mail: a mesma situação (mesma ``dedupe_key``) gera um alerta por dia na lista,
mas só volta a ser enviada por e-mail depois de ``ALERT_EMAIL_REPEAT_DAYS`` (7) — a lista mostra
o dia a dia, a caixa de entrada não vira spam. E-mail só a partir de ``ALERT_EMAIL_HOUR`` (7h)
no fuso da empresa.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta

from flask import current_app
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app import rls
from app.extensions import db
from app.formatting import br_date, local_dt
from app.models import (
    ALERT_DEADLINE_RISK,
    ALERT_FORECAST_LATE,
    ALERT_PART_OVERDUE,
    ALERT_STAGE_STALLED,
    PROJECT_ACTIVE,
    Activity,
    Alert,
    Company,
    Project,
    ProgressEntry,
)
from app.services import calc, modules, notifications
from app.services import projects as svc
from app.services.email import EmailError
from app.services.holidays import holidays_for

logger = logging.getLogger(__name__)

ALERT_LIST_DAYS = 14
ALERT_EMAIL_REPEAT_DAYS = 7
ALERT_EMAIL_HOUR = 7
DIGEST_SUBJECT = "Alertas de produção"

KIND_LABELS = {
    ALERT_FORECAST_LATE: "Atraso previsto",
    ALERT_DEADLINE_RISK: "Prazo em risco",
    ALERT_STAGE_STALLED: "Etapa parada",
    ALERT_PART_OVERDUE: "Peça atrasada",
}


def _iso(value) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except (TypeError, ValueError):
        return None


def _plural(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def describe(alert: Alert) -> str:
    """Frase do alerta para a tela e o e-mail (números já calculados por calc)."""
    d = alert.details or {}
    stage = alert.stage.name if alert.stage is not None else ""
    if alert.kind == ALERT_FORECAST_LATE:
        return (
            f"Término previsto em {br_date(_iso(d.get('previsao')))}, depois do prazo de "
            f"{br_date(_iso(d.get('prazo')))} ({_plural(int(d.get('atraso_du', 0)), 'dia útil', 'dias úteis')} de atraso)."
        )
    if alert.kind == ALERT_DEADLINE_RISK:
        if "vencido_du" in d:
            return (
                f"O prazo de {br_date(_iso(d.get('prazo')))} passou há "
                f"{_plural(int(d['vencido_du']), 'dia útil', 'dias úteis')} e o projeto não terminou."
            )
        if "folga_du" in d:
            return (
                f"Término previsto em {br_date(_iso(d.get('previsao')))}, com folga de só "
                f"{_plural(int(d['folga_du']), 'dia útil', 'dias úteis')} até o prazo ({br_date(_iso(d.get('prazo')))})."
            )
        return (
            f"Prazo em {br_date(_iso(d.get('prazo')))} ({_plural(int(d.get('ate_prazo_du', 0)), 'dia útil', 'dias úteis')}) "
            "e sem previsão de término (confira a equipe do projeto)."
        )
    if alert.kind == ALERT_STAGE_STALLED:
        return (
            f"Etapa “{stage}” sem lançamento há {_plural(int(d.get('parada_du', 0)), 'dia útil', 'dias úteis')} "
            f"(último em {br_date(_iso(d.get('ultimo')))})."
        )
    if alert.kind == ALERT_PART_OVERDUE:
        return (
            f"Etapa “{stage}” aguardando peça: a previsão era {br_date(_iso(d.get('prevista')))} e a marca não foi "
            "atualizada. Confirme a nova data ou retire a marca."
        )
    return KIND_LABELS.get(alert.kind, alert.kind)  # pragma: no cover


# ------------------------------------------------------------------ avaliação


def _last_entry_days(company: Company) -> dict[uuid.UUID, date]:
    """Dia local do último lançamento por etapa (uma consulta)."""
    rows = db.session.execute(
        select(Activity.stage_id, func.max(ProgressEntry.at))
        .join(Activity, Activity.id == ProgressEntry.activity_id)
        .where(ProgressEntry.company_id == company.id, Activity.company_id == company.id)
        .group_by(Activity.stage_id)
    ).all()
    return {stage_id: local_dt(at, company.timezone).date() for stage_id, at in rows if at is not None}


def compute_company(company: Company, today: date) -> list[tuple[Project, calc.Alerta]]:
    """Alertas de hoje para os projetos ativos da empresa (sem gravar)."""
    projects = list(
        db.session.execute(
            select(Project)
            .where(Project.company_id == company.id, Project.archived_at.is_(None), Project.status == PROJECT_ACTIVE)
            .order_by(Project.created_at)
        ).scalars()
    )
    if not projects:
        return []
    holidays = holidays_for(company.id)
    days = company.workdays()
    last = _last_entry_days(company)
    stalled = company.stalled_days if calc.dias_parada_valido(company.stalled_days) else calc.DIAS_PARADA_PADRAO
    # R6: sem o módulo “aguardando peça”, a marca não vale (nem “peça atrasada”, nem a exceção
    # de etapa parada) — o dado fica guardado e volta a valer se o módulo for religado.
    waiting_on = modules.is_enabled(company, modules.AGUARDANDO_PECA)
    out = []
    for project in projects:
        result = svc.summary(project)
        status = calc.status_etapa(result.unidades_concluidas, project.quantity, result.progresso_geral)
        forecast = svc.forecast_end(project, result, company, today)
        stages = [
            calc.EtapaAlerta(
                id=stage.id,
                status=sr.status,
                ultimo_registro=last.get(stage.id),
                aguardando_peca=waiting_on and bool(stage.waiting_part),
                peca_prevista=stage.part_expected_on,
                peca_atualizada=local_dt(stage.part_updated_at, company.timezone).date() if stage.part_updated_at else None,
            )
            for stage, sr in zip(svc.active_stages(project), result.etapas)
        ]
        for alerta in calc.alertas_projeto(
            projeto=project.id,
            hoje=today,
            prazo=project.due_date,
            previsao=forecast,
            concluido=status == calc.STATUS_CONCLUIDA,
            etapas=stages,
            dias_parada=stalled,
            feriados=holidays,
            dias_semana=days,
        ):
            out.append((project, alerta))
    return out


def evaluate_company(company: Company, now: datetime) -> list[Alert]:
    """Grava os alertas de hoje que ainda não existem (idempotente). Sem commit."""
    today = notifications.local_today(company, now)
    found = compute_company(company, today)
    if not found:
        return []
    existing = set(
        db.session.execute(
            select(Alert.dedupe_key).where(Alert.company_id == company.id, Alert.day == today)
        ).scalars()
    )
    created = []
    for project, alerta in found:
        if alerta.chave in existing:
            continue
        existing.add(alerta.chave)
        alert = Alert(
            company_id=company.id,
            kind=alerta.tipo,
            severity=alerta.severidade,
            dedupe_key=alerta.chave,
            day=today,
            project_id=project.id,
            stage_id=alerta.etapa,
            details=dict(alerta.valores),
            created_at=now,
        )
        db.session.add(alert)
        created.append(alert)
    db.session.flush()
    return created


# ------------------------------------------------------------------ e-mail


def send_digest(company: Company, now: datetime) -> int:
    """Um e-mail por destinatário com os alertas de HOJE ainda não enviados (respeitando a
    janela de repetição). Devolve quantos e-mails saíram. Sem commit."""
    local = notifications.local_now(company, now)
    if local.hour < int(current_app.config.get("ALERT_EMAIL_HOUR", ALERT_EMAIL_HOUR)):
        return 0
    today = local.date()
    pending = list(
        db.session.execute(
            select(Alert)
            .where(Alert.company_id == company.id, Alert.day == today, Alert.emailed_at.is_(None))
            .order_by(Alert.severity.asc(), Alert.created_at)
        ).scalars()
    )
    if not pending:
        return 0
    recent = set(
        db.session.execute(
            select(Alert.dedupe_key).where(
                Alert.company_id == company.id,
                Alert.emailed_at.is_not(None),
                Alert.emailed_at >= now - timedelta(days=ALERT_EMAIL_REPEAT_DAYS),
            )
        ).scalars()
    )
    to_send = [a for a in pending if a.dedupe_key not in recent]
    if not to_send:
        return 0
    people = notifications.recipients(company.id, "notify_alerts")
    if not people:
        return 0
    items = [
        {
            "label": KIND_LABELS.get(a.kind, a.kind),
            "project": a.project.name,
            "text": describe(a),
            "url": notifications.url_for_email("app.project_detail", project_id=a.project_id),
        }
        for a in to_send
    ]
    context = dict(
        company_name=company.name,
        items=items,
        list_url=notifications.url_for_email("app.alerts"),
        prefs_url=notifications.url_for_email("account.profile", _anchor="notificacoes"),
    )
    sent = 0
    for person in people:
        try:
            notifications.send(person.email, f"{DIGEST_SUBJECT} · {company.name}", "alerts_digest",
                               name=person.name, **context)
            sent += 1
        except EmailError:
            logger.warning("resumo de alertas da empresa %s não entregue a um destinatário", company.id)
    if sent:
        for alert in to_send:
            alert.emailed_at = now
    return sent


def run_company(company: Company, now: datetime) -> tuple[int, int]:
    """Avalia e envia para uma empresa, no contexto RLS dela, com commit."""
    rls.set_context(company_id=company.id)
    try:
        created = evaluate_company(company, now)
        db.session.commit()
    except IntegrityError:  # outro worker gravou o mesmo alerta ao mesmo tempo
        db.session.rollback()
        created = []
    rls.set_context(company_id=company.id)
    sent = send_digest(company, now)
    db.session.commit()
    return len(created), sent


def run_all(now: datetime) -> dict[str, int]:
    from app.services.worker import company_ids

    total = {"companies": 0, "created": 0, "emails": 0}
    try:
        for company_id in company_ids():
            company = db.session.get(Company, company_id)
            if company is None or company.deletion_requested_at is not None:
                continue
            if not modules.is_enabled(company, modules.ALERTAS):
                continue  # R6: módulo desligado = nenhum alerta gravado nem e-mail
            created, sent = run_company(company, now)
            total["companies"] += 1
            total["created"] += created
            total["emails"] += sent
    finally:
        rls.set_context(company_id=None)
    return total


# ------------------------------------------------------------------ tela


def recent(company_id: uuid.UUID, today: date, days: int = ALERT_LIST_DAYS) -> list[Alert]:
    """Alertas da empresa dos últimos ``days`` dias (mais recentes primeiro)."""
    return list(
        db.session.execute(
            select(Alert)
            .where(Alert.company_id == company_id, Alert.day > today - timedelta(days=days))
            .order_by(Alert.day.desc(), Alert.severity.asc(), Alert.created_at)
        ).scalars()
    )
