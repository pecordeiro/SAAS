"""Etapa F — worker (ADR-0010): backoff do outbox e marcas de execução.

- ``domain_events.next_attempt_at`` (nullable): próxima tentativa depois de falha (backoff).
- ``domain_events.last_error`` (nullable, 200): nome da última exceção do handler.
- ``job_runs`` (dado da empresa, RLS ``tenant_isolation``): marca de tarefa agendada por
  empresa e período (relatório semanal), ``UNIQUE(company_id, job, period_key)``.

No PostgreSQL cria a política ``tenant_isolation`` em ``job_runs`` e, se o RLS já estiver
ligado nas tabelas de cliente (``flask rls enable`` antes desta migration), liga e força
também na tabela nova — senão ela ficaria sem cobrança até rodar ``flask rls enable`` de novo.

Não altera linhas existentes.

Revision ID: e2b7f1c3a9d0
Revises: d4a8c2e6f1b3
Create Date: 2026-10-15 18:00:00

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = 'e2b7f1c3a9d0'
down_revision = 'd4a8c2e6f1b3'
branch_labels = None
depends_on = None

CURRENT_COMPANY = "NULLIF(current_setting('app.company_id', true), '')::uuid"
JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql')


def _postgres() -> bool:
    return op.get_bind().dialect.name == 'postgresql'


def tenant_rls(table: str) -> None:
    """Política tenant_isolation + mesmo estado de ENABLE/FORCE das tabelas existentes."""
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
    # ADD/DROP COLUMN direto (sem batch): recriar a tabela no SQLite perderia o índice
    # parcial ix_domain_events_unpublished.
    op.add_column('domain_events', sa.Column('next_attempt_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('domain_events', sa.Column('last_error', sa.String(length=200), nullable=True))

    op.create_table(
        'job_runs',
        sa.Column('job', sa.String(length=40), nullable=False),
        sa.Column('period_key', sa.String(length=40), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('details', JSON_TYPE, nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_job_runs_company_id_companies'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_job_runs')),
        sa.UniqueConstraint('company_id', 'job', 'period_key', name='uq_job_runs_company_job_period'),
    )
    tenant_rls('job_runs')


def downgrade():
    op.drop_table('job_runs')  # a política some junto com a tabela
    op.drop_column('domain_events', 'last_error')
    op.drop_column('domain_events', 'next_attempt_at')
