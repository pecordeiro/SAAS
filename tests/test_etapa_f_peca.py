"""Etapa F — etapa “aguardando peça”: só sinaliza (nunca bloqueia), supervisor+, version,
auditoria e selo com texto + ícone na lista, no detalhe e no painel."""

from __future__ import annotations

from datetime import date

from app.extensions import db
from app.models import Activity, AuditLog, Stage
from tests.conftest import login, post, text_of

URL = "/app/etapas/{id}/aguardando-peca"


def _mark(client, app, tenant, **data):
    payload = {"waiting": "y", "expected_on": "2026-10-20", "note": "Motor do fornecedor X", "version": 1}
    payload.update(data)
    return post(client, app, URL.format(id=tenant.stage_id), {k: v for k, v in payload.items() if v is not None})


def test_supervisor_marca_e_desmarca_com_auditoria(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    response = _mark(client, app, a)
    assert response.status_code == 303
    with app.app_context():
        stage = db.session.get(Stage, a.stage_id)
        assert stage.waiting_part is True
        assert stage.part_expected_on == date(2026, 10, 20)
        assert stage.part_note == "Motor do fornecedor X"
        assert stage.part_updated_at is not None and stage.version == 2
        log = db.session.query(AuditLog).filter_by(company_id=a.company_id, action="stage.waiting_part").one()
        assert log.details["depois"] == {"aguardando": True, "previsao": "2026-10-20"}
        assert "Motor" not in str(log.details)  # observação livre fica fora da auditoria
    # Desmarcar limpa previsão e observação.
    assert post(client, app, URL.format(id=a.stage_id), {"version": 2}).status_code == 303
    with app.app_context():
        stage = db.session.get(Stage, a.stage_id)
        assert (stage.waiting_part, stage.part_expected_on, stage.part_note, stage.part_updated_at) == (False, None, None, None)


def test_operador_nao_marca_e_nao_ve_o_formulario(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    assert _mark(client, app, a).status_code == 403
    page = text_of(client.get(f"/app/projetos/{a.project_id}"))
    assert "Marcar aguardando peça" not in page
    with app.app_context():
        assert db.session.get(Stage, a.stage_id).waiting_part is False


def test_versao_velha_responde_409_e_nada_grava(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    assert _mark(client, app, a).status_code == 303
    response = _mark(client, app, a, note="Outra coisa", version=1)
    assert response.status_code == 409
    assert "Outra pessoa alterou esta etapa" in text_of(response)
    with app.app_context():
        assert db.session.get(Stage, a.stage_id).part_note == "Motor do fornecedor X"


def test_observacao_longa_e_data_absurda_sao_recusadas_no_servidor(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    assert _mark(client, app, a, note="x" * 141).status_code == 400
    assert _mark(client, app, a, expected_on="1900-01-01").status_code == 400
    assert _mark(client, app, a, expected_on="nao-e-data").status_code == 400
    with app.app_context():
        assert db.session.get(Stage, a.stage_id).waiting_part is False


def test_so_sinaliza_registro_de_pecas_continua_liberado(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    assert _mark(client, app, a).status_code == 303
    op = app.test_client()
    login(op, app, a.operator_email)
    response = post(op, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 3, "version": 1})
    assert response.status_code == 303
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).units_done == 3


def test_selo_com_texto_e_icone_na_lista_detalhe_e_painel(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    _mark(client, app, a)
    op = app.test_client()
    login(op, app, a.operator_email)  # o selo aparece para todos; o formulário só para supervisor+
    detail = op.get(f"/app/projetos/{a.project_id}").get_data(as_text=True)
    assert "Aguardando peça · prev. 20/10" in detail and "#i-package" in detail
    assert "Motor do fornecedor X" in detail
    listing = op.get("/app/projetos").get_data(as_text=True)
    assert "Aguardando peça" in listing and "#i-package" in listing
    panel = op.get(f"/app/projetos/{a.project_id}/painel").get_data(as_text=True)
    assert "Aguardando peça · 1 etapa" in panel and "Aguardando peça · prev. 20/10" in panel
    # Sem a marca, nenhum selo.
    _, b = tenants
    other = app.test_client()
    login(other, app, b.owner_email)
    assert "Aguardando peça ·" not in other.get(f"/app/projetos/{b.project_id}").get_data(as_text=True)
