"""``FakeProvider``: provedor em memória, determinístico, para testes e desenvolvimento.

Ids previsíveis (``cus_fake_0001``, ``sub_fake_0001``, ``pay_fake_0001``, ``evt_fake_0001``).
O estado vive em ``FakeStore`` (um por app, em ``app.extensions``), então sobrevive entre
requisições do mesmo app de teste. Helpers só de teste: ``set_payment_status``,
``add_payment`` (próxima mensalidade), ``webhook`` (payload no formato do Asaas) e
``fail_next`` (simula recusa do provedor).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from app.services.billing.provider import (
    PAID_STATUSES,
    PAY_CANCELED,
    PAY_PENDING,
    CustomerData,
    PaymentProvider,
    PaymentProviderError,
    ProviderPayment,
    ProviderSubscription,
)

INVOICE_BASE = "https://pagamento.fake.invalid/i/"

# Status local → status do Asaas (para montar payloads realistas).
ASAAS_STATUS = {
    "pending": "PENDING",
    "confirmed": "CONFIRMED",
    "received": "RECEIVED",
    "overdue": "OVERDUE",
    "refunded": "REFUNDED",
    "canceled": "PENDING",
}


def add_months(day: date, months: int = 1) -> date:
    month = day.month - 1 + months
    year = day.year + month // 12
    month = month % 12 + 1
    last = [31, 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
    return date(year, month, min(day.day, last))


@dataclass
class FakeStore:
    counters: dict = field(default_factory=dict)
    customers: dict = field(default_factory=dict)
    subscriptions: dict = field(default_factory=dict)
    payments: dict = field(default_factory=dict)
    calls: list = field(default_factory=list)
    fail_next: str | None = None
    fail_on: dict = field(default_factory=dict)  # operação → mensagem (falha sempre nela)

    def next_id(self, prefix: str) -> str:
        self.counters[prefix] = self.counters.get(prefix, 0) + 1
        return f"{prefix}_fake_{self.counters[prefix]:04d}"


class FakeProvider(PaymentProvider):
    name = "fake"

    def __init__(self, store: FakeStore | None = None):
        self.store = store or FakeStore()

    def _maybe_fail(self, op: str) -> None:
        self.store.calls.append(op)
        if op in self.store.fail_on:
            raise PaymentProviderError(self.store.fail_on[op], status=400, codes=("invalid_action",))
        if self.store.fail_next:
            message, self.store.fail_next = self.store.fail_next, None
            raise PaymentProviderError(message, status=400, codes=("invalid_action",))

    # ------------------------------------------------------------------ interface

    def create_customer(self, data: CustomerData) -> str:
        self._maybe_fail("create_customer")
        cid = self.store.next_id("cus")
        self.store.customers[cid] = data
        return cid

    def update_customer(self, customer_id: str, data: CustomerData) -> None:
        self._maybe_fail("update_customer")
        if customer_id not in self.store.customers:
            raise PaymentProviderError("Cliente não encontrado no provedor.", status=404)
        self.store.customers[customer_id] = data

    def create_subscription(self, customer_id, value_cents, next_due_date, description, external_reference):
        self._maybe_fail("create_subscription")
        if customer_id not in self.store.customers:
            raise PaymentProviderError("Cliente não encontrado no provedor.", status=404)
        sid = self.store.next_id("sub")
        self.store.subscriptions[sid] = {
            "id": sid,
            "customer": customer_id,
            "value_cents": value_cents,
            "next_due_date": next_due_date,
            "active": True,
            "description": description,
        }
        self.add_payment(sid)  # o Asaas gera a 1ª cobrança na criação
        return self._sub(sid)

    def change_plan(self, subscription_id, value_cents, description):
        self._maybe_fail("change_plan")
        sub = self._raw_sub(subscription_id)
        sub["value_cents"] = value_cents
        sub["description"] = description
        for pay in self.store.payments.values():
            if pay["subscription"] == subscription_id and pay["status"] in ("pending", "overdue"):
                pay["value_cents"] = value_cents
        return self._sub(subscription_id)

    def cancel(self, subscription_id: str) -> None:
        self._maybe_fail("cancel")
        sub = self.store.subscriptions.get(subscription_id)
        if sub is None:
            return
        sub["active"] = False
        # Como no Asaas: cobranças ainda em aberto são removidas junto.
        for pay in self.store.payments.values():
            if pay["subscription"] == subscription_id and pay["status"] in ("pending", "overdue"):
                pay["status"] = PAY_CANCELED

    def get_subscription(self, subscription_id: str) -> ProviderSubscription | None:
        self.store.calls.append("get_subscription")
        if subscription_id not in self.store.subscriptions:
            return None
        return self._sub(subscription_id)

    def list_payments(self, subscription_id: str) -> list[ProviderPayment]:
        self.store.calls.append("list_payments")
        return [self._payment(p) for p in self.store.payments.values() if p["subscription"] == subscription_id]

    # ------------------------------------------------------------------ helpers de teste

    def _raw_sub(self, sid: str) -> dict:
        try:
            return self.store.subscriptions[sid]
        except KeyError:
            raise PaymentProviderError("Assinatura não encontrada no provedor.", status=404) from None

    def _sub(self, sid: str) -> ProviderSubscription:
        s = self.store.subscriptions[sid]
        return ProviderSubscription(s["id"], s["customer"], s["value_cents"], s["next_due_date"], s["active"])

    @staticmethod
    def _payment(p: dict) -> ProviderPayment:
        return ProviderPayment(p["id"], p["subscription"], p["status"], p["value_cents"], p["due_date"], p["paid_at"], p["invoice_url"])

    def add_payment(self, subscription_id: str, due_date: date | None = None) -> str:
        """Gera a próxima mensalidade (como o agendador do Asaas)."""
        sub = self._raw_sub(subscription_id)
        pid = self.store.next_id("pay")
        due = due_date or sub["next_due_date"]
        self.store.payments[pid] = {
            "id": pid,
            "subscription": subscription_id,
            "customer": sub["customer"],
            "status": PAY_PENDING,
            "value_cents": sub["value_cents"],
            "due_date": due,
            "paid_at": None,
            "invoice_url": INVOICE_BASE + pid,
        }
        sub["next_due_date"] = add_months(due)
        return pid

    def set_payment_status(self, payment_id: str, status: str, paid_on: date | None = None) -> None:
        pay = self.store.payments[payment_id]
        pay["status"] = status
        if status in PAID_STATUSES:
            day = paid_on or date.today()
            pay["paid_at"] = datetime(day.year, day.month, day.day, 12, tzinfo=timezone.utc)

    def payments_of(self, subscription_id: str) -> list[str]:
        return [p["id"] for p in self.store.payments.values() if p["subscription"] == subscription_id]

    def webhook(self, event: str, payment_id: str | None = None, subscription_id: str | None = None, event_id: str | None = None) -> dict:
        """Payload no formato do Asaas: ``{"id", "event", "dateCreated", "payment"|"subscription"}``."""
        payload: dict = {
            "id": event_id or self.store.next_id("evt"),
            "event": event,
            "dateCreated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        }
        if payment_id:
            p = copy.deepcopy(self.store.payments[payment_id])
            payload["payment"] = {
                "object": "payment",
                "id": p["id"],
                "customer": p["customer"],
                "subscription": p["subscription"],
                "value": p["value_cents"] / 100,
                "status": ASAAS_STATUS[p["status"]],
                "dueDate": p["due_date"].isoformat(),
                "paymentDate": p["paid_at"].date().isoformat() if p["paid_at"] else None,
                "invoiceUrl": p["invoice_url"],
                "deleted": p["status"] == PAY_CANCELED,
            }
        if subscription_id:
            s = self.store.subscriptions[subscription_id]
            payload["subscription"] = {
                "object": "subscription",
                "id": s["id"],
                "customer": s["customer"],
                "value": s["value_cents"] / 100,
                "nextDueDate": s["next_due_date"].isoformat(),
                "status": "ACTIVE" if s["active"] else "INACTIVE",
                "deleted": not s["active"],
            }
        return payload
