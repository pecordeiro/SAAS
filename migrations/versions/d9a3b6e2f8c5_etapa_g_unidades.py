"""Etapa G — unidades (número de série) e vínculo opcional com lançamentos e inspeções.

- ``units``: série única por empresa+projeto (UNIQUE), status, versão; índice por série para a
  busca. Rastreabilidade: o cálculo continua em ``activities.units_done``.
- ``progress_entries.unit_id`` e ``stage_inspections.unit_id``: opcionais (NULL nas linhas
  existentes), FK RESTRICT, índice ``company_id, unit_id``. ``progress_entries`` continua
  append-only (a coluna só é preenchida no INSERT).

RLS ``tenant_isolation`` em ``units``.

Revision ID: d9a3b6e2f8c5
Revises: c8f2a5d1e7b4
Create Date: 2026-10-15 23:00:00

"""
import sqlalchemy as sa
from alembic import op


revision = 'd9a3b6e2f8c5'
down_revision = 'c8f2a5d1e7b4'
branch_labels = None
depends_on = None

CURRENT_COMPANY = "NULLIF(current_setting('app.company_id', true), '')::uuid"


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
        'units',
        sa.Column('project_id', sa.Uuid(), nullable=False),
        sa.Column('serial', sa.String(length=60), nullable=False),
        sa.Column('status', sa.String(length=15), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_by_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.CheckConstraint("status IN ('in_progress', 'done', 'shipped', 'scrapped')", name=op.f('ck_units_status_valid')),
        sa.CheckConstraint('length(serial) >= 1', name=op.f('ck_units_serial_not_empty')),
        sa.CheckConstraint('version >= 1', name=op.f('ck_units_version_positive')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_units_company_id_companies'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name=op.f('fk_units_created_by_id_users'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_units_project_id_projects'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_units')),
        sa.UniqueConstraint('company_id', 'project_id', 'serial', name='uq_units_company_project_serial'),
    )
    op.create_index('ix_units_company_serial', 'units', ['company_id', 'serial'], unique=False)
    tenant_rls('units')

    for table in ('progress_entries', 'stage_inspections'):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column('unit_id', sa.Uuid(), nullable=True))
            batch_op.create_foreign_key(op.f(f'fk_{table}_unit_id_units'), 'units', ['unit_id'], ['id'], ondelete='RESTRICT')
            batch_op.create_index(f'ix_{table}_company_unit', ['company_id', 'unit_id'], unique=False)


def downgrade():
    for table in ('stage_inspections', 'progress_entries'):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_index(f'ix_{table}_company_unit')
            batch_op.drop_constraint(op.f(f'fk_{table}_unit_id_units'), type_='foreignkey')
            batch_op.drop_column('unit_id')
    op.drop_index('ix_units_company_serial', table_name='units')
    op.drop_table('units')
