"""R4 — modo de lançar progresso por projeto (plano de reestruturação §4.4, decisão D1).

``projects.progress_mode``: ``'simples'`` (a pessoa lança o % da etapa) ou ``'detalhado'``
(subatividades com tempo ideal e peças, igual à planilha). NOT NULL com padrão
``'detalhado'``: todos os projetos que já existem (e os importados da planilha de referência)
continuam como estavam. O padrão ``'simples'`` para projeto novo é decidido na tela de novo
projeto, não no banco. CHECK restringe aos dois valores. Só ADD COLUMN; a política RLS de
``projects`` não muda.

Revision ID: b5d2e7a9c3f1
Revises: e8c4a7b2d1f9
Create Date: 2026-10-21 18:00:00

"""
import sqlalchemy as sa
from alembic import op


revision = 'b5d2e7a9c3f1'
down_revision = 'e8c4a7b2d1f9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('progress_mode', sa.String(length=12), server_default='detalhado', nullable=False)
        )
        batch_op.create_check_constraint(
            op.f('ck_projects_progress_mode_valid'), "progress_mode IN ('simples', 'detalhado')"
        )


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('ck_projects_progress_mode_valid'), type_='check')
        batch_op.drop_column('progress_mode')
