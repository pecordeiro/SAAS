"""Etapa F — alertas automáticos: regra pura (calc), gravação com dedupe por chave + dia,
e-mail-resumo por preferência, tela /app/alertas, X configurável por empresa e /conta."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from app.extensions import db
from app.models import Alert, Company, Membership, Project, ProgressEntry, Stage, User
from app.services import alerts, calc, email, worker
from tests.conftest import login, make_tenant, post, text_of

D = date(2026, 10, 14)  # quarta-feira
ANDAMENTO = calc.STATUS_EM_ANDAMENTO


# ================================================================ regra pura (calc)


def _tipos(saida):
    return [(a.tipo, a.severidade) for a in saida]


def test_projeto_concluido_nao_gera_alerta():
    etapa = calc.EtapaAlerta(id="e", status=ANDAMENTO, ultimo_registro=D - timedelta(days=30))
    assert calc.alertas_projeto(projeto="p", hoje=D, prazo=D - timedelta(days=9), previsao=D, concluido=True,
                                etapas=[etapa]) == ()


def test_atraso_previsto_em_dias_uteis():
    # prazo sexta 16/10, previsão terça 20/10 → 2 dias úteis de atraso (segunda e terça)
    saida = calc.alertas_projeto(projeto="p", hoje=D, prazo=date(2026, 10, 16), previsao=date(2026, 10, 20), concluido=False)
    assert _tipos(saida) == [(calc.ALERTA_ATRASO_PREVISTO, "danger")]
    assert saida[0].valores["atraso_du"] == 2 and saida[0].chave == "forecast_late:p"


@pytest.mark.parametrize(
    "previsao,esperado",
    [
        (date(2026, 10, 16), [(calc.ALERTA_PRAZO_EM_RISCO, "warning")]),  # folga 0
        (date(2026, 10, 15), [(calc.ALERTA_PRAZO_EM_RISCO, "warning")]),  # folga 1 dia útil
        (date(2026, 10, 14), []),  # folga 2 dias úteis: ok
    ],
)
def test_prazo_em_risco_pela_folga(previsao, esperado):
    saida = calc.alertas_projeto(projeto="p", hoje=D, prazo=date(2026, 10, 16), previsao=previsao, concluido=False)
    assert _tipos(saida) == esperado


def test_sem_previsao_prazo_vencido_e_prazo_perto():
    vencido = calc.alertas_projeto(projeto="p", hoje=D, prazo=date(2026, 10, 12), previsao=None, concluido=False)
    assert _tipos(vencido) == [(calc.ALERTA_PRAZO_EM_RISCO, "danger")] and vencido[0].valores["vencido_du"] == 2
    perto = calc.alertas_projeto(projeto="p", hoje=D, prazo=date(2026, 10, 21), previsao=None, concluido=False)
    assert _tipos(perto) == [(calc.ALERTA_PRAZO_EM_RISCO, "warning")] and perto[0].valores["ate_prazo_du"] == 5
    longe = calc.alertas_projeto(projeto="p", hoje=D, prazo=date(2026, 10, 22), previsao=None, concluido=False)
    assert longe == ()
    assert calc.alertas_projeto(projeto="p", hoje=D, prazo=None, previsao=None, concluido=False) == ()


def test_etapa_parada_conta_dias_uteis_e_respeita_o_limite():
    sexta = date(2026, 10, 9)  # sexta → quarta 14/10: seg, ter, qua = 3 dias úteis
    etapas = [
        calc.EtapaAlerta(id="parada", status=ANDAMENTO, ultimo_registro=sexta),
        calc.EtapaAlerta(id="recente", status=ANDAMENTO, ultimo_registro=date(2026, 10, 12)),  # 2 d.u.
        calc.EtapaAlerta(id="nao-iniciada", status=calc.STATUS_NAO_INICIADA, ultimo_registro=None),
        calc.EtapaAlerta(id="concluida", status=calc.STATUS_CONCLUIDA, ultimo_registro=sexta),
        calc.EtapaAlerta(id="peca", status=ANDAMENTO, ultimo_registro=sexta, aguardando_peca=True),
    ]
    saida = calc.alertas_projeto(projeto="p", hoje=D, prazo=None, previsao=None, concluido=False, etapas=etapas)
    assert [(a.tipo, a.etapa, a.valores["parada_du"]) for a in saida] == [(calc.ALERTA_ETAPA_PARADA, "parada", 3)]
    # Limite configurável: com 4 dias, ninguém está parado ainda; feriado na segunda também tira 1 dia.
    assert calc.alertas_projeto(projeto="p", hoje=D, prazo=None, previsao=None, concluido=False, etapas=etapas,
                                dias_parada=4) == ()
    assert calc.alertas_projeto(projeto="p", hoje=D, prazo=None, previsao=None, concluido=False, etapas=etapas[:1],
                                feriados=[date(2026, 10, 12)]) == ()


def test_peca_atrasada_so_quando_ninguem_atualizou_depois_da_previsao():
    base = dict(id="e", status=ANDAMENTO, aguardando_peca=True, peca_prevista=date(2026, 10, 12))
    atrasada = calc.alertas_projeto(projeto="p", hoje=D, prazo=None, previsao=None, concluido=False,
                                    etapas=[calc.EtapaAlerta(**base, peca_atualizada=date(2026, 10, 5))])
    assert _tipos(atrasada) == [(calc.ALERTA_PECA_ATRASADA, "warning")]
    assert atrasada[0].chave == "part_overdue:e:2026-10-12" and atrasada[0].valores["dias"] == 2
    atualizada = calc.EtapaAlerta(**base, peca_atualizada=date(2026, 10, 13))
    no_dia = calc.EtapaAlerta(**{**base, "peca_prevista": D})
    assert calc.alertas_projeto(projeto="p", hoje=D, prazo=None, previsao=None, concluido=False,
                                etapas=[atualizada, no_dia]) == ()


def test_dias_parada_validado():
    assert calc.dias_parada_valido(1) and calc.dias_parada_valido(60)
    for bad in (0, 61, -1, True, 3.0, "3", None):
        assert not calc.dias_parada_valido(bad)
    with pytest.raises(ValueError):
        calc.alertas_projeto(projeto="p", hoje=D, prazo=None, previsao=None, concluido=False, dias_parada=0)


# ================================================================ worker: gravação e e-mail

NOW = datetime(2026, 10, 14, 13, 0, tzinfo=timezone.utc)  # 10h em São Paulo


def _late_project(tenant, now=NOW):
    """Prazo ontem e atividade em andamento sem lançamento há 7 dias."""
    project = db.session.get(Project, tenant.project_id)
    project.due_date = date(2026, 10, 13)
    stage = db.session.get(Stage, tenant.stage_id)
    activity = stage.activities[0]
    activity.units_done = 2
    db.session.add(ProgressEntry(company_id=tenant.company_id, activity_id=activity.id, user_id=tenant.operator_id,
                                 delta=2, at=now - timedelta(days=7)))
    db.session.commit()


def _digests(app, to=None):
    return [m for m in email.outbox(app) if m.subject.startswith(alerts.DIGEST_SUBJECT) and (to is None or m.to == to)]


def test_worker_grava_alertas_com_dedupe_e_manda_resumo(app_factory):
    app = app_factory({"APP_BASE_URL": "https://app.exemplo.com.br"})
    with app.app_context():
        a, b = make_tenant("A"), make_tenant("B")
        _late_project(a)
        result = worker.run_task(worker.TASK_ALERTS, NOW)
        assert result["created"] == 2  # atraso previsto + etapa parada
        kinds = sorted(x.kind for x in db.session.query(Alert).filter_by(company_id=a.company_id))
        assert kinds == ["forecast_late", "stage_stalled"]
        assert db.session.query(Alert).filter_by(company_id=b.company_id).count() == 0
        # Mesmo dia de novo: nada duplicado, nenhum e-mail repetido.
        assert worker.run_task(worker.TASK_ALERTS, NOW + timedelta(hours=1))["created"] == 0
        assert db.session.query(Alert).filter_by(company_id=a.company_id).count() == 2
        sent = _digests(app)
        assert sorted(m.to for m in sent) == ["owner.a@exemplo.com", "supervisor.a@exemplo.com"]  # operador não
        body = sent[0].text
        assert "Atraso previsto" in body and "Etapa parada" in body and "Projeto A" in body
        assert f"https://app.exemplo.com.br/app/projetos/{a.project_id}" in body
        assert "https://app.exemplo.com.br/conta/perfil#notificacoes" in body
        assert "Projeto B" not in body and "operator" not in body


def test_dia_seguinte_cria_alerta_novo_mas_nao_repete_email_na_semana(app):
    with app.app_context():
        a = make_tenant("A")
        _late_project(a)
        worker.run_task(worker.TASK_ALERTS, NOW)
        first = len(_digests(app))
        worker.run_task(worker.TASK_ALERTS, NOW + timedelta(days=1))
        assert db.session.query(Alert).filter_by(company_id=a.company_id).count() == 4  # 2 por dia
        assert len(_digests(app)) == first
        worker.run_task(worker.TASK_ALERTS, NOW + timedelta(days=8))
        assert len(_digests(app)) == first * 2  # passou a janela de 7 dias


def test_antes_das_7h_grava_mas_so_envia_depois(app):
    with app.app_context():
        a = make_tenant("A")
        _late_project(a)
        early = datetime(2026, 10, 14, 8, 0, tzinfo=timezone.utc)  # 5h em São Paulo
        assert worker.run_task(worker.TASK_ALERTS, early)["emails"] == 0
        assert db.session.query(Alert).filter_by(company_id=a.company_id).count() == 2
        assert worker.run_task(worker.TASK_ALERTS, NOW)["emails"] == 2


def test_preferencia_desligada_nao_recebe(app):
    with app.app_context():
        a = make_tenant("A")
        _late_project(a)
        db.session.query(User).filter_by(email=a.supervisor_email).one().notify_alerts = False
        db.session.commit()
        worker.run_task(worker.TASK_ALERTS, NOW)
        assert [m.to for m in _digests(app)] == [a.owner_email]


def test_vinculo_desativado_ou_suporte_nao_recebe(app):
    with app.app_context():
        a = make_tenant("A")
        _late_project(a)
        sup = db.session.query(User).filter_by(email=a.supervisor_email).one()
        db.session.query(Membership).filter_by(user_id=sup.id).one().active = False
        db.session.commit()
        worker.run_task(worker.TASK_ALERTS, NOW)
        assert [m.to for m in _digests(app)] == [a.owner_email]


def test_peca_atrasada_vira_lembrete(app):
    with app.app_context():
        a = make_tenant("A")
        stage = db.session.get(Stage, a.stage_id)
        stage.waiting_part = True
        stage.part_expected_on = date(2026, 10, 12)
        stage.part_updated_at = datetime(2026, 10, 5, 12, tzinfo=timezone.utc)
        db.session.commit()
        worker.run_task(worker.TASK_ALERTS, NOW)
        alert = db.session.query(Alert).filter_by(company_id=a.company_id).one()
        assert alert.kind == "part_overdue" and alert.stage_id == a.stage_id
        assert "aguardando peça" in _digests(app)[0].text


def test_etapa_parada_usa_o_x_da_empresa(app):
    with app.app_context():
        a = make_tenant("A")
        _late_project(a)
        db.session.get(Company, a.company_id).stalled_days = 10
        db.session.commit()
        worker.run_task(worker.TASK_ALERTS, NOW)
        assert [x.kind for x in db.session.query(Alert).filter_by(company_id=a.company_id)] == ["forecast_late"]


# ================================================================ tela, empresa e preferências


def test_tela_de_alertas_so_supervisor_e_so_a_propria_empresa(client, app):
    with app.app_context():
        a, b = make_tenant("A"), make_tenant("B")
        _late_project(a)
        _late_project(b)
        worker.run_task(worker.TASK_ALERTS, datetime.now(timezone.utc))
    login(client, app, a.supervisor_email)
    page = text_of(client.get("/app/alertas"))
    assert "Projeto A" in page and "Atraso previsto" in page and "Projeto B" not in page
    assert "Alertas" in page
    op = app.test_client()
    login(op, app, a.operator_email)
    assert op.get("/app/alertas").status_code == 403


def test_tela_vazia(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    assert "Nenhum alerta" in text_of(client.get("/app/alertas"))


def test_x_da_etapa_parada_validado_no_servidor(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    base = {"name": "Empresa A", "daily_hours": "8", "workdays": ["0", "1", "2", "3", "4"]}
    for bad in ("0", "61", "abc", "-3"):
        assert post(client, app, "/app/empresa", {**base, "stalled_days": bad}).status_code == 400
    assert post(client, app, "/app/empresa", {**base, "stalled_days": "5"}).status_code == 303
    with app.app_context():
        assert db.session.get(Company, a.company_id).stalled_days == 5
    # Sem o campo: mantém o valor atual.
    assert post(client, app, "/app/empresa", base).status_code == 303
    with app.app_context():
        assert db.session.get(Company, a.company_id).stalled_days == 5
    sup = app.test_client()
    login(sup, app, a.supervisor_email)
    assert post(sup, app, "/app/empresa", {**base, "stalled_days": "9"}).status_code == 403


def test_servico_recusa_x_invalido_mesmo_sem_o_formulario(app, tenants):
    from app.services import company as company_svc

    a, _ = tenants
    with app.app_context():
        company = db.session.get(Company, a.company_id)
        with pytest.raises(company_svc.CompanyError):
            company_svc.update_company(company, name="A", cnpj=None, daily_hours=company.daily_hours,
                                       workdays=[0], user_id=None, stalled_days=0)


def test_preferencias_de_email_so_do_proprio_usuario(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    page = text_of(client.get("/conta/perfil"))
    assert "Notificações por e-mail" in page
    response = post(client, app, "/conta/perfil/notificacoes", {"notify_assignment": "y"})
    assert response.status_code == 303
    with app.app_context():
        sup = db.session.query(User).filter_by(email=a.supervisor_email).one()
        assert (sup.notify_assignment, sup.notify_alerts, sup.notify_weekly) == (True, False, False)
        owner = db.session.query(User).filter_by(email=a.owner_email).one()
        assert (owner.notify_assignment, owner.notify_alerts, owner.notify_weekly) == (True, True, True)
    # Sem CSRF → 400.
    assert client.post("/conta/perfil/notificacoes", data={"notify_alerts": "y"}).status_code == 400
