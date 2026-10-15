"""Notificações por e-mail disparadas pelo worker (Etapa F).

Rodam FORA de requisição, no contexto RLS da empresa do evento (ADR-0010). Toda mensagem
leva só o necessário (nome da empresa/projeto/atividade e o link); links sempre absolutos a
partir de ``APP_BASE_URL`` (``email.external_url``). Falha de entrega levanta ``EmailError``:
o evento volta para a fila com backoff.
"""

from __future__ import annotations

import logging

from flask import current_app

from app.models import DomainEvent
from app.services import email as email_svc

logger = logging.getLogger(__name__)

VISUAL_REQUEST_SUBJECT = "Nova requisição de identidade visual"


def _send(to: str, subject: str, template: str, attachments=(), **context) -> None:
    with email_svc.request_scope():
        message = email_svc.render_message(to, subject, template, attachments=attachments, **context)
    email_svc.send_now(message)


def _url(endpoint: str, **values) -> str:
    with email_svc.request_scope():
        return email_svc.external_url(endpoint, **values)


def on_visual_custom_contracted(event: DomainEvent) -> None:
    """Etapa C (pendência): avisa a equipe da plataforma que há requisição nova no /interno.
    Só com ``STAFF_NOTIFY_EMAIL`` configurado; sem ele o evento é só marcado publicado."""
    to = (current_app.config.get("STAFF_NOTIFY_EMAIL") or "").strip()
    if not to:
        return
    plan = str((event.payload or {}).get("plano") or "")
    _send(to, VISUAL_REQUEST_SUBJECT, "staff_visual_request", plan=plan, url=_url("interno.index"))
