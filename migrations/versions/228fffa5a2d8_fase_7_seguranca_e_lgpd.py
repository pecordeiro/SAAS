"""Fase 7 — segurança e LGPD: acesso de suporte, auditoria da plataforma e token da API com RLS.

- memberships.is_support / memberships.expires_at: acesso temporário de suporte
  (``flask suporte conceder``); vínculo vencido deixa de valer sozinho (tenancy).
- platform_audit_logs: auditoria da PLATAFORMA (sem company_id e sem FK para companies) —
  sobrevive ao expurgo LGPD da empresa; só ids, contagens e motivo.
- Política api_tokens_by_token (SELECT, só PostgreSQL): mesma ideia de invitations_by_token
  (Fase 5). A autenticação da API acha o token pelo hash ANTES de saber a empresa; com RLS
  forçado, a aplicação põe o SHA-256 do token recebido em app.token_hash (SET LOCAL) e a
  política deixa ler só essa linha. Ter o token é a autorização; gravar continua exigindo
  app.company_id. (Função SECURITY DEFINER não serve aqui: com FORCE ROW LEVEL SECURITY o
  dono da função também passa pelo RLS — ver ADR-0003.)

Revision ID: 228fffa5a2d8
Revises: 4d8a644d753b
Create Date: 2026-10-14 02:02:51.279099

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '228fffa5a2d8'
down_revision = '4d8a644d753b'
branch_labels = None
depends_on = None

CURRENT_TOKEN = "NULLIF(current_setting('app.token_hash', true), '')"


def _postgres() -> bool:
    return op.get_bind().dialect.name == 'postgresql'


def upgrade():
    op.create_table('platform_audit_logs',
    sa.Column('action', sa.String(length=80), nullable=False),
    sa.Column('subject_company_id', sa.Uuid(), nullable=True),
    sa.Column('operator', sa.String(length=120), nullable=True),
    sa.Column('details', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_platform_audit_logs'))
    )
    op.create_index('ix_platform_audit_logs_at', 'platform_audit_logs', ['at'], unique=False)
    op.create_index('ix_platform_audit_logs_subject', 'platform_audit_logs', ['subject_company_id', 'at'], unique=False)

    # ADD COLUMN simples nos dois bancos (sem recriar a tabela).
    op.add_column('memberships', sa.Column('is_support', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('memberships', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))

    if _postgres():
        op.execute(
            'CREATE POLICY api_tokens_by_token ON api_tokens FOR SELECT '
            f'USING (token_hash = {CURRENT_TOKEN})'
        )


def downgrade():
    if _postgres():
        op.execute('DROP POLICY IF EXISTS api_tokens_by_token ON api_tokens')
        op.drop_column('memberships', 'expires_at')
        op.drop_column('memberships', 'is_support')
    else:
        with op.batch_alter_table('memberships', schema=None) as batch_op:
            batch_op.drop_column('expires_at')
            batch_op.drop_column('is_support')

    op.drop_index('ix_platform_audit_logs_subject', table_name='platform_audit_logs')
    op.drop_index('ix_platform_audit_logs_at', table_name='platform_audit_logs')
    op.drop_table('platform_audit_logs')
