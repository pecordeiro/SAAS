"""Avisos de cobrança por e-mail (pagamento em atraso / carência).

Usa o serviço de e-mail da Fase 5 (``app.services.email.send_template``): console em
development/test (os testes leem ``email.outbox(app)``), Resend em produção, entrega sem
derrubar a requisição. Textos em ``app/templates/emails/billing_past_due.txt|html``.
"""

from __future__ import annotations

import logging
from contextlib import nullcontext

from flask import current_app, has_request_context
from sqlalchemy import select

from app.extensions import db
from app.formatting import br_date, local_dt
from app.models import ROLE_OWNER, Membership, User
from app.services import email as email_svc

logger = logging.getLogger(__name__)

PAST_DUE_SUBJECT = "Pagamento da assinatura em atraso"


def owner_emails(company_id) -> list[str]:
    return list(
        db.session.execute(
            select(User.email)
            .join(Membership, Membership.user_id == User.id)
            .where(
                Membership.company_id == company_id,
                Membership.role == ROLE_OWNER,
                Membership.active.is_(True),
                User.active.is_(True),
            )
            .order_by(User.email)
        ).scalars()
    )


def _request_scope():
    """Fora de requisição (CLI/reconciliação) os context processors do layout esperam uma
    requisição: renderiza dentro de uma requisição sintética com a URL base do site."""
    if has_request_context():
        return nullcontext()
    base = current_app.config.get("APP_BASE_URL") or "http://localhost"
    return current_app.test_request_context("/", base_url=base)


def _send(to: str, subject: str, template: str, **context) -> None:
    with _request_scope():
        email_svc.send_template(to, subject, template, **context)


def _billing_url() -> str:
    with _request_scope():
        try:
            return email_svc.external_url("billing.overview")
        except RuntimeError:  # pragma: no cover - sem APP_BASE_URL fora de dev/test
            return (current_app.config.get("APP_BASE_URL") or "").rstrip("/") + "/app/assinatura"


def past_due(company, grace_until) -> int:
    """Avisa os proprietários que o pagamento venceu e até quando vai a carência."""
    sent = 0
    context = {
        "company_name": company.name,
        "grace_date": br_date(local_dt(grace_until).date()) if grace_until else "—",
        "billing_url": _billing_url(),
    }
    for to in owner_emails(company.id):
        try:
            _send(to, PAST_DUE_SUBJECT, "billing_past_due", **context)
            sent += 1
        except Exception as exc:  # noqa: BLE001 - aviso nunca derruba o webhook
            logger.error("falha ao enviar aviso de atraso (%s)", exc.__class__.__name__)
    return sent


DOWNGRADE_CANCELED_SUBJECT = "Troca de plano não aplicada"


def downgrade_canceled(company, kept_plan, refused_plan, reason: str) -> int:
    """Avisa que o downgrade agendado não foi aplicado porque o uso não cabe no plano menor."""
    sent = 0
    context = {
        "company_name": company.name,
        "kept_plan": kept_plan.name,
        "refused_plan": refused_plan.name,
        "reason": reason,
        "billing_url": _billing_url(),
    }
    for to in owner_emails(company.id):
        try:
            _send(to, DOWNGRADE_CANCELED_SUBJECT, "billing_downgrade_canceled", **context)
            sent += 1
        except Exception as exc:  # noqa: BLE001
            logger.error("falha ao enviar aviso de downgrade (%s)", exc.__class__.__name__)
    return sent
