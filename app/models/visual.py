"""ADR-0019 §2–3 — briefing de identidade visual e agendamento da ligação.

Dado DA EMPRESA (``company_id NOT NULL`` + RLS ``tenant_isolation``, migration c5a1e9d7b3f2):
- ``visual_briefings``: um briefing por empresa, preenchido só pelo proprietário. Ligado à
  requisição da plataforma (``visual_requests``) por ``visual_request_id`` (sem FK: a requisição é
  dado da plataforma, fora do RLS por empresa — mesmo padrão de ``visual_requests.company_id``).
- ``visual_briefing_files``: logo e fotos de produto. Os bytes ficam no armazenamento privado
  (``storage.briefing_key``: prefixo da empresa, uuid gerado aqui), nunca em pasta pública.
- ``call_bookings``: a reserva da ligação. UNIQUE em ``slot_id`` (duas empresas nunca reservam o
  mesmo horário, nem em concorrência: a segunda inserção viola a restrição) e UNIQUE em
  ``company_id`` (uma reserva por empresa de cada vez).

Dado DA PLATAFORMA (sem ``company_id``, sem RLS; só a equipe cria e remove em ``/interno``):
- ``call_slots``: horários oferecidos, guardados em UTC (exibidos em America/Sao_Paulo). O RLS
  esconde as reservas das outras empresas, então o horário carrega uma marca de ocupado
  (``booked_at``) e, para o painel não ler tabela de empresa, uma CÓPIA do contato da ligação e do
  pedido de mudança — o mesmo padrão de ``visual_requests.contact_*``. O expurgo LGPD limpa essa
  cópia (``services/agenda.release_company``).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import TenantMixin, UUIDPk, utcnow

TONE_FORMAL = "formal"
TONE_NEUTRAL = "neutro"
TONE_CASUAL = "descontraido"
TONES = (TONE_FORMAL, TONE_NEUTRAL, TONE_CASUAL)

FILE_LOGO = "logo"
FILE_PRODUCT = "produto"
FILE_KINDS = (FILE_LOGO, FILE_PRODUCT)

CHANGE_CANCEL = "cancelar"
CHANGE_RESCHEDULE = "remarcar"
CHANGE_KINDS = (CHANGE_CANCEL, CHANGE_RESCHEDULE)

# Tamanhos (o formulário e o serviço usam os mesmos números).
NAME_MAX = 120
PRODUCTS_MAX = 1000
PREFS_MAX = 300
SITES_MAX_CHARS = 1600
PHONE_MAX = 30
EMAIL_MAX = 254


class VisualBriefing(UUIDPk, TenantMixin, db.Model):
    __tablename__ = "visual_briefings"
    __table_args__ = (
        UniqueConstraint("company_id"),
        CheckConstraint("tone IS NULL OR tone IN ('formal', 'neutro', 'descontraido')", name="tone_valid"),
    )

    visual_request_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    company_name: Mapped[str | None] = mapped_column(String(NAME_MAX))
    products: Mapped[str | None] = mapped_column(Text)
    colors: Mapped[str | None] = mapped_column(String(PREFS_MAX))
    fonts: Mapped[str | None] = mapped_column(String(PREFS_MAX))
    # Um endereço por linha (validados no serviço: http/https, tamanho e quantidade).
    reference_sites: Mapped[str | None] = mapped_column(Text)
    tone: Mapped[str | None] = mapped_column(String(20))
    contact_name: Mapped[str | None] = mapped_column(String(NAME_MAX))
    contact_phone: Mapped[str | None] = mapped_column(String(PHONE_MAX))
    contact_email: Mapped[str | None] = mapped_column(String(EMAIL_MAX))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))

    files = relationship("VisualBriefingFile", back_populates="briefing", order_by="VisualBriefingFile.created_at")


class VisualBriefingFile(UUIDPk, TenantMixin, db.Model):
    __tablename__ = "visual_briefing_files"
    __table_args__ = (
        Index("ix_visual_briefing_files_company_briefing", "company_id", "briefing_id"),
        CheckConstraint("kind IN ('logo', 'produto')", name="kind_valid"),
        CheckConstraint("size_bytes > 0", name="size_positive"),
    )

    briefing_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("visual_briefings.id", ondelete="RESTRICT"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    object_key: Mapped[str] = mapped_column(String(200), nullable=False)
    thumb_key: Mapped[str] = mapped_column(String(200), nullable=False)
    content_type: Mapped[str] = mapped_column(String(40), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))

    briefing = relationship("VisualBriefing", back_populates="files")


class CallSlot(UUIDPk, db.Model):
    """Horário da plataforma (sem empresa). Ver o docstring do módulo sobre a cópia do contato."""

    __tablename__ = "call_slots"
    __table_args__ = (
        UniqueConstraint("starts_at"),
        Index("ix_call_slots_booked_starts", "booked_at", "starts_at"),
        CheckConstraint("duration_minutes BETWEEN 10 AND 240", name="duration_valid"),
        CheckConstraint(
            "change_request IS NULL OR change_request IN ('cancelar', 'remarcar')", name="change_request_valid"
        ),
    )

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    created_by: Mapped[str | None] = mapped_column(String(254))
    # Marca de ocupado + cópia para o painel (preenchidas na mesma transação da reserva).
    booked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    visual_request_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, index=True)
    booked_contact_name: Mapped[str | None] = mapped_column(String(NAME_MAX))
    booked_contact_phone: Mapped[str | None] = mapped_column(String(PHONE_MAX))
    change_request: Mapped[str | None] = mapped_column(String(20))
    change_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CallBooking(UUIDPk, TenantMixin, db.Model):
    __tablename__ = "call_bookings"
    __table_args__ = (
        UniqueConstraint("company_id"),
        UniqueConstraint("slot_id"),
        CheckConstraint(
            "change_request IS NULL OR change_request IN ('cancelar', 'remarcar')", name="change_request_valid"
        ),
    )

    slot_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("call_slots.id", ondelete="RESTRICT"), nullable=False)
    visual_request_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    contact_name: Mapped[str] = mapped_column(String(NAME_MAX), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(PHONE_MAX), nullable=False)
    change_request: Mapped[str | None] = mapped_column(String(20))
    change_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"))

    slot = relationship("CallSlot")
