"""Bloqueio progressivo de login por conta e por IP (tabela ``login_throttles``).

- Cada senha (ou código MFA) errada soma uma falha na chave da conta (e-mail normalizado,
  exista ou não a conta — o comportamento não revela cadastro) e na chave do IP.
- Ao atingir o limite (5 por conta, 20 por IP — escritórios dividem IP), a chave fica
  bloqueada por 1 min; cada falha seguinte aumenta para 5, 15, 60 min (o último se repete).
- Login certo zera a chave da conta. A do IP não zera (senão quem tem uma conta válida
  "limparia" o IP entre tentativas); ela expira sozinha após LOCKOUT_RESET_HOURS sem falha.
- As chaves são guardadas só como SHA-256 (nada de e-mail ou IP em claro nesta tabela).
- Complementa o Flask-Limiter (limite por minuto), que continua valendo.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import THROTTLE_ACCOUNT, THROTTLE_IP, LoginThrottle
from app.services.tokens import aware, utcnow


@dataclass(frozen=True)
class LockStatus:
    locked: bool
    retry_after_seconds: int = 0

    @property
    def minutes(self) -> int:
        return max(1, math.ceil(self.retry_after_seconds / 60))


def _key(scope: str, value: str) -> str:
    return hashlib.sha256(f"{scope}:{(value or '').strip().lower()}".encode()).hexdigest()


def _keys(email: str | None, ip: str | None) -> list[tuple[str, str]]:
    keys = []
    if email:
        keys.append((THROTTLE_ACCOUNT, _key(THROTTLE_ACCOUNT, email)))
    if ip:
        keys.append((THROTTLE_IP, _key(THROTTLE_IP, ip)))
    return keys


def _row(scope: str, key_hash: str) -> LoginThrottle | None:
    return db.session.execute(
        select(LoginThrottle).where(LoginThrottle.scope == scope, LoginThrottle.key_hash == key_hash).with_for_update()
    ).scalar_one_or_none()


def status(email: str | None, ip: str | None, now: datetime | None = None) -> LockStatus:
    now = now or utcnow()
    wait = 0
    for scope, key_hash in _keys(email, ip):
        row = db.session.execute(
            select(LoginThrottle).where(LoginThrottle.scope == scope, LoginThrottle.key_hash == key_hash)
        ).scalar_one_or_none()
        until = aware(row.locked_until) if row is not None else None
        if until and until > now:
            wait = max(wait, math.ceil((until - now).total_seconds()))
    return LockStatus(locked=wait > 0, retry_after_seconds=wait)


def _threshold(scope: str) -> int:
    cfg = current_app.config
    return int(cfg["LOCKOUT_ACCOUNT_THRESHOLD"] if scope == THROTTLE_ACCOUNT else cfg["LOCKOUT_IP_THRESHOLD"])


def register_failure(email: str | None, ip: str | None, now: datetime | None = None) -> LockStatus:
    """Soma uma falha nas chaves e grava (commit próprio: vale mesmo se a requisição falhar)."""
    now = now or utcnow()
    steps = [int(m) for m in current_app.config["LOCKOUT_STEPS_MINUTES"]]
    reset_after = timedelta(hours=int(current_app.config["LOCKOUT_RESET_HOURS"]))
    for scope, key_hash in _keys(email, ip):
        for _attempt in range(2):  # 2ª volta só se outra requisição inseriu a mesma chave
            row = _row(scope, key_hash)
            if row is None:
                row = LoginThrottle(scope=scope, key_hash=key_hash, failures=0, last_failure_at=now)
                db.session.add(row)
            elif aware(row.last_failure_at) < now - reset_after:
                row.failures = 0
                row.locked_until = None
            row.failures += 1
            row.last_failure_at = now
            threshold = _threshold(scope)
            if row.failures >= threshold:
                step = steps[min(row.failures - threshold, len(steps) - 1)]
                row.locked_until = now + timedelta(minutes=step)
            try:
                db.session.commit()
                break
            except IntegrityError:
                db.session.rollback()
    return status(email, ip, now)


def register_success(email: str | None) -> None:
    """Zera a chave da conta (não a do IP). Não faz commit."""
    if email:
        db.session.execute(
            delete(LoginThrottle).where(
                LoginThrottle.scope == THROTTLE_ACCOUNT,
                LoginThrottle.key_hash == _key(THROTTLE_ACCOUNT, email),
            )
        )
