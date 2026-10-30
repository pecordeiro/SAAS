"""Tokens da API pública (Fase 9): criação, autenticação e revogação.

- O token é ``cp_`` + 43 caracteres aleatórios (``secrets.token_urlsafe(32)``). O texto puro
  só existe na resposta da criação (mostrado uma vez); no banco fica o SHA-256 em hex
  (``token_hash``) e um prefixo curto (``token_prefix``) só para identificar na tela.
  Como o token tem 256 bits de entropia, SHA-256 simples basta (sem sal nem KDF lento).
- ``find_by_raw`` é o ÚNICO ponto que busca token antes de saber a empresa (ADR-0003): com
  ``RLS_ENABLED`` ligado ele precisa de papel de plataforma (BYPASSRLS) ou de uma função
  ``SECURITY DEFINER`` estreita (pendência registrada em docs/plano/progresso.md, Fase 9).
- Nunca grave o token puro em log, auditoria ou ``details``.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.extensions import db
from app.models import ApiClient, ApiToken, Company
from app.services import audit

TOKEN_PREFIX = "cp_"
TOKEN_MAX_LENGTH = 128  # recusa lixo gigante antes de calcular o hash

SCOPE_READ_PROJECTS = "read:projects"
SCOPE_WRITE_PROGRESS = "write:progress"
SCOPES: dict[str, str] = {
    SCOPE_READ_PROJECTS: "Ler projetos, resumos e eventos",
    SCOPE_WRITE_PROGRESS: "Registrar progresso de subatividades",
}
EXPIRY_CHOICES: tuple[tuple[str, str], ...] = (
    ("30", "30 dias"),
    ("90", "90 dias"),
    ("365", "1 ano"),
    ("0", "Sem expiração"),
)

TOKEN_CREATED = "api_token.created"
TOKEN_REVOKED = "api_token.revoked"
API_REQUEST = "api.request"

# Motivos de recusa (viram o ``code`` do erro RFC 9457)
INVALID = "invalid_token"
REVOKED = "token_revoked"
EXPIRED = "token_expired"


class TokenError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _aware(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    value = _aware(value)
    return value.astimezone(timezone.utc).isoformat() if value else None


@dataclass
class CreatedToken:
    token: ApiToken
    raw: str  # exibido uma única vez


def create_token(
    company: Company, *, name: str, scopes: list[str], expires_in_days: int | None, user_id: uuid.UUID | None
) -> CreatedToken:
    """Cria a integração (``api_clients``) e o token. Sem commit. Escopo desconhecido → ValueError."""
    clean = sorted(set(scopes))
    if not clean or any(s not in SCOPES for s in clean):
        raise ValueError("Escolha ao menos um escopo válido.")
    client = ApiClient(company_id=company.id, name=name, created_by_user_id=user_id)
    db.session.add(client)
    db.session.flush()
    raw = TOKEN_PREFIX + secrets.token_urlsafe(32)
    token = ApiToken(
        company_id=company.id,
        api_client_id=client.id,
        token_hash=hash_token(raw),
        token_prefix=raw[:11],
        scopes=clean,
        expires_at=_now() + timedelta(days=expires_in_days) if expires_in_days else None,
    )
    db.session.add(token)
    db.session.flush()
    audit.record(
        TOKEN_CREATED,
        company_id=company.id,
        actor_user_id=user_id,
        object_type="api_token",
        object_id=token.id,
        details={"name": name, "scopes": clean, "prefix": token.token_prefix, "expires_at": _iso(token.expires_at)},
    )
    return CreatedToken(token, raw)


def find_by_raw(raw: str) -> ApiToken | None:
    """Token pelo texto recebido (busca por hash, ainda sem empresa). None se não existe."""
    if not raw.startswith(TOKEN_PREFIX) or len(raw) > TOKEN_MAX_LENGTH:
        return None
    token_hash = hash_token(raw)
    # RLS (Fase 7, política api_tokens_by_token): antes de saber a empresa, o banco só deixa
    # ler a linha cujo hash é o do token apresentado — ter o token é a autorização.
    from app import rls

    rls.set_context(token_hash=token_hash)
    return db.session.execute(select(ApiToken).where(ApiToken.token_hash == token_hash)).scalar_one_or_none()


def check_usable(token: ApiToken, now: datetime | None = None) -> None:
    """Levanta ``TokenError`` se revogado (token ou integração) ou expirado."""
    now = now or _now()
    if token.revoked_at is not None or token.client.revoked_at is not None:
        raise TokenError(REVOKED)
    expires = _aware(token.expires_at)
    if expires is not None and expires <= now:
        raise TokenError(EXPIRED)


def status_of(token: ApiToken, now: datetime | None = None) -> str:
    """``active`` | ``revoked`` | ``expired`` (para a tela)."""
    try:
        check_usable(token, now)
    except TokenError as exc:
        return "revoked" if exc.code == REVOKED else "expired"
    return "active"


def list_tokens(company_id: uuid.UUID) -> list[ApiToken]:
    return list(
        db.session.execute(
            select(ApiToken).where(ApiToken.company_id == company_id).order_by(ApiToken.created_at.desc())
        ).scalars()
    )


def revoke(token: ApiToken, user_id: uuid.UUID | None) -> bool:
    """Revoga token e integração. Idempotente (False se já estava revogado). Sem commit."""
    if token.revoked_at is not None:
        return False
    now = _now()
    token.revoked_at = now
    if token.client.revoked_at is None:
        token.client.revoked_at = now
    audit.record(
        TOKEN_REVOKED,
        company_id=token.company_id,
        actor_user_id=user_id,
        object_type="api_token",
        object_id=token.id,
        details={"name": token.client.name, "prefix": token.token_prefix},
    )
    return True
