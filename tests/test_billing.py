"""Fase 8 — assinatura e pagamento com FakeProvider (sem rede).

Cenários do roadmap: aprovado, recusado, vencido, pago com atraso, cancelado, reembolso,
webhook com token inválido (401), duplicado (200 sem efeito), fora de ordem; CPF/CNPJ
inválido no formulário e no serviço; troca de plano muda limites na requisição seguinte;
só o proprietário gerencia a cobrança.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models import AuditLog, Company, Payment, Project, Subscription, WebhookEvent
from app.models.billing import SUB_ACTIVE, SUB_CANCELED, SUB_EXPIRED, SUB_PAST_DUE, SUB_TRIALING
from app.services import entitlements
from app.services.billing import documents
from app.services.billing import service as billing
from app.services.billing.fake import INVOICE_BASE, FakeProvider, add_months
from tests.conftest import login, make_tenant, post, text_of

WEBHOOK_TOKEN = "token-do-webhook-de-teste-123"
VALID_CNPJ = "11.222.333/0001-81"
VALID_CPF = "529.982.247-25"
NEW_PROJECT = {"name": "Lote novo", "quantity": 4, "people": 1, "hours_per_day": "8",
               "stages-0-name": "Etapa", "stages-0-activities": "Corte; 10"}


# ---------------------------------------------------------------- fixtures e helpers


@pytest.fixture()
def bapp(app_factory):
    return app_factory({"ASAAS_WEBHOOK_TOKEN": WEBHOOK_TOKEN, "BILLING_PROVIDER": "fake"})


@pytest.fixture()
def bclient(bapp):
    return bapp.test_client()


@pytest.fixture()
def btenants(bapp):
    with bapp.app_context():
        return make_tenant("A"), make_tenant("B")


def fake(app) -> FakeProvider:
    with app.app_context():
        provider = billing.get_provider(app)
    assert isinstance(provider, FakeProvider)
    return provider


def hook(client, payload, token=WEBHOOK_TOKEN):
    headers = {"asaas-access-token": token} if token is not None else {}
    return client.post("/webhooks/asaas", json=payload, headers=headers)


def sub_state(app, company_id) -> dict:
    with app.app_context():
        sub = db.session.execute(select(Subscription).where(Subscription.company_id == company_id)).scalar_one()
        return {
            "status": sub.status,
            "plan": sub.plan.code,
            "pending_plan": sub.pending_plan.code if sub.pending_plan else None,
            "provider_subscription_id": sub.provider_subscription_id,
            "provider_customer_id": sub.provider_customer_id,
            "current_period_end": billing._aware(sub.current_period_end),
            "grace_until": billing._aware(sub.grace_until),
            "trial_ends_at": billing._aware(sub.trial_ends_at),
            "canceled_at": sub.canceled_at,
        }


def payments(app, company_id) -> list[Payment]:
    with app.app_context():
        rows = db.session.execute(select(Payment).where(Payment.company_id == company_id).order_by(Payment.due_date)).scalars().all()
        db.session.expunge_all()
        return rows


def subscribe(client, app, tenant, plan="profissional", doc=VALID_CNPJ):
    login(client, app, tenant.owner_email)
    return post(client, app, "/app/assinatura/cobranca",
                {"plan": plan, "name": "Empresa Teste Ltda", "cpf_cnpj": doc, "email": "financeiro@exemplo.com"})


def pay(client, app, tenant, event="PAYMENT_CONFIRMED", status="confirmed", paid_on=None, payment_id=None):
    """Muda o status no provedor fake e manda o webhook correspondente."""
    provider = fake(app)
    sid = sub_state(app, tenant.company_id)["provider_subscription_id"]
    pid = payment_id or provider.payments_of(sid)[0]
    provider.set_payment_status(pid, status, paid_on)
    response = hook(client, provider.webhook(event, payment_id=pid))
    assert response.status_code == 200, response.get_data(as_text=True)
    return pid


def notices(app) -> list:
    from app.services import email
    from app.services.billing.notify import PAST_DUE_SUBJECT

    with app.app_context():
        return [m for m in email.outbox(app) if m.subject == PAST_DUE_SUBJECT]


def is_read_only(app, company_id, now=None) -> bool:
    with app.app_context():
        return entitlements.is_read_only(db.session.get(Company, company_id), now)


# ---------------------------------------------------------------- CPF / CNPJ


@pytest.mark.parametrize("value", [VALID_CNPJ, "11222333000181", VALID_CPF, "52998224725"])
def test_documentos_validos(value):
    assert documents.is_valid_document(value)


@pytest.mark.parametrize("value", ["11.222.333/0001-82", "529.982.247-26", "111.111.111-11", "00000000000000", "123", "", None])
def test_documentos_invalidos(value):
    assert not documents.is_valid_document(value)


def test_cnpj_invalido_recusado_no_formulario_sem_chamar_provedor(bclient, bapp, btenants):
    a, _ = btenants
    response = subscribe(bclient, bapp, a, doc="11.222.333/0001-80")
    assert response.status_code == 400
    assert "CPF ou CNPJ inválido" in text_of(response)
    assert fake(bapp).store.calls == []
    with bapp.app_context():
        assert db.session.query(Subscription).filter(Subscription.provider_customer_id.isnot(None)).count() == 0


def test_cpf_invalido_recusado_no_servico(bapp, btenants):
    a, _ = btenants
    with bapp.app_context():
        company = db.session.get(Company, a.company_id)
        from app.services.plans import get_plan

        with pytest.raises(billing.BillingError, match="CPF ou CNPJ inválido"):
            billing.subscribe(company, get_plan("essencial"), billing.BillingInfo("X Ltda", "529.982.247-00", "a@b.com"), None)
    assert fake(bapp).store.calls == []


# ---------------------------------------------------------------- teste grátis e assinatura


def test_teste_gratis_de_14_dias_sem_cartao(bclient, bapp, btenants):
    a, _ = btenants
    login(bclient, bapp, a.owner_email)
    page = text_of(bclient.get("/app/projetos"))
    assert "Teste grátis: faltam 14 dias" in page and "Escolher plano" in page
    overview = text_of(bclient.get("/app/assinatura"))
    assert "Teste grátis" in overview and "Plano Profissional" in overview
    state = sub_state(bapp, a.company_id)
    assert state["status"] == SUB_TRIALING
    assert timedelta(days=13, hours=23) < state["trial_ends_at"] - datetime.now(timezone.utc) <= timedelta(days=14)
    assert state["provider_customer_id"] is None  # nada no provedor sem escolher plano


def test_assinar_leva_ao_checkout_do_asaas(bclient, bapp, btenants):
    a, _ = btenants
    response = subscribe(bclient, bapp, a, plan="essencial")
    assert response.status_code == 303
    assert response.headers["Location"] == INVOICE_BASE + "pay_fake_0001"
    state = sub_state(bapp, a.company_id)
    assert state["status"] == SUB_TRIALING and state["plan"] == "essencial"
    assert state["provider_customer_id"] == "cus_fake_0001" and state["provider_subscription_id"] == "sub_fake_0001"
    customer = fake(bapp).store.customers["cus_fake_0001"]
    assert customer.cpf_cnpj == "11222333000181" and customer.external_reference == str(a.company_id)
    [p] = payments(bapp, a.company_id)
    assert p.status == "pending" and p.value_cents == 14900 and p.invoice_url.startswith(INVOICE_BASE)
    # 1ª cobrança vence no fim do teste grátis
    assert p.due_date == billing.local_date(state["trial_ends_at"])
    with bapp.app_context():
        assert db.session.query(AuditLog).filter_by(company_id=a.company_id, action=billing.SUBSCRIBED).count() == 1
    # já assinou: a faixa de teste some; a tela mostra a fatura em aberto
    assert "Teste grátis: faltam" not in text_of(bclient.get("/app/projetos"))
    assert "Pagar fatura" in text_of(bclient.get("/app/assinatura"))


def test_checkout_so_redireciona_para_host_conhecido(bclient, bapp, btenants):
    a, _ = btenants
    bapp.config["BILLING_CHECKOUT_HOSTS"] = ("www.asaas.com",)
    response = subscribe(bclient, bapp, a)
    assert response.status_code == 303
    assert response.headers["Location"].endswith("/app/assinatura/faturas")


def test_erro_do_provedor_aparece_na_tela_e_nao_assina(bclient, bapp, btenants):
    a, _ = btenants
    fake(bapp).store.fail_next = "O CPF/CNPJ informado é inválido."
    response = subscribe(bclient, bapp, a)
    assert response.status_code == 400
    assert "O CPF/CNPJ informado é inválido." in text_of(response)
    with bapp.app_context():
        assert db.session.query(Subscription).filter(Subscription.provider_subscription_id.isnot(None)).count() == 0


# ---------------------------------------------------------------- webhook: cenários


def test_pagamento_aprovado_ativa_e_estende_periodo(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a)
    pid = pay(bclient, bapp, a)
    state = sub_state(bapp, a.company_id)
    [p] = payments(bapp, a.company_id)
    assert state["status"] == SUB_ACTIVE and p.status == "confirmed" and p.paid_at is not None
    assert state["current_period_end"] == billing.end_of_day(add_months(p.due_date, 1))
    # PAYMENT_RECEIVED (saldo disponível) depois do CONFIRMED: segue ativa, sem regressão
    pay(bclient, bapp, a, event="PAYMENT_RECEIVED", status="received", payment_id=pid)
    assert sub_state(bapp, a.company_id)["status"] == SUB_ACTIVE
    # próxima mensalidade paga estende o período
    provider = fake(bapp)
    pid2 = provider.add_payment(state["provider_subscription_id"])
    pay(bclient, bapp, a, payment_id=pid2)
    assert sub_state(bapp, a.company_id)["current_period_end"] == billing.end_of_day(add_months(p.due_date, 2))
    assert "Ativa" in text_of(bclient.get("/app/assinatura"))


def test_cartao_recusado_nao_ativa(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a)
    provider = fake(bapp)
    pid = provider.payments_of("sub_fake_0001")[0]
    response = hook(bclient, provider.webhook("PAYMENT_CREDIT_CARD_CAPTURE_REFUSED", payment_id=pid))
    assert response.status_code == 200
    assert sub_state(bapp, a.company_id)["status"] == SUB_TRIALING
    assert payments(bapp, a.company_id)[0].status == "pending"
    with bapp.app_context():
        assert db.session.query(WebhookEvent).one().status == "processed"


def test_vencido_entra_em_carencia_avisa_e_depois_modo_leitura(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a)
    pay(bclient, bapp, a, event="PAYMENT_OVERDUE", status="overdue")
    state = sub_state(bapp, a.company_id)
    [p] = payments(bapp, a.company_id)
    assert state["status"] == SUB_PAST_DUE
    assert state["grace_until"] == billing.end_of_day(p.due_date) + timedelta(days=7)
    sent = notices(bapp)
    assert [n.to for n in sent] == [a.owner_email]
    assert "modo leitura" in sent[0].text and "Nenhum dado é apagado" in sent[0].text
    assert "/app/assinatura" in sent[0].text
    # durante a carência: escreve normalmente e vê a faixa
    assert not is_read_only(bapp, a.company_id)
    operator = bapp.test_client()
    login(operator, bapp, a.operator_email)
    page = text_of(operator.get("/app/projetos"))
    assert "Pagamento em atraso." in page and "Fale com o proprietário" in page
    # depois da carência (reconciliação diária): modo leitura, nada apagado
    after = state["grace_until"] + timedelta(minutes=1)
    with bapp.app_context():
        billing.reconcile_all(now=after)
    assert sub_state(bapp, a.company_id)["status"] == SUB_EXPIRED
    assert is_read_only(bapp, a.company_id)
    login(bclient, bapp, a.owner_email)
    assert post(bclient, bapp, "/app/projetos/novo", NEW_PROJECT).status_code == 402
    assert bclient.get(f"/app/projetos/{a.project_id}").status_code == 200
    assert bclient.get("/app/assinatura").status_code == 200  # dá para regularizar
    with bapp.app_context():
        assert db.session.query(Project).filter_by(company_id=a.company_id).count() == 1


def test_pago_com_atraso_volta_a_ativa(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a)
    pid = pay(bclient, bapp, a, event="PAYMENT_OVERDUE", status="overdue")
    assert sub_state(bapp, a.company_id)["status"] == SUB_PAST_DUE
    pay(bclient, bapp, a, event="PAYMENT_RECEIVED", status="received", payment_id=pid)
    state = sub_state(bapp, a.company_id)
    assert state["status"] == SUB_ACTIVE and state["grace_until"] is None
    assert payments(bapp, a.company_id)[0].status == "received"


def test_cancelar_vale_ate_o_fim_do_periodo_pago(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a)
    pay(bclient, bapp, a)
    period_end = sub_state(bapp, a.company_id)["current_period_end"]
    login(bclient, bapp, a.owner_email)
    assert 'id="cancelar"' in bclient.get("/app/assinatura").get_data(as_text=True)  # modal de confirmação
    assert bclient.post("/app/assinatura/cancelar").status_code == 400  # sem CSRF
    response = post(bclient, bapp, "/app/assinatura/cancelar", follow_redirects=True)
    assert "Acesso completo até" in text_of(response)
    state = sub_state(bapp, a.company_id)
    assert state["status"] == SUB_CANCELED and state["current_period_end"] == period_end and state["canceled_at"]
    assert fake(bapp).store.subscriptions["sub_fake_0001"]["active"] is False
    assert not is_read_only(bapp, a.company_id)
    assert post(bclient, bapp, "/app/projetos/novo", NEW_PROJECT).status_code == 303
    # eco do Asaas (SUBSCRIPTION_DELETED) não muda nada
    assert hook(bclient, fake(bapp).webhook("SUBSCRIPTION_DELETED", subscription_id="sub_fake_0001")).status_code == 200
    assert sub_state(bapp, a.company_id)["status"] == SUB_CANCELED
    # passado o período: modo leitura
    with bapp.app_context():
        billing.reconcile_all(now=period_end + timedelta(seconds=1))
    assert sub_state(bapp, a.company_id)["status"] == SUB_EXPIRED
    assert is_read_only(bapp, a.company_id)


def test_cancelamento_pelo_painel_do_asaas_chega_por_webhook(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a)
    pay(bclient, bapp, a)
    provider = fake(bapp)
    provider.cancel("sub_fake_0001")
    hook(bclient, provider.webhook("SUBSCRIPTION_DELETED", subscription_id="sub_fake_0001"))
    assert sub_state(bapp, a.company_id)["status"] == SUB_CANCELED


def test_reembolso_tira_o_acesso_do_periodo(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a)
    pid = pay(bclient, bapp, a)
    assert sub_state(bapp, a.company_id)["status"] == SUB_ACTIVE
    pay(bclient, bapp, a, event="PAYMENT_REFUNDED", status="refunded", payment_id=pid)
    state = sub_state(bapp, a.company_id)
    assert state["status"] == SUB_EXPIRED and state["current_period_end"] is None
    assert payments(bapp, a.company_id)[0].status == "refunded"
    assert is_read_only(bapp, a.company_id)
    login(bclient, bapp, a.owner_email)
    assert "Estornada" in text_of(bclient.get("/app/assinatura/faturas"))


def test_assinar_de_novo_depois_de_encerrada(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a)
    pid = pay(bclient, bapp, a)
    pay(bclient, bapp, a, event="PAYMENT_REFUNDED", status="refunded", payment_id=pid)
    response = subscribe(bclient, bapp, a, plan="essencial")
    assert response.status_code == 303 and response.headers["Location"].startswith(INVOICE_BASE)
    state = sub_state(bapp, a.company_id)
    assert state["provider_subscription_id"] == "sub_fake_0002" and state["provider_customer_id"] == "cus_fake_0001"
    new_pid = fake(bapp).payments_of("sub_fake_0002")[0]
    pay(bclient, bapp, a, payment_id=new_pid)
    assert sub_state(bapp, a.company_id)["status"] == SUB_ACTIVE


# ---------------------------------------------------------------- webhook: segurança e idempotência


@pytest.mark.parametrize("token", [None, "", "errado", WEBHOOK_TOKEN + "x"])
def test_webhook_com_token_invalido_responde_401(bclient, bapp, btenants, token):
    a, _ = btenants
    subscribe(bclient, bapp, a)
    provider = fake(bapp)
    pid = provider.payments_of("sub_fake_0001")[0]
    provider.set_payment_status(pid, "confirmed")
    response = hook(bclient, provider.webhook("PAYMENT_CONFIRMED", payment_id=pid), token=token)
    assert response.status_code == 401
    with bapp.app_context():
        assert db.session.query(WebhookEvent).count() == 0
    assert sub_state(bapp, a.company_id)["status"] == SUB_TRIALING


def test_webhook_sem_token_configurado_recusa_tudo(app_factory):
    app = app_factory({"ASAAS_WEBHOOK_TOKEN": None, "BILLING_PROVIDER": "fake"})
    response = app.test_client().post("/webhooks/asaas", json={"id": "evt_1", "event": "PAYMENT_CONFIRMED"},
                                      headers={"asaas-access-token": ""})
    assert response.status_code == 401


def test_webhook_isento_de_csrf_e_payload_invalido_400(bclient, bapp):
    assert hook(bclient, {"event": "PAYMENT_CONFIRMED"}).status_code == 400
    response = bclient.post("/webhooks/asaas", data="nao-json", headers={"asaas-access-token": WEBHOOK_TOKEN})
    assert response.status_code == 400


def test_webhook_duplicado_responde_200_sem_efeito(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a)
    provider = fake(bapp)
    pid = provider.payments_of("sub_fake_0001")[0]
    provider.set_payment_status(pid, "overdue")
    payload = provider.webhook("PAYMENT_OVERDUE", payment_id=pid)
    assert hook(bclient, payload).get_json() == {"status": "processed"}
    before = sub_state(bapp, a.company_id)
    sent = len(notices(bapp))
    # mesmo id de evento de novo (entrega "pelo menos uma vez"), até com conteúdo diferente
    provider.set_payment_status(pid, "confirmed")
    replay = dict(payload, payment=dict(payload["payment"], status="CONFIRMED"))
    response = hook(bclient, replay)
    assert response.status_code == 200 and response.get_json() == {"status": "duplicate"}
    assert sub_state(bapp, a.company_id) == before
    assert len(notices(bapp)) == sent  # sem 2º e-mail
    with bapp.app_context():
        assert db.session.query(WebhookEvent).filter_by(external_event_id=payload["id"]).count() == 1


def test_evento_fora_de_ordem_consulta_o_provedor(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a)
    provider = fake(bapp)
    pid = provider.payments_of("sub_fake_0001")[0]
    provider.set_payment_status(pid, "overdue")
    stale = provider.webhook("PAYMENT_OVERDUE", payment_id=pid)  # gerado antes, chega depois
    provider.set_payment_status(pid, "received")
    hook(bclient, provider.webhook("PAYMENT_RECEIVED", payment_id=pid))
    assert sub_state(bapp, a.company_id)["status"] == SUB_ACTIVE
    provider.store.calls.clear()
    assert hook(bclient, stale).status_code == 200
    assert "list_payments" in provider.store.calls  # em dúvida, perguntou ao Asaas
    assert payments(bapp, a.company_id)[0].status == "received"
    assert sub_state(bapp, a.company_id)["status"] == SUB_ACTIVE
    assert notices(bapp) == []


def test_evento_de_pagamento_antes_da_criacao_local(bclient, bapp, btenants):
    """CONFIRMED chega antes do CREATED: a cobrança é criada já paga; o CREATED atrasado
    não faz a assinatura voltar."""
    a, _ = btenants
    subscribe(bclient, bapp, a)
    provider = fake(bapp)
    pid2 = provider.add_payment("sub_fake_0001")
    created = provider.webhook("PAYMENT_CREATED", payment_id=pid2)
    provider.set_payment_status(pid2, "confirmed")
    hook(bclient, provider.webhook("PAYMENT_CONFIRMED", payment_id=pid2))
    hook(bclient, created)
    assert {p.provider_payment_id: p.status for p in payments(bapp, a.company_id)}[pid2] == "confirmed"
    assert sub_state(bapp, a.company_id)["status"] == SUB_ACTIVE


def test_erro_no_processamento_fica_registrado_e_responde_200(bclient, bapp, btenants, monkeypatch):
    a, _ = btenants
    subscribe(bclient, bapp, a)

    def boom(payload, now=None):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(billing, "handle_webhook", boom)
    response = hook(bclient, {"id": "evt_x", "event": "PAYMENT_CONFIRMED", "payment": {"id": "pay_x"}})
    assert response.status_code == 200 and response.get_json() == {"status": "failed"}
    with bapp.app_context():
        event = db.session.query(WebhookEvent).one()
        assert event.status == "failed" and event.error.startswith("RuntimeError")


def test_evento_de_assinatura_desconhecida_e_ignorado(bclient, bapp):
    payload = {"id": "evt_y", "event": "PAYMENT_CONFIRMED",
               "payment": {"id": "pay_y", "subscription": "sub_de_ninguem", "status": "CONFIRMED", "value": 10, "dueDate": "2026-10-01"}}
    assert hook(bclient, payload).get_json() == {"status": "ignored"}


# ---------------------------------------------------------------- trocar plano


def test_rebaixar_vale_no_fim_do_periodo_pago(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a, plan="profissional")
    pay(bclient, bapp, a)
    login(bclient, bapp, a.owner_email)
    for _ in range(2):
        assert post(bclient, bapp, "/app/projetos/novo", NEW_PROJECT).status_code == 303  # 3 ativos
    page = text_of(bclient.get("/app/assinatura/planos/essencial"))
    assert "R$ 349,00/mês" in page and "R$ 149,00/mês" in page and "−R$ 200,00" in page
    period_end = sub_state(bapp, a.company_id)["current_period_end"]
    assert "Vale a partir de" in page
    response = post(bclient, bapp, "/app/assinatura/planos/essencial", follow_redirects=True)
    assert "agendada: vale a partir de" in text_of(response)
    state = sub_state(bapp, a.company_id)
    assert state["plan"] == "profissional" and state["pending_plan"] == "essencial"
    assert fake(bapp).store.subscriptions["sub_fake_0001"]["value_cents"] == 14900  # próxima fatura
    # até o fim do período pago, limites do Profissional
    assert not is_read_only(bapp, a.company_id)
    with bapp.app_context():
        billing.reconcile_all(now=period_end - timedelta(minutes=1))
    assert sub_state(bapp, a.company_id)["plan"] == "profissional"
    with bapp.app_context():
        billing.reconcile_all(now=period_end + timedelta(seconds=1))
    assert sub_state(bapp, a.company_id)["plan"] == "essencial"
    # requisição seguinte: limite do Essencial (3 projetos)
    response = post(bclient, bapp, "/app/projetos/novo", NEW_PROJECT)
    assert response.status_code == 402 and "Essencial permite 3 projetos ativos" in text_of(response)


def test_upgrade_so_vale_com_a_fatura_no_valor_novo_paga(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a, plan="essencial")
    pay(bclient, bapp, a)
    login(bclient, bapp, a.owner_email)
    for _ in range(2):
        assert post(bclient, bapp, "/app/projetos/novo", NEW_PROJECT).status_code == 303  # 3 ativos
    provider = fake(bapp)
    next_pid = provider.add_payment("sub_fake_0001")  # próxima mensalidade já gerada pelo Asaas
    assert "Vale após o pagamento" in text_of(bclient.get("/app/assinatura/planos/profissional"))
    response = post(bclient, bapp, "/app/assinatura/planos/profissional", follow_redirects=True)
    assert "valem assim que a fatura no valor novo for paga" in text_of(response)
    state = sub_state(bapp, a.company_id)
    assert state["plan"] == "essencial" and state["pending_plan"] == "profissional"
    assert provider.store.payments[next_pid]["value_cents"] == 34900
    # sem pagar: limites continuam os do Essencial (nada de upgrade grátis)
    assert post(bclient, bapp, "/app/projetos/novo", NEW_PROJECT).status_code == 402
    # paga a fatura no valor novo → limites sobem na requisição seguinte
    pay(bclient, bapp, a, payment_id=next_pid)
    state = sub_state(bapp, a.company_id)
    assert state["plan"] == "profissional" and state["pending_plan"] is None
    assert post(bclient, bapp, "/app/projetos/novo", NEW_PROJECT).status_code == 303
    with bapp.app_context():
        changes = db.session.query(AuditLog).filter_by(company_id=a.company_id, action="subscription.plan_changed").count()
    assert changes == 1


def test_upgrade_pedido_e_cancelado_nao_libera_nada(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a, plan="essencial")
    pay(bclient, bapp, a)
    login(bclient, bapp, a.owner_email)
    post(bclient, bapp, "/app/assinatura/planos/empresa")
    assert post(bclient, bapp, "/app/assinatura/cancelar").status_code == 303
    state = sub_state(bapp, a.company_id)
    assert state["plan"] == "essencial" and state["pending_plan"] is None and state["status"] == SUB_CANCELED


def test_troca_de_plano_bloqueada_em_atraso(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a, plan="essencial")
    pay(bclient, bapp, a, event="PAYMENT_OVERDUE", status="overdue")
    assert "Troca de plano indisponível" in text_of(bclient.get("/app/assinatura/planos/empresa"))
    response = post(bclient, bapp, "/app/assinatura/planos/empresa")
    assert response.status_code == 400 and "Pagamento em atraso" in text_of(response)
    state = sub_state(bapp, a.company_id)
    assert state["plan"] == "essencial" and state["pending_plan"] is None
    assert fake(bapp).store.subscriptions["sub_fake_0001"]["value_cents"] == 14900


def test_falha_do_provedor_ao_criar_assinatura_nao_muda_estado_local(bclient, bapp, btenants):
    a, _ = btenants
    before = sub_state(bapp, a.company_id) if _has_sub(bapp, a.company_id) else None
    provider = fake(bapp)
    provider.store.fail_on["create_subscription"] = "Falha simulada no Asaas."
    response = subscribe(bclient, bapp, a, plan="empresa")
    assert response.status_code == 400 and "Falha simulada no Asaas." in text_of(response)
    state = sub_state(bapp, a.company_id)
    assert state["status"] == SUB_TRIALING and state["plan"] == "profissional" and state["pending_plan"] is None
    assert state["provider_subscription_id"] is None
    assert state["provider_customer_id"] == "cus_fake_0001"  # só o cliente foi guardado
    if before is not None:
        assert state["trial_ends_at"] == before["trial_ends_at"]
    with bapp.app_context():
        assert db.session.query(AuditLog).filter_by(company_id=a.company_id, action=billing.SUBSCRIBED).count() == 0
        assert db.session.query(Payment).count() == 0
    # nova tentativa: reaproveita o cliente (sem duplicar) e o upgrade espera o pagamento
    del provider.store.fail_on["create_subscription"]
    assert subscribe(bclient, bapp, a, plan="empresa").status_code == 303
    assert provider.store.calls.count("create_customer") == 1 and "update_customer" in provider.store.calls
    state = sub_state(bapp, a.company_id)
    assert state["plan"] == "profissional" and state["pending_plan"] == "empresa"
    pay(bclient, bapp, a)
    assert sub_state(bapp, a.company_id)["plan"] == "empresa"


def test_falha_do_provedor_ao_listar_cobrancas_tambem_nao_muda_nada(bclient, bapp, btenants):
    a, _ = btenants
    fake(bapp).store.fail_on["list_payments"] = "Asaas fora do ar."
    # list_payments do fake não passa por _maybe_fail: simula pela troca do método
    provider = fake(bapp)
    original = provider.list_payments

    def failing(subscription_id):
        raise billing.PaymentProviderError("Asaas fora do ar.", status=503)

    provider.list_payments = failing
    try:
        response = subscribe(bclient, bapp, a, plan="essencial")
    finally:
        provider.list_payments = original
        provider.store.fail_on.clear()
    assert response.status_code == 400
    state = sub_state(bapp, a.company_id)
    assert state["plan"] == "profissional" and state["provider_subscription_id"] is None


def _has_sub(app, company_id) -> bool:
    with app.app_context():
        return db.session.query(Subscription).filter_by(company_id=company_id).count() == 1


def test_rebaixar_plano_com_uso_acima_do_limite_e_recusado(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a, plan="profissional")
    pay(bclient, bapp, a)
    login(bclient, bapp, a.owner_email)
    for _ in range(3):
        post(bclient, bapp, "/app/projetos/novo", NEW_PROJECT)
    response = post(bclient, bapp, "/app/assinatura/planos/essencial")
    assert response.status_code == 400 and "você tem 4" in text_of(response)
    assert sub_state(bapp, a.company_id)["plan"] == "profissional"


def test_escolher_plano_sem_assinatura_vai_para_dados_de_cobranca(bclient, bapp, btenants):
    a, _ = btenants
    login(bclient, bapp, a.owner_email)
    page = text_of(bclient.get("/app/assinatura/planos"))
    assert "Assinar Essencial" in page and "Assinar Empresa" in page
    response = bclient.get("/app/assinatura/planos/empresa")
    assert response.status_code == 302 and response.headers["Location"].endswith("/app/assinatura/cobranca?plano=empresa")
    assert "Plano Empresa · R$ 799,00/mês" in text_of(bclient.get("/app/assinatura/cobranca?plano=empresa"))
    assert bclient.get("/app/assinatura/planos/inexistente").status_code == 404


def test_atualizar_dados_de_cobranca(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a)
    response = post(bclient, bapp, "/app/assinatura/cobranca",
                    {"name": "Nova Razão Ltda", "cpf_cnpj": VALID_CPF, "email": "novo@exemplo.com"})
    assert response.status_code == 303
    customer = fake(bapp).store.customers["cus_fake_0001"]
    assert customer.name == "Nova Razão Ltda" and customer.cpf_cnpj == "52998224725"
    bad = post(bclient, bapp, "/app/assinatura/cobranca", {"name": "X Ltda", "cpf_cnpj": "123.456.789-00", "email": "a@b.com"})
    assert bad.status_code == 400


# ---------------------------------------------------------------- papéis


BILLING_GETS = ["/app/assinatura", "/app/assinatura/planos", "/app/assinatura/planos/essencial",
                "/app/assinatura/cobranca", "/app/assinatura/faturas"]
BILLING_POSTS = ["/app/assinatura/cancelar", "/app/assinatura/cobranca", "/app/assinatura/planos/essencial"]


@pytest.mark.parametrize("role", ["supervisor", "operator"])
def test_so_proprietario_gerencia_cobranca(bclient, bapp, btenants, role):
    a, _ = btenants
    login(bclient, bapp, getattr(a, f"{role}_email"))
    for url in BILLING_GETS:
        assert bclient.get(url).status_code == 403, url
    for url in BILLING_POSTS:
        assert post(bclient, bapp, url, {"plan": "essencial", "name": "X Ltda", "cpf_cnpj": VALID_CNPJ, "email": "a@b.com"}).status_code == 403, url
    nav = bclient.get("/app/projetos").get_data(as_text=True)
    assert "/app/assinatura" not in nav  # sem item de menu nem botão na faixa


def test_rotas_de_cobranca_exigem_login(bclient):
    response = bclient.get("/app/assinatura")
    assert response.status_code == 302 and "/entrar" in response.headers["Location"]
