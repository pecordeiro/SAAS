"""Limites de plano e modo leitura (regra inviolável 7: checado no backend).

Plano efetivo da empresa:
- com assinatura (``subscriptions``): o plano dela;
- sem assinatura nenhuma: teste grátis implícito de ``TRIAL_DAYS`` dias contados da criação
  da empresa, no plano ``DEFAULT_TRIAL_PLAN`` (o cadastro ainda não cria assinatura; a
  Fase 8 passa a criar a de verdade).

Escrita liberada (``writable``) quando a assinatura está:
- ``trialing`` com ``trial_ends_at`` no futuro (ou sem data);
- ``active``;
- ``past_due`` dentro da carência (``grace_until``; sem ela, ``current_period_end`` +
  ``PAST_DUE_GRACE_DAYS``);
- ``canceled`` até o fim do período pago (``current_period_end``).
Fora disso (``expired``, carência vencida, teste vencido) a empresa fica em MODO LEITURA:
toda escrita responde 402 e a leitura continua liberada. ``READ_ONLY_ENFORCED=False`` desliga
o modo leitura (regra configurável); os limites de quantidade continuam valendo.

Limites (NULL no plano = ilimitado):
- ``max_projects``: projetos ativos = não arquivados e não concluídos;
- ``max_users``: vínculos ativos + convites pendentes (não usados, não revogados, no prazo).
Pontos de criação chamam ``check_can_create_project`` / ``check_can_add_user`` (a Fase 5
chama o segundo ao convidar e ao aceitar convite).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from flask import current_app, has_app_context
from sqlalchemy import func, select

from app.extensions import db
from app.models import PROJECT_ACTIVE, Company, Invitation, Membership, Plan, Project, Subscription
from app.models.billing import SUB_ACTIVE, SUB_CANCELED, SUB_PAST_DUE, SUB_TRIALING

DEFAULTS = {
    "READ_ONLY_ENFORCED": True,
    "TRIAL_DAYS": 14,
    "DEFAULT_TRIAL_PLAN": "profissional",
    "PAST_DUE_GRACE_DAYS": 7,
}

UPGRADE_HINT = "Arquive um projeto ou mude de plano."


class EntitlementError(Exception):
    """Ação bloqueada pelo plano/assinatura. Vira HTTP 402 com mensagem amigável."""

    status_code = 402
    title = "Limite do plano"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class PlanLimitError(EntitlementError):
    title = "Limite do plano atingido"


class ReadOnlyError(EntitlementError):
    title = "Assinatura em modo leitura"


@dataclass(frozen=True)
class Access:
    plan: Plan
    status: str  # status da assinatura ou "implicit_trial"
    writable: bool
    until: datetime | None  # até quando a escrita está garantida (None = sem data)


def _setting(name: str):
    if has_app_context():
        return current_app.config.get(name, DEFAULTS[name])
    return DEFAULTS[name]  # pragma: no cover - sempre há contexto no app


def _aware(value: datetime | None) -> datetime | None:
    """SQLite devolve datetime sem fuso; tudo aqui é UTC."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def subscription_for(company_id: uuid.UUID) -> Subscription | None:
    return db.session.execute(
        select(Subscription).where(Subscription.company_id == company_id)
    ).scalar_one_or_none()


def _plan_by_code(code: str) -> Plan:
    return db.session.execute(select(Plan).where(Plan.code == code)).scalar_one()


def access(company: Company, now: datetime | None = None) -> Access:
    now = now or datetime.now(timezone.utc)
    sub = subscription_for(company.id)
    if sub is None:
        until = _aware(company.created_at) + timedelta(days=int(_setting("TRIAL_DAYS")))
        return Access(_plan_by_code(_setting("DEFAULT_TRIAL_PLAN")), "implicit_trial", now < until, until)
    if sub.status == SUB_TRIALING:
        until = _aware(sub.trial_ends_at)
    elif sub.status == SUB_ACTIVE:
        return Access(sub.plan, sub.status, True, _aware(sub.current_period_end))
    elif sub.status == SUB_PAST_DUE:
        until = _aware(sub.grace_until)
        if until is None and sub.current_period_end is not None:
            until = _aware(sub.current_period_end) + timedelta(days=int(_setting("PAST_DUE_GRACE_DAYS")))
        if until is None:
            return Access(sub.plan, sub.status, False, None)
    elif sub.status == SUB_CANCELED:
        until = _aware(sub.current_period_end)
        if until is None:
            return Access(sub.plan, sub.status, False, None)
    else:  # expired
        return Access(sub.plan, sub.status, False, None)
    return Access(sub.plan, sub.status, until is None or now < until, until)


def effective_plan(company: Company) -> Plan:
    return access(company).plan


def is_read_only(company: Company, now: datetime | None = None) -> bool:
    if not _setting("READ_ONLY_ENFORCED"):
        return False
    return not access(company, now).writable


def ensure_writable(company: Company) -> None:
    if is_read_only(company):
        raise ReadOnlyError(
            "Sua assinatura está em modo leitura: dá para ver e exportar tudo, mas não gravar. "
            "Regularize a assinatura para voltar a registrar."
        )


def count_active_projects(company_id: uuid.UUID) -> int:
    return db.session.execute(
        select(func.count())
        .select_from(Project)
        .where(Project.company_id == company_id, Project.archived_at.is_(None), Project.status == PROJECT_ACTIVE)
    ).scalar_one()


def count_users(company_id: uuid.UUID, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    members = db.session.execute(
        select(func.count())
        .select_from(Membership)
        .where(Membership.company_id == company_id, Membership.active.is_(True), Membership.is_support.is_(False))
    ).scalar_one()
    pending = db.session.execute(
        select(func.count())
        .select_from(Invitation)
        .where(
            Invitation.company_id == company_id,
            Invitation.used_at.is_(None),
            Invitation.revoked_at.is_(None),
            Invitation.expires_at > now,
        )
    ).scalar_one()
    return members + pending


def check_can_create_project(company: Company, adding: int = 1) -> None:
    plan = effective_plan(company)
    if plan.max_projects is None:
        return
    if count_active_projects(company.id) + adding > plan.max_projects:
        raise PlanLimitError(
            f"Seu plano {plan.name} permite {plan.max_projects} projetos ativos. {UPGRADE_HINT}"
        )


def check_can_add_user(company: Company, adding: int = 1) -> None:
    plan = effective_plan(company)
    if plan.max_users is None:  # pragma: no cover - todos os planos do catálogo têm limite
        return
    if count_users(company.id) + adding > plan.max_users:
        raise PlanLimitError(
            f"Seu plano {plan.name} permite {plan.max_users} usuários (contando convites pendentes). "
            "Remova alguém ou mude de plano."
        )


def has_feature(company: Company, name: str) -> bool:
    return bool((effective_plan(company).features or {}).get(name))


def require_feature(company: Company, name: str, label: str) -> None:
    if not has_feature(company, name):
        raise PlanLimitError(f"{label} não está disponível no plano {effective_plan(company).name}.")


def usage(company: Company) -> dict:
    """Uso atual × limites, para telas (“2 de 3 projetos”)."""
    acc = access(company)
    return {
        "plan": acc.plan,
        "status": acc.status,
        "writable": acc.writable or not _setting("READ_ONLY_ENFORCED"),
        "until": acc.until,
        "projects": count_active_projects(company.id),
        "max_projects": acc.plan.max_projects,
        "users": count_users(company.id),
        "max_users": acc.plan.max_users,
    }
