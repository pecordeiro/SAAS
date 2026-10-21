"""R8 — restaurar o projeto para uma data e hora.

A restauração grava lançamentos COMPENSATÓRIOS em ``progress_entries`` (que continua
append-only). Duas colunas opcionais, NULL em todas as linhas existentes:

- ``restore_id``: id da operação de restauração que gravou o lançamento (agrupa os
  lançamentos dela). Sem FK: a operação não tem tabela própria; o registro dela (quem, quando,
  para qual data) fica em ``audit_logs``.
- ``restore_undoes_id``: preenchido só nos lançamentos de um DESFAZER de restauração, com o id
  da restauração desfeita. O CHECK exige que o desfazer também tenha o seu ``restore_id``.

Índices ``company_id, restore_id`` e ``company_id, restore_undoes_id`` (buscar os lançamentos de
uma restauração e saber se ela já foi desfeita). A política RLS de progress_entries não muda.

Revision ID: e8c4a7b2d1f9
Revises: d9a3b6e2f8c5
Create Date: 2026-10-21 12:00:00

"""
import sqlalchemy as sa
from alembic import op


revision = 'e8c4a7b2d1f9'
down_revision = 'd9a3b6e2f8c5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('progress_entries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('restore_id', sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column('restore_undoes_id', sa.Uuid(), nullable=True))
        batch_op.create_index('ix_progress_entries_company_restore', ['company_id', 'restore_id'], unique=False)
        batch_op.create_index(
            'ix_progress_entries_company_restore_undoes', ['company_id', 'restore_undoes_id'], unique=False
        )
        batch_op.create_check_constraint(
            op.f('ck_progress_entries_restore_undo_grouped'), 'restore_undoes_id IS NULL OR restore_id IS NOT NULL'
        )


def downgrade():
    with op.batch_alter_table('progress_entries', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('ck_progress_entries_restore_undo_grouped'), type_='check')
        batch_op.drop_index('ix_progress_entries_company_restore_undoes')
        batch_op.drop_index('ix_progress_entries_company_restore')
        batch_op.drop_column('restore_undoes_id')
        batch_op.drop_column('restore_id')
