"""Fase 8 — AsaasProvider sem rede (sessão HTTP falsa): URL, header access_token, timeout,
corpo das chamadas, mapeamento de status e que a chave nunca aparece em log/repr."""

from __future__ import annotations

import logging
from datetime import date

import pytest
import requests

from app.services.billing.asaas import SANDBOX_URL, AsaasProvider, map_payment
from app.services.billing.provider import CustomerData, PaymentProviderError

KEY = "$aact_hmlg_chave_secreta_de_teste"


class FakeResponse:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def provider(*responses, base=None):
    session = FakeSession(responses)
    return AsaasProvider(KEY, base or SANDBOX_URL, timeout=(3, 7), session=session), session


def test_cria_cliente_e_assinatura_com_header_e_timeout():
    p, s = provider(
        FakeResponse(200, {"id": "cus_000001"}),
        FakeResponse(200, {"id": "sub_000001", "customer": "cus_000001", "value": 149.0, "nextDueDate": "2026-10-28", "status": "ACTIVE"}),
    )
    cid = p.create_customer(CustomerData("Empresa X", "11222333000181", "f@x.com", "empresa-uuid"))
    sub = p.create_subscription(cid, 14900, date(2026, 10, 28), "plano", "empresa-uuid")
    method, url, kw = s.calls[0]
    assert (method, url) == ("POST", "https://api-sandbox.asaas.com/v3/customers")
    assert kw["headers"]["access_token"] == KEY and "Authorization" not in kw["headers"]
    assert kw["headers"]["User-Agent"] and kw["timeout"] == (3, 7)
    assert kw["json"] == {"name": "Empresa X", "cpfCnpj": "11222333000181", "email": "f@x.com", "externalReference": "empresa-uuid"}
    method, url, kw = s.calls[1]
    assert (method, url) == ("POST", "https://api-sandbox.asaas.com/v3/subscriptions")
    assert kw["json"]["billingType"] == "UNDEFINED" and kw["json"]["cycle"] == "MONTHLY"
    assert kw["json"]["value"] == 149.0 and kw["json"]["nextDueDate"] == "2026-10-28"
    assert sub.id == "sub_000001" and sub.value_cents == 14900 and sub.active


def test_base_url_configuravel_e_troca_cancelamento():
    p, s = provider(
        FakeResponse(200, {"id": "sub_1", "customer": "c", "value": 349, "status": "ACTIVE"}),
        FakeResponse(200, {"deleted": True, "id": "sub_1"}),
        base="https://api.asaas.com/v3/",
    )
    p.change_plan("sub_1", 34900, "Profissional")
    p.cancel("sub_1")
    assert s.calls[0][0:2] == ("PUT", "https://api.asaas.com/v3/subscriptions/sub_1")
    assert s.calls[0][2]["json"] == {"value": 349.0, "description": "Profissional", "updatePendingPayments": True}
    assert s.calls[1][0:2] == ("DELETE", "https://api.asaas.com/v3/subscriptions/sub_1")


def test_lista_cobrancas_paginada_e_mapeia_status():
    p, s = provider(
        FakeResponse(200, {"hasMore": True, "data": [{"id": "pay_1", "subscription": "sub_1", "status": "RECEIVED", "value": 149,
                                                      "dueDate": "2026-09-28", "paymentDate": "2026-09-27", "invoiceUrl": "https://sandbox.asaas.com/i/1"}]}),
        FakeResponse(200, {"hasMore": False, "data": [{"id": "pay_2", "subscription": "sub_1", "status": "OVERDUE", "value": 149, "dueDate": "2026-10-28"}]}),
    )
    items = p.list_payments("sub_1")
    assert [(i.id, i.status) for i in items] == [("pay_1", "received"), ("pay_2", "overdue")]
    assert items[0].paid_at.date() == date(2026, 9, 27) and items[0].invoice_url.endswith("/i/1")
    assert s.calls[1][2]["params"] == {"offset": 100, "limit": 100}


@pytest.mark.parametrize("raw,local", [("PENDING", "pending"), ("CONFIRMED", "confirmed"), ("RECEIVED_IN_CASH", "received"),
                                       ("REFUNDED", "refunded"), ("CHARGEBACK_REQUESTED", "refunded"),
                                       ("REFUND_REQUESTED", "confirmed"), ("DESCONHECIDO", "pending")])
def test_mapa_de_status(raw, local):
    assert map_payment({"id": "p", "status": raw, "value": 1, "dueDate": "2026-01-01"}).status == local


def test_cobranca_removida_vira_cancelada():
    assert map_payment({"id": "p", "status": "PENDING", "deleted": True, "dueDate": "2026-01-01"}).status == "canceled"


def test_erro_http_vira_erro_seguro_sem_vazar_chave(caplog):
    p, _ = provider(FakeResponse(400, {"errors": [{"code": "invalid_cpfCnpj", "description": "O CPF/CNPJ informado é inválido."}]}))
    # alembic (fileConfig nos testes de migration) desliga loggers já criados
    logging.getLogger("app.services.billing.asaas").disabled = False
    caplog.set_level(logging.DEBUG)
    with pytest.raises(PaymentProviderError) as info:
        p.create_customer(CustomerData("X", "11222333000181", "f@x.com", "e"))
    assert info.value.status == 400 and info.value.codes == ("invalid_cpfCnpj",)
    assert "inválido" in info.value.message
    assert KEY not in caplog.text and "11222333000181" not in caplog.text
    assert "invalid_cpfCnpj" in caplog.text
    assert KEY not in repr(p)


def test_falha_de_rede_e_404():
    p, _ = provider(requests.ConnectTimeout("x"), FakeResponse(404, {}))
    with pytest.raises(PaymentProviderError) as info:
        p.get_subscription("sub_1")
    assert info.value.status is None
    assert p.get_subscription("sub_1") is None


def test_sem_chave_nao_inicia():
    with pytest.raises(PaymentProviderError):
        AsaasProvider("")


def test_provedor_em_producao_exige_chave():
    # Fase 7: produção exige Redis no rate limit (cliente preguiçoso: não conecta no init).
    from app import create_app
    from app.services.billing import service as billing

    app = create_app("production", {"SQLALCHEMY_DATABASE_URI": "sqlite://", "SECRET_KEY": "x" * 32, "RATELIMIT_STORAGE_URI": "redis://127.0.0.1:6399/0"})
    with app.app_context():
        with pytest.raises(PaymentProviderError):
            billing.get_provider(app)
    app2 = create_app("production", {"SQLALCHEMY_DATABASE_URI": "sqlite://", "SECRET_KEY": "x" * 32, "RATELIMIT_STORAGE_URI": "redis://127.0.0.1:6399/0", "ASAAS_API_KEY": KEY})
    with app2.app_context():
        prov = billing.get_provider(app2)
        assert isinstance(prov, AsaasProvider) and prov.base_url == SANDBOX_URL


def test_link_de_pagamento_so_https():
    assert map_payment({"id": "p", "status": "PENDING", "dueDate": "2026-01-01", "invoiceUrl": "javascript:alert(1)"}).invoice_url is None
    assert map_payment({"id": "p", "status": "PENDING", "dueDate": "2026-01-01", "invoiceUrl": "http://x/i/1"}).invoice_url is None
