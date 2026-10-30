"""Etapa F — etapa “aguardando peça” (só sinaliza; nunca bloqueia o registro).

- ``stages.waiting_part`` (bool, padrão false)
- ``stages.part_expected_on`` (date, nullable): previsão de chegada
- ``stages.part_note`` (texto curto, até 140, nullable)
- ``stages.part_updated_at`` (timestamptz, nullable): última mudança na marca (lembrete)

``stages`` já tem RLS (tenant_isolation); nada muda nas políticas. Não altera linhas
existentes (todas as etapas ficam sem a marca).

Revision ID: f3c8a2d4b1e5
Revises: e2b7f1c3a9d0
Create Date: 2026-10-15 18:30:00

"""
import sqlalchemy as sa
from alembic import op


revision = 'f3c8a2d4b1e5'
down_revision = 'e2b7f1c3a9d0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('stages', sa.Column('waiting_part', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('stages', sa.Column('part_expected_on', sa.Date(), nullable=True))
    op.add_column('stages', sa.Column('part_note', sa.String(length=140), nullable=True))
    op.add_column('stages', sa.Column('part_updated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column('stages', 'part_updated_at')
    op.drop_column('stages', 'part_note')
    op.drop_column('stages', 'part_expected_on')
    op.drop_column('stages', 'waiting_part')
