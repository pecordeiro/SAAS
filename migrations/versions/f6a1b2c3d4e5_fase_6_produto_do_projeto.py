"""Fase 6 — campo opcional "produto" no projeto (subtítulo na lista e no detalhe).

Só ADD COLUMN anulável: não toca em dados existentes nem em RLS (projects já tem a política).

Revision ID: f6a1b2c3d4e5
Revises: 4d8a644d753b
Create Date: 2026-10-14 09:00:00

"""
import sqlalchemy as sa
from alembic import op


revision = 'f6a1b2c3d4e5'
down_revision = "228fffa5a2d8"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('product', sa.String(length=160), nullable=True))


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_column('product')
