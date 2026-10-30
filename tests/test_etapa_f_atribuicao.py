"""Etapa F — e-mail ao responsável quando a atividade é atribuída (consome activity.assigned)."""

from __future__ import annotations

from app.extensions import db
from app.models import Activity, DomainEvent, Membership, User
from app.services import email, worker
from app.services.notifications import ASSIGNED_SUBJECT
from tests.conftest import login, post


def _assign(client, app, tenant, user_id):
    return post(client, app, f"/app/atividades/{tenant.activity_id}/responsavel", {"assignee_id": str(user_id)})


def _sent(app, to=None):
    return [m for m in email.outbox(app) if m.subject == ASSIGNED_SUBJECT and (to is None or m.to == to)]


def _run(app):
    with app.app_context():
        return worker.run_task(worker.TASK_EVENTS)


def test_atribuir_envia_email_com_link_pelo_worker(app_factory):
    from tests.conftest import make_tenant

    app = app_factory({"APP_BASE_URL": "https://app.exemplo.com.br"})
    with app.app_context():
        a, _ = make_tenant("A"), make_tenant("B")
    client = app.test_client()
    login(client, app, a.supervisor_email)
    assert _assign(client, app, a, a.operator_id).status_code == 303
    assert _sent(app) == []  # a requisição só grava o evento; quem envia é o worker
    _run(app)
    sent = _sent(app)
    assert [m.to for m in sent] == [a.operator_email]
    body = sent[0].text
    assert f"https://app.exemplo.com.br/app/atividades/{a.activity_id}" in body
    assert "Atividade 1" in body and "Etapa 1" in body and "Projeto A" in body and "Empresa A" in body
    assert "https://app.exemplo.com.br/conta/perfil#notificacoes" in body
    assert "Projeto B" not in body and "senha" not in body.lower().split("troque a senha")[0]
    # Evento publicado: rodar de novo não reenvia.
    _run(app)
    assert len(_sent(app)) == 1
    with app.app_context():
        assert db.session.query(DomainEvent).filter_by(type="activity.assigned", published_at=None).count() == 0


def test_preferencia_desligada_nao_envia_e_evento_e_publicado(client, app, tenants):
    a, _ = tenants
    with app.app_context():
        db.session.get(User, a.operator_id).notify_assignment = False
        db.session.commit()
    login(client, app, a.supervisor_email)
    _assign(client, app, a, a.operator_id)
    _run(app)
    assert _sent(app) == []
    with app.app_context():
        assert db.session.query(DomainEvent).filter_by(type="activity.assigned", published_at=None).count() == 0


def test_quem_se_atribui_nao_recebe(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    _assign(client, app, a, a.owner_id)
    _run(app)
    assert _sent(app) == []


def test_reatribuida_antes_do_worker_so_o_atual_recebe(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    with app.app_context():
        sup_id = db.session.query(User).filter_by(email=a.supervisor_email).one().id
    _assign(client, app, a, a.operator_id)
    _assign(client, app, a, sup_id)
    _run(app)
    assert [m.to for m in _sent(app)] == [a.supervisor_email]


def test_pessoa_desativada_ou_atividade_arquivada_nao_recebe(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    _assign(client, app, a, a.operator_id)
    with app.app_context():
        db.session.query(Membership).filter_by(user_id=a.operator_id).one().active = False
        db.session.commit()
    _run(app)
    assert _sent(app) == []


def test_falha_no_envio_volta_para_a_fila(client, app, tenants, monkeypatch):
    a, _ = tenants
    login(client, app, a.owner_email)
    _assign(client, app, a, a.operator_id)
    with app.app_context():
        def fail(message):
            raise email.EmailError("fora do ar")

        monkeypatch.setattr(email.get_sender(app), "send", fail)
        worker.run_task(worker.TASK_EVENTS)
        event = db.session.query(DomainEvent).filter_by(type="activity.assigned").one()
        assert event.published_at is None and event.attempts == 1 and event.last_error == "EmailError"
        assert db.session.get(Activity, a.activity_id).assignee_id == a.operator_id
