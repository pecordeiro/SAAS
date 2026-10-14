"""Fase 8 — cobrança: link de pagamento, desconto e busca do webhook com RLS.

- payments.invoice_url: página de pagamento do provedor (Pix, boleto ou cartão).
- subscriptions.pending_plan_id / pending_plan_at: troca de plano pendente (upgrade só vale
  com a fatura no valor novo paga; downgrade no fim do período pago).
- subscriptions.discount_percent (0–90, NULL = sem desconto): desconto do admin da
  plataforma, sempre com motivo em audit_logs.
- Política subscriptions_provider_lookup (só PostgreSQL): o webhook do Asaas chega sem
  empresa; ele só conhece o id da assinatura NO PROVEDOR. Com RLS forçado, a política
  tenant_isolation esconderia a linha. Esta política libera SELECT apenas da linha cujo
  provider_subscription_id é igual a app.billing_lookup (SET LOCAL feito pelo serviço só
  durante a busca). Quem não sabe o id do provedor não lê nada; gravar continua exigindo
  app.company_id (o serviço passa a usar a empresa da assinatura achada).

Revision ID: d8b2e6f4a1c7
Revises: 4d8a644d753b
Create Date: 2026-10-14 10:00:00

"""
import sqlalchemy as sa
from alembic import op


revision = 'd8b2e6f4a1c7'
down_revision = '4d8a644d753b'
branch_labels = None
depends_on = None

LOOKUP = "NULLIF(current_setting('app.billing_lookup', true), '')"


def _postgres() -> bool:
    return op.get_bind().dialect.name == 'postgresql'


def upgrade():
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('invoice_url', sa.String(length=255), nullable=True))
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('discount_percent', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('pending_plan_id', sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column('pending_plan_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key(
            op.f('fk_subscriptions_pending_plan_id_plans'), 'plans', ['pending_plan_id'], ['id'], ondelete='RESTRICT'
        )
        batch_op.create_check_constraint(
            op.f('ck_subscriptions_discount_range'),
            'discount_percent IS NULL OR (discount_percent >= 0 AND discount_percent <= 90)',
        )
    if _postgres():
        op.execute(
            'CREATE POLICY subscriptions_provider_lookup ON subscriptions FOR SELECT '
            f'USING (provider_subscription_id = {LOOKUP})'
        )


def downgrade():
    if _postgres():
        op.execute('DROP POLICY IF EXISTS subscriptions_provider_lookup ON subscriptions')
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.drop_constraint(op.f('fk_subscriptions_pending_plan_id_plans'), type_='foreignkey')
        batch_op.drop_constraint(op.f('ck_subscriptions_discount_range'), type_='check')
        batch_op.drop_column('pending_plan_at')
        batch_op.drop_column('pending_plan_id')
        batch_op.drop_column('discount_percent')
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.drop_column('invoice_url')
