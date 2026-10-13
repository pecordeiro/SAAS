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
    # API pública (Fase 9): limite por token e teto por IP.
    API_RATE_LIMIT = "120 per minute"
    API_RATE_LIMIT_IP = "600 per minute"

    # Assinatura/planos (app/services/entitlements.py). Sem assinatura ativa a empresa fica
    # em modo leitura (402 em escrita) — READ_ONLY_ENFORCED=0 desliga a regra.
    READ_ONLY_ENFORCED = True
    TRIAL_DAYS = 14
    DEFAULT_TRIAL_PLAN = "profissional"
    PAST_DUE_GRACE_DAYS = 7

    # Importação (app/services/importer.py): arquivo lido em memória, nunca gravado em disco.
    IMPORT_MAX_BYTES = 2 * 1024 * 1024
    # Teto de qualquer corpo de requisição (o maior é o upload da importação): acima disso o
    # Werkzeug recusa com 413 antes de ler o corpo (inclusive antes do CSRF).
    MAX_CONTENT_LENGTH = IMPORT_MAX_BYTES + 256 * 1024

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
            "API_RATE_LIMIT": os.environ.get("API_RATE_LIMIT", cls.API_RATE_LIMIT),
            "API_RATE_LIMIT_IP": os.environ.get("API_RATE_LIMIT_IP", cls.API_RATE_LIMIT_IP),
            "READ_ONLY_ENFORCED": _bool("READ_ONLY_ENFORCED", cls.READ_ONLY_ENFORCED),
            "TRIAL_DAYS": int(os.environ.get("TRIAL_DAYS", cls.TRIAL_DAYS)),
            "DEFAULT_TRIAL_PLAN": os.environ.get("DEFAULT_TRIAL_PLAN", cls.DEFAULT_TRIAL_PLAN),
            "PAST_DUE_GRACE_DAYS": int(os.environ.get("PAST_DUE_GRACE_DAYS", cls.PAST_DUE_GRACE_DAYS)),
        }
        for key in ("LOGIN_RATE_LIMIT", "SIGNUP_RATE_LIMIT"):
            values[key] = os.environ.get(key, getattr(cls, key))
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
