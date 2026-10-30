"""Fase 7 — trilha de auditoria da PLATAFORMA (fora das empresas).

``audit_logs`` pertence à empresa e é apagado com ela no expurgo LGPD. O que precisa
sobreviver ao expurgo (prova de que a empresa X foi apagada, quando e quantas linhas) e as
ações de operador sem empresa ficam aqui. Sem dado pessoal: só ids, contagens e motivo.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, Uuid, event
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import UUIDPk, utcnow
from app.models.billing import JSONType


class PlatformAuditLog(UUIDPk, db.Model):
    __tablename__ = "platform_audit_logs"
    __table_args__ = (
        Index("ix_platform_audit_logs_at", "at"),
        Index("ix_platform_audit_logs_subject", "subject_company_id", "at"),
    )

    action: Mapped[str] = mapped_column(String(80), nullable=False)
    # Empresa a que a ação se refere (sem FK: a empresa pode já ter sido apagada).
    subject_company_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    # Quem rodou o comando (texto livre informado ao CLI; não é usuário do site).
    operator: Mapped[str | None] = mapped_column(String(120))
    details: Mapped[dict | None] = mapped_column(JSONType)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


@event.listens_for(PlatformAuditLog, "before_update")
def _no_update(mapper, connection, target):  # pragma: no cover - guarda
    raise RuntimeError("platform_audit_logs é append-only.")


@event.listens_for(PlatformAuditLog, "before_delete")
def _no_delete(mapper, connection, target):  # pragma: no cover - guarda
    raise RuntimeError("platform_audit_logs é append-only.")
