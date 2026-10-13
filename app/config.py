"""Configuração por ambiente. Tudo vem de variáveis de ambiente (ver .env.example)."""

from __future__ import annotations

import os
import secrets


def _bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


def _database_url(default: str | None) -> str | None:
    return _database_url_raw(os.environ.get("DATABASE_URL") or default)


def _database_url_raw(url: str | None) -> str | None:
    # Render/Heroku entregam "postgres://"; o SQLAlchemy 2 + psycopg 3 querem este prefixo.
    if url and url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://") :]
    elif url and url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


class Config:
    ENV_NAME = "base"
    SECRET_KEY: str | None = None
    DEFAULT_DATABASE_URL: str | None = None
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sessão
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_NAME = "__Host-session"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 12  # 12 h

    # CSRF em todo POST
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 60 * 60 * 8
    # Sem Flask-Babel: as mensagens vêm das traduções do próprio WTForms (Meta.locales em forms.py).
    WTF_I18N_ENABLED = False

    # Rate limit (memória na Fase 0; Redis em produção a partir da Fase 5/7)
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_HEADERS_ENABLED = True
    LOGIN_RATE_LIMIT = "10 per minute; 50 per hour"
    SIGNUP_RATE_LIMIT = "5 per minute; 20 per hour"

    RLS_ENABLED = False
    FEATURE_PUBLIC_API = False

    # Fase 5 — contas
    # Limites extras (além do bloqueio progressivo por conta/IP de app/services/lockout.py).
    PASSWORD_RESET_RATE_LIMIT = "5 per minute; 20 per hour"
    MFA_RATE_LIMIT = "10 per minute; 50 per hour"
    INVITE_RATE_LIMIT = "20 per minute; 100 per hour"
    EMAIL_RESEND_RATE_LIMIT = "3 per minute; 10 per hour"
    # Bloqueio progressivo: N falhas seguidas → espera 1, 5, 15, 60 min (o último se repete).
    LOCKOUT_ACCOUNT_THRESHOLD = 5
    LOCKOUT_IP_THRESHOLD = 20
    LOCKOUT_STEPS_MINUTES = (1, 5, 15, 60)
    LOCKOUT_RESET_HOURS = 24  # falhas mais antigas que isto deixam de contar
    # E-mail: "console" (guarda em memória e, em development, grava .eml em instance/emails)
    # ou "resend" (API HTTP). Sem MAIL_BACKEND: resend se houver RESEND_API_KEY, senão console.
    MAIL_BACKEND: str | None = None
    MAIL_FROM = "Controle de Produção <nao-responda@localhost>"
    RESEND_API_KEY: str | None = None
    MAIL_TIMEOUT_SECONDS = 10
    # Base dos links enviados por e-mail (https://app.exemplo.com.br). Fora de development/test
    # é obrigatória na hora de enviar: o host da requisição não é confiável (host header).
    APP_BASE_URL: str | None = None
    # Chave do Fernet que cifra o segredo TOTP (derivada por HKDF). Sem valor: SECRET_KEY.
    MFA_ENCRYPTION_KEY: str | None = None

    @classmethod
    def from_env(cls) -> dict:
        """Lê as variáveis de ambiente na hora de criar o app (não na importação)."""
        values: dict = {
            "SECRET_KEY": os.environ.get("SECRET_KEY") or cls.SECRET_KEY,
            "SQLALCHEMY_DATABASE_URI": _database_url(cls.DEFAULT_DATABASE_URL),
            "RATELIMIT_ENABLED": _bool("RATELIMIT_ENABLED", cls.RATELIMIT_ENABLED),
            "RATELIMIT_STORAGE_URI": os.environ.get("RATELIMIT_STORAGE_URI", cls.RATELIMIT_STORAGE_URI),
            "RLS_ENABLED": _bool("RLS_ENABLED", cls.RLS_ENABLED),
            "FEATURE_PUBLIC_API": _bool("FEATURE_PUBLIC_API", cls.FEATURE_PUBLIC_API),
        }
        for key in (
            "LOGIN_RATE_LIMIT",
            "SIGNUP_RATE_LIMIT",
            "PASSWORD_RESET_RATE_LIMIT",
            "MFA_RATE_LIMIT",
            "INVITE_RATE_LIMIT",
            "EMAIL_RESEND_RATE_LIMIT",
        ):
            values[key] = os.environ.get(key, getattr(cls, key))
        for key in ("MAIL_BACKEND", "MAIL_FROM", "RESEND_API_KEY", "APP_BASE_URL", "MFA_ENCRYPTION_KEY"):
            values[key] = os.environ.get(key) or getattr(cls, key)
        return values


class DevelopmentConfig(Config):
    ENV_NAME = "development"
    DEBUG = True
    DEFAULT_DATABASE_URL = "sqlite:///dev.db"
    # http://localhost não aceita cookie Secure nem o prefixo __Host-.
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_NAME = "session"
    REMEMBER_COOKIE_SECURE = False


class TestConfig(Config):
    ENV_NAME = "test"
    TESTING = True
    SECRET_KEY = "chave-so-para-testes"
    SQLALCHEMY_ENGINE_OPTIONS: dict = {}
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_NAME = "session"
    REMEMBER_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False

    @classmethod
    def from_env(cls) -> dict:
        values = super().from_env()
        # Testes nunca usam DATABASE_URL (evita apagar um banco real por engano).
        values["SQLALCHEMY_DATABASE_URI"] = _database_url_raw(os.environ.get("TEST_DATABASE_URL")) or "sqlite://"
        values["RATELIMIT_ENABLED"] = False
        # Testes nunca mandam e-mail de verdade: backend console (caixa em memória).
        values["MAIL_BACKEND"] = "console"
        values["RESEND_API_KEY"] = None
        return values


class ProductionConfig(Config):
    ENV_NAME = "production"


class StagingConfig(ProductionConfig):
    ENV_NAME = "staging"


CONFIGS: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "test": TestConfig,
    "testing": TestConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> type[Config]:
    name = (name or os.environ.get("APP_ENV") or os.environ.get("FLASK_ENV") or "production").lower()
    try:
        return CONFIGS[name]
    except KeyError:
        raise RuntimeError(f"Ambiente desconhecido: {name!r}") from None


def finalize_config(app_config: dict, env_name: str) -> None:
    """Valida o que é obrigatório. Fora de development/test, SECRET_KEY e DATABASE_URL são exigidos."""
    if env_name in {"development", "test"}:
        if not app_config.get("SECRET_KEY"):
            # Chave efêmera só em desenvolvimento: as sessões caem a cada reinício.
            app_config["SECRET_KEY"] = secrets.token_hex(32)
        return
    if not app_config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY é obrigatório fora de development/test.")
    if not app_config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("DATABASE_URL é obrigatório fora de development/test.")
