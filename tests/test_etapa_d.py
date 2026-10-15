"""Etapa D — colaboração: autoria, edição com concorrência, atribuição, progresso por
pessoa e arrastar (ordem decidida no servidor)."""

from __future__ import annotations

from app.extensions import db
from app.models import Activity, ProgressEntry, User
from app.services import projects as svc
from tests.conftest import login, post, text_of


# ================================================================ 1) autoria


def test_detalhe_mostra_quem_fez_o_ultimo_lancamento(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    assert post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 2, "version": 1}).status_code == 303
    page = text_of(client.get(f"/app/projetos/{a.project_id}"))
    assert "Último: operator A +2" in page
    # A outra atividade (sem lançamento) não ganha linha de autoria inventada.
    assert page.count("Último: ") == 2  # celular + desktop da mesma atividade


def test_historico_mostra_autor_e_quem_desfez(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 3, "version": 1})
    with app.app_context():
        entry_id = db.session.query(ProgressEntry).filter_by(activity_id=a.activity_id).one().id
    sup = app.test_client()
    login(sup, app, a.supervisor_email)
    assert post(sup, app, f"/app/registros/{entry_id}/desfazer", {"confirm": "y"}).status_code == 303
    page = text_of(sup.get(f"/app/projetos/{a.project_id}/historico"))
    assert "operator A" in page  # autor do registro
    assert "por supervisor A" in page  # quem desfez


# ================================================================ 2) edição com concorrência


def test_renomear_etapa_com_versao_velha_responde_409_com_valor_atual(client, app, tenants):
    from app.models import AuditLog, Stage

    a, _ = tenants
    login(client, app, a.supervisor_email)
    url = f"/app/etapas/{a.stage_id}/renomear"
    # Primeira aba renomeia (versão 1 → 2).
    assert post(client, app, url, {"name": "Montagem", "version": 1}).status_code == 303
    # Segunda aba ainda com a versão 1: conflito, nada gravado, mostra o valor atual.
    response = post(client, app, url, {"name": "Pintura", "version": 1})
    assert response.status_code == 409
    page = text_of(response)
    assert "“Montagem”" in page and 'value="Pintura"' in page and "Confirmar e salvar" in page
    with app.app_context():
        stage = db.session.get(Stage, a.stage_id)
        assert (stage.name, stage.version) == ("Montagem", 2)
    # Confirmação consciente: salva de novo com a versão atual.
    assert post(client, app, url, {"name": "Pintura", "version": 2}).status_code == 303
    with app.app_context():
        stage = db.session.get(Stage, a.stage_id)
        assert (stage.name, stage.version) == ("Pintura", 3)
        actions = [r.action for r in db.session.query(AuditLog).filter_by(company_id=a.company_id)]
        assert actions.count("stage.renamed") == 2


def test_editar_atividade_depois_de_registro_alheio_responde_409(client, app, tenants):
    a, _ = tenants
    op = app.test_client()
    login(op, app, a.operator_email)
    assert post(op, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 2, "version": 1}).status_code == 303
    login(client, app, a.supervisor_email)
    url = f"/app/atividades/{a.activity_id}/editar"
    response = post(client, app, url, {"name": "Parafusar", "ideal_minutes": "12", "version": 1})
    assert response.status_code == 409
    page = text_of(response)
    assert "“Atividade 1”, 10,00 min, 2 de 10 peças" in page and 'value="Parafusar"' in page
    with app.app_context():
        activity = db.session.get(Activity, a.activity_id)
        assert activity.name == "Atividade 1" and activity.version == 2
    assert post(client, app, url, {"name": "Parafusar", "ideal_minutes": "12", "version": 2}).status_code == 303
    with app.app_context():
        activity = db.session.get(Activity, a.activity_id)
        assert (activity.name, activity.ideal_minutes, activity.units_done, activity.version) == (
            "Parafusar", 12, 2, 3,
        )


def test_registro_com_versao_da_tela_de_edicao_ve_o_conflito(client, app, tenants):
    """Editar o tempo ideal muda a versão: quem registra com a tela velha recebe 409."""
    a, _ = tenants
    login(client, app, a.supervisor_email)
    url = f"/app/atividades/{a.activity_id}/editar"
    assert post(client, app, url, {"name": "Atividade 1", "ideal_minutes": "15", "version": 1}).status_code == 303
    assert post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 1, "version": 1}).status_code == 409


def test_edicao_sem_versao_continua_aceita(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    assert post(client, app, f"/app/etapas/{a.stage_id}/renomear", {"name": "X"}).status_code == 303
    assert post(client, app, f"/app/atividades/{a.activity_id}/editar", {"name": "Y", "ideal_minutes": "3"}).status_code == 303


def test_tela_de_edicao_envia_a_versao(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    page = client.get(f"/app/projetos/{a.project_id}/editar").get_data(as_text=True)
    assert page.count('name="version" value="1"') >= 3  # etapa + 2 atividades
