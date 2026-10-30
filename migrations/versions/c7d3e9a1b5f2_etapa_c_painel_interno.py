"""Etapa C — equipe da plataforma e requisições de identidade visual.

``users.is_staff`` (padrão false) e ``visual_requests`` (dado da plataforma, sem RLS por
empresa; só ``/interno`` lê). Não altera linhas existentes.

Revision ID: c7d3e9a1b5f2
Revises: b1e7c9d2a4f6
Create Date: 2026-10-15 10:00:00

"""
import sqlalchemy as sa
from alembic import op


revision = 'c7d3e9a1b5f2'
down_revision = 'b1e7c9d2a4f6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('is_staff', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.create_table(
        'visual_requests',
        sa.Column('company_id', sa.Uuid(), nullable=True),
        sa.Column('company_name', sa.String(length=120), nullable=False),
        sa.Column('plan_code', sa.String(length=40), nullable=False),
        sa.Column('contact_name', sa.String(length=120), nullable=True),
        sa.Column('contact_email', sa.String(length=254), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_by', sa.String(length=254), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.CheckConstraint("status IN ('new', 'in_progress', 'delivered')", name=op.f('ck_visual_requests_status_valid')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_visual_requests')),
    )
    op.create_index('ix_visual_requests_company', 'visual_requests', ['company_id'], unique=False)
    op.create_index('ix_visual_requests_status_created', 'visual_requests', ['status', 'created_at'], unique=False)


def downgrade():
    op.drop_index('ix_visual_requests_status_created', table_name='visual_requests')
    op.drop_index('ix_visual_requests_company', table_name='visual_requests')
    op.drop_table('visual_requests')
    # DROP COLUMN direto nos dois bancos: o batch do SQLite recriaria `users` e perderia o
    # índice funcional uq_users_email_lower (que ele não reflete).
    op.drop_column('users', 'is_staff')
