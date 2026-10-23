"""ADR-0019 §3 — agendamento da ligação de identidade visual.

- Horários (``call_slots``) são dado da PLATAFORMA: só a equipe cria e remove (``/interno``, MFA,
  ``platform_audit_logs``). Guardados em UTC; a equipe digita e a tela mostra em America/Sao_Paulo.
- Reserva (``call_bookings``) é dado DA EMPRESA (RLS). A reserva é ATÔMICA no servidor: a
  inserção bate na restrição UNIQUE ``slot_id`` — duas empresas no mesmo horário, mesmo em
  concorrência (tela desatualizada, dois cliques ao mesmo tempo), e a segunda recebe
  ``SlotTaken``. Depois, um ``UPDATE ... WHERE booked_at IS NULL`` marca o horário como ocupado
  (é a marca que a lista de horários livres lê: o RLS esconde as reservas das outras empresas).
  Se alguma das duas falhar, a transação inteira é desfeita.
- O servidor valida tudo: plano com ``visual_custom``, horário existente, futuro (com
  ``CALL_MIN_LEAD_MINUTES`` de antecedência), livre e uma reserva por empresa.
- Cancelar ou remarcar: o cliente só PEDE (``request_change``); a equipe decide no painel
  (``release`` libera o horário e apaga a reserva; ``decline`` mantém). Sem remarcação automática.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import current_app, g, has_request_context
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from app import rls
from app.extensions import db
from app.models import Company, PlatformAuditLog, User, VisualRequest
from app.models.base import utcnow
from app.models.visual import CHANGE_KINDS, NAME_MAX, PHONE_MAX, CallBooking, CallSlot
from app.services import audit
from app.services import visual as visual_svc

TZ = ZoneInfo("America/Sao_Paulo")
DURATION_MIN, DURATION_MAX = 10, 240
SLOTS_SHOWN = 60
CHANGE_LABELS = {"cancelar": "Cancelar a ligação", "remarcar": "Remarcar a ligação"}

SLOT_CREATED = "staff.call_slot_created"
SLOT_REMOVED = "staff.call_slot_removed"
BOOKING_RELEASED = "staff.call_released"
CHANGE_DECLINED = "staff.call_change_declined"
CALL_BOOKED_PLATFORM = "visual.call_booked"


class AgendaError(Exception):
    """Ação recusada (mensagem pronta para a tela)."""


class SlotTaken(AgendaError):
    """O horário foi reservado por outra empresa (ou pela mesma, em outro clique)."""


def _aware(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def local(value: datetime) -> datetime:
    return _aware(value).astimezone(TZ)


def to_utc(day: date, at: time) -> datetime:
    """Data e hora digitadas em America/Sao_Paulo → UTC (o banco guarda UTC)."""
    return datetime.combine(day, at.replace(second=0, microsecond=0, tzinfo=None)).replace(tzinfo=TZ).astimezone(timezone.utc)


def min_start(now: datetime | None = None) -> datetime:
    now = now or utcnow()
    return now + timedelta(minutes=int(current_app.config.get("CALL_MIN_LEAD_MINUTES", 60)))


# ---------------------------------------------------------------- empresa


def free_slots(now: datetime | None = None) -> list[CallSlot]:
    """Horários livres e futuros (com a antecedência mínima), em ordem."""
    return list(
        db.session.execute(
            select(CallSlot)
            .where(CallSlot.booked_at.is_(None), CallSlot.starts_at > min_start(now))
            .order_by(CallSlot.starts_at)
            .limit(SLOTS_SHOWN)
        ).scalars()
    )


def booking_for(company_id: uuid.UUID) -> CallBooking | None:
    return db.session.execute(select(CallBooking).where(CallBooking.company_id == company_id)).scalar_one_or_none()


@dataclass(frozen=True)
class Contact:
    name: str
    phone: str


def validate_contact(name: str | None, phone: str | None) -> Contact:
    name, phone = (name or "").strip(), (phone or "").strip()
    if not name:
        raise AgendaError("Informe o nome de quem vai atender a ligação.")
    if len(name) > NAME_MAX:
        raise AgendaError(f"Nome do contato: no máximo {NAME_MAX} caracteres.")
    if not phone or len(phone) > PHONE_MAX or not visual_svc.PHONE_RE.fullmatch(phone):
        raise AgendaError("Informe um telefone com DDD (só números, espaço, parênteses, + ou -).")
    return Contact(name, phone)


def book(company: Company, slot_id: uuid.UUID | str | None, contact: Contact, user_id: uuid.UUID | None,
         now: datetime | None = None) -> CallBooking:
    """Reserva o horário para a empresa (flush, sem commit). Recusa com ``AgendaError``.

    Concorrência: a inserção na restrição UNIQUE(slot_id) é o árbitro. Na violação a transação é
    desfeita (``rollback``) e levanta ``SlotTaken`` — quem chama só mostra a mensagem."""
    if not visual_svc.available(company):
        raise AgendaError("O agendamento faz parte dos planos Empresa e Implantação.")
    try:
        slot_uuid = slot_id if isinstance(slot_id, uuid.UUID) else uuid.UUID(str(slot_id))
    except (TypeError, ValueError):
        raise AgendaError("Escolha um horário da lista.") from None
    now = now or utcnow()
    if booking_for(company.id) is not None:
        raise AgendaError("Sua empresa já tem uma ligação marcada. Para mudar, peça pela própria tela.")
    slot = db.session.get(CallSlot, slot_uuid)
    if slot is None:
        raise AgendaError("Esse horário não existe mais. Escolha outro.")
    if _aware(slot.starts_at) <= min_start(now):
        raise AgendaError("Esse horário já passou ou está perto demais. Escolha outro.")
    if slot.booked_at is not None:
        raise SlotTaken("Esse horário acabou de ser reservado. Escolha outro.")
    request_ = visual_svc.ensure_request(company)
    company_id, request_id = company.id, request_.id if request_ is not None else None
    booking = CallBooking(
        company_id=company_id,
        slot_id=slot_uuid,
        visual_request_id=request_id,
        contact_name=contact.name,
        contact_phone=contact.phone,
        created_by_id=user_id,
    )
    db.session.add(booking)
    try:
        db.session.flush()  # tenta inserir: a restrição UNIQUE decide quem fica com o horário
    except IntegrityError:
        db.session.rollback()
        raise SlotTaken("Esse horário acabou de ser reservado por outra pessoa. Escolha outro.") from None
    marked = db.session.execute(
        update(CallSlot)
        .where(CallSlot.id == slot_uuid, CallSlot.booked_at.is_(None))
        .values(
            booked_at=now,
            visual_request_id=request_id,
            booked_contact_name=contact.name,
            booked_contact_phone=contact.phone,
            change_request=None,
            change_requested_at=None,
        )
        .execution_options(synchronize_session=False)
    )
    if marked.rowcount != 1:
        db.session.rollback()
        raise SlotTaken("Esse horário acabou de ser reservado por outra pessoa. Escolha outro.")
    audit.record(
        audit.CALL_BOOKED,
        company_id=company_id,
        actor_user_id=user_id,
        object_type="call_booking",
        object_id=booking.id,
        details={"slot_id": str(slot_uuid), "inicio": _aware(slot.starts_at).isoformat()},
    )
    db.session.add(
        PlatformAuditLog(
            action=CALL_BOOKED_PLATFORM,
            subject_company_id=company_id,
            operator="cliente",
            details={"slot_id": str(slot_uuid), "request_id": str(request_id) if request_id else None},
        )
    )
    db.session.flush()
    db.session.refresh(slot)
    return booking


def request_change(company: Company, booking: CallBooking, kind: str, user_id: uuid.UUID | None,
                   now: datetime | None = None) -> None:
    """O cliente PEDE cancelar ou remarcar (sem commit). A equipe decide no painel."""
    if kind not in CHANGE_KINDS:
        raise AgendaError("Escolha cancelar ou remarcar.")
    if booking.company_id != company.id:  # defesa: a rota já buscou na empresa da sessão
        raise AgendaError("Reserva não encontrada.")
    now = now or utcnow()
    booking.change_request, booking.change_requested_at = kind, now
    db.session.execute(
        update(CallSlot)
        .where(CallSlot.id == booking.slot_id)
        .values(change_request=kind, change_requested_at=now)
        .execution_options(synchronize_session=False)
    )
    audit.record(
        audit.CALL_CHANGE_REQUESTED,
        company_id=company.id,
        actor_user_id=user_id,
        object_type="call_booking",
        object_id=booking.id,
        details={"pedido": kind},
    )
    db.session.flush()


# ---------------------------------------------------------------- equipe (/interno)


def staff_slots(now: datetime | None = None, *, days_back: int = 7) -> list[CallSlot]:
    """Horários a partir de ``days_back`` dias atrás (os passados recentes ainda aparecem)."""
    since = (now or utcnow()) - timedelta(days=days_back)
    return list(
        db.session.execute(select(CallSlot).where(CallSlot.starts_at >= since).order_by(CallSlot.starts_at)).scalars()
    )


def requests_by_id(ids) -> dict[uuid.UUID, VisualRequest]:
    ids = [i for i in ids if i]
    if not ids:
        return {}
    return {r.id: r for r in db.session.execute(select(VisualRequest).where(VisualRequest.id.in_(ids))).scalars()}


def slot_for_request(request_id: uuid.UUID) -> CallSlot | None:
    return db.session.execute(
        select(CallSlot).where(CallSlot.visual_request_id == request_id).order_by(CallSlot.starts_at.desc())
    ).scalars().first()


def _platform_log(action: str, actor: User, details: dict, company_id: uuid.UUID | None = None) -> None:
    db.session.add(
        PlatformAuditLog(action=action, subject_company_id=company_id, operator=actor.email[:120], details=details)
    )


def create_slot(day: date, at: time, duration: int, actor: User, now: datetime | None = None) -> CallSlot:
    """Cria um horário (commit). Data/hora em America/Sao_Paulo; precisa ser futuro."""
    if duration is None or not DURATION_MIN <= int(duration) <= DURATION_MAX:
        raise AgendaError(f"Duração entre {DURATION_MIN} e {DURATION_MAX} minutos.")
    starts = to_utc(day, at)
    if starts <= (now or utcnow()):
        raise AgendaError("O horário precisa ser no futuro.")
    exists = db.session.execute(select(CallSlot.id).where(CallSlot.starts_at == starts)).first()
    if exists:
        raise AgendaError("Já existe um horário começando nesse momento.")
    slot = CallSlot(starts_at=starts, duration_minutes=int(duration), created_by=actor.email[:254])
    db.session.add(slot)
    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        raise AgendaError("Já existe um horário começando nesse momento.") from None
    _platform_log(SLOT_CREATED, actor, {"slot_id": str(slot.id), "inicio": starts.isoformat(), "minutos": int(duration)})
    db.session.commit()
    return slot


def remove_slot(slot: CallSlot, actor: User) -> None:
    """Remove um horário livre (commit). Reservado → recusa (libere a reserva antes)."""
    if slot.booked_at is not None:
        raise AgendaError("Esse horário está reservado. Cancele a reserva antes de remover.")
    details = {"slot_id": str(slot.id), "inicio": _aware(slot.starts_at).isoformat()}
    db.session.delete(slot)
    try:
        db.session.flush()
    except IntegrityError:  # reserva criada entre a leitura e a remoção (FK RESTRICT)
        db.session.rollback()
        raise AgendaError("Esse horário acabou de ser reservado. Atualize a página.") from None
    _platform_log(SLOT_REMOVED, actor, details)
    db.session.commit()


class _CompanyContext:
    """Contexto RLS da empresa da reserva, só durante a ação da equipe (como o expurgo LGPD)."""

    def __init__(self, company_id: uuid.UUID):
        self.company_id = company_id
        self.previous = None

    def __enter__(self):
        if has_request_context():
            self.previous = (g.get("rls_context") or {}).get("company_id") or None
        rls.set_context(company_id=self.company_id)
        return self

    def __exit__(self, *exc):
        rls.set_context(company_id=self.previous)
        return False


def _company_of(slot: CallSlot) -> uuid.UUID | None:
    req = db.session.get(VisualRequest, slot.visual_request_id) if slot.visual_request_id else None
    return req.company_id if req is not None else None


def release(slot: CallSlot, actor: User) -> VisualRequest | None:
    """A equipe cancela a reserva (a pedido do cliente ou não): apaga a reserva da empresa e libera
    o horário (commit). Devolve a requisição (para o e-mail ao cliente)."""
    if slot.booked_at is None:
        raise AgendaError("Esse horário não está reservado.")
    request_ = db.session.get(VisualRequest, slot.visual_request_id) if slot.visual_request_id else None
    company_id = request_.company_id if request_ is not None else None
    pedido = slot.change_request
    if company_id is not None:
        with _CompanyContext(company_id):
            booking = db.session.execute(
                select(CallBooking).where(CallBooking.slot_id == slot.id, CallBooking.company_id == company_id)
            ).scalar_one_or_none()
            if booking is not None:
                audit.record(
                    audit.CALL_RELEASED,
                    company_id=company_id,
                    actor_user_id=None,
                    object_type="call_booking",
                    object_id=booking.id,
                    details={"pedido": pedido, "por": "equipe"},
                )
                db.session.execute(delete(CallBooking).where(CallBooking.id == booking.id))
            db.session.flush()
    _clear(slot)
    _platform_log(BOOKING_RELEASED, actor, {"slot_id": str(slot.id), "pedido": pedido}, company_id)
    db.session.commit()
    return request_


def decline(slot: CallSlot, actor: User) -> VisualRequest | None:
    """A equipe mantém a reserva e recusa o pedido de mudança (commit)."""
    if slot.booked_at is None or not slot.change_request:
        raise AgendaError("Não há pedido de mudança para esse horário.")
    request_ = db.session.get(VisualRequest, slot.visual_request_id) if slot.visual_request_id else None
    company_id = request_.company_id if request_ is not None else None
    pedido = slot.change_request
    if company_id is not None:
        with _CompanyContext(company_id):
            booking = db.session.execute(
                select(CallBooking).where(CallBooking.slot_id == slot.id, CallBooking.company_id == company_id)
            ).scalar_one_or_none()
            if booking is not None:
                booking.change_request, booking.change_requested_at = None, None
                audit.record(
                    audit.CALL_CHANGE_DECLINED,
                    company_id=company_id,
                    actor_user_id=None,
                    object_type="call_booking",
                    object_id=booking.id,
                    details={"pedido": pedido, "por": "equipe"},
                )
            db.session.flush()
    slot.change_request, slot.change_requested_at = None, None
    _platform_log(CHANGE_DECLINED, actor, {"slot_id": str(slot.id), "pedido": pedido}, company_id)
    db.session.commit()
    return request_


def _clear(slot: CallSlot) -> None:
    slot.booked_at = None
    slot.visual_request_id = None
    slot.booked_contact_name = None
    slot.booked_contact_phone = None
    slot.change_request = None
    slot.change_requested_at = None


def release_company(company_id: uuid.UUID, *, dry_run: bool = False) -> int:
    """Expurgo LGPD: libera os horários reservados pela empresa e apaga a cópia do contato
    (``call_slots`` é da plataforma e não sai no laço de tabelas da empresa). Sem commit."""
    request_ids = list(
        db.session.execute(select(VisualRequest.id).where(VisualRequest.company_id == company_id)).scalars()
    )
    booked_slot_ids = list(
        db.session.execute(select(CallBooking.slot_id).where(CallBooking.company_id == company_id)).scalars()
    )
    conditions = []
    if request_ids:
        conditions.append(CallSlot.visual_request_id.in_(request_ids))
    if booked_slot_ids:
        conditions.append(CallSlot.id.in_(booked_slot_ids))
    if not conditions:
        return 0
    from sqlalchemy import or_

    slots = list(db.session.execute(select(CallSlot).where(or_(*conditions))).scalars())
    if not dry_run:
        for slot in slots:
            _clear(slot)
        db.session.flush()
    return len(slots)
