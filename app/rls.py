"""Row Level Security (RLS) do PostgreSQL: a segunda barreira do isolamento (ADR-0003).

Como funciona
- A migration ``b3e9f1a2c4d5`` cria as políticas em toda tabela com dado de cliente:
  ``company_id = NULLIF(current_setting('app.company_id', true), '')::uuid`` (USING e
  WITH CHECK). Extras: ``memberships`` deixa o usuário ler os PRÓPRIOS vínculos
  (``app.user_id``), necessário no login antes de haver empresa; ``holidays`` deixa ler os
  feriados nacionais (``company_id IS NULL``).
- Com ``RLS_ENABLED=1`` a aplicação faz ``set_config(..., true)`` (equivale a
  ``SET LOCAL``) no início de CADA transação do ``db.session`` (evento ``after_begin``) com
  a empresa/usuário da requisição. ``SET LOCAL`` some no fim da transação, então uma conexão
  devolvida ao pool nunca carrega a empresa de outra requisição.
- A cobrança (``ENABLE`` + ``FORCE ROW LEVEL SECURITY``) é ligada por
  ``flask rls enable`` (e desligada por ``flask rls disable``). Fica DESLIGADA por padrão:
  as políticas existem, mas só passam a valer depois do comando.
- RLS não vale para superusuário nem para papel com ``BYPASSRLS``: o app precisa conectar
  com um papel comum. Com ``FORCE``, nem o dono das tabelas escapa das políticas.

Sem PostgreSQL (SQLite nos testes rápidos) tudo aqui vira no-op.
"""

from __future__ import annotations

import uuid
from typing import Any

from flask import current_app, g, has_app_context
from sqlalchemy import event, text
from sqlalchemy.engine import Connection

from app.extensions import db

COMPANY_GUC = "app.company_id"
USER_GUC = "app.user_id"
# Fase 5: SHA-256 do token de convite apresentado (política invitations_by_token, migration
# 4d8a644d753b) — permite ler SÓ o convite cujo hash é este, antes de saber a empresa.
TOKEN_GUC = "app.token_hash"

# Tabelas com política: as da migration b3e9f1a2c4d5 + as novas de cada etapa (cada migration
# cria a sua ``tenant_isolation``). tests/test_schema.py confere que toda tabela com
# company_id NOT NULL do metadata está aqui (e no banco).
RLS_TABLES: tuple[str, ...] = (
    "memberships",
    "invitations",
    "templates",
    "template_versions",
    "template_stages",
    "template_activities",
    "projects",
    "stages",
    "activities",
    "progress_entries",
    "holidays",
    "subscriptions",
    "payments",
    "audit_logs",
    "domain_events",
    "api_clients",
    "api_tokens",
    # Etapa F (worker, ADR-0010): migration e2b7f1c3a9d0.
    "job_runs",
    "alerts",  # migration a5d9e3f7c2b8
    # Etapa G (qualidade): migration b6e1f4a2c9d3.
    "activity_comments",
    "activity_photos",
    # migration c8f2a5d1e7b4 (checklist de inspeção).
    "template_checklist_items",
    "stage_checklist_items",
    "stage_inspections",
    "inspection_answers",
    "units",  # migration d9a3b6e2f8c5 (número de série)
    "company_modules",  # migration f1a7c3e9b2d4 (R6: módulos opcionais)
    # ADR-0019 (briefing de identidade visual e reserva da ligação): migration c5a1e9d7b3f2.
    "visual_briefings",
    "visual_briefing_files",
    "call_bookings",
)

_UNSET: Any = object()


def _is_postgres(connection: Connection) -> bool:
    return connection.dialect.name == "postgresql"


def _enabled() -> bool:
    return has_app_context() and bool(current_app.config.get("RLS_ENABLED"))


def _context() -> dict[str, str]:
    ctx = g.get("rls_context") or {}
    return {
        "company_id": ctx.get("company_id") or "",
        "user_id": ctx.get("user_id") or "",
        "token_hash": ctx.get("token_hash") or "",
    }


def _apply(connection: Connection) -> None:
    ctx = _context()
    connection.execute(
        text("SELECT set_config(:cg, :company, true), set_config(:ug, :user, true), set_config(:tg, :token, true)"),
        {
            "cg": COMPANY_GUC,
            "company": ctx["company_id"],
            "ug": USER_GUC,
            "user": ctx["user_id"],
            "tg": TOKEN_GUC,
            "token": ctx["token_hash"],
        },
    )


def _after_begin(session, transaction, connection: Connection) -> None:
    if _enabled() and _is_postgres(connection):
        _apply(connection)


def init_app(app) -> None:
    """Liga o hook ``after_begin`` (uma vez por processo; o hook consulta a flag do app)."""
    if not event.contains(db.session, "after_begin", _after_begin):
        event.listen(db.session, "after_begin", _after_begin)


def set_context(
    company_id: uuid.UUID | str | None = _UNSET,
    user_id: uuid.UUID | str | None = _UNSET,
    token_hash: str | None = _UNSET,
) -> None:
    """Define a empresa e/ou o usuário da transação atual e das próximas desta requisição.

    Chamado por ``tenancy`` depois de validar o vínculo (nunca com valor vindo do usuário).
    Se já há transação aberta, aplica nela na hora; as próximas pegam pelo ``after_begin``.
    """
    if not has_app_context():
        return
    ctx = dict(g.get("rls_context") or {})
    if company_id is not _UNSET:
        ctx["company_id"] = str(company_id) if company_id else ""
    if user_id is not _UNSET:
        ctx["user_id"] = str(user_id) if user_id else ""
    if token_hash is not _UNSET:
        ctx["token_hash"] = str(token_hash) if token_hash else ""
    g.rls_context = ctx
    session = db.session()  # a Session real por trás do scoped_session
    if _enabled() and session.in_transaction():
        connection = session.connection()
        if _is_postgres(connection):
            _apply(connection)


# --- Ligar/desligar a cobrança (DDL; rodar com o papel dono das tabelas) ---------------


def enable(connection: Connection) -> None:
    for table in RLS_TABLES:
        connection.execute(text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
        connection.execute(text(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY'))


def disable(connection: Connection) -> None:
    for table in RLS_TABLES:
        connection.execute(text(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY'))
        connection.execute(text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))


def status(connection: Connection) -> dict[str, dict[str, Any]]:
    """Por tabela: RLS ligado, forçado e nomes das políticas."""
    rows = connection.execute(
        text(
            "SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity, "
            "COALESCE(array_agg(p.polname ORDER BY p.polname) FILTER (WHERE p.polname IS NOT NULL), '{}') "
            "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "LEFT JOIN pg_policy p ON p.polrelid = c.oid "
            "WHERE n.nspname = current_schema() AND c.relkind = 'r' "
            "GROUP BY c.relname, c.relrowsecurity, c.relforcerowsecurity"
        )
    ).all()
    return {
        name: {"enabled": bool(enabled), "forced": bool(forced), "policies": list(policies)}
        for name, enabled, forced, policies in rows
    }
