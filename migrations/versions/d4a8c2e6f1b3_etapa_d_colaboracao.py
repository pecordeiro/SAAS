"""Etapa D — colaboração: versão da etapa e responsável da atividade.

- ``stages.version`` (padrão 1, CHECK >= 1): controle otimista ao renomear a etapa
  (409 com o valor atual), como ``activities.version`` já faz no registro de peças.
- ``activities.assignee_id`` (nullable, FK ``users`` com ON DELETE SET NULL) + índice
  ``(company_id, assignee_id)``. Que o responsável seja membro ATIVO da mesma empresa é
  conferido no serviço (``projects.assign_activity``).

Não altera linhas existentes (etapas ficam na versão 1; atividades sem responsável).

Revision ID: d4a8c2e6f1b3
Revises: c7d3e9a1b5f2
Create Date: 2026-10-15 14:00:00

"""
import sqlalchemy as sa
from alembic import op


revision = 'd4a8c2e6f1b3'
down_revision = 'c7d3e9a1b5f2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('stages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('version', sa.Integer(), server_default='1', nullable=False))
        batch_op.create_check_constraint(op.f('ck_stages_version_positive'), 'version >= 1')

    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assignee_id', sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            op.f('fk_activities_assignee_id_users'), 'users', ['assignee_id'], ['id'], ondelete='SET NULL'
        )
        batch_op.create_index('ix_activities_company_assignee', ['company_id', 'assignee_id'], unique=False)


def downgrade():
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.drop_index('ix_activities_company_assignee')
        batch_op.drop_constraint(op.f('fk_activities_assignee_id_users'), type_='foreignkey')
        batch_op.drop_column('assignee_id')

    with op.batch_alter_table('stages', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('ck_stages_version_positive'), type_='check')
        batch_op.drop_column('version')
