"""Etapa G — unidades (número de série por equipamento do projeto).

- Rastreabilidade, NÃO cálculo: progresso, status e prazo continuam vindo de
  ``activities.units_done`` via ``calc.py`` (intocado). A unidade só identifica QUAL equipamento
  recebeu um lançamento ou uma inspeção.
- Supervisor+ cria (faixa com prefixo ou lista colada) e muda o status; limite = ``quantity`` do
  projeto (checado aqui, no backend). Série normalizada (espaços nas pontas, MAIÚSCULAS), única
  por empresa+projeto (UNIQUE no banco também).
- Operador+ registra uma atividade NUMA unidade: sempre +1 peça, no máximo uma vez por
  atividade+unidade (desfazer libera de novo). Usa ``projects.register_progress`` (mesmas
  regras: máximo, versão, eventos).
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select

from app.extensions import db
from app.models import Activity, ProgressEntry, Project
from app.models.quality import UNIT_SERIAL_MAX, UNIT_STATUSES, StageInspection, Unit
from app.services import audit
from app.services import projects as projects_svc
from app.tenancy import current_company_id

STATUS_LABELS = {"in_progress": "Em produção", "done": "Concluída", "shipped": "Expedida", "scrapped": "Refugada"}
SERIAL_RE = re.compile(r"^[A-Z0-9][A-Z0-9._/-]*$")
PREFIX_RE = re.compile(r"^[A-Z0-9._/-]*$")
PREFIX_MAX = 40
WIDTH_MAX = 10
IMPORT_MAX_LINES = 5000
SEARCH_LIMIT = 50
LIKE_ESCAPE = "\\"


class UnitError(Exception):
    """Regra violada (mensagem pronta para a tela)."""


class UnitConflict(UnitError):
    """A unidade mudou desde que a tela foi aberta → 409."""


def normalize(serial: str | None) -> str:
    return "".join((serial or "").split()).upper()


def validate_serial(serial: str, where: str = "") -> str:
    serial = normalize(serial)
    if not serial or len(serial) > UNIT_SERIAL_MAX or not SERIAL_RE.fullmatch(serial):
        raise UnitError(
            f"{where}número de série inválido: use letras, números e . _ / - (até {UNIT_SERIAL_MAX} caracteres)."
        )
    return serial


def list_units(project: Project) -> list[Unit]:
    return list(
        db.session.execute(
            select(Unit).where(Unit.company_id == project.company_id, Unit.project_id == project.id).order_by(Unit.serial)
        ).scalars()
    )


def count_units(project: Project) -> int:
    return db.session.execute(
        select(func.count()).select_from(Unit).where(Unit.company_id == project.company_id, Unit.project_id == project.id)
    ).scalar_one()


def _create(project: Project, serials: list[str], user_id: uuid.UUID | None, how: str) -> list[Unit]:
    existing = {u.serial for u in list_units(project)}
    repeated = [s for s in serials if s in existing]
    if repeated:
        raise UnitError(f"Já cadastrado(s) neste projeto: {', '.join(repeated[:5])}{'…' if len(repeated) > 5 else ''}.")
    total = len(existing) + len(serials)
    if total > project.quantity:
        raise UnitError(
            f"O projeto tem {project.quantity} equipamentos: com estes, seriam {total} números de série. "
            "Aumente a quantidade do projeto ou cadastre menos."
        )
    units = [
        Unit(company_id=project.company_id, project_id=project.id, serial=s, created_by_id=user_id) for s in serials
    ]
    db.session.add_all(units)
    db.session.flush()
    audit.record(
        audit.UNITS_CREATED, company_id=project.company_id, actor_user_id=user_id, object_type="project",
        object_id=project.id, details={"como": how, "quantidade": len(units), "primeira": serials[0], "ultima": serials[-1]},
    )
    return units


def generate(project: Project, prefix: str | None, start: int, count: int, width: int,
             user_id: uuid.UUID | None) -> list[Unit]:
    """Faixa: ``prefixo`` + número com ``width`` dígitos (ex.: MT-001 … MT-010)."""
    prefix = normalize(prefix)
    if len(prefix) > PREFIX_MAX or not PREFIX_RE.fullmatch(prefix):
        raise UnitError(f"Prefixo inválido: letras, números e . _ / - (até {PREFIX_MAX} caracteres).")
    if not (0 <= start <= 10**9) or not (1 <= width <= WIDTH_MAX):
        raise UnitError("Número inicial ou dígitos inválidos.")
    if not (1 <= count <= project.quantity):
        raise UnitError(f"Quantidade entre 1 e {project.quantity}.")
    serials = [validate_serial(f"{prefix}{n:0{width}d}") for n in range(start, start + count)]
    return _create(project, serials, user_id, "faixa")


def import_list(project: Project, text: str | None, user_id: uuid.UUID | None) -> list[Unit]:
    """Lista colada: um número por linha (também aceita ``;`` ou ``,`` como separador)."""
    raw = [part for line in (text or "").splitlines() for part in re.split(r"[;,\t]", line)]
    if len(raw) > IMPORT_MAX_LINES:
        raise UnitError(f"No máximo {IMPORT_MAX_LINES} números por vez.")
    serials: list[str] = []
    seen: set[str] = set()
    for number, value in enumerate(raw, start=1):
        if not value.strip():
            continue
        serial = validate_serial(value, f"Item {number}: ")
        if serial in seen:
            raise UnitError(f"Item {number}: {serial} repetido na lista.")
        seen.add(serial)
        serials.append(serial)
    if not serials:
        raise UnitError("Cole pelo menos um número de série.")
    return _create(project, serials, user_id, "lista")


def set_status(unit: Unit, status: str, user_id: uuid.UUID | None, expected_version: int | None = None) -> None:
    if status not in UNIT_STATUSES:
        raise UnitError("Situação inválida.")
    if expected_version is not None and expected_version != unit.version:
        raise UnitConflict("Outra pessoa alterou esta unidade. Confira a situação atual.")
    if status == unit.status:
        return
    before = unit.status
    from sqlalchemy import update

    result = db.session.execute(
        update(Unit)
        .where(Unit.id == unit.id, Unit.company_id == unit.company_id, Unit.version == unit.version)
        .values(status=status, version=Unit.version + 1, updated_at=func.now())
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:  # pragma: no cover - corrida entre abas
        raise UnitConflict("Outra pessoa alterou esta unidade. Confira a situação atual.")
    db.session.refresh(unit)
    audit.record(
        audit.UNIT_STATUS_CHANGED, company_id=unit.company_id, actor_user_id=user_id, object_type="unit",
        object_id=unit.id, details={"serial": unit.serial, "de": before, "para": status},
    )


def _active_entry(activity: Activity, unit: Unit) -> ProgressEntry | None:
    """Lançamento positivo desta unidade nesta atividade que ainda não foi desfeito."""
    entries = list(
        db.session.execute(
            select(ProgressEntry).where(
                ProgressEntry.company_id == unit.company_id,
                ProgressEntry.activity_id == activity.id,
                ProgressEntry.unit_id == unit.id,
            )
        ).scalars()
    )
    undone = {e.reverts_entry_id for e in entries if e.reverts_entry_id}
    return next((e for e in entries if e.delta > 0 and e.id not in undone), None)


def register_for_unit(unit: Unit, activity: Activity, user_id: uuid.UUID, expected_version: int | None = None) -> ProgressEntry:
    if activity.stage.project_id != unit.project_id or activity.company_id != unit.company_id:
        raise UnitError("Subatividade de outro projeto.")
    if _active_entry(activity, unit) is not None:
        raise UnitError(f"A unidade {unit.serial} já foi registrada nesta subatividade.")
    return projects_svc.register_progress(activity, 1, expected_version, user_id, unit_id=unit.id)


@dataclass(frozen=True)
class UnitHistory:
    entries: list
    undone: set
    inspections: list
    changes: list
    done_activities: set


def history(unit: Unit) -> UnitHistory:
    entries = list(
        db.session.execute(
            select(ProgressEntry)
            .where(ProgressEntry.company_id == unit.company_id, ProgressEntry.unit_id == unit.id)
            .order_by(ProgressEntry.at.desc(), ProgressEntry.id)
        ).scalars()
    )
    undone = {e.reverts_entry_id for e in entries if e.reverts_entry_id}
    done_activities = {e.activity_id for e in entries if e.delta > 0 and e.id not in undone}
    inspections = list(
        db.session.execute(
            select(StageInspection)
            .where(StageInspection.company_id == unit.company_id, StageInspection.unit_id == unit.id)
            .order_by(StageInspection.created_at.desc())
        ).scalars()
    )
    return UnitHistory(
        entries=entries,
        undone=undone,
        inspections=inspections,
        changes=audit.for_object(unit.company_id, "unit", unit.id),
        done_activities=done_activities,
    )


def _like(term: str) -> str:
    escaped = term.replace(LIKE_ESCAPE, LIKE_ESCAPE * 2).replace("%", LIKE_ESCAPE + "%").replace("_", LIKE_ESCAPE + "_")
    return f"%{escaped}%"


def search(q: str | None, project: Project | None = None) -> list[Unit]:
    """Busca por série na empresa da sessão (opcionalmente num projeto). Até 50 resultados."""
    term = normalize(q)[:UNIT_SERIAL_MAX]
    if not term:
        return []
    stmt = (
        select(Unit)
        .join(Project, Project.id == Unit.project_id)
        .where(
            Unit.company_id == current_company_id(),
            Project.company_id == current_company_id(),
            Project.archived_at.is_(None),
            Unit.serial.like(_like(term), escape=LIKE_ESCAPE),
        )
        .order_by(Unit.serial)
        .limit(SEARCH_LIMIT)
    )
    if project is not None:
        stmt = stmt.where(Unit.project_id == project.id)
    return list(db.session.execute(stmt).scalars())
