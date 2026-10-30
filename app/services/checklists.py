"""Etapa G — checklist de inspeção por etapa.

Papéis (decisão registrada no ADR-0011; conferidos na ROTA e aqui só a regra de negócio):
- supervisor+ define itens da etapa do projeto (incluir/arquivar) e liga “exige checklist”;
- operador+ abre uma inspeção (rascunho), preenche e ASSINA;
- supervisor+ registra CORREÇÃO depois de assinada (nova linha + motivo; a antiga fica).

Assinatura = ``signed_by_id`` (usuário autenticado da sessão) + ``signed_at`` (relógio do
servidor) — nunca vem do formulário, nunca é desenho. Depois de assinada, as respostas ficam com
``locked_at`` e a guarda do ORM recusa UPDATE/DELETE (models/quality.py).

“Exige checklist” SÓ SINALIZA (“Checklist pendente”), igual a “aguardando peça”: não bloqueia
registro de peças nem a conclusão da etapa (ADR-0011).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select, update

from app.extensions import db
from app.models import Stage
from app.models.quality import (
    CHECKLIST_ITEM_MAX,
    CHECKLIST_NOTE_MAX,
    INSPECTION_DRAFT,
    INSPECTION_SIGNED,
    RESULT_NONCONFORMING,
    RESULTS,
    InspectionAnswer,
    StageChecklistItem,
    StageInspection,
)
from app.services import audit

MAX_ACTIVE_ITEMS = 30
REASON_MIN = 5
RESULT_LABELS = {"ok": "OK", "nonconforming": "Não conforme", "na": "N/A"}


class ChecklistError(Exception):
    """Regra violada (mensagem pronta para a tela)."""


class InspectionConflict(ChecklistError):
    """A inspeção mudou desde que a tela foi aberta (``version``) → 409."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- itens


def active_items(stage: Stage) -> list[StageChecklistItem]:
    return list(
        db.session.execute(
            select(StageChecklistItem)
            .where(
                StageChecklistItem.company_id == stage.company_id,
                StageChecklistItem.stage_id == stage.id,
                StageChecklistItem.archived_at.is_(None),
            )
            .order_by(StageChecklistItem.position, StageChecklistItem.created_at)
        ).scalars()
    )


def add_item(stage: Stage, text: str | None, user_id: uuid.UUID | None) -> StageChecklistItem:
    text = " ".join((text or "").split())
    if not text or len(text) > CHECKLIST_ITEM_MAX:
        raise ChecklistError(f"Escreva o item (até {CHECKLIST_ITEM_MAX} caracteres).")
    items = active_items(stage)
    if len(items) >= MAX_ACTIVE_ITEMS:
        raise ChecklistError(f"No máximo {MAX_ACTIVE_ITEMS} itens ativos por etapa.")
    if any(i.text.casefold() == text.casefold() for i in items):
        raise ChecklistError("Este item já está no checklist.")
    item = StageChecklistItem(
        company_id=stage.company_id,
        stage_id=stage.id,
        text=text,
        position=max((i.position for i in items), default=-1) + 1,
        created_by_id=user_id,
    )
    db.session.add(item)
    db.session.flush()
    audit.record(
        audit.CHECKLIST_ITEM_ADDED, company_id=stage.company_id, actor_user_id=user_id,
        object_type="project", object_id=stage.project_id, details={"stage": stage.name, "item": text},
    )
    return item


def archive_item(item: StageChecklistItem, user_id: uuid.UUID | None) -> None:
    """Arquiva (respostas já dadas continuam apontando para o item)."""
    item.archived_at = _now()
    db.session.flush()
    audit.record(
        audit.CHECKLIST_ITEM_ARCHIVED, company_id=item.company_id, actor_user_id=user_id,
        object_type="project", object_id=item.stage.project_id, details={"stage": item.stage.name, "item": item.text},
    )


def set_required(stage: Stage, required: bool, user_id: uuid.UUID | None) -> None:
    if bool(stage.checklist_required) == bool(required):
        return
    stage.checklist_required = bool(required)
    db.session.flush()
    audit.record(
        audit.STAGE_CHECKLIST_REQUIRED, company_id=stage.company_id, actor_user_id=user_id,
        object_type="project", object_id=stage.project_id, details={"stage": stage.name, "exige": bool(required)},
    )


# ---------------------------------------------------------------- inspeções


def inspections_for(stage: Stage) -> list[StageInspection]:
    return list(
        db.session.execute(
            select(StageInspection)
            .where(StageInspection.company_id == stage.company_id, StageInspection.stage_id == stage.id)
            .order_by(StageInspection.created_at.desc(), StageInspection.id)
        ).scalars()
    )


def start_inspection(stage: Stage, user_id: uuid.UUID | None, unit=None) -> StageInspection:
    """Abre um rascunho (ou devolve o rascunho que já existe para a mesma etapa/unidade)."""
    if not active_items(stage):
        raise ChecklistError("Esta etapa ainda não tem itens de checklist.")
    query = select(StageInspection).where(
        StageInspection.company_id == stage.company_id,
        StageInspection.stage_id == stage.id,
        StageInspection.status == INSPECTION_DRAFT,
    )
    unit_id = unit.id if unit is not None else None
    query = query.where(StageInspection.unit_id.is_(None) if unit_id is None else StageInspection.unit_id == unit_id)
    existing = db.session.execute(query.limit(1)).scalar_one_or_none()
    if existing is not None:
        return existing
    inspection = StageInspection(company_id=stage.company_id, stage_id=stage.id, created_by_id=user_id, unit_id=unit_id)
    db.session.add(inspection)
    db.session.flush()
    return inspection


def all_answers(inspection: StageInspection) -> list[InspectionAnswer]:
    return list(
        db.session.execute(
            select(InspectionAnswer)
            .where(InspectionAnswer.company_id == inspection.company_id, InspectionAnswer.inspection_id == inspection.id)
            .order_by(InspectionAnswer.answered_at, InspectionAnswer.id)
        ).scalars()
    )


def current_answers(inspection: StageInspection) -> dict[uuid.UUID, InspectionAnswer]:
    """Resposta VIGENTE por item: a que nenhuma outra corrigiu."""
    answers = all_answers(inspection)
    superseded = {a.supersedes_id for a in answers if a.supersedes_id}
    return {a.item_id: a for a in answers if a.id not in superseded}


def history_by_item(inspection: StageInspection) -> dict[uuid.UUID, list[InspectionAnswer]]:
    out: dict[uuid.UUID, list[InspectionAnswer]] = {}
    for a in all_answers(inspection):
        out.setdefault(a.item_id, []).append(a)
    return out


def items_of(inspection: StageInspection) -> list[StageChecklistItem]:
    """Itens mostrados: os ativos da etapa + os arquivados que já têm resposta nesta inspeção."""
    answered = {a.item_id for a in all_answers(inspection)}
    rows = db.session.execute(
        select(StageChecklistItem)
        .where(StageChecklistItem.company_id == inspection.company_id, StageChecklistItem.stage_id == inspection.stage_id)
        .order_by(StageChecklistItem.position, StageChecklistItem.created_at)
    ).scalars()
    return [i for i in rows if i.archived_at is None or i.id in answered]


@dataclass(frozen=True)
class AnswerInput:
    result: str
    note: str | None


def _clean(value: AnswerInput) -> AnswerInput:
    if value.result not in RESULTS:
        raise ChecklistError("Resultado inválido (use OK, Não conforme ou N/A).")
    note = (value.note or "").strip() or None
    if note is not None and len(note) > CHECKLIST_NOTE_MAX:
        raise ChecklistError(f"Observação com no máximo {CHECKLIST_NOTE_MAX} caracteres.")
    return AnswerInput(value.result, note)


def _bump(inspection: StageInspection, expected_version: int | None, values: dict) -> None:
    """UPDATE condicional (rascunho + versão): outra aba assinou/salvou antes → conflito."""
    if expected_version is not None and expected_version != inspection.version:
        raise InspectionConflict("Outra pessoa mexeu nesta inspeção enquanto você preenchia. Confira e salve de novo.")
    result = db.session.execute(
        update(StageInspection)
        .where(
            StageInspection.id == inspection.id,
            StageInspection.company_id == inspection.company_id,
            StageInspection.version == inspection.version,
            StageInspection.status == INSPECTION_DRAFT,
        )
        .values(**values, version=StageInspection.version + 1)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise InspectionConflict("Outra pessoa mexeu nesta inspeção enquanto você preenchia. Confira e salve de novo.")
    db.session.refresh(inspection)


def save_answers(
    inspection: StageInspection,
    answers: dict[uuid.UUID, AnswerInput],
    user_id: uuid.UUID | None,
    expected_version: int | None,
) -> None:
    """Grava o rascunho. Só itens desta etapa (ids desconhecidos são ignorados)."""
    if inspection.status != INSPECTION_DRAFT:
        raise ChecklistError("Inspeção já assinada: mudanças só por correção registrada.")
    known = {i.id: i for i in items_of(inspection)}
    cleaned = {item_id: _clean(v) for item_id, v in answers.items() if item_id in known}
    current = current_answers(inspection)
    now = _now()
    _bump(inspection, expected_version, {})
    for item_id, value in cleaned.items():
        row = current.get(item_id)
        if row is None:
            db.session.add(InspectionAnswer(
                company_id=inspection.company_id, inspection_id=inspection.id, item_id=item_id,
                result=value.result, note=value.note, answered_by_id=user_id, answered_at=now,
            ))
        elif (row.result, row.note) != (value.result, value.note):
            row.result, row.note, row.answered_by_id, row.answered_at = value.result, value.note, user_id, now
    db.session.flush()


def sign(inspection: StageInspection, user_id: uuid.UUID, expected_version: int | None) -> None:
    """Assina: todo item ativo respondido; “não conforme” exige observação. Grava quem e quando
    (servidor) e trava as respostas."""
    if inspection.status != INSPECTION_DRAFT:
        raise ChecklistError("Esta inspeção já foi assinada.")
    current = current_answers(inspection)
    missing = [i.text for i in active_items(inspection.stage) if i.id not in current]
    if missing:
        raise ChecklistError(f"Responda todos os itens antes de assinar ({len(missing)} sem resposta).")
    if any(a.result == RESULT_NONCONFORMING and not a.note for a in current.values()):
        raise ChecklistError("Item “Não conforme” precisa de observação.")
    now = _now()
    _bump(inspection, expected_version, {"status": INSPECTION_SIGNED, "signed_by_id": user_id, "signed_at": now})
    for answer in current.values():
        answer.locked_at = now
    db.session.flush()
    nonconforming = sum(1 for a in current.values() if a.result == RESULT_NONCONFORMING)
    audit.record(
        audit.INSPECTION_SIGNED, company_id=inspection.company_id, actor_user_id=user_id,
        object_type="project", object_id=inspection.stage.project_id,
        details={"stage": inspection.stage.name, "inspection_id": str(inspection.id), "itens": len(current),
                 "nao_conformes": nonconforming},
    )


def correct(
    inspection: StageInspection,
    item: StageChecklistItem,
    value: AnswerInput,
    reason: str | None,
    user_id: uuid.UUID | None,
) -> InspectionAnswer:
    """Correção depois de assinada: NOVA linha (``supersedes_id`` = vigente; UNIQUE impede duas
    correções simultâneas da mesma linha) com motivo; a resposta antiga continua no banco."""
    if inspection.status != INSPECTION_SIGNED:
        raise ChecklistError("Só inspeção assinada recebe correção; o rascunho se edita direto.")
    if item.stage_id != inspection.stage_id or item.company_id != inspection.company_id:
        raise ChecklistError("Item não pertence a esta inspeção.")
    value = _clean(value)
    reason = (reason or "").strip()
    if len(reason) < REASON_MIN or len(reason) > CHECKLIST_NOTE_MAX:
        raise ChecklistError(f"Explique o motivo da correção ({REASON_MIN} a {CHECKLIST_NOTE_MAX} caracteres).")
    if value.result == RESULT_NONCONFORMING and not value.note:
        raise ChecklistError("Item “Não conforme” precisa de observação.")
    previous = current_answers(inspection).get(item.id)
    if previous is not None and (previous.result, previous.note) == (value.result, value.note):
        raise ChecklistError("Nada mudou nesta resposta.")
    now = _now()
    row = InspectionAnswer(
        company_id=inspection.company_id, inspection_id=inspection.id, item_id=item.id,
        result=value.result, note=value.note, answered_by_id=user_id, answered_at=now, locked_at=now,
        supersedes_id=previous.id if previous is not None else None, correction_reason=reason,
    )
    db.session.add(row)
    db.session.flush()
    audit.record(
        audit.INSPECTION_CORRECTED, company_id=inspection.company_id, actor_user_id=user_id,
        object_type="project", object_id=inspection.stage.project_id,
        details={
            "stage": inspection.stage.name, "inspection_id": str(inspection.id), "item": item.text,
            "de": previous.result if previous is not None else None, "para": value.result,
        },
    )
    return row


# ---------------------------------------------------------------- sinal na tela


@dataclass(frozen=True)
class StageSignal:
    required: bool
    items: int
    signed: int
    drafts: int

    @property
    def pending(self) -> bool:
        return self.required and self.signed == 0


def signals(company_id: uuid.UUID, stages: list[Stage]) -> dict[uuid.UUID, StageSignal]:
    """Por etapa: exige?, itens ativos, inspeções assinadas e rascunhos (3 consultas agrupadas)."""
    ids = [s.id for s in stages]
    if not ids:
        return {}
    items = dict(db.session.execute(
        select(StageChecklistItem.stage_id, func.count())
        .where(StageChecklistItem.company_id == company_id, StageChecklistItem.stage_id.in_(ids),
               StageChecklistItem.archived_at.is_(None))
        .group_by(StageChecklistItem.stage_id)
    ).all())
    counts: dict = {}
    for stage_id, status, n in db.session.execute(
        select(StageInspection.stage_id, StageInspection.status, func.count())
        .where(StageInspection.company_id == company_id, StageInspection.stage_id.in_(ids))
        .group_by(StageInspection.stage_id, StageInspection.status)
    ).all():
        counts[(stage_id, status)] = n
    return {
        s.id: StageSignal(
            required=bool(s.checklist_required),
            items=items.get(s.id, 0),
            signed=counts.get((s.id, INSPECTION_SIGNED), 0),
            drafts=counts.get((s.id, INSPECTION_DRAFT), 0),
        )
        for s in stages
    }
