"""Etapa F — worker (ADR-0010): outbox com tentativas/backoff, tarefas agendadas, CLI."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models import DomainEvent, EmailConfirmation, Invitation, PasswordReset
from app.models.privacy import PlatformAuditLog
from app.services import email, events, worker
from tests.conftest import make_tenant

NOW = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def handlers():
    """Troca os consumidores do outbox só durante o teste."""
    calls: list = []
    table: dict = {}
    worker.HANDLERS_OVERRIDE = table
    yield table, calls
    worker.HANDLERS_OVERRIDE = None


def _pending(company_id):
    return list(
        db.session.execute(
            select(DomainEvent).where(DomainEvent.company_id == company_id, DomainEvent.published_at.is_(None))
        ).scalars()
    )


def test_backoff_exponencial_com_teto():
    assert worker.backoff(1) == timedelta(seconds=60)
    assert worker.backoff(2) == timedelta(seconds=120)
    assert worker.backoff(4) == timedelta(seconds=480)
    assert worker.backoff(30) == timedelta(hours=6)


def test_publica_eventos_de_todas_as_empresas_e_tipo_sem_consumidor_so_marca(app, handlers):
    table, calls = handlers
    table[events.PROJECT_CREATED] = lambda ev: calls.append((ev.company_id, ev.type))
    with app.app_context():
        a, b = make_tenant("A"), make_tenant("B")
        assert len(_pending(a.company_id)) == 1 and len(_pending(b.company_id)) == 1
        result = worker.process_events(NOW)
        assert result == {"published": 2, "failed": 0}
        assert sorted(c for c, _ in calls) == sorted([a.company_id, b.company_id])
        assert _pending(a.company_id) == [] and _pending(b.company_id) == []
        # Rodar de novo não entrega duas vezes.
        assert worker.process_events(NOW) == {"published": 0, "failed": 0}
        assert len(calls) == 2


def test_falha_conta_tentativa_espera_backoff_e_esgota(app_factory, handlers):
    app = app_factory({"WORKER_EVENT_MAX_ATTEMPTS": 3})
    table, calls = handlers

    def boom(ev):
        calls.append(ev.id)
        raise RuntimeError("detalhe que não pode ir para o banco: maria@exemplo.com")

    table[events.PROJECT_CREATED] = boom
    with app.app_context():
        a = make_tenant("A")
        assert worker.process_events(NOW) == {"published": 0, "failed": 1}
        event = _pending(a.company_id)[0]
        assert event.attempts == 1
        assert event.last_error == "RuntimeError"  # só o nome, nunca a mensagem
        assert worker._aware(event.next_attempt_at) == NOW + timedelta(seconds=60)
        # Antes do backoff vencer: não tenta de novo.
        assert worker.process_events(NOW + timedelta(seconds=30)) == {"published": 0, "failed": 0}
        assert worker.process_events(NOW + timedelta(seconds=61)) == {"published": 0, "failed": 1}
        assert worker.process_events(NOW + timedelta(hours=1)) == {"published": 0, "failed": 1}
        assert _pending(a.company_id)[0].attempts == 3
        # Esgotado: sai da fila e aparece no status.
        assert worker.process_events(NOW + timedelta(days=1)) == {"published": 0, "failed": 0}
        assert len(calls) == 3
        assert worker.queue_status() == [{"company_id": a.company_id, "pending": 0, "dead": 1}]


def test_falha_de_um_evento_nao_impede_os_outros(app, handlers):
    table, _ = handlers
    table[events.PROJECT_CREATED] = lambda ev: (_ for _ in ()).throw(ValueError("x"))
    with app.app_context():
        a = make_tenant("A")
        events.emit(a.company_id, events.STAGE_COMPLETED, {"stage_id": a.stage_id})
        db.session.commit()
        assert worker.process_events(NOW) == {"published": 1, "failed": 1}
        pending = _pending(a.company_id)
        assert [e.type for e in pending] == [events.PROJECT_CREATED]


def test_aviso_a_equipe_da_requisicao_de_identidade_visual(app_factory):
    app = app_factory({"STAFF_NOTIFY_EMAIL": "equipe@plataforma.example", "APP_BASE_URL": "https://app.exemplo.com.br"})
    with app.app_context():
        a = make_tenant("A")
        events.emit(a.company_id, events.PLAN_VISUAL_CUSTOM_CONTRACTED, {"plano": "empresa"})
        db.session.commit()
        worker.process_events(NOW)
        sent = [m for m in email.outbox(app) if m.to == "equipe@plataforma.example"]
        assert len(sent) == 1
        assert "https://app.exemplo.com.br/interno" in sent[0].text
        assert "plano empresa" in sent[0].text
        assert _pending(a.company_id) == []


def test_sem_email_da_equipe_o_evento_so_e_marcado(app):
    with app.app_context():
        a = make_tenant("A")
        events.emit(a.company_id, events.PLAN_VISUAL_CUSTOM_CONTRACTED, {"plano": "empresa"})
        db.session.commit()
        worker.process_events(NOW)
        assert email.outbox(app) == [] and _pending(a.company_id) == []


def test_falha_de_entrega_do_email_volta_para_a_fila(app_factory, monkeypatch):
    app = app_factory({"STAFF_NOTIFY_EMAIL": "equipe@plataforma.example"})
    with app.app_context():
        a = make_tenant("A")
        events.emit(a.company_id, events.PLAN_VISUAL_CUSTOM_CONTRACTED, {"plano": "empresa"})
        db.session.commit()

        def fail(message):
            raise email.EmailError("fora do ar")

        monkeypatch.setattr(email.get_sender(app), "send", fail)
        worker.process_events(NOW)
        failed = [e for e in _pending(a.company_id) if e.type == events.PLAN_VISUAL_CUSTOM_CONTRACTED]
        assert failed[0].attempts == 1 and failed[0].last_error == "EmailError"


def test_limpeza_de_tokens_apaga_so_os_vencidos_ou_usados_antigos(app):
    from app.models import User

    with app.app_context():
        a = make_tenant("A")
        user = db.session.get(User, a.owner_id)
        old = NOW - timedelta(days=40)
        db.session.add_all(
            [
                PasswordReset(user_id=user.id, token_hash="a" * 64, expires_at=old + timedelta(hours=1), created_at=old),
                PasswordReset(user_id=user.id, token_hash="b" * 64, expires_at=NOW + timedelta(hours=1), created_at=NOW),
                EmailConfirmation(user_id=user.id, email=user.email, token_hash="c" * 64,
                                  expires_at=old + timedelta(days=1), used_at=old, created_at=old),
                Invitation(company_id=a.company_id, email="x@exemplo.com", role="operator", token_hash="d" * 64,
                           expires_at=old + timedelta(days=7), created_at=old),
                Invitation(company_id=a.company_id, email="y@exemplo.com", role="operator", token_hash="e" * 64,
                           expires_at=NOW + timedelta(days=7), created_at=NOW),
            ]
        )
        db.session.commit()
        result = worker.run_task(worker.TASK_TOKENS, NOW)
        assert result == {"password_resets": 1, "email_confirmations": 1, "invitations": 1}
        assert db.session.query(PasswordReset).count() == 1
        assert db.session.query(Invitation).count() == 1
        assert db.session.query(PlatformAuditLog).filter_by(action="worker.tokens_purged").count() == 1
        # Idempotente: de novo não apaga nada nem audita de novo.
        assert worker.run_task(worker.TASK_TOKENS, NOW) == {"password_resets": 0, "email_confirmations": 0, "invitations": 0}
        assert db.session.query(PlatformAuditLog).filter_by(action="worker.tokens_purged").count() == 1


def test_reconciliacao_reaproveita_o_servico_de_cobranca(app):
    with app.app_context():
        make_tenant("A", plan="profissional")
        result = worker.run_task(worker.TASK_RECONCILE, NOW)
        assert result["checked"] == 1 and result["errors"] == 0


def test_tarefa_com_erro_nao_derruba_as_outras(app, monkeypatch):
    monkeypatch.setitem(worker.RUNNERS, worker.TASK_TOKENS, lambda now: 1 / 0)
    with app.app_context():
        make_tenant("A")
        results = worker.run_once((worker.TASK_TOKENS, worker.TASK_EVENTS), NOW)
        assert results[worker.TASK_TOKENS] == {"error": "ZeroDivisionError"}
        assert results[worker.TASK_EVENTS]["published"] == 1


def test_laco_respeita_o_intervalo_de_cada_tarefa(app, monkeypatch):
    calls = []
    monkeypatch.setitem(worker.RUNNERS, worker.TASK_EVENTS, lambda now: calls.append("events") or {})
    monkeypatch.setitem(worker.RUNNERS, worker.TASK_TOKENS, lambda now: calls.append("tokens") or {})
    loop = worker.Loop(tasks=(worker.TASK_EVENTS, worker.TASK_TOKENS), intervals={"events": 0, "tokens": 3600})
    with app.app_context():
        loop.cycle(clock=0)
        loop.cycle(clock=10)
        loop.cycle(clock=3601)
    assert calls == ["events", "tokens", "events", "events", "tokens"]
    loop.stop.set()
    with app.app_context():
        assert loop.cycle(clock=99999) == {}


def test_cli_worker_run_once_e_status(app):
    with app.app_context():
        make_tenant("A")
    runner = app.test_cli_runner()
    status = runner.invoke(args=["worker", "status"])
    assert "pendentes=1" in status.output
    result = runner.invoke(args=["worker", "run", "--once", "--task", "events"])
    assert result.exit_code == 0, result.output
    assert "events: {'published': 1, 'failed': 0}" in result.output
    assert "Fila vazia" in runner.invoke(args=["worker", "status"]).output
