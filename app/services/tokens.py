"""Tokens de uso único (confirmação de e-mail, reset de senha, convite).

- 32 bytes aleatórios (``secrets.token_urlsafe``) vão SÓ no link do e-mail.
- No banco fica só o SHA-256 em hex (64 caracteres). O token tem entropia alta, então um
  hash rápido basta (não é senha); a busca é pela igualdade do hash no índice UNIQUE.
- Nunca logar o token nem o link.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

TOKEN_BYTES = 32
# Formato aceito na URL: base64url sem padding (43 caracteres para 32 bytes). Rejeitar cedo
# o que não tem essa cara evita consulta à toa.
_ALPHABET = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")


def new_token() -> tuple[str, str]:
    """Devolve (token em claro para o link, hash para o banco)."""
    token = secrets.token_urlsafe(TOKEN_BYTES)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def looks_valid(token: str | None) -> bool:
    return bool(token) and 20 <= len(token) <= 100 and all(ch in _ALPHABET for ch in token)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def aware(value: datetime | None) -> datetime | None:
    """SQLite devolve datetime sem fuso mesmo em DateTime(timezone=True): trata como UTC."""
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def is_expired(expires_at: datetime, now: datetime | None = None) -> bool:
    return aware(expires_at) <= (now or utcnow())
