"""``AsaasProvider``: API v3 do Asaas (https://docs.asaas.com, ver docs/plano/pagamentos.md).

- Base URL por ``ASAAS_BASE_URL`` (padrão: sandbox ``https://api-sandbox.asaas.com/v3``;
  produção ``https://api.asaas.com/v3``). Chave em ``ASAAS_API_KEY``, enviada no header
  ``access_token`` (o Asaas não usa ``Authorization: Bearer``).
- Toda chamada com timeout (conexão, leitura). Erro vira ``PaymentProviderError`` com
  mensagem segura; o log leva só método, caminho, HTTP e códigos de erro do Asaas — nunca
  a chave, o corpo enviado nem o payload completo devolvido.
- Nenhum dado de cartão passa por aqui: a assinatura nasce com ``billingType=UNDEFINED`` e
  o cliente escolhe Pix, boleto ou cartão na página de pagamento do próprio Asaas
  (``invoiceUrl`` da cobrança).
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import requests

from app.services.billing.provider import (
    PAY_CANCELED,
    PAY_CONFIRMED,
    PAY_OVERDUE,
    PAY_PENDING,
    PAY_RECEIVED,
    PAY_REFUNDED,
    CustomerData,
    PaymentProvider,
    PaymentProviderError,
    ProviderPayment,
    ProviderSubscription,
)

logger = logging.getLogger(__name__)

SANDBOX_URL = "https://api-sandbox.asaas.com/v3"
PRODUCTION_URL = "https://api.asaas.com/v3"
USER_AGENT = "controle-producao/1.0"
PAGE_SIZE = 100
MAX_PAGES = 50

# Status de cobrança do Asaas → vocabulário local. Estorno pedido/em andamento ainda conta
# como pago (o dinheiro só volta com REFUNDED); chargeback tira o acesso como um estorno.
PAYMENT_STATUS_MAP: dict[str, str] = {
    "PENDING": PAY_PENDING,
    "AWAITING_RISK_ANALYSIS": PAY_PENDING,
    "APPROVED_BY_RISK_ANALYSIS": PAY_PENDING,
    "REPROVED_BY_RISK_ANALYSIS": PAY_PENDING,
    "CONFIRMED": PAY_CONFIRMED,
    "RECEIVED": PAY_RECEIVED,
    "RECEIVED_IN_CASH": PAY_RECEIVED,
    "DUNNING_RECEIVED": PAY_RECEIVED,
    "REFUND_REQUESTED": PAY_CONFIRMED,
    "REFUND_IN_PROGRESS": PAY_CONFIRMED,
    "OVERDUE": PAY_OVERDUE,
    "DUNNING_REQUESTED": PAY_OVERDUE,
    "REFUNDED": PAY_REFUNDED,
    "CHARGEBACK_REQUESTED": PAY_REFUNDED,
    "CHARGEBACK_DISPUTE": PAY_REFUNDED,
    "AWAITING_CHARGEBACK_REVERSAL": PAY_REFUNDED,
}


def to_cents(value: Any) -> int:
    return int((Decimal(str(value or 0)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def to_reais(cents: int) -> float:
    return float(Decimal(cents) / 100)


def _date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _https(url: Any) -> str | None:
    """Só guarda link https (vira href na tela; nada de javascript: ou http)."""
    url = str(url or "")
    return url[:255] if url.startswith("https://") else None


def map_payment(obj: dict) -> ProviderPayment:
    """Objeto ``payment`` do Asaas (API ou webhook) → ``ProviderPayment``."""
    raw = str(obj.get("status") or "").upper()
    status = PAY_CANCELED if obj.get("deleted") else PAYMENT_STATUS_MAP.get(raw, PAY_PENDING)
    paid_day = _date(obj.get("clientPaymentDate") or obj.get("paymentDate") or obj.get("confirmedDate"))
    return ProviderPayment(
        id=str(obj.get("id") or ""),
        subscription_id=obj.get("subscription") or None,
        status=status,
        value_cents=to_cents(obj.get("value")),
        due_date=_date(obj.get("dueDate")) or date.today(),
        paid_at=datetime(paid_day.year, paid_day.month, paid_day.day, 12, tzinfo=timezone.utc) if paid_day else None,
        invoice_url=_https(obj.get("invoiceUrl")),
    )


def map_subscription(obj: dict) -> ProviderSubscription:
    status = str(obj.get("status") or "").upper()
    return ProviderSubscription(
        id=str(obj.get("id") or ""),
        customer_id=str(obj.get("customer") or ""),
        value_cents=to_cents(obj.get("value")),
        next_due_date=_date(obj.get("nextDueDate")),
        active=status == "ACTIVE" and not obj.get("deleted"),
    )


class AsaasProvider(PaymentProvider):
    name = "asaas"

    def __init__(self, api_key: str, base_url: str = SANDBOX_URL, timeout: tuple[float, float] = (5.0, 15.0), session=None):
        if not api_key:
            raise PaymentProviderError("Pagamento não configurado (ASAAS_API_KEY ausente).")
        self._api_key = api_key
        self.base_url = (base_url or SANDBOX_URL).rstrip("/")
        self.timeout = timeout
        self._http = session or requests.Session()

    def __repr__(self) -> str:  # nunca mostra a chave
        return f"AsaasProvider(base_url={self.base_url!r})"

    # ------------------------------------------------------------------ HTTP

    def _request(self, method: str, path: str, *, json: dict | None = None, params: dict | None = None, allow_404: bool = False):
        url = f"{self.base_url}{path}"
        headers = {
            "access_token": self._api_key,
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        try:
            response = self._http.request(method, url, headers=headers, json=json, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            logger.error("asaas %s %s: falha de rede (%s)", method, path, exc.__class__.__name__)
            raise PaymentProviderError("Não foi possível falar com o Asaas agora. Tente de novo em instantes.") from None
        if allow_404 and response.status_code == 404:
            return None
        if response.status_code >= 400:
            codes: tuple[str, ...] = ()
            message = "O Asaas recusou a operação. Confira os dados de cobrança e tente de novo; se continuar, fale com a gente."
            try:
                errors = (response.json() or {}).get("errors") or []
                codes = tuple(str(e.get("code") or "") for e in errors if isinstance(e, dict))
                # A descrição do Asaas é texto do próprio provedor (ex.: "CPF inválido"):
                # mostrada ao usuário, mas não vai para o log.
                descriptions = [str(e.get("description") or "") for e in errors if isinstance(e, dict)]
                if descriptions and response.status_code == 400:
                    message = " ".join(d for d in descriptions if d)[:300] or message
            except ValueError:
                pass
            logger.error("asaas %s %s: HTTP %s %s", method, path, response.status_code, ",".join(codes))
            raise PaymentProviderError(message, status=response.status_code, codes=codes)
        logger.info("asaas %s %s: HTTP %s", method, path, response.status_code)
        try:
            return response.json()
        except ValueError:
            return {}

    # ------------------------------------------------------------------ interface

    @staticmethod
    def _customer_body(data: CustomerData) -> dict:
        return {
            "name": data.name,
            "cpfCnpj": data.cpf_cnpj,
            "email": data.email,
            "externalReference": data.external_reference,
        }

    def create_customer(self, data: CustomerData) -> str:
        body = self._request("POST", "/customers", json=self._customer_body(data))
        return str(body["id"])

    def update_customer(self, customer_id: str, data: CustomerData) -> None:
        self._request("PUT", f"/customers/{customer_id}", json=self._customer_body(data))

    def create_subscription(self, customer_id, value_cents, next_due_date, description, external_reference):
        body = self._request(
            "POST",
            "/subscriptions",
            json={
                "customer": customer_id,
                "billingType": "UNDEFINED",
                "value": to_reais(value_cents),
                "nextDueDate": next_due_date.isoformat(),
                "cycle": "MONTHLY",
                "description": description,
                "externalReference": external_reference,
            },
        )
        return map_subscription(body)

    def change_plan(self, subscription_id, value_cents, description):
        body = self._request(
            "PUT",
            f"/subscriptions/{subscription_id}",
            json={"value": to_reais(value_cents), "description": description, "updatePendingPayments": True},
        )
        return map_subscription(body)

    def cancel(self, subscription_id: str) -> None:
        self._request("DELETE", f"/subscriptions/{subscription_id}", allow_404=True)

    def get_subscription(self, subscription_id: str) -> ProviderSubscription | None:
        body = self._request("GET", f"/subscriptions/{subscription_id}", allow_404=True)
        return map_subscription(body) if body else None

    def list_payments(self, subscription_id: str) -> list[ProviderPayment]:
        payments: list[ProviderPayment] = []
        offset = 0
        for _ in range(MAX_PAGES):
            body = self._request(
                "GET", f"/subscriptions/{subscription_id}/payments", params={"offset": offset, "limit": PAGE_SIZE}, allow_404=True
            )
            if not body:
                break
            payments.extend(map_payment(p) for p in body.get("data") or [])
            if not body.get("hasMore"):
                break
            offset += PAGE_SIZE
        return payments
