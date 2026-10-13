"""Fase 0 — esqueleto inicial: empresas, usuários, vínculos, projetos, etapas, atividades,
registros de progresso (append-only) e feriados.

Gerada por autogenerate e revisada à mão: PKs UUID; company_id NOT NULL em toda tabela de
dado de cliente; índices compostos começando por company_id; nomes de constraints pela
naming convention de app/extensions.py (iguais no SQLite e no PostgreSQL).

Revision ID: e972bfba83c7
Revises: 
Create Date: 2026-10-13 12:36:01.278015

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e972bfba83c7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('companies',
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('cnpj', sa.String(length=18), nullable=True),
    sa.Column('timezone', sa.String(length=64), nullable=False),
    sa.Column('daily_hours', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('workdays_mask', sa.Integer(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_companies'))
    )
    op.create_table('users',
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('email_confirmed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('session_version', sa.Integer(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('email', name=op.f('uq_users_email'))
    )
    op.create_table('holidays',
    sa.Column('day', sa.Date(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_holidays_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_holidays')),
    sa.UniqueConstraint('company_id', 'day', name='uq_holidays_company_day')
    )
    op.create_table('memberships',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint("role IN ('owner', 'supervisor', 'operator')", name=op.f('ck_memberships_role_valid')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_memberships_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_memberships_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_memberships')),
    sa.UniqueConstraint('company_id', 'user_id', name='uq_memberships_company_user')
    )
    with op.batch_alter_table('memberships', schema=None) as batch_op:
        batch_op.create_index('ix_memberships_company_role', ['company_id', 'role'], unique=False)
        batch_op.create_index('ix_memberships_user', ['user_id'], unique=False)

    op.create_table('projects',
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('people', sa.Integer(), server_default='1', nullable=False),
    sa.Column('hours_per_day', sa.Numeric(precision=4, scale=2), server_default='8', nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint('hours_per_day > 0', name=op.f('ck_projects_hours_per_day_positive')),
    sa.CheckConstraint('people >= 1', name=op.f('ck_projects_people_positive')),
    sa.CheckConstraint('quantity >= 0', name=op.f('ck_projects_quantity_nonnegative')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_projects_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_projects'))
    )
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.create_index('ix_projects_company_created', ['company_id', 'created_at'], unique=False)
        batch_op.create_index('ix_projects_company_status', ['company_id', 'status'], unique=False)

    op.create_table('stages',
    sa.Column('project_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_stages_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_stages_project_id_projects'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_stages'))
    )
    with op.batch_alter_table('stages', schema=None) as batch_op:
        batch_op.create_index('ix_stages_company_project_position', ['company_id', 'project_id', 'position'], unique=False)

    op.create_table('activities',
    sa.Column('stage_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('ideal_minutes', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('units_done', sa.Integer(), server_default='0', nullable=False),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint('ideal_minutes >= 0', name=op.f('ck_activities_ideal_minutes_nonnegative')),
    sa.CheckConstraint('units_done >= 0', name=op.f('ck_activities_units_done_nonnegative')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_activities_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['stage_id'], ['stages.id'], name=op.f('fk_activities_stage_id_stages'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_activities'))
    )
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.create_index('ix_activities_company_stage_position', ['company_id', 'stage_id', 'position'], unique=False)

    op.create_table('progress_entries',
    sa.Column('activity_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=True),
    sa.Column('delta', sa.Integer(), nullable=False),
    sa.Column('at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint('delta <> 0', name=op.f('ck_progress_entries_delta_nonzero')),
    sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], name=op.f('fk_progress_entries_activity_id_activities'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_progress_entries_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_progress_entries_user_id_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_progress_entries'))
    )
    with op.batch_alter_table('progress_entries', schema=None) as batch_op:
        batch_op.create_index('ix_progress_entries_company_activity_at', ['company_id', 'activity_id', 'at'], unique=False)
        batch_op.create_index('ix_progress_entries_company_at', ['company_id', 'at'], unique=False)



def downgrade():
    with op.batch_alter_table('progress_entries', schema=None) as batch_op:
        batch_op.drop_index('ix_progress_entries_company_at')
        batch_op.drop_index('ix_progress_entries_company_activity_at')

    op.drop_table('progress_entries')
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.drop_index('ix_activities_company_stage_position')

    op.drop_table('activities')
    with op.batch_alter_table('stages', schema=None) as batch_op:
        batch_op.drop_index('ix_stages_company_project_position')

    op.drop_table('stages')
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_index('ix_projects_company_status')
        batch_op.drop_index('ix_projects_company_created')

    op.drop_table('projects')
    with op.batch_alter_table('memberships', schema=None) as batch_op:
        batch_op.drop_index('ix_memberships_user')
        batch_op.drop_index('ix_memberships_company_role')

    op.drop_table('memberships')
    op.drop_table('holidays')
    op.drop_table('users')
    op.drop_table('companies')
