"""MFA TOTP (pyotp) com segredo cifrado e códigos de recuperação.

- Segredo TOTP cifrado com Fernet; a chave é derivada por HKDF-SHA256 de
  ``MFA_ENCRYPTION_KEY`` (ou, sem ela, de ``SECRET_KEY``). Trocar a chave invalida os
  segredos gravados (os usuários precisam reativar o MFA) — rotação fica documentada.
- QR code em SVG gerado no servidor (segno), sem serviço de terceiros.
- Códigos de recuperação: 10 códigos aleatórios, mostrados uma vez; no banco só o SHA-256;
  uso único.
- Código TOTP aceito uma vez só: ``users.totp_last_step`` guarda o último passo usado.
"""

from __future__ import annotations

import base64
import hashlib
import io
import secrets
import time

import pyotp
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from flask import current_app
from sqlalchemy import delete, select

from app.extensions import db
from app.models import MfaRecoveryCode, User
from app.services.tokens import utcnow

ISSUER = "Controle de Produção"
RECOVERY_CODES = 10
_RECOVERY_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"  # sem 0/o/1/l/i


def _fernet() -> Fernet:
    secret = current_app.config.get("MFA_ENCRYPTION_KEY") or current_app.config["SECRET_KEY"]
    key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"controle-producao/mfa",
        info=b"totp-secret-v1",
    ).derive(secret.encode("utf-8"))
    return Fernet(base64.urlsafe_b64encode(key))


def new_secret() -> str:
    return pyotp.random_base32()


def encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode("ascii")).decode("ascii")


def decrypt_secret(token: str) -> str | None:
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("ascii")
    except (InvalidToken, ValueError):
        return None


def provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER)


def qr_svg(uri: str) -> bytes:
    import segno

    buffer = io.BytesIO()
    segno.make(uri, error="m").save(buffer, kind="svg", scale=6, border=2, xmldecl=False, svgns=True, title="QR code do MFA")
    return buffer.getvalue()


def _clean_code(code: str | None) -> str:
    return "".join(ch for ch in (code or "") if not ch.isspace() and ch != "-").lower()


def check_totp(secret: str, code: str | None, last_step: int | None = None, at: float | None = None) -> int | None:
    """Devolve o passo aceito (para gravar em totp_last_step) ou None. Janela ±1 passo."""
    code = _clean_code(code)
    if len(code) != 6 or not code.isdigit():
        return None
    totp = pyotp.TOTP(secret)
    now = time.time() if at is None else at
    current = int(now // totp.interval)
    for step in (current - 1, current, current + 1):
        if last_step is not None and step <= last_step:
            continue
        if secrets.compare_digest(totp.at(step * totp.interval), code):
            return step
    return None


def verify_user_totp(user: User, code: str | None) -> bool:
    if not user.totp_secret_enc:
        return False
    secret = decrypt_secret(user.totp_secret_enc)
    if secret is None:
        return False
    step = check_totp(secret, code, user.totp_last_step)
    if step is None:
        return False
    user.totp_last_step = step
    return True


def _hash_code(code: str) -> str:
    return hashlib.sha256(_clean_code(code).encode()).hexdigest()


def new_recovery_codes(user: User) -> list[str]:
    """Troca os códigos do usuário por 10 novos (devolvidos em claro só aqui). Sem commit."""
    db.session.execute(delete(MfaRecoveryCode).where(MfaRecoveryCode.user_id == user.id))
    codes = []
    for _ in range(RECOVERY_CODES):
        raw = "".join(secrets.choice(_RECOVERY_ALPHABET) for _ in range(10))
        codes.append(f"{raw[:5]}-{raw[5:]}")
    db.session.add_all(MfaRecoveryCode(user_id=user.id, code_hash=_hash_code(c)) for c in codes)
    return codes


def use_recovery_code(user: User, code: str | None) -> bool:
    cleaned = _clean_code(code)
    if len(cleaned) != 10:
        return False
    row = db.session.execute(
        select(MfaRecoveryCode)
        .where(
            MfaRecoveryCode.user_id == user.id,
            MfaRecoveryCode.code_hash == _hash_code(cleaned),
            MfaRecoveryCode.used_at.is_(None),
        )
        .with_for_update()
    ).scalar_one_or_none()
    if row is None:
        return False
    row.used_at = utcnow()
    return True


def remaining_recovery_codes(user: User) -> int:
    return len(
        db.session.execute(
            select(MfaRecoveryCode.id).where(MfaRecoveryCode.user_id == user.id, MfaRecoveryCode.used_at.is_(None))
        ).all()
    )


def enable(user: User, secret: str) -> list[str]:
    user.totp_secret_enc = encrypt_secret(secret)
    user.mfa_enabled = True
    return new_recovery_codes(user)


def disable(user: User) -> None:
    user.totp_secret_enc = None
    user.mfa_enabled = False
    user.totp_last_step = None
    db.session.execute(delete(MfaRecoveryCode).where(MfaRecoveryCode.user_id == user.id))
