"""Etapa G — evidências por atividade: comentários e fotos.

- ``activity_comments``: texto (1..1000), autor, data. Apagar = linha removida + auditoria.
- ``activity_photos``: só METADADOS da foto (chave do objeto ``<company_id>/fotos/<uuid>.jpg``,
  miniatura, tamanho, dimensões, SHA-256, legenda, quem enviou). O arquivo mora no
  armazenamento (``app/services/storage.py``); o nome original enviado nunca é guardado.

Ambas são dado da empresa: ``company_id NOT NULL``, índices começando por ``company_id`` e
política RLS ``tenant_isolation`` (no PostgreSQL; liga ENABLE/FORCE se o RLS já estiver ativo).

Revision ID: b6e1f4a2c9d3
Revises: a5d9e3f7c2b8
Create Date: 2026-10-15 21:00:00

"""
import sqlalchemy as sa
from alembic import op


revision = 'b6e1f4a2c9d3'
down_revision = 'a5d9e3f7c2b8'
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
        'activity_comments',
        sa.Column('activity_id', sa.Uuid(), nullable=False),
        sa.Column('body', sa.String(length=1000), nullable=False),
        sa.Column('author_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.CheckConstraint('length(body) >= 1', name=op.f('ck_activity_comments_body_not_empty')),
        sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], name=op.f('fk_activity_comments_activity_id_activities'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], name=op.f('fk_activity_comments_author_id_users'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_activity_comments_company_id_companies'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_activity_comments')),
    )
    op.create_index('ix_activity_comments_company_activity_at', 'activity_comments', ['company_id', 'activity_id', 'created_at'], unique=False)
    tenant_rls('activity_comments')

    op.create_table(
        'activity_photos',
        sa.Column('activity_id', sa.Uuid(), nullable=False),
        sa.Column('object_key', sa.String(length=160), nullable=False),
        sa.Column('thumb_key', sa.String(length=160), nullable=False),
        sa.Column('content_type', sa.String(length=20), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('caption', sa.String(length=140), nullable=True),
        sa.Column('uploaded_by_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.CheckConstraint("content_type = 'image/jpeg'", name=op.f('ck_activity_photos_content_type_jpeg')),
        sa.CheckConstraint('size_bytes > 0', name=op.f('ck_activity_photos_size_positive')),
        sa.CheckConstraint('width > 0 AND height > 0', name=op.f('ck_activity_photos_dimensions_positive')),
        sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], name=op.f('fk_activity_photos_activity_id_activities'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_activity_photos_company_id_companies'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], name=op.f('fk_activity_photos_uploaded_by_id_users'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_activity_photos')),
        sa.UniqueConstraint('object_key', name=op.f('uq_activity_photos_object_key')),
        sa.UniqueConstraint('thumb_key', name=op.f('uq_activity_photos_thumb_key')),
    )
    op.create_index('ix_activity_photos_company_activity_at', 'activity_photos', ['company_id', 'activity_id', 'created_at'], unique=False)
    tenant_rls('activity_photos')


def downgrade():
    # Atenção: o downgrade apaga só os METADADOS; os objetos no armazenamento ficam. Rode o
    # expurgo/limpeza do bucket antes se for descartar as fotos de verdade.
    op.drop_index('ix_activity_photos_company_activity_at', table_name='activity_photos')
    op.drop_table('activity_photos')
    op.drop_index('ix_activity_comments_company_activity_at', table_name='activity_comments')
    op.drop_table('activity_comments')
