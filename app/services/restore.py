"""R8 — restaurar o projeto para como estava numa data e hora.

Escopo: só as PEÇAS concluídas das atividades (o que o histórico ``progress_entries``
registra). Nomes, tempos ideais, quantidade, estrutura de etapas/atividades (criar, mover,
arquivar) e marcas como “aguardando peça” NÃO voltam: o histórico não guarda esses estados.
Atividades e etapas arquivadas ficam de fora (não entram no cálculo do projeto).

Como funciona:
- ``restore_preview``: para cada atividade ativa, peças no instante =
  ``calc.pecas_no_instante`` (peças de agora menos tudo o que foi lançado depois do instante,
  registros, desfazeres e restaurações incluídos). Devolve a diferença por etapa/atividade, o
  resumo do projeto antes/depois (``calc.resumo_projeto``) e um ``token`` — assinatura do estado
  usado na prévia (versão e peças de cada atividade, quantidade do projeto, instante).
- ``restore_apply``: refaz a prévia; token diferente → ``RestoreConflict`` (409: algo mudou
  entre a prévia e a confirmação). Grava UM lançamento COMPENSATÓRIO por atividade que muda
  (delta = alvo − atual, ``restore_id`` = id da operação), com UPDATE condicional na versão
  (mesma técnica de ``register_progress``/``undo_progress``). Nunca apaga histórico. Auditoria
  ``project.restored``.
- ``restore_undo``: desfaz a restauração inteira com lançamentos que invertem os dela
  (``restore_undoes_id`` = restauração desfeita). Uma vez só; não desfaz um desfazer.

Permissão (supervisor+) e empresa (404) ficam na rota; aqui tudo usa a empresa do projeto.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select, update

from app.extensions import db
from app.models import Activity, AuditLog, Project, ProgressEntry, Stage
from app.services import audit, calc, events
from app.services import projects as psvc

DEFAULT_TZ = "America/Sao_Paulo"
INPUT_FORMAT = "%Y-%m-%dT%H:%M"

PROJECT_RESTORED = audit.PROJECT_RESTORED
PROJECT_RESTORE_UNDONE = audit.PROJECT_RESTORE_UNDONE

CONFLICT_MESSAGE = "O projeto mudou depois da prévia. Confira a nova prévia e confirme de novo."


class RestoreError(psvc.ProgressError):
    """Restauração inválida (mensagem pronta para a tela)."""


class RestoreConflict(RestoreError):
    """O estado mudou entre a prévia e a confirmação → 409 (nada foi gravado)."""


class NothingToRestore(RestoreError):
    """No instante pedido o projeto já estava como está agora."""


class RestoreNotFound(LookupError):
    """Restauração inexistente neste projeto/empresa → 404."""


# ---------------------------------------------------------------- data e hora


def _tz(tz_name: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name or DEFAULT_TZ)
    except Exception:  # noqa: BLE001 - fuso inválido cai no padrão
        return ZoneInfo(DEFAULT_TZ)


def parse_local(raw: str | None, tz_name: str | None = DEFAULT_TZ) -> datetime | None:
    """``AAAA-MM-DDTHH:MM`` digitado no fuso da empresa → instante em UTC. Inválido → None.

    O instante é o início do minuto (HH:MM:00): um lançamento feito às 10:30:20 fica DEPOIS
    de “10:30” e é desfeito por uma restauração para 10:30."""
    try:
        local = datetime.strptime((raw or "").strip(), INPUT_FORMAT)
    except ValueError:
        return None
    return local.replace(tzinfo=_tz(tz_name)).astimezone(timezone.utc)


def format_local(at: datetime, tz_name: str | None = DEFAULT_TZ) -> str:
    """Instante → ``AAAA-MM-DDTHH:MM`` no fuso da empresa (volta para o formulário)."""
    return _aware(at).astimezone(_tz(tz_name)).strftime(INPUT_FORMAT)


def _aware(at: datetime) -> datetime:
    # SQLite devolve datetime sem fuso (gravado em UTC); PostgreSQL devolve com fuso.
    return at if at.tzinfo is not None else at.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------- prévia


@dataclass(frozen=True)
class ActivityDiff:
    activity: Activity
    current: int  # peças agora
    target: int  # peças no instante (depois de restaurar)
    version: int

    @property
    def delta(self) -> int:
        return self.target - self.current

    @property
    def changed(self) -> bool:
        return self.target != self.current


@dataclass(frozen=True)
class StageDiff:
    stage: Stage
    activities: tuple[ActivityDiff, ...]
    before: calc.ResultadoEtapa
    after: calc.ResultadoEtapa

    @property
    def changed(self) -> bool:
        return any(a.changed for a in self.activities)


@dataclass(frozen=True)
class RestorePreview:
    project: Project
    at: datetime  # UTC
    stages: tuple[StageDiff, ...]
    before: calc.ResultadoProjeto
    after: calc.ResultadoProjeto
    token: str

    @property
    def changes(self) -> list[ActivityDiff]:
        return [a for s in self.stages for a in s.activities if a.changed]

    @property
    def changed(self) -> bool:
        return bool(self.changes)


def _deltas_after(project: Project, activity_ids: list[uuid.UUID], at: datetime) -> dict[uuid.UUID, list[int]]:
    if not activity_ids:
        return {}
    rows = db.session.execute(
        select(ProgressEntry.activity_id, ProgressEntry.delta, ProgressEntry.at).where(
            ProgressEntry.company_id == project.company_id, ProgressEntry.activity_id.in_(activity_ids)
        )
    ).all()
    out: dict[uuid.UUID, list[int]] = {}
    for activity_id, delta, entry_at in rows:
        if _aware(entry_at) > at:
            out.setdefault(activity_id, []).append(delta)
    return out


def _token(project: Project, at: datetime, diffs: list[ActivityDiff]) -> str:
    parts = [str(project.id), at.isoformat(), str(project.quantity)]
    parts += sorted(f"{d.activity.id}:{d.version}:{d.current}" for d in diffs)
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:32]


def _resumo(project: Project, etapas: list[calc.Etapa]) -> calc.ResultadoProjeto:
    return calc.resumo_projeto(
        etapas, quantidade=project.quantity, pessoas=project.people, horas_dia=float(project.hours_per_day)
    )


def restore_preview(project: Project, at: datetime) -> RestorePreview:
    """O que muda ao voltar o projeto para ``at`` (instante com fuso; UTC de preferência)."""
    at = _aware(at).astimezone(timezone.utc)
    stages = psvc.active_stages(project)
    live = [(s, psvc.active_activities(s)) for s in stages]
    after_t = _deltas_after(project, [a.id for _, acts in live for a in acts], at)
    stage_diffs: list[StageDiff] = []
    before_etapas: list[calc.Etapa] = []
    after_etapas: list[calc.Etapa] = []
    all_diffs: list[ActivityDiff] = []
    for stage, acts in live:
        diffs = tuple(
            ActivityDiff(
                activity=a,
                current=a.units_done,
                target=calc.pecas_no_instante(a.units_done, after_t.get(a.id, ()), project.quantity),
                version=a.version,
            )
            for a in acts
        )
        all_diffs.extend(diffs)
        etapa_antes = calc.Etapa(
            atividades=tuple(calc.Atividade(ideal_min=float(d.activity.ideal_minutes or 0), pecas=d.current) for d in diffs),
            previstas=project.quantity,
        )
        etapa_depois = calc.Etapa(
            atividades=tuple(calc.Atividade(ideal_min=float(d.activity.ideal_minutes or 0), pecas=d.target) for d in diffs),
            previstas=project.quantity,
        )
        before_etapas.append(etapa_antes)
        after_etapas.append(etapa_depois)
        stage_diffs.append(
            StageDiff(stage=stage, activities=diffs, before=calc.resumo_etapa(etapa_antes), after=calc.resumo_etapa(etapa_depois))
        )
    return RestorePreview(
        project=project,
        at=at,
        stages=tuple(stage_diffs),
        before=_resumo(project, before_etapas),
        after=_resumo(project, after_etapas),
        token=_token(project, at, all_diffs),
    )


# ---------------------------------------------------------------- aplicar


@dataclass(frozen=True)
class RestoreResult:
    restore_id: uuid.UUID
    entries: list[ProgressEntry]


def _ensure_open(project: Project) -> None:
    if project.archived_at is not None:
        raise RestoreError("Projeto arquivado não pode ser restaurado.")


def _write(
    project: Project,
    moves: list[tuple[Activity, int, int]],
    actor_id: uuid.UUID | None,
    restore_id: uuid.UUID,
    undoes: uuid.UUID | None,
) -> list[ProgressEntry]:
    """Grava os lançamentos (atividade, versão esperada, delta) com UPDATE condicional.
    Qualquer linha que mudou no caminho → rollback e ``RestoreConflict``."""
    stage_before = {s.id: psvc._stage_done(s) for s in psvc.active_stages(project)}
    project_before = psvc._project_done(project)
    entries: list[ProgressEntry] = []
    for activity, version, delta in moves:
        result = db.session.execute(
            update(Activity)
            .where(
                Activity.id == activity.id,
                Activity.company_id == project.company_id,
                Activity.version == version,
                Activity.units_done + delta >= 0,
                Activity.units_done + delta <= project.quantity,
            )
            .values(units_done=Activity.units_done + delta, version=Activity.version + 1)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            db.session.rollback()
            raise RestoreConflict(CONFLICT_MESSAGE)
        entry = ProgressEntry(
            company_id=project.company_id,
            activity_id=activity.id,
            user_id=actor_id,
            delta=delta,
            restore_id=restore_id,
            restore_undoes_id=undoes,
        )
        db.session.add(entry)
        entries.append(entry)
    db.session.flush()
    for activity, _, _ in moves:
        db.session.refresh(activity)
    for entry in entries:
        activity = entry.activity
        events.emit(
            project.company_id,
            events.ACTIVITY_PROGRESS_UPDATED,
            {
                "project_id": project.id,
                "stage_id": activity.stage_id,
                "activity_id": activity.id,
                "entry_id": entry.id,
                "delta": entry.delta,
                "units_done": activity.units_done,
                "quantity": project.quantity,
            },
        )
    for stage in psvc.active_stages(project):
        if not stage_before.get(stage.id, True) and psvc._stage_done(stage):
            events.emit(project.company_id, events.STAGE_COMPLETED, {"project_id": project.id, "stage_id": stage.id})
    project_after = psvc._project_done(project)
    if not project_before and project_after:
        events.emit(project.company_id, events.PROJECT_COMPLETED, {"project_id": project.id})
    psvc._sync_status(project, project_after)
    return entries


def restore_apply(
    project: Project,
    at: datetime,
    actor_id: uuid.UUID | None,
    expected_token: str | None,
    *,
    tz_name: str | None = DEFAULT_TZ,
) -> RestoreResult:
    """Volta as peças das atividades para ``at``. Sem commit (quem chama faz)."""
    _ensure_open(project)
    preview = restore_preview(project, at)
    if not expected_token or expected_token != preview.token:
        raise RestoreConflict(CONFLICT_MESSAGE)
    changes = preview.changes
    if not changes:
        raise NothingToRestore("Nada a restaurar: nesse momento o projeto já estava como está agora.")
    restore_id = uuid.uuid4()
    entries = _write(project, [(d.activity, d.version, d.delta) for d in changes], actor_id, restore_id, None)
    audit.record(
        PROJECT_RESTORED,
        company_id=project.company_id,
        actor_user_id=actor_id,
        object_type="project",
        object_id=project.id,
        details={
            "restore_id": str(restore_id),
            "ate": format_local(preview.at, tz_name),
            "ate_utc": preview.at.isoformat(),
            "lancamentos": len(entries),
            "pecas_antes": sum(d.current for d in changes),
            "pecas_depois": sum(d.target for d in changes),
        },
    )
    return RestoreResult(restore_id=restore_id, entries=entries)


# ---------------------------------------------------------------- desfazer a restauração


def _group(project: Project, restore_id: uuid.UUID) -> list[ProgressEntry]:
    return list(
        db.session.execute(
            select(ProgressEntry)
            .join(Activity, Activity.id == ProgressEntry.activity_id)
            .join(Stage, Stage.id == Activity.stage_id)
            .where(
                ProgressEntry.company_id == project.company_id,
                Activity.company_id == project.company_id,
                Stage.project_id == project.id,
                ProgressEntry.restore_id == restore_id,
            )
            .order_by(ProgressEntry.at, ProgressEntry.id)
        ).scalars()
    )


def restore_exists(project: Project, restore_id: uuid.UUID) -> bool:
    """A restauração existe NESTE projeto (empresa do projeto)?"""
    return bool(_group(project, restore_id))


def is_restore_undone(project: Project, restore_id: uuid.UUID) -> bool:
    return (
        db.session.execute(
            select(ProgressEntry.id).where(
                ProgressEntry.company_id == project.company_id, ProgressEntry.restore_undoes_id == restore_id
            )
        ).first()
        is not None
    )


def restore_undo(project: Project, restore_id: uuid.UUID, actor_id: uuid.UUID | None) -> RestoreResult:
    """Desfaz a restauração ``restore_id`` deste projeto (lançamentos que invertem os dela).

    Relativo, como o desfazer de registro: o que foi lançado depois da restauração continua.
    Se a inversão deixaria alguma atividade abaixo de 0 ou acima das previstas, recusa."""
    entries = _group(project, restore_id)
    if not entries:
        raise RestoreNotFound(str(restore_id))
    _ensure_open(project)
    if any(e.restore_undoes_id is not None for e in entries):
        raise RestoreError("Isto já é um desfazer de restauração.")
    if is_restore_undone(project, restore_id):
        raise RestoreError("Esta restauração já foi desfeita.")
    moves: list[tuple[Activity, int, int]] = []
    for entry in entries:
        activity = entry.activity
        db.session.refresh(activity)
        new = activity.units_done - entry.delta
        if new < 0 or new > project.quantity:
            raise RestoreError(
                f"Não dá para desfazer: {activity.name} mudou depois da restauração "
                f"({activity.units_done} de {project.quantity})."
            )
        moves.append((activity, activity.version, -entry.delta))
    undo_id = uuid.uuid4()
    written = _write(project, moves, actor_id, undo_id, restore_id)
    audit.record(
        PROJECT_RESTORE_UNDONE,
        company_id=project.company_id,
        actor_user_id=actor_id,
        object_type="project",
        object_id=project.id,
        details={"restore_id": str(restore_id), "undo_id": str(undo_id), "lancamentos": len(written)},
    )
    return RestoreResult(restore_id=undo_id, entries=written)


# ---------------------------------------------------------------- leitura


@dataclass(frozen=True)
class RestoreRecord:
    restore_id: uuid.UUID
    log: AuditLog
    target: str  # AAAA-MM-DDTHH:MM no fuso da empresa
    entries: int
    undone: bool


def restorations(project: Project, limit: int = 20) -> list[RestoreRecord]:
    """Restaurações do projeto (mais recentes primeiro), com “já desfeita?”."""
    logs = list(
        db.session.execute(
            select(AuditLog)
            .where(
                AuditLog.company_id == project.company_id,
                AuditLog.object_type == "project",
                AuditLog.object_id == project.id,
                AuditLog.action == PROJECT_RESTORED,
            )
            .order_by(AuditLog.at.desc())
            .limit(limit)
        ).scalars()
    )
    ids = []
    for log in logs:
        try:
            ids.append(uuid.UUID((log.details or {}).get("restore_id", "")))
        except ValueError:
            ids.append(None)
    wanted = [i for i in ids if i is not None]
    undone = (
        set(
            db.session.execute(
                select(ProgressEntry.restore_undoes_id).where(
                    ProgressEntry.company_id == project.company_id, ProgressEntry.restore_undoes_id.in_(wanted)
                )
            ).scalars()
        )
        if wanted
        else set()
    )
    return [
        RestoreRecord(
            restore_id=rid,
            log=log,
            target=(log.details or {}).get("ate", ""),
            entries=int((log.details or {}).get("lancamentos", 0)),
            undone=rid in undone,
        )
        for log, rid in zip(logs, ids)
        if rid is not None
    ]
