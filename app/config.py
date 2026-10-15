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
    # Fase 7: prefixo __Host- (só HTTPS, Path=/, sem Domain) e SameSite em todo cookie de sessão.
    REMEMBER_COOKIE_NAME = "__Host-remember"
    REMEMBER_COOKIE_SAMESITE = "Lax"
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
    # Quantos proxies confiáveis (Render = 1) põem X-Forwarded-For/Proto na frente do app.
    # 0 = ignora esses headers (padrão; qualquer cliente poderia forjá-los).
    TRUSTED_PROXY_COUNT = 0

    # Assinatura/planos (app/services/entitlements.py). Sem assinatura ativa a empresa fica
    # em modo leitura (402 em escrita) — READ_ONLY_ENFORCED=0 desliga a regra.
    READ_ONLY_ENFORCED = True
    TRIAL_DAYS = 14
    DEFAULT_TRIAL_PLAN = "profissional"
    PAST_DUE_GRACE_DAYS = 7

    # Fase 8 — cobrança (app/services/billing). Segredos só por variável de ambiente.
    # BILLING_PROVIDER vazio = "asaas" se houver ASAAS_API_KEY, senão "fake" (só dev/test).
    BILLING_PROVIDER = ""
    ASAAS_API_KEY: str | None = None
    ASAAS_BASE_URL = "https://api-sandbox.asaas.com/v3"
    ASAAS_WEBHOOK_TOKEN: str | None = None
    WEBHOOK_RATE_LIMIT = "120 per minute"
    # Hosts aceitos no redirecionamento para a página de pagamento (anti open redirect).
    BILLING_CHECKOUT_HOSTS = ("www.asaas.com", "asaas.com", "sandbox.asaas.com", "pagamento.fake.invalid")

    # E-mail público de contato mostrado em /contato (só texto; não há formulário).
    CONTACT_EMAIL = "contato@controledeproducao.example"

    # Importação (app/services/importer.py): arquivo lido em memória, nunca gravado em disco.
    IMPORT_MAX_BYTES = 2 * 1024 * 1024
    # Teto de qualquer corpo de requisição (o maior é o upload da importação): acima disso o
    # Werkzeug recusa com 413 antes de ler o corpo (inclusive antes do CSRF).
    MAX_CONTENT_LENGTH = IMPORT_MAX_BYTES + 256 * 1024

    # Fase 7 — segurança e LGPD (app/security.py, app/logging_config.py, app/services/lgpd.py)
    # Rotação: chaves antigas que ainda VALIDAM (sessão, prévia de importação, dispositivo
    # confiável); só SECRET_KEY assina. Lista separada por vírgula no env.
    SECRET_KEY_FALLBACKS: list = []
    IMPORT_RATE_LIMIT = "10 per minute; 60 per hour"
    WEBHOOK_RATE_LIMIT = "120 per minute"
    LGPD_EXPORT_RATE_LIMIT = "3 per hour"
    LGPD_DELETE_RATE_LIMIT = "5 per hour"
    # Logs JSON em stdout (LOG_JSON=0 volta ao texto simples, útil no terminal de dev).
    LOG_JSON = True
    LOG_LEVEL = "INFO"
    # Sentry opcional (sem DSN = desligado). Nunca manda PII (ver app/logging_config.py).
    SENTRY_DSN: str | None = None
    SENTRY_TRACES_SAMPLE_RATE = 0.0
    # LGPD: carência da exclusão da empresa e retenção (dias). Ver docs/plano/lgpd.md.
    LGPD_DELETION_GRACE_DAYS = 30
    RETENTION_API_REQUEST_DAYS = 183  # registros de acesso (Marco Civil, art. 15: 6 meses)
    RETENTION_AUDIT_DAYS = 5 * 365
    RETENTION_EVENTS_DAYS = 90  # domain_events já publicados
    RETENTION_TOKENS_DAYS = 30  # convites/resets/confirmações usados ou vencidos
    RETENTION_THROTTLE_DAYS = 30
    # Acesso de suporte (flask suporte conceder): teto de horas por concessão.
    SUPPORT_ACCESS_MAX_HOURS = 72
    # Etapa F — worker (flask worker run, ADR-0010).
    WORKER_INTERVAL_SECONDS = 30  # pausa entre ciclos do laço
    WORKER_EVENT_MAX_ATTEMPTS = 8  # depois disso o evento sai da fila (flask worker status)
    # Aviso à equipe da plataforma (requisição de identidade visual). Vazio = sem aviso.
    STAFF_NOTIFY_EMAIL: str | None = None

    # Etapa G — fotos, comentários, checklist e unidades (app/services/storage.py, photos.py).
    # STORAGE_BACKEND: local (disco em instance/uploads, só development/test) | s3 (R2/AWS/MinIO)
    # | none. Vazio = local em development/test e none (fotos desligadas) fora deles.
    STORAGE_BACKEND = ""
    STORAGE_LOCAL_DIR: str | None = None
    STORAGE_S3_ENDPOINT: str | None = None  # ex.: https://<conta>.r2.cloudflarestorage.com
    STORAGE_S3_BUCKET: str | None = None
    STORAGE_S3_REGION = "auto"  # R2 = auto; AWS = região do bucket (ex.: sa-east-1)
    STORAGE_S3_ACCESS_KEY_ID: str | None = None
    STORAGE_S3_SECRET_ACCESS_KEY: str | None = None
    STORAGE_S3_ADDRESSING = "path"  # path (R2/MinIO) | virtual (AWS)
    STORAGE_TIMEOUT_SECONDS = 10
    PHOTO_MAX_BYTES = 5 * 1024 * 1024
    # Só a rota de upload de foto aceita corpo maior que MAX_CONTENT_LENGTH (security.py).
    PHOTO_MAX_REQUEST_BYTES = PHOTO_MAX_BYTES + 256 * 1024
    PHOTO_MAX_PIXELS = 40_000_000  # largura × altura lida do cabeçalho, antes de decodificar
    PHOTO_MAX_SIDE = 2560  # a foto guardada é reduzida para no máximo isto (lado maior)
    PHOTO_THUMB_SIDE = 480
    PHOTOS_MAX_PER_ACTIVITY = 20
    PHOTOS_MAX_PER_COMPANY = 5000
    PHOTO_UPLOAD_RATE_LIMIT = "30 per minute; 300 per hour"
    COMMENT_MAX_CHARS = 1000

    @classmethod
    def from_env(cls) -> dict:
        """Lê as variáveis de ambiente na hora de criar o app (não na importação)."""
        values: dict = {
            "SECRET_KEY": os.environ.get("SECRET_KEY") or cls.SECRET_KEY,
            "SQLALCHEMY_DATABASE_URI": _database_url(cls.DEFAULT_DATABASE_URL),
            "RATELIMIT_ENABLED": _bool("RATELIMIT_ENABLED", cls.RATELIMIT_ENABLED),
            # Produção: Redis (REDIS_URL do Render/compose) — memória não é compartilhada entre
            # workers do Gunicorn. finalize_config recusa memory:// fora de dev/test.
            "RATELIMIT_STORAGE_URI": os.environ.get("RATELIMIT_STORAGE_URI")
            or os.environ.get("REDIS_URL")
            or cls.RATELIMIT_STORAGE_URI,
            "RLS_ENABLED": _bool("RLS_ENABLED", cls.RLS_ENABLED),
            "FEATURE_PUBLIC_API": _bool("FEATURE_PUBLIC_API", cls.FEATURE_PUBLIC_API),
            "API_RATE_LIMIT": os.environ.get("API_RATE_LIMIT", cls.API_RATE_LIMIT),
            "API_RATE_LIMIT_IP": os.environ.get("API_RATE_LIMIT_IP", cls.API_RATE_LIMIT_IP),
            "READ_ONLY_ENFORCED": _bool("READ_ONLY_ENFORCED", cls.READ_ONLY_ENFORCED),
            "TRIAL_DAYS": int(os.environ.get("TRIAL_DAYS", cls.TRIAL_DAYS)),
            "DEFAULT_TRIAL_PLAN": os.environ.get("DEFAULT_TRIAL_PLAN", cls.DEFAULT_TRIAL_PLAN),
            "PAST_DUE_GRACE_DAYS": int(os.environ.get("PAST_DUE_GRACE_DAYS", cls.PAST_DUE_GRACE_DAYS)),
        }
        values["BILLING_PROVIDER"] = os.environ.get("BILLING_PROVIDER", cls.BILLING_PROVIDER)
        values["ASAAS_API_KEY"] = os.environ.get("ASAAS_API_KEY") or cls.ASAAS_API_KEY
        values["ASAAS_BASE_URL"] = os.environ.get("ASAAS_BASE_URL") or cls.ASAAS_BASE_URL
        values["ASAAS_WEBHOOK_TOKEN"] = os.environ.get("ASAAS_WEBHOOK_TOKEN") or cls.ASAAS_WEBHOOK_TOKEN
        values["WEBHOOK_RATE_LIMIT"] = os.environ.get("WEBHOOK_RATE_LIMIT", cls.WEBHOOK_RATE_LIMIT)

        for key in (
            "LOGIN_RATE_LIMIT",
            "SIGNUP_RATE_LIMIT",
            "PASSWORD_RESET_RATE_LIMIT",
            "MFA_RATE_LIMIT",
            "INVITE_RATE_LIMIT",
            "EMAIL_RESEND_RATE_LIMIT",
        ):
            values[key] = os.environ.get(key, getattr(cls, key))
        try:
            values["TRUSTED_PROXY_COUNT"] = max(0, int(os.environ.get("TRUSTED_PROXY_COUNT", cls.TRUSTED_PROXY_COUNT)))
        except ValueError:
            raise RuntimeError("TRUSTED_PROXY_COUNT precisa ser um número inteiro.") from None
        for key in ("MAIL_BACKEND", "MAIL_FROM", "RESEND_API_KEY", "APP_BASE_URL", "MFA_ENCRYPTION_KEY", "CONTACT_EMAIL"):
            values[key] = os.environ.get(key) or getattr(cls, key)
        # Fase 7
        fallbacks = os.environ.get("SECRET_KEY_FALLBACKS", "")
        values["SECRET_KEY_FALLBACKS"] = [k.strip() for k in fallbacks.split(",") if k.strip()]
        for key in ("IMPORT_RATE_LIMIT", "WEBHOOK_RATE_LIMIT", "LGPD_EXPORT_RATE_LIMIT", "LGPD_DELETE_RATE_LIMIT", "LOG_LEVEL"):
            values[key] = os.environ.get(key) or getattr(cls, key)
        values["LOG_JSON"] = _bool("LOG_JSON", cls.LOG_JSON)
        # Etapa F — worker
        values["STAFF_NOTIFY_EMAIL"] = os.environ.get("STAFF_NOTIFY_EMAIL") or cls.STAFF_NOTIFY_EMAIL
        for key in ("WORKER_INTERVAL_SECONDS", "WORKER_EVENT_MAX_ATTEMPTS"):
            try:
                values[key] = max(1, int(os.environ.get(key, getattr(cls, key))))
            except ValueError:
                raise RuntimeError(f"{key} precisa ser um número inteiro.") from None
        values["SENTRY_DSN"] = os.environ.get("SENTRY_DSN") or None
        # Etapa G — armazenamento de fotos (segredos só daqui; nunca em código ou log).
        for key in (
            "STORAGE_BACKEND",
            "STORAGE_LOCAL_DIR",
            "STORAGE_S3_ENDPOINT",
            "STORAGE_S3_BUCKET",
            "STORAGE_S3_REGION",
            "STORAGE_S3_ACCESS_KEY_ID",
            "STORAGE_S3_SECRET_ACCESS_KEY",
            "STORAGE_S3_ADDRESSING",
            "PHOTO_UPLOAD_RATE_LIMIT",
        ):
            values[key] = os.environ.get(key) or getattr(cls, key)
        for key in ("PHOTOS_MAX_PER_ACTIVITY", "PHOTOS_MAX_PER_COMPANY", "STORAGE_TIMEOUT_SECONDS"):
            try:
                values[key] = max(1, int(os.environ.get(key, getattr(cls, key))))
            except ValueError:
                raise RuntimeError(f"{key} precisa ser um número inteiro.") from None
        try:
            values["SENTRY_TRACES_SAMPLE_RATE"] = float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", cls.SENTRY_TRACES_SAMPLE_RATE))
        except ValueError:
            raise RuntimeError("SENTRY_TRACES_SAMPLE_RATE precisa ser um número entre 0 e 1.") from None
        return values


class DevelopmentConfig(Config):
    ENV_NAME = "development"
    DEBUG = True
    DEFAULT_DATABASE_URL = "sqlite:///dev.db"
    # http://localhost não aceita cookie Secure nem o prefixo __Host-.
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_NAME = "session"
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_NAME = "remember_token"
    LOG_JSON = False


class TestConfig(Config):
    ENV_NAME = "test"
    TESTING = True
    SECRET_KEY = "chave-so-para-testes"
    SQLALCHEMY_ENGINE_OPTIONS: dict = {}
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_NAME = "session"
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_NAME = "remember_token"
    RATELIMIT_ENABLED = False
    LOG_JSON = False

    @classmethod
    def from_env(cls) -> dict:
        values = super().from_env()
        # Testes nunca usam DATABASE_URL (evita apagar um banco real por engano).
        values["SQLALCHEMY_DATABASE_URI"] = _database_url_raw(os.environ.get("TEST_DATABASE_URL")) or "sqlite://"
        values["RATELIMIT_ENABLED"] = False
        # Testes nunca mandam e-mail de verdade: backend console (caixa em memória).
        values["MAIL_BACKEND"] = "console"
        values["RESEND_API_KEY"] = None
        # Testes nunca mandam erro para o Sentry nem usam o Redis do ambiente.
        values["SENTRY_DSN"] = None
        values["RATELIMIT_STORAGE_URI"] = "memory://"
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
    """Valida o que é obrigatório. Fora de development/test, SECRET_KEY, DATABASE_URL e
    APP_BASE_URL (https) são exigidos. Etapa G: armazenamento de fotos coerente com o ambiente
    (disco local nunca em produção; S3 com todas as variáveis)."""
    from app.services.storage import validate_config as validate_storage

    validate_storage(app_config, env_name)
    if env_name in {"development", "test"}:
        if not app_config.get("SECRET_KEY"):
            # Chave efêmera só em desenvolvimento: as sessões caem a cada reinício.
            app_config["SECRET_KEY"] = secrets.token_hex(32)
        return
    if not app_config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY é obrigatório fora de development/test.")
    if not app_config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("DATABASE_URL é obrigatório fora de development/test.")
    base_url = str(app_config.get("APP_BASE_URL") or "").strip()
    if not base_url.startswith("https://") or len(base_url) <= len("https://"):
        # Links de e-mail, canonical e retorno do pagamento não podem vir do host da
        # requisição (host header é do cliente): sem APP_BASE_URL o app não sobe.
        raise RuntimeError("APP_BASE_URL é obrigatório fora de development/test (ex.: https://app.exemplo.com.br).")
    storage = str(app_config.get("RATELIMIT_STORAGE_URI") or "")
    if app_config.get("RATELIMIT_ENABLED") and not storage.startswith(("redis://", "rediss://", "redis+sentinel://")):
        # Em memória cada worker do Gunicorn tem o próprio contador (o limite vira N vezes
        # maior) e reiniciar zera tudo: produção sem Redis é erro de configuração.
        raise RuntimeError("Rate limit em produção exige Redis: defina REDIS_URL (ou RATELIMIT_STORAGE_URI=redis://...).")
