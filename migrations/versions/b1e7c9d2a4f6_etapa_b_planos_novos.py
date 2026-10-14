"""Etapa B — planos novos: Essencial, Profissional, Empresa e Implantação (sob consulta).

Esquema: ``plans.price_cents`` passa a aceitar NULL (= sob consulta, sem checkout) e o CHECK
``ck_plans_price_nonnegative`` vira ``price_cents IS NULL OR price_cents >= 0``.

Dados: atualiza os três planos existentes (mesmos ids uuid5 do código) e insere
``implantacao``. Não há cliente pagante nos preços antigos (decisão do usuário): só
substitui, sem migrar assinaturas. Valores copiados de app/services/plans.py::PLAN_CATALOG
de propósito (migration não importa o app); `flask seed-plans` sincroniza depois.

Downgrade: volta os três planos aos valores da Fase 3, remove ``implantacao`` (recusa se
alguma assinatura usa esse plano — nunca apaga dado de cliente) e volta NOT NULL.

Revision ID: b1e7c9d2a4f6
Revises: f6a1b2c3d4e5
Create Date: 2026-10-14 15:00:00

"""
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op


revision = 'b1e7c9d2a4f6'
down_revision = 'f6a1b2c3d4e5'
branch_labels = None
depends_on = None

PLAN_NAMESPACE = uuid.UUID('6f1d3c3e-2b7a-4c55-9a43-6d1f0c2a9e10')


def _features(**on):
    return {key: bool(on.get(key, False)) for key in ('mfa_required', 'api', 'visual_custom', 'implantacao')}


PLANS = (
    # code, name, price_cents, max_projects, max_users, features
    ('essencial', 'Essencial', 24990, 3, 3, _features()),
    ('profissional', 'Profissional', 49700, 10, 20, _features()),
    ('empresa', 'Empresa', 99700, None, None, _features(mfa_required=True, api=True, visual_custom=True)),
    ('implantacao', 'Implantação', None, None, None,
     _features(mfa_required=True, api=True, visual_custom=True, implantacao=True)),
)

OLD_PLANS = (
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


def _upsert(bind, rows):
    existing = set(bind.execute(sa.select(plans.c.code)).scalars())
    now = datetime.now(timezone.utc)
    for code, name, price, max_projects, max_users, features in rows:
        values = {
            'name': name,
            'price_cents': price,
            'max_projects': max_projects,
            'max_users': max_users,
            'features': features,
            'active': True,
        }
        if code in existing:
            bind.execute(plans.update().where(plans.c.code == code).values(**values))
        else:
            bind.execute(plans.insert().values(id=uuid.uuid5(PLAN_NAMESPACE, code), code=code, created_at=now, **values))


def upgrade():
    with op.batch_alter_table('plans', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('ck_plans_price_nonnegative'), type_='check')
        batch_op.alter_column('price_cents', existing_type=sa.Integer(), nullable=True)
        batch_op.create_check_constraint(op.f('ck_plans_price_nonnegative'), 'price_cents IS NULL OR price_cents >= 0')
    _upsert(op.get_bind(), PLANS)


def downgrade():
    bind = op.get_bind()
    in_use = bind.execute(
        sa.text(
            "SELECT count(*) FROM subscriptions s JOIN plans p ON p.id = s.plan_id OR p.id = s.pending_plan_id "
            "WHERE p.code = 'implantacao' OR p.price_cents IS NULL"
        )
    ).scalar_one()
    if in_use:
        raise RuntimeError('Há assinatura em plano sob consulta (implantacao): mude o plano antes do downgrade.')
    bind.execute(sa.text("DELETE FROM plans WHERE code = 'implantacao' OR price_cents IS NULL"))
    _upsert(bind, OLD_PLANS)
    with op.batch_alter_table('plans', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('ck_plans_price_nonnegative'), type_='check')
        batch_op.alter_column('price_cents', existing_type=sa.Integer(), nullable=False)
        batch_op.create_check_constraint(op.f('ck_plans_price_nonnegative'), 'price_cents >= 0')
