"""Fase 7 — acesso temporário de suporte da plataforma a uma empresa.

Só por linha de comando (``flask suporte conceder|revogar|listar|expirar``), nunca pela tela:
- motivo obrigatório (mín. 15 caracteres), prazo em horas (teto ``SUPPORT_ACCESS_MAX_HOURS``),
  papel operador ou supervisor (nunca proprietário);
- a pessoa de suporte precisa ter conta ativa, e-mail confirmado e MFA ligado;
- vira um vínculo ``memberships`` com ``is_support`` e ``expires_at``: ``tenancy`` ignora o
  vínculo vencido na hora (expira sozinho, sem depender de cron); ``flask suporte expirar``
  só desativa e audita os vencidos;
- não conta no limite de usuários do plano e o proprietário pode desativá-lo na tela;
- cada concessão, revogação e expiração vai para ``audit_logs`` da empresa (visível ao
  proprietário) e os proprietários recebem e-mail com o motivo e o prazo.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy import select

from app import rls
from app.extensions import db
from app.models import ROLE_OPERATOR, ROLE_SUPERVISOR, Company, Membership, User
from app.models.base import utcnow
from app.services import audit

GRANTED = audit.SUPPORT_ACCESS_GRANTED
REVOKED = audit.SUPPORT_ACCESS_REVOKED
EXPIRED = audit.SUPPORT_ACCESS_EXPIRED
ALLOWED_ROLES = (ROLE_OPERATOR, ROLE_SUPERVISOR)
MIN_REASON = 15


class SupportError(Exception):
    pass


def _find_user(email: str) -> User:
    from app.services.accounts import find_user_by_email

    user = find_user_by_email(email)
    if user is None or not user.active:
        raise SupportError("Usuário de suporte não encontrado ou desativado.")
    return user


def _find_company(company_id: uuid.UUID | str) -> Company:
    try:
        company = db.session.get(Company, uuid.UUID(str(company_id)))
    except ValueError:
        company = None
    if company is None:
        raise SupportError("Empresa não encontrada.")
    return company


def grant(
    *, email: str, company_id: uuid.UUID | str, reason: str, hours: int, role: str, operator: str, now: datetime | None = None
) -> Membership:
    """Concede (ou renova) o acesso. Faz commit e avisa os proprietários."""
    now = now or utcnow()
    reason = (reason or "").strip()
    operator = (operator or "").strip()
    if len(reason) < MIN_REASON:
        raise SupportError(f"Motivo obrigatório (mínimo {MIN_REASON} caracteres).")
    if not operator:
        raise SupportError("Informe quem autorizou (--autorizado-por).")
    max_hours = int(current_app.config.get("SUPPORT_ACCESS_MAX_HOURS", 72))
    if not 1 <= hours <= max_hours:
        raise SupportError(f"Prazo entre 1 e {max_hours} horas.")
    if role not in ALLOWED_ROLES:
        raise SupportError("Papel de suporte: operator ou supervisor.")
    user = _find_user(email)
    if user.email_confirmed_at is None or not user.mfa_enabled:
        raise SupportError("A conta de suporte precisa de e-mail confirmado e MFA ativo.")
    company = _find_company(company_id)
    rls.set_context(company_id=company.id)
    member = db.session.execute(
        select(Membership).where(Membership.company_id == company.id, Membership.user_id == user.id)
    ).scalar_one_or_none()
    if member is not None and not member.is_support:
        raise SupportError("Esta pessoa já é membro da empresa; acesso de suporte não se aplica.")
    expires_at = now + timedelta(hours=hours)
    if member is None:
        member = Membership(company_id=company.id, user_id=user.id, role=role, is_support=True)
        db.session.add(member)
    member.role = role
    member.active = True
    member.expires_at = expires_at
    db.session.flush()
    audit.record(
        GRANTED,
        company_id=company.id,
        actor_user_id=None,
        object_type="membership",
        object_id=member.id,
        details={
            "support_user": user.name,
            "role": role,
            "reason": reason[:500],
            "expires_at": expires_at.isoformat(),
            "authorized_by": operator[:120],
        },
    )
    db.session.commit()
    _notify(company, user, reason, expires_at, role)
    return member


def _notify(company: Company, support_user: User, reason: str, expires_at: datetime, role: str) -> None:
    from app.models import ROLE_LABELS
    from app.services.email import send_template
    from app.services.lgpd import _owners, email_context

    owners = _owners(company.id)
    with email_context():
        for owner in owners:
            send_template(
                owner.email,
                "Acesso de suporte concedido à sua empresa",
                "support_access",
                name=owner.name,
                company_name=company.name,
                support_name=support_user.name,
                reason=reason,
                expires_at=expires_at,
                role_label=ROLE_LABELS.get(role, role),
            )


def revoke(*, email: str, company_id: uuid.UUID | str, operator: str) -> bool:
    user = _find_user(email)
    company = _find_company(company_id)
    rls.set_context(company_id=company.id)
    member = db.session.execute(
        select(Membership).where(
            Membership.company_id == company.id, Membership.user_id == user.id, Membership.is_support.is_(True)
        )
    ).scalar_one_or_none()
    if member is None or not member.active:
        return False
    member.active = False
    audit.record(
        REVOKED,
        company_id=company.id,
        actor_user_id=None,
        object_type="membership",
        object_id=member.id,
        details={"support_user": user.name, "authorized_by": (operator or "")[:120]},
    )
    db.session.commit()
    return True


def _support_memberships() -> list[Membership]:
    """Vínculos de suporte de todas as empresas (cada empresa no próprio contexto RLS)."""
    found: list[Membership] = []
    for company_id in list(db.session.execute(select(Company.id)).scalars()):
        rls.set_context(company_id=company_id)
        found.extend(
            db.session.execute(
                select(Membership).where(Membership.company_id == company_id, Membership.is_support.is_(True))
            ).scalars()
        )
    return found


def expire(now: datetime | None = None) -> int:
    """Desativa e audita os vínculos de suporte vencidos (o acesso já não valia). Commit."""
    now = now or utcnow()
    count = 0
    for member in _support_memberships():
        expires = member.expires_at
        if expires is not None and expires.tzinfo is None:
            from datetime import timezone

            expires = expires.replace(tzinfo=timezone.utc)
        if member.active and expires is not None and expires <= now:
            rls.set_context(company_id=member.company_id)
            member.active = False
            audit.record(
                EXPIRED,
                company_id=member.company_id,
                actor_user_id=None,
                object_type="membership",
                object_id=member.id,
                details={"expired_at": expires.isoformat()},
                    )
            count += 1
    rls.set_context(company_id=None)
    db.session.commit()
    return count


def active_grants(now: datetime | None = None) -> list[Membership]:
    now = now or utcnow()
    result = []
    for member in _support_memberships():
        expires = member.expires_at
        if expires is not None and expires.tzinfo is None:
            from datetime import timezone

            expires = expires.replace(tzinfo=timezone.utc)
        if member.active and expires is not None and expires > now:
            result.append(member)
    rls.set_context(company_id=None)
    return result
