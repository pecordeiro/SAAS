"""Fase 5 — bloqueio progressivo de login (por conta e por IP), persistido no banco."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import Timestamps, UUIDPk, utcnow

THROTTLE_ACCOUNT = "account"
THROTTLE_IP = "ip"


class LoginThrottle(UUIDPk, Timestamps, db.Model):
    """Contador de falhas de login. Plataforma (sem company_id): chega antes de saber a
    empresa. A chave (e-mail normalizado ou IP) é guardada só como SHA-256."""

    __tablename__ = "login_throttles"
    __table_args__ = (
        UniqueConstraint("scope", "key_hash", name="uq_login_throttles_scope_key"),
        CheckConstraint("scope IN ('account', 'ip')", name="scope_valid"),
        CheckConstraint("failures >= 0", name="failures_nonnegative"),
    )

    scope: Mapped[str] = mapped_column(String(10), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failure_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
