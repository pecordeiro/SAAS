"""Auditoria do sistema (2026-10-28, docs/plano/system-findings.md): correções com teste.

- F-01: pedido do HTMX com a sessão encerrada não pode virar “salvo” (o XHR seguia o 302 do login).
- F-03: o Painel da operação não faz uma consulta por etapa nem lê os feriados por projeto.
"""

from __future__ import annotations

from decimal import Decimal

from flask import g
from sqlalchemy import event

from app.extensions import db
from app.models import Activity, Company, User
from app.services import projects as svc
from tests.conftest import login, post

HX = {"HX-Request": "true"}


def _end_session(app, user_id):
    """Como trocar a senha em outro aparelho: a sessão deste navegador deixa de valer."""
    with app.app_context():
        user = db.session.get(User, user_id)
        user.session_version += 1
        db.session.commit()


def test_htmx_com_sessao_encerrada_recebe_401_e_vai_ao_login(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    _end_session(app, a.operator_id)
    page = f"/app/preencher?projeto={a.project_id}&etapa={a.stage_id}"
    response = post(client, app, f"/app/preencher/atividades/{a.activity_id}",
                    {"campo": "units_done", "units_done": "4", "version": "1"},
                    headers={**HX, "HX-Current-URL": f"http://localhost{page}"})
    assert response.status_code == 401
    assert "Location" not in response.headers
    target = response.headers["HX-Redirect"]
    assert target.startswith("/entrar?next=/app/preencher?projeto")  # volta para a tela, não para o POST
    assert response.get_data() == b""
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).units_done == 0  # nada foi gravado


def test_htmx_de_outro_host_nao_vira_next(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    _end_session(app, a.operator_id)
    response = post(client, app, f"/app/preencher/atividades/{a.activity_id}",
                    {"campo": "units_done", "units_done": "4", "version": "1"},
                    headers={**HX, "HX-Current-URL": "https://exemplo.invalid/app/preencher"})
    assert response.status_code == 401
    assert response.headers["HX-Redirect"] == "/entrar"


def test_navegacao_normal_continua_com_302_para_o_login(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    _end_session(app, a.operator_id)
    response = client.get("/app/preencher")
    assert response.status_code == 302
    assert "/entrar" in response.headers["Location"]
    assert "HX-Redirect" not in response.headers


def test_outros_redirecionamentos_do_htmx_nao_mudam(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    response = post(client, app, f"/app/preencher/projetos/{a.project_id}/etapas", {"name": "Etapa nova"}, headers=HX)
    assert response.status_code == 303
    assert "/app/preencher" in response.headers["Location"]


def _queries(app, client, url):
    with app.app_context():
        engine = db.engine
    count = {"n": 0}

    def tick(*_args, **_kwargs):
        count["n"] += 1

    event.listen(engine, "before_cursor_execute", tick)
    try:
        response = client.get(url)
    finally:
        event.remove(engine, "before_cursor_execute", tick)
    assert response.status_code == 200
    return count["n"]


def test_painel_da_operacao_nao_cresce_uma_consulta_por_projeto(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    one = _queries(app, client, "/app/")
    with app.app_context():
        company = db.session.get(Company, a.company_id)
        for i in range(4):
            with app.test_request_context():
                g.company = company
                svc.create_project(company, name=f"Lote {i}", quantity=10, start_date=None, due_date=None, people=2,
                                   hours_per_day=Decimal("8"), stages=[svc.NewStage(name=f"Etapa {j}") for j in range(6)],
                                   progress_mode="simples")
        db.session.commit()
    five = _queries(app, client, "/app/")
    assert five == one, f"1 projeto: {one} consultas; 5 projetos: {five}"
