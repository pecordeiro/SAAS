"""Notificações por e-mail disparadas pelo worker (Etapa F).

Rodam FORA de requisição, no contexto RLS da empresa do evento (ADR-0010). Toda mensagem
leva só o necessário (nome da empresa/projeto/atividade e o link); links sempre absolutos a
partir de ``APP_BASE_URL`` (``email.external_url``). Falha de entrega levanta ``EmailError``:
o evento volta para a fila com backoff.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo

from flask import current_app
from sqlalchemy import select

from app.extensions import db
from app.models import ROLE_LEVEL, ROLE_SUPERVISOR, Activity, Company, DomainEvent, Membership, User
from app.services import email as email_svc

logger = logging.getLogger(__name__)

VISUAL_REQUEST_SUBJECT = "Nova requisição de identidade visual"
ASSIGNED_SUBJECT = "Nova atividade atribuída a você"


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
