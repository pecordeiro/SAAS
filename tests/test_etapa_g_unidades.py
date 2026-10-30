"""Etapa G (bloco 3) — número de série por unidade (rastreabilidade, sem mudar o cálculo)."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.extensions import db
from app.models import Activity, AuditLog, ProgressEntry, Project, Unit
from app.models.quality import StageInspection
from app.services import audit, checklists, units
from app.services import projects as svc
from tests.conftest import login, post, text_of


def _gen(client, app, project_id, **kw):
    data = {"prefix": "mt-", "start": 1, "count": 3, "width": 3}
    data.update(kw)
    return post(client, app, f"/app/projetos/{project_id}/unidades/gerar", data)


def _units(app, project_id):
    with app.app_context():
        return [u.serial for u in db.session.execute(select(Unit).where(Unit.project_id == project_id).order_by(Unit.serial)).scalars()]


def _unit_id(app, serial):
    with app.app_context():
        return db.session.execute(select(Unit.id).where(Unit.serial == serial)).scalar_one()


def test_supervisor_gera_faixa_e_lista_com_limite_da_quantidade(app, client, tenants):
    a, _ = tenants  # quantidade 10
    login(client, app, a.supervisor_email)
    assert _gen(client, app, a.project_id).status_code == 303
    assert _units(app, a.project_id) == ["MT-001", "MT-002", "MT-003"]
    # repetida → 400 e nada grava
    response = _gen(client, app, a.project_id, start=3, count=2)
    assert response.status_code == 400 and "MT-003" in text_of(response)
    # lista colada: normaliza, aceita ; e , ; repetida na lista → 400
    bad = post(client, app, f"/app/projetos/{a.project_id}/unidades/importar", {"serials": "x1\nX1"})
    assert bad.status_code == 400 and "repetido" in text_of(bad)
    bad = post(client, app, f"/app/projetos/{a.project_id}/unidades/importar", {"serials": "ok-1\n<script>"})
    assert bad.status_code == 400
    ok = post(client, app, f"/app/projetos/{a.project_id}/unidades/importar", {"serials": " sn 9 ; sn-10, SN-11\n\n"})
    assert ok.status_code == 303
    assert _units(app, a.project_id) == ["MT-001", "MT-002", "MT-003", "SN-10", "SN-11", "SN9"]
    # passar da quantidade do projeto (10) → 400
    response = _gen(client, app, a.project_id, prefix="Z", start=1, count=5, width=1)
    assert response.status_code == 400 and "10 equipamentos" in text_of(response)
    assert len(_units(app, a.project_id)) == 6
    with app.app_context():
        assert db.session.execute(select(func.count()).select_from(AuditLog).where(AuditLog.action == audit.UNITS_CREATED)).scalar_one() == 2
        # quantidade do projeto não fica abaixo das unidades cadastradas
        project = db.session.get(Project, a.project_id)
        with pytest.raises(svc.EditError):
            svc.update_project(project, name=project.name, quantity=5, start_date=None, due_date=None, people=1,
                               hours_per_day=project.hours_per_day, user_id=None)


def test_operador_ve_mas_nao_cria_nem_muda_status(app, tenants):
    a, _ = tenants
    sup = app.test_client()
    login(sup, app, a.supervisor_email)
    _gen(sup, app, a.project_id, count=1)
    unit_id = _unit_id(app, "MT-001")
    op = app.test_client()
    login(op, app, a.operator_email)
    page = op.get(f"/app/projetos/{a.project_id}/unidades")
    assert page.status_code == 200 and "MT-001" in page.get_data(as_text=True)
    assert "unidades/gerar" not in page.get_data(as_text=True)
    assert _gen(op, app, a.project_id).status_code == 403
    assert post(op, app, f"/app/projetos/{a.project_id}/unidades/importar", {"serials": "X"}).status_code == 403
    assert post(op, app, f"/app/unidades/{unit_id}/status", {"status": "done"}).status_code == 403
    assert op.get(f"/app/unidades/{unit_id}").status_code == 200


def test_status_com_versao_e_auditoria_no_historico(app, client, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    _gen(client, app, a.project_id, count=1)
    unit_id = _unit_id(app, "MT-001")
    assert post(client, app, f"/app/unidades/{unit_id}/status", {"status": "done", "version": 1}).status_code == 303
    assert post(client, app, f"/app/unidades/{unit_id}/status", {"status": "shipped", "version": 1}).status_code == 409
    assert post(client, app, f"/app/unidades/{unit_id}/status", {"status": "perdida", "version": 2}).status_code == 400
    page = text_of(client.get(f"/app/unidades/{unit_id}"))
    assert "Situação da unidade alterada" in page and "Em produção → Concluída" in page


def test_registrar_atividade_na_unidade_uma_vez_e_desfazer_libera(app, tenants):
    a, _ = tenants
    sup = app.test_client()
    login(sup, app, a.supervisor_email)
    _gen(sup, app, a.project_id, count=2)
    u1, u2 = _unit_id(app, "MT-001"), _unit_id(app, "MT-002")
    op = app.test_client()
    login(op, app, a.operator_email)
    url = f"/app/unidades/{u1}/registrar"
    assert post(op, app, url, {"activity_id": str(a.activity_id)}).status_code == 303
    again = post(op, app, url, {"activity_id": str(a.activity_id)})
    assert again.status_code == 400 and "já foi registrada" in text_of(again)
    assert post(op, app, f"/app/unidades/{u2}/registrar", {"activity_id": str(a.activity_id)}).status_code == 303
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).units_done == 2  # contador continua a fonte
        entry = db.session.execute(select(ProgressEntry).where(ProgressEntry.unit_id == u1)).scalar_one()
        assert entry.delta == 1
        entry_id = entry.id
    # desfazer (supervisor) mantém a unidade no lançamento compensatório e libera de novo
    assert post(sup, app, f"/app/registros/{entry_id}/desfazer", {"confirm": "y"}).status_code == 303
    with app.app_context():
        reversal = db.session.execute(select(ProgressEntry).where(ProgressEntry.reverts_entry_id == entry_id)).scalar_one()
        assert reversal.unit_id == u1
    page = text_of(op.get(f"/app/unidades/{u1}"))
    assert "desfeito" in page
    assert post(op, app, url, {"activity_id": str(a.activity_id)}).status_code == 303


def test_criar_unidades_nao_muda_o_calculo(app, client, tenants):
    a, _ = tenants
    with app.app_context():
        before = svc.summary(db.session.get(Project, a.project_id))
    login(client, app, a.supervisor_email)
    _gen(client, app, a.project_id, count=10)
    with app.app_context():
        assert svc.summary(db.session.get(Project, a.project_id)) == before


def test_inspecao_por_unidade_aparece_no_historico(app, tenants):
    a, _ = tenants
    sup = app.test_client()
    login(sup, app, a.supervisor_email)
    _gen(sup, app, a.project_id, count=1)
    unit_id = _unit_id(app, "MT-001")
    post(sup, app, f"/app/etapas/{a.stage_id}/checklist/itens", {"text": "Torque"})
    assert "MT-001" in sup.get(f"/app/etapas/{a.stage_id}/checklist").get_data(as_text=True)
    assert post(sup, app, f"/app/etapas/{a.stage_id}/inspecoes", {"unit_id": str(unit_id)}).status_code == 303
    assert post(sup, app, f"/app/etapas/{a.stage_id}/inspecoes", {}).status_code == 303  # outra (etapa inteira)
    with app.app_context():
        rows = list(db.session.execute(select(StageInspection)).scalars())
        assert sorted(str(r.unit_id) for r in rows) == sorted([str(unit_id), "None"])
        insp_id = next(r.id for r in rows if r.unit_id == unit_id)
    page = sup.get(f"/app/unidades/{unit_id}").get_data(as_text=True)
    assert f"/app/inspecoes/{insp_id}" in page


def test_busca_por_serie_escapa_curingas(app, client, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    post(client, app, f"/app/projetos/{a.project_id}/unidades/importar", {"serials": "AB-1\nAB_2\nXY-3"})
    page = text_of(client.get("/app/unidades?q=ab"))
    assert "AB-1" in page and "AB_2" in page and "XY-3" not in page
    page = text_of(client.get("/app/unidades?q=_"))  # “_” é literal, não curinga
    assert "AB_2" in page and "AB-1" not in page
    assert "XY-3" not in text_of(client.get("/app/unidades?q=%25"))
    project_page = text_of(client.get(f"/app/projetos/{a.project_id}/unidades?q=xy"))
    assert "XY-3" in project_page and "AB-1" not in project_page


def test_service_valida_serie():
    with pytest.raises(units.UnitError):
        units.validate_serial("-comeca-com-hifen")
    with pytest.raises(units.UnitError):
        units.validate_serial("A" * 61)
    assert units.validate_serial(" ab 12/x ") == "AB12/X"


def test_menu_e_detalhe_levam_as_unidades(app, client, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    html = client.get(f"/app/projetos/{a.project_id}").get_data(as_text=True)
    assert f"/app/projetos/{a.project_id}/unidades" in html and "/app/unidades" in html


def test_checklists_signal_independe_de_unidades(app, tenants):
    a, _ = tenants
    with app.app_context():
        from app.models import Stage

        stage = db.session.get(Stage, a.stage_id)
        assert checklists.signals(a.company_id, [stage])[stage.id].pending is False
