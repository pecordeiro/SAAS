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

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Uuid
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
