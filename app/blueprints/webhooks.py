"""Webhooks recebidos: ``POST /webhooks/asaas``.

1. Sem CSRF (quem chama é o Asaas), mas com rate limit e corpo pequeno.
2. Header ``asaas-access-token`` comparado em tempo constante (``hmac.compare_digest``)
   com ``ASAAS_WEBHOOK_TOKEN``; sem token configurado ou diferente → 401.
3. ``webhook_events.external_event_id`` (UNIQUE) é gravado e COMMITADO antes de processar:
   evento repetido (o Asaas entrega “pelo menos uma vez”) bate no UNIQUE e responde 200
   sem efeito nenhum.
4. Processa na hora (é rápido: só grava a cobrança e recalcula o estado). Erro no
   processamento fica em ``webhook_events.error``/``status=failed`` e a resposta é 200
   mesmo assim: resposta fora de 2xx faz o Asaas reenviar e, repetida, interromper a fila
   de webhooks da conta. O evento com falha é corrigido por ``flask billing-reconcile``
   (que consulta o Asaas). Payload completo nunca vai para log nem banco.
"""

from __future__ import annotations

import hmac
import logging

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.extensions import csrf, db, limiter
from app.models import WebhookEvent
from app.services.billing import service as billing
from app.services.billing.service import now_utc

logger = logging.getLogger(__name__)

bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")

MAX_BODY = 256 * 1024


def _rate_limit() -> str:
    return current_app.config.get("WEBHOOK_RATE_LIMIT", "120 per minute")


def _authorized() -> bool:
    expected = current_app.config.get("ASAAS_WEBHOOK_TOKEN") or ""
    received = request.headers.get("asaas-access-token", "")
    if not expected:
        logger.error("webhook asaas recusado: ASAAS_WEBHOOK_TOKEN não configurado")
        return False
    return hmac.compare_digest(received.encode("utf-8"), expected.encode("utf-8"))


@bp.post("/asaas")
@csrf.exempt
@limiter.limit(_rate_limit)
def asaas():
    if not _authorized():
        return jsonify({"error": "unauthorized"}), 401
    if (request.content_length or 0) > MAX_BODY:
        return jsonify({"error": "payload too large"}), 413
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload.get("id") or not payload.get("event"):
        return jsonify({"error": "invalid payload"}), 400
    event_id = str(payload["id"])[:100]
    event_type = str(payload["event"])[:80]

    record = WebhookEvent(provider="asaas", external_event_id=event_id, type=event_type, status="received")
    db.session.add(record)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        logger.info("webhook asaas %s %s duplicado: ignorado", event_type, event_id)
        return jsonify({"status": "duplicate"}), 200

    record_id = record.id
    try:
        status, company_id = billing.handle_webhook(payload)
        record = db.session.get(WebhookEvent, record_id)
        record.status = status
        record.company_id = company_id
        record.processed_at = now_utc()
        db.session.commit()
    except Exception as exc:  # noqa: BLE001 - registrado e respondido com 200 (ver docstring)
        db.session.rollback()
        logger.error("webhook asaas %s %s falhou: %s", event_type, event_id, exc.__class__.__name__)
        record = db.session.get(WebhookEvent, record_id)
        record.status = "failed"
        record.error = f"{exc.__class__.__name__}: {getattr(exc, 'message', '')}"[:500]
        record.processed_at = now_utc()
        db.session.commit()
        return jsonify({"status": "failed"}), 200
    return jsonify({"status": status}), 200
