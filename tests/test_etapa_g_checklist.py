"""Etapa G (bloco 2) — checklist de inspeção por etapa.

Itens no modelo → copiados ao projeto; supervisor+ define itens/“exige”; operador+ preenche e
assina (usuário + hora do servidor); depois de assinada só muda por correção registrada (nova
linha, a antiga fica); “exige checklist” só sinaliza (não bloqueia o registro de peças).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.extensions import db
from app.models import Activity, AuditLog, Company, Project, Stage, Template, User
from app.models.quality import InspectionAnswer, StageChecklistItem, StageInspection, TemplateChecklistItem
from app.services import audit, checklists
from app.services import projects as svc
from app.services import templates as tsvc
from tests.conftest import login, post, text_of


def _add_items(app, stage_id, *texts, required=False):
    with app.app_context():
        stage = db.session.get(Stage, stage_id)
        ids = [checklists.add_item(stage, t, None).id for t in texts]
        checklists.set_required(stage, required, None)
        db.session.commit()
        return ids


def _inspection(app):
    with app.app_context():
        row = db.session.execute(select(StageInspection)).scalar_one()
        db.session.expunge(row)
        return row


# ---------------------------------------------------------------- modelo → projeto


def test_itens_do_modelo_sao_versionados_e_copiados_ao_projeto(app, client, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    form = {
        "name": "Painel",
        "stages-0-name": "Montagem",
        "stages-0-activities": "Fixar; 10",
        "stages-0-checklist": "Torque conferido\n\nTorque conferido\nAterramento ok",
        "stages-0-checklist_required": "y",
    }
    assert post(client, app, "/app/modelos/novo", form).status_code == 303
    with app.app_context():
        template = db.session.execute(select(Template)).scalar_one()
        stage = template.current_version.stages[0]
        assert [i.text for i in stage.checklist_items] == ["Torque conferido", "Aterramento ok"]
        assert stage.checklist_required is True
        template_id = template.id
    # mudar só o checklist cria nova versão
    form2 = dict(form, **{"stages-0-checklist": "Torque conferido\nAterramento ok\nEtiqueta"})
    assert post(client, app, f"/app/modelos/{template_id}", form2).status_code == 303
    with app.app_context():
        template = db.session.get(Template, template_id)
        assert template.current_version.number == 2
        assert db.session.execute(select(func.count()).select_from(TemplateChecklistItem)).scalar_one() == 5
    # projeto novo copia os itens da versão atual
    base = {"name": "Proj", "quantity": 3, "people": 1, "hours_per_day": "8", "template_id": str(template_id)}
    assert post(client, app, "/app/projetos/novo", base).status_code == 303
    with app.app_context():
        project = db.session.execute(select(Project).where(Project.name == "Proj")).scalar_one()
        stage = project.stages[0]
        assert stage.checklist_required is True
        assert [i.text for i in checklists.active_items(stage)] == ["Torque conferido", "Aterramento ok", "Etiqueta"]
        # duplicar copia também
        copy = svc.duplicate_project(project, None)
        db.session.commit()
        assert [i.text for i in checklists.active_items(copy.stages[0])] == ["Torque conferido", "Aterramento ok", "Etiqueta"]


def test_aplicar_versao_do_modelo_inclui_itens_novos_sem_apagar_os_do_projeto(app, tenants):
    a, _ = tenants
    with app.app_context():
        company = db.session.get(Company, a.company_id)
        stages = [svc.NewStage("Etapa 1", [svc.NewActivity("A", Decimal("1"))], checklist=["Item 1"])]
        template = tsvc.create_template(company, "M", stages)
        project = tsvc.create_project_from_template(company, template, name="P", quantity=2, start_date=None,
                                                    due_date=None, people=1, hours_per_day=Decimal("8"))
        stage = project.stages[0]
        checklists.add_item(stage, "Do projeto", None)
        tsvc.update_template(template, name="M", description=None, user_id=None, stages=[
            svc.NewStage("Etapa 1", [svc.NewActivity("A", Decimal("1"))], checklist=["Item 1", "Item 2"],
                         checklist_required=True)
        ])
        comparison = tsvc.compare(project)
        assert [c.kind for c in comparison.changes] == ["checklist_changed"]
        tsvc.apply_current_version(project, template.current_version_id, None)
        db.session.commit()
        stage = db.session.get(Stage, stage.id)
        assert [i.text for i in checklists.active_items(stage)] == ["Item 1", "Do projeto", "Item 2"]
        assert stage.checklist_required is True


# ---------------------------------------------------------------- papéis


def test_operador_nao_define_itens_nem_exigencia(app, client, tenants):
    a, _ = tenants
    [item_id] = _add_items(app, a.stage_id, "Torque")
    login(client, app, a.operator_email)
    page = client.get(f"/app/etapas/{a.stage_id}/checklist")
    assert page.status_code == 200 and "Torque" in page.get_data(as_text=True)
    assert "/checklist/itens" not in page.get_data(as_text=True)
    assert post(client, app, f"/app/etapas/{a.stage_id}/checklist/itens", {"text": "X"}).status_code == 403
    assert post(client, app, f"/app/etapas/{a.stage_id}/checklist/exigir", {"required": "y"}).status_code == 403
    assert post(client, app, f"/app/checklist-itens/{item_id}/arquivar").status_code == 403
    with app.app_context():
        assert db.session.get(Stage, a.stage_id).checklist_required is False
        assert db.session.get(StageChecklistItem, item_id).archived_at is None


def test_supervisor_inclui_arquiva_e_exige_com_auditoria(app, client, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    assert post(client, app, f"/app/etapas/{a.stage_id}/checklist/itens", {"text": "  Aperto   final "}).status_code == 303
    assert post(client, app, f"/app/etapas/{a.stage_id}/checklist/itens", {"text": "aperto final"}).status_code == 400
    assert post(client, app, f"/app/etapas/{a.stage_id}/checklist/itens", {"text": "x" * 201}).status_code == 400
    assert post(client, app, f"/app/etapas/{a.stage_id}/checklist/exigir", {"required": "y"}).status_code == 303
    with app.app_context():
        item = db.session.execute(select(StageChecklistItem)).scalar_one()
        assert item.text == "Aperto final"
        item_id = item.id
        assert db.session.get(Stage, a.stage_id).checklist_required is True
    assert post(client, app, f"/app/checklist-itens/{item_id}/arquivar").status_code == 303
    with app.app_context():
        assert db.session.get(StageChecklistItem, item_id).archived_at is not None
        actions = set(db.session.execute(select(AuditLog.action).where(AuditLog.company_id == a.company_id)).scalars())
        assert {audit.CHECKLIST_ITEM_ADDED, audit.CHECKLIST_ITEM_ARCHIVED, audit.STAGE_CHECKLIST_REQUIRED} <= actions


# ---------------------------------------------------------------- preencher, assinar, corrigir


def test_fluxo_completo_assinatura_do_servidor_e_correcao_registrada(app, tenants):
    a, _ = tenants
    i1, i2 = _add_items(app, a.stage_id, "Torque", "Aterramento", required=True)
    op = app.test_client()
    login(op, app, a.operator_email)
    detail = op.get(f"/app/projetos/{a.project_id}").get_data(as_text=True)
    assert "Checklist pendente" in detail
    assert post(op, app, f"/app/etapas/{a.stage_id}/inspecoes").status_code == 303
    insp = _inspection(app)
    url = f"/app/inspecoes/{insp.id}"
    # rascunho parcial
    assert post(op, app, url, {"acao": "salvar", "version": insp.version, f"resultado-{i1}": "ok"}).status_code == 303
    # assinar sem responder tudo → 400
    insp = _inspection(app)
    response = post(op, app, url, {"acao": "assinar", "version": insp.version, f"resultado-{i1}": "ok"})
    assert response.status_code == 400 and "Responda todos" in text_of(response)
    # não conforme sem observação → 400
    response = post(op, app, url, {"acao": "assinar", "version": insp.version, f"resultado-{i1}": "ok",
                                   f"resultado-{i2}": "nonconforming"})
    assert response.status_code == 400 and "observação" in text_of(response)
    # assinatura: campos forjados no formulário são ignorados
    response = post(op, app, url, {
        "acao": "assinar", "version": insp.version, f"resultado-{i1}": "ok", f"resultado-{i2}": "nonconforming",
        f"obs-{i2}": "Cabo solto", "signed_by_id": str(a.owner_id), "signed_at": "2000-01-01T00:00:00",
    })
    assert response.status_code == 303
    with app.app_context():
        insp = db.session.execute(select(StageInspection)).scalar_one()
        assert insp.status == "signed" and insp.signed_by_id == a.operator_id
        assert insp.signed_at.year >= 2026
        answers = checklists.current_answers(insp)
        assert answers[i2].result == "nonconforming" and answers[i2].locked_at is not None
        old_id = answers[i2].id
        # guarda do ORM: resposta assinada não muda nem some
        answers[i2].result = "ok"
        with pytest.raises(RuntimeError):
            db.session.flush()
        db.session.rollback()
        insp_id = insp.id
    detail = op.get(f"/app/projetos/{a.project_id}").get_data(as_text=True)
    assert "Checklist assinado" in detail
    # depois de assinada: salvar de novo é recusado; operador não corrige
    assert post(op, app, url, {"acao": "salvar", f"resultado-{i1}": "na"}).status_code == 400
    assert post(op, app, f"{url}/corrigir", {"item_id": str(i2), "result": "ok", "reason": "Reaperto feito"}).status_code == 403
    # supervisor corrige: motivo obrigatório; nova linha; antiga fica
    sup = app.test_client()
    login(sup, app, a.supervisor_email)
    assert post(sup, app, f"{url}/corrigir", {"item_id": str(i2), "result": "ok", "reason": ""}).status_code == 400
    assert post(sup, app, f"{url}/corrigir", {"item_id": str(i2), "result": "ok", "reason": "Reaperto feito e testado"}).status_code == 303
    with app.app_context():
        insp = db.session.get(StageInspection, insp_id)
        current = checklists.current_answers(insp)
        assert current[i2].result == "ok" and current[i2].supersedes_id == old_id
        assert current[i2].correction_reason == "Reaperto feito e testado"
        assert db.session.get(InspectionAnswer, old_id).result == "nonconforming"  # a antiga fica
        assert db.session.execute(select(func.count()).select_from(InspectionAnswer)).scalar_one() == 3
        log = db.session.execute(select(AuditLog).where(AuditLog.action == audit.INSPECTION_CORRECTED)).scalar_one()
        assert log.details["de"] == "nonconforming" and log.details["para"] == "ok"
    page = sup.get(url).get_data(as_text=True)
    assert "Cabo solto" in page and "Reaperto feito e testado" in page


def test_conflito_de_versao_no_rascunho_responde_409(app, tenants):
    a, _ = tenants
    [i1] = _add_items(app, a.stage_id, "Torque")
    op = app.test_client()
    login(op, app, a.operator_email)
    post(op, app, f"/app/etapas/{a.stage_id}/inspecoes")
    insp = _inspection(app)
    url = f"/app/inspecoes/{insp.id}"
    assert post(op, app, url, {"acao": "salvar", "version": 1, f"resultado-{i1}": "ok"}).status_code == 303
    assert post(op, app, url, {"acao": "assinar", "version": 1, f"resultado-{i1}": "ok"}).status_code == 409
    assert _inspection(app).status == "draft"


def test_nova_inspecao_reaproveita_o_rascunho_e_exige_itens(app, client, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    assert post(client, app, f"/app/etapas/{a.stage_id}/inspecoes").status_code == 400  # sem itens
    _add_items(app, a.stage_id, "Torque")
    post(client, app, f"/app/etapas/{a.stage_id}/inspecoes")
    post(client, app, f"/app/etapas/{a.stage_id}/inspecoes")
    with app.app_context():
        assert db.session.execute(select(func.count()).select_from(StageInspection)).scalar_one() == 1


def test_item_de_outra_etapa_nao_entra_na_inspecao(app, tenants):
    a, _ = tenants
    with app.app_context():
        project = db.session.get(Project, a.project_id)
        other = svc.add_stage(project, "Outra", [], checklist=["De fora"])
        db.session.commit()
        other_item = checklists.active_items(other)[0].id
    [i1] = _add_items(app, a.stage_id, "Torque")
    op = app.test_client()
    login(op, app, a.operator_email)
    post(op, app, f"/app/etapas/{a.stage_id}/inspecoes")
    insp = _inspection(app)
    url = f"/app/inspecoes/{insp.id}"
    post(op, app, url, {"acao": "assinar", f"resultado-{i1}": "ok", f"resultado-{other_item}": "ok"})
    with app.app_context():
        assert {a_.item_id for a_ in db.session.execute(select(InspectionAnswer)).scalars()} == {i1}
    sup = app.test_client()
    login(sup, app, a.supervisor_email)
    assert post(sup, app, f"{url}/corrigir", {"item_id": str(other_item), "result": "na", "reason": "teste x"}).status_code == 404


def test_exigir_checklist_so_sinaliza_e_nao_bloqueia_registro(app, client, tenants):
    a, _ = tenants
    _add_items(app, a.stage_id, "Torque", required=True)
    login(client, app, a.operator_email)
    assert post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 10, "version": 1}).status_code == 303
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).units_done == 10


def test_modo_leitura_bloqueia_assinatura(app, client, tenants):
    from datetime import timedelta

    from app.models.base import utcnow

    a, _ = tenants
    [i1] = _add_items(app, a.stage_id, "Torque")
    login(client, app, a.operator_email)
    post(client, app, f"/app/etapas/{a.stage_id}/inspecoes")
    insp = _inspection(app)
    with app.app_context():
        db.session.get(Company, a.company_id).created_at = utcnow() - timedelta(days=400)
        db.session.commit()
    assert post(client, app, f"/app/inspecoes/{insp.id}", {"acao": "assinar", f"resultado-{i1}": "ok"}).status_code == 402
    assert client.get(f"/app/inspecoes/{insp.id}").status_code == 200
