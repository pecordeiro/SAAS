"""Etapa G — qualidade: evidências por atividade (comentários e fotos).

Tudo é dado da empresa (``company_id NOT NULL``, RLS ``tenant_isolation``, índices começando
por ``company_id``). Comentário e foto nunca mudam depois de criados; supervisor+ pode apagar
(linha removida + ``audit_logs`` sem o texto/imagem). O arquivo da foto mora no armazenamento
(``services/storage.py``) sob a chave ``<company_id>/fotos/<uuid>.jpg``; a linha guarda só
metadados (nunca o nome original do arquivo enviado).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, Uuid, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import TenantMixin, UUIDPk, utcnow

COMMENT_MAX_CHARS = 1000
PHOTO_CAPTION_MAX = 140


class ActivityComment(UUIDPk, TenantMixin, db.Model):
    __tablename__ = "activity_comments"
    __table_args__ = (
        Index("ix_activity_comments_company_activity_at", "company_id", "activity_id", "created_at"),
        CheckConstraint("length(body) >= 1", name="body_not_empty"),
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("activities.id", ondelete="RESTRICT"), nullable=False)
    body: Mapped[str] = mapped_column(String(COMMENT_MAX_CHARS), nullable=False)
    author_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    activity = relationship("Activity")
    author = relationship("User")


class ActivityPhoto(UUIDPk, TenantMixin, db.Model):
    """Foto de evidência (montagem / não conformidade). ``id`` também é o nome do objeto."""

    __tablename__ = "activity_photos"
    __table_args__ = (
        Index("ix_activity_photos_company_activity_at", "company_id", "activity_id", "created_at"),
        CheckConstraint("size_bytes > 0", name="size_positive"),
        CheckConstraint("width > 0 AND height > 0", name="dimensions_positive"),
        CheckConstraint("content_type = 'image/jpeg'", name="content_type_jpeg"),
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("activities.id", ondelete="RESTRICT"), nullable=False)
    object_key: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    thumb_key: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False, default="image/jpeg")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    # SHA-256 da imagem GUARDADA (já reencodada): confere integridade na leitura.
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    caption: Mapped[str | None] = mapped_column(String(PHOTO_CAPTION_MAX))
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    activity = relationship("Activity")
    uploaded_by = relationship("User")


# ---------------------------------------------------------------- checklist de inspeção (bloco 2)
#
# Itens definidos no MODELO (template_checklist_items, por etapa do modelo, versionados junto com
# a versão) e COPIADOS ao projeto (stage_checklist_items) na criação. Supervisor+ define/arquiva
# itens; operador+ preenche e assina. Assinatura = usuário autenticado + data/hora gravados pelo
# servidor. Depois de assinada, uma resposta só muda por CORREÇÃO: nova linha com
# ``supersedes_id`` (UNIQUE) e motivo; a antiga fica (guarda ORM + ``locked_at``).

CHECKLIST_ITEM_MAX = 200
CHECKLIST_NOTE_MAX = 500
RESULT_OK = "ok"
RESULT_NONCONFORMING = "nonconforming"
RESULT_NA = "na"
RESULTS = (RESULT_OK, RESULT_NONCONFORMING, RESULT_NA)
INSPECTION_DRAFT = "draft"
INSPECTION_SIGNED = "signed"


class TemplateChecklistItem(UUIDPk, TenantMixin, db.Model):
    __tablename__ = "template_checklist_items"
    __table_args__ = (
        Index("ix_template_checklist_items_company_stage_position", "company_id", "template_stage_id", "position"),
        CheckConstraint("position >= 0", name="position_nonnegative"),
    )

    template_stage_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("template_stages.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(String(CHECKLIST_ITEM_MAX), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    stage = relationship("TemplateStage", back_populates="checklist_items")


class StageChecklistItem(UUIDPk, TenantMixin, db.Model):
    """Item do checklist da etapa do PROJETO. Não se edita; arquiva (respostas antigas ficam)."""

    __tablename__ = "stage_checklist_items"
    __table_args__ = (
        Index("ix_stage_checklist_items_company_stage_position", "company_id", "stage_id", "position"),
        CheckConstraint("position >= 0", name="position_nonnegative"),
    )

    stage_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("stages.id", ondelete="RESTRICT"), nullable=False)
    text: Mapped[str] = mapped_column(String(CHECKLIST_ITEM_MAX), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    stage = relationship("Stage")


class StageInspection(UUIDPk, TenantMixin, db.Model):
    """Uma inspeção (preenchimento do checklist) da etapa. ``draft`` → ``signed`` (uma vez)."""

    __tablename__ = "stage_inspections"
    __table_args__ = (
        Index("ix_stage_inspections_company_stage_created", "company_id", "stage_id", "created_at"),
        Index("ix_stage_inspections_company_unit", "company_id", "unit_id"),
        CheckConstraint("status IN ('draft', 'signed')", name="status_valid"),
        CheckConstraint(
            "status <> 'signed' OR (signed_at IS NOT NULL AND signed_by_id IS NOT NULL)", name="signed_has_signature"
        ),
        CheckConstraint("version >= 1", name="version_positive"),
    )

    stage_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("stages.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=INSPECTION_DRAFT)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    # Assinatura: quem estava autenticado e quando (relógio do servidor). Nunca vem do formulário.
    signed_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Bloco 3: inspeção de uma unidade (número de série) — opcional.
    unit_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("units.id", ondelete="RESTRICT"))

    stage = relationship("Stage")
    unit = relationship("Unit")
    created_by = relationship("User", foreign_keys=[created_by_id])
    signed_by = relationship("User", foreign_keys=[signed_by_id])


class InspectionAnswer(UUIDPk, TenantMixin, db.Model):
    """Resposta a um item. Rascunho: a linha é atualizada. Assinada (``locked_at``): imutável —
    mudar = nova linha com ``supersedes_id`` + ``correction_reason`` (a antiga fica)."""

    __tablename__ = "inspection_answers"
    __table_args__ = (
        Index("ix_inspection_answers_company_inspection_item", "company_id", "inspection_id", "item_id"),
        CheckConstraint("result IN ('ok', 'nonconforming', 'na')", name="result_valid"),
        CheckConstraint("supersedes_id IS NULL OR correction_reason IS NOT NULL", name="correction_has_reason"),
    )

    inspection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("stage_inspections.id", ondelete="RESTRICT"), nullable=False
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("stage_checklist_items.id", ondelete="RESTRICT"), nullable=False
    )
    result: Mapped[str] = mapped_column(String(15), nullable=False)
    note: Mapped[str | None] = mapped_column(String(CHECKLIST_NOTE_MAX))
    answered_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("inspection_answers.id", ondelete="RESTRICT"), unique=True
    )
    correction_reason: Mapped[str | None] = mapped_column(String(CHECKLIST_NOTE_MAX))

    inspection = relationship("StageInspection")
    item = relationship("StageChecklistItem")
    answered_by = relationship("User")

    @property
    def is_correction(self) -> bool:
        return self.correction_reason is not None


def _locked_before(target) -> bool:
    from sqlalchemy import inspect as sa_inspect

    history = sa_inspect(target).attrs.locked_at.history
    previous = history.deleted[0] if history.deleted else (history.unchanged[0] if history.unchanged else None)
    return previous is not None


@event.listens_for(InspectionAnswer, "before_update")
def _answer_locked_no_update(mapper, connection, target):
    if _locked_before(target):
        raise RuntimeError("Resposta assinada não muda: registre uma correção (nova linha).")


@event.listens_for(InspectionAnswer, "before_delete")
def _answer_locked_no_delete(mapper, connection, target):
    if _locked_before(target):
        raise RuntimeError("Resposta assinada não pode ser apagada.")


# ---------------------------------------------------------------- unidades / número de série (bloco 3)
#
# Rastreabilidade: cada equipamento do projeto pode ter um número de série. NÃO muda o cálculo —
# o progresso continua vindo de ``activities.units_done`` (calc.py). Lançamentos de peça e
# inspeções podem apontar para a unidade (``unit_id`` opcional).

UNIT_SERIAL_MAX = 60
UNIT_IN_PROGRESS = "in_progress"
UNIT_DONE = "done"
UNIT_SHIPPED = "shipped"
UNIT_SCRAPPED = "scrapped"
UNIT_STATUSES = (UNIT_IN_PROGRESS, UNIT_DONE, UNIT_SHIPPED, UNIT_SCRAPPED)


class Unit(UUIDPk, TenantMixin, db.Model):
    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint("company_id", "project_id", "serial", name="uq_units_company_project_serial"),
        Index("ix_units_company_serial", "company_id", "serial"),
        CheckConstraint("status IN ('in_progress', 'done', 'shipped', 'scrapped')", name="status_valid"),
        CheckConstraint("length(serial) >= 1", name="serial_not_empty"),
        CheckConstraint("version >= 1", name="version_positive"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    serial: Mapped[str] = mapped_column(String(UNIT_SERIAL_MAX), nullable=False)
    status: Mapped[str] = mapped_column(String(15), nullable=False, default=UNIT_IN_PROGRESS)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    project = relationship("Project")
