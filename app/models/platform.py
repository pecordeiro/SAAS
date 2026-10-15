"""Auditoria, eventos de domínio (outbox) e clientes/tokens da API pública."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, Uuid, event, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import Timestamps, TenantMixin, UUIDPk, utcnow
from app.models.billing import JSONType


class AuditLog(UUIDPk, TenantMixin, db.Model):
    """Trilha de auditoria append-only (quem fez o quê, em qual objeto, de qual IP)."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_company_at", "company_id", "at"),
        Index("ix_audit_logs_company_object", "company_id", "object_type", "object_id"),
    )

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    object_type: Mapped[str | None] = mapped_column(String(40))
    object_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    # IPv4/IPv6 em texto (portável; 45 cobre IPv6 com IPv4 embutido).
    ip: Mapped[str | None] = mapped_column(String(45))
    details: Mapped[dict | None] = mapped_column(JSONType)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


@event.listens_for(AuditLog, "before_update")
def _audit_no_update(mapper, connection, target):  # pragma: no cover - guarda
    raise RuntimeError("audit_logs é append-only: não pode ser alterado.")


@event.listens_for(AuditLog, "before_delete")
def _audit_no_delete(mapper, connection, target):  # pragma: no cover - guarda
    raise RuntimeError("audit_logs é append-only: não pode ser apagado.")


class DomainEvent(UUIDPk, TenantMixin, db.Model):
    """Outbox: gravado na mesma transação da mudança; publicado depois pelo worker."""

    __tablename__ = "domain_events"
    __table_args__ = (
        Index("ix_domain_events_company_created", "company_id", "created_at"),
        # Fila do worker (entre empresas): só as linhas ainda não publicadas.
        Index(
            "ix_domain_events_unpublished",
            "created_at",
            postgresql_where=text("published_at IS NULL"),
            sqlite_where=text("published_at IS NULL"),
        ),
        CheckConstraint("attempts >= 0", name="attempts_nonnegative"),
    )

    type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # Etapa F (worker, ADR-0010): próxima tentativa depois de uma falha (backoff) e o nome da
    # última exceção (nunca a mensagem: pode carregar dado pessoal).
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(200))


class ApiClient(UUIDPk, Timestamps, TenantMixin, db.Model):
    """Integração da empresa com a API pública (fase 9)."""

    __tablename__ = "api_clients"
    __table_args__ = (UniqueConstraint("company_id", "name", name="uq_api_clients_company_name"),)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tokens: Mapped[list["ApiToken"]] = relationship(back_populates="client")


class ApiToken(UUIDPk, Timestamps, TenantMixin, db.Model):
    """Token Bearer: só o SHA-256 vai ao banco; ``token_prefix`` serve para identificar na tela."""

    __tablename__ = "api_tokens"
    __table_args__ = (Index("ix_api_tokens_company_client", "company_id", "api_client_id"),)

    api_client_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("api_clients.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    token_prefix: Mapped[str] = mapped_column(String(12), nullable=False)
    # Lista de escopos, ex.: ["read:projects", "write:progress"].
    scopes: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    client: Mapped[ApiClient] = relationship(back_populates="tokens")
