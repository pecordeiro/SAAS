"""Planos, assinaturas, cobranças e webhooks recebidos (Asaas via PaymentProvider)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import Timestamps, TenantMixin, UUIDPk, utcnow

# JSON portátil: JSONB no PostgreSQL, JSON (texto) no SQLite.
JSONType = JSON().with_variant(JSONB(), "postgresql")

PROVIDERS = ("asaas", "fake")

SUB_TRIALING = "trialing"
SUB_ACTIVE = "active"
SUB_PAST_DUE = "past_due"
SUB_CANCELED = "canceled"
SUB_EXPIRED = "expired"
SUBSCRIPTION_STATUSES = (SUB_TRIALING, SUB_ACTIVE, SUB_PAST_DUE, SUB_CANCELED, SUB_EXPIRED)

PAYMENT_STATUSES = ("pending", "confirmed", "received", "overdue", "refunded", "canceled")

WEBHOOK_STATUSES = ("received", "processed", "ignored", "failed")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"


class Plan(UUIDPk, Timestamps, db.Model):
    """Catálogo de planos (global, sem company_id). Seed: migration + `flask seed-plans`."""

    __tablename__ = "plans"
    __table_args__ = (
        CheckConstraint("price_cents >= 0", name="price_nonnegative"),
        CheckConstraint("max_projects IS NULL OR max_projects >= 0", name="max_projects_nonnegative"),
        CheckConstraint("max_users IS NULL OR max_users >= 1", name="max_users_positive"),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    # NULL = ilimitado.
    max_projects: Mapped[int | None] = mapped_column(Integer)
    max_users: Mapped[int | None] = mapped_column(Integer)
    features: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))


class Subscription(UUIDPk, Timestamps, TenantMixin, db.Model):
    """Assinatura da empresa (no máximo uma por empresa)."""

    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("company_id", name="uq_subscriptions_company"),
        UniqueConstraint("provider", "provider_subscription_id", name="uq_subscriptions_provider_subscription"),
        Index("ix_subscriptions_status_period_end", "status", "current_period_end"),
        CheckConstraint(_in("status", SUBSCRIPTION_STATUSES), name="status_valid"),
        CheckConstraint(_in("provider", PROVIDERS), name="provider_valid"),
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_customer_id: Mapped[str | None] = mapped_column(String(64))
    provider_subscription_id: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=SUB_TRIALING)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    grace_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    plan: Mapped[Plan] = relationship()


class Payment(UUIDPk, Timestamps, TenantMixin, db.Model):
    """Cobrança. company_id é redundante com a assinatura de propósito: isolamento e RLS
    diretos, sem depender de JOIN."""

    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_company_due", "company_id", "due_date"),
        Index("ix_payments_subscription", "subscription_id"),
        CheckConstraint(_in("status", PAYMENT_STATUSES), name="status_valid"),
        CheckConstraint("value_cents >= 0", name="value_nonnegative"),
    )

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("subscriptions.id", ondelete="RESTRICT"), nullable=False
    )
    provider_payment_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    value_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class WebhookEvent(UUIDPk, db.Model):
    """Caixa de entrada de webhooks (plataforma, sem RLS): o id externo é gravado com
    UNIQUE ANTES de processar, então o mesmo evento nunca é processado duas vezes."""

    __tablename__ = "webhook_events"
    __table_args__ = (
        Index("ix_webhook_events_status_received", "status", "received_at"),
        CheckConstraint(_in("status", WEBHOOK_STATUSES), name="status_valid"),
        CheckConstraint(_in("provider", PROVIDERS), name="provider_valid"),
    )

    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_event_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    # Preenchido depois de identificar a assinatura (opcional).
    company_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("companies.id", ondelete="SET NULL"))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="received")
    error: Mapped[str | None] = mapped_column(Text)
