"""Empresas, usuários e vínculos."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from flask_login import UserMixin
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    and_,
    func,
    or_,
    text,
)
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


# CHECK de papel reaproveitado em memberships e invitations.
ROLES_SQL = "role IN ('owner', 'supervisor', 'operator')"


class Company(UUIDPk, Timestamps, db.Model):
    """Raiz do tenant: o próprio id é o company_id das demais tabelas (sem RLS própria)."""

    __tablename__ = "companies"
    __table_args__ = (
        CheckConstraint("daily_hours > 0 AND daily_hours <= 24", name="daily_hours_range"),
        CheckConstraint("workdays_mask BETWEEN 0 AND 127", name="workdays_mask_range"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(18))
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="America/Sao_Paulo")
    daily_hours: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("8"))
    workdays_mask: Mapped[int] = mapped_column(Integer, nullable=False, default=WORKDAYS_MON_FRI)
    # Fase 5: MFA obrigatório para owner quando ligado (só nos planos com a feature).
    mfa_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    # LGPD: pedido de exclusão; o worker apaga depois do prazo de carência.
    deletion_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    memberships: Mapped[list["Membership"]] = relationship(back_populates="company")

    def workdays(self) -> tuple[int, ...]:
        return tuple(d for d in range(7) if self.workdays_mask & (1 << d))


class User(UUIDPk, Timestamps, UserMixin, db.Model):
    """Identidade global (um usuário pode ter vínculo com várias empresas): sem company_id."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    session_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Fase 5 (MFA TOTP): segredo cifrado pela aplicação, nunca em claro.
    totp_secret_enc: Mapped[str | None] = mapped_column(String(255))
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    # Fase 5: último passo TOTP aceito (impede reusar o mesmo código de 30 s) e último acesso.
    totp_last_step: Mapped[int | None] = mapped_column(Integer)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    memberships: Mapped[list["Membership"]] = relationship(back_populates="user")

    # Flask-Login: o id da sessão carrega a versão, então trocar session_version
    # derruba todas as sessões abertas do usuário.
    def get_id(self) -> str:
        return f"{self.id}:{self.session_version}"

    @property
    def is_active(self) -> bool:  # type: ignore[override]
        return bool(self.active)


# E-mail case-insensitive no banco (decisão da Fase 3: índice único em lower(email), igual
# no PostgreSQL e no SQLite, em vez de citext). A aplicação já grava em minúsculas; o índice
# impede duplicata "Maria@x" × "maria@x" mesmo se algum caminho esquecer de normalizar.
Index("uq_users_email_lower", func.lower(User.email), unique=True)


class Membership(UUIDPk, Timestamps, TenantMixin, db.Model):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("company_id", "user_id", name="uq_memberships_company_user"),
        Index("ix_memberships_company_role", "company_id", "role"),
        Index("ix_memberships_user", "user_id"),
        CheckConstraint(ROLES_SQL, name="role_valid"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Fase 7 — acesso de suporte da plataforma (flask suporte conceder): vínculo temporário,
    # nunca owner, não conta no limite do plano e deixa de valer sozinho em expires_at.
    is_support: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    company: Mapped[Company] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")

    @property
    def level(self) -> int:
        return ROLE_LEVEL.get(self.role, 0)

    def has_role(self, min_role: str) -> bool:
        return self.level >= ROLE_LEVEL[min_role]

    @classmethod
    def usable(cls, now: datetime | None = None):
        """Condição SQL de vínculo que vale agora: ativo e (sem validade ou ainda no prazo)."""
        from app.models.base import utcnow

        now = now or utcnow()
        return and_(cls.active.is_(True), or_(cls.expires_at.is_(None), cls.expires_at > now))


class Invitation(UUIDPk, Timestamps, TenantMixin, db.Model):
    """Convite para entrar na empresa. Só o SHA-256 do token vai ao banco."""

    __tablename__ = "invitations"
    __table_args__ = (
        Index("ix_invitations_company_email", "company_id", "email"),
        Index("ix_invitations_company_created", "company_id", "created_at"),
        CheckConstraint(ROLES_SQL, name="role_valid"),
        CheckConstraint("email = lower(email)", name="email_lowercase"),
    )

    email: Mapped[str] = mapped_column(String(254), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    invited_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class _UserToken(UUIDPk, Timestamps):
    """Token de uso único ligado ao usuário (global, sem company_id): só o hash é guardado."""

    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PasswordReset(_UserToken, db.Model):
    __tablename__ = "password_resets"
    __table_args__ = (Index("ix_password_resets_user_created", "user_id", "created_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


class EmailConfirmation(_UserToken, db.Model):
    __tablename__ = "email_confirmations"
    __table_args__ = (Index("ix_email_confirmations_user_created", "user_id", "created_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # E-mail que está sendo confirmado (permite trocar de e-mail com confirmação).
    email: Mapped[str] = mapped_column(String(254), nullable=False)


class MfaRecoveryCode(UUIDPk, Timestamps, db.Model):
    """Códigos de recuperação do MFA (hash Argon2/SHA-256; uso único)."""

    __tablename__ = "mfa_recovery_codes"
    __table_args__ = (UniqueConstraint("user_id", "code_hash", name="uq_mfa_recovery_codes_user_code"),)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
