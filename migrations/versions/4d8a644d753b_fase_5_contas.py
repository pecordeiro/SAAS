"""Fase 5 — contas: bloqueio progressivo, último passo TOTP, último acesso e convite por token com RLS.

- login_throttles: contador de falhas de login por conta e por IP (chave só como SHA-256).
  Tabela de plataforma (sem company_id): o login acontece antes de saber a empresa.
- users.totp_last_step: último passo TOTP aceito (o mesmo código não vale duas vezes).
- users.last_login_at: “Último acesso” na tela de usuários.
- Política invitations_by_token (SELECT, só PostgreSQL): com RLS ligado, o aceite de
  convite acontece ANTES de saber a empresa. A aplicação põe o SHA-256 do token recebido
  em app.token_hash (SET LOCAL) e a política deixa ler só o convite com esse hash — ter o
  token é a autorização; sem ele nada é lido. Gravar continua exigindo app.company_id.

Revision ID: 4d8a644d753b
Revises: a7c2d4e8f901
Create Date: 2026-10-13 13:37:41.261782

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d8a644d753b'
down_revision = 'a7c2d4e8f901'
branch_labels = None
depends_on = None

CURRENT_TOKEN = "NULLIF(current_setting('app.token_hash', true), '')"


def _postgres() -> bool:
    return op.get_bind().dialect.name == 'postgresql'


def upgrade():
    op.create_table('login_throttles',
    sa.Column('scope', sa.String(length=10), nullable=False),
    sa.Column('key_hash', sa.String(length=64), nullable=False),
    sa.Column('failures', sa.Integer(), nullable=False),
    sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("scope IN ('account', 'ip')", name=op.f('ck_login_throttles_scope_valid')),
    sa.CheckConstraint('failures >= 0', name=op.f('ck_login_throttles_failures_nonnegative')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_login_throttles')),
    sa.UniqueConstraint('scope', 'key_hash', name='uq_login_throttles_scope_key')
    )
    # ADD COLUMN simples (sem recriar a tabela): preserva o índice de expressão lower(email).
    op.add_column('users', sa.Column('totp_last_step', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))
    if _postgres():
        op.execute(
            'CREATE POLICY invitations_by_token ON invitations FOR SELECT '
            f'USING (token_hash = {CURRENT_TOKEN})'
        )


def downgrade():
    if _postgres():
        op.execute('DROP POLICY IF EXISTS invitations_by_token ON invitations')
        op.drop_column('users', 'last_login_at')
        op.drop_column('users', 'totp_last_step')
    else:
        # SQLite: o batch recria a tabela e não recria índice de expressão (ver progresso,
        # Fase 3) — tira e põe de volta uq_users_email_lower fora do batch.
        op.drop_index('uq_users_email_lower', table_name='users')
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.drop_column('last_login_at')
            batch_op.drop_column('totp_last_step')
        op.create_index('uq_users_email_lower', 'users', [sa.text('lower(email)')], unique=True)
    op.drop_table('login_throttles')
