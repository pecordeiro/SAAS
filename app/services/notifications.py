"""Notificações por e-mail disparadas pelo worker (Etapa F).

Rodam FORA de requisição, no contexto RLS da empresa do evento (ADR-0010). Toda mensagem
leva só o necessário (nome da empresa/projeto/atividade e o link); links sempre absolutos a
partir de ``APP_BASE_URL`` (``email.external_url``). Falha de entrega levanta ``EmailError``:
o evento volta para a fila com backoff.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import current_app
from sqlalchemy import select

from app.extensions import db
from app.models import ROLE_LEVEL, ROLE_SUPERVISOR, Activity, Company, DomainEvent, Membership, User
from app.services import email as email_svc

logger = logging.getLogger(__name__)

VISUAL_REQUEST_SUBJECT = "Nova requisição de identidade visual"
ASSIGNED_SUBJECT = "Nova subatividade atribuída a você"


PREFS = ("notify_assignment", "notify_alerts", "notify_weekly")


def local_now(company: Company, now: datetime) -> datetime:
    """Agora no fuso da empresa (fuso inválido cai em America/Sao_Paulo)."""
    try:
        return now.astimezone(ZoneInfo(company.timezone))
    except Exception:  # noqa: BLE001
        return now.astimezone(ZoneInfo("America/Sao_Paulo"))


def local_today(company: Company, now: datetime) -> date:
    return local_now(company, now).date()


def recipients(company_id: uuid.UUID, pref: str, min_role: str = ROLE_SUPERVISOR) -> list[User]:
    """Pessoas que recebem um aviso da empresa: vínculo que vale agora (ativo, no prazo), sem
    acesso de suporte, usuário ativo, papel ≥ ``min_role`` e preferência ``pref`` ligada."""
    if pref not in PREFS:
        raise ValueError(pref)
    allowed = [role for role, level in ROLE_LEVEL.items() if level >= ROLE_LEVEL[min_role]]
    return list(
        db.session.execute(
            select(User)
            .join(Membership, Membership.user_id == User.id)
            .where(
                Membership.company_id == company_id,
                Membership.usable(),
                Membership.is_support.is_(False),
                Membership.role.in_(allowed),
                User.active.is_(True),
                getattr(User, pref).is_(True),
            )
            .order_by(User.email)
        ).scalars()
    )


def send(to: str, subject: str, template: str, attachments=(), **context) -> None:
    with email_svc.request_scope():
        message = email_svc.render_message(to, subject, template, attachments=attachments, **context)
    email_svc.send_now(message)


def url_for_email(endpoint: str, **values) -> str:
    with email_svc.request_scope():
        return email_svc.external_url(endpoint, **values)


def on_visual_custom_contracted(event: DomainEvent) -> None:
    """Etapa C (pendência): avisa a equipe da plataforma que há requisição nova no /interno.
    Só com ``STAFF_NOTIFY_EMAIL`` configurado; sem ele o evento é só marcado publicado."""
    to = (current_app.config.get("STAFF_NOTIFY_EMAIL") or "").strip()
    if not to:
        return
    plan = str((event.payload or {}).get("plano") or "")
    send(to, VISUAL_REQUEST_SUBJECT, "staff_visual_request", plan=plan, url=url_for_email("interno.index"))


def _uuid(value) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        return None


def _active_member(company_id: uuid.UUID, user_id: uuid.UUID) -> User | None:
    """Usuário com vínculo que vale agora na empresa (sem suporte) e conta ativa."""
    return db.session.execute(
        select(User)
        .join(Membership, Membership.user_id == User.id)
        .where(
            Membership.company_id == company_id,
            Membership.user_id == user_id,
            Membership.usable(),
            Membership.is_support.is_(False),
            User.active.is_(True),
        )
    ).scalar_one_or_none()


def on_activity_assigned(event: DomainEvent) -> None:
    """Etapa D → F: e-mail ao responsável com o link da atividade.

    Confere o estado ATUAL antes de enviar (entrega “pelo menos uma vez”): atividade ainda
    existe, não está arquivada e continua com o mesmo responsável; a pessoa ainda é membro
    ativo; a preferência ``notify_assignment`` está ligada; não foi ela mesma que se atribuiu.
    Qualquer “não” → nada a enviar (o evento é marcado publicado)."""
    from app.services import modules

    if not modules.is_enabled(event.company_id, modules.ATRIBUICAO):
        return  # R6: módulo desligado depois da atribuição → nada a enviar
    payload = event.payload or {}
    activity_id = _uuid(payload.get("activity_id"))
    assignee_id = _uuid(payload.get("assignee_user_id"))
    if activity_id is None or assignee_id is None:
        return
    if _uuid(payload.get("assigned_by_user_id")) == assignee_id:
        return
    activity = db.session.execute(
        select(Activity).where(Activity.id == activity_id, Activity.company_id == event.company_id)
    ).scalar_one_or_none()
    if activity is None or activity.assignee_id != assignee_id:
        return
    stage = activity.stage
    project = stage.project
    if activity.archived_at or stage.archived_at or project.archived_at:
        return
    user = _active_member(event.company_id, assignee_id)
    if user is None or not user.notify_assignment:
        return
    company = db.session.get(Company, event.company_id)
    send(
        user.email,
        ASSIGNED_SUBJECT,
        "activity_assigned",
        name=user.name,
        company_name=company.name if company else "",
        project_name=project.name,
        stage_name=stage.name,
        activity_name=activity.name,
        url=url_for_email("app.activity_detail", activity_id=activity.id),
        prefs_url=url_for_email("account.profile", _anchor="notificacoes"),
    )


# ------------------------------------------------------------------ relatório semanal

WEEKLY_SUBJECT = "Relatório semanal de produção"
WEEKLY_JOB = "weekly_report"
WEEKLY_REPORT_WEEKDAY = 0  # segunda-feira (fuso da empresa)
WEEKLY_REPORT_HOUR = 7


def week_key(day: date) -> str:
    iso = day.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _since(start: date) -> datetime:
    """Corte grosso em UTC (um dia de folga para qualquer fuso); o filtro fino é pelo dia local."""
    return datetime.combine(start - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)


def _project_rows(company: Company, start: date, end: date, today: date) -> list[dict]:
    """Uma linha por projeto ativo (não arquivado, não concluído), números de calc/serviços."""
    from sqlalchemy import func

    from app.formatting import local_dt
    from app.models import PROJECT_ACTIVE, Project, ProgressEntry, Stage
    from app.services import calc
    from app.services import projects as svc

    projects = list(
        db.session.execute(
            select(Project)
            .where(Project.company_id == company.id, Project.archived_at.is_(None), Project.status == PROJECT_ACTIVE)
            .order_by(Project.name)
        ).scalars()
    )
    if not projects:
        return []
    since = _since(start)
    pieces: dict = {}
    for project_id, at, delta in db.session.execute(
        select(Stage.project_id, ProgressEntry.at, ProgressEntry.delta)
        .join(Activity, Activity.id == ProgressEntry.activity_id)
        .join(Stage, Stage.id == Activity.stage_id)
        .where(ProgressEntry.company_id == company.id, Stage.project_id.in_([p.id for p in projects]))
        .where(ProgressEntry.at >= since)
    ).all():
        if start <= local_dt(at, company.timezone).date() <= end:
            pieces[project_id] = pieces.get(project_id, 0) + delta
    waiting = dict(
        db.session.execute(
            select(Stage.project_id, func.count())
            .where(Stage.company_id == company.id, Stage.waiting_part.is_(True), Stage.archived_at.is_(None))
            .group_by(Stage.project_id)
        ).all()
    )
    from app.services import modules

    waiting_on = modules.is_enabled(company, modules.AGUARDANDO_PECA)
    rows = []
    for project in projects:
        result = svc.summary(project)
        status = calc.status_etapa(result.unidades_concluidas, project.quantity, result.progresso_geral)
        forecast = svc.forecast_end(project, result, company, today)
        late = bool(status != calc.STATUS_CONCLUIDA and forecast and project.due_date and forecast > project.due_date)
        rows.append(
            {
                "Projeto": project.name,
                "Produto": project.product or "",
                "Situação": status,
                "Progresso": round(result.progresso_geral, 4),
                "Unidades concluídas": result.unidades_concluidas,
                "Quantidade": project.quantity,
                "Peças na semana": pieces.get(project.id, 0),
                "Horas que faltam": round(result.tempo_restante_h, 2),
                "Prazo": project.due_date,
                "Término previsto": forecast,
                "Atraso previsto (dias úteis)": svc.delay_workdays(project, forecast, company) if late else 0,
            }
        )
        if waiting_on:
            rows[-1]["Etapas aguardando peça"] = waiting.get(project.id, 0)
    return rows


def _people_rows(company: Company, start: date, end: date) -> list[dict]:
    """Por pessoa, na semana, em todos os projetos (agregação em calc.progresso_por_pessoa)."""
    from app.formatting import local_dt
    from app.models import ProgressEntry
    from app.services import calc

    since = _since(start)
    entries = db.session.execute(
        select(ProgressEntry.user_id, ProgressEntry.activity_id, ProgressEntry.delta, ProgressEntry.at, Activity.ideal_minutes)
        .join(Activity, Activity.id == ProgressEntry.activity_id)
        .where(ProgressEntry.company_id == company.id)
        .where(ProgressEntry.at >= since)
    ).all()
    lancamentos = [
        calc.Lancamento(pessoa=user_id, atividade=activity_id, delta=delta,
                        dia=local_dt(at, company.timezone).date(), ideal_min=float(ideal or 0))
        for user_id, activity_id, delta, at, ideal in entries
    ]
    result = calc.progresso_por_pessoa(lancamentos, (), inicio=start, fim=end)
    ids = [r.pessoa for r in result if r.pessoa is not None]
    names = dict(db.session.execute(select(User.id, User.name).where(User.id.in_(ids))).all()) if ids else {}
    return [
        {
            "Pessoa": names.get(r.pessoa, "Pessoa removida") if r.pessoa else "Pessoa removida",
            "Peças (saldo)": r.pecas,
            "Registros": r.registros,
            "Desfeitos": r.desfeitos,
            "Horas-padrão": round(r.horas, 2),
            "Dias com lançamento": r.dias_ativos,
        }
        for r in result
    ]


def weekly_report(company: Company, now: datetime, force: bool = False) -> dict | None:
    """Relatório da semana anterior para UMA empresa (no contexto RLS dela), uma vez por
    semana ISO (marca em ``job_runs``). None = não é hora ou já foi feito. Sem commit."""
    from sqlalchemy.exc import IntegrityError

    from app.models import JobRun
    from app.services import exporter
    from app.services.email import Attachment, EmailError

    local = local_now(company, now)
    if not force and (local.weekday() != WEEKLY_REPORT_WEEKDAY or local.hour < WEEKLY_REPORT_HOUR):
        return None
    today = local.date()
    period_key = week_key(today)
    exists = db.session.execute(
        select(JobRun.id).where(JobRun.company_id == company.id, JobRun.job == WEEKLY_JOB, JobRun.period_key == period_key)
    ).first()
    if exists:
        return None
    run = JobRun(company_id=company.id, job=WEEKLY_JOB, period_key=period_key, created_at=now)
    db.session.add(run)
    try:
        db.session.flush()
    except IntegrityError:  # outro worker marcou primeiro
        db.session.rollback()
        return None
    from app.services import modules

    start, end = today - timedelta(days=7), today - timedelta(days=1)
    projects = _project_rows(company, start, end, today)
    # R6: progresso por pessoa é do módulo “atribuição”; aguardando peça, do módulo dele.
    by_person = modules.is_enabled(company, modules.ATRIBUICAO)
    people = _people_rows(company, start, end) if by_person else []
    sent = 0
    recipients_ = recipients(company.id, "notify_weekly") if (projects or people) else []
    if recipients_:
        from app.formatting import br_date

        period = f"{br_date(start)} a {br_date(end)}"
        attachment = Attachment(
            filename=f"relatorio-semanal-{period_key}.xlsx",
            content=exporter.weekly_xlsx(
                projects, people, period, waiting=modules.is_enabled(company, modules.AGUARDANDO_PECA),
                by_person=by_person,
            ),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        context = dict(
            company_name=company.name,
            period=period,
            projects=projects,
            people=people[:10],
            more_people=max(0, len(people) - 10),
            projects_url=url_for_email("app.projects"),
            prefs_url=url_for_email("account.profile", _anchor="notificacoes"),
        )
        for person in recipients_:
            try:
                send(person.email, f"{WEEKLY_SUBJECT} · {company.name}", "weekly_report", attachments=(attachment,),
                     name=person.name, **context)
                sent += 1
            except EmailError:
                logger.warning("relatório semanal da empresa %s não entregue a um destinatário", company.id)
    run.details = {"projetos": len(projects), "pessoas": len(people), "enviados": sent}
    return run.details


def run_weekly_reports(now: datetime) -> dict[str, int]:
    from app import rls
    from app.services import modules
    from app.services.worker import company_ids

    total = {"companies": 0, "emails": 0}
    try:
        for company_id in company_ids():
            company = db.session.get(Company, company_id)
            if company is None or company.deletion_requested_at is not None:
                continue
            rls.set_context(company_id=company.id)
            if not modules.is_enabled(company, modules.ALERTAS):
                db.session.rollback()
                continue  # R6: relatório semanal é do módulo “alertas”
            details = weekly_report(company, now)
            db.session.commit()
            if details is not None:
                total["companies"] += 1
                total["emails"] += details["enviados"]
    finally:
        rls.set_context(company_id=None)
    return total
