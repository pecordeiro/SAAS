"""Fase 3 — políticas de Row Level Security (segunda barreira do isolamento, ADR-0003).

Cria as políticas em toda tabela com dado de cliente, mas NÃO liga a cobrança: ENABLE +
FORCE ROW LEVEL SECURITY é feito por `flask rls enable` quando RLS_ENABLED=1 (ver
app/rls.py). No SQLite não faz nada (não existe RLS).

- tenant_isolation (todas): company_id = app.company_id, para ler e para gravar.
  NULLIF(..., '') porque, depois do primeiro SET LOCAL na conexão, a variável volta a ''
  (e não a NULL) no fim da transação; ''::uuid daria erro.
- memberships_own_user (SELECT): o usuário lê os próprios vínculos (app.user_id) — o login
  precisa disso antes de existir empresa ativa.
- holidays_national_read (SELECT): feriados nacionais (company_id IS NULL) são lidos por
  todas as empresas; gravar continua restrito à própria empresa.

A lista de tabelas é cópia congelada de app/rls.py::RLS_TABLES (migration não importa o
app); tests/test_schema.py confere que as duas e o banco batem.

Revision ID: b3e9f1a2c4d5
Revises: e05ae54663a3
Create Date: 2026-10-13 13:10:00

"""
from alembic import op


revision = 'b3e9f1a2c4d5'
down_revision = 'e05ae54663a3'
branch_labels = None
depends_on = None

TABLES = (
    'memberships',
    'invitations',
    'templates',
    'template_versions',
    'template_stages',
    'template_activities',
    'projects',
    'stages',
    'activities',
    'progress_entries',
    'holidays',
    'subscriptions',
    'payments',
    'audit_logs',
    'domain_events',
    'api_clients',
    'api_tokens',
)

CURRENT_COMPANY = "NULLIF(current_setting('app.company_id', true), '')::uuid"
CURRENT_USER = "NULLIF(current_setting('app.user_id', true), '')::uuid"


def _postgres() -> bool:
    return op.get_bind().dialect.name == 'postgresql'


def upgrade():
    if not _postgres():
        return
    for table in TABLES:
        op.execute(
            f'CREATE POLICY tenant_isolation ON "{table}" '
            f'USING (company_id = {CURRENT_COMPANY}) '
            f'WITH CHECK (company_id = {CURRENT_COMPANY})'
        )
    op.execute(
        'CREATE POLICY memberships_own_user ON memberships FOR SELECT '
        f'USING (user_id = {CURRENT_USER})'
    )
    op.execute(
        'CREATE POLICY holidays_national_read ON holidays FOR SELECT '
        'USING (company_id IS NULL)'
    )


def downgrade():
    if not _postgres():
        return
    op.execute('DROP POLICY IF EXISTS holidays_national_read ON holidays')
    op.execute('DROP POLICY IF EXISTS memberships_own_user ON memberships')
    for table in TABLES:
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}"')
        # Se `flask rls enable` foi usado, desliga junto (tabela sem política + RLS = 0 linhas).
        op.execute(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
