"""Projetos, etapas, atividades, registros de progresso e feriados."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    event,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import Timestamps, TenantMixin, UUIDPk, utcnow

PROJECT_ACTIVE = "active"
PROJECT_DONE = "done"
PROJECT_STATUSES = (PROJECT_ACTIVE, PROJECT_DONE)


class Project(UUIDPk, Timestamps, TenantMixin, db.Model):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_company_status", "company_id", "status"),
        Index("ix_projects_company_created", "company_id", "created_at"),
        CheckConstraint("quantity >= 0", name="quantity_nonnegative"),
        CheckConstraint("people >= 1", name="people_positive"),
        CheckConstraint("hours_per_day > 0", name="hours_per_day_positive"),
        CheckConstraint("status IN ('active', 'done')", name="status_valid"),
    )

    # Modelo de origem (snapshot): as etapas foram COPIADAS desta versão na criação.
    template_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("template_versions.id", ondelete="RESTRICT")
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    product: Mapped[str | None] = mapped_column(String(160))  # Fase 6: subtítulo opcional
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    people: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    hours_per_day: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), nullable=False, default=Decimal("8"), server_default="8"
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=PROJECT_ACTIVE)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    stages: Mapped[list["Stage"]] = relationship(
        back_populates="project", order_by="Stage.position"
    )


class Stage(UUIDPk, Timestamps, TenantMixin, db.Model):
    __tablename__ = "stages"
    __table_args__ = (
        Index("ix_stages_company_project_position", "company_id", "project_id", "position"),
        CheckConstraint("position >= 0", name="position_nonnegative"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project] = relationship(back_populates="stages")
    activities: Mapped[list["Activity"]] = relationship(
        back_populates="stage", order_by="Activity.position"
    )


class Activity(UUIDPk, Timestamps, TenantMixin, db.Model):
    __tablename__ = "activities"
    __table_args__ = (
        Index("ix_activities_company_stage_position", "company_id", "stage_id", "position"),
        CheckConstraint("ideal_minutes >= 0", name="ideal_minutes_nonnegative"),
        CheckConstraint("units_done >= 0", name="units_done_nonnegative"),
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint("position >= 0", name="position_nonnegative"),
    )

    stage_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("stages.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    ideal_minutes: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    units_done: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # Controle otimista de concorrência: cada registro incrementa a versão.
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    stage: Mapped[Stage] = relationship(back_populates="activities")


class ProgressEntry(UUIDPk, TenantMixin, db.Model):
    """Histórico append-only: nunca é alterado nem apagado.

    Desfazer (D13, Fase 4) grava um lançamento COMPENSATÓRIO: delta negativo e
    ``reverts_entry_id`` apontando para o registro desfeito (UNIQUE: desfaz uma vez só).
    """

    __tablename__ = "progress_entries"
    __table_args__ = (
        Index("ix_progress_entries_company_activity_at", "company_id", "activity_id", "at"),
        Index("ix_progress_entries_company_at", "company_id", "at"),
        CheckConstraint("delta <> 0", name="delta_nonzero"),
        CheckConstraint("reverts_entry_id IS NULL OR delta < 0", name="reversal_negative"),
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("activities.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    reverts_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("progress_entries.id", ondelete="RESTRICT"), unique=True
    )

    activity: Mapped[Activity] = relationship()
    user = relationship("User")


@event.listens_for(ProgressEntry, "before_update")
def _progress_entry_no_update(mapper, connection, target):  # pragma: no cover - guarda
    raise RuntimeError("progress_entries é append-only: não pode ser alterado.")


@event.listens_for(ProgressEntry, "before_delete")
def _progress_entry_no_delete(mapper, connection, target):  # pragma: no cover - guarda
    raise RuntimeError("progress_entries é append-only: não pode ser apagado.")


class Holiday(UUIDPk, Timestamps, db.Model):
    """Feriado. ``company_id`` NULL = feriado nacional (compartilhado, só leitura para as
    empresas; gravado por `flask seed-holidays`). Com ``company_id`` = feriado da empresa.

    Decisão da Fase 3 (pendência da Fase 0): linha global em vez de copiar os nacionais para
    cada empresa — um único lugar para corrigir, sem N cópias. A política RLS permite ler as
    linhas com company_id NULL e só gravar as da própria empresa.
    """

    __tablename__ = "holidays"
    __table_args__ = (
        UniqueConstraint("company_id", "day", name="uq_holidays_company_day"),
        # NULL não colide em UNIQUE: os nacionais têm índice único parcial próprio.
        Index(
            "uq_holidays_national_day",
            "day",
            unique=True,
            postgresql_where=text("company_id IS NULL"),
            sqlite_where=text("company_id IS NULL"),
        ),
    )

    company_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("companies.id", ondelete="RESTRICT"))
    day: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    @property
    def national(self) -> bool:
        return self.company_id is None
