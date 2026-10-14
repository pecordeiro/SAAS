"""Regras de assinatura e cobrança (Fase 8).

Estados locais (``subscriptions.status``), arquitetura.md §7:

    trialing → active ⇄ past_due → (carência) → expired;  canceled vale até current_period_end

- O estado é NOSSO e é sempre RECALCULADO a partir das cobranças locais (``recompute``),
  não “empurrado” por evento. Assim a ordem de chegada dos webhooks não importa: um evento
  só atualiza o status de UMA cobrança, e o status da assinatura sai do conjunto.
- Uma cobrança nunca “volta” de status por webhook (ex.: OVERDUE chegando depois de
  RECEIVED). Quando o evento contradiz o que já sabemos, perguntamos ao provedor
  (``list_payments``) e vale o que ele disser — o Asaas é a fonte de verdade de pagamentos.
- Pago (confirmed/received) cobre do vencimento até o mesmo dia do mês seguinte
  (``current_period_end``). Vencida sem pagamento → ``past_due`` com ``grace_until`` =
  vencimento + ``PAST_DUE_GRACE_DAYS`` (7) e e-mail aos proprietários; passada a carência →
  ``expired`` = modo leitura (``entitlements``). Nada é apagado.
- Cancelar vale até o fim do período pago; estorno/chargeback tira a cobertura daquele mês.

Nenhuma função aqui faz commit: quem chama (rota, webhook, CLI) fecha a transação.
"""

from __future__ import annotations

import logging
import math
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import current_app
from sqlalchemy import select, text

from app import rls
from app.extensions import db
from app.models import Company, Payment, Plan, Subscription
from app.models.billing import SUB_ACTIVE, SUB_CANCELED, SUB_EXPIRED, SUB_PAST_DUE, SUB_TRIALING
from app.services import audit, entitlements
from app.services.billing import notify
from app.services.billing.asaas import AsaasProvider, map_payment
from app.services.billing.documents import is_valid_document, only_digits
from app.services.billing.fake import FakeProvider, FakeStore, add_months
from app.services.billing.provider import (
    PAID_STATUSES,
    PAY_CANCELED,
    PAY_OVERDUE,
    PAY_PENDING,
    PAY_REFUNDED,
    CustomerData,
    PaymentProvider,
    PaymentProviderError,
    ProviderPayment,
)

logger = logging.getLogger(__name__)

TZ = ZoneInfo("America/Sao_Paulo")

# Auditoria (texto estável; os rótulos entram no dicionário do audit sem editar audit.py).
SUBSCRIBED = "subscription.created"
CANCELED = "subscription.canceled"
BILLING_INFO_UPDATED = "subscription.billing_info_updated"
TRIAL_EXTENDED = "subscription.trial_extended"
DISCOUNT_GRANTED = "subscription.discount_granted"
DOWNGRADE_CANCELED = "subscription.downgrade_canceled"
audit.ACTION_LABELS.update(
    {
        SUBSCRIBED: "Assinatura contratada",
        CANCELED: "Assinatura cancelada",
        BILLING_INFO_UPDATED: "Dados de cobrança atualizados",
        TRIAL_EXTENDED: "Teste grátis estendido",
        DISCOUNT_GRANTED: "Desconto concedido",
        DOWNGRADE_CANCELED: "Troca para plano menor não aplicada",
    }
)

STATUS_LABELS = {
    SUB_TRIALING: "Teste grátis",
    SUB_ACTIVE: "Ativa",
    SUB_PAST_DUE: "Pagamento em atraso",
    SUB_CANCELED: "Cancelada",
    SUB_EXPIRED: "Encerrada (modo leitura)",
    "implicit_trial": "Teste grátis",
}
STATUS_TONES = {
    SUB_TRIALING: "info",
    "implicit_trial": "info",
    SUB_ACTIVE: "success",
    SUB_PAST_DUE: "warning",
    SUB_CANCELED: "neutral",
    SUB_EXPIRED: "danger",
}
PAYMENT_LABELS = {
    "pending": "Aguardando pagamento",
    "confirmed": "Pago",
    "received": "Pago",
    "overdue": "Vencida",
    "refunded": "Estornada",
    "canceled": "Cancelada",
}
PAYMENT_TONES = {
    "pending": "info",
    "confirmed": "success",
    "received": "success",
    "overdue": "danger",
    "refunded": "neutral",
    "canceled": "neutral",
}

# Ordem natural de uma cobrança; evento com status "anterior" ao local = fora de ordem.
_RANK = {PAY_PENDING: 0, PAY_OVERDUE: 1, "confirmed": 2, "received": 3, PAY_REFUNDED: 4, PAY_CANCELED: 4}

MAX_DISCOUNT_PERCENT = 90
MIN_REASON_LENGTH = 5


class BillingError(Exception):
    """Regra de cobrança violada; ``message`` vai para a tela."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


# ------------------------------------------------------------------ tempo


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def local_date(value: datetime) -> date:
    return _aware(value).astimezone(TZ).date()


def end_of_day(day: date) -> datetime:
    """23:59:59 do dia em São Paulo, em UTC."""
    return datetime.combine(day, time(23, 59, 59), tzinfo=TZ).astimezone(timezone.utc)


def _setting(name: str):
    return current_app.config.get(name, entitlements.DEFAULTS.get(name))


# ------------------------------------------------------------------ provedor


def provider_name(app=None) -> str:
    app = app or current_app
    name = (app.config.get("BILLING_PROVIDER") or "").strip().lower()
    if not name:
        name = "asaas" if app.config.get("ASAAS_API_KEY") else "fake"
    return name


def get_provider(app=None) -> PaymentProvider:
    """Provedor do app (um por processo). Fake só em development/test."""
    app = app or current_app._get_current_object()  # type: ignore[attr-defined]
    provider = app.extensions.get("billing_provider")
    if provider is not None:
        return provider
    name = provider_name(app)
    if name == "asaas":
        provider = AsaasProvider(
            app.config.get("ASAAS_API_KEY") or "",
            app.config.get("ASAAS_BASE_URL") or None,
            timeout=(float(app.config.get("ASAAS_CONNECT_TIMEOUT", 5)), float(app.config.get("ASAAS_READ_TIMEOUT", 15))),
        )
    elif name == "fake":
        if app.config.get("ENV_NAME") not in {"development", "test"}:
            raise PaymentProviderError("Pagamento não configurado: defina ASAAS_API_KEY.")
        provider = FakeProvider(app.extensions.setdefault("billing_fake_store", FakeStore()))
    else:
        raise PaymentProviderError(f"Provedor de pagamento desconhecido: {name}.")
    app.extensions["billing_provider"] = provider
    return provider


# ------------------------------------------------------------------ assinatura local


def subscription_for(company_id: uuid.UUID) -> Subscription | None:
    return entitlements.subscription_for(company_id)


def ensure_subscription(company: Company) -> Subscription:
    """Assinatura da empresa; cria a de teste grátis (14 dias desde a criação da empresa,
    plano padrão) se ainda não houver — mesma regra do teste implícito de entitlements.
    A Fase 5 cria a assinatura ``trialing`` no cadastro; aqui é só a rede de segurança."""
    sub = subscription_for(company.id)
    if sub is not None:
        return sub
    plan = db.session.execute(select(Plan).where(Plan.code == _setting("DEFAULT_TRIAL_PLAN"))).scalar_one()
    created = _aware(company.created_at) or now_utc()
    sub = Subscription(
        company_id=company.id,
        plan_id=plan.id,
        provider=provider_name() if provider_name() == "fake" else "asaas",
        status=SUB_TRIALING,
        trial_ends_at=created + timedelta(days=int(_setting("TRIAL_DAYS"))),
    )
    sub.plan = plan
    db.session.add(sub)
    db.session.flush()
    return sub


def price_for(sub: Subscription, plan: Plan) -> int:
    discount = sub.discount_percent or 0
    return plan.price_cents * (100 - discount) // 100


def needs_checkout(sub: Subscription) -> bool:
    """Sem assinatura viva no provedor: escolher plano leva a dados de cobrança + checkout."""
    return not sub.provider_subscription_id or sub.status in (SUB_CANCELED, SUB_EXPIRED)


def payments_for(sub: Subscription) -> list[Payment]:
    return list(
        db.session.execute(
            select(Payment)
            .where(Payment.company_id == sub.company_id, Payment.subscription_id == sub.id)
            .order_by(Payment.due_date.desc(), Payment.created_at.desc())
        ).scalars()
    )


def open_payment(sub: Subscription) -> Payment | None:
    """Cobrança em aberto mais antiga (a que o cliente deve pagar primeiro)."""
    open_ = [p for p in payments_for(sub) if p.status in (PAY_PENDING, PAY_OVERDUE)]
    return min(open_, key=lambda p: p.due_date) if open_ else None


@dataclass(frozen=True)
class BillingInfo:
    name: str
    cpf_cnpj: str
    email: str

    def validated(self) -> "BillingInfo":
        name = (self.name or "").strip()
        email = (self.email or "").strip().lower()
        if not 2 <= len(name) <= 120:
            raise BillingError("Informe o nome ou a razão social (2 a 120 caracteres).")
        if not is_valid_document(self.cpf_cnpj):
            raise BillingError("CPF ou CNPJ inválido: confira os números.")
        if "@" not in email or len(email) > 254:
            raise BillingError("Informe um e-mail de cobrança válido.")
        return BillingInfo(name, only_digits(self.cpf_cnpj), email)


def _customer(company: Company, info: BillingInfo) -> CustomerData:
    return CustomerData(info.name, info.cpf_cnpj, info.email, str(company.id))


def _description(plan: Plan) -> str:
    return f"Controle de Produção — plano {plan.name}"


def check_plan_fits(company: Company, plan: Plan) -> None:
    """Trocar para um plano menor só se o uso atual couber (nada é apagado)."""
    projects = entitlements.count_active_projects(company.id)
    users = entitlements.count_users(company.id)
    if plan.max_projects is not None and projects > plan.max_projects:
        raise BillingError(
            f"O plano {plan.name} permite {plan.max_projects} projetos ativos e você tem {projects}. "
            f"Arquive ou conclua {projects - plan.max_projects} projeto(s) antes de trocar."
        )
    if plan.max_users is not None and users > plan.max_users:
        raise BillingError(
            f"O plano {plan.name} permite {plan.max_users} usuários e você tem {users} (com convites pendentes). "
            f"Desative ou revogue {users - plan.max_users} usuário(s)/convite(s) antes de trocar."
        )


# ------------------------------------------------------------------ ações do proprietário


def subscribe(company: Company, plan: Plan, info: BillingInfo, actor_user_id, now: datetime | None = None) -> str | None:
    """Cria cliente + assinatura no provedor e devolve a URL de pagamento da 1ª cobrança.

    Em teste grátis, a 1ª cobrança vence no último dia do teste (pode pagar antes). Depois
    de cancelada com período pago, vence no fim desse período. Nenhum dado de cartão passa
    por aqui: o cliente paga na página do provedor (``invoiceUrl``).

    Ordem: TODAS as chamadas ao provedor primeiro (cliente, assinatura, cobranças); só
    depois o estado local muda. Se o provedor falhar no meio, a transação é desfeita e só o
    ``provider_customer_id`` recém-criado é gravado, numa transação pequena e separada (para
    não duplicar o cliente na próxima tentativa); status e plano ficam como estavam."""
    now = now or now_utc()
    info = info.validated()  # de novo: o serviço não confia no formulário
    if not plan.active:
        raise BillingError("Plano indisponível.")
    sub = ensure_subscription(company)
    if not needs_checkout(sub):
        raise BillingError("Sua assinatura já está ativa: use “Trocar plano”.")
    check_plan_fits(company, plan)
    provider = get_provider()
    data = _customer(company, info)
    start = local_date(now)
    if sub.status == SUB_TRIALING and sub.trial_ends_at and _aware(sub.trial_ends_at) > now:
        start = max(start, local_date(sub.trial_ends_at))
    if sub.status == SUB_CANCELED and sub.current_period_end and _aware(sub.current_period_end) > now:
        start = max(start, local_date(sub.current_period_end))
    value = price_for(sub, plan)

    customer_id = sub.provider_customer_id if sub.provider == provider.name else None
    created_customer = None
    try:
        if customer_id:
            provider.update_customer(customer_id, data)
        else:
            customer_id = created_customer = provider.create_customer(data)
        remote = provider.create_subscription(customer_id, value, start, _description(plan), str(company.id))
        remote_payments = provider.list_payments(remote.id)
    except PaymentProviderError:
        db.session.rollback()
        if created_customer:
            _save_customer_only(company, provider.name, created_customer)
        raise

    # Provedor ok: agora o estado local.
    sub.provider = provider.name
    sub.provider_customer_id = customer_id
    sub.provider_subscription_id = remote.id
    covered = sub.status == SUB_TRIALING or (
        sub.status == SUB_CANCELED and sub.current_period_end is not None and _aware(sub.current_period_end) > now
    )
    if covered and is_upgrade(sub, plan):
        # Teste/período pago no plano atual: o plano mais caro só vale com a fatura paga.
        sub.pending_plan_id, sub.pending_plan_at = plan.id, now
    else:
        sub.plan_id, sub.plan = plan.id, plan
        sub.pending_plan_id = sub.pending_plan_at = None
    if sub.status == SUB_CANCELED:
        # Volta a assinar: sem nada pago, retoma o teste (se ainda vale); com período pago,
        # ``recompute`` decide entre ativa, em atraso ou encerrada.
        never_paid = not any(p.status in PAID_STATUSES for p in payments_for(sub))
        if never_paid and sub.trial_ends_at and _aware(sub.trial_ends_at) > now:
            sub.status = SUB_TRIALING
            sub.current_period_end = None
        else:
            sub.status = SUB_ACTIVE if not never_paid else SUB_EXPIRED
        sub.canceled_at = None
    _sync_payments(sub, remote_payments)
    recompute(sub, now)
    audit.record(
        SUBSCRIBED,
        company_id=company.id,
        actor_user_id=actor_user_id,
        object_type="subscription",
        object_id=sub.id,
        details={"plano": plan.code, "valor_centavos": value, "primeiro_vencimento": start.isoformat()},
    )
    db.session.flush()
    payment = open_payment(sub)
    return payment.invoice_url if payment else None


def _save_customer_only(company: Company, provider_name_: str, customer_id: str) -> None:
    """Transação própria e mínima: só o id do cliente criado no provedor."""
    try:
        rls.set_context(company_id=company.id)
        sub = ensure_subscription(db.session.get(Company, company.id))
        sub.provider = provider_name_
        sub.provider_customer_id = customer_id
        db.session.commit()
    except Exception as exc:  # noqa: BLE001 - não mascara o erro do provedor
        db.session.rollback()
        logger.error("não foi possível guardar o cliente do provedor (%s)", exc.__class__.__name__)


def update_billing_info(company: Company, info: BillingInfo, actor_user_id) -> None:
    info = info.validated()
    sub = ensure_subscription(company)
    if not sub.provider_customer_id:
        raise BillingError("Ainda não há dados de cobrança: escolha um plano para assinar.")
    get_provider().update_customer(sub.provider_customer_id, _customer(company, info))
    audit.record(
        BILLING_INFO_UPDATED,
        company_id=company.id,
        actor_user_id=actor_user_id,
        object_type="subscription",
        object_id=sub.id,
        details={"documento": "CNPJ" if len(info.cpf_cnpj) == 14 else "CPF"},
    )


def is_upgrade(sub: Subscription, plan: Plan) -> bool:
    return price_for(sub, plan) > price_for(sub, sub.plan)


def downgrade_effective_at(sub: Subscription, now: datetime) -> datetime:
    """Rebaixar vale no fim do que já está pago (período pago ou teste grátis)."""
    candidates = [_aware(sub.current_period_end), _aware(sub.trial_ends_at) if sub.status == SUB_TRIALING else None]
    future = [c for c in candidates if c is not None and c > now]
    return max(future) if future else now


def projection(company: Company, new_plan: Plan, now: datetime | None = None) -> dict:
    """Projeção da troca: valor mensal atual × novo, quando passa a valer e quanto custa."""
    now = now or now_utc()
    sub = ensure_subscription(company)
    current = price_for(sub, sub.plan)
    new = price_for(sub, new_plan)
    payment = open_payment(sub)
    if payment is not None:
        next_due = payment.due_date
    elif sub.current_period_end:
        next_due = local_date(sub.current_period_end)
    elif sub.trial_ends_at:
        next_due = local_date(sub.trial_ends_at)
    else:
        next_due = None
    upgrade = new > current
    return {
        "plan": new_plan,
        "current_plan": sub.plan,
        "current_cents": current,
        "new_cents": new,
        "difference_cents": new - current,
        "next_due": next_due,
        "upgrade": upgrade,
        # upgrade: vale quando a fatura no valor novo for paga; downgrade: no fim do período.
        "effective_at": None if upgrade else downgrade_effective_at(sub, now),
        "blocked": "Pagamento em atraso: regularize antes de trocar de plano." if sub.status == SUB_PAST_DUE else None,
        "discount_percent": sub.discount_percent or 0,
        "checkout": needs_checkout(sub),
        "projects": entitlements.count_active_projects(company.id),
        "users": entitlements.count_users(company.id),
    }


def change_plan(company: Company, new_plan: Plan, actor_user_id, now: datetime | None = None) -> Subscription:
    """Pede a troca de plano. Os limites NÃO mudam de graça:

    - upgrade (mais caro): o provedor passa a cobrar o valor novo já na fatura em aberto; o
      plano novo fica em ``pending_plan_id`` e só vira o plano da empresa quando uma fatura no
      valor novo for paga (``recompute``) — limites sobem na requisição seguinte ao pagamento;
    - downgrade (mais barato): vale no fim do período pago/teste (``pending_plan_at``);
    - bloqueado com pagamento em atraso, cancelada ou encerrada."""
    now = now or now_utc()
    sub = ensure_subscription(company)
    if not new_plan.active:
        raise BillingError("Plano indisponível.")
    if sub.status in (SUB_CANCELED, SUB_EXPIRED):
        raise BillingError("Assinatura encerrada: escolha o plano e assine de novo.")
    if sub.status == SUB_PAST_DUE:
        raise BillingError("Pagamento em atraso: regularize a fatura antes de trocar de plano.")
    if new_plan.id == sub.plan_id:
        if sub.pending_plan_id is None:
            raise BillingError("Esse já é o seu plano.")
    else:
        check_plan_fits(company, new_plan)
    upgrade = is_upgrade(sub, new_plan)
    if sub.provider_subscription_id:
        provider = get_provider()
        provider.change_plan(sub.provider_subscription_id, price_for(sub, new_plan), _description(new_plan))
        remote = provider.list_payments(sub.provider_subscription_id)
        _sync_payments(sub, remote)
    old_plan = sub.plan
    if new_plan.id == sub.plan_id:
        sub.pending_plan_id = sub.pending_plan_at = None  # desistiu da troca pendente
        when = "desfeita"
    elif upgrade:
        sub.pending_plan_id, sub.pending_plan_at = new_plan.id, now
        when = "após o pagamento"
    else:
        sub.pending_plan_id, sub.pending_plan_at = new_plan.id, downgrade_effective_at(sub, now)
        when = sub.pending_plan_at.isoformat()
    apply_pending_plan(sub, now)
    audit.record(
        audit.PLAN_CHANGED,
        company_id=company.id,
        actor_user_id=actor_user_id,
        object_type="subscription",
        object_id=sub.id,
        details={"de": old_plan.code, "para": new_plan.code, "vale": when},
    )
    db.session.flush()
    return sub


def apply_pending_plan(sub: Subscription, now: datetime | None = None) -> bool:
    """Efetiva a troca pendente: upgrade quando houver fatura paga no valor novo depois do
    pedido; downgrade quando chegar ``pending_plan_at``. True = aplicou."""
    if sub.pending_plan_id is None:
        return False
    now = now or now_utc()
    plan = db.session.get(Plan, sub.pending_plan_id)
    if plan is None:  # pragma: no cover - FK impede
        sub.pending_plan_id = sub.pending_plan_at = None
        return False
    since = _aware(sub.pending_plan_at) or now
    if price_for(sub, plan) > price_for(sub, sub.plan):
        since_day = local_date(since)
        ready = any(
            p.status in PAID_STATUSES
            and p.value_cents >= price_for(sub, plan)
            and p.paid_at is not None
            and local_date(p.paid_at) >= since_day
            for p in payments_for(sub)
        )
    else:
        ready = since <= now
        if ready:
            company = db.session.get(Company, sub.company_id)
            try:
                check_plan_fits(company, plan)
            except BillingError as exc:
                return _abort_downgrade(sub, company, plan, exc.message)
    if ready:
        sub.plan_id, sub.plan = plan.id, plan
        sub.pending_plan_id = sub.pending_plan_at = None
    return ready


def cancel(company: Company, actor_user_id, now: datetime | None = None) -> Subscription:
    """Cancela a recorrência. O acesso completo continua até o fim do período pago (ou do
    teste grátis); depois, modo leitura. Nada é apagado."""
    now = now or now_utc()
    sub = ensure_subscription(company)
    if sub.status in (SUB_CANCELED, SUB_EXPIRED):
        raise BillingError("A assinatura já está cancelada.")
    if sub.provider_subscription_id:
        get_provider().cancel(sub.provider_subscription_id)
    for payment in payments_for(sub):
        if payment.status in (PAY_PENDING, PAY_OVERDUE):
            payment.status = PAY_CANCELED  # o provedor remove as cobranças em aberto
    _mark_canceled(sub, now)
    recompute(sub, now)
    audit.record(
        CANCELED,
        company_id=company.id,
        actor_user_id=actor_user_id,
        object_type="subscription",
        object_id=sub.id,
        details={"acesso_ate": _aware(sub.current_period_end).isoformat() if sub.current_period_end else None},
    )
    db.session.flush()
    return sub


def _mark_canceled(sub: Subscription, now: datetime) -> None:
    if sub.status == SUB_TRIALING and not any(p.status in PAID_STATUSES for p in payments_for(sub)):
        sub.current_period_end = sub.trial_ends_at
    sub.status = SUB_CANCELED
    sub.canceled_at = sub.canceled_at or now
    sub.grace_until = None
    sub.pending_plan_id = sub.pending_plan_at = None


def _abort_downgrade(sub: Subscription, company: Company, plan: Plan, reason: str) -> bool:
    """Downgrade agendado que não cabe mais no uso atual: NÃO aplica. Mantém plano e preço
    atuais (o valor no provedor volta ao do plano atual), limpa o pendente, audita e avisa
    os proprietários. Se o provedor falhar, o pendente fica para a próxima tentativa."""
    if sub.provider_subscription_id and not needs_checkout(sub):
        provider = get_provider()
        try:
            provider.change_plan(sub.provider_subscription_id, price_for(sub, sub.plan), _description(sub.plan))
            _sync_payments(sub, provider.list_payments(sub.provider_subscription_id))
        except PaymentProviderError as exc:
            logger.error("downgrade não aplicado; falha ao restaurar valor no provedor: %s", exc.message)
            return False
    sub.pending_plan_id = sub.pending_plan_at = None
    audit.record(
        DOWNGRADE_CANCELED,
        company_id=company.id,
        actor_user_id=None,
        object_type="subscription",
        object_id=sub.id,
        details={"plano_mantido": sub.plan.code, "plano_recusado": plan.code, "motivo": reason},
    )
    notify.downgrade_canceled(company, sub.plan, plan, reason)
    return False


# ------------------------------------------------------------------ cobranças e estado


def _sync_payments(sub: Subscription, remote: list[ProviderPayment]) -> int:
    """Grava as cobranças do provedor como estão lá (fonte de verdade). Devolve mudanças."""
    changed = 0
    for item in remote:
        changed += _upsert_payment(sub, item, trust=True)
    return changed


def _find_payment(provider_payment_id: str) -> Payment | None:
    return db.session.execute(
        select(Payment).where(Payment.provider_payment_id == provider_payment_id)
    ).scalar_one_or_none()


def _upsert_payment(sub: Subscription, item: ProviderPayment, *, trust: bool) -> int:
    """``trust=False`` (webhook): status que regride ou conflita com o local é conferido no
    provedor antes de valer (evento fora de ordem)."""
    if not item.id:
        return 0
    payment = _find_payment(item.id)
    if payment is not None and payment.company_id != sub.company_id:  # pragma: no cover - defesa
        logger.error("cobrança %s pertence a outra empresa: ignorada", item.id)
        return 0
    if payment is not None and not trust and item.status != payment.status:
        if _RANK.get(item.status, 0) <= _RANK.get(payment.status, 0):
            fresh = _ask_provider(item)
            if fresh is None or fresh.status == payment.status:
                return 0
            item = fresh
    if payment is None:
        payment = Payment(
            company_id=sub.company_id,
            subscription_id=sub.id,
            provider_payment_id=item.id,
            status=item.status,
            value_cents=item.value_cents,
            due_date=item.due_date,
            paid_at=item.paid_at,
            invoice_url=item.invoice_url,
        )
        db.session.add(payment)
        db.session.flush()
        return 1
    wanted = {
        "status": item.status,
        "value_cents": item.value_cents,
        "due_date": item.due_date,
        "paid_at": item.paid_at if item.status in PAID_STATUSES and item.paid_at else _aware(payment.paid_at),
        "invoice_url": item.invoice_url or payment.invoice_url,
    }
    changed = 0
    for key, value in wanted.items():
        current = _aware(getattr(payment, key)) if key == "paid_at" else getattr(payment, key)
        if current != value:
            setattr(payment, key, value)
            changed = 1
    return changed


def _ask_provider(item: ProviderPayment) -> ProviderPayment | None:
    if not item.subscription_id:
        return None
    for remote in get_provider().list_payments(item.subscription_id):
        if remote.id == item.id:
            return remote
    return None


def recompute(sub: Subscription, now: datetime | None = None) -> tuple[str, str]:
    """Recalcula status, ``current_period_end`` e ``grace_until`` a partir das cobranças.
    Idempotente e independente da ordem dos eventos. Avisa por e-mail ao entrar em atraso."""
    now = now or now_utc()
    old_status = sub.status
    if sub.status not in (SUB_CANCELED, SUB_EXPIRED):
        apply_pending_plan(sub, now)
    payments = payments_for(sub)
    paid = [p for p in payments if p.status in PAID_STATUSES]
    refunded = any(p.status == PAY_REFUNDED for p in payments)
    overdue = sorted((p for p in payments if p.status == PAY_OVERDUE), key=lambda p: p.due_date)
    pending = [p for p in payments if p.status == PAY_PENDING]
    grace_days = timedelta(days=int(_setting("PAST_DUE_GRACE_DAYS")))
    paid_end = max((end_of_day(add_months(p.due_date, 1)) for p in paid), default=None)

    if sub.status == SUB_CANCELED:
        if paid_end is not None:
            sub.current_period_end = paid_end
        elif refunded:
            sub.current_period_end = min(_aware(sub.canceled_at) or now, now)
        end = _aware(sub.current_period_end)
        if end is None or end <= now:
            sub.status = SUB_EXPIRED
        return old_status, sub.status

    if paid_end is not None or refunded:
        sub.current_period_end = paid_end
    if paid_end is not None and paid_end > now:
        sub.status, sub.grace_until = SUB_ACTIVE, None
    elif overdue:
        sub.grace_until = end_of_day(overdue[0].due_date) + grace_days
        sub.status = SUB_PAST_DUE if now <= sub.grace_until else SUB_EXPIRED
    elif paid_end is not None:
        # Período pago acabou e o provedor ainda não avisou o vencimento da próxima.
        sub.grace_until = paid_end + grace_days
        sub.status = SUB_PAST_DUE if now <= sub.grace_until else SUB_EXPIRED
    elif sub.status == SUB_TRIALING:
        trial_end = _aware(sub.trial_ends_at)
        if trial_end is not None and trial_end <= now and not pending:
            sub.status = SUB_EXPIRED
    elif sub.status != SUB_EXPIRED:
        sub.status, sub.grace_until = SUB_EXPIRED, None  # nada pago (ex.: tudo estornado)

    if sub.status == SUB_PAST_DUE and old_status != SUB_PAST_DUE:
        company = db.session.get(Company, sub.company_id)
        notify.past_due(company, sub.grace_until)
    return old_status, sub.status


# ------------------------------------------------------------------ webhook


def find_by_provider_subscription(provider_subscription_id: str) -> Subscription | None:
    """Acha a assinatura pelo id do provedor ANTES de saber a empresa.

    Com RLS ligado, ``subscriptions`` só mostra linhas de ``app.company_id``. A política
    ``subscriptions_provider_lookup`` (migration da Fase 8) libera SELECT da linha cujo
    ``provider_subscription_id`` é igual a ``app.billing_lookup`` — quem não sabe o id do
    provedor não lê nada. A variável vale só nesta transação e é limpa logo depois; achada a
    assinatura, o contexto passa a ser a empresa dela."""
    is_pg = db.session.get_bind().dialect.name == "postgresql"
    if is_pg:
        db.session.execute(text("SELECT set_config('app.billing_lookup', :v, true)"), {"v": provider_subscription_id})
    try:
        sub = db.session.execute(
            select(Subscription).where(Subscription.provider_subscription_id == provider_subscription_id)
        ).scalar_one_or_none()
    finally:
        if is_pg:
            db.session.execute(text("SELECT set_config('app.billing_lookup', '', true)"))
    if sub is not None:
        rls.set_context(company_id=sub.company_id)
    return sub


SUBSCRIPTION_END_EVENTS = {"SUBSCRIPTION_DELETED", "SUBSCRIPTION_INACTIVATED"}


def handle_webhook(payload: dict, now: datetime | None = None) -> tuple[str, uuid.UUID | None]:
    """Processa um evento do Asaas já registrado em ``webhook_events``.
    Devolve (``processed`` | ``ignored``, company_id)."""
    now = now or now_utc()
    event = str(payload.get("event") or "")
    payment_obj = payload.get("payment") if isinstance(payload.get("payment"), dict) else None
    subscription_obj = payload.get("subscription") if isinstance(payload.get("subscription"), dict) else None

    if event.startswith("PAYMENT_") and payment_obj:
        remote = map_payment(payment_obj)
        if not remote.subscription_id:
            return "ignored", None  # cobrança avulsa: não é nossa assinatura
        sub = find_by_provider_subscription(remote.subscription_id)
        if sub is None:
            return "ignored", None
        _upsert_payment(sub, remote, trust=False)
        recompute(sub, now)
        return "processed", sub.company_id

    if event in SUBSCRIPTION_END_EVENTS and subscription_obj and subscription_obj.get("id"):
        sub = find_by_provider_subscription(str(subscription_obj["id"]))
        if sub is None:
            return "ignored", None
        if sub.status not in (SUB_CANCELED, SUB_EXPIRED):
            # Pode ser eco do nosso próprio cancelamento ou cancelamento pelo painel do Asaas.
            remote = get_provider().get_subscription(sub.provider_subscription_id)
            if remote is None or not remote.active:
                _mark_canceled(sub, now)
                recompute(sub, now)
        return "processed", sub.company_id

    return "ignored", None


# ------------------------------------------------------------------ reconciliação


def reconcile_subscription(sub: Subscription, now: datetime | None = None) -> bool:
    """Alinha uma assinatura com o provedor e recalcula o estado. True = algo mudou."""
    now = now or now_utc()
    before = (sub.status, _aware(sub.current_period_end), _aware(sub.grace_until))
    changed = 0
    provider = get_provider()
    if sub.provider_subscription_id and sub.provider == provider.name:
        remote = provider.get_subscription(sub.provider_subscription_id)
        if (remote is None or not remote.active) and sub.status not in (SUB_CANCELED, SUB_EXPIRED):
            _mark_canceled(sub, now)
            changed += 1
        changed += _sync_payments(sub, provider.list_payments(sub.provider_subscription_id))
    recompute(sub, now)
    after = (sub.status, _aware(sub.current_period_end), _aware(sub.grace_until))
    return bool(changed) or before != after


def reconcile_all(now: datetime | None = None) -> dict:
    """Todas as empresas, uma transação por empresa (contexto RLS dela)."""
    now = now or now_utc()
    result = {"checked": 0, "changed": 0, "errors": 0}
    company_ids = list(db.session.execute(select(Company.id).order_by(Company.created_at)).scalars())
    for company_id in company_ids:
        rls.set_context(company_id=company_id)
        sub = subscription_for(company_id)
        if sub is None:
            continue
        result["checked"] += 1
        try:
            if reconcile_subscription(sub, now):
                result["changed"] += 1
            db.session.commit()
        except PaymentProviderError as exc:
            db.session.rollback()
            result["errors"] += 1
            logger.error("reconciliação da empresa %s falhou: %s", company_id, exc.message)
    rls.set_context(company_id=None)
    return result


# ------------------------------------------------------------------ admin da plataforma


def _reason(reason: str | None) -> str:
    reason = (reason or "").strip()
    if len(reason) < MIN_REASON_LENGTH:
        raise BillingError(f"Motivo obrigatório (mínimo {MIN_REASON_LENGTH} caracteres).")
    return reason[:500]


def admin_extend_trial(company: Company, days: int, reason: str, now: datetime | None = None) -> Subscription:
    now = now or now_utc()
    reason = _reason(reason)
    if not 1 <= days <= 90:
        raise BillingError("Dias entre 1 e 90.")
    sub = ensure_subscription(company)
    if sub.status not in (SUB_TRIALING, SUB_EXPIRED) or any(p.status in PAID_STATUSES for p in payments_for(sub)):
        raise BillingError("Só dá para estender o teste grátis de quem ainda não pagou nenhuma mensalidade.")
    base = max(_aware(sub.trial_ends_at) or now, now)
    sub.trial_ends_at = base + timedelta(days=days)
    sub.status = SUB_TRIALING
    sub.grace_until = None
    audit.record(
        TRIAL_EXTENDED,
        company_id=company.id,
        actor_user_id=None,
        object_type="subscription",
        object_id=sub.id,
        details={"motivo": reason, "dias": days, "novo_fim": sub.trial_ends_at.isoformat(), "por": "admin da plataforma"},
    )
    db.session.flush()
    return sub


def admin_discount(company: Company, percent: int, reason: str) -> Subscription:
    reason = _reason(reason)
    if not 0 <= percent <= MAX_DISCOUNT_PERCENT:
        raise BillingError(f"Desconto entre 0 e {MAX_DISCOUNT_PERCENT}%.")
    sub = ensure_subscription(company)
    old = sub.discount_percent or 0
    sub.discount_percent = percent or None
    if sub.provider_subscription_id and not needs_checkout(sub):
        provider = get_provider()
        provider.change_plan(sub.provider_subscription_id, price_for(sub, sub.plan), _description(sub.plan))
        _sync_payments(sub, provider.list_payments(sub.provider_subscription_id))
    audit.record(
        DISCOUNT_GRANTED,
        company_id=company.id,
        actor_user_id=None,
        object_type="subscription",
        object_id=sub.id,
        details={"motivo": reason, "de_percentual": old, "para_percentual": percent, "por": "admin da plataforma"},
    )
    db.session.flush()
    return sub


# ------------------------------------------------------------------ faixa de aviso


def banner(company: Company, now: datetime | None = None) -> dict | None:
    """Aviso no topo do /app: teste grátis, atraso (carência) ou cancelamento agendado.
    Modo leitura já tem o aviso próprio do layout."""
    now = now or now_utc()
    acc = entitlements.access(company, now)
    if not acc.writable:
        return None
    sub = subscription_for(company.id)
    until = acc.until
    if acc.status in ("implicit_trial", SUB_TRIALING):
        if sub is not None and sub.provider_subscription_id:
            return None  # já assinou durante o teste
        days = max(0, math.ceil((until - now).total_seconds() / 86400)) if until else None
        body = "Escolha um plano para continuar depois do teste. Pix, boleto ou cartão."
        title = f"Teste grátis: falta{'m' if days != 1 else ''} {days} dia{'s' if days != 1 else ''}." if days is not None else "Teste grátis."
        return {"kind": "info", "title": title, "body": body, "action_label": "Escolher plano"}
    if acc.status == SUB_PAST_DUE:
        when = local_date(until).strftime("%d/%m/%Y") if until else "—"
        return {
            "kind": "warning",
            "title": "Pagamento em atraso.",
            "body": f"Regularize até {when} para não entrar em modo leitura. Nenhum dado é apagado.",
            "action_label": "Pagar agora",
        }
    if acc.status == SUB_CANCELED:
        when = local_date(until).strftime("%d/%m/%Y") if until else "—"
        return {
            "kind": "info",
            "title": "Assinatura cancelada.",
            "body": f"Acesso completo até {when}; depois, modo leitura (seus dados continuam guardados).",
            "action_label": "Assinar de novo",
        }
    return None
