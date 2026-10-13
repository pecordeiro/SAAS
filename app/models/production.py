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
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
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
    __table_args__ = (Index("ix_stages_company_project_position", "company_id", "project_id", "position"),)

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
    """Histórico append-only: nunca é alterado nem apagado."""

    __tablename__ = "progress_entries"
    __table_args__ = (
        Index("ix_progress_entries_company_activity_at", "company_id", "activity_id", "at"),
        Index("ix_progress_entries_company_at", "company_id", "at"),
        CheckConstraint("delta <> 0", name="delta_nonzero"),
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("activities.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    activity: Mapped[Activity] = relationship()
    user = relationship("User")


@event.listens_for(ProgressEntry, "before_update")
def _progress_entry_no_update(mapper, connection, target):  # pragma: no cover - guarda
    raise RuntimeError("progress_entries é append-only: não pode ser alterado.")


@event.listens_for(ProgressEntry, "before_delete")
def _progress_entry_no_delete(mapper, connection, target):  # pragma: no cover - guarda
    raise RuntimeError("progress_entries é append-only: não pode ser apagado.")


class Holiday(UUIDPk, Timestamps, TenantMixin, db.Model):
    __tablename__ = "holidays"
    __table_args__ = (UniqueConstraint("company_id", "day", name="uq_holidays_company_day"),)

    day: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
