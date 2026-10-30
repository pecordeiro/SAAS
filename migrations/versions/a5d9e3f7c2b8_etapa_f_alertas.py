"""Etapa F — alertas automáticos e preferências de e-mail.

- ``alerts`` (dado da empresa, RLS ``tenant_isolation``): alerta por projeto/etapa com dedupe
  ``UNIQUE(company_id, dedupe_key, day)``; ``details`` só com números e datas.
- ``companies.stalled_days`` (padrão 3, CHECK 1..60): X de “etapa parada há X dias úteis”.
- ``users.notify_assignment|notify_alerts|notify_weekly`` (padrão true): preferências de
  e-mail ligadas/desligadas em /conta/perfil.

No PostgreSQL cria a política da tabela nova e, se o RLS já estiver ligado (``flask rls
enable``), liga e força também nela. Não altera linhas existentes além dos padrões.

Revision ID: a5d9e3f7c2b8
Revises: f3c8a2d4b1e5
Create Date: 2026-10-15 19:00:00

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = 'a5d9e3f7c2b8'
down_revision = 'f3c8a2d4b1e5'
branch_labels = None
depends_on = None

CURRENT_COMPANY = "NULLIF(current_setting('app.company_id', true), '')::uuid"
JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql')
NOTIFY_COLUMNS = ('notify_assignment', 'notify_alerts', 'notify_weekly')


def _postgres() -> bool:
    return op.get_bind().dialect.name == 'postgresql'


def tenant_rls(table: str) -> None:
    if not _postgres():
        return
    op.execute(
        f'CREATE POLICY tenant_isolation ON "{table}" '
        f'USING (company_id = {CURRENT_COMPANY}) '
        f'WITH CHECK (company_id = {CURRENT_COMPANY})'
    )
    enabled = op.get_bind().execute(
        sa.text("SELECT relrowsecurity FROM pg_class WHERE relname = 'projects' AND relnamespace = current_schema()::regnamespace")
    ).scalar()
    if enabled:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')


def upgrade():
    op.create_table(
        'alerts',
        sa.Column('kind', sa.String(length=30), nullable=False),
        sa.Column('severity', sa.String(length=10), nullable=False),
        sa.Column('dedupe_key', sa.String(length=120), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=False),
        sa.Column('stage_id', sa.Uuid(), nullable=True),
        sa.Column('details', JSON_TYPE, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('emailed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "kind IN ('deadline_risk', 'forecast_late', 'stage_stalled', 'part_overdue')", name=op.f('ck_alerts_kind_valid')
        ),
        sa.CheckConstraint("severity IN ('warning', 'danger')", name=op.f('ck_alerts_severity_valid')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_alerts_company_id_companies'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_alerts_project_id_projects'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stage_id'], ['stages.id'], name=op.f('fk_alerts_stage_id_stages'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_alerts')),
        sa.UniqueConstraint('company_id', 'dedupe_key', 'day', name='uq_alerts_company_key_day'),
    )
    op.create_index('ix_alerts_company_day', 'alerts', ['company_id', 'day'], unique=False)
    op.create_index('ix_alerts_company_project', 'alerts', ['company_id', 'project_id'], unique=False)
    tenant_rls('alerts')

    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stalled_days', sa.Integer(), server_default='3', nullable=False))
        batch_op.create_check_constraint(op.f('ck_companies_stalled_days_range'), 'stalled_days BETWEEN 1 AND 60')

    # ADD/DROP COLUMN direto: o batch do SQLite recriaria `users` e perderia o índice
    # funcional uq_users_email_lower (mesma razão da migration c7d3e9a1b5f2).
    for column in NOTIFY_COLUMNS:
        op.add_column('users', sa.Column(column, sa.Boolean(), server_default=sa.text('true'), nullable=False))


def downgrade():
    for column in reversed(NOTIFY_COLUMNS):
        op.drop_column('users', column)
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('ck_companies_stalled_days_range'), type_='check')
        batch_op.drop_column('stalled_days')
    op.drop_index('ix_alerts_company_project', table_name='alerts')
    op.drop_index('ix_alerts_company_day', table_name='alerts')
    op.drop_table('alerts')
