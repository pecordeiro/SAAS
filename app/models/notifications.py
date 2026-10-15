"""Etapa F — worker: marcas de execução das tarefas agendadas e alertas automáticos.

Ambas são dado da empresa (``company_id NOT NULL``, RLS ``tenant_isolation``): o worker grava
cada empresa no contexto dela (ADR-0010).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

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
