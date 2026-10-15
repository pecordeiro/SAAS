"""Etapa F — worker: marcas de execução das tarefas agendadas e alertas automáticos.

Ambas são dado da empresa (``company_id NOT NULL``, RLS ``tenant_isolation``): o worker grava
cada empresa no contexto dela (ADR-0010).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import TenantMixin, UUIDPk, utcnow
from app.models.billing import JSONType


class JobRun(UUIDPk, TenantMixin, db.Model):
    """Marca “esta tarefa já rodou para esta empresa neste período” (idempotência).

    Ex.: ``job="weekly_report"``, ``period_key="2026-W42"``. A UNIQUE impede repetir mesmo com
    dois workers ao mesmo tempo (o segundo recebe IntegrityError e desiste)."""

    __tablename__ = "job_runs"
    __table_args__ = (UniqueConstraint("company_id", "job", "period_key", name="uq_job_runs_company_job_period"),)

    job: Mapped[str] = mapped_column(String(40), nullable=False)
    period_key: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    details: Mapped[dict | None] = mapped_column(JSONType)


ALERT_DEADLINE_RISK = "deadline_risk"
ALERT_FORECAST_LATE = "forecast_late"
ALERT_STAGE_STALLED = "stage_stalled"
ALERT_PART_OVERDUE = "part_overdue"
ALERT_KINDS = (ALERT_DEADLINE_RISK, ALERT_FORECAST_LATE, ALERT_STAGE_STALLED, ALERT_PART_OVERDUE)
ALERT_SEVERITIES = ("warning", "danger")


class Alert(UUIDPk, TenantMixin, db.Model):
    """Alerta automático (prazo em risco, atraso previsto, etapa parada, peça atrasada).

    Gerado pelo worker a partir de ``calc.alertas_projeto`` (regra pura). Dedupe por
    ``(company_id, dedupe_key, day)``: a mesma situação gera no máximo um alerta por dia (dia
    local da empresa). ``details`` leva só números e datas (nada de nome de pessoa)."""

    __tablename__ = "alerts"
    __table_args__ = (
        UniqueConstraint("company_id", "dedupe_key", "day", name="uq_alerts_company_key_day"),
        Index("ix_alerts_company_day", "company_id", "day"),
        Index("ix_alerts_company_project", "company_id", "project_id"),
        CheckConstraint(
            "kind IN ('deadline_risk', 'forecast_late', 'stage_stalled', 'part_overdue')", name="kind_valid"
        ),
        CheckConstraint("severity IN ('warning', 'danger')", name="severity_valid"),
    )

    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(120), nullable=False)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    stage_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("stages.id", ondelete="CASCADE"))
    details: Mapped[dict | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    emailed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project = relationship("Project")
    stage = relationship("Stage")
