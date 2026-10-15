"""Etapa C — dados da PLATAFORMA acompanhados pela equipe (painel ``/interno``).

``visual_requests``: requisição de identidade visual aberta quando a empresa contrata um plano
com ``visual_custom`` (Empresa, Implantação). É dado da plataforma, não da empresa: só a equipe
(``User.is_staff`` + MFA) lê e muda; a empresa não tem tela nem rota para ela. ``company_id`` é
nullable e sem FK de propósito (fica fora do RLS por empresa, como ``platform_audit_logs``),
mas o expurgo LGPD apaga as linhas da empresa (``lgpd.company_tables``).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import UUIDPk, utcnow

VISUAL_NEW = "new"
VISUAL_IN_PROGRESS = "in_progress"
VISUAL_DELIVERED = "delivered"
VISUAL_STATUSES = (VISUAL_NEW, VISUAL_IN_PROGRESS, VISUAL_DELIVERED)


class VisualRequest(UUIDPk, db.Model):
    __tablename__ = "visual_requests"
    __table_args__ = (
        Index("ix_visual_requests_company", "company_id"),
        Index("ix_visual_requests_status_created", "status", "created_at"),
        CheckConstraint("status IN ('new', 'in_progress', 'delivered')", name="status_valid"),
    )

    company_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    company_name: Mapped[str] = mapped_column(String(120), nullable=False)
    plan_code: Mapped[str] = mapped_column(String(40), nullable=False)
    # Contato do proprietário no momento da contratação (cópia: o painel não lê a empresa).
    contact_name: Mapped[str | None] = mapped_column(String(120))
    contact_email: Mapped[str | None] = mapped_column(String(254))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=VISUAL_NEW)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_by: Mapped[str | None] = mapped_column(String(254))
