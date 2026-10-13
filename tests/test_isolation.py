"""Isolamento multiempresa: recurso da empresa B acessado por usuário da empresa A → 404.

Toda rota com <uuid:...> da área logada precisa de caso aqui (regra inviolável 1).
"""

from __future__ import annotations

import pytest

from app.extensions import db
from app.models import Activity, ProgressEntry, Stage
from tests.conftest import login, post

# (método, molde da URL, campo do Tenant, dados do POST)
ROUTES = [
    ("GET", "/app/projetos/{id}", "project_id", None),
    ("GET", "/app/projetos/{id}/historico", "project_id", None),
    ("POST", "/app/projetos/{id}/etapas", "project_id", {"name": "Invasora"}),
    ("GET", "/app/etapas/{id}", "stage_id", None),
    ("POST", "/app/etapas/{id}/atividades", "stage_id", {"name": "Invasora", "ideal_minutes": "5"}),
    ("GET", "/app/atividades/{id}", "activity_id", None),
    ("POST", "/app/atividades/{id}/registrar", "activity_id", {"delta": 1}),
]


def _call(client, app, method, url, data):
    if method == "GET":
        return client.get(url)
    return post(client, app, url, data)


@pytest.mark.parametrize("method,template,field,data", ROUTES)
def test_recurso_de_outra_empresa_responde_404(client, app, tenants, method, template, field, data):
    a, b = tenants
    login(client, app, a.owner_email)  # owner: papel máximo, só a empresa impede o acesso
    response = _call(client, app, method, template.format(id=getattr(b, field)), data)
    assert response.status_code == 404


@pytest.mark.parametrize("method,template,field,data", ROUTES)
def test_mesma_rota_funciona_na_propria_empresa(client, app, tenants, method, template, field, data):
    a, _ = tenants
    login(client, app, a.owner_email)
    response = _call(client, app, method, template.format(id=getattr(a, field)), data)
    assert response.status_code in (200, 302, 303)


def test_escrita_bloqueada_nao_altera_dados_de_b(client, app, tenants):
    a, b = tenants
    login(client, app, a.owner_email)
    for method, template, field, data in ROUTES:
        if method == "POST":
            _call(client, app, method, template.format(id=getattr(b, field)), data)
    with app.app_context():
        activity = db.session.get(Activity, b.activity_id)
        assert activity.units_done == 0 and activity.version == 1
        assert db.session.query(ProgressEntry).filter_by(company_id=b.company_id).count() == 0
        assert db.session.query(Stage).filter_by(company_id=b.company_id).count() == 1
        assert db.session.query(Activity).filter_by(company_id=b.company_id).count() == 2


def test_lista_de_projetos_so_mostra_a_propria_empresa(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    page = client.get("/app/projetos").get_data(as_text=True)
    assert "Projeto A" in page
    assert "Projeto B" not in page


def test_company_id_forjado_na_sessao_nao_da_acesso(client, app, tenants):
    a, b = tenants
    login(client, app, a.owner_email)
    with client.session_transaction() as sess:
        sess["company_id"] = str(b.company_id)  # usuário de A sem vínculo com B
    assert client.get(f"/app/projetos/{b.project_id}").status_code == 404
    page = client.get("/app/projetos").get_data(as_text=True)
    assert "Projeto B" not in page and "Projeto A" in page


def test_vinculo_desativado_perde_acesso(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    from app.models import Membership

    with app.app_context():
        membership = db.session.query(Membership).filter_by(user_id=a.operator_id).one()
        membership.active = False
        db.session.commit()
    assert client.get(f"/app/projetos/{a.project_id}").status_code == 403


def test_toda_rota_com_uuid_tem_caso_de_isolamento(app):
    cobertas = {template.replace("{id}", "") for _, template, _, _ in ROUTES}
    for rule in app.url_map.iter_rules():
        if "<uuid:" not in rule.rule:
            continue
        sem_parametro = rule.rule.split("<")[0] + rule.rule.split(">", 1)[1]
        assert sem_parametro in cobertas, f"rota {rule.rule} sem teste de isolamento A/B"


def test_registrar_pecas_valida_maximo_e_grava_historico(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    url = f"/app/atividades/{a.activity_id}/registrar"
    assert post(client, app, url, {"delta": 3, "version": 1}).status_code == 303
    assert post(client, app, url, {"delta": 2, "version": 2}).status_code == 303
    with app.app_context():
        activity = db.session.get(Activity, a.activity_id)
        assert activity.units_done == 5 and activity.version == 3
    # +20 numa atividade com 5/10 → "máximo 5"
    response = post(client, app, url, {"delta": 20, "version": 3})
    assert response.status_code == 400
    assert "Máximo 5" in response.get_data(as_text=True)
    # versão antiga → conflito 409
    assert post(client, app, url, {"delta": 1, "version": 1}).status_code == 409
    with app.app_context():
        activity = db.session.get(Activity, a.activity_id)
        assert activity.units_done == 5
        entries = db.session.query(ProgressEntry).filter_by(activity_id=a.activity_id).all()
        assert sorted(e.delta for e in entries) == [2, 3]
    history = client.get(f"/app/projetos/{a.project_id}/historico").get_data(as_text=True)
    assert "+3" in history and "+2" in history
