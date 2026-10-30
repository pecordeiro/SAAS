"""Fase 4 — desfazer registro de peças (D13) por lançamento compensatório.

progress_entries continua append-only: desfazer grava uma linha nova com delta negativo e
``reverts_entry_id`` apontando para o registro desfeito. UNIQUE garante que cada registro
é desfeito no máximo uma vez; o CHECK garante que só lançamento negativo compensa.

Revision ID: c4f8a1d2e3b6
Revises: a7c2d4e8f901
Create Date: 2026-10-13 18:00:00

"""
import sqlalchemy as sa
from alembic import op


revision = 'c4f8a1d2e3b6'
down_revision = 'a7c2d4e8f901'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('progress_entries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reverts_entry_id', sa.Uuid(), nullable=True))
        batch_op.create_unique_constraint(op.f('uq_progress_entries_reverts_entry_id'), ['reverts_entry_id'])
        batch_op.create_foreign_key(
            op.f('fk_progress_entries_reverts_entry_id_progress_entries'),
            'progress_entries', ['reverts_entry_id'], ['id'], ondelete='RESTRICT',
        )
        batch_op.create_check_constraint(
            op.f('ck_progress_entries_reversal_negative'), 'reverts_entry_id IS NULL OR delta < 0'
        )


def downgrade():
    with op.batch_alter_table('progress_entries', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('ck_progress_entries_reversal_negative'), type_='check')
        batch_op.drop_constraint(op.f('fk_progress_entries_reverts_entry_id_progress_entries'), type_='foreignkey')
        batch_op.drop_constraint(op.f('uq_progress_entries_reverts_entry_id'), type_='unique')
        batch_op.drop_column('reverts_entry_id')
