"""Fase 3 — schema completo do MVP: modelos de etapas versionados, convites, tokens de
conta, MFA, planos, assinaturas, cobranças, webhooks, auditoria, outbox e API.

Gerada por autogenerate e revisada à mão:
- FK circular templates.current_version_id → template_versions criada no fim (e removida
  primeiro no downgrade), porque as duas tabelas se referenciam.
- CHECKs novos em tabelas existentes (autogenerate não compara CHECK) adicionados à mão.
- holidays.company_id passa a aceitar NULL (feriado nacional); o downgrade apaga os
  nacionais antes de voltar a NOT NULL.
- E-mail case-insensitive: índice único em lower(email) (funciona no SQLite e no Postgres).

Revision ID: e05ae54663a3
Revises: e972bfba83c7
Create Date: 2026-10-13 12:54:37.046206

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e05ae54663a3'
down_revision = 'e972bfba83c7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('plans',
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('price_cents', sa.Integer(), nullable=False),
    sa.Column('max_projects', sa.Integer(), nullable=True),
    sa.Column('max_users', sa.Integer(), nullable=True),
    sa.Column('features', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
    sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('max_projects IS NULL OR max_projects >= 0', name=op.f('ck_plans_max_projects_nonnegative')),
    sa.CheckConstraint('max_users IS NULL OR max_users >= 1', name=op.f('ck_plans_max_users_positive')),
    sa.CheckConstraint('price_cents >= 0', name=op.f('ck_plans_price_nonnegative')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_plans')),
    sa.UniqueConstraint('code', name=op.f('uq_plans_code'))
    )
    op.create_table('api_clients',
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('created_by_user_id', sa.Uuid(), nullable=True),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_api_clients_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name=op.f('fk_api_clients_created_by_user_id_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_api_clients')),
    sa.UniqueConstraint('company_id', 'name', name='uq_api_clients_company_name')
    )
    op.create_table('audit_logs',
    sa.Column('actor_user_id', sa.Uuid(), nullable=True),
    sa.Column('action', sa.String(length=80), nullable=False),
    sa.Column('object_type', sa.String(length=40), nullable=True),
    sa.Column('object_id', sa.Uuid(), nullable=True),
    sa.Column('ip', sa.String(length=45), nullable=True),
    sa.Column('details', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], name=op.f('fk_audit_logs_actor_user_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_audit_logs_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    with op.batch_alter_table('audit_logs', schema=None) as batch_op:
        batch_op.create_index('ix_audit_logs_company_at', ['company_id', 'at'], unique=False)
        batch_op.create_index('ix_audit_logs_company_object', ['company_id', 'object_type', 'object_id'], unique=False)

    op.create_table('domain_events',
    sa.Column('type', sa.String(length=80), nullable=False),
    sa.Column('payload', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint('attempts >= 0', name=op.f('ck_domain_events_attempts_nonnegative')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_domain_events_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_domain_events'))
    )
    with op.batch_alter_table('domain_events', schema=None) as batch_op:
        batch_op.create_index('ix_domain_events_company_created', ['company_id', 'created_at'], unique=False)
        batch_op.create_index('ix_domain_events_unpublished', ['created_at'], unique=False, postgresql_where=sa.text('published_at IS NULL'), sqlite_where=sa.text('published_at IS NULL'))

    op.create_table('email_confirmations',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_email_confirmations_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_email_confirmations')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_email_confirmations_token_hash'))
    )
    with op.batch_alter_table('email_confirmations', schema=None) as batch_op:
        batch_op.create_index('ix_email_confirmations_user_created', ['user_id', 'created_at'], unique=False)

    op.create_table('invitations',
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('invited_by_user_id', sa.Uuid(), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint("role IN ('owner', 'supervisor', 'operator')", name=op.f('ck_invitations_role_valid')),
    sa.CheckConstraint('email = lower(email)', name=op.f('ck_invitations_email_lowercase')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_invitations_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['invited_by_user_id'], ['users.id'], name=op.f('fk_invitations_invited_by_user_id_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_invitations')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_invitations_token_hash'))
    )
    with op.batch_alter_table('invitations', schema=None) as batch_op:
        batch_op.create_index('ix_invitations_company_created', ['company_id', 'created_at'], unique=False)
        batch_op.create_index('ix_invitations_company_email', ['company_id', 'email'], unique=False)

    op.create_table('mfa_recovery_codes',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('code_hash', sa.String(length=255), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_mfa_recovery_codes_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_mfa_recovery_codes')),
    sa.UniqueConstraint('user_id', 'code_hash', name='uq_mfa_recovery_codes_user_code')
    )
    op.create_table('password_resets',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_password_resets_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_password_resets')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_password_resets_token_hash'))
    )
    with op.batch_alter_table('password_resets', schema=None) as batch_op:
        batch_op.create_index('ix_password_resets_user_created', ['user_id', 'created_at'], unique=False)

    op.create_table('subscriptions',
    sa.Column('plan_id', sa.Uuid(), nullable=False),
    sa.Column('provider', sa.String(length=20), nullable=False),
    sa.Column('provider_customer_id', sa.String(length=64), nullable=True),
    sa.Column('provider_subscription_id', sa.String(length=64), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('grace_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('canceled_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint("provider IN ('asaas', 'fake')", name=op.f('ck_subscriptions_provider_valid')),
    sa.CheckConstraint("status IN ('trialing', 'active', 'past_due', 'canceled', 'expired')", name=op.f('ck_subscriptions_status_valid')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_subscriptions_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], name=op.f('fk_subscriptions_plan_id_plans'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_subscriptions')),
    sa.UniqueConstraint('company_id', name='uq_subscriptions_company'),
    sa.UniqueConstraint('provider', 'provider_subscription_id', name='uq_subscriptions_provider_subscription')
    )
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.create_index('ix_subscriptions_status_period_end', ['status', 'current_period_end'], unique=False)

    op.create_table('templates',
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('current_version_id', sa.Uuid(), nullable=True),
    sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_templates_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_templates')),
    sa.UniqueConstraint('company_id', 'name', name='uq_templates_company_name')
    )
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.create_index('ix_templates_company_archived', ['company_id', 'archived_at'], unique=False)

    op.create_table('webhook_events',
    sa.Column('provider', sa.String(length=20), nullable=False),
    sa.Column('external_event_id', sa.String(length=100), nullable=False),
    sa.Column('type', sa.String(length=80), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=True),
    sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.CheckConstraint("provider IN ('asaas', 'fake')", name=op.f('ck_webhook_events_provider_valid')),
    sa.CheckConstraint("status IN ('received', 'processed', 'ignored', 'failed')", name=op.f('ck_webhook_events_status_valid')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_webhook_events_company_id_companies'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_webhook_events')),
    sa.UniqueConstraint('external_event_id', name=op.f('uq_webhook_events_external_event_id'))
    )
    with op.batch_alter_table('webhook_events', schema=None) as batch_op:
        batch_op.create_index('ix_webhook_events_status_received', ['status', 'received_at'], unique=False)

    op.create_table('api_tokens',
    sa.Column('api_client_id', sa.Uuid(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('token_prefix', sa.String(length=12), nullable=False),
    sa.Column('scopes', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['api_client_id'], ['api_clients.id'], name=op.f('fk_api_tokens_api_client_id_api_clients'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_api_tokens_company_id_companies'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_api_tokens')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_api_tokens_token_hash'))
    )
    with op.batch_alter_table('api_tokens', schema=None) as batch_op:
        batch_op.create_index('ix_api_tokens_company_client', ['company_id', 'api_client_id'], unique=False)

    op.create_table('payments',
    sa.Column('subscription_id', sa.Uuid(), nullable=False),
    sa.Column('provider_payment_id', sa.String(length=64), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('value_cents', sa.Integer(), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint("status IN ('pending', 'confirmed', 'received', 'overdue', 'refunded', 'canceled')", name=op.f('ck_payments_status_valid')),
    sa.CheckConstraint('value_cents >= 0', name=op.f('ck_payments_value_nonnegative')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_payments_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], name=op.f('fk_payments_subscription_id_subscriptions'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_payments')),
    sa.UniqueConstraint('provider_payment_id', name=op.f('uq_payments_provider_payment_id'))
    )
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.create_index('ix_payments_company_due', ['company_id', 'due_date'], unique=False)
        batch_op.create_index('ix_payments_subscription', ['subscription_id'], unique=False)

    op.create_table('template_versions',
    sa.Column('template_id', sa.Uuid(), nullable=False),
    sa.Column('number', sa.Integer(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_by_user_id', sa.Uuid(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint('number >= 1', name=op.f('ck_template_versions_number_positive')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_template_versions_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name=op.f('fk_template_versions_created_by_user_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['template_id'], ['templates.id'], name=op.f('fk_template_versions_template_id_templates'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_template_versions')),
    sa.UniqueConstraint('company_id', 'template_id', 'number', name='uq_template_versions_company_template_number')
    )
    op.create_table('template_stages',
    sa.Column('template_version_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint('position >= 0', name=op.f('ck_template_stages_position_nonnegative')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_template_stages_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['template_version_id'], ['template_versions.id'], name=op.f('fk_template_stages_template_version_id_template_versions'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_template_stages'))
    )
    with op.batch_alter_table('template_stages', schema=None) as batch_op:
        batch_op.create_index('ix_template_stages_company_version_position', ['company_id', 'template_version_id', 'position'], unique=False)

    op.create_table('template_activities',
    sa.Column('template_stage_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('ideal_minutes', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('company_id', sa.Uuid(), nullable=False),
    sa.CheckConstraint('ideal_minutes >= 0', name=op.f('ck_template_activities_ideal_minutes_nonnegative')),
    sa.CheckConstraint('position >= 0', name=op.f('ck_template_activities_position_nonnegative')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_template_activities_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['template_stage_id'], ['template_stages.id'], name=op.f('fk_template_activities_template_stage_id_template_stages'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_template_activities'))
    )
    with op.batch_alter_table('template_activities', schema=None) as batch_op:
        batch_op.create_index('ix_template_activities_company_stage_position', ['company_id', 'template_stage_id', 'position'], unique=False)

    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mfa_required', sa.Boolean(), server_default=sa.text('false'), nullable=False))
        batch_op.add_column(sa.Column('deletion_requested_at', sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table('holidays', schema=None) as batch_op:
        batch_op.alter_column('company_id',
               existing_type=sa.UUID(),
               nullable=True)
        batch_op.create_index('uq_holidays_national_day', ['day'], unique=True, postgresql_where=sa.text('company_id IS NULL'), sqlite_where=sa.text('company_id IS NULL'))

    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('template_version_id', sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(batch_op.f('fk_projects_template_version_id_template_versions'), 'template_versions', ['template_version_id'], ['id'], ondelete='RESTRICT')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('totp_secret_enc', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('mfa_enabled', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    # Índice de expressão fora do batch: o modo batch do SQLite não recria índices de expressão.
    op.create_index('uq_users_email_lower', 'users', [sa.text('lower(email)')], unique=True)

    # FK do ciclo templates ⇄ template_versions: só depois de as duas tabelas existirem.
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_templates_current_version_id_template_versions',
            'template_versions', ['current_version_id'], ['id'], ondelete='SET NULL',
        )

    # CHECKs novos em tabelas da Fase 0 (o autogenerate não detecta CHECK).
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.create_check_constraint(op.f('ck_companies_daily_hours_range'), 'daily_hours > 0 AND daily_hours <= 24')
        batch_op.create_check_constraint(op.f('ck_companies_workdays_mask_range'), 'workdays_mask BETWEEN 0 AND 127')
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.create_check_constraint(op.f('ck_projects_status_valid'), "status IN ('active', 'done')")
    with op.batch_alter_table('stages', schema=None) as batch_op:
        batch_op.create_check_constraint(op.f('ck_stages_position_nonnegative'), 'position >= 0')
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.create_check_constraint(op.f('ck_activities_version_positive'), 'version >= 1')
        batch_op.create_check_constraint(op.f('ck_activities_position_nonnegative'), 'position >= 0')


def downgrade():
    with op.batch_alter_table('activities', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('ck_activities_position_nonnegative'), type_='check')
        batch_op.drop_constraint(op.f('ck_activities_version_positive'), type_='check')
    with op.batch_alter_table('stages', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('ck_stages_position_nonnegative'), type_='check')
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('ck_projects_status_valid'), type_='check')
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('ck_companies_workdays_mask_range'), type_='check')
        batch_op.drop_constraint(op.f('ck_companies_daily_hours_range'), type_='check')

    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.drop_constraint('fk_templates_current_version_id_template_versions', type_='foreignkey')

    op.drop_index('uq_users_email_lower', table_name='users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('mfa_enabled')
        batch_op.drop_column('totp_secret_enc')

    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_projects_template_version_id_template_versions'), type_='foreignkey')
        batch_op.drop_column('template_version_id')

    # Feriados nacionais (company_id NULL) não cabem no schema da Fase 0.
    op.execute("DELETE FROM holidays WHERE company_id IS NULL")
    with op.batch_alter_table('holidays', schema=None) as batch_op:
        batch_op.drop_index('uq_holidays_national_day', postgresql_where=sa.text('company_id IS NULL'), sqlite_where=sa.text('company_id IS NULL'))
        batch_op.alter_column('company_id',
               existing_type=sa.UUID(),
               nullable=False)

    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.drop_column('deletion_requested_at')
        batch_op.drop_column('mfa_required')

    with op.batch_alter_table('template_activities', schema=None) as batch_op:
        batch_op.drop_index('ix_template_activities_company_stage_position')

    op.drop_table('template_activities')
    with op.batch_alter_table('template_stages', schema=None) as batch_op:
        batch_op.drop_index('ix_template_stages_company_version_position')

    op.drop_table('template_stages')
    op.drop_table('template_versions')
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.drop_index('ix_payments_subscription')
        batch_op.drop_index('ix_payments_company_due')

    op.drop_table('payments')
    with op.batch_alter_table('api_tokens', schema=None) as batch_op:
        batch_op.drop_index('ix_api_tokens_company_client')

    op.drop_table('api_tokens')
    with op.batch_alter_table('webhook_events', schema=None) as batch_op:
        batch_op.drop_index('ix_webhook_events_status_received')

    op.drop_table('webhook_events')
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.drop_index('ix_templates_company_archived')

    op.drop_table('templates')
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.drop_index('ix_subscriptions_status_period_end')

    op.drop_table('subscriptions')
    with op.batch_alter_table('password_resets', schema=None) as batch_op:
        batch_op.drop_index('ix_password_resets_user_created')

    op.drop_table('password_resets')
    op.drop_table('mfa_recovery_codes')
    with op.batch_alter_table('invitations', schema=None) as batch_op:
        batch_op.drop_index('ix_invitations_company_email')
        batch_op.drop_index('ix_invitations_company_created')

    op.drop_table('invitations')
    with op.batch_alter_table('email_confirmations', schema=None) as batch_op:
        batch_op.drop_index('ix_email_confirmations_user_created')

    op.drop_table('email_confirmations')
    with op.batch_alter_table('domain_events', schema=None) as batch_op:
        batch_op.drop_index('ix_domain_events_unpublished', postgresql_where=sa.text('published_at IS NULL'), sqlite_where=sa.text('published_at IS NULL'))
        batch_op.drop_index('ix_domain_events_company_created')

    op.drop_table('domain_events')
    with op.batch_alter_table('audit_logs', schema=None) as batch_op:
        batch_op.drop_index('ix_audit_logs_company_object')
        batch_op.drop_index('ix_audit_logs_company_at')

    op.drop_table('audit_logs')
    op.drop_table('api_clients')
    op.drop_table('plans')
