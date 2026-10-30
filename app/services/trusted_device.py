"""Cookie de dispositivo confiável (para o bloqueio de login por IP).

Com o IP bloqueado (muitas senhas erradas vindas dele), o login NÃO verifica credenciais —
resposta genérica de bloqueio, o que barra password spraying —, EXCETO para contas que já
entraram com sucesso neste navegador. Assim, um atacante atrás do mesmo NAT/proxy não tranca
quem já usa o sistema.

O cookie é assinado (itsdangerous, salt próprio, validade de 90 dias), HttpOnly, Secure
(quando a sessão é Secure), SameSite=Lax, e guarda só hashes SHA-256 dos ids (até 5 contas
por navegador). Não autentica ninguém: só libera a verificação da senha.
"""

from __future__ import annotations

import hashlib
import uuid

from flask import current_app, g, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.security import signing_keys

MAX_AGE_SECONDS = 90 * 24 * 3600
MAX_ACCOUNTS = 5
_SALT = "dispositivo-confiavel-v1"


def cookie_name() -> str:
    return "__Host-dispositivo" if current_app.config.get("SESSION_COOKIE_SECURE") else "dispositivo"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(signing_keys(), salt=_SALT)


def _hash(user_id: uuid.UUID | str) -> str:
    return hashlib.sha256(f"device:{user_id}".encode()).hexdigest()


def _known() -> list[str]:
    raw = request.cookies.get(cookie_name())
    if not raw:
        return []
    try:
        data = _serializer().loads(raw, max_age=MAX_AGE_SECONDS)
    except BadSignature:
        return []
    return [h for h in data if isinstance(h, str)][:MAX_ACCOUNTS] if isinstance(data, list) else []


def is_trusted(user_id: uuid.UUID | str) -> bool:
    return _hash(user_id) in _known()


def remember(user_id: uuid.UUID | str) -> None:
    """Marca para o after_request gravar o cookie na resposta deste login."""
    g.trusted_device_user = str(user_id)


def apply(response):
    """after_request: renova o cookie com a conta que acabou de entrar (no topo da lista)."""
    user_id = g.get("trusted_device_user")
    if not user_id:
        return response
    entry = _hash(user_id)
    hashes = [entry] + [h for h in _known() if h != entry]
    response.set_cookie(
        cookie_name(),
        _serializer().dumps(hashes[:MAX_ACCOUNTS]),
        max_age=MAX_AGE_SECONDS,
        httponly=True,
        secure=bool(current_app.config.get("SESSION_COOKIE_SECURE")),
        samesite="Lax",
        path="/",
    )
    return response
