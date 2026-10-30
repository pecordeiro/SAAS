"""ADR-0021 — tour de primeiro acesso.

- ``users.tour_seen_at`` (nulo = ainda não viu): o tour pelas telas abre sozinho no Painel
  enquanto for nulo e é marcado quando começa. Rever o tour não mexe na coluna.
- Quem já tinha entrado no sistema antes desta versão fica como “já viu” (``last_login_at``):
  o tour é para o primeiro acesso, não para quem já usa. Dá para abrir em Como funciona.
- Coluna da conta (sem ``company_id``): vale para todas as empresas da pessoa, como as
  preferências de e-mail. Downgrade só apaga a coluna.

Revision ID: d7b2f4a9c1e3
Revises: c5a1e9d7b3f2
Create Date: 2026-10-30 12:00:00

"""
import sqlalchemy as sa
from alembic import op


revision = 'd7b2f4a9c1e3'
down_revision = 'c5a1e9d7b3f2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('tour_seen_at', sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE users SET tour_seen_at = last_login_at WHERE last_login_at IS NOT NULL")


def downgrade():
    op.drop_column('users', 'tour_seen_at')
