"""Etapa C — equipe da plataforma e requisições de identidade visual.

- ``grant``/``revoke``/``list_staff``: só por linha de comando (``flask staff ...``), com motivo
  e quem autorizou; a conta precisa de e-mail confirmado e MFA ligado. Cada ação vai para
  ``platform_audit_logs`` (append-only).
- ``open_visual_request``: chamado por ``billing.service._apply_plan`` na mesma transação da
  troca de plano; idempotente (uma requisição aberta por empresa).
- ``set_status``: único caminho para mudar o estado/anotação; audita em ``platform_audit_logs``
  (sem o texto da anotação, que pode ter dado de contato).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.extensions import db
from app.models import (
    ROLE_OWNER,
    VISUAL_DELIVERED,
    VISUAL_NEW,
    VISUAL_STATUSES,
    Company,
    Membership,
    PlatformAuditLog,
    User,
    VisualRequest,
)
from app.models.base import utcnow

VISUAL_REQUEST_OPENED = "staff.visual_request_opened"
VISUAL_STATUS_CHANGED = "staff.visual_status_changed"
STAFF_GRANTED = "staff.granted"
STAFF_REVOKED = "staff.revoked"
STATUS_LABELS = {
    VISUAL_NEW: "Nova",
    "briefing_filled": "Briefing preenchido",
    "in_progress": "Em andamento",
    VISUAL_DELIVERED: "Entregue",
}
MIN_REASON = 15
MAX_NOTES = 4000


class StaffError(Exception):
    pass


def is_staff(user) -> bool:
    return bool(
        getattr(user, "is_authenticated", False)
        and user.is_staff
        and user.active
        and user.mfa_enabled
        and user.email_confirmed_at is not None
    )


def open_visual_request(company_id: uuid.UUID, plan_code: str) -> VisualRequest | None:
    """Abre a requisição (sem commit). ``None`` se já existe uma não entregue."""
    existing = db.session.execute(
        select(VisualRequest.id).where(VisualRequest.company_id == company_id, VisualRequest.status != VISUAL_DELIVERED)
    ).first()
    if existing:
        return None
    company = db.session.get(Company, company_id)
    owner = db.session.execute(
        select(User)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.company_id == company_id, Membership.role == ROLE_OWNER, Membership.active.is_(True))
        .order_by(Membership.created_at)
    ).scalars().first()
    request_ = VisualRequest(
        company_id=company_id,
        company_name=company.name if company else "",
        plan_code=plan_code,
        contact_name=owner.name if owner else None,
        contact_email=owner.email if owner else None,
    )
    db.session.add(request_)
    db.session.flush()
    db.session.add(
        PlatformAuditLog(
            action=VISUAL_REQUEST_OPENED,
            subject_company_id=company_id,
            operator="sistema",
            details={"request_id": str(request_.id), "plano": plan_code},
        )
    )
    return request_


def list_requests(status: str | None = None) -> list[VisualRequest]:
    query = select(VisualRequest).order_by(VisualRequest.created_at.desc())
    if status in VISUAL_STATUSES:
        query = query.where(VisualRequest.status == status)
    return list(db.session.execute(query).scalars())


def get_request(request_id: uuid.UUID) -> VisualRequest | None:
    return db.session.get(VisualRequest, request_id)


def set_status(request_: VisualRequest, status: str, notes: str | None, actor: User) -> None:
    """Muda estado e anotação (com commit). Estado inválido → ``StaffError``."""
    if status not in VISUAL_STATUSES:
        raise StaffError("Estado inválido.")
    notes = (notes or "").strip() or None
    if notes and len(notes) > MAX_NOTES:
        raise StaffError(f"Anotação com no máximo {MAX_NOTES} caracteres.")
    before = request_.status
    request_.status, request_.notes = status, notes
    request_.updated_at, request_.updated_by = utcnow(), actor.email
    db.session.add(
        PlatformAuditLog(
            action=VISUAL_STATUS_CHANGED,
            subject_company_id=request_.company_id,
            operator=actor.email[:120],
            details={"request_id": str(request_.id), "de": before, "para": status},
        )
    )
    db.session.commit()


def _user(email: str) -> User:
    from app.services.accounts import find_user_by_email

    user = find_user_by_email(email)
    if user is None or not user.active:
        raise StaffError("Usuário não encontrado ou desativado.")
    return user


def _check(reason: str, operator: str) -> tuple[str, str]:
    reason, operator = (reason or "").strip(), (operator or "").strip()
    if len(reason) < MIN_REASON:
        raise StaffError(f"Motivo obrigatório (mínimo {MIN_REASON} caracteres).")
    if not operator:
        raise StaffError("Informe quem autorizou (--autorizado-por).")
    return reason, operator


def grant(email: str, reason: str, operator: str) -> User:
    reason, operator = _check(reason, operator)
    user = _user(email)
    if user.email_confirmed_at is None or not user.mfa_enabled:
        raise StaffError("A conta da equipe precisa de e-mail confirmado e MFA ativo.")
    user.is_staff = True
    db.session.add(PlatformAuditLog(action=STAFF_GRANTED, operator=operator[:120], details={"user_id": str(user.id), "motivo": reason}))
    db.session.commit()
    return user


def revoke(email: str, reason: str, operator: str) -> User:
    reason, operator = _check(reason, operator)
    user = _user(email)
    user.is_staff = False
    user.session_version += 1  # derruba as sessões abertas
    db.session.add(PlatformAuditLog(action=STAFF_REVOKED, operator=operator[:120], details={"user_id": str(user.id), "motivo": reason}))
    db.session.commit()
    return user


def list_staff() -> list[User]:
    return list(db.session.execute(select(User).where(User.is_staff.is_(True)).order_by(User.email)).scalars())
