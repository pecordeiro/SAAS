"""Fase 7 — LGPD: portabilidade (ZIP de CSVs), exclusão com carência, expurgo e retenção.

Regras (docs/plano/lgpd.md):
- Exportar: só o proprietário, só linhas com ``company_id`` da empresa da sessão + a
  própria empresa + os usuários vinculados a ela. Segredos (hash de senha/token, segredo
  TOTP) nunca saem. Células perigosas para planilha neutralizadas (= + - @ TAB CR).
- Excluir: o proprietário pede → ``companies.deletion_requested_at`` e aviso por e-mail aos
  proprietários; pode cancelar durante ``LGPD_DELETION_GRACE_DAYS`` (30). Depois disso,
  ``flask lgpd-purge`` apaga tudo da empresa e os usuários que não têm vínculo com outra
  empresa. Idempotente (empresa já apagada = nada a fazer) e registrado em
  ``platform_audit_logs`` (sobrevive ao expurgo; só ids e contagens).
- Retenção: ``flask lgpd-retencao`` apaga o que passou do prazo (tokens usados/vencidos,
  bloqueios de login antigos, eventos já publicados, auditoria de acesso da API > 6 meses,
  auditoria geral > 5 anos).
- Com RLS ligado, cada empresa é tratada no próprio contexto (``rls.set_context``); para
  achar vínculos de um usuário em OUTRAS empresas usa-se a política ``memberships_own_user``
  (contexto de usuário), nunca um papel com BYPASSRLS.
"""

from __future__ import annotations

import csv
import io
import json
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from flask import current_app
from sqlalchemy import Table, and_, delete, func, or_, select

from app import rls
from app.extensions import db
from app.models import (
    ROLE_OWNER,
    AuditLog,
    Company,
    DomainEvent,
    EmailConfirmation,
    Invitation,
    LoginThrottle,
    Membership,
    MfaRecoveryCode,
    PasswordReset,
    User,
)
from app.models.base import utcnow
from app.models.privacy import PlatformAuditLog
from app.services import audit
from app.services.exporter import neutralize

# Ações (audit_logs da empresa e platform_audit_logs).
DATA_EXPORTED = audit.COMPANY_DATA_EXPORTED
DELETION_REQUESTED = audit.COMPANY_DELETION_REQUESTED
DELETION_CANCELLED = audit.COMPANY_DELETION_CANCELLED
COMPANY_PURGED = "lgpd.company_purged"
RETENTION_APPLIED = "lgpd.retention_applied"

# Colunas que nunca saem na exportação (segredos e controles internos).
SECRET_COLUMNS = frozenset(
    {"password_hash", "totp_secret_enc", "totp_last_step", "session_version", "token_hash", "code_hash", "key_hash"}
)
# Tabelas com company_id que NÃO entram no ZIP: caixa de entrada bruta do provedor de
# pagamento (pode trazer campos do Asaas sem relação com o titular; os dados úteis já estão
# em subscriptions/payments).
# visual_requests: anotações e e-mail da equipe (Etapa C) não são dado da empresa para devolver a ela.
EXPORT_SKIP_TABLES = frozenset({"webhook_events", "visual_requests"})
USER_EXPORT_COLUMNS = ("id", "name", "email", "email_confirmed_at", "active", "mfa_enabled", "last_login_at", "created_at")
# Tabelas globais ligadas ao usuário (sem company_id) apagadas junto com o usuário.
USER_CHILD_MODELS = (PasswordReset, EmailConfirmation, MfaRecoveryCode)


class LgpdError(Exception):
    """Regra violada; a mensagem vai para a tela/terminal."""


def _now() -> datetime:
    return utcnow()


def _aware(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def grace_days() -> int:
    return int(current_app.config.get("LGPD_DELETION_GRACE_DAYS", 30))


def purge_date(company: Company) -> datetime | None:
    requested = _aware(company.deletion_requested_at)
    return requested + timedelta(days=grace_days()) if requested else None


# ---------------------------------------------------------------- exportação


def company_tables() -> list[Table]:
    """Tabelas com ``company_id`` (ordem de dependência: pais antes dos filhos)."""
    return [t for t in db.metadata.sorted_tables if "company_id" in t.c and t.name not in {"companies"}]


def _cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "sim" if value else "não"
    if isinstance(value, datetime):
        return _aware(value).isoformat()
    if isinstance(value, (date, uuid.UUID, Decimal)):
        return str(value)
    if isinstance(value, (dict, list)):
        return neutralize(json.dumps(value, ensure_ascii=False, default=str))
    return neutralize(str(value))


def _csv_bytes(columns: list[str], rows) -> tuple[bytes, int]:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(columns)
    count = 0
    for row in rows:
        writer.writerow([_cell(row[c]) for c in columns])
        count += 1
    return ("﻿" + buffer.getvalue()).encode("utf-8"), count


def export_company(company: Company) -> tuple[bytes, dict[str, int]]:
    """ZIP com um CSV por tabela da empresa + LEIA-ME. Devolve (bytes, linhas por arquivo)."""
    counts: dict[str, int] = {}
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        company_cols = [c.name for c in Company.__table__.columns if c.name not in SECRET_COLUMNS]
        row = db.session.execute(select(Company.__table__).where(Company.__table__.c.id == company.id)).mappings().all()
        data, counts["empresa.csv"] = _csv_bytes(company_cols, row)
        zf.writestr("empresa.csv", data)

        users = User.__table__
        member_ids = select(Membership.user_id).where(Membership.company_id == company.id)
        rows = db.session.execute(
            select(*(users.c[c] for c in USER_EXPORT_COLUMNS)).where(users.c.id.in_(member_ids)).order_by(users.c.created_at)
        ).mappings()
        data, counts["usuarios.csv"] = _csv_bytes(list(USER_EXPORT_COLUMNS), rows)
        zf.writestr("usuarios.csv", data)

        for table in company_tables():
            if table.name in EXPORT_SKIP_TABLES:
                continue
            columns = [c.name for c in table.columns if c.name not in SECRET_COLUMNS]
            order = [table.c[c] for c in ("created_at", "at", "id") if c in table.c][:1]
            rows = db.session.execute(
                select(*(table.c[c] for c in columns)).where(table.c.company_id == company.id).order_by(*order)
            ).mappings()
            data, counts[f"{table.name}.csv"] = _csv_bytes(columns, rows)
            zf.writestr(f"{table.name}.csv", data)

        readme = (
            "Exportação de dados da empresa — Controle de Produção\n"
            f"Gerada em {_now().isoformat()} (UTC).\n\n"
            "Um arquivo CSV por tabela (separador ';', UTF-8 com BOM, abre no Excel).\n"
            "Datas em ISO 8601 (UTC). Textos que começam com = + - @ ganham um apóstrofo\n"
            "para a planilha não executar fórmula.\n"
            "Não incluídos por segurança: hashes de senha e de tokens, segredo do MFA.\n\n"
            "Arquivos e linhas:\n" + "".join(f"  {name}: {n}\n" for name, n in counts.items())
        )
        zf.writestr("LEIA-ME.txt", readme.encode("utf-8"))
    return out.getvalue(), counts


def record_export(company: Company, actor_user_id: uuid.UUID, counts: dict[str, int]) -> None:
    audit.record(
        DATA_EXPORTED,
        company_id=company.id,
        actor_user_id=actor_user_id,
        object_type="company",
        object_id=company.id,
        details={"files": len(counts), "rows": sum(counts.values())},
    )


def export_filename(company: Company) -> str:
    return f"dados-empresa-{_now():%Y%m%d}.zip"


# ---------------------------------------------------------------- exclusão com carência


def _owners(company_id: uuid.UUID) -> list[User]:
    return list(
        db.session.execute(
            select(User)
            .join(Membership, Membership.user_id == User.id)
            .where(
                Membership.company_id == company_id,
                Membership.role == ROLE_OWNER,
                Membership.usable(),
                Membership.is_support.is_(False),
                User.active.is_(True),
            )
        ).scalars()
    )


def email_context():
    """Contexto de requisição para renderizar e-mail fora de uma requisição (CLI/cron): os
    context processors do app leem ``request``/``current_user``."""
    from contextlib import nullcontext

    from flask import has_request_context

    if has_request_context():
        return nullcontext()
    return current_app.test_request_context("/", base_url=current_app.config.get("APP_BASE_URL") or "http://localhost")


def _notify_owners(company: Company, subject: str, template: str, **ctx) -> None:
    from app.services.email import send_template

    owners = _owners(company.id)
    with email_context():
        for owner in owners:
            send_template(owner.email, subject, template, name=owner.name, company_name=company.name, **ctx)


def request_deletion(company: Company, actor_user_id: uuid.UUID) -> datetime:
    """Marca a exclusão (idempotente: pedir de novo não reinicia o prazo). Sem commit."""
    if company.deletion_requested_at is None:
        company.deletion_requested_at = _now()
        audit.record(
            DELETION_REQUESTED,
            company_id=company.id,
            actor_user_id=actor_user_id,
            object_type="company",
            object_id=company.id,
            details={"grace_days": grace_days()},
        )
        db.session.flush()
        _notify_owners(
            company,
            "Exclusão da empresa agendada",
            "deletion_requested",
            purge_at=purge_date(company),
        )
    return purge_date(company)


def cancel_deletion(company: Company, actor_user_id: uuid.UUID) -> bool:
    if company.deletion_requested_at is None:
        return False
    company.deletion_requested_at = None
    audit.record(
        DELETION_CANCELLED, company_id=company.id, actor_user_id=actor_user_id, object_type="company", object_id=company.id
    )
    db.session.flush()
    _notify_owners(company, "Exclusão da empresa cancelada", "deletion_cancelled")
    return True


def due_for_purge(now: datetime | None = None) -> list[Company]:
    now = now or _now()
    limit = now - timedelta(days=grace_days())
    return list(
        db.session.execute(
            select(Company)
            .where(Company.deletion_requested_at.is_not(None), Company.deletion_requested_at <= limit)
            .order_by(Company.deletion_requested_at)
        ).scalars()
    )


@dataclass
class PurgeResult:
    company_id: uuid.UUID
    rows: dict[str, int] = field(default_factory=dict)
    users_deleted: int = 0
    dry_run: bool = False


def _count(table: Table, company_id: uuid.UUID) -> int:
    return db.session.execute(select(func.count()).select_from(table).where(table.c.company_id == company_id)).scalar_one()


def _user_has_other_membership(user_id: uuid.UUID) -> bool:
    # Política memberships_own_user: com app.user_id = este usuário, o RLS mostra os vínculos
    # dele em TODAS as empresas (os da empresa expurgada já foram apagados).
    rls.set_context(user_id=user_id)
    return bool(
        db.session.execute(select(func.count()).select_from(Membership).where(Membership.user_id == user_id)).scalar_one()
    )


def purge_company(company_id: uuid.UUID, *, operator: str, now: datetime | None = None, dry_run: bool = False) -> PurgeResult | None:
    """Apaga a empresa e tudo dela. ``None`` se ela já não existe (idempotente).

    Recusa empresa sem pedido de exclusão ou ainda na carência (o comando nunca apaga por
    engano uma empresa ativa). Faz commit (exceto em ``dry_run``)."""
    now = now or _now()
    company = db.session.get(Company, company_id)
    if company is None:
        return None
    when = purge_date(company)
    if when is None or when > now:
        raise LgpdError("Empresa sem pedido de exclusão ou ainda na carência.")
    result = PurgeResult(company_id=company_id, dry_run=dry_run)
    rls.set_context(company_id=company_id, user_id=None)
    try:
        # Conta de suporte da plataforma não é dado da empresa: o vínculo some, a conta fica.
        member_ids = list(
            db.session.execute(
                select(Membership.user_id).where(Membership.company_id == company_id, Membership.is_support.is_(False))
            ).scalars()
        )
        requested_at = _aware(company.deletion_requested_at)
        for table in reversed(company_tables()):
            if dry_run:
                result.rows[table.name] = _count(table, company_id)
            else:
                result.rows[table.name] = db.session.execute(
                    delete(table).where(table.c.company_id == company_id)
                ).rowcount or 0
        if dry_run:
            db.session.rollback()
            result.users_deleted = len(member_ids)  # máximo possível (sem conferir outros vínculos)
            return result
        db.session.expunge_all()
        for user_id in set(member_ids):
            if _user_has_other_membership(user_id):
                continue
            user = db.session.get(User, user_id)
            if user is None:
                continue
            from app.services import lockout

            db.session.execute(
                delete(LoginThrottle.__table__).where(LoginThrottle.key_hash == lockout._key("account", user.email))
            )
            for model in USER_CHILD_MODELS:
                db.session.execute(delete(model.__table__).where(model.user_id == user_id))
            db.session.execute(delete(User.__table__).where(User.__table__.c.id == user_id))
            result.users_deleted += 1
        rls.set_context(company_id=None, user_id=None)
        db.session.execute(delete(Company.__table__).where(Company.__table__.c.id == company_id))
        db.session.add(
            PlatformAuditLog(
                action=COMPANY_PURGED,
                subject_company_id=company_id,
                operator=operator[:120],
                details={
                    "requested_at": requested_at.isoformat() if requested_at else None,
                    "rows": {k: v for k, v in result.rows.items() if v},
                    "users_deleted": result.users_deleted,
                },
            )
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    finally:
        rls.set_context(company_id=None, user_id=None)
    return result


def purge_due(*, operator: str, now: datetime | None = None, dry_run: bool = False) -> list[PurgeResult]:
    results = []
    for company_id in [c.id for c in due_for_purge(now)]:
        result = purge_company(company_id, operator=operator, now=now, dry_run=dry_run)
        if result is not None:
            results.append(result)
    return results


# ---------------------------------------------------------------- retenção


def _days(key: str, default: int) -> timedelta:
    return timedelta(days=int(current_app.config.get(key, default)))


def apply_retention(*, operator: str, now: datetime | None = None, dry_run: bool = False) -> dict[str, int]:
    """Apaga o que passou do prazo de retenção (docs/plano/lgpd.md §Retenção). Commit no fim."""
    now = now or _now()
    tokens_limit = now - _days("RETENTION_TOKENS_DAYS", 30)
    counts: dict[str, int] = {}

    def run(name: str, stmt) -> None:
        if dry_run:
            sub = stmt.whereclause
            table = stmt.table
            n = db.session.execute(select(func.count()).select_from(table).where(sub)).scalar_one()
        else:
            n = db.session.execute(stmt).rowcount or 0
        counts[name] = counts.get(name, 0) + n

    # Plataforma (sem RLS).
    run(
        "login_throttles",
        delete(LoginThrottle.__table__).where(LoginThrottle.last_failure_at < now - _days("RETENTION_THROTTLE_DAYS", 30)),
    )
    for model in (PasswordReset, EmailConfirmation):
        run(
            model.__tablename__,
            delete(model.__table__).where(
                model.created_at < tokens_limit, or_(model.used_at.is_not(None), model.expires_at < now)
            ),
        )
    run(
        "platform_audit_logs",
        delete(PlatformAuditLog.__table__).where(
            PlatformAuditLog.__table__.c.at < now - _days("RETENTION_AUDIT_DAYS", 5 * 365)
        ),
    )
    # Por empresa (com RLS ligado, cada uma no próprio contexto).
    from app.services.api_tokens import API_REQUEST

    audit_table = AuditLog.__table__
    for company_id in list(db.session.execute(select(Company.id)).scalars()):
        rls.set_context(company_id=company_id)
        run(
            "invitations",
            delete(Invitation.__table__).where(
                Invitation.company_id == company_id,
                Invitation.created_at < tokens_limit,
                or_(Invitation.used_at.is_not(None), Invitation.revoked_at.is_not(None), Invitation.expires_at < now),
            ),
        )
        run(
            "domain_events",
            delete(DomainEvent.__table__).where(
                DomainEvent.company_id == company_id,
                DomainEvent.published_at.is_not(None),
                DomainEvent.published_at < now - _days("RETENTION_EVENTS_DAYS", 90),
            ),
        )
        run(
            "audit_logs",
            delete(audit_table).where(
                audit_table.c.company_id == company_id,
                or_(
                    and_(audit_table.c.action == API_REQUEST, audit_table.c.at < now - _days("RETENTION_API_REQUEST_DAYS", 183)),
                    audit_table.c.at < now - _days("RETENTION_AUDIT_DAYS", 5 * 365),
                ),
            ),
        )
    rls.set_context(company_id=None)
    if dry_run:
        db.session.rollback()
        return counts
    db.session.add(
        PlatformAuditLog(action=RETENTION_APPLIED, operator=operator[:120], details={k: v for k, v in counts.items() if v})
    )
    db.session.commit()
    return counts


TOKENS_PURGED = "worker.tokens_purged"


def purge_expired_tokens(*, operator: str, now: datetime | None = None) -> dict[str, int]:
    """Etapa F (tarefa ``tokens`` do worker): só a parte de tokens da retenção — resets de
    senha, confirmações de e-mail e convites usados/vencidos/revogados há mais de
    ``RETENTION_TOKENS_DAYS``. Idempotente; convites empresa a empresa no contexto RLS dela.
    Registra em ``platform_audit_logs`` só quando apagou algo (só contagens)."""
    now = now or _now()
    limit = now - _days("RETENTION_TOKENS_DAYS", 30)
    counts: dict[str, int] = {}
    for model in (PasswordReset, EmailConfirmation):
        stmt = delete(model.__table__).where(
            model.created_at < limit, or_(model.used_at.is_not(None), model.expires_at < now)
        )
        counts[model.__tablename__] = db.session.execute(stmt).rowcount or 0
    counts["invitations"] = 0
    try:
        for company_id in list(db.session.execute(select(Company.id)).scalars()):
            rls.set_context(company_id=company_id)
            counts["invitations"] += db.session.execute(
                delete(Invitation.__table__).where(
                    Invitation.company_id == company_id,
                    Invitation.created_at < limit,
                    or_(Invitation.used_at.is_not(None), Invitation.revoked_at.is_not(None), Invitation.expires_at < now),
                )
            ).rowcount or 0
    finally:
        rls.set_context(company_id=None)
    if any(counts.values()):
        db.session.add(
            PlatformAuditLog(action=TOKENS_PURGED, operator=operator[:120], details={k: v for k, v in counts.items() if v})
        )
    db.session.commit()
    return counts
