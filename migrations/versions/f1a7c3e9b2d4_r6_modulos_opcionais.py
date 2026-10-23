"""R6 — módulos opcionais por empresa (ADR-0017, plano de reestruturação §4.5).

- ``company_modules``: uma linha por empresa e módulo (``atribuicao``, ``alertas``,
  ``aguardando_peca``, ``fotos``, ``checklist``, ``unidades``, ``api``) com ``enabled``. Sem
  linha = desligado: empresa NOVA vê só o núcleo (etapas). UNIQUE ``(company_id, module)``
  (também é o índice que começa por ``company_id``). RLS ``tenant_isolation``.
- Migração de dados (empresas que JÁ existem): liga o módulo em que a empresa já tem dados, para
  ninguém perder acesso ao que usava. Regra por módulo:
    atribuicao      — alguma atividade com responsável (``activities.assignee_id``);
    alertas         — algum alerta gravado ou relatório semanal já feito (``job_runs``);
    aguardando_peca — alguma etapa marcada ou com previsão de peça, ou a marca já mudou
                      (``audit_logs`` ``stage.waiting_part``);
    fotos           — algum comentário ou foto;
    checklist       — algum item de checklist (etapa ou modelo), inspeção ou etapa que exige;
    unidades        — algum número de série;
    api             — algum cliente ou token da API.
  A leitura é feita EMPRESA A EMPRESA com ``app.company_id`` definido (``set_config`` local), então
  funciona com o RLS forçado e com qualquer papel. Nenhum dado existente é alterado.
- Downgrade: apaga a tabela (as linhas de dados dos módulos continuam onde estavam).

Revision ID: f1a7c3e9b2d4
Revises: b5d2e7a9c3f1
Create Date: 2026-10-23 10:00:00

"""
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = 'f1a7c3e9b2d4'
down_revision = 'b5d2e7a9c3f1'
branch_labels = None
depends_on = None

CURRENT_COMPANY = "NULLIF(current_setting('app.company_id', true), '')::uuid"

# Módulo → consulta que diz se a empresa :c já tem dados nele (EXISTS; SQL comum a SQLite e PG).
EVIDENCE = {
    'atribuicao': ["SELECT 1 FROM activities WHERE company_id = :c AND assignee_id IS NOT NULL"],
    'alertas': [
        "SELECT 1 FROM alerts WHERE company_id = :c",
        "SELECT 1 FROM job_runs WHERE company_id = :c AND job = 'weekly_report'",
    ],
    'aguardando_peca': [
        "SELECT 1 FROM stages WHERE company_id = :c AND (waiting_part = :t OR part_expected_on IS NOT NULL)",
        "SELECT 1 FROM audit_logs WHERE company_id = :c AND action = 'stage.waiting_part'",
    ],
    'fotos': [
        "SELECT 1 FROM activity_comments WHERE company_id = :c",
        "SELECT 1 FROM activity_photos WHERE company_id = :c",
    ],
    'checklist': [
        "SELECT 1 FROM stage_checklist_items WHERE company_id = :c",
        "SELECT 1 FROM template_checklist_items WHERE company_id = :c",
        "SELECT 1 FROM stage_inspections WHERE company_id = :c",
        "SELECT 1 FROM stages WHERE company_id = :c AND checklist_required = :t",
    ],
    'unidades': ["SELECT 1 FROM units WHERE company_id = :c"],
    'api': [
        "SELECT 1 FROM api_clients WHERE company_id = :c",
        "SELECT 1 FROM api_tokens WHERE company_id = :c",
    ],
}


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


def _set_company(bind, company_id) -> None:
    if _postgres():
        bind.execute(sa.text("SELECT set_config('app.company_id', :c, true)"), {"c": str(company_id) if company_id else ''})


def _backfill() -> None:
    bind = op.get_bind()
    table = sa.table(
        'company_modules',
        sa.column('id', sa.Uuid()),
        sa.column('company_id', sa.Uuid()),
        sa.column('module', sa.String()),
        sa.column('enabled', sa.Boolean()),
        sa.column('updated_at', sa.DateTime(timezone=True)),
    )
    company_ids = [row[0] for row in bind.execute(sa.text("SELECT id FROM companies ORDER BY created_at, id"))]
    now = datetime.now(timezone.utc)
    try:
        for raw_id in company_ids:
            company_id = raw_id if isinstance(raw_id, uuid.UUID) else uuid.UUID(str(raw_id))
            _set_company(bind, company_id)
            # SQLite guarda UUID como 32 hex sem hífen (sa.Uuid); PG compara com o texto do uuid.
            param = company_id if _postgres() else company_id.hex
            rows = []
            for module, queries in EVIDENCE.items():
                if any(bind.execute(sa.text(q + " LIMIT 1"), {"c": param, "t": True}).first() for q in queries):
                    rows.append(
                        {'id': uuid.uuid4(), 'company_id': company_id, 'module': module, 'enabled': True, 'updated_at': now}
                    )
            if rows:
                op.bulk_insert(table, rows)
    finally:
        _set_company(bind, None)


def upgrade():
    op.create_table(
        'company_modules',
        sa.Column('module', sa.String(length=30), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_by_id', sa.Uuid(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.CheckConstraint('length(module) >= 1', name=op.f('ck_company_modules_module_not_empty')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_company_modules_company_id_companies'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], name=op.f('fk_company_modules_updated_by_id_users'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_company_modules')),
        sa.UniqueConstraint('company_id', 'module', name='uq_company_modules_company_module'),
    )
    tenant_rls('company_modules')
    _backfill()


def downgrade():
    op.drop_table('company_modules')
