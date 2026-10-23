"""Etapa B — planos novos e cobrança.

Essencial (R$ 249,90; 5 projetos; 5 pessoas; teste), Profissional (R$ 497,90; 10; 25; teste),
Empresa (R$ 997,90; ilimitado; sem teste) e Implantação (sob orçamento; só `billing-admin
set-plan`). Tudo checado pelo servidor: limites pelas rotas (402), teste grátis só nos planos
1 e 2, plano 4 fora do autosserviço, preço e limite lidos da tabela ``plans``.
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app import create_app
from app.extensions import db
from app.models import AuditLog, Company, DomainEvent, Invitation, Plan, Subscription
from app.models.billing import SUB_ACTIVE, SUB_TRIALING
from app.services import entitlements, events
from app.services import plans as catalog
from app.services import projects as svc
from app.services.billing import service as billing
from tests.conftest import login, make_tenant, post, text_of
from tests.test_billing import (  # noqa: F401 (fixtures)
    NEW_PROJECT,
    bapp,
    bclient,
    btenants,
    fake,
    pay,
    payments,
    sub_state,
    subscribe,
)


def run(app, *args):
    return app.test_cli_runner().invoke(args=list(args))


def _set_sub(app, company_id, code, status="active", **kw):
    with app.app_context():
        plan_id = catalog.get_plan(code).id
        sub = db.session.execute(select(Subscription).where(Subscription.company_id == company_id)).scalar_one_or_none()
        if sub is None:
            sub = Subscription(company_id=company_id, provider="fake", plan_id=plan_id)
            db.session.add(sub)
        sub.plan_id = plan_id
        sub.status = status
        for key, value in kw.items():
            setattr(sub, key, value)
        db.session.commit()


def _add_projects(app, company_id, n):
    with app.app_context():
        company = db.session.get(Company, company_id)
        for i in range(n):
            svc.create_project(company, name=f"Extra {i}", quantity=1, start_date=None, due_date=None, people=1,
                               hours_per_day=Decimal("8"), stages=[])
        db.session.commit()


def _add_invites(app, company_id, n):
    with app.app_context():
        for i in range(n):
            db.session.add(Invitation(company_id=company_id, email=f"conv{i}@x.com", role="operator",
                                      token_hash=f"{i:064d}", expires_at=billing.now_utc() + timedelta(days=3)))
        db.session.commit()


def _plan_code(app, company_id) -> str:
    """Plano efetivo (com ou sem assinatura gravada)."""
    with app.app_context():
        return entitlements.effective_plan(db.session.get(Company, company_id)).code


def _audit(app, company_id, action):
    with app.app_context():
        return db.session.execute(
            select(AuditLog).where(AuditLog.company_id == company_id, AuditLog.action == action)
        ).scalars().all()


def _events(app, company_id, kind):
    with app.app_context():
        return db.session.execute(
            select(DomainEvent).where(DomainEvent.company_id == company_id, DomainEvent.type == kind)
        ).scalars().all()


# ---------------------------------------------------------------- catálogo


def test_catalogo_quatro_planos_ordem_e_regras(app):
    with app.app_context():
        plans = catalog.active_plans()
        assert [p.code for p in plans] == ["essencial", "profissional", "empresa", "implantacao"]
        by = {p.code: p for p in plans}
        assert [catalog.has_trial(p) for p in plans] == [True, True, False, False]
        assert [catalog.is_self_service(p) for p in plans] == [True, True, True, False]
        assert by["implantacao"].price_cents is None and catalog.is_managed(by["implantacao"])
        assert by["implantacao"].id == uuid.uuid5(catalog.PLAN_NAMESPACE, "implantacao")
        assert catalog.seed_plans() == (0, 0)


# ---------------------------------------------------------------- limites pelas rotas (402)


@pytest.mark.parametrize("code,max_projects", [("essencial", 5), ("profissional", 10)])
def test_limite_de_projetos_pela_rota(client, app, tenants, code, max_projects):
    a, _ = tenants
    _set_sub(app, a.company_id, code)
    _add_projects(app, a.company_id, max_projects - 2)  # tenant já tem 1 → falta 1
    login(client, app, a.supervisor_email)
    assert post(client, app, "/app/projetos/novo", NEW_PROJECT).status_code == 303
    blocked = post(client, app, "/app/projetos/novo", NEW_PROJECT)
    assert blocked.status_code == 402 and f"permite {max_projects} projetos ativos" in text_of(blocked)


@pytest.mark.parametrize("code,max_users", [("essencial", 5), ("profissional", 25)])
def test_limite_de_pessoas_pela_rota(client, app, tenants, code, max_users):
    a, _ = tenants
    _set_sub(app, a.company_id, code)
    login(client, app, a.owner_email)
    _add_invites(app, a.company_id, max_users - 3 - 1)  # 3 vínculos + convites = limite - 1
    assert post(client, app, "/app/usuarios/convidar", {"email": "ok@x.com", "role": "operator"}).status_code == 303
    blocked = post(client, app, "/app/usuarios/convidar", {"email": "nao@x.com", "role": "operator"})
    assert blocked.status_code == 402 and f"permite {max_users} usuários" in text_of(blocked)


@pytest.mark.parametrize("code", ["empresa", "implantacao"])
def test_empresa_e_implantacao_sem_limite(client, app, tenants, code):
    a, _ = tenants
    _set_sub(app, a.company_id, code)
    _add_projects(app, a.company_id, 15)
    _add_invites(app, a.company_id, 30)
    login(client, app, a.owner_email)
    assert post(client, app, "/app/projetos/novo", NEW_PROJECT).status_code == 303
    assert post(client, app, "/app/usuarios/convidar", {"email": "mais@x.com", "role": "operator"}).status_code == 303
    with app.app_context():
        company = db.session.get(Company, a.company_id)
        assert entitlements.has_feature(company, "api") and entitlements.has_feature(company, "visual_custom")
        assert entitlements.has_feature(company, "implantacao") is (code == "implantacao")


def test_preco_e_limite_vem_do_banco(client, app, tenants):
    a, _ = tenants
    with app.app_context():
        catalog.get_plan("empresa").price_cents = 123400
        catalog.get_plan("profissional").max_projects = 1
        db.session.commit()
    html = client.get("/precos").get_data(as_text=True)
    assert "1.234" in html and "Sob consulta" in html
    # teste grátis implícito no Profissional: o limite novo (1) vale na hora
    login(client, app, a.supervisor_email)
    blocked = post(client, app, "/app/projetos/novo", NEW_PROJECT)
    assert blocked.status_code == 402 and "permite 1 projetos ativos" in text_of(blocked)


# ---------------------------------------------------------------- teste grátis só nos planos 1 e 2


def test_plano_de_teste_fora_dos_planos_1_e_2_cai_no_profissional(app_factory):
    app = app_factory({"DEFAULT_TRIAL_PLAN": "empresa"})
    with app.app_context():
        a = make_tenant("A")
        company = db.session.get(Company, a.company_id)
        acc = entitlements.access(company)
        assert acc.status == "implicit_trial" and acc.plan.code == "profissional"
        assert not entitlements.has_feature(company, "api")
        sub = billing.ensure_subscription(company)
        assert sub.status == SUB_TRIALING and sub.plan.code == "profissional"


def test_cadastro_novo_comeca_no_teste_do_profissional_mesmo_com_config_errada(app_factory):
    app = app_factory({"DEFAULT_TRIAL_PLAN": "implantacao"})
    client = app.test_client()
    response = post(client, app, "/cadastro", {
        "company_name": "Nova Ltda", "name": "Dona", "email": "dona@nova.com",
        "password": "senha-forte-123", "password_confirm": "senha-forte-123",
    })
    assert response.status_code in (200, 302, 303)
    with app.app_context():
        sub = db.session.execute(select(Subscription)).scalars().all()
        assert len(sub) == 1 and sub[0].plan.code == "profissional" and sub[0].status == SUB_TRIALING


@pytest.mark.parametrize("code", ["empresa", "implantacao"])
def test_teste_grátis_em_plano_sem_teste_nao_libera_recursos(app, tenants, code):
    a, _ = tenants
    _set_sub(app, a.company_id, code, status=SUB_TRIALING, trial_ends_at=billing.now_utc() + timedelta(days=5))
    with app.app_context():
        company = db.session.get(Company, a.company_id)
        assert entitlements.effective_plan(company).code == "profissional"
        assert not entitlements.has_feature(company, "api")
        with pytest.raises(entitlements.PlanLimitError):
            entitlements.require_feature(company, "visual_custom", "Identidade visual")


def test_empresa_sem_teste_cobra_hoje_e_so_vale_pago(bclient, bapp, btenants):
    a, _ = btenants
    response = subscribe(bclient, bapp, a, plan="empresa")
    assert response.status_code == 303
    state = sub_state(bapp, a.company_id)
    assert state["status"] == SUB_TRIALING and state["plan"] == "profissional" and state["pending_plan"] == "empresa"
    [first] = payments(bapp, a.company_id)
    assert first.value_cents == 99790
    assert first.due_date == billing.local_date(billing.now_utc())  # sem esperar o fim do teste
    assert _events(bapp, a.company_id, events.PLAN_VISUAL_CUSTOM_CONTRACTED) == []
    pay(bclient, bapp, a)
    state = sub_state(bapp, a.company_id)
    assert state["plan"] == "empresa" and state["status"] == SUB_ACTIVE
    # gancho da Etapa C: evento interno + auditoria, uma vez
    assert len(_events(bapp, a.company_id, events.PLAN_VISUAL_CUSTOM_CONTRACTED)) == 1
    assert len(_audit(bapp, a.company_id, billing.VISUAL_CUSTOM_CONTRACTED)) == 1


def test_essencial_com_teste_vence_no_fim_do_teste(bclient, bapp, btenants):
    a, _ = btenants
    assert subscribe(bclient, bapp, a, plan="essencial").status_code == 303
    [first] = payments(bapp, a.company_id)
    trial_end = sub_state(bapp, a.company_id)["trial_ends_at"]
    assert first.value_cents == 24990 and first.due_date == billing.local_date(trial_end)


def test_estender_teste_recusado_em_plano_sem_teste(bapp, btenants):
    a, _ = btenants
    _set_sub(bapp, a.company_id, "empresa", status="expired")
    result = run(bapp, "billing-admin", "extend-trial", "--company", str(a.company_id), "--days", "7", "--reason", "Cliente pediu")
    assert result.exit_code != 0 and "não tem teste grátis" in result.output
    assert sub_state(bapp, a.company_id)["status"] == "expired"


# ---------------------------------------------------------------- plano 4: só pela plataforma


def test_implantacao_fora_do_autosservico(bclient, bapp, btenants):
    a, _ = btenants
    login(bclient, bapp, a.owner_email)
    assert bclient.get("/app/assinatura/planos/implantacao").status_code == 404
    assert post(bclient, bapp, "/app/assinatura/planos/implantacao").status_code == 404
    assert bclient.get("/app/assinatura/cobranca?plano=implantacao").status_code == 404
    response = subscribe(bclient, bapp, a, plan="implantacao")
    assert response.status_code == 404
    assert fake(bapp).store.calls == []
    with bapp.app_context():
        company = db.session.get(Company, a.company_id)
        plan = catalog.get_plan("implantacao")
        info = billing.BillingInfo("X Ltda", "11.222.333/0001-81", "a@b.com")
        with pytest.raises(billing.BillingError, match="Sob consulta|sob consulta"):
            billing.subscribe(company, plan, info, None)
        with pytest.raises(billing.BillingError):
            billing.change_plan(company, plan, None)
        db.session.rollback()
    assert _plan_code(bapp, a.company_id) == "profissional"


def test_telas_com_os_quatro_planos_respondem_200(bclient, bapp, btenants):
    a, _ = btenants
    for path in ("/", "/precos"):
        html = text_of(bclient.get(path))
        assert "Sob consulta" in html and "Implantação" in html and "249,90" in html and "Fale conosco" in html
    login(bclient, bapp, a.owner_email)
    assert bclient.get("/app/assinatura").status_code == 200
    page = bclient.get("/app/assinatura/planos")
    html = text_of(page)
    assert page.status_code == 200 and "Sob consulta" in html and "/app/assinatura/planos/implantacao" not in html
    assert "Sem teste grátis" in html
    subscribe(bclient, bapp, a, plan="profissional")
    for code in ("essencial", "empresa"):
        assert bclient.get(f"/app/assinatura/planos/{code}").status_code == 200


def test_precos_novos_e_servicos_da_implantacao_nas_paginas(client):
    """ADR-0019: preços, limites e textos dos serviços vêm do catálogo/tabela, nunca do template."""
    for path in ("/", "/precos"):
        html = text_of(client.get(path))
        for price in ("249,90", "497,90", "997,90"):
            assert price in html, (path, price)
        for old in ("R$ 497,00", "R$ 997,00", "R$ 497 ", "R$ 997 "):
            assert old not in html, (path, old)
        for service in catalog.IMPLANTACAO_SERVICES:
            assert service in html, (path, service)
        assert "5 projetos ativos" in html and "25 pessoas" in html
    # sem limite nem checagem: os serviços não são recursos do catálogo
    assert not [k for k in catalog.FEATURE_KEYS if "treinamento" in k or "acompanhamento" in k]


def test_set_plan_exige_motivo_audita_e_emite_evento(bclient, bapp, btenants):
    a, b = btenants
    subscribe(bclient, bapp, a)
    pay(bclient, bapp, a)
    assert run(bapp, "billing-admin", "set-plan", "--company", str(a.company_id), "--plan", "implantacao").exit_code != 0
    short = run(bapp, "billing-admin", "set-plan", "--company", str(a.company_id), "--plan", "implantacao", "--reason", "x")
    assert short.exit_code != 0 and "Motivo obrigatório" in short.output
    assert sub_state(bapp, a.company_id)["plan"] == "profissional"
    ok = run(bapp, "billing-admin", "set-plan", "--company", str(a.company_id), "--plan", "implantacao",
             "--reason", "Contrato de implantação 2026-11")
    assert ok.exit_code == 0, ok.output
    state = sub_state(bapp, a.company_id)
    assert state["plan"] == "implantacao" and state["status"] == SUB_ACTIVE and state["provider_subscription_id"] is None
    assert "cancel" in fake(bapp).store.calls  # a recorrência do Asaas parou
    [log] = _audit(bapp, a.company_id, billing.ADMIN_PLAN_SET)
    assert log.details["motivo"] == "Contrato de implantação 2026-11" and log.details["para"] == "implantacao"
    assert len(_events(bapp, a.company_id, events.PLAN_VISUAL_CUSTOM_CONTRACTED)) == 1
    assert _plan_code(bapp, b.company_id) == "profissional"  # B intacta
    # reconciliação não derruba o contrato sob consulta
    assert run(bapp, "billing-reconcile").exit_code == 0
    assert sub_state(bapp, a.company_id)["status"] == SUB_ACTIVE
    # o proprietário não troca nem cancela pelo autosserviço (recusa, sem 500)
    login(bclient, bapp, a.owner_email)
    assert bclient.get("/app/assinatura").status_code == 200
    assert bclient.get("/app/assinatura/planos").status_code == 200
    assert subscribe(bclient, bapp, a, plan="empresa").status_code == 400
    post(bclient, bapp, "/app/assinatura/cancelar")
    assert sub_state(bapp, a.company_id)["status"] == SUB_ACTIVE
    assert sub_state(bapp, a.company_id)["plan"] == "implantacao"


def test_set_plan_plano_com_preco_exige_assinatura_no_provedor(bapp, btenants):
    a, _ = btenants
    result = run(bapp, "billing-admin", "set-plan", "--company", str(a.company_id), "--plan", "empresa", "--reason", "Teste piloto")
    assert result.exit_code != 0 and "tela de assinatura" in result.output
    assert _plan_code(bapp, a.company_id) == "profissional"


# ---------------------------------------------------------------- comparação de preço explícita


def _sub_with(price_now, price_new):
    current = Plan(id=uuid.uuid4(), code="a", name="A", price_cents=price_now, features={})
    new = Plan(id=uuid.uuid4(), code="b", name="B", price_cents=price_new, features={})
    sub = Subscription(plan_id=current.id, discount_percent=None)
    sub.plan = current
    return sub, new


@pytest.mark.parametrize(
    "now,new,kind,upgrade",
    [
        (24990, 49790, billing.UPGRADE, True),
        (49790, 24990, billing.DOWNGRADE, False),
        (49790, 49790, billing.SAME_PRICE, True),  # mesmo preço: só depois de pago, nunca na hora
        (49790, None, billing.MANAGED, False),
        (None, 49790, billing.MANAGED, False),
    ],
)
def test_compare_plans_trata_igual_e_nulo(app, now, new, kind, upgrade):
    with app.app_context():
        sub, plan = _sub_with(now, new)
        assert billing.compare_plans(sub, plan) == kind
        assert billing.is_upgrade(sub, plan) is upgrade
        if new is None:
            assert billing.price_for(sub, plan) is None
            with pytest.raises(billing.BillingError):
                billing.charge_for(sub, plan)


def test_troca_pendente_de_mesmo_preco_nao_vale_na_hora(app, tenants):
    a, _ = tenants
    _set_sub(app, a.company_id, "profissional")
    with app.app_context():
        twin = Plan(code="gemeo", name="Gêmeo", price_cents=49790, max_projects=10, max_users=25, features={})
        db.session.add(twin)
        db.session.flush()
        sub = billing.subscription_for(a.company_id)
        sub.pending_plan_id, sub.pending_plan_at = twin.id, billing.now_utc() - timedelta(days=1)
        assert billing.apply_pending_plan(sub) is False  # sem fatura paga depois do pedido
        assert sub.plan.code == "profissional" and sub.pending_plan_id == twin.id
        db.session.rollback()


# ---------------------------------------------------------------- APP_BASE_URL em produção


PROD = {"SECRET_KEY": "k" * 64, "SQLALCHEMY_DATABASE_URI": "sqlite://", "RATELIMIT_STORAGE_URI": "redis://127.0.0.1:6399/0"}


@pytest.mark.parametrize("value", [None, "", "http://app.exemplo.com.br", "https://"])
def test_producao_exige_app_base_url_https(value):
    overrides = dict(PROD)
    if value is not None:
        overrides["APP_BASE_URL"] = value
    with pytest.raises(RuntimeError, match="APP_BASE_URL"):
        create_app("production", overrides)


def test_producao_sobe_com_app_base_url():
    app = create_app("production", {**PROD, "APP_BASE_URL": "https://app.exemplo.com.br"})
    assert app.config["APP_BASE_URL"] == "https://app.exemplo.com.br"

