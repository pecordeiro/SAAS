"""Fase 4 — serviços: modelos versionados, edição, desfazer, eventos, auditoria, limites de
plano, importação e exportação. Rotas ficam em test_fase4_routes.py."""

from __future__ import annotations

import csv
import io
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from flask import g
from sqlalchemy import select

from app.extensions import db
from app.models import (
    PROJECT_ACTIVE,
    PROJECT_DONE,
    Activity,
    AuditLog,
    Company,
    DomainEvent,
    Invitation,
    Membership,
    Project,
    ProgressEntry,
    Stage,
    Subscription,
    User,
)
from app.services import audit, entitlements, events, exporter, importer
from app.services import projects as svc
from app.services import templates as tsvc
from app.services.plans import EMPRESA, ESSENCIAL, PROFISSIONAL, get_plan
from tests.conftest import make_tenant

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "docs" / "referencia" / "acompanhamento_montagem_v4.xlsx"


@pytest.fixture()
def ctx(app):
    """Contexto de requisição com a empresa A ativa (como depois do tenant_required)."""
    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "203.0.113.7"}):
        tenant = make_tenant("A")
        company = db.session.get(Company, tenant.company_id)
        g.company = company
        owner = db.session.get(User, tenant.owner_id)
        yield company, owner, tenant


def _stages(*spec):
    return [svc.NewStage(name, [svc.NewActivity(a, Decimal(str(m))) for a, m in acts]) for name, acts in spec]


def _events(company_id, kind=None):
    query = select(DomainEvent).where(DomainEvent.company_id == company_id)
    if kind:
        query = query.where(DomainEvent.type == kind)
    return list(db.session.execute(query).scalars())


def _project(company, quantity=2, stages=None, name="P"):
    return svc.create_project(
        company, name=name, quantity=quantity, start_date=None, due_date=None, people=1,
        hours_per_day=Decimal("8"), stages=stages or _stages(("E1", [("a", 10), ("b", 20)]), ("E2", [("c", 5)])),
    )


# ---------------------------------------------------------------- modelos (F4-1, F4-2)


def test_editar_modelo_cria_versao_e_projeto_antigo_nao_muda(ctx):
    company, owner, _ = ctx
    template = tsvc.create_template(company, "Compacto", _stages(("Base", [("Corte", 60), ("Furação", 45)])), owner.id)
    v1 = template.current_version
    project = tsvc.create_project_from_template(
        company, template, name="Lote 1", quantity=10, start_date=None, due_date=None, people=2, hours_per_day=Decimal("8")
    )
    db.session.commit()
    assert project.template_version_id == v1.id
    assert [(s.name, [(a.name, a.ideal_minutes) for a in s.activities]) for s in project.stages] == [
        ("Base", [("Corte", Decimal("60")), ("Furação", Decimal("45"))])
    ]
    v2 = tsvc.update_template(
        template, name="Compacto", description="d", user_id=owner.id,
        stages=_stages(("Base", [("Corte", 50), ("Furação", 45)]), ("Pintura", [("Pintar", 30)])),
    )
    db.session.commit()
    assert v2.number == 2 and template.current_version_id == v2.id
    db.session.refresh(project)
    assert project.template_version_id == v1.id
    assert [a.ideal_minutes for a in project.stages[0].activities] == [Decimal("60"), Decimal("45")]
    assert len(project.stages) == 1
    # Sem mudança nas etapas → sem versão nova (só renomeia)
    assert tsvc.update_template(template, name="Compacto X", description=None, user_id=owner.id,
                                stages=tsvc.stages_from_version(v2)) is None
    assert template.name == "Compacto X" and len(template.versions) == 2
    assert tsvc.minutes_per_unit(v2) == Decimal("125")
    assert tsvc.minutes_per_unit(None) == Decimal("0")
    assert tsvc.projects_using(template) == 1


def test_comparar_e_aplicar_so_com_versao_confirmada(ctx):
    company, owner, _ = ctx
    template = tsvc.create_template(
        company, "M", _stages(("A", [("a1", 10), ("a2", 20)]), ("B", [("b1", 5)]), ("C", [("c1", 1)])), owner.id
    )
    project = tsvc.create_project_from_template(
        company, template, name="P", quantity=4, start_date=None, due_date=None, people=1, hours_per_day=Decimal("8")
    )
    svc.register_progress(project.stages[0].activities[1], 3, None, owner.id)  # a2: 3 peças
    db.session.commit()
    assert tsvc.compare(project).up_to_date and tsvc.compare(project).changes == ()
    v2 = tsvc.update_template(
        template, name="M", description=None, user_id=owner.id,
        # B sai, ordem A/C troca, a1 muda tempo, a2 sai, a3 entra, D entra
        stages=_stages(("C", [("c1", 1)]), ("A", [("a1", 15), ("a3", 7)]), ("D", [("d1", 2)])),
    )
    db.session.commit()
    comparison = tsvc.compare(project)
    assert not comparison.up_to_date
    kinds = sorted(c.kind for c in comparison.changes)
    assert kinds == sorted(
        ["minutes_changed", "activity_added", "activity_removed", "stage_added", "activity_added", "stage_removed", "order_changed"]
    )
    assert all(c.label for c in comparison.changes)
    # Projeto continua igual até a confirmação
    assert [s.name for s in svc.active_stages(project)] == ["A", "B", "C"]
    with pytest.raises(tsvc.TemplateError):
        tsvc.apply_current_version(project, project.template_version_id, owner.id)  # versão errada
    tsvc.apply_current_version(project, v2.id, owner.id)
    db.session.commit()
    db.session.refresh(project)
    assert project.template_version_id == v2.id
    assert [s.name for s in svc.active_stages(project)] == ["C", "A", "D"]
    stage_a = svc.active_stages(project)[1]
    assert [(a.name, a.ideal_minutes) for a in svc.active_activities(stage_a)] == [("a1", Decimal("15")), ("a3", Decimal("7"))]
    # a2 (com 3 peças) e B ficaram arquivadas, nada apagado
    a2 = db.session.execute(select(Activity).where(Activity.name == "a2")).scalar_one()
    assert a2.archived_at is not None and a2.units_done == 3
    assert db.session.execute(select(Stage).where(Stage.name == "B")).scalar_one().archived_at is not None
    log = db.session.execute(select(AuditLog).where(AuditLog.action == audit.TEMPLATE_VERSION_APPLIED)).scalar_one()
    assert log.details["from_version"] == 1 and log.details["to_version"] == 2
    assert log.actor_user_id == owner.id and log.ip == "203.0.113.7" and log.object_id == project.id
    assert tsvc.compare(project).changes == ()
    with pytest.raises(tsvc.TemplateError):
        tsvc.apply_current_version(project, v2.id, owner.id)  # nada a aplicar


def test_comparar_projeto_sem_modelo(ctx):
    company, owner, tenant = ctx
    project = db.session.get(Project, tenant.project_id)
    comparison = tsvc.compare(project)
    assert comparison.current_version is None and comparison.up_to_date
    with pytest.raises(tsvc.TemplateError):
        tsvc.apply_current_version(project, project.id, owner.id)


def test_modelo_nome_repetido_vazio_e_sem_etapas(ctx):
    company, owner, _ = ctx
    tsvc.create_template(company, "Único", _stages(("E", [("a", 1)])), owner.id)
    with pytest.raises(tsvc.TemplateError):
        tsvc.create_template(company, "único", _stages(("E", [("a", 1)])), owner.id)
    with pytest.raises(tsvc.TemplateError):
        tsvc.create_template(company, " ", _stages(("E", [("a", 1)])), owner.id)
    with pytest.raises(tsvc.TemplateError):
        tsvc.create_template(company, "Outro", [], owner.id)


def test_arquivar_modelo_some_da_lista_e_nao_cria_projeto(ctx):
    company, owner, _ = ctx
    template = tsvc.create_template(company, "Velho", _stages(("E", [("a", 1)])), owner.id)
    assert [t.name for t in tsvc.list_templates()] == ["Velho"]
    tsvc.archive_template(template, owner.id)
    assert tsvc.list_templates() == []
    with pytest.raises(tsvc.TemplateError):
        tsvc.create_project_from_template(
            company, template, name="X", quantity=1, start_date=None, due_date=None, people=1, hours_per_day=Decimal("8")
        )


def test_modelo_de_outra_empresa_nao_cria_projeto(app):
    with app.test_request_context("/"):
        a, b = make_tenant("A"), make_tenant("B")
        company_a = db.session.get(Company, a.company_id)
        company_b = db.session.get(Company, b.company_id)
        template_b = tsvc.create_template(company_b, "De B", _stages(("E", [("a", 1)])))
        with pytest.raises(tsvc.TemplateError):
            tsvc.create_project_from_template(
                company_a, template_b, name="X", quantity=1, start_date=None, due_date=None, people=1,
                hours_per_day=Decimal("8"),
            )


# ---------------------------------------------------------------- edição (F4-3, F4-4)


def test_reordenar_etapas_persiste(ctx):
    company, owner, _ = ctx
    project = _project(company, stages=_stages(("A", []), ("B", []), ("C", [])))
    db.session.commit()
    ids = {s.name: s.id for s in project.stages}
    svc.reorder_stages(project, [ids["C"], ids["A"], ids["B"]])
    db.session.commit()
    db.session.expire_all()
    project = db.session.get(Project, project.id)
    assert [s.name for s in svc.active_stages(project)] == ["C", "A", "B"]
    with pytest.raises(svc.EditError):
        svc.reorder_stages(project, [ids["C"], ids["A"]])


def test_mover_renomear_e_arquivar_sem_perder_historico(ctx):
    company, owner, _ = ctx
    project = _project(company, quantity=3)
    db.session.commit()
    e1, e2 = project.stages
    assert svc.move_stage(e2, -1) is True
    assert svc.move_stage(e2, -1) is False  # já é a primeira
    assert [s.name for s in svc.active_stages(project)] == ["E2", "E1"]
    a, b = e1.activities
    assert svc.move_activity(a, 1) is True
    assert [x.name for x in svc.active_activities(e1)] == ["b", "a"]
    svc.rename_stage(e1, "  Etapa um ")
    assert e1.name == "Etapa um"
    with pytest.raises(svc.EditError):
        svc.rename_stage(e1, "")
    svc.update_activity(a, "a2", Decimal("12.5"))
    assert (a.name, a.ideal_minutes) == ("a2", Decimal("12.5"))
    with pytest.raises(svc.EditError):
        svc.update_activity(a, "a2", Decimal("-1"))
    entry = svc.register_progress(a, 2, None, owner.id)
    svc.archive_activity(a, owner.id)
    db.session.commit()
    assert [x.name for x in svc.active_activities(e1)] == ["b"]
    assert entry in svc.history(project)  # histórico mantém
    rows = exporter.rows(project)
    assert any(r[exporter.COL_ACTIVITY] == "a2" and r[exporter.COL_STATUS] == exporter.STATUS_ARCHIVED for r in rows)
    # mover com arquivado no meio: pula o arquivado
    assert svc.move_activity(b, -1) is False
    svc.archive_stage(e2, owner.id)
    db.session.commit()
    assert [s.name for s in svc.active_stages(project)] == ["Etapa um"]
    actions = {log.action for log in audit.for_object(company.id, "project", project.id)}
    assert {audit.ACTIVITY_ARCHIVED, audit.STAGE_ARCHIVED} <= actions


def test_editar_dados_do_projeto(ctx):
    company, owner, _ = ctx
    project = _project(company, quantity=5)
    svc.register_progress(project.stages[0].activities[0], 4, None, owner.id)
    with pytest.raises(svc.EditError):
        svc.update_project(project, name="X", quantity=3, start_date=None, due_date=None, people=1,
                           hours_per_day=Decimal("8"), user_id=owner.id)
    with pytest.raises(svc.EditError):
        svc.update_project(project, name="X", quantity=5, start_date=date(2026, 10, 10), due_date=date(2026, 10, 1),
                           people=1, hours_per_day=Decimal("8"), user_id=owner.id)
    svc.update_project(project, name="Novo", quantity=4, start_date=date(2026, 10, 1), due_date=date(2026, 10, 30),
                       people=3, hours_per_day=Decimal("6"), user_id=owner.id)
    assert (project.name, project.quantity, project.people) == ("Novo", 4, 3)
    log = audit.for_object(company.id, "project", project.id)[0]
    assert log.action == audit.PROJECT_UPDATED and log.details["antes"]["quantity"] == 5


def test_duplicar_projeto_zera_progresso(ctx):
    company, owner, _ = ctx
    project = _project(company, quantity=3)
    svc.register_progress(project.stages[0].activities[0], 2, None, owner.id)
    svc.archive_activity(project.stages[1].activities[0], owner.id)
    copy = svc.duplicate_project(project, owner.id)
    db.session.commit()
    assert copy.name == "Cópia de P" and copy.quantity == 3 and copy.id != project.id
    assert [(s.name, [(a.name, a.units_done) for a in s.activities]) for s in copy.stages] == [
        ("E1", [("a", 0), ("b", 0)]),
        ("E2", []),
    ]
    assert svc.history(copy) == []


def test_arquivar_projeto_some_da_lista(ctx):
    company, owner, tenant = ctx
    project = db.session.get(Project, tenant.project_id)
    svc.archive_project(project, owner.id)
    db.session.commit()
    assert svc.list_projects() == []


# ---------------------------------------------------------------- desfazer (D13) e eventos


def test_desfazer_grava_compensatorio_append_only(ctx):
    company, owner, _ = ctx
    project = _project(company, quantity=2)
    activity = project.stages[0].activities[0]
    entry = svc.register_progress(activity, 2, None, owner.id)
    db.session.commit()
    reversal = svc.undo_progress(entry, owner.id)
    db.session.commit()
    assert reversal.delta == -2 and reversal.reverts_entry_id == entry.id
    assert activity.units_done == 0 and activity.version == 3
    assert svc.is_undone(entry)
    assert db.session.get(ProgressEntry, entry.id).delta == 2  # original intacto
    with pytest.raises(svc.ProgressError):
        svc.undo_progress(entry, owner.id)
    with pytest.raises(svc.ProgressError):
        svc.undo_progress(reversal, owner.id)
    log = db.session.execute(select(AuditLog).where(AuditLog.action == audit.PROGRESS_UNDONE)).scalar_one()
    assert log.actor_user_id == owner.id and log.ip == "203.0.113.7" and log.details["delta"] == 2
    progress_events = _events(company.id, events.ACTIVITY_PROGRESS_UPDATED)
    assert sorted(e.payload["delta"] for e in progress_events) == [-2, 2]


def test_eventos_na_mesma_transacao_e_exatamente_um(ctx):
    company, owner, _ = ctx
    base_events = len(_events(company.id))
    project = _project(company, quantity=1, stages=_stages(("E1", [("a", 1)]), ("E2", [("b", 1)])))
    db.session.commit()
    assert len(_events(company.id, events.PROJECT_CREATED)) == 2  # o do make_tenant + este
    a = project.stages[0].activities[0]
    b = project.stages[1].activities[0]
    # rollback leva o evento junto
    svc.register_progress(a, 1, None, owner.id)
    db.session.rollback()
    assert len(_events(company.id)) == base_events + 1
    a = db.session.get(Activity, a.id)
    b = db.session.get(Activity, b.id)
    svc.register_progress(a, 1, None, owner.id)
    db.session.commit()
    assert len(_events(company.id, events.ACTIVITY_PROGRESS_UPDATED)) == 1
    assert len(_events(company.id, events.STAGE_COMPLETED)) == 1
    assert _events(company.id, events.PROJECT_COMPLETED) == []
    svc.register_progress(b, 1, None, owner.id)
    db.session.commit()
    assert len(_events(company.id, events.STAGE_COMPLETED)) == 2
    done = _events(company.id, events.PROJECT_COMPLETED)
    assert len(done) == 1 and done[0].payload["project_id"] == str(project.id)
    assert db.session.get(Project, project.id).status == PROJECT_DONE
    # desfazer volta para ativo sem novo evento de conclusão
    entry = svc.history(project)[0]
    svc.undo_progress(entry, owner.id)
    db.session.commit()
    assert db.session.get(Project, project.id).status == PROJECT_ACTIVE
    assert len(_events(company.id, events.PROJECT_COMPLETED)) == 1


def test_emit_recusa_tipo_desconhecido(ctx):
    company, _, _ = ctx
    with pytest.raises(ValueError):
        events.emit(company.id, "qualquer.coisa", {})
    event = events.emit(company.id, events.PROJECT_CREATED, {"x": Decimal("1.5"), "l": [Decimal("2")]})
    assert event.payload == {"x": 1.5, "l": [2.0]}


def test_audit_record_para_fase5_e_sem_request(app):
    with app.app_context():
        tenant = make_tenant("A")
        entry = audit.record(
            audit.ROLE_CHANGED, company_id=tenant.company_id, actor_user_id=tenant.owner_id,
            object_type="membership", object_id=tenant.operator_id, details={"de": "operator", "para": "supervisor"},
        )
        db.session.commit()
        assert entry.ip is None and entry.action == "membership.role_changed"
        assert audit.ACTION_LABELS[audit.ROLE_CHANGED] == "Papel alterado"


# ---------------------------------------------------------------- limites de plano (F4-7)


def _subscribe(company, code, status="active", **kw):
    sub = Subscription(company_id=company.id, plan_id=get_plan(code).id, provider="fake", status=status, **kw)
    db.session.add(sub)
    db.session.flush()
    return sub


def test_limite_de_projetos_do_plano(ctx):
    company, owner, _ = ctx
    _subscribe(company, ESSENCIAL)
    for n in ("2", "3", "4", "5"):
        _project(company, name=n)
    assert entitlements.count_active_projects(company.id) == 5
    with pytest.raises(entitlements.PlanLimitError) as exc:
        _project(company, name="6")
    assert "Essencial permite 5 projetos" in exc.value.message and exc.value.status_code == 402
    # Concluído ou arquivado libera vaga
    project = svc.list_projects()[0]
    svc.archive_project(project, owner.id)
    _project(company, name="6")
    usage = entitlements.usage(company)
    assert usage["projects"] == 5 and usage["max_projects"] == 5 and usage["writable"]


def test_plano_empresa_sem_limite_de_projetos_e_features(ctx):
    company, _, _ = ctx
    _subscribe(company, EMPRESA)
    entitlements.check_can_create_project(company, adding=1000)
    assert entitlements.has_feature(company, "api")
    entitlements.require_feature(company, "api", "API")


def test_limite_de_usuarios_conta_convites_pendentes(ctx):
    company, owner, _ = ctx
    _subscribe(company, PROFISSIONAL)  # 25 pessoas; o tenant tem 3 vínculos
    now = datetime.now(timezone.utc)
    db.session.add(Invitation(company_id=company.id, email="a@x.com", role="operator", token_hash="1" * 64,
                              expires_at=now + timedelta(days=3)))
    db.session.add(Invitation(company_id=company.id, email="b@x.com", role="operator", token_hash="2" * 64,
                              expires_at=now - timedelta(days=1)))  # vencido não conta
    db.session.flush()
    assert entitlements.count_users(company.id) == 4
    entitlements.check_can_add_user(company, adding=21)
    with pytest.raises(entitlements.PlanLimitError):
        entitlements.check_can_add_user(company, adding=22)
    assert not entitlements.has_feature(company, "api")
    with pytest.raises(entitlements.PlanLimitError):
        entitlements.require_feature(company, "api", "API")


@pytest.mark.parametrize(
    "status,fields,writable",
    [
        ("active", {}, True),
        ("trialing", {"trial_ends_at": +1}, True),
        ("trialing", {"trial_ends_at": -1}, False),
        ("trialing", {}, True),
        ("past_due", {"grace_until": +1}, True),
        ("past_due", {"grace_until": -1}, False),
        ("past_due", {"current_period_end": -3}, True),  # carência padrão de 7 dias
        ("past_due", {"current_period_end": -10}, False),
        ("past_due", {}, False),
        ("canceled", {"current_period_end": +5}, True),
        ("canceled", {"current_period_end": -1}, False),
        ("canceled", {}, False),
        ("expired", {}, False),
    ],
)
def test_modo_leitura_por_status(ctx, status, fields, writable):
    company, _, _ = ctx
    now = datetime.now(timezone.utc)
    _subscribe(company, ESSENCIAL, status=status, **{k: now + timedelta(days=v) for k, v in fields.items()})
    assert entitlements.is_read_only(company) is (not writable)
    if writable:
        entitlements.ensure_writable(company)
    else:
        with pytest.raises(entitlements.ReadOnlyError):
            entitlements.ensure_writable(company)


def test_sem_assinatura_teste_implicito_e_regra_configuravel(ctx, app):
    company, _, _ = ctx
    assert not entitlements.is_read_only(company)
    assert entitlements.effective_plan(company).code == "profissional"
    company.created_at = datetime.now(timezone.utc) - timedelta(days=15)
    db.session.flush()
    assert entitlements.is_read_only(company)
    app.config["READ_ONLY_ENFORCED"] = False
    try:
        assert not entitlements.is_read_only(company)
        assert entitlements.usage(company)["writable"]
    finally:
        app.config["READ_ONLY_ENFORCED"] = True


# ---------------------------------------------------------------- importação e exportação (F4-5, F4-6)


def _csv(rows, header=exporter.COLUMNS[:11], delimiter=";") -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter)
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _row(stage, activity, minutes, units="0", project="", quantity="", status="ativa"):
    return [project, quantity, "", "", "", "", stage, activity, minutes, units, status]


def test_importar_csv_valido(ctx):
    data = _csv([
        ["Lote", "10", "05/10/2026", "2026-10-30", "3", "7,5", "Base", "Corte", "60", "2", "ativa"],
        _row("Base", "Furação", "45,5"),
        _row("Pintura", "", ""),
    ], delimiter=",")
    result = importer.parse_upload("x.csv", data, 10**6)
    assert result.ok, result.errors
    assert (result.name, result.quantity, result.people, result.hours_per_day) == ("Lote", 10, 3, Decimal("7.50"))
    assert (result.start_date, result.due_date) == (date(2026, 10, 5), date(2026, 10, 30))
    assert [(s.name, [(a.name, a.ideal_minutes, a.units_done) for a in s.activities]) for s in result.stages] == [
        ("Base", [("Corte", Decimal("60.00"), 2), ("Furação", Decimal("45.50"), 0)]),
        ("Pintura", []),
    ]


def test_importar_csv_com_erro_na_linha_7_nao_grava(ctx):
    company, owner, _ = ctx
    rows = [["Lote", "10", "", "", "", "", "Base", "A1", "10", "0", "ativa"]]
    rows += [_row("Base", f"A{i}", "10") for i in range(2, 6)]
    rows += [_row("Base", "Quebrada", "dez")]  # linha 7 do arquivo (1 = cabeçalho)
    result = importer.parse_upload("x.csv", _csv(rows), 10**6)
    assert not result.ok
    assert [str(e) for e in result.errors] == ["Linha 7, tempo ideal: número inválido"]
    before = db.session.query(Project).count()
    with pytest.raises(ValueError):
        importer.save(company, result, owner.id)
    assert db.session.query(Project).count() == before


@pytest.mark.parametrize(
    "rows,expected",
    [
        ([["", "10", "", "", "", "", "E", "A", "1", "0", "ativa"]], "Projeto"),
        ([["L", "0", "", "", "", "", "E", "A", "1", "0", "ativa"]], "Quantidade"),
        ([["L", "2", "32/13/2026", "", "", "", "E", "A", "1", "0", "ativa"]], "Início"),
        ([["L", "2", "10/10/2026", "01/10/2026", "", "", "E", "A", "1", "0", "ativa"]], "Prazo"),
        ([["L", "2", "", "", "0", "", "E", "A", "1", "0", "ativa"]], "Pessoas"),
        ([["L", "2", "", "", "", "30", "E", "A", "1", "0", "ativa"]], "Horas por dia"),
        ([["L", "2", "", "", "", "", "", "A", "1", "0", "ativa"]], "Etapa"),
        ([["L", "2", "", "", "", "", "E" * 161, "A", "1", "0", "ativa"]], "Etapa"),
        ([["L", "2", "", "", "", "", "E", "A", "1", "0", "talvez"]], "Situação"),
        ([["L", "2", "", "", "", "", "E", "A" * 161, "1", "0", "ativa"]], "Atividade"),
        ([["L", "2", "", "", "", "", "E", "A", "-1", "0", "ativa"]], "tempo ideal"),
        ([["L", "2", "", "", "", "", "E", "A", "1", "1,5", "ativa"]], "Peças concluídas"),
        ([["L", "2", "", "", "", "", "E", "A", "1", "3", "ativa"]], "Peças concluídas"),
    ],
)
def test_importar_csv_erros_por_coluna(ctx, rows, expected):
    result = importer.parse_upload("x.csv", _csv(rows), 10**6)
    assert [e.column for e in result.errors] == [expected], result.errors


def test_importar_csv_cabecalho_e_arquivo(ctx):
    assert importer.parse_upload("x.csv", _csv([], header=["Etapa"]), 10**6).errors[0].column == "cabeçalho"
    assert importer.parse_upload("x.csv", _csv([]), 10**6).errors[0].message == "nenhuma linha de dados"
    assert importer.parse_upload("x.csv", b"\n", 10**6).errors[0].column == "cabeçalho"
    assert importer.parse_csv(b"").errors[0].message == "vazio"
    latin = _csv([["Lote ç", "1", "", "", "", "", "E", "A", "1", "0", "ativa"]]).decode().encode("cp1252")
    assert importer.parse_upload("x.csv", latin, 10**6).name == "Lote ç"
    with pytest.raises(importer.ImportError_):
        importer.parse_upload("x.csv", b"a\x00b", 10**6)
    with pytest.raises(importer.ImportError_):
        importer.parse_upload("x.csv", b"", 10**6)
    with pytest.raises(importer.ImportError_):
        importer.parse_upload("x.csv", b"x" * 11, 10)
    with pytest.raises(importer.ImportError_):
        importer.parse_upload("x.exe", b"MZ", 10**6)
    with pytest.raises(importer.ImportError_):
        importer.parse_upload("x.xlsx", b"nao e zip", 10**6)  # extensão sem o conteúdo
    with pytest.raises(importer.ImportError_):
        importer.parse_upload("x.csv", b"PK\x03\x04resto", 10**6)
    with pytest.raises(importer.ImportError_):
        importer.parse_upload("x.xlsx", b"PK\x03\x04quebrado", 10**6)


def test_importar_limites_de_linhas(ctx, monkeypatch):
    monkeypatch.setattr(importer, "MAX_ROWS", 2)
    monkeypatch.setattr(importer, "MAX_STAGES", 1)
    monkeypatch.setattr(importer, "MAX_ACTIVITIES_PER_STAGE", 1)
    rows = [["L", "2", "", "", "", "", "E", "A", "1", "0", "ativa"], _row("E", "B", "1"), _row("F", "C", "1")]
    messages = [e.message for e in importer.parse_upload("x.csv", _csv(rows), 10**6).errors]
    assert messages == ["mais de 1 subatividades na etapa", "mais de 2 linhas"]
    rows = [["L", "2", "", "", "", "", "E", "A", "1", "0", "ativa"], _row("F", "C", "1")]
    assert [e.message for e in importer.parse_upload("x.csv", _csv(rows), 10**6).errors] == ["mais de 1 etapas"]


def test_zip_bomb_recusado(ctx, monkeypatch):
    monkeypatch.setattr(importer, "MAX_UNCOMPRESSED", 10)
    data = XLSX.read_bytes()
    with pytest.raises(importer.ImportError_):
        importer.parse_upload("x.xlsx", data, 10**7)


def test_importar_planilha_de_referencia_pelos_titulos(ctx):
    company, owner, _ = ctx
    if not XLSX.exists():  # pragma: no cover
        pytest.skip("planilha de referência ausente")
    result = importer.parse_upload("acompanhamento.xlsx", XLSX.read_bytes(), 10**7)
    assert result.ok, result.errors
    assert result.source == importer.SOURCE_REFERENCE
    assert result.quantity == 10 and result.people == 1 and result.hours_per_day == Decimal("8.00")
    assert len(result.stages) == 24
    first = result.stages[0]
    assert first.name == "3. Montagem do Suporte de Manutenção"
    assert [(a.name, a.ideal_minutes, a.units_done) for a in first.activities] == [
        ("Alinhamento", Decimal("10.00"), 5),
        ("Instalar pé", Decimal("10.00"), 5),
        ("Montar placa de manutenção", Decimal("10.00"), 5),
        ("Instalar placa", Decimal("100.00"), 0),
    ]
    project = importer.save(company, result, owner.id, name="SoBot")
    db.session.commit()
    assert project.name == "SoBot" and len(project.stages) == 24
    # o histórico soma as peças importadas
    total_entries = sum(e.delta for e in svc.history(project, limit=1000))
    assert total_entries == sum(a.units_done for s in project.stages for a in s.activities) > 0
    # mesmos indicadores que o calc dá para a planilha (tempo restante 29,1666 h)
    assert svc.summary(project).tempo_restante_min / 60 == pytest.approx(29.166666666666668)


def test_planilha_sem_blocos_ou_com_valores_invalidos(ctx):
    from openpyxl import Workbook

    def book(cells: dict, team: dict | None = None) -> bytes:
        wb = Workbook()
        ws = wb.active
        for (r, c), v in cells.items():
            ws.cell(r, c, v)
        if team is not None:
            t = wb.create_sheet("Equipe")
            for (r, c), v in team.items():
                t.cell(r, c, v)
        buffer = io.BytesIO()
        wb.save(buffer)
        return buffer.getvalue()

    result = importer.parse_upload("x.xlsx", book({(1, 1): "nada"}), 10**6)
    assert result.errors[0].column == "A"
    block = {(1, 1): "T", (5, 1): "1. Etapa", (6, 1): "Unidades previstas", (7, 1): "Subatividade",
             (8, 1): "Atv", (8, 2): "x", (9, 1): "Total da etapa"}
    result = importer.parse_upload("x.xlsx", book(block, {(1, 1): "Pessoas montando", (1, 2): "dois"}), 10**6)
    assert {e.column for e in result.errors} == {"A", "tempo ideal", "Equipe!B (Pessoas montando)"}
    result = importer.parse_upload("x.xlsx", book({**block, (8, 2): 5, (2, 1): "Meta", (2, 2): "dez"}), 10**6)
    assert [e.column for e in result.errors] == ["B (meta)"]


def test_exportar_neutraliza_celulas_perigosas(ctx):
    company, owner, _ = ctx
    project = _project(company, name="=HYPERLINK(\"http://x\")",
                       stages=_stages(("+Etapa", [("-1 atividade", 10), ("@soma", 5), ("\tTab", 1), ("\rCR", 1)])))
    db.session.commit()
    text = exporter.to_csv(project).decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    assert rows[0] == list(exporter.COLUMNS)
    for row in rows[1:]:
        for cell in row:
            assert not cell.startswith(("=", "+", "-", "@", "\t", "\r")), cell
    assert rows[1][0] == "'=HYPERLINK(\"http://x\")" and rows[1][6] == "'+Etapa" and rows[1][7] == "'-1 atividade"
    from openpyxl import load_workbook

    ws = load_workbook(io.BytesIO(exporter.to_xlsx(project))).active
    values = [c.value for row in ws.iter_rows(min_row=2) for c in row if isinstance(c.value, str)]
    assert values and all(not v.startswith(("=", "+", "-", "@", "\t", "\r")) for v in values)
    assert all(c.data_type != "f" for row in ws.iter_rows() for c in row)
    assert exporter.filename(project, "csv") == "hyperlink-http-x.csv"
    assert exporter.neutralize(-5) == -5
    assert exporter.br_decimal(None) == "" and exporter.br_decimal(Decimal("7.50")) == "7,5"
    assert exporter.template_csv().decode("utf-8-sig").startswith("Projeto;Quantidade")


def _shape(project: Project) -> tuple:
    stages = sorted(project.stages, key=lambda s: (s.archived_at is not None, s.position))
    return (
        project.name, project.quantity, project.start_date, project.due_date, project.people,
        Decimal(project.hours_per_day),
        [
            (
                s.name, s.archived_at is not None,
                [
                    (a.name, Decimal(a.ideal_minutes), a.units_done, a.archived_at is not None)
                    for a in sorted(s.activities, key=lambda a: (a.archived_at is not None, a.position))
                ],
            )
            for s in stages
        ],
    )


@pytest.mark.parametrize("fmt", ["csv", "xlsx"])
def test_exportar_e_importar_devolve_os_mesmos_dados(ctx, fmt):
    company, owner, _ = ctx
    project = svc.create_project(
        company, name="-Lote @especial", quantity=6, start_date=date(2026, 10, 5), due_date=date(2026, 11, 20),
        people=3, hours_per_day=Decimal("7.5"),
        stages=_stages(("1. Base", [("Corte", 60), ("Furação", "45.25")]), ("2. Vazia", []), ("3. Fim", [("=Teste", 5)])),
    )
    svc.register_progress(project.stages[0].activities[0], 4, None, owner.id)
    svc.register_progress(project.stages[2].activities[0], 6, None, owner.id)
    extra = svc.add_activity(project.stages[2], svc.NewActivity("Velha", Decimal("3")))
    svc.archive_activity(extra, owner.id)
    gone = svc.add_stage(project, "Arquivada", [svc.NewActivity("x", Decimal("1"))])
    svc.archive_stage(gone, owner.id)
    db.session.commit()
    db.session.expire_all()
    project = db.session.get(Project, project.id)
    data = exporter.to_csv(project) if fmt == "csv" else exporter.to_xlsx(project)
    result = importer.parse_upload(f"x.{fmt}", data, 10**7)
    assert result.ok, result.errors
    # pré-visualização → payload assinado → gravação
    result = importer.from_payload(importer.to_payload(result))
    assert result.ok
    imported = importer.save(company, result, owner.id)
    db.session.commit()
    db.session.expire_all()
    original = db.session.get(Project, project.id)
    imported = db.session.get(Project, imported.id)
    assert _shape(imported) == _shape(original)
    assert svc.summary(imported) == svc.summary(original)


def test_payload_adulterado_e_revalidado(ctx):
    bad = importer.from_payload({"name": "X", "quantity": "dez"})
    assert not bad.ok
    invalid = importer.from_payload({
        "name": "", "quantity": 0, "people": 0, "hours_per_day": "99",
        "stages": [{"name": "", "activities": [{"name": "", "ideal_minutes": "-1", "units_done": 5}]}],
    })
    assert {e.column for e in invalid.errors} >= {"Projeto", "Quantidade", "equipe", "Etapa", "Atividade"}
    assert not importer.from_payload({"name": "X", "quantity": 1, "stages": []}).ok


def test_importacao_respeita_limite_do_plano(ctx):
    company, owner, _ = ctx
    _subscribe(company, ESSENCIAL)
    for n in ("2", "3", "4", "5"):
        _project(company, name=n)
    result = importer.parse_upload("x.csv", _csv([["L", "2", "", "", "", "", "E", "A", "1", "0", "ativa"]]), 10**6)
    with pytest.raises(entitlements.PlanLimitError):
        importer.save(company, result, owner.id)


def test_atraso_previsto_em_dias_uteis(ctx):
    company, _, tenant = ctx
    project = db.session.get(Project, tenant.project_id)
    assert svc.delay_workdays(project, date(2026, 10, 20), company) == 0  # sem prazo
    project.due_date = date(2026, 10, 16)
    assert svc.delay_workdays(project, date(2026, 10, 20), company) == 2
    assert svc.delay_workdays(project, None, company) == 0


def test_membership_inativo_nao_conta_usuario(ctx):
    company, _, tenant = ctx
    membership = db.session.execute(select(Membership).where(Membership.user_id == tenant.operator_id)).scalar_one()
    membership.active = False
    db.session.flush()
    assert entitlements.count_users(company.id) == 2


def test_desfazer_em_projeto_concluido_respeita_limite_do_plano(ctx):
    """Concluir libera vaga; reativar (desfazendo) não pode furar max_projects."""
    company, owner, _ = ctx
    _subscribe(company, ESSENCIAL)
    project = _project(company, quantity=1, stages=_stages(("E1", [("a", 10)])), name="Concluível")
    entry = svc.register_progress(project.stages[0].activities[0], 1, None, owner.id)
    db.session.commit()
    assert project.status == PROJECT_DONE
    # o ctx já tem 1 projeto ativo; com mais 4 o Essencial (5) fica cheio
    for n in ("2", "3", "4", "5"):
        _project(company, name=n)
    assert entitlements.count_active_projects(company.id) == 5
    db.session.commit()
    with pytest.raises(entitlements.PlanLimitError):
        svc.undo_progress(entry, owner.id)
