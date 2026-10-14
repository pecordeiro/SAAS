"""Fase 8 com RLS ligado e forçado (papel comum, sem BYPASSRLS): o webhook chega sem
empresa e acha a assinatura só pelo id do provedor (política subscriptions_provider_lookup).

Usa o papel de cluster de tests/test_rls.py (``controle_app_rls_test``)."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app import create_app
from app.extensions import db
from tests.conftest import login, post, requires_postgres
from tests.test_billing import VALID_CNPJ, WEBHOOK_TOKEN
from tests.test_rls import _set, raw, rls_url  # noqa: F401 (fixtures)

pytestmark = requires_postgres


@pytest.fixture()
def rls_billing_app(rls_url):
    app = create_app(
        "test",
        {"SQLALCHEMY_DATABASE_URI": rls_url, "RLS_ENABLED": True, "BILLING_PROVIDER": "fake", "ASAAS_WEBHOOK_TOKEN": WEBHOOK_TOKEN},
    )
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


def test_ciclo_de_assinatura_e_webhook_com_rls(app, rls_billing_app, tenants):
    a, b = tenants
    from app.models import Payment, Subscription
    from app.services.billing import service as billing

    rapp = rls_billing_app
    client = rapp.test_client()
    login(client, rapp, a.owner_email)
    response = post(client, rapp, "/app/assinatura/cobranca",
                    {"plan": "essencial", "name": "Empresa A Ltda", "cpf_cnpj": VALID_CNPJ, "email": "fin@a.com"})
    assert response.status_code == 303, response.get_data(as_text=True)[:500]
    with rapp.app_context():
        provider = billing.get_provider(rapp)
    pid = provider.payments_of("sub_fake_0001")[0]
    provider.set_payment_status(pid, "confirmed")
    webhook = rapp.test_client().post("/webhooks/asaas", json=provider.webhook("PAYMENT_CONFIRMED", payment_id=pid),
                                      headers={"asaas-access-token": WEBHOOK_TOKEN})
    assert webhook.get_json() == {"status": "processed"}
    with app.app_context():  # papel dono: confere o resultado
        sub = db.session.query(Subscription).filter_by(company_id=a.company_id).one()
        assert sub.status == "active"
        assert db.session.query(Payment).filter_by(company_id=a.company_id, status="confirmed").count() == 1
        assert db.session.query(Subscription).filter_by(company_id=b.company_id).count() == 0


def test_politica_de_busca_so_libera_a_linha_do_id_informado(app, raw, tenants):
    a, b = tenants
    from app.models import Subscription
    from app.services.plans import get_plan

    with app.app_context():
        plan = get_plan("essencial")
        for t, sid in ((a, "sub_rls_a"), (b, "sub_rls_b")):
            db.session.add(Subscription(company_id=t.company_id, plan_id=plan.id, provider="asaas", status="active",
                                        provider_subscription_id=sid))
        db.session.commit()
    with raw.begin() as conn:
        assert conn.execute(text("SELECT count(*) FROM subscriptions")).scalar() == 0
        conn.execute(text("SELECT set_config('app.billing_lookup', 'sub_rls_b', true)"))
        rows = conn.execute(text("SELECT company_id FROM subscriptions")).scalars().all()
        assert rows == [b.company_id]
        # só leitura: com a busca ligada não dá para alterar a linha
        assert conn.execute(text("UPDATE subscriptions SET status = 'expired'")).rowcount == 0
        conn.execute(text("SELECT set_config('app.billing_lookup', 'sub_inexistente', true)"))
        assert conn.execute(text("SELECT count(*) FROM subscriptions")).scalar() == 0
    with raw.begin() as conn:  # transação nova: a variável some
        assert conn.execute(text("SELECT count(*) FROM subscriptions")).scalar() == 0
    with raw.begin() as conn:
        _set(conn, company=a.company_id)
        assert conn.execute(text("SELECT provider_subscription_id FROM subscriptions")).scalars().all() == ["sub_rls_a"]
