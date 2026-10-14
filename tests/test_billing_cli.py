"""Fase 8 — `flask billing-reconcile` (idempotente) e `flask billing-admin` (motivo auditado)."""

from __future__ import annotations

from datetime import timedelta

from app.extensions import db
from app.models import AuditLog
from app.models.billing import SUB_ACTIVE, SUB_CANCELED, SUB_EXPIRED, SUB_TRIALING
from app.services.billing import service as billing
from tests.test_billing import bapp, bclient, btenants, fake, pay, sub_state, subscribe  # noqa: F401 (fixtures)


def run(app, *args):
    return app.test_cli_runner().invoke(args=list(args))


def test_reconcile_corrige_webhook_perdido_e_e_idempotente(bclient, bapp, btenants):
    a, b = btenants
    subscribe(bclient, bapp, a)
    provider = fake(bapp)
    pid = provider.payments_of("sub_fake_0001")[0]
    provider.set_payment_status(pid, "received")  # pago no Asaas, webhook nunca chegou
    assert sub_state(bapp, a.company_id)["status"] == SUB_TRIALING
    result = run(bapp, "billing-reconcile")
    assert result.exit_code == 0, result.output
    assert "corrigidas: 1" in result.output
    assert sub_state(bapp, a.company_id)["status"] == SUB_ACTIVE
    again = run(bapp, "billing-reconcile")
    assert again.exit_code == 0 and "corrigidas: 0" in again.output


def test_reconcile_pega_cancelamento_feito_direto_no_asaas(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a)
    pay(bclient, bapp, a)
    fake(bapp).cancel("sub_fake_0001")  # sem webhook
    run(bapp, "billing-reconcile")
    assert sub_state(bapp, a.company_id)["status"] == SUB_CANCELED


def test_reconcile_encerra_teste_vencido_sem_assinar(bapp, btenants):
    a, _ = btenants
    with bapp.app_context():
        from app.models import Company

        sub = billing.ensure_subscription(db.session.get(Company, a.company_id))
        sub.trial_ends_at = billing.now_utc() - timedelta(minutes=1)
        db.session.commit()
    run(bapp, "billing-reconcile")
    assert sub_state(bapp, a.company_id)["status"] == SUB_EXPIRED


def test_admin_estende_teste_com_motivo_auditado(bapp, btenants):
    a, _ = btenants
    no_reason = run(bapp, "billing-admin", "extend-trial", "--company", str(a.company_id), "--days", "7")
    assert no_reason.exit_code != 0 and "--reason" in no_reason.output
    blank = run(bapp, "billing-admin", "extend-trial", "--company", str(a.company_id), "--days", "7", "--reason", "  ")
    assert blank.exit_code != 0 and "Motivo obrigatório" in blank.output
    before = None
    with bapp.app_context():
        from app.models import Company

        before = billing.ensure_subscription(db.session.get(Company, a.company_id)).trial_ends_at
        db.session.commit()
    ok = run(bapp, "billing-admin", "extend-trial", "--company", str(a.company_id), "--days", "7",
             "--reason", "Piloto pediu mais uma semana")
    assert ok.exit_code == 0, ok.output
    state = sub_state(bapp, a.company_id)
    assert state["trial_ends_at"] - billing._aware(before) == timedelta(days=7)
    with bapp.app_context():
        log = db.session.query(AuditLog).filter_by(company_id=a.company_id, action=billing.TRIAL_EXTENDED).one()
        assert log.details["motivo"] == "Piloto pediu mais uma semana" and log.details["dias"] == 7
        assert log.actor_user_id is None
    assert run(bapp, "billing-admin", "extend-trial", "--company", "nao-e-uuid", "--days", "7", "--reason", "Motivo x").exit_code != 0


def test_admin_desconto_muda_valor_no_provedor_e_audita(bclient, bapp, btenants):
    a, _ = btenants
    subscribe(bclient, bapp, a, plan="profissional")
    pay(bclient, bapp, a)
    result = run(bapp, "billing-admin", "discount", "--company", str(a.company_id), "--percent", "20",
                 "--reason", "Cliente piloto (contrato 2026)")
    assert result.exit_code == 0, result.output
    assert "R$ 279.20/mês" in result.output
    assert fake(bapp).store.subscriptions["sub_fake_0001"]["value_cents"] == 27920
    with bapp.app_context():
        log = db.session.query(AuditLog).filter_by(company_id=a.company_id, action=billing.DISCOUNT_GRANTED).one()
        assert log.details["motivo"] == "Cliente piloto (contrato 2026)" and log.details["para_percentual"] == 20
    assert run(bapp, "billing-admin", "discount", "--company", str(a.company_id), "--percent", "95",
               "--reason", "Muito desconto").exit_code != 0
    # a tela mostra o desconto
    assert "20% de desconto" in bclient.get("/app/assinatura").get_data(as_text=True)
