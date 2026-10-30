"""R6 — módulos opcionais (ADR-0017): desligados por padrão, ligados em Configurações › Módulos.

- Desligado: TODA rota do módulo responde 404 (para qualquer papel) e o menu/fragmento some.
- Ligado: a rota funciona e o item aparece com o selo “Opcional”.
- Só o proprietário muda; cada mudança fica em audit_logs; uma empresa não vê nem muda a outra.
- Worker: módulo desligado não gera alerta nem e-mail.
- Limites de plano continuam valendo à parte.
- Migration: liga, nas empresas que já existiam, o módulo em que elas já tinham dados.
"""

from __future__ import annotations

import io
import re
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from openpyxl import load_workbook
from sqlalchemy import select, text

from app import create_app
from app.extensions import db
from app.models import (
    Activity,
    Alert,
    AuditLog,
    Company,
    CompanyModule,
    DomainEvent,
    ProgressEntry,
    Project,
    Stage,
)
from app.services import email, entitlements, modules, worker
from tests.conftest import (
    PASSWORD,
    downgrade_migrations,
    get_test_database_url,
    login,
    make_tenant,
    post,
    requires_postgres,
    run_migrations,
    set_tenant_modules,
    text_of,
)

ALL = modules.KEYS


def _rules_of(app, key: str):
    """Regras do url_map que pertencem ao módulo (pelo mapa de services/modules.py)."""
    return [r for r in app.url_map.iter_rules() if modules.module_for_endpoint(r.endpoint) == key]


def _url(rule) -> str:
    """URL concreta da regra com UUIDs aleatórios (o guarda responde antes de buscar o recurso)."""
    return re.sub(r"<uuid:[^>]+>", lambda _m: str(uuid.uuid4()), rule.rule).replace("<path:rest>", "x")


def _call(client, app, method, url):
    if method == "GET":
        return client.get(url)
    return post(client, app, url, {})


def _methods(rule):
    return sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})


# ================================================================ catálogo


def test_catalogo_aponta_para_rotas_que_existem(app_factory):
    app = app_factory({"FEATURE_PUBLIC_API": True})
    endpoints = {r.endpoint for r in app.url_map.iter_rules()}
    for module in modules.CATALOG:
        for endpoint in module.endpoints:
            assert endpoint in endpoints, f"{module.key}: {endpoint} não existe"
        assert _rules_of(app, module.key), f"{module.key} sem rota"
    # Núcleo nunca entra no mapa (painel, preencher, projetos, histórico, configurações).
    for core in ("app.home", "preencher.fill", "app.project_detail", "app.history", "empresa.modules", "dados.import_upload"):
        assert modules.module_for_endpoint(core) is None


# ================================================================ desligado = 404, ligado = funciona


@pytest.mark.parametrize("key", [k for k in ALL if k != modules.API])
def test_modulo_desligado_toda_rota_responde_404(app, client, key):
    with app.app_context():
        a = make_tenant("A", modules=[k for k in ALL if k != key])  # todos menos este
    login(client, app, a.owner_email)  # owner: papel máximo, só o módulo impede
    rules = _rules_of(app, key)
    assert rules
    for rule in rules:
        for method in _methods(rule):
            response = _call(client, app, method, _url(rule))
            assert response.status_code == 404, f"{method} {rule.rule} → {response.status_code}"


@pytest.mark.parametrize("key", [k for k in ALL if k != modules.API])
def test_modulo_desligado_404_vem_antes_do_papel(app, client, key):
    """Operador numa rota de supervisor de módulo desligado: 404 (não 403)."""
    with app.app_context():
        a = make_tenant("A", modules=())
    login(client, app, a.operator_email)
    for rule in _rules_of(app, key):
        for method in _methods(rule):
            assert _call(client, app, method, _url(rule)).status_code == 404


def test_api_desligada_404_na_tela_e_na_api(app_factory):
    from app.services import api_tokens as tokens

    app = app_factory({"FEATURE_PUBLIC_API": True})
    client = app.test_client()
    with app.app_context():
        a = make_tenant("A", plan="empresa", modules=())
        created = tokens.create_token(db.session.get(Company, a.company_id), name="ERP", scopes=["read:projects"],
                                      expires_in_days=30, user_id=None)
        db.session.commit()
        raw = created.raw
    auth = {"Authorization": f"Bearer {raw}"}
    assert client.get("/api/v1/projects", headers=auth).status_code == 404
    login(client, app, a.owner_email)
    for rule in _rules_of(app, modules.API):
        if rule.endpoint.startswith("api_v1."):
            continue
        for method in _methods(rule):
            assert _call(client, app, method, _url(rule)).status_code == 404
    # Ligado: a API responde (plano Empresa tem a feature).
    with app.app_context():
        set_tenant_modules(a.company_id, [modules.API])
        db.session.commit()
    assert client.get("/api/v1/projects", headers=auth).status_code == 200
    assert client.get("/app/integracoes/api").status_code == 200


def test_modulos_ligados_rotas_funcionam(app, client):
    """Uma rota de cada módulo, com o módulo ligado, responde normalmente (não 404)."""
    with app.app_context():
        a = make_tenant("A", modules=ALL)
    login(client, app, a.owner_email)
    pages = [
        f"/app/atividades/{a.activity_id}/evidencias",  # fotos
        f"/app/etapas/{a.stage_id}/checklist",  # checklist
        f"/app/projetos/{a.project_id}/unidades",  # unidades
        "/app/unidades",
        f"/app/projetos/{a.project_id}/pessoas",  # atribuição
        "/app/alertas",  # alertas
    ]
    for url in pages:
        assert client.get(url).status_code == 200, url
    ok = post(client, app, f"/app/etapas/{a.stage_id}/aguardando-peca", {"waiting": "y", "version": 1})
    assert ok.status_code == 303
    with app.app_context():
        assert db.session.get(Stage, a.stage_id).waiting_part is True


# ================================================================ menu e fragmentos


def test_empresa_nova_ve_so_o_nucleo(app, client):
    """Cadastro de verdade: a empresa nasce sem nenhum módulo; menu e detalhe sem os opcionais."""
    from tests.test_accounts import SIGNUP

    post(client, app, "/cadastro", SIGNUP)
    with app.app_context():
        company = db.session.execute(select(Company).where(Company.name == SIGNUP["company_name"])).scalar_one()
        assert modules.enabled_keys(company.id) == frozenset()
        assert db.session.query(CompanyModule).filter_by(company_id=company.id).count() == 0
    login(client, app, SIGNUP["email"], SIGNUP["password"])
    page = text_of(client.get("/app/projetos"))
    for label in ("Alertas", "Unidades", "Opcional"):
        assert label not in page
    assert "Módulos" in page  # o proprietário acha onde ligar


def test_menu_e_detalhe_desligados_e_ligados(app, client):
    with app.app_context():
        off = make_tenant("A", modules=())
        on = make_tenant("B", modules=ALL)
        db.session.get(Stage, on.stage_id).waiting_part = True
        db.session.get(Stage, off.stage_id).waiting_part = True  # dado antigo: some com o módulo desligado
        db.session.commit()
    marks = ("Fotos e comentários", "Checklist de inspeção", "Marcar aguardando peça", "Atualizar aguardando peça",
             "Aguardando peça", "Pessoas · 7 dias", "Ver progresso por pessoa", "/unidades")
    login(client, app, off.owner_email)
    page = text_of(client.get(f"/app/projetos/{off.project_id}"))
    for mark in marks:
        assert mark not in page, mark
    nav = text_of(client.get("/app/projetos"))
    assert ">Alertas<" not in nav and ">Unidades<" not in nav and "Opcional" not in nav

    post(client, app, "/sair")
    login(client, app, on.owner_email)
    page = text_of(client.get(f"/app/projetos/{on.project_id}"))
    for mark in ("Fotos e comentários", "Checklist de inspeção", "Atualizar aguardando peça", "Pessoas · 7 dias",
                 f"/app/projetos/{on.project_id}/unidades"):
        assert mark in page, mark
    assert "Opcional" in page
    nav = text_of(client.get("/app/projetos"))
    assert "Alertas" in nav and "Unidades" in nav and "Opcional" in nav


def test_painel_ignora_aguardando_peca_com_modulo_desligado(app, client):
    with app.app_context():
        a = make_tenant("A", modules=())
        db.session.get(Stage, a.stage_id).waiting_part = True
        db.session.commit()
    login(client, app, a.owner_email)
    for url in ("/app/", f"/app/projetos/{a.project_id}/painel", f"/app/preencher?projeto={a.project_id}"):
        response = client.get(url, follow_redirects=True)
        assert response.status_code == 200
        assert "aguardando peça" not in text_of(response).lower(), url
    with app.app_context():
        set_tenant_modules(a.company_id, [modules.AGUARDANDO_PECA])
        db.session.commit()
    assert "aguardando peça" in text_of(client.get("/app/")).lower()


def test_editar_projeto_sem_campo_responsavel_com_modulo_desligado(app, client):
    with app.app_context():
        a = make_tenant("A", modules=())
    login(client, app, a.owner_email)
    page = client.get(f"/app/projetos/{a.project_id}/editar").get_data(as_text=True)
    assert "/responsavel" not in page and "Sem responsável" not in page


def test_modelo_sem_checklist_preserva_o_que_ja_tinha(app, client):
    """Com o checklist desligado o campo some e o servidor ignora o que vier: o checklist que o
    modelo já tinha continua na versão nova."""
    from app.models import Template
    from app.services import templates as tsvc
    from app.services.projects import NewActivity, NewStage

    with app.app_context():
        a = make_tenant("A", modules=())
        company = db.session.get(Company, a.company_id)
        template = tsvc.create_template(
            company, "Modelo", [NewStage(name="Montagem", activities=[NewActivity("Parafusar", Decimal("5"))],
                                         checklist=["Torque conferido"], checklist_required=True)],
            created_by_user_id=a.owner_id,
        )
        db.session.commit()
        template_id = template.id
    login(client, app, a.owner_email)
    page = client.get(f"/app/modelos/{template_id}").get_data(as_text=True)
    assert "Checklist de inspeção" not in page
    response = post(client, app, f"/app/modelos/{template_id}", {
        "name": "Modelo", "description": "",
        "stages-0-name": "Montagem", "stages-0-activities": "Parafusar; 7",
        "stages-0-checklist": "Forjado pelo navegador", "stages-0-checklist_required": "",
        "stages-1-name": "Teste", "stages-1-activities": "Ligar; 3",
    })
    assert response.status_code == 303
    with app.app_context():
        version = db.session.get(Template, template_id).current_version
        by_name = {s.name: s for s in version.stages}
        assert [i.text for i in by_name["Montagem"].checklist_items] == ["Torque conferido"]
        assert by_name["Montagem"].checklist_required is True
        assert by_name["Teste"].checklist_items == [] and by_name["Teste"].checklist_required is False


def test_inspecao_ignora_unidade_sem_o_modulo_de_serie(app, client):
    from app.models import StageInspection
    from app.services import checklists
    from app.services import units as units_svc

    with app.app_context():
        a = make_tenant("A", modules=[modules.CHECKLIST, modules.UNIDADES])
        stage = db.session.get(Stage, a.stage_id)
        checklists.add_item(stage, "Torque", a.owner_id)
        unit = units_svc.import_list(db.session.get(Project, a.project_id), "SN-1", a.owner_id)[0]
        db.session.commit()
        unit_id = unit.id
        set_tenant_modules(a.company_id, [modules.CHECKLIST])
        db.session.commit()
    login(client, app, a.owner_email)
    page = client.get(f"/app/etapas/{a.stage_id}/checklist").get_data(as_text=True)
    assert "SN-1" not in page
    assert post(client, app, f"/app/etapas/{a.stage_id}/inspecoes", {"unit_id": str(unit_id)}).status_code == 303
    with app.app_context():
        assert db.session.query(StageInspection).one().unit_id is None


# ================================================================ Configurações › Módulos


def test_so_o_proprietario_ve_e_muda_os_modulos(app, client):
    with app.app_context():
        a = make_tenant("A", modules=())
    for email_ in (a.supervisor_email, a.operator_email):
        login(client, app, email_)
        assert client.get("/app/empresa/modulos").status_code == 403
        assert post(client, app, "/app/empresa/modulos", {"modulo": modules.FOTOS}).status_code == 403
        assert "/app/empresa/modulos" not in client.get("/app/projetos").get_data(as_text=True)
        post(client, app, "/sair")
    with app.app_context():
        assert modules.enabled_keys(a.company_id) == frozenset()
        assert db.session.query(AuditLog).filter(AuditLog.action.like("module.%")).count() == 0


def test_proprietario_liga_e_desliga_com_auditoria(app, client):
    with app.app_context():
        a = make_tenant("A", modules=())
    login(client, app, a.owner_email)
    page = text_of(client.get("/app/empresa/modulos"))
    assert "Módulos opcionais" in page and "Desligado" in page and "Opcional" in page
    with app.app_context():
        names = [m.name for m in modules.available()]
    for name in names:
        assert name in page
    response = post(client, app, "/app/empresa/modulos", {"modulo": [modules.FOTOS, modules.ALERTAS]})
    assert response.status_code == 303
    with app.app_context():
        assert modules.enabled_keys(a.company_id) == {modules.FOTOS, modules.ALERTAS}
        logs = db.session.query(AuditLog).filter(AuditLog.action == "module.enabled").all()
        assert sorted(l.details["modulo"] for l in logs) == [modules.ALERTAS, modules.FOTOS]
        assert all(l.actor_user_id == a.owner_id and l.company_id == a.company_id for l in logs)
    assert client.get(f"/app/atividades/{a.activity_id}/evidencias").status_code == 200
    # Mesmo estado de novo: nada muda, nenhuma auditoria nova.
    post(client, app, "/app/empresa/modulos", {"modulo": [modules.FOTOS, modules.ALERTAS]})
    with app.app_context():
        assert db.session.query(AuditLog).filter(AuditLog.action.like("module.%")).count() == 2
    # Desmarcar desliga (e audita); a rota volta a 404 e o dado continua no banco.
    post(client, app, "/app/empresa/modulos", {"modulo": [modules.ALERTAS]})
    with app.app_context():
        assert modules.enabled_keys(a.company_id) == {modules.ALERTAS}
        off = db.session.query(AuditLog).filter(AuditLog.action == "module.disabled").one()
        assert off.details["modulo"] == modules.FOTOS
        assert db.session.query(CompanyModule).filter_by(company_id=a.company_id, module=modules.FOTOS).one().enabled is False
    assert client.get(f"/app/atividades/{a.activity_id}/evidencias").status_code == 404


def test_chave_desconhecida_e_recusada(app_factory):
    app = app_factory()  # sem FEATURE_PUBLIC_API: o módulo API nem existe aqui
    client = app.test_client()
    with app.app_context():
        a = make_tenant("A", modules=())
    login(client, app, a.owner_email)
    for bad in ("inexistente", modules.API):
        response = post(client, app, "/app/empresa/modulos", {"modulo": [modules.FOTOS, bad]})
        assert response.status_code == 400
    with app.app_context():
        assert modules.enabled_keys(a.company_id) == frozenset()
    assert "API de integração" not in client.get("/app/empresa/modulos").get_data(as_text=True)


def test_post_sem_csrf_e_recusado(app, client):
    with app.app_context():
        a = make_tenant("A", modules=())
    login(client, app, a.owner_email)
    assert client.post("/app/empresa/modulos", data={"modulo": modules.FOTOS}).status_code == 400
    with app.app_context():
        assert modules.enabled_keys(a.company_id) == frozenset()


def test_modo_leitura_nao_muda_modulos(app_factory):
    app = app_factory({"TRIAL_DAYS": 0})  # teste grátis vencido = modo leitura
    client = app.test_client()
    with app.app_context():
        a = make_tenant("A", modules=())
    login(client, app, a.owner_email)
    assert post(client, app, "/app/empresa/modulos", {"modulo": modules.FOTOS}).status_code == 402
    with app.app_context():
        assert modules.enabled_keys(a.company_id) == frozenset()


# ================================================================ isolamento A/B


def test_modulos_de_uma_empresa_nao_vazam_para_outra(app, client, tenants):
    a, b = tenants
    with app.app_context():
        set_tenant_modules(a.company_id, ())
        set_tenant_modules(b.company_id, ())
        db.session.commit()
    login(client, app, a.owner_email)
    # Campo forjado com a empresa B é ignorado: a empresa vem só da sessão.
    post(client, app, "/app/empresa/modulos", {"modulo": [modules.FOTOS], "company_id": str(b.company_id)})
    with app.app_context():
        assert modules.enabled_keys(a.company_id) == {modules.FOTOS}
        assert modules.enabled_keys(b.company_id) == frozenset()
        assert db.session.query(AuditLog).filter_by(company_id=b.company_id).filter(AuditLog.action.like("module.%")).count() == 0
    # A tem fotos ligado, B não: o usuário de A não alcança a evidência de B (404) e B continua 404.
    assert client.get(f"/app/atividades/{a.activity_id}/evidencias").status_code == 200
    assert client.get(f"/app/atividades/{b.activity_id}/evidencias").status_code == 404
    post(client, app, "/sair")
    login(client, app, b.owner_email)
    assert client.get(f"/app/atividades/{b.activity_id}/evidencias").status_code == 404
    assert "Ligado" not in text_of(client.get("/app/empresa/modulos"))


def test_company_id_forjado_na_sessao_nao_mostra_modulos_de_b(app, client, tenants):
    a, b = tenants
    with app.app_context():
        set_tenant_modules(a.company_id, ())
        db.session.commit()
    login(client, app, a.owner_email)
    with client.session_transaction() as sess:
        sess["company_id"] = str(b.company_id)  # sem vínculo com B → volta para A
    assert client.get(f"/app/atividades/{a.activity_id}/evidencias").status_code == 404
    page = text_of(client.get("/app/empresa/modulos"))
    assert "Ligado" not in page


# ================================================================ worker e e-mails

NOW = datetime(2026, 10, 14, 13, 0, tzinfo=timezone.utc)  # 10h em São Paulo
MONDAY = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)


def _late_project(tenant):
    project = db.session.get(Project, tenant.project_id)
    project.due_date = date(2026, 10, 13)
    activity = db.session.get(Activity, tenant.activity_id)
    activity.units_done = 2
    db.session.add(ProgressEntry(company_id=tenant.company_id, activity_id=activity.id, user_id=tenant.operator_id,
                                 delta=2, at=NOW - timedelta(days=7)))
    db.session.commit()


def test_worker_nao_gera_alerta_nem_email_com_modulo_desligado(app):
    from app.services import alerts

    with app.app_context():
        off = make_tenant("A", modules=())
        on = make_tenant("B", modules=[modules.ALERTAS])
        _late_project(off)
        _late_project(on)
        result = worker.run_task(worker.TASK_ALERTS, NOW)
        assert result["companies"] == 1
        assert db.session.query(Alert).filter_by(company_id=off.company_id).count() == 0
        assert db.session.query(Alert).filter_by(company_id=on.company_id).count() == 2
        to = sorted(m.to for m in email.outbox(app) if m.subject.startswith(alerts.DIGEST_SUBJECT))
        assert to == [on.owner_email, on.supervisor_email]


def test_peca_atrasada_so_com_modulo_aguardando_peca(app):
    with app.app_context():
        a = make_tenant("A", modules=[modules.ALERTAS])
        stage = db.session.get(Stage, a.stage_id)
        stage.waiting_part = True
        stage.part_expected_on = date(2026, 10, 1)
        stage.part_updated_at = datetime(2026, 9, 20, tzinfo=timezone.utc)
        db.session.commit()
        worker.run_task(worker.TASK_ALERTS, NOW)
        assert db.session.query(Alert).filter_by(kind="part_overdue").count() == 0
        set_tenant_modules(a.company_id, [modules.ALERTAS, modules.AGUARDANDO_PECA])
        db.session.commit()
        worker.run_task(worker.TASK_ALERTS, NOW + timedelta(hours=1))
        assert db.session.query(Alert).filter_by(kind="part_overdue").count() == 1


def test_relatorio_semanal_respeita_os_modulos(app):
    from app.services.notifications import WEEKLY_SUBJECT

    with app.app_context():
        off = make_tenant("A", modules=())
        only = make_tenant("B", modules=[modules.ALERTAS])
        result = worker.run_task(worker.TASK_WEEKLY, MONDAY)
        assert result["companies"] == 1
        sent = [m for m in email.outbox(app) if m.subject.startswith(WEEKLY_SUBJECT)]
        assert sent and all("Empresa B" in m.subject for m in sent)
        wb = load_workbook(io.BytesIO(sent[0].attachments[0].content))
        assert wb.sheetnames == ["Projetos"]  # sem atribuição: sem a aba Pessoas
        header = [c.value for c in wb["Projetos"][2]]
        assert "Etapas aguardando peça" not in header
        assert off.company_id != only.company_id


def test_email_de_atribuicao_nao_sai_com_modulo_desligado(app):
    from app.services import events, notifications

    with app.app_context():
        a = make_tenant("A", modules=[modules.ATRIBUICAO])
        activity = db.session.get(Activity, a.activity_id)
        activity.assignee_id = a.operator_id
        event = DomainEvent(company_id=a.company_id, type=events.ACTIVITY_ASSIGNED,
                            payload={"activity_id": str(activity.id), "assignee_user_id": str(a.operator_id),
                                     "assigned_by_user_id": str(a.owner_id)})
        db.session.add(event)
        set_tenant_modules(a.company_id, ())
        db.session.commit()
        notifications.on_activity_assigned(event)
        assert not [m for m in email.outbox(app) if m.subject == notifications.ASSIGNED_SUBJECT]
        set_tenant_modules(a.company_id, [modules.ATRIBUICAO])
        db.session.commit()
        notifications.on_activity_assigned(event)
        assert [m.to for m in email.outbox(app) if m.subject == notifications.ASSIGNED_SUBJECT] == [a.operator_email]


# ================================================================ plano à parte


def test_limite_de_plano_vale_com_ou_sem_modulos(app):
    with app.app_context():
        for label, mods in (("A", ()), ("B", ALL)):
            t = make_tenant(label, plan="essencial", modules=mods)
            company = db.session.get(Company, t.company_id)
            limit = entitlements.effective_plan(company).max_projects
            assert limit is not None
            with pytest.raises(entitlements.PlanLimitError):
                entitlements.check_can_create_project(company, adding=limit)


def test_api_ligada_continua_exigindo_o_plano(app_factory):
    from app.services import api_tokens as tokens

    app = app_factory({"FEATURE_PUBLIC_API": True})
    client = app.test_client()
    with app.app_context():
        a = make_tenant("A", plan="essencial", modules=ALL)
        created = tokens.create_token(db.session.get(Company, a.company_id), name="ERP", scopes=["read:projects"],
                                      expires_in_days=30, user_id=None)
        db.session.commit()
    response = client.get("/api/v1/projects", headers={"Authorization": f"Bearer {created.raw}"})
    assert response.status_code == 403 and response.get_json()["code"] == "plan_feature_unavailable"
    login(client, app, a.owner_email)
    assert "não inclui a API" in text_of(client.get("/app/empresa/modulos"))
    assert post(client, app, "/app/integracoes/api", {"name": "X", "scopes": "read:projects"}).status_code == 402


# ================================================================ migration (dados de empresas existentes)

BEFORE = "b5d2e7a9c3f1"  # revisão anterior à R6


def _seed_old_companies() -> dict:
    """Duas empresas criadas ANTES da R6: uma usa responsável + aguardando peça; a outra só o núcleo."""
    from app.services import projects as svc

    ids = {}
    for label in ("Usa", "Nucleo"):
        company = Company(name=f"Antiga {label}")
        db.session.add(company)
        db.session.flush()
        project = svc.create_project(
            company, name=f"P {label}", quantity=5, start_date=None, due_date=None, people=1,
            hours_per_day=Decimal("8"),
            stages=[svc.NewStage(name="E1", activities=[svc.NewActivity(name="A1", ideal_minutes=Decimal("10"))])],
        )
        ids[label] = company.id
        if label == "Usa":
            from app.models import User
            from app.services.passwords import hash_password

            # INSERT só com as colunas informadas (+ padrões do Python): o banco está numa revisão
            # antiga, sem as colunas que vieram depois (ex.: users.tour_seen_at, ADR-0021).
            user_id = uuid.uuid4()
            db.session.execute(
                User.__table__.insert().values(
                    id=user_id, email="antiga@exemplo.com", name="Antiga", password_hash=hash_password(PASSWORD)
                )
            )
            project.stages[0].activities[0].assignee_id = user_id
            project.stages[0].waiting_part = True
    db.session.commit()
    return ids


def _migration_roundtrip(app):
    run_migrations(app, BEFORE)
    with app.app_context():
        from app import rls

        rls.set_context(company_id=None)
        ids = _seed_old_companies()
    run_migrations(app, "head")
    with app.app_context():
        rows = db.session.execute(
            text("SELECT company_id, module, enabled FROM company_modules ORDER BY module")
        ).all()
        by_company: dict = {}
        for company_id, module, enabled in rows:
            assert enabled
            by_company.setdefault(str(uuid.UUID(str(company_id))), set()).add(module)
        assert by_company == {str(ids["Usa"]): {"aguardando_peca", "atribuicao"}}
    downgrade_migrations(app, BEFORE)
    run_migrations(app, "head")
    with app.app_context():
        assert db.session.execute(text("SELECT count(*) FROM company_modules")).scalar() == 2
        db.session.remove()


def test_migration_liga_modulos_em_uso_sqlite(tmp_path):
    app = create_app("test", {"SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'r6.db'}"})
    try:
        _migration_roundtrip(app)
    finally:
        with app.app_context():
            db.engine.dispose()


@requires_postgres
def test_migration_liga_modulos_em_uso_postgres(_postgres_schema):
    app = create_app("test", {"SQLALCHEMY_DATABASE_URI": get_test_database_url()})
    try:
        with app.app_context():
            db.session.execute(text("TRUNCATE companies, users CASCADE"))
            db.session.commit()
        downgrade_migrations(app, BEFORE)
        _migration_roundtrip(app)
    finally:
        with app.app_context():
            db.session.execute(text("TRUNCATE companies, users CASCADE"))
            db.session.commit()
            db.engine.dispose()


# ================================================================ RLS (PostgreSQL)


@requires_postgres
def test_rls_company_modules_so_da_propria_empresa(app, tenants):
    """Com RLS forçado e papel comum, a empresa A não lê nem grava módulos de B."""
    import secrets

    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url
    from sqlalchemy.exc import DBAPIError

    from app import rls

    a, b = tenants
    role = "controle_app_r6_rls"
    password = secrets.token_hex(12)
    with app.app_context():
        with db.engine.begin() as conn:
            if conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname = :r"), {"r": role}).first():
                conn.execute(text(f"DROP OWNED BY {role}"))
                conn.execute(text(f"DROP ROLE {role}"))
            conn.execute(text(f"CREATE ROLE {role} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD '{password}'"))
            conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {role}"))
            conn.execute(text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {role}"))
            rls.enable(conn)
    engine = create_engine(make_url(get_test_database_url()).set(username=role, password=password))
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT set_config('app.company_id', :c, true)"), {"c": str(a.company_id)})
            seen = set(conn.execute(text("SELECT DISTINCT company_id FROM company_modules")).scalars())
            assert seen == {a.company_id}
            changed = conn.execute(text("UPDATE company_modules SET enabled = false WHERE company_id = :c"),
                                   {"c": b.company_id})
            assert changed.rowcount == 0
        with engine.connect() as conn:
            trans = conn.begin()
            conn.execute(text("SELECT set_config('app.company_id', :c, true)"), {"c": str(a.company_id)})
            with pytest.raises(DBAPIError, match="row-level security"):
                conn.execute(
                    text("INSERT INTO company_modules (id, company_id, module, enabled, updated_at) "
                         "VALUES (:id, :c, 'fotos', true, now())"),
                    {"id": uuid.uuid4(), "c": b.company_id},
                )
            trans.rollback()
    finally:
        engine.dispose()
        with app.app_context():
            with db.engine.begin() as conn:
                rls.disable(conn)
                conn.execute(text(f"DROP OWNED BY {role}"))
                conn.execute(text(f"DROP ROLE {role}"))


def test_toda_rota_de_qualidade_pertence_a_um_modulo(app_factory):
    """Falha fechada: rota nova do blueprint `qualidade` sem módulo no CATALOG ficaria aberta com o módulo
    desligado. Ou entra no catálogo, ou entra na lista de rotas do núcleo abaixo (decisão consciente)."""
    app = app_factory({"FEATURE_PUBLIC_API": True})
    NUCLEO_QUALIDADE: set[str] = set()
    soltas = sorted(
        r.endpoint for r in app.url_map.iter_rules()
        if r.endpoint.startswith("qualidade.")
        and modules.module_for_endpoint(r.endpoint) is None
        and r.endpoint not in NUCLEO_QUALIDADE
    )
    assert not soltas, f"rotas de qualidade fora de qualquer módulo: {soltas}"
