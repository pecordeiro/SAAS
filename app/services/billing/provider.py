"""Interface ``PaymentProvider`` (ADR-0004) e os tipos que ela devolve.

O resto do sistema (serviço, telas, webhook, reconciliação) só conhece esta interface:
trocar o Asaas por outro provedor é escrever outra implementação. Valores sempre em
centavos (int) e datas como ``date``; o status de cobrança já vem traduzido para o
vocabulário local (``app.models.billing.PAYMENT_STATUSES``).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime

# Status locais de cobrança (iguais ao CHECK de payments.status).
PAY_PENDING = "pending"
PAY_CONFIRMED = "confirmed"
PAY_RECEIVED = "received"
PAY_OVERDUE = "overdue"
PAY_REFUNDED = "refunded"
PAY_CANCELED = "canceled"
PAID_STATUSES = frozenset({PAY_CONFIRMED, PAY_RECEIVED})


class PaymentProviderError(Exception):
    """Falha ao falar com o provedor. ``message`` é segura para mostrar ao usuário (sem
    chave, sem payload); ``status`` é o HTTP devolvido (None = rede/timeout)."""

    def __init__(self, message: str, status: int | None = None, codes: tuple[str, ...] = ()):
        super().__init__(message)
        self.message = message
        self.status = status
        self.codes = codes


@dataclass(frozen=True)
class CustomerData:
    name: str
    cpf_cnpj: str  # só dígitos, já validado
    email: str
    external_reference: str  # id da empresa (nosso)


@dataclass(frozen=True)
class ProviderSubscription:
    id: str
    customer_id: str
    value_cents: int
    next_due_date: date | None
    active: bool  # False = inativada, expirada ou removida no provedor


@dataclass(frozen=True)
class ProviderPayment:
    id: str
    subscription_id: str | None
    status: str  # vocabulário local (PAY_*)
    value_cents: int
    due_date: date
    paid_at: datetime | None
    invoice_url: str | None


class PaymentProvider(ABC):
    """Contrato mínimo de um provedor de assinaturas recorrentes com checkout hospedado."""

    name: str  # "asaas" | "fake" (CHECK de subscriptions.provider)

    @abstractmethod
    def create_customer(self, data: CustomerData) -> str:
        """Cria o cliente e devolve o id dele no provedor."""

    @abstractmethod
    def update_customer(self, customer_id: str, data: CustomerData) -> None:
        """Atualiza nome, CPF/CNPJ e e-mail de cobrança."""

    @abstractmethod
    def create_subscription(
        self, customer_id: str, value_cents: int, next_due_date: date, description: str, external_reference: str
    ) -> ProviderSubscription:
        """Assinatura mensal; o provedor gera a primeira cobrança com vencimento em
        ``next_due_date`` (Pix, boleto ou cartão, à escolha do cliente na página dele)."""

    @abstractmethod
    def change_plan(self, subscription_id: str, value_cents: int, description: str) -> ProviderSubscription:
        """Novo valor mensal; cobranças pendentes passam a valer o novo valor."""

    @abstractmethod
    def cancel(self, subscription_id: str) -> None:
        """Encerra a recorrência no provedor (novas cobranças deixam de ser geradas)."""

    @abstractmethod
    def get_subscription(self, subscription_id: str) -> ProviderSubscription | None:
        """Estado atual no provedor (None = não existe mais)."""

    @abstractmethod
    def list_payments(self, subscription_id: str) -> list[ProviderPayment]:
        """Todas as cobranças da assinatura, com status atual (fonte de verdade)."""
