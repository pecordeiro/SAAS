"""Auditoria mínima das ações de conta/equipe (Fase 5).

Provisório: a Fase 4 cria ``app/services/audit.py``; depois unificamos. Grava em
``audit_logs`` (append-only) na transação corrente — quem chama faz o commit.
Nunca põe token, senha ou segredo em ``details``.
"""

from __future__ import annotations

import uuid

from flask import has_request_context, request
from flask_login import current_user

from app.extensions import db
from app.models import AuditLog


def record(
    company_id: uuid.UUID,
    action: str,
    object_type: str | None = None,
    object_id: uuid.UUID | None = None,
    details: dict | None = None,
    actor_user_id: uuid.UUID | None = None,
) -> AuditLog:
    if actor_user_id is None and has_request_context() and current_user.is_authenticated:
        actor_user_id = current_user.id
    ip = request.remote_addr if has_request_context() else None
    entry = AuditLog(
        company_id=company_id,
        actor_user_id=actor_user_id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        ip=(ip or "")[:45] or None,
        details=details or None,
    )
    db.session.add(entry)
    return entry
