"""Etapa D — colaboração: autoria, edição com concorrência, atribuição, progresso por
pessoa e arrastar (ordem decidida no servidor)."""

from __future__ import annotations

import re

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


# ================================================================ 3) atribuição


def _assign(client, app, activity_id, user_id):
    return post(client, app, f"/app/atividades/{activity_id}/responsavel", {"assignee_id": str(user_id or "")})


def test_supervisor_atribui_audita_e_grava_evento_interno_so_com_ids(client, app, tenants):
    from app.models import AuditLog, DomainEvent
    from app.services import events

    a, _ = tenants
    login(client, app, a.supervisor_email)
    assert _assign(client, app, a.activity_id, a.operator_id).status_code == 303
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).assignee_id == a.operator_id
        log = db.session.query(AuditLog).filter_by(company_id=a.company_id, action="activity.assigned").one()
        assert log.details["para"] == str(a.operator_id)
        event = db.session.query(DomainEvent).filter_by(company_id=a.company_id, type="activity.assigned").one()
        assert set(event.payload) == {"project_id", "stage_id", "activity_id", "assignee_user_id"}
        assert "@" not in str(event.payload) and "operator A" not in str(event.payload)
        assert events.ACTIVITY_ASSIGNED in events.INTERNAL_EVENT_TYPES
        assert events.ACTIVITY_ASSIGNED not in events.PUBLIC_EVENT_TYPES
    page = text_of(client.get(f"/app/projetos/{a.project_id}"))
    assert "Resp.: operator A" in page
    # Tirar o responsável: audita, sem evento novo.
    assert _assign(client, app, a.activity_id, None).status_code == 303
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).assignee_id is None
        assert db.session.query(DomainEvent).filter_by(type="activity.assigned").count() == 1
        assert db.session.query(AuditLog).filter_by(action="activity.assigned").count() == 2


def test_operador_nao_atribui(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    assert _assign(client, app, a.activity_id, a.operator_id).status_code == 403
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).assignee_id is None


def test_membro_desativado_nao_pode_ser_responsavel_e_perde_atribuicoes(client, app, tenants):
    from app.models import Membership
    from app.services import accounts

    a, _ = tenants
    login(client, app, a.owner_email)
    assert _assign(client, app, a.activity_id, a.operator_id).status_code == 303
    with app.app_context():
        member = db.session.query(Membership).filter_by(user_id=a.operator_id).one()
        accounts.deactivate_member(member)
        assert db.session.get(Activity, a.activity_id).assignee_id is None
    assert _assign(client, app, a.activity_id, a.operator_id).status_code == 404
    page = client.get(f"/app/projetos/{a.project_id}/editar").get_data(as_text=True)
    assert str(a.operator_id) not in page  # não aparece na lista de responsáveis


def test_suporte_da_plataforma_nao_e_responsavel(app, tenants):
    from app.models import Membership

    a, _ = tenants
    with app.app_context():
        user = User(email="suporte@plataforma.com", name="Suporte", password_hash="x")
        db.session.add(user)
        db.session.flush()
        db.session.add(Membership(company_id=a.company_id, user_id=user.id, role="supervisor", is_support=True))
        db.session.commit()
        assert user.id not in {u.id for u in svc.assignable_members(a.company_id)}
        activity = db.session.get(Activity, a.activity_id)
        try:
            svc.assign_activity(activity, user.id, None)
        except svc.AssignError:
            pass
        else:  # pragma: no cover
            raise AssertionError("suporte não pode ser responsável")


# ================================================================ 4) progresso por pessoa


def test_calc_progresso_por_pessoa_agrega_periodo_e_atribuidas():
    from datetime import date

    from app.services.calc import AtividadeAtribuida, Lancamento, progresso_por_pessoa

    d1, d2, d3 = date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 3)
    lancs = [
        Lancamento("ana", "x", 3, d1, 10),
        Lancamento("ana", "y", 2, d2, 30),
        Lancamento("ana", "x", -1, d2, 10),  # desfazer
        Lancamento("bia", "x", 5, d3, 10),
        Lancamento(None, "y", 1, d2, 30),  # autor removido
        Lancamento("ana", "x", 7, date(2026, 9, 1), 10),  # fora do período
    ]
    atrib = [
        AtividadeAtribuida("x", "ana", 10, 10, 10),  # concluída
        AtividadeAtribuida("y", "ana", 30, 3, 10),
        AtividadeAtribuida("z", "caio", 0, 5, 10),  # só responsável, sem lançamento; tempo 0
        AtividadeAtribuida("w", None, 5, 1, 10),  # sem responsável: ignorada
    ]
    res = progresso_por_pessoa(lancs, atrib, inicio=d1, fim=d3)
    by = {r.pessoa: r for r in res}
    assert [r.pessoa for r in res] == ["bia", "ana", "caio", None]
    ana = by["ana"]
    assert (ana.pecas, ana.registros, ana.desfeitos, ana.dias_ativos) == (4, 2, 1, 2)
    assert abs(ana.horas - (3 * 10 + 2 * 30 - 10) / 60) < 1e-9
    assert dict(ana.por_atividade) == {"x": 2, "y": 2}
    assert (ana.atribuidas, ana.atribuidas_concluidas, ana.pecas_atribuidas, ana.previstas_atribuidas) == (2, 1, 13, 20)
    # Σ(tempo × %) ÷ Σ tempo = (10×1 + 30×0,3) ÷ 40
    assert abs(ana.progresso_atribuidas - (10 * 1 + 30 * 0.3) / 40) < 1e-9
    caio = by["caio"]
    assert (caio.pecas, caio.registros, caio.atribuidas) == (0, 0, 1)
    assert abs(caio.progresso_atribuidas - 0.5) < 1e-9  # tempos 0 → média simples
    assert by[None].pecas == 1
    # Sem limites: tudo entra.
    assert {r.pessoa: r.pecas for r in progresso_por_pessoa(lancs)}["ana"] == 11
    assert progresso_por_pessoa([]) == ()


def test_tela_de_pessoas_mostra_numeros_do_servidor(client, app, tenants):
    a, _ = tenants
    op = app.test_client()
    login(op, app, a.operator_email)
    post(op, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 4, "version": 1})
    assert op.get(f"/app/projetos/{a.project_id}/pessoas").status_code == 403  # operador não vê
    assert "Pessoas · 7 dias" not in op.get(f"/app/projetos/{a.project_id}").get_data(as_text=True)
    login(client, app, a.supervisor_email)
    _assign(client, app, a.activity_id, a.operator_id)
    for period in ("7", "30", "90", "tudo", "invalido"):
        response = client.get(f"/app/projetos/{a.project_id}/pessoas?periodo={period}")
        assert response.status_code == 200
        page = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", response.get_data(as_text=True)))
        assert "operator A" in page and "Atividade 1 +4" in page and "0 de 1 concluída" in page
    detail = text_of(client.get(f"/app/projetos/{a.project_id}"))
    assert "Pessoas · 7 dias" in detail and "Ver progresso por pessoa" in detail
