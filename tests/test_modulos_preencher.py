"""Módulos opcionais (R6) dentro de “Preencher etapas” (2026-10-28).

Antes, ligar um módulo em Configurações › Módulos só mudava a tela antiga do projeto: em Preencher
etapas (a tela de uso diário) não havia onde marcar “aguardando peça”, abrir fotos, checklist,
unidades nem atribuir responsável. Aqui ficam os controles; as rotas continuam recusando sozinhas
quando o módulo está desligado e checando o papel (ADR-0009)."""

from __future__ import annotations

import re

from app.extensions import db
from app.models import Activity, Stage
from tests.conftest import login, post, set_tenant_modules


def _fill(client, a, **query):
    q = "&".join(f"{k}={v}" for k, v in query.items())
    response = client.get(f"/app/preencher?projeto={a.project_id}&etapa={a.stage_id}" + (f"&{q}" if q else ""))
    assert response.status_code == 200
    return response.get_data(as_text=True)


def _modules(app, a, keys):
    with app.app_context():
        set_tenant_modules(a.company_id, keys)
        db.session.commit()


def test_modulos_ligados_aparecem_para_o_supervisor(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    html = _fill(client, a)
    assert "Marcar aguardando peça" in html
    assert "Fotos e comentários" in html
    assert "Checklist de inspeção" in html
    assert "Progresso por pessoa" in html
    # responsável: bolinha ao lado de cada subatividade, com a janelinha “Atribuir a” (sem botão “Responsáveis”)
    assert "data-who" in html and "Atribuir a" in html and "Digite um nome ou um e-mail" in html
    assert f'name="assignee_id" value="{a.operator_id}"' in html
    assert "Responsáveis" not in html
    assert f"/app/projetos/{a.project_id}/unidades" in html  # Unidades, no topo
    assert f"/app/etapas/{a.stage_id}/aguardando-peca" in html
    assert re.search(r'name="voltar" value="preencher"', html)  # a ação volta para esta tela


def test_modulos_desligados_nao_aparecem(client, app, tenants):
    a, _ = tenants
    _modules(app, a, [])
    login(client, app, a.supervisor_email)
    html = _fill(client, a)
    for text in ("aguardando peça", "Fotos e comentários", "Checklist de inspeção", "Progresso por pessoa", "Atribuir a"):
        assert text not in html, text
    assert "data-who" not in html and "who__avatar" not in html
    assert f"/app/projetos/{a.project_id}/unidades" not in html  # (“Unidades prontas” é outra coisa)
    assert "stage-extras" not in html


def test_operador_ve_fotos_e_checklist_mas_nao_marca_peca_nem_atribui(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    html = _fill(client, a)
    assert "Fotos e comentários" in html and "Checklist de inspeção" in html
    assert "Marcar aguardando peça" not in html and "data-who" not in html and "Progresso por pessoa" not in html
    # e a rota continua recusando no servidor
    response = post(client, app, f"/app/etapas/{a.stage_id}/aguardando-peca", {"waiting": "y", "voltar": "preencher"})
    assert response.status_code == 403


def test_marcar_aguardando_peca_volta_para_preencher_e_aparece(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    with app.app_context():
        version = db.session.get(Stage, a.stage_id).version
    response = post(client, app, f"/app/etapas/{a.stage_id}/aguardando-peca",
                    {"waiting": "y", "expected_on": "2026-11-05", "note": "Chega do fornecedor", "version": version,
                     "voltar": "preencher"})
    assert response.status_code == 303
    location = response.headers["Location"]
    assert location.startswith("/app/preencher") and f"etapa={a.stage_id}" in location
    with app.app_context():
        stage = db.session.get(Stage, a.stage_id)
        assert stage.waiting_part and stage.part_note == "Chega do fornecedor"
    html = client.get(location).get_data(as_text=True)
    assert "Aguardando peça · previsão 05/11/2026" in html and "Chega do fornecedor" in html
    assert "Atualizar aguardando peça" in html
    assert "Etapa marcada como aguardando peça." in html  # mensagem


def test_aguardando_peca_com_versao_velha_nao_grava_e_volta_com_aviso(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    response = post(client, app, f"/app/etapas/{a.stage_id}/aguardando-peca",
                    {"waiting": "y", "version": 999, "voltar": "preencher"})
    assert response.status_code == 303 and response.headers["Location"].startswith("/app/preencher")
    with app.app_context():
        assert not db.session.get(Stage, a.stage_id).waiting_part
    html = client.get(response.headers["Location"]).get_data(as_text=True)
    assert "Outra pessoa alterou esta etapa" in html


def test_aguardando_peca_sem_voltar_continua_na_tela_antiga(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    with app.app_context():
        version = db.session.get(Stage, a.stage_id).version
    response = post(client, app, f"/app/etapas/{a.stage_id}/aguardando-peca", {"waiting": "y", "version": version})
    assert response.status_code == 303
    assert response.headers["Location"].startswith(f"/app/projetos/{a.project_id}")


def test_atribuir_responsavel_pelo_preencher_volta_para_a_etapa(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    response = post(client, app, f"/app/atividades/{a.activity_id}/responsavel",
                    {"assignee_id": str(a.operator_id), "voltar": "preencher"})
    assert response.status_code == 303
    location = response.headers["Location"]
    assert location.startswith("/app/preencher") and f"etapa={a.stage_id}" in location
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).assignee_id == a.operator_id
    html = client.get(location).get_data(as_text=True)
    assert "responsável operator A. Trocar" in html  # a bolinha mostra quem é (iniciais OA)
    assert '<span aria-hidden="true">OA</span>' in html
    assert "is-current" in html  # a pessoa atual aparece marcada na janelinha


def test_rotas_dos_modulos_recusam_quando_desligados(client, app, tenants):
    a, _ = tenants
    _modules(app, a, [])
    login(client, app, a.supervisor_email)
    assert post(client, app, f"/app/etapas/{a.stage_id}/aguardando-peca", {"waiting": "y", "voltar": "preencher"}).status_code == 404
    assert post(client, app, f"/app/atividades/{a.activity_id}/responsavel",
                {"assignee_id": str(a.operator_id), "voltar": "preencher"}).status_code == 404
    assert client.get(f"/app/etapas/{a.stage_id}/checklist").status_code == 404
    assert client.get(f"/app/atividades/{a.activity_id}/evidencias").status_code == 404


def test_voltar_dos_modulos_leva_para_preencher(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    for url in (f"/app/atividades/{a.activity_id}/evidencias", f"/app/etapas/{a.stage_id}/checklist"):
        html = client.get(url).get_data(as_text=True)
        assert f'href="/app/preencher?projeto={a.project_id}&amp;etapa={a.stage_id}"' in html, url
    html = client.get(f"/app/projetos/{a.project_id}/unidades").get_data(as_text=True)
    assert f'href="/app/preencher?projeto={a.project_id}"' in html


def test_tirar_o_responsavel_pela_janelinha(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    post(client, app, f"/app/atividades/{a.activity_id}/responsavel", {"assignee_id": str(a.operator_id), "voltar": "preencher"})
    html = _fill(client, a)
    assert "Tirar o responsável" in html
    response = post(client, app, f"/app/atividades/{a.activity_id}/responsavel", {"assignee_id": "", "voltar": "preencher"})
    assert response.status_code == 303 and response.headers["Location"].startswith("/app/preencher")
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).assignee_id is None
    html = _fill(client, a)
    assert "who__avatar--empty" in html and "Tirar o responsável" not in html


def test_operador_ve_a_bolinha_mas_nao_troca_o_responsavel(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    post(client, app, f"/app/atividades/{a.activity_id}/responsavel", {"assignee_id": str(a.operator_id), "voltar": "preencher"})
    other = app.test_client()
    login(other, app, a.operator_email)
    html = _fill(other, a)
    assert 'role="img"' in html and "responsável operator A" in html
    assert "data-who" not in html and "Atribuir a" not in html
    assert post(other, app, f"/app/atividades/{a.activity_id}/responsavel", {"assignee_id": "", "voltar": "preencher"}).status_code == 403


def test_iniciais_da_bolinha():
    from app.formatting import iniciais

    assert iniciais("Marina Souza") == "MS"
    assert iniciais("Jandir - Solis Tecnologia") == "JT"  # primeira e última palavra
    assert iniciais("pedro") == "P"
    assert iniciais("  RODRIGO   lima ") == "RL"
    assert iniciais("João Pereira") == "JP"
    assert iniciais("") == "?" and iniciais(None) == "?" and iniciais("- -") == "?"
