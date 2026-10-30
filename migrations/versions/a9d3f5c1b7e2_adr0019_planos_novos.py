"""ADR-0019 — planos novos: novos preços e limites de Essencial, Profissional e Empresa.

Só dados (sem mudança de esquema). Os códigos e os ids (uuid5 do código) não mudam:

- ``essencial``: R$ 249,90, 5 projetos, 5 pessoas (era 3 e 3);
- ``profissional``: R$ 497,90, 10 projetos, 25 pessoas (era R$ 497,00, 10 e 20);
- ``empresa``: R$ 997,90, ilimitado (era R$ 997,00);
- ``implantacao``: sob orçamento (preço NULL), ilimitado; mantém os recursos. Os serviços
  (implantação, 1 mês de acompanhamento, treinamento) são só texto das telas.

Ainda não há cliente pagante nos preços antigos (ADR-0019): os planos são substituídos no lugar,
sem migrar assinaturas. Valores copiados de app/services/plans.py::PLAN_CATALOG de propósito
(migration não importa o app); `flask seed-plans` sincroniza depois. Se a linha do plano não
existir, é criada (mesmo padrão da b1e7c9d2a4f6).

Downgrade: devolve os valores da Etapa B (b1e7c9d2a4f6).

Revision ID: a9d3f5c1b7e2
Revises: f1a7c3e9b2d4
Create Date: 2026-10-23 16:00:00

"""
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op


revision = 'a9d3f5c1b7e2'
down_revision = 'f1a7c3e9b2d4'
branch_labels = None
depends_on = None

PLAN_NAMESPACE = uuid.UUID('6f1d3c3e-2b7a-4c55-9a43-6d1f0c2a9e10')


def _features(**on):
    return {key: bool(on.get(key, False)) for key in ('mfa_required', 'api', 'visual_custom', 'implantacao')}


PLANS = (
    # code, name, price_cents, max_projects, max_users, features
    ('essencial', 'Essencial', 24990, 5, 5, _features()),
    ('profissional', 'Profissional', 49790, 10, 25, _features()),
    ('empresa', 'Empresa', 99790, None, None, _features(mfa_required=True, api=True, visual_custom=True)),
    ('implantacao', 'Implantação', None, None, None,
     _features(mfa_required=True, api=True, visual_custom=True, implantacao=True)),
)

# Valores da Etapa B (migration b1e7c9d2a4f6), para o downgrade.
PREVIOUS_PLANS = (
    ('essencial', 'Essencial', 24990, 3, 3, _features()),
    ('profissional', 'Profissional', 49700, 10, 20, _features()),
    ('empresa', 'Empresa', 99700, None, None, _features(mfa_required=True, api=True, visual_custom=True)),
    ('implantacao', 'Implantação', None, None, None,
     _features(mfa_required=True, api=True, visual_custom=True, implantacao=True)),
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
    _upsert(op.get_bind(), PLANS)


def downgrade():
    _upsert(op.get_bind(), PREVIOUS_PLANS)
