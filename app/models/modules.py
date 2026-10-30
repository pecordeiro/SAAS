"""R6 — módulos opcionais por empresa (ADR-0017).

Uma linha por empresa e módulo que alguém já ligou ou desligou. Sem linha = DESLIGADO: empresa
nova vê só o núcleo (etapas). O catálogo de módulos (chaves, nomes, rotas) mora em
``app/services/modules.py``; aqui só a persistência. Dado da empresa: ``company_id NOT NULL`` e
RLS ``tenant_isolation`` (migration f1a7c3e9b2d4).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import TenantMixin, UUIDPk, utcnow


class CompanyModule(UUIDPk, TenantMixin, db.Model):
    __tablename__ = "company_modules"
    __table_args__ = (
        UniqueConstraint("company_id", "module", name="uq_company_modules_company_module"),
        CheckConstraint("length(module) >= 1", name="module_not_empty"),
    )

    module: Mapped[str] = mapped_column(String(30), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    # Quem mudou por último (NULL = migration ou pessoa já removida). O histórico fica em audit_logs.
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))
