"""Etapa G — checklist de inspeção por etapa.

- ``template_checklist_items`` (itens por etapa do MODELO; versionados com a versão) e
  ``template_stages.checklist_required``;
- ``stage_checklist_items`` (cópia no projeto; arquiva, não apaga) e ``stages.checklist_required``
  (só SINALIZA “checklist pendente”; não bloqueia nada — ADR-0011);
- ``stage_inspections`` (rascunho → assinada: ``signed_by_id`` + ``signed_at`` do servidor);
- ``inspection_answers`` (resposta por item; depois de assinada é imutável — correção = nova linha
  com ``supersedes_id`` UNIQUE + ``correction_reason``).

Todas com ``company_id NOT NULL``, índices começando por ``company_id`` e RLS ``tenant_isolation``.
Colunas novas em ``stages``/``template_stages`` por ADD COLUMN direto (com padrão false).

Revision ID: c8f2a5d1e7b4
Revises: b6e1f4a2c9d3
Create Date: 2026-10-15 22:00:00

"""
import sqlalchemy as sa
from alembic import op


revision = 'c8f2a5d1e7b4'
down_revision = 'b6e1f4a2c9d3'
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


def _company_fk(table: str):
    return sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f(f'fk_{table}_company_id_companies'), ondelete='RESTRICT')


def upgrade():
    op.add_column('template_stages', sa.Column('checklist_required', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('stages', sa.Column('checklist_required', sa.Boolean(), server_default=sa.text('false'), nullable=False))

    op.create_table(
        'template_checklist_items',
        sa.Column('template_stage_id', sa.Uuid(), nullable=False),
        sa.Column('text', sa.String(length=200), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.CheckConstraint('position >= 0', name=op.f('ck_template_checklist_items_position_nonnegative')),
        _company_fk('template_checklist_items'),
        sa.ForeignKeyConstraint(['template_stage_id'], ['template_stages.id'], name=op.f('fk_template_checklist_items_template_stage_id_template_stages'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_template_checklist_items')),
    )
    op.create_index('ix_template_checklist_items_company_stage_position', 'template_checklist_items', ['company_id', 'template_stage_id', 'position'], unique=False)
    tenant_rls('template_checklist_items')

    op.create_table(
        'stage_checklist_items',
        sa.Column('stage_id', sa.Uuid(), nullable=False),
        sa.Column('text', sa.String(length=200), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.CheckConstraint('position >= 0', name=op.f('ck_stage_checklist_items_position_nonnegative')),
        _company_fk('stage_checklist_items'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name=op.f('fk_stage_checklist_items_created_by_id_users'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['stage_id'], ['stages.id'], name=op.f('fk_stage_checklist_items_stage_id_stages'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_stage_checklist_items')),
    )
    op.create_index('ix_stage_checklist_items_company_stage_position', 'stage_checklist_items', ['company_id', 'stage_id', 'position'], unique=False)
    tenant_rls('stage_checklist_items')

    op.create_table(
        'stage_inspections',
        sa.Column('stage_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_by_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('signed_by_id', sa.Uuid(), nullable=True),
        sa.Column('signed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.CheckConstraint("status <> 'signed' OR (signed_at IS NOT NULL AND signed_by_id IS NOT NULL)", name=op.f('ck_stage_inspections_signed_has_signature')),
        sa.CheckConstraint("status IN ('draft', 'signed')", name=op.f('ck_stage_inspections_status_valid')),
        sa.CheckConstraint('version >= 1', name=op.f('ck_stage_inspections_version_positive')),
        _company_fk('stage_inspections'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name=op.f('fk_stage_inspections_created_by_id_users'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['signed_by_id'], ['users.id'], name=op.f('fk_stage_inspections_signed_by_id_users'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['stage_id'], ['stages.id'], name=op.f('fk_stage_inspections_stage_id_stages'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_stage_inspections')),
    )
    op.create_index('ix_stage_inspections_company_stage_created', 'stage_inspections', ['company_id', 'stage_id', 'created_at'], unique=False)
    tenant_rls('stage_inspections')

    op.create_table(
        'inspection_answers',
        sa.Column('inspection_id', sa.Uuid(), nullable=False),
        sa.Column('item_id', sa.Uuid(), nullable=False),
        sa.Column('result', sa.String(length=15), nullable=False),
        sa.Column('note', sa.String(length=500), nullable=True),
        sa.Column('answered_by_id', sa.Uuid(), nullable=True),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('supersedes_id', sa.Uuid(), nullable=True),
        sa.Column('correction_reason', sa.String(length=500), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.CheckConstraint("result IN ('ok', 'nonconforming', 'na')", name=op.f('ck_inspection_answers_result_valid')),
        sa.CheckConstraint('supersedes_id IS NULL OR correction_reason IS NOT NULL', name=op.f('ck_inspection_answers_correction_has_reason')),
        sa.ForeignKeyConstraint(['answered_by_id'], ['users.id'], name=op.f('fk_inspection_answers_answered_by_id_users'), ondelete='SET NULL'),
        _company_fk('inspection_answers'),
        sa.ForeignKeyConstraint(['inspection_id'], ['stage_inspections.id'], name=op.f('fk_inspection_answers_inspection_id_stage_inspections'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['item_id'], ['stage_checklist_items.id'], name=op.f('fk_inspection_answers_item_id_stage_checklist_items'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['supersedes_id'], ['inspection_answers.id'], name=op.f('fk_inspection_answers_supersedes_id_inspection_answers'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_inspection_answers')),
        sa.UniqueConstraint('supersedes_id', name=op.f('uq_inspection_answers_supersedes_id')),
    )
    op.create_index('ix_inspection_answers_company_inspection_item', 'inspection_answers', ['company_id', 'inspection_id', 'item_id'], unique=False)
    tenant_rls('inspection_answers')


def downgrade():
    op.drop_index('ix_inspection_answers_company_inspection_item', table_name='inspection_answers')
    op.drop_table('inspection_answers')
    op.drop_index('ix_stage_inspections_company_stage_created', table_name='stage_inspections')
    op.drop_table('stage_inspections')
    op.drop_index('ix_stage_checklist_items_company_stage_position', table_name='stage_checklist_items')
    op.drop_table('stage_checklist_items')
    op.drop_index('ix_template_checklist_items_company_stage_position', table_name='template_checklist_items')
    op.drop_table('template_checklist_items')
    op.drop_column('stages', 'checklist_required')
    op.drop_column('template_stages', 'checklist_required')
