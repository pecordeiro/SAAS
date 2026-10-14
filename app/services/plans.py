"""Catálogo de planos (fonte única para `flask seed-plans`, para a migration da Etapa B e
para os testes).

Quatro planos (decisões D2–D4 do PRD, Etapa B):

- ``essencial`` — R$ 249,90/mês, 3 projetos ativos, 3 pessoas, teste grátis;
- ``profissional`` — R$ 497,00/mês, 10 projetos ativos, 20 pessoas, teste grátis (plano do
  cadastro novo);
- ``empresa`` — R$ 997,00/mês, ilimitado, MFA obrigatório, API e identidade visual
  personalizada; SEM teste grátis (cobrança imediata no checkout);
- ``implantacao`` — sob consulta (``price_cents`` NULL): tudo do Empresa + implantação por
  técnicos nossos. Não entra no autosserviço; só ``flask billing-admin set-plan`` atribui.

As migrations ``a7c2d4e8f901`` (3 planos antigos) e ``b1e7c9d2a4f6`` (Etapa B) gravam os
mesmos ids (uuid5 do código); `flask seed-plans` é idempotente e sincroniza preço/limites.
Limite NULL = ilimitado. Preço NULL = sob consulta (sem checkout).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select

from app.extensions import db
from app.models import Plan

# Namespace fixo: o id do plano é derivado do código e é igual em todo ambiente.
PLAN_NAMESPACE = uuid.UUID("6f1d3c3e-2b7a-4c55-9a43-6d1f0c2a9e10")

ESSENCIAL = "essencial"
PROFISSIONAL = "profissional"
EMPRESA = "empresa"
IMPLANTACAO = "implantacao"

# Só estes planos têm teste grátis (regra de negócio, checada no backend).
TRIAL_PLAN_CODES = frozenset({ESSENCIAL, PROFISSIONAL})

FEATURE_KEYS = ("mfa_required", "api", "visual_custom", "implantacao")


@dataclass(frozen=True)
class PlanSpec:
    code: str
    name: str
    price_cents: int | None
    max_projects: int | None
    max_users: int | None
    features: dict = field(default_factory=dict)

    @property
    def id(self) -> uuid.UUID:
        return uuid.uuid5(PLAN_NAMESPACE, self.code)


def _features(**on: bool) -> dict:
    return {key: bool(on.get(key, False)) for key in FEATURE_KEYS}


PLAN_CATALOG: tuple[PlanSpec, ...] = (
    PlanSpec(ESSENCIAL, "Essencial", 24990, 3, 3, _features()),
    PlanSpec(PROFISSIONAL, "Profissional", 49700, 10, 20, _features()),
    PlanSpec(EMPRESA, "Empresa", 99700, None, None, _features(mfa_required=True, api=True, visual_custom=True)),
    PlanSpec(
        IMPLANTACAO,
        "Implantação",
        None,
        None,
        None,
        _features(mfa_required=True, api=True, visual_custom=True, implantacao=True),
    ),
)


def has_trial(plan: Plan) -> bool:
    """Plano com teste grátis (só Essencial e Profissional)."""
    return plan.code in TRIAL_PLAN_CODES


def is_self_service(plan: Plan) -> bool:
    """Pode ser contratado pela tela (ativo e com preço). Sob consulta (preço NULL) ou com
    implantação: só a equipe da plataforma atribui (``billing-admin set-plan``)."""
    return bool(plan.active) and plan.price_cents is not None and not (plan.features or {}).get("implantacao")


def is_managed(plan: Plan) -> bool:
    """Contrato fora do autosserviço (sob consulta): sem cobrança recorrente no provedor."""
    return plan.price_cents is None or bool((plan.features or {}).get("implantacao"))


def active_plans() -> list[Plan]:
    """Planos ativos em ordem de preço; sob consulta (preço NULL) por último."""
    plans = db.session.execute(select(Plan).where(Plan.active.is_(True))).scalars()
    return sorted(plans, key=lambda p: (p.price_cents is None, p.price_cents or 0, p.code))


def seed_plans() -> tuple[int, int]:
    """Cria ou atualiza os planos do catálogo. Devolve (criados, atualizados). Não faz commit."""
    created = updated = 0
    for spec in PLAN_CATALOG:
        plan = db.session.execute(select(Plan).where(Plan.code == spec.code)).scalar_one_or_none()
        values = {
            "name": spec.name,
            "price_cents": spec.price_cents,
            "max_projects": spec.max_projects,
            "max_users": spec.max_users,
            "features": dict(spec.features),
            "active": True,
        }
        if plan is None:
            db.session.add(Plan(id=spec.id, code=spec.code, **values))
            created += 1
            continue
        changed = False
        for key, value in values.items():
            if getattr(plan, key) != value:
                setattr(plan, key, value)
                changed = True
        if changed:
            updated += 1
    db.session.flush()
    return created, updated


def get_plan(code: str) -> Plan:
    return db.session.execute(select(Plan).where(Plan.code == code)).scalar_one()
