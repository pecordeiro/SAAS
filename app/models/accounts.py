"""Empresas, usuários e vínculos."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from flask_login import UserMixin
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import Timestamps, TenantMixin, UUIDPk

ROLE_OWNER = "owner"
ROLE_SUPERVISOR = "supervisor"
ROLE_OPERATOR = "operator"
ROLES = (ROLE_OWNER, ROLE_SUPERVISOR, ROLE_OPERATOR)
ROLE_LEVEL = {ROLE_OPERATOR: 1, ROLE_SUPERVISOR: 2, ROLE_OWNER: 3}
ROLE_LABELS = {ROLE_OWNER: "Proprietário", ROLE_SUPERVISOR: "Supervisor", ROLE_OPERATOR: "Operador"}

# Bits de dias úteis: segunda = bit 0 ... domingo = bit 6. 31 = segunda a sexta.
WORKDAYS_MON_FRI = 0b0011111


class Company(UUIDPk, Timestamps, db.Model):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(18))
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="America/Sao_Paulo")
    daily_hours: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("8"))
    workdays_mask: Mapped[int] = mapped_column(Integer, nullable=False, default=WORKDAYS_MON_FRI)

    memberships: Mapped[list["Membership"]] = relationship(back_populates="company")

    def workdays(self) -> tuple[int, ...]:
        return tuple(d for d in range(7) if self.workdays_mask & (1 << d))


class User(UUIDPk, Timestamps, UserMixin, db.Model):
    __tablename__ = "users"

    # Guardado sempre em minúsculas (citext no PostgreSQL fica para a Fase 3).
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    session_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    memberships: Mapped[list["Membership"]] = relationship(back_populates="user")

    # Flask-Login: o id da sessão carrega a versão, então trocar session_version
    # derruba todas as sessões abertas do usuário.
    def get_id(self) -> str:
        return f"{self.id}:{self.session_version}"

    @property
    def is_active(self) -> bool:  # type: ignore[override]
        return bool(self.active)


class Membership(UUIDPk, Timestamps, TenantMixin, db.Model):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("company_id", "user_id", name="uq_memberships_company_user"),
        Index("ix_memberships_company_role", "company_id", "role"),
        Index("ix_memberships_user", "user_id"),
        CheckConstraint("role IN ('owner', 'supervisor', 'operator')", name="role_valid"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    company: Mapped[Company] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")

    @property
    def level(self) -> int:
        return ROLE_LEVEL.get(self.role, 0)

    def has_role(self, min_role: str) -> bool:
        return self.level >= ROLE_LEVEL[min_role]
