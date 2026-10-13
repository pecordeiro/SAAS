"""Catálogo de planos (fonte única para `flask seed-plans` e para os testes).

A migration ``a7c2d4e8f901`` grava os mesmos três planos com os mesmos ids (uuid5 do
código); `flask seed-plans` é idempotente e serve para sincronizar preço/limites depois.
Limite NULL = ilimitado.
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


@dataclass(frozen=True)
class PlanSpec:
    code: str
    name: str
    price_cents: int
    max_projects: int | None
    max_users: int | None
    features: dict = field(default_factory=dict)

    @property
    def id(self) -> uuid.UUID:
        return uuid.uuid5(PLAN_NAMESPACE, self.code)


PLAN_CATALOG: tuple[PlanSpec, ...] = (
    PlanSpec(ESSENCIAL, "Essencial", 14900, 3, 5, {"mfa_required": False, "api": False}),
    PlanSpec(PROFISSIONAL, "Profissional", 34900, 15, 25, {"mfa_required": False, "api": False}),
    PlanSpec(EMPRESA, "Empresa", 79900, None, 100, {"mfa_required": True, "api": True}),
)


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
        }
        if plan is None:
            db.session.add(Plan(id=spec.id, code=spec.code, active=True, **values))
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
