"""Worker (Etapa F, ADR-0010): outbox + tarefas agendadas, empresa a empresa no contexto RLS.

Roda em PROCESSO SEPARADO (``flask worker run``; ``--once`` faz um ciclo e sai). Nunca usa
papel com BYPASSRLS: lê ``companies`` (sem RLS) e, para cada empresa, faz
``rls.set_context(company_id=…)``, trabalha só nas linhas dela e dá ``commit``.

Tarefas (todas idempotentes — rodar de novo não duplica nada):
- ``events``: consome ``domain_events`` pendentes (``published_at IS NULL``), um por vez com
  ``FOR UPDATE SKIP LOCKED`` no PostgreSQL. Sucesso → ``published_at``. Erro → ``attempts+1``,
  ``next_attempt_at`` com backoff exponencial e ``last_error`` (só o nome da exceção). Esgotou
  ``WORKER_EVENT_MAX_ATTEMPTS`` → sai da fila (``flask worker status`` mostra).
- ``alerts``: alertas automáticos por empresa (``services/alerts.py``) e e-mail aos supervisores.
- ``weekly``: relatório semanal por e-mail com XLSX (``services/notifications.py``).
- ``reconcile``: reconciliação do Asaas (``billing.reconcile_all``, já idempotente).
- ``tokens``: limpeza de tokens vencidos/usados (``lgpd.purge_expired_tokens``).
"""

from __future__ import annotations

import logging
import signal
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

from flask import current_app
from sqlalchemy import func, or_, select

from app import rls
from app.extensions import db
from app.models import Company, DomainEvent

logger = logging.getLogger(__name__)

TASK_EVENTS = "events"
TASK_ALERTS = "alerts"
TASK_WEEKLY = "weekly"
TASK_RECONCILE = "reconcile"
TASK_TOKENS = "tokens"
TASKS = (TASK_EVENTS, TASK_RECONCILE, TASK_TOKENS)

# Intervalo mínimo entre execuções de cada tarefa no modo laço (segundos). ``--once`` roda
# todas as pedidas, sem olhar o intervalo (cron).
DEFAULT_INTERVALS = {
    TASK_EVENTS: 0,  # todo ciclo
    TASK_ALERTS: 15 * 60,
    TASK_WEEKLY: 15 * 60,
    TASK_RECONCILE: 24 * 3600,
    TASK_TOKENS: 24 * 3600,
}

BACKOFF_BASE_SECONDS = 60
BACKOFF_MAX_SECONDS = 6 * 3600


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    """SQLite devolve datetime sem fuso: trata como UTC."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _setting(name: str, default):
    return current_app.config.get(name, default)


def max_attempts() -> int:
    return int(_setting("WORKER_EVENT_MAX_ATTEMPTS", 8))


def backoff(attempts: int) -> timedelta:
    """Espera antes da tentativa seguinte: 60 s × 2^(tentativas − 1), teto de 6 h."""
    seconds = BACKOFF_BASE_SECONDS * (2 ** max(attempts - 1, 0))
    return timedelta(seconds=min(seconds, BACKOFF_MAX_SECONDS))


def company_ids() -> list[uuid.UUID]:
    """Todas as empresas (``companies`` não tem RLS). Ordem estável."""
    return list(db.session.execute(select(Company.id).order_by(Company.created_at, Company.id)).scalars())


# ------------------------------------------------------------------ outbox


def _handlers() -> dict[str, Callable[[DomainEvent], None]]:
    """Consumidor por tipo de evento. Tipo sem consumidor = só marca publicado (eventos
    públicos esperam os webhooks de saída)."""
    from app.services import events, notifications

    return {
        events.PLAN_VISUAL_CUSTOM_CONTRACTED: notifications.on_visual_custom_contracted,
    }


HANDLERS_OVERRIDE: dict[str, Callable[[DomainEvent], None]] | None = None  # testes


def _pending_stmt(company_id: uuid.UUID, now: datetime):
    return (
        select(DomainEvent)
        .where(
            DomainEvent.company_id == company_id,
            DomainEvent.published_at.is_(None),
            DomainEvent.attempts < max_attempts(),
            or_(DomainEvent.next_attempt_at.is_(None), DomainEvent.next_attempt_at <= now),
        )
        .order_by(DomainEvent.created_at, DomainEvent.id)
    )


def _record_failure(company_id: uuid.UUID, event_id: uuid.UUID, exc: BaseException, now: datetime) -> None:
    rls.set_context(company_id=company_id)
    event = db.session.get(DomainEvent, event_id)
    if event is None:  # pragma: no cover - apagado entre a falha e o registro
        return
    event.attempts = (event.attempts or 0) + 1
    event.next_attempt_at = now + backoff(event.attempts)
    event.last_error = exc.__class__.__name__[:200]
    db.session.commit()
    level = logging.ERROR if event.attempts >= max_attempts() else logging.WARNING
    logger.log(
        level,
        "evento %s (%s) falhou: tentativa %s de %s (%s)",
        event.id,
        event.type,
        event.attempts,
        max_attempts(),
        event.last_error,
    )


def process_company_events(company_id: uuid.UUID, now: datetime | None = None, limit: int = 100) -> dict[str, int]:
    """Consome até ``limit`` eventos pendentes da empresa, um por transação."""
    now = now or _now()
    handlers = HANDLERS_OVERRIDE if HANDLERS_OVERRIDE is not None else _handlers()
    result = {"published": 0, "failed": 0}
    seen: set[uuid.UUID] = set()
    for _ in range(limit):
        rls.set_context(company_id=company_id)
        stmt = _pending_stmt(company_id, now)
        if seen:
            stmt = stmt.where(DomainEvent.id.notin_(seen))
        event = db.session.execute(stmt.limit(1).with_for_update(skip_locked=True)).scalar_one_or_none()
        if event is None:
            db.session.rollback()
            break
        seen.add(event.id)
        event_id = event.id
        handler = handlers.get(event.type)
        try:
            if handler is not None:
                handler(event)
            event.published_at = now
            event.next_attempt_at = None
            event.last_error = None
            db.session.commit()
            result["published"] += 1
        except Exception as exc:  # noqa: BLE001 - falha de um evento nunca para o worker
            db.session.rollback()
            result["failed"] += 1
            _record_failure(company_id, event_id, exc, now)
    return result


def process_events(now: datetime | None = None) -> dict[str, int]:
    now = now or _now()
    total = {"published": 0, "failed": 0}
    try:
        for company_id in company_ids():
            part = process_company_events(company_id, now)
            for key in total:
                total[key] += part[key]
    finally:
        rls.set_context(company_id=None)
    return total


def queue_status() -> list[dict]:
    """Por empresa: pendentes (ainda na fila) e esgotados (tentativas no limite)."""
    rows = []
    limit = max_attempts()
    try:
        for company_id in company_ids():
            rls.set_context(company_id=company_id)
            base = select(func.count()).select_from(DomainEvent).where(
                DomainEvent.company_id == company_id, DomainEvent.published_at.is_(None)
            )
            pending = db.session.execute(base.where(DomainEvent.attempts < limit)).scalar_one()
            dead = db.session.execute(base.where(DomainEvent.attempts >= limit)).scalar_one()
            if pending or dead:
                rows.append({"company_id": company_id, "pending": pending, "dead": dead})
        db.session.rollback()
    finally:
        rls.set_context(company_id=None)
    return rows


# ------------------------------------------------------------------ tarefas agendadas


def run_reconcile(now: datetime | None = None) -> dict:
    from app.services.billing import service as billing

    return billing.reconcile_all(now)


def run_tokens(now: datetime | None = None) -> dict:
    from app.services import lgpd

    return lgpd.purge_expired_tokens(now=now or _now(), operator="worker")


RUNNERS: dict[str, Callable[..., dict]] = {
    TASK_EVENTS: process_events,
    TASK_RECONCILE: run_reconcile,
    TASK_TOKENS: run_tokens,
}


def run_task(name: str, now: datetime | None = None) -> dict:
    """Roda uma tarefa isolando a falha (log + rollback); devolve o resumo ou ``{"error": …}``."""
    try:
        result = RUNNERS[name](now)
    except Exception as exc:  # noqa: BLE001 - uma tarefa com erro não derruba as outras
        db.session.rollback()
        rls.set_context(company_id=None)
        logger.exception("tarefa %s falhou (%s)", name, exc.__class__.__name__)
        return {"error": exc.__class__.__name__}
    finally:
        db.session.remove()
    logger.info("tarefa %s: %s", name, result)
    return result


def run_once(tasks: tuple[str, ...] = TASKS, now: datetime | None = None) -> dict[str, dict]:
    return {name: run_task(name, now) for name in tasks}


@dataclass
class Loop:
    """Laço do processo worker. Cada tarefa roda quando o seu intervalo venceu."""

    tasks: tuple[str, ...] = TASKS
    interval: float = 30.0
    intervals: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_INTERVALS))
    stop: threading.Event = field(default_factory=threading.Event)
    last_run: dict[str, float] = field(default_factory=dict)

    def due(self, name: str, clock: float) -> bool:
        last = self.last_run.get(name)
        return last is None or clock - last >= self.intervals.get(name, 0)

    def cycle(self, clock: float | None = None) -> dict[str, dict]:
        clock = time.monotonic() if clock is None else clock
        done = {}
        for name in self.tasks:
            if self.stop.is_set():
                break
            if self.due(name, clock):
                done[name] = run_task(name)
                self.last_run[name] = clock
        return done

    def install_signals(self) -> None:
        def _stop(signum, _frame):
            logger.info("worker: sinal %s recebido, parando no fim do ciclo", signum)
            self.stop.set()

        signal.signal(signal.SIGTERM, _stop)
        signal.signal(signal.SIGINT, _stop)

    def run(self) -> None:
        logger.info("worker iniciado: tarefas %s, intervalo %ss", ",".join(self.tasks), self.interval)
        while not self.stop.is_set():
            self.cycle()
            self.stop.wait(self.interval)
        logger.info("worker parado")
