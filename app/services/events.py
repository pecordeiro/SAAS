"""Eventos de domínio (outbox).

``emit`` só ADICIONA a linha em ``domain_events`` na sessão atual: ela é gravada no mesmo
commit da mudança (ou some junto num rollback). Nada consome os eventos no MVP; o worker da
Fase 9 lê ``published_at IS NULL`` e entrega aos webhooks de saída.

O payload leva só ids e números (nada de nome de pessoa ou e-mail).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.extensions import db
from app.models import DomainEvent

PROJECT_CREATED = "project.created"
ACTIVITY_PROGRESS_UPDATED = "activity.progress_updated"
STAGE_COMPLETED = "stage.completed"
PROJECT_COMPLETED = "project.completed"
EVENT_TYPES = (PROJECT_CREATED, ACTIVITY_PROGRESS_UPDATED, STAGE_COMPLETED, PROJECT_COMPLETED)


def _jsonable(value):
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def emit(company_id: uuid.UUID, event_type: str, payload: dict | None = None) -> DomainEvent:
    """Adiciona o evento à transação corrente (sem commit)."""
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Tipo de evento desconhecido: {event_type!r}")
    event = DomainEvent(company_id=company_id, type=event_type, payload=_jsonable(payload or {}))
    db.session.add(event)
    return event
