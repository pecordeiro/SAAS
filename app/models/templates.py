"""Modelos de etapas (templates) versionados.

Um modelo (``templates``) tem versões imutáveis (``template_versions``); cada versão tem
etapas e atividades com tempo ideal. Criar um projeto COPIA as etapas/atividades da versão
para ``stages``/``activities`` (snapshot) e guarda ``projects.template_version_id``. Editar o
modelo cria nova versão; o projeto só muda com confirmação explícita (Fase 4).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import Timestamps, TenantMixin, UUIDPk


class Template(UUIDPk, Timestamps, TenantMixin, db.Model):
    __tablename__ = "templates"
    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_templates_company_name"),
        Index("ix_templates_company_archived", "company_id", "archived_at"),
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Versão em uso para novos projetos. FK criada depois das duas tabelas (ciclo).
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey(
            "template_versions.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_templates_current_version_id_template_versions",
        ),
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    versions: Mapped[list["TemplateVersion"]] = relationship(
        back_populates="template",
        foreign_keys="TemplateVersion.template_id",
        order_by="TemplateVersion.number",
    )
    current_version: Mapped["TemplateVersion | None"] = relationship(
        foreign_keys=[current_version_id], post_update=True
    )


class TemplateVersion(UUIDPk, Timestamps, TenantMixin, db.Model):
    __tablename__ = "template_versions"
    __table_args__ = (
        UniqueConstraint("company_id", "template_id", "number", name="uq_template_versions_company_template_number"),
        CheckConstraint("number >= 1", name="number_positive"),
    )

    template_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("templates.id", ondelete="RESTRICT"), nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))

    template: Mapped[Template] = relationship(back_populates="versions", foreign_keys=[template_id])
    stages: Mapped[list["TemplateStage"]] = relationship(
        back_populates="version", order_by="TemplateStage.position"
    )


class TemplateStage(UUIDPk, Timestamps, TenantMixin, db.Model):
    __tablename__ = "template_stages"
    __table_args__ = (
        Index("ix_template_stages_company_version_position", "company_id", "template_version_id", "position"),
        CheckConstraint("position >= 0", name="position_nonnegative"),
    )

    template_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("template_versions.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    version: Mapped[TemplateVersion] = relationship(back_populates="stages")
    activities: Mapped[list["TemplateActivity"]] = relationship(
        back_populates="stage", order_by="TemplateActivity.position"
    )


class TemplateActivity(UUIDPk, Timestamps, TenantMixin, db.Model):
    __tablename__ = "template_activities"
    __table_args__ = (
        Index("ix_template_activities_company_stage_position", "company_id", "template_stage_id", "position"),
        CheckConstraint("ideal_minutes >= 0", name="ideal_minutes_nonnegative"),
        CheckConstraint("position >= 0", name="position_nonnegative"),
    )

    template_stage_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("template_stages.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    # Tempo ideal por unidade, em minutos (mesma regra de activities.ideal_minutes).
    ideal_minutes: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    stage: Mapped[TemplateStage] = relationship(back_populates="activities")
