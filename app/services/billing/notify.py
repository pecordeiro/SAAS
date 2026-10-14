"""Avisos de cobrança por e-mail (pagamento em atraso / carência).

Usa o serviço de e-mail da Fase 5 (``app.services.email.send_template``): console em
development/test (os testes leem ``email.outbox(app)``), Resend em produção, entrega sem
derrubar a requisição. Textos em ``app/templates/emails/billing_past_due.txt|html``.
"""

from __future__ import annotations

import logging

from flask import current_app
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


def _billing_url() -> str:
    try:
        return email_svc.external_url("billing.overview")
    except RuntimeError:  # sem APP_BASE_URL e fora de requisição (ex.: CLI)
        base = current_app.config.get("APP_BASE_URL") or ""
        return base.rstrip("/") + "/app/assinatura"


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
            email_svc.send_template(to, PAST_DUE_SUBJECT, "billing_past_due", **context)
            sent += 1
        except Exception as exc:  # noqa: BLE001 - aviso nunca derruba o webhook
            logger.error("falha ao enviar aviso de atraso (%s)", exc.__class__.__name__)
    return sent
