"""Fase 3 — dados: planos Essencial, Profissional e Empresa.

Mesmos valores e ids (uuid5 do código) de app/services/plans.py::PLAN_CATALOG, copiados
aqui de propósito (migration não importa o app). Ajustes posteriores de preço/limite:
`flask seed-plans` (idempotente). Limite NULL = ilimitado.

Revision ID: a7c2d4e8f901
Revises: b3e9f1a2c4d5
Create Date: 2026-10-13 13:20:00

"""
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op


revision = 'a7c2d4e8f901'
down_revision = 'b3e9f1a2c4d5'
branch_labels = None
depends_on = None

PLAN_NAMESPACE = uuid.UUID('6f1d3c3e-2b7a-4c55-9a43-6d1f0c2a9e10')

PLANS = (
    # code, name, price_cents, max_projects, max_users, features
    ('essencial', 'Essencial', 14900, 3, 5, {'mfa_required': False, 'api': False}),
    ('profissional', 'Profissional', 34900, 15, 25, {'mfa_required': False, 'api': False}),
    ('empresa', 'Empresa', 79900, None, 100, {'mfa_required': True, 'api': True}),
)

plans = sa.table(
    'plans',
    sa.column('id', sa.Uuid()),
    sa.column('code', sa.String()),
    sa.column('name', sa.String()),
    sa.column('price_cents', sa.Integer()),
    sa.column('max_projects', sa.Integer()),
    sa.column('max_users', sa.Integer()),
    sa.column('features', sa.JSON()),
    sa.column('active', sa.Boolean()),
    sa.column('created_at', sa.DateTime(timezone=True)),
)


def upgrade():
    bind = op.get_bind()
    existing = set(bind.execute(sa.select(plans.c.code)).scalars())
    now = datetime.now(timezone.utc)
    rows = [
        {
            'id': uuid.uuid5(PLAN_NAMESPACE, code),
            'code': code,
            'name': name,
            'price_cents': price,
            'max_projects': max_projects,
            'max_users': max_users,
            'features': features,
            'active': True,
            'created_at': now,
        }
        for code, name, price, max_projects, max_users, features in PLANS
        if code not in existing
    ]
    if rows:
        op.bulk_insert(plans, rows)


def downgrade():
    # Só remove planos sem assinatura (nunca apaga dado de cliente).
    op.execute(
        "DELETE FROM plans WHERE code IN ('essencial', 'profissional', 'empresa') "
        "AND id NOT IN (SELECT plan_id FROM subscriptions)"
    )
