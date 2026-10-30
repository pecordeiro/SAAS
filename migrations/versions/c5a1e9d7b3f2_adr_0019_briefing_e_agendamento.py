"""ADR-0019 — briefing de identidade visual e agendamento da ligação.

- ``visual_requests.status`` aceita ``briefing_filled`` (nova → briefing preenchido → em andamento →
  entregue). Só troca a CHECK; nenhuma linha muda.
- ``visual_briefings`` e ``visual_briefing_files``: dado DA EMPRESA (``company_id NOT NULL``),
  RLS ``tenant_isolation``. Um briefing por empresa (UNIQUE ``company_id``).
- ``call_slots``: horários da PLATAFORMA (sem ``company_id``, sem RLS), UNIQUE ``starts_at`` (UTC).
- ``call_bookings``: reserva DA EMPRESA (RLS). UNIQUE ``slot_id`` é o árbitro da concorrência
  (duas empresas nunca ficam com o mesmo horário) e UNIQUE ``company_id`` = uma reserva por vez.
- RLS: política criada sempre (PostgreSQL); ENABLE + FORCE só se o RLS já estiver ligado no banco
  (mesmo padrão da f1a7c3e9b2d4: ``flask rls enable`` liga a cobrança).
- Downgrade: apaga as quatro tabelas e volta a CHECK antiga (requisição em ``briefing_filled``
  volta para ``new``, senão a CHECK antiga não seria criada).

Revision ID: c5a1e9d7b3f2
Revises: f1a7c3e9b2d4
Create Date: 2026-10-23 18:00:00

"""
import sqlalchemy as sa
from alembic import op

revision = 'c5a1e9d7b3f2'
down_revision = 'a9d3f5c1b7e2'
branch_labels = None
depends_on = None

CURRENT_COMPANY = "NULLIF(current_setting('app.company_id', true), '')::uuid"
TENANT_TABLES = ('visual_briefings', 'visual_briefing_files', 'call_bookings')
STATUS_NEW = "status IN ('new', 'briefing_filled', 'in_progress', 'delivered')"
STATUS_OLD = "status IN ('new', 'in_progress', 'delivered')"


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


def _swap_status_check(new: str) -> None:
    with op.batch_alter_table('visual_requests') as batch:
        batch.drop_constraint(op.f('ck_visual_requests_status_valid'), type_='check')
        batch.create_check_constraint(op.f('ck_visual_requests_status_valid'), new)


def upgrade():
    _swap_status_check(STATUS_NEW)

    op.create_table(
        'visual_briefings',
        sa.Column('visual_request_id', sa.Uuid(), nullable=True),
        sa.Column('company_name', sa.String(length=120), nullable=True),
        sa.Column('products', sa.Text(), nullable=True),
        sa.Column('colors', sa.String(length=300), nullable=True),
        sa.Column('fonts', sa.String(length=300), nullable=True),
        sa.Column('reference_sites', sa.Text(), nullable=True),
        sa.Column('tone', sa.String(length=20), nullable=True),
        sa.Column('contact_name', sa.String(length=120), nullable=True),
        sa.Column('contact_phone', sa.String(length=30), nullable=True),
        sa.Column('contact_email', sa.String(length=254), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_by_id', sa.Uuid(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "tone IS NULL OR tone IN ('formal', 'neutro', 'descontraido')", name=op.f('ck_visual_briefings_tone_valid')
        ),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_visual_briefings_company_id_companies'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], name=op.f('fk_visual_briefings_updated_by_id_users'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_visual_briefings')),
        sa.UniqueConstraint('company_id', name=op.f('uq_visual_briefings_company_id')),
    )

    op.create_table(
        'visual_briefing_files',
        sa.Column('briefing_id', sa.Uuid(), nullable=False),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('object_key', sa.String(length=200), nullable=False),
        sa.Column('thumb_key', sa.String(length=200), nullable=False),
        sa.Column('content_type', sa.String(length=40), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('uploaded_by_id', sa.Uuid(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.CheckConstraint("kind IN ('logo', 'produto')", name=op.f('ck_visual_briefing_files_kind_valid')),
        sa.CheckConstraint('size_bytes > 0', name=op.f('ck_visual_briefing_files_size_positive')),
        sa.ForeignKeyConstraint(['briefing_id'], ['visual_briefings.id'], name=op.f('fk_visual_briefing_files_briefing_id_visual_briefings'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_visual_briefing_files_company_id_companies'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], name=op.f('fk_visual_briefing_files_uploaded_by_id_users'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_visual_briefing_files')),
    )
    op.create_index('ix_visual_briefing_files_company_briefing', 'visual_briefing_files', ['company_id', 'briefing_id'], unique=False)

    op.create_table(
        'call_slots',
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=254), nullable=True),
        sa.Column('booked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('visual_request_id', sa.Uuid(), nullable=True),
        sa.Column('booked_company_id', sa.Uuid(), nullable=True),
        sa.Column('booked_contact_name', sa.String(length=120), nullable=True),
        sa.Column('booked_contact_phone', sa.String(length=30), nullable=True),
        sa.Column('change_request', sa.String(length=20), nullable=True),
        sa.Column('change_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.CheckConstraint('duration_minutes BETWEEN 10 AND 240', name=op.f('ck_call_slots_duration_valid')),
        sa.CheckConstraint(
            "change_request IS NULL OR change_request IN ('cancelar', 'remarcar')", name=op.f('ck_call_slots_change_request_valid')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_call_slots')),
        sa.UniqueConstraint('starts_at', name=op.f('uq_call_slots_starts_at')),
    )
    op.create_index('ix_call_slots_booked_starts', 'call_slots', ['booked_at', 'starts_at'], unique=False)
    op.create_index(op.f('ix_call_slots_visual_request_id'), 'call_slots', ['visual_request_id'], unique=False)
    op.create_index(op.f('ix_call_slots_booked_company_id'), 'call_slots', ['booked_company_id'], unique=False)

    op.create_table(
        'call_bookings',
        sa.Column('slot_id', sa.Uuid(), nullable=False),
        sa.Column('visual_request_id', sa.Uuid(), nullable=True),
        sa.Column('contact_name', sa.String(length=120), nullable=False),
        sa.Column('contact_phone', sa.String(length=30), nullable=False),
        sa.Column('change_request', sa.String(length=20), nullable=True),
        sa.Column('change_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_id', sa.Uuid(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "change_request IS NULL OR change_request IN ('cancelar', 'remarcar')", name=op.f('ck_call_bookings_change_request_valid')
        ),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_call_bookings_company_id_companies'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name=op.f('fk_call_bookings_created_by_id_users'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['slot_id'], ['call_slots.id'], name=op.f('fk_call_bookings_slot_id_call_slots'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_call_bookings')),
        sa.UniqueConstraint('company_id', name=op.f('uq_call_bookings_company_id')),
        sa.UniqueConstraint('slot_id', name=op.f('uq_call_bookings_slot_id')),
    )

    for table in TENANT_TABLES:
        tenant_rls(table)


def downgrade():
    # Políticas somem junto com as tabelas (DROP TABLE apaga as políticas do RLS).
    op.drop_table('call_bookings')
    op.drop_index(op.f('ix_call_slots_booked_company_id'), table_name='call_slots')
    op.drop_index(op.f('ix_call_slots_visual_request_id'), table_name='call_slots')
    op.drop_index('ix_call_slots_booked_starts', table_name='call_slots')
    op.drop_table('call_slots')
    op.drop_index('ix_visual_briefing_files_company_briefing', table_name='visual_briefing_files')
    op.drop_table('visual_briefing_files')
    op.drop_table('visual_briefings')
    op.execute("UPDATE visual_requests SET status = 'new' WHERE status = 'briefing_filled'")
    _swap_status_check(STATUS_OLD)
