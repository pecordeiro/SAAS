"""Reestruturação R3–R5: Preencher etapas, modo simples e Meta e equipe / Como funciona.

Serviço (projects.py), contas (calc.py) e rotas. Os casos A/B das rotas novas ficam em
tests/test_isolation.py (bloco R3–R5)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from flask import g

from app.extensions import db
from app.models import Activity, AuditLog, Company, Project, ProgressEntry, Stage, User
from app.services import audit, calc
from app.services import projects as svc
from tests.conftest import login, make_tenant, post, text_of


@pytest.fixture()
def ctx(app):
    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "203.0.113.9"}):
        tenant = make_tenant("A")
        g.company = db.session.get(Company, tenant.company_id)
        owner = db.session.get(User, tenant.owner_id)
        yield g.company, owner, tenant


def _simple_project(company, name="Simples", quantity=20, stages=("Corte", "Solda")):
    project = svc.create_project(
        company, name=name, quantity=quantity, start_date=None, due_date=None, people=2,
        hours_per_day=Decimal("8"), stages=[svc.NewStage(name=n) for n in stages], progress_mode="simples",
    )
    db.session.commit()
    return project


# ---------------------------------------------------------------- calc


def test_calc_resumo_equipe_igual_a_aba_equipe():
    etapas = [calc.Etapa((calc.Atividade(30, 4), calc.Atividade(30, 10)), 10)]
    r = calc.resumo_projeto(etapas, 10, 2, 8)
    eq = calc.resumo_equipe(r, 2, 8)
    assert eq.horas_restantes == pytest.approx(3.0) and eq.horas_meta == pytest.approx(10.0)
    assert eq.dias_restantes == pytest.approx(3 / 16) and eq.dias_meta == pytest.approx(10 / 16)
    assert [(l.pessoas, l.horas_equipe, l.atual) for l in eq.linhas] == [
        (1, 8, False), (2, 16, True), (3, 24, False), (4, 32, False), (5, 40, False), (6, 48, False)
    ]
    assert eq.linhas[2].dias == pytest.approx(3 / 24)
    # equipe maior que 6: a linha atual entra no fim, destacada
    grande = calc.resumo_equipe(r, 9, 8)
    assert grande.linhas[-1].pessoas == 9 and grande.linhas[-1].atual and len(grande.linhas) == 7


def test_calc_como_funciona_exemplos_com_os_numeros_atuais():
    etapas = [calc.Etapa((calc.Atividade(15, 4), calc.Atividade(30, 10)), 10), calc.Etapa((calc.Atividade(60, 2),), 10)]
    linhas = calc.como_funciona(etapas, ["Preparação", "Montagem"], [["Cortar", "Soldar"], ["Montar"]], 10, 2, 8)
    por_conta = {l.conta: l.exemplo for l in linhas}
    assert por_conta["Peso da subatividade na etapa"] == "Cortar: 15 min ÷ 45 min = 33%"
    assert por_conta["% concluído da subatividade"] == "Cortar: 4 ÷ 10 = 40%"
    assert por_conta["Progresso da etapa pelas tarefas (Tabela 1)"] == "Preparação: 80,0%"
    assert por_conta["Tempo que falta"] == "Cortar: 15 min × (10 − 4) = 90 min"
    assert por_conta["Unidades concluídas do projeto"] == "Menor valor entre as etapas = 2 de 10"
    assert por_conta["Dias úteis restantes (Meta e equipe)"] == "9,5 h ÷ (2 pessoas × 8 h) = 0,6 dias úteis"
    assert len(linhas) == 11


def test_calc_como_funciona_sem_etapa_e_modo_simples():
    vazias = calc.como_funciona([], [], [], 10, 1, 8)
    assert vazias and all(l.exemplo == calc.SEM_EXEMPLO for l in vazias)
    simples = calc.como_funciona([calc.Etapa((calc.Atividade(60, 9),), 20)], ["Solda"], [["Solda"]], 20, 1, 8, simples=True)
    contas = [l.conta for l in simples]
    assert "Peso da subatividade na etapa" not in contas and contas[0] == "% concluído da etapa"
    assert simples[0].exemplo == "Solda: 45% × 20 = 9 unidades"


# ---------------------------------------------------------------- R4: modo simples


def test_projeto_existente_e_de_teste_continua_detalhado(ctx):
    _, _, tenant = ctx
    assert db.session.get(Project, tenant.project_id).progress_mode == "detalhado"


def test_projeto_simples_cria_atividade_interna_e_percentual_vira_pecas(ctx):
    company, owner, _ = ctx
    project = _simple_project(company)
    stage = project.stages[0]
    (activity,) = svc.active_activities(stage)
    assert activity.name == "Corte" and activity.ideal_minutes == svc.SIMPLE_DEFAULT_MINUTES
    svc.set_stage_percent(stage, svc.parse_percent("45,5"), activity.version, owner.id, can_decrease=False)
    db.session.commit()
    assert activity.units_done == calc.pecas_de_percentual(0.455, 20) == 9
    assert svc.summary(project).etapas[0].progresso == pytest.approx(0.45)
    # renomear a etapa leva a atividade interna junto
    svc.rename_stage(stage, "Corte a laser", stage.version, owner.id)
    db.session.commit()
    assert svc.active_activities(stage)[0].name == "Corte a laser"
    # nova etapa num projeto simples já nasce com a atividade interna
    new = svc.add_stage(project, "Pintura", [])
    assert [a.name for a in svc.active_activities(new)] == ["Pintura"]


@pytest.mark.parametrize("raw", ["", "abc", "-1", "100,5", "101", "45,55", "1e2x"])
def test_percentual_invalido(raw):
    with pytest.raises(svc.ProgressError):
        svc.parse_percent(raw)


def test_percentual_valido():
    assert svc.parse_percent("45%") == Decimal("45.0")
    assert svc.parse_percent(" 0 ") == Decimal("0.0")
    assert svc.parse_percent("100") == Decimal("100.0")
    assert svc.parse_percent("12.5") == Decimal("12.5")


@pytest.mark.parametrize("raw,ok", [("0", 0), ("10", 10), ("3", 3), ("", None), ("2,5", None), ("-1", None), ("11", None), ("x", None)])
def test_pecas_so_inteiro_de_0_ate_previstas(raw, ok):
    if ok is None:
        with pytest.raises(svc.ProgressError):
            svc.parse_pieces(raw, 10)
    else:
        assert svc.parse_pieces(raw, 10) == ok


def test_trocar_modo_detalhado_para_simples_so_com_uma_atividade_por_etapa(ctx):
    company, owner, tenant = ctx
    project = db.session.get(Project, tenant.project_id)  # 1 etapa com 2 atividades
    with pytest.raises(svc.EditError) as exc:
        svc.set_progress_mode(project, "simples", owner.id)
    assert "Etapa 1" in str(exc.value)
    db.session.rollback()
    project = db.session.get(Project, tenant.project_id)
    svc.archive_activity(project.stages[0].activities[1], owner.id)
    assert svc.set_progress_mode(project, "simples", owner.id) is True
    db.session.commit()
    assert project.progress_mode == "simples"
    assert db.session.query(AuditLog).filter_by(action=audit.PROJECT_MODE_CHANGED).count() == 1
    # de volta ao detalhado: mantém a atividade
    assert svc.set_progress_mode(project, "detalhado", owner.id) is True
    assert [a.name for a in svc.active_activities(project.stages[0])] == ["Atividade 1"]
    assert svc.set_progress_mode(project, "detalhado", owner.id) is False


def test_simples_com_etapa_sem_atividade_ganha_a_interna_ao_trocar(ctx):
    company, owner, _ = ctx
    project = svc.create_project(
        company, name="Sem atividade", quantity=5, start_date=None, due_date=None, people=1,
        hours_per_day=Decimal("8"), stages=[svc.NewStage(name="Só nome")],
    )
    assert svc.active_activities(project.stages[0]) == []
    svc.set_progress_mode(project, "simples", owner.id)
    assert [a.name for a in svc.active_activities(project.stages[0])] == ["Só nome"]


def test_projeto_simples_recusa_mais_de_uma_atividade_por_etapa(ctx):
    company, _, _ = ctx
    with pytest.raises(svc.EditError):
        svc.create_project(
            company, name="X", quantity=5, start_date=None, due_date=None, people=1, hours_per_day=Decimal("8"),
            stages=[svc.NewStage(name="E", activities=[svc.NewActivity("a", Decimal(1)), svc.NewActivity("b", Decimal(1))])],
            progress_mode="simples",
        )


def test_duplicar_mantem_o_modo(ctx):
    company, owner, _ = ctx
    project = _simple_project(company)
    copy = svc.duplicate_project(project, owner.id)
    assert copy.progress_mode == "simples"


# ---------------------------------------------------------------- R3: peças em valor absoluto


def test_pecas_absolutas_para_cima_registra_e_para_baixo_corrige(ctx):
    company, owner, tenant = ctx
    activity = db.session.get(Activity, tenant.activity_id)
    svc.set_units_done(activity, 6, activity.version, owner.id, can_decrease=False)
    db.session.commit()
    assert activity.units_done == 6 and activity.version == 2
    assert svc.set_units_done(activity, 6, activity.version, owner.id, can_decrease=False) is None
    with pytest.raises(svc.ProgressError, match="supervisor"):
        svc.set_units_done(activity, 4, activity.version, owner.id, can_decrease=False)
    entry = svc.set_units_done(activity, 4, activity.version, owner.id, can_decrease=True)
    db.session.commit()
    assert entry.delta == -2 and activity.units_done == 4 and entry.reverts_entry_id is None
    assert db.session.query(AuditLog).filter_by(action=audit.PROGRESS_CORRECTED).count() == 1
    deltas = sorted(e.delta for e in db.session.query(ProgressEntry).filter_by(activity_id=activity.id))
    assert deltas == [-2, 6]
    with pytest.raises(svc.ConflictError):
        svc.set_units_done(activity, 5, 1, owner.id, can_decrease=True)
    with pytest.raises(svc.ProgressError):
        svc.set_units_done(activity, 11, activity.version, owner.id, can_decrease=True)


# ---------------------------------------------------------------- R3: desfazer exclusão


def test_excluir_e_desfazer_exclusao_de_etapa_e_atividade(ctx):
    company, owner, tenant = ctx
    project = db.session.get(Project, tenant.project_id)
    stage = project.stages[0]
    activity = stage.activities[0]
    svc.archive_activity(activity, owner.id)
    svc.archive_stage(stage, owner.id)
    db.session.commit()
    assert svc.archived_stages(project) == [stage]
    with pytest.raises(svc.EditError, match="etapa"):
        svc.unarchive_activity(activity, owner.id)
    svc.unarchive_stage(stage, owner.id)
    svc.unarchive_activity(activity, owner.id)
    db.session.commit()
    assert stage.archived_at is None and activity.archived_at is None
    actions = {a.action for a in db.session.query(AuditLog).filter_by(company_id=company.id)}
    assert {audit.STAGE_UNARCHIVED, audit.ACTIVITY_UNARCHIVED} <= actions
    with pytest.raises(svc.EditError):
        svc.unarchive_stage(stage, owner.id)
