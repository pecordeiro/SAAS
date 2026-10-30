"""Tipos e mixins comuns aos modelos."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UUIDPk:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class TenantMixin:
    """Dado de cliente: company_id NOT NULL. Índices compostos começam por company_id."""

    @declared_attr
    def company_id(cls) -> Mapped[uuid.UUID]:  # noqa: N805
        return mapped_column(Uuid, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
