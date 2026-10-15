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
