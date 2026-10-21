"""Reestruturação R3–R5: rotas de Preencher etapas, Meta e equipe e Como funciona.

Casos A/B ficam em tests/test_isolation.py (bloco R3–R5)."""

from __future__ import annotations

from decimal import Decimal

from flask import g

from app.extensions import db
from app.models import Activity, AuditLog, Company, Project, ProgressEntry, Stage
from app.services import audit
from app.services import projects as svc
from tests.conftest import login, post

HX = {"HX-Request": "true"}


def _simple_project(company, name="Simples", quantity=20, stages=("Corte", "Solda")):
    project = svc.create_project(
        company, name=name, quantity=quantity, start_date=None, due_date=None, people=2,
        hours_per_day=Decimal("8"), stages=[svc.NewStage(name=n) for n in stages], progress_mode="simples",
    )
    db.session.commit()
    return project


# ---------------------------------------------------------------- Preencher etapas


def test_telas_abrem_para_cada_papel(client, app, tenants):
    a, _ = tenants
    for email in (a.owner_email, a.operator_email):
        login(client, app, email)
        for url in ("/app/preencher", f"/app/preencher?projeto={a.project_id}&etapa={a.stage_id}",
                    "/app/meta-e-equipe", "/app/como-funciona", "/app/preencher?etapa=nao-e-uuid"):
            response = client.get(url)
            assert response.status_code == 200, url


def test_preencher_mostra_lista_tabela_e_celulas(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    html = client.get(f"/app/preencher?projeto={a.project_id}").get_data(as_text=True)
    assert "Atividade 1" in html and "Total da etapa" in html and 'class="cell' in html
    assert "Progresso pelas tarefas" in html and "Nova subatividade" in html
    assert f'id="lista-info-{a.stage_id}"' in html


def test_celula_de_pecas_salva_e_devolve_numeros_do_servidor(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    response = post(client, app, f"/app/preencher/atividades/{a.activity_id}",
                    {"campo": "units_done", "units_done": "4", "version": "1"}, headers=HX)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Salvo" in html and "operator A" in html and 'hx-swap-oob="true"' in html
    assert f'id="v-{a.activity_id}" name="version" value="2"' in html  # versão nova
    assert "4/10" in html
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).units_done == 4


def test_celula_recusa_peca_invalida_com_mensagem(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    for raw, msg in (("2,5", "número inteiro"), ("11", "previstas (10)"), ("-1", "número inteiro"), ("", "número inteiro")):
        response = post(client, app, f"/app/preencher/atividades/{a.activity_id}",
                        {"campo": "units_done", "units_done": raw, "version": "1"}, headers=HX)
        assert response.status_code == 400 and msg in response.get_data(as_text=True), raw
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).units_done == 0


def test_operador_nao_edita_estrutura_nem_diminui(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    url = f"/app/preencher/atividades/{a.activity_id}"
    assert post(client, app, url, {"campo": "name", "name": "Outro nome", "version": "1"}, headers=HX).status_code == 403
    assert post(client, app, url, {"campo": "ideal_minutes", "ideal_minutes": "99", "version": "1"}, headers=HX).status_code == 403
    assert post(client, app, url, {"campo": "units_done", "units_done": "5", "version": "1"}, headers=HX).status_code == 200
    response = post(client, app, url, {"campo": "units_done", "units_done": "3", "version": "2"}, headers=HX)
    assert response.status_code == 400 and "supervisor" in response.get_data(as_text=True)
    assert post(client, app, f"/app/preencher/etapas/{a.stage_id}", {"campo": "name", "name": "X", "version": "1"}).status_code == 403
    assert post(client, app, f"/app/preencher/etapas/{a.stage_id}/atividades", {"name": "Nova"}).status_code == 403
    html = client.get("/app/preencher").get_data(as_text=True)
    assert 'id="nome-etapa"' not in html and "Excluir etapa" not in html and 'name="units_done"' in html


def test_versao_velha_responde_409_com_valor_atual(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    url = f"/app/preencher/atividades/{a.activity_id}"
    assert post(client, app, url, {"campo": "units_done", "units_done": "2", "version": "1"}, headers=HX).status_code == 200
    response = post(client, app, url, {"campo": "ideal_minutes", "ideal_minutes": "12", "version": "1"}, headers=HX)
    assert response.status_code == 409
    html = response.get_data(as_text=True)
    assert "Outra pessoa" in html and "2 de 10" in html and f'id="v-{a.activity_id}" name="version" value="2"' in html
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).ideal_minutes == Decimal("10.00")


def test_supervisor_edita_nome_tempo_e_corrige_para_baixo(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    url = f"/app/preencher/atividades/{a.activity_id}"
    assert post(client, app, url, {"campo": "name", "name": "Cortar", "version": "1"}, headers=HX).status_code == 200
    assert post(client, app, url, {"campo": "ideal_minutes", "ideal_minutes": "7,5", "version": "2"}, headers=HX).status_code == 200
    assert post(client, app, url, {"campo": "units_done", "units_done": "6", "version": "3"}, headers=HX).status_code == 200
    assert post(client, app, url, {"campo": "units_done", "units_done": "1", "version": "4"}, headers=HX).status_code == 200
    with app.app_context():
        act = db.session.get(Activity, a.activity_id)
        assert (act.name, act.ideal_minutes, act.units_done) == ("Cortar", Decimal("7.50"), 1)
        assert db.session.query(AuditLog).filter_by(action=audit.PROGRESS_CORRECTED).count() == 1


def test_sem_js_botao_salvar_manda_a_linha_inteira(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    response = post(client, app, f"/app/preencher/atividades/{a.activity_id}",
                    {"name": "Atividade 1", "ideal_minutes": "20", "units_done": "3", "version": "1"})
    assert response.status_code == 303 and f"etapa={a.stage_id}" in response.headers["Location"]
    with app.app_context():
        act = db.session.get(Activity, a.activity_id)
        assert act.ideal_minutes == Decimal("20.00") and act.units_done == 3


def test_linha_vazia_inclui_subatividade_e_renomear_etapa(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    response = post(client, app, f"/app/preencher/etapas/{a.stage_id}/atividades",
                    {"name": "Pintar", "ideal_minutes": "5", "units_done": "2"}, headers=HX)
    assert response.status_code == 200 and 'id="painel-etapa"' in response.get_data(as_text=True)
    response = post(client, app, f"/app/preencher/etapas/{a.stage_id}", {"campo": "name", "name": "Preparação", "version": "1"}, headers=HX)
    assert response.status_code == 200
    with app.app_context():
        stage = db.session.get(Stage, a.stage_id)
        assert stage.name == "Preparação"
        novo = [x for x in stage.activities if x.name == "Pintar"][0]
        assert novo.units_done == 2
        assert db.session.query(ProgressEntry).filter_by(activity_id=novo.id).one().delta == 2


def test_excluir_e_desfazer_pela_tela(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    response = post(client, app, f"/app/atividades/{a.activity_id}/arquivar", {"voltar": "preencher"})
    assert response.status_code == 303 and "/app/preencher" in response.headers["Location"]
    html = client.get(f"/app/preencher?projeto={a.project_id}").get_data(as_text=True)
    assert "Subatividades excluídas (1)" in html
    assert post(client, app, f"/app/preencher/atividades/{a.activity_id}/desfazer-exclusao").status_code == 303
    assert post(client, app, f"/app/etapas/{a.stage_id}/arquivar", {"voltar": "preencher"}).status_code == 303
    assert "Etapas excluídas (1)" in client.get(f"/app/preencher?projeto={a.project_id}").get_data(as_text=True)
    assert post(client, app, f"/app/preencher/etapas/{a.stage_id}/desfazer-exclusao").status_code == 303
    with app.app_context():
        assert db.session.get(Stage, a.stage_id).archived_at is None
        assert db.session.get(Activity, a.activity_id).archived_at is None


def test_reordenar_e_mover_voltam_para_preencher(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    response = post(client, app, f"/app/projetos/{a.project_id}/etapas/ordem", {"order": [str(a.stage_id)], "voltar": "preencher"})
    assert response.status_code == 303 and "/app/preencher" in response.headers["Location"]
    response = post(client, app, f"/app/preencher/projetos/{a.project_id}/etapas", {"name": "Pintura"})
    assert response.status_code == 303
    response = post(client, app, f"/app/etapas/{a.stage_id}/mover", {"direction": "down", "voltar": "preencher"})
    assert response.status_code == 303 and "/app/preencher" in response.headers["Location"]
    with app.app_context():
        assert [s.name for s in db.session.get(Project, a.project_id).stages] == ["Pintura", "Etapa 1"]


# ---------------------------------------------------------------- modo simples


def test_modo_simples_na_tela_e_percentual_pela_rota(client, app, tenants):
    a, _ = tenants
    with app.test_request_context("/"):
        g.company = db.session.get(Company, a.company_id)
        project = _simple_project(g.company)
        stage_id, project_id = project.stages[0].id, project.id
        act_version = project.stages[0].activities[0].version
    login(client, app, a.operator_email)
    html = client.get(f"/app/preencher?projeto={project_id}").get_data(as_text=True)
    assert 'name="percent"' in html and "Modo simples" in html and "Nova subatividade" not in html
    response = post(client, app, f"/app/preencher/etapas/{stage_id}",
                    {"campo": "percent", "percent": "45", "activity_version": str(act_version)}, headers=HX)
    assert response.status_code == 200 and "9 de 20" in response.get_data(as_text=True)
    bad = post(client, app, f"/app/preencher/etapas/{stage_id}", {"campo": "percent", "percent": "120"}, headers=HX)
    assert bad.status_code == 400 and "0 a 100" in bad.get_data(as_text=True)
    assert post(client, app, f"/app/preencher/etapas/{stage_id}", {"campo": "ideal_minutes", "ideal_minutes": "30"}).status_code == 403
    with app.app_context():
        assert db.session.get(Stage, stage_id).activities[0].units_done == 9


# ---------------------------------------------------------------- Meta e equipe e Como funciona


def test_meta_e_equipe_salva_campo_e_recalcula(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    url = f"/app/meta-e-equipe/{a.project_id}"
    response = post(client, app, url, {"campo": "people", "people": "3"}, headers=HX)
    html = response.get_data(as_text=True)
    assert response.status_code == 200 and "Salvo (pessoas)" in html and "equipe atual" in html
    assert 'id="equipe-caixas"' in html
    bad = post(client, app, url, {"campo": "quantity", "quantity": "0"}, headers=HX)
    assert bad.status_code == 400 and "1 a 100000" in bad.get_data(as_text=True)
    assert post(client, app, url, {"campo": "hours_per_day", "hours_per_day": "7,5"}, headers=HX).status_code == 200
    assert post(client, app, url, {"campo": "due_date", "due_date": "2030-01-31"}, headers=HX).status_code == 200
    with app.app_context():
        p = db.session.get(Project, a.project_id)
        assert (p.people, p.hours_per_day, str(p.due_date)) == (3, Decimal("7.50"), "2030-01-31")
    page = client.get(f"/app/meta-e-equipe?projeto={a.project_id}").get_data(as_text=True)
    assert page.count('class="is-current"') == 1 and "6 pessoas" in page


def test_meta_e_equipe_operador_so_ve(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    page = client.get("/app/meta-e-equipe").get_data(as_text=True)
    assert "Só supervisores" in page and 'name="people"' not in page
    assert post(client, app, f"/app/meta-e-equipe/{a.project_id}", {"campo": "people", "people": "3"}).status_code == 403
    assert post(client, app, f"/app/meta-e-equipe/{a.project_id}/modo", {"progress_mode": "simples"}).status_code == 403


def test_trocar_modo_pela_tela_explica_quando_nao_pode(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    response = post(client, app, f"/app/meta-e-equipe/{a.project_id}/modo", {"progress_mode": "simples"})
    assert response.status_code == 400 and "no máximo uma subatividade" in response.get_data(as_text=True)
    with app.app_context():
        assert db.session.get(Project, a.project_id).progress_mode == "detalhado"


def test_novo_projeto_pela_tela_comeca_no_modo_simples(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    page = client.get("/app/projetos/novo").get_data(as_text=True)
    assert 'name="progress_mode" value="simples" checked' in page
    response = post(client, app, "/app/projetos/novo", {
        "name": "Lote novo", "quantity": "5", "people": "1", "hours_per_day": "8", "progress_mode": "simples",
        "stages-0-name": "Corte", "stages-1-name": "Solda", "stages-1-activities": "Solda; 45",
    })
    assert response.status_code == 303
    with app.app_context():
        project = db.session.query(Project).filter_by(name="Lote novo").one()
        assert project.progress_mode == "simples"
        assert [(s.name, [(x.name, x.ideal_minutes) for x in s.activities]) for s in project.stages] == [
            ("Corte", [("Corte", svc.SIMPLE_DEFAULT_MINUTES)]), ("Solda", [("Solda", Decimal("45.00"))]),
        ]
    bad = post(client, app, "/app/projetos/novo", {
        "name": "Lote 2", "quantity": "5", "people": "1", "hours_per_day": "8", "progress_mode": "simples",
        "stages-0-name": "Corte", "stages-0-activities": "a; 1\nb; 2",
    })
    assert bad.status_code == 400 and "uma linha só" in bad.get_data(as_text=True)


def test_como_funciona_mostra_numeros_atuais(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 4})
    html = client.get(f"/app/como-funciona?projeto={a.project_id}").get_data(as_text=True)
    assert "Como cada conta funciona" in html
    assert "Atividade 1: 4 ÷ 10 = 40%" in html
    assert "Atividade 1: 10 min ÷ 40 min = 25%" in html
