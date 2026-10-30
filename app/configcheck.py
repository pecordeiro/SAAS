"""Etapa H — conferência da configuração de produção (``flask config-check``).

Lista TUDO o que falta ou está inseguro, de uma vez, em vez de falhar no primeiro erro como o
``finalize_config`` (que continua sendo a trava de boot). Usado no ``preDeployCommand`` do
``render.yaml``: se houver erro, o deploy não sobe.

Regras:
- Nunca imprime valor de variável, só o NOME e o fato (“ausente”, “curta”, “sandbox”).
- Funciona sem criar o app (``python scripts/config_check.py``): recebe um ``dict`` de config.
- Níveis: ``erro`` (bloqueia), ``aviso`` (não bloqueia, a menos que ``--strict``), ``info``.
- Fora de produção/staging (development/test) tudo vira aviso: o comando serve para ensaiar.
- ``--online`` acrescenta o que exige rede: banco, papel do banco, RLS, migrations, Redis.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ERRO = "erro"
AVISO = "aviso"
INFO = "info"

PRODUCTION_LIKE = ("production", "staging")
_PLACEHOLDER_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0", "example", "seu-dominio", "seudominio", "exemplo")
_WEAK_SECRET_MARKERS = (
    "changeme",
    "change-me",
    "troque",
    "trocar",
    "secret",
    "senha",
    "password",
    "chave-so-para-testes",
    "your-",
    "placeholder",
    "dev-key",
    "insecure",
)
MIN_SECRET_LENGTH = 32


@dataclass(frozen=True)
class Finding:
    code: str  # estável: serve para --ignorar
    level: str
    message: str

    def line(self) -> str:
        return f"[{self.level.upper():5}] {self.code}: {self.message}"


def _s(cfg: dict, key: str) -> str:
    return str(cfg.get(key) or "").strip()


def _looks_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _PLACEHOLDER_HOSTS)


def weak_secret(value: str) -> str | None:
    """Motivo pelo qual ``value`` não serve como segredo, ou ``None``."""
    if len(value) < MIN_SECRET_LENGTH:
        return f"tem menos de {MIN_SECRET_LENGTH} caracteres"
    if len(set(value)) < 12:
        return "tem poucos caracteres distintos (repetitiva)"
    lowered = value.lower()
    if any(marker in lowered for marker in _WEAK_SECRET_MARKERS):
        return "parece um valor de exemplo"
    return None


def collect(cfg: dict, env_name: str, environ: dict | None = None) -> list[Finding]:
    """Verificações offline sobre o dict de configuração já lido do ambiente."""
    environ = os.environ if environ is None else environ
    found: list[Finding] = []

    def add(code: str, level: str, message: str) -> None:
        found.append(Finding(code, level, message))

    production = env_name == "production"

    # --- ambiente
    if env_name not in PRODUCTION_LIKE:
        add("ENV", INFO, f"APP_ENV={env_name}: verificações de produção rodam como aviso (ensaio).")
    elif not (environ.get("APP_ENV") or environ.get("FLASK_ENV")):
        add("APP_ENV", AVISO, "APP_ENV não está definido (o padrão é production); defina explicitamente.")

    # --- segredos
    secret = _s(cfg, "SECRET_KEY")
    if not secret:
        add("SECRET_KEY", ERRO, "SECRET_KEY ausente.")
    else:
        reason = weak_secret(secret)
        if reason:
            add("SECRET_KEY", ERRO, f"SECRET_KEY fraca: {reason}. Gere com: python -c \"import secrets; print(secrets.token_hex(32))\".")
    mfa = _s(cfg, "MFA_ENCRYPTION_KEY")
    if not mfa:
        add(
            "MFA_ENCRYPTION_KEY",
            ERRO,
            "MFA_ENCRYPTION_KEY ausente (sem ela o segredo TOTP é cifrado com a SECRET_KEY e trocar uma invalida os MFA).",
        )
    else:
        parts = [p.strip() for p in mfa.split(",") if p.strip()]
        if any(weak_secret(p) for p in parts):
            add("MFA_ENCRYPTION_KEY", ERRO, "MFA_ENCRYPTION_KEY fraca (mínimo 32 caracteres, aleatória) .")
        if secret and secret in parts:
            add("MFA_ENCRYPTION_KEY", AVISO, "MFA_ENCRYPTION_KEY igual à SECRET_KEY: use chaves independentes.")

    # --- banco
    db_uri = _s(cfg, "SQLALCHEMY_DATABASE_URI")
    if not db_uri:
        add("DATABASE_URL", ERRO, "DATABASE_URL ausente.")
    elif db_uri.startswith("sqlite"):
        add("DATABASE_URL", ERRO, "DATABASE_URL aponta para SQLite: produção usa PostgreSQL 16.")
    elif not db_uri.startswith("postgresql"):
        add("DATABASE_URL", ERRO, "DATABASE_URL não é PostgreSQL.")
    else:
        host = re.sub(r"^.*@", "", db_uri.split("://", 1)[-1]).split("/", 1)[0].split(":", 1)[0]
        if host in {"localhost", "127.0.0.1", "::1", ""}:
            add("DATABASE_URL", ERRO, "DATABASE_URL aponta para a própria máquina (localhost).")

    # --- URL pública
    base = _s(cfg, "APP_BASE_URL")
    if not base:
        add("APP_BASE_URL", ERRO, "APP_BASE_URL ausente (links de e-mail, canonical e retorno do pagamento).")
    elif not base.startswith("https://") or len(base) <= len("https://"):
        add("APP_BASE_URL", ERRO, "APP_BASE_URL precisa começar com https://.")
    elif _looks_placeholder(base):
        add("APP_BASE_URL", ERRO, "APP_BASE_URL parece um endereço de exemplo/local.")
    elif base.endswith("/"):
        add("APP_BASE_URL", AVISO, "APP_BASE_URL termina com '/': remova a barra final.")
    contact = _s(cfg, "CONTACT_EMAIL")
    if not contact or _looks_placeholder(contact):
        add(
            "CONTACT_EMAIL",
            ERRO if production else AVISO,
            "CONTACT_EMAIL é o de exemplo: aparece em /contato; defina o e-mail real de atendimento.",
        )

    # --- proxy / cookies
    if int(cfg.get("TRUSTED_PROXY_COUNT") or 0) < 1:
        add(
            "TRUSTED_PROXY_COUNT",
            ERRO,
            "TRUSTED_PROXY_COUNT=0 atrás do proxy do Render: todo cliente teria o IP do proxy (rate limit e bloqueio de login valeriam para todos juntos). Use 1.",
        )
    for prefix in ("SESSION", "REMEMBER"):
        if not cfg.get(f"{prefix}_COOKIE_SECURE"):
            add("COOKIES", ERRO, f"{prefix}_COOKIE_SECURE desligado.")

    # --- Redis / rate limit
    if not cfg.get("RATELIMIT_ENABLED"):
        add("RATELIMIT", ERRO, "RATELIMIT_ENABLED desligado: login e cadastro ficam sem limite.")
    storage = _s(cfg, "RATELIMIT_STORAGE_URI")
    if not storage.startswith(("redis://", "rediss://", "redis+sentinel://")):
        add("REDIS_URL", ERRO, "Redis ausente: defina REDIS_URL (o rate limit em memória é por processo e zera a cada reinício).")

    # --- RLS
    if not cfg.get("RLS_ENABLED"):
        add(
            "RLS_ENABLED",
            ERRO if production else AVISO,
            "RLS_ENABLED desligado: o app não informa a empresa ao banco (segunda barreira de isolamento, ADR-0003).",
        )

    # --- e-mail
    backend = _s(cfg, "MAIL_BACKEND").lower() or ("resend" if _s(cfg, "RESEND_API_KEY") else "console")
    if backend == "console":
        add("MAIL_BACKEND", ERRO, "E-mail em modo console: nada é entregue (convites, reset de senha, alertas). Defina RESEND_API_KEY.")
    elif backend == "resend":
        if not _s(cfg, "RESEND_API_KEY"):
            add("RESEND_API_KEY", ERRO, "MAIL_BACKEND=resend sem RESEND_API_KEY.")
    else:
        add("MAIL_BACKEND", ERRO, "MAIL_BACKEND desconhecido (use resend).")
    mail_from = _s(cfg, "MAIL_FROM")
    if not mail_from or _looks_placeholder(mail_from):
        add("MAIL_FROM", ERRO, "MAIL_FROM é o padrão/exemplo: use um remetente do seu domínio verificado (SPF/DKIM/DMARC).")

    # --- fotos
    storage_backend = _s(cfg, "STORAGE_BACKEND").lower() or "none"
    if storage_backend == "local":
        add("STORAGE_BACKEND", ERRO, "STORAGE_BACKEND=local: disco do container é efêmero; use s3 (R2).")
    elif storage_backend == "none":
        add("STORAGE_BACKEND", AVISO, "Fotos de evidência desligadas (STORAGE_BACKEND vazio/none).")
    elif storage_backend == "s3":
        missing = [
            k
            for k in ("STORAGE_S3_ENDPOINT", "STORAGE_S3_BUCKET", "STORAGE_S3_ACCESS_KEY_ID", "STORAGE_S3_SECRET_ACCESS_KEY")
            if not _s(cfg, k)
        ]
        if missing:
            add("STORAGE_S3", ERRO, "STORAGE_BACKEND=s3 sem " + ", ".join(missing) + ".")
        elif not _s(cfg, "STORAGE_S3_ENDPOINT").startswith("https://"):
            add("STORAGE_S3", ERRO, "STORAGE_S3_ENDPOINT precisa ser https://.")

    # --- cobrança (Asaas)
    provider = _s(cfg, "BILLING_PROVIDER").lower() or ("asaas" if _s(cfg, "ASAAS_API_KEY") else "fake")
    asaas_url = _s(cfg, "ASAAS_BASE_URL")
    asaas_key = _s(cfg, "ASAAS_API_KEY")
    if provider == "fake":
        add("BILLING_PROVIDER", ERRO if production else AVISO, "Cobrança em modo fake/ausente (sem ASAAS_API_KEY): ninguém consegue assinar.")
    else:
        if not asaas_key:
            add("ASAAS_API_KEY", ERRO, "ASAAS_API_KEY ausente.")
        if not _s(cfg, "ASAAS_WEBHOOK_TOKEN"):
            add("ASAAS_WEBHOOK_TOKEN", ERRO, "ASAAS_WEBHOOK_TOKEN ausente: o webhook do Asaas seria recusado.")
        elif len(_s(cfg, "ASAAS_WEBHOOK_TOKEN")) < 24:
            add("ASAAS_WEBHOOK_TOKEN", AVISO, "ASAAS_WEBHOOK_TOKEN curto (use token_urlsafe(32)).")
        sandbox_url = "sandbox" in asaas_url
        sandbox_key = "_hmlg_" in asaas_key
        if production:
            if sandbox_url:
                add("ASAAS_BASE_URL", ERRO, "ASAAS_BASE_URL é o SANDBOX em production: use https://api.asaas.com/v3.")
            if sandbox_key:
                add("ASAAS_API_KEY", ERRO, "ASAAS_API_KEY é de sandbox ($aact_hmlg_…) em production.")
            if not asaas_url.startswith("https://"):
                add("ASAAS_BASE_URL", ERRO, "ASAAS_BASE_URL precisa ser https://.")
        else:
            if asaas_url and not sandbox_url:
                add("ASAAS_BASE_URL", AVISO, f"{env_name}: ASAAS_BASE_URL não é o sandbox; staging não deve cobrar de verdade.")
    if not cfg.get("READ_ONLY_ENFORCED"):
        add("READ_ONLY_ENFORCED", ERRO, "READ_ONLY_ENFORCED desligado: empresa sem assinatura ativa continuaria escrevendo.")

    # --- observabilidade e operação
    if not _s(cfg, "SENTRY_DSN"):
        add("SENTRY_DSN", AVISO, "SENTRY_DSN ausente: erros 500 não chegam ao Sentry (só ao log).")
    if not _s(cfg, "STAFF_NOTIFY_EMAIL"):
        add("STAFF_NOTIFY_EMAIL", AVISO, "STAFF_NOTIFY_EMAIL ausente: a equipe não é avisada de requisições de identidade visual.")
    if not cfg.get("LOG_JSON"):
        add("LOG_JSON", AVISO, "LOG_JSON desligado: logs em texto não são agregáveis.")
    if str(cfg.get("LOG_LEVEL") or "").upper() == "DEBUG":
        add("LOG_LEVEL", AVISO, "LOG_LEVEL=DEBUG em produção: ruído e risco de dado em log.")
    if cfg.get("SECRET_KEY_FALLBACKS"):
        add("SECRET_KEY_FALLBACKS", AVISO, "SECRET_KEY_FALLBACKS preenchida: rotação em andamento; remova quando acabar.")
    if cfg.get("FEATURE_PUBLIC_API"):
        add("FEATURE_PUBLIC_API", INFO, "API pública LIGADA (confirme que é intencional).")

    # --- assets construídos (CSP estrita: sem CDN)
    manifest = Path(__file__).resolve().parent / "static" / "dist" / "manifest.json"
    if not manifest.exists():
        add("ASSETS", ERRO, "app/static/dist/manifest.json ausente: rode python scripts/build_assets.py (o Dockerfile já faz).")
    return found


def collect_online(cfg: dict, env_name: str) -> list[Finding]:
    """Verificações que falam com o banco e o Redis (``--online``)."""
    found: list[Finding] = []

    def add(code: str, level: str, message: str) -> None:
        found.append(Finding(code, level, message))

    uri = _s(cfg, "SQLALCHEMY_DATABASE_URI")
    if uri.startswith("postgresql"):
        found.extend(_online_database(cfg, uri, env_name))
    elif uri:
        add("DB_ONLINE", AVISO, "Banco não é PostgreSQL: verificações de papel/RLS puladas.")
    storage = _s(cfg, "RATELIMIT_STORAGE_URI")
    if storage.startswith(("redis://", "rediss://", "redis+sentinel://")):
        try:
            import redis

            redis.Redis.from_url(storage, socket_connect_timeout=3, socket_timeout=3).ping()
            add("REDIS_ONLINE", INFO, "Redis respondeu ao PING.")
        except Exception as exc:  # noqa: BLE001 - só o tipo, a URL leva senha
            add("REDIS_ONLINE", ERRO, f"Redis não respondeu ({exc.__class__.__name__}).")
    return found


def _online_database(cfg: dict, uri: str, env_name: str) -> list[Finding]:
    from sqlalchemy import create_engine, text

    from app import rls

    found: list[Finding] = []

    def add(code: str, level: str, message: str) -> None:
        found.append(Finding(code, level, message))

    engine = create_engine(uri, connect_args={"connect_timeout": 5})
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            add("DB_ONLINE", INFO, "Banco respondeu.")
            superuser, bypass = conn.execute(
                text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
            ).one()
            if superuser or bypass:
                add(
                    "DB_ROLE",
                    ERRO if cfg.get("RLS_ENABLED") else AVISO,
                    "O papel do app é superusuário ou tem BYPASSRLS: o RLS não vale para ele. "
                    "Use um papel comum (ver docs/plano/lancamento.md, item de RLS).",
                )
            else:
                add("DB_ROLE", INFO, "Papel do app é comum (sem superusuário/BYPASSRLS).")
            has_alembic = conn.execute(text("SELECT to_regclass('alembic_version') IS NOT NULL")).scalar()
            if not has_alembic:
                add("MIGRATIONS", INFO, "Banco ainda sem schema (primeiro deploy): flask db upgrade vai criá-lo.")
            else:
                current = conn.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
                head = _migration_heads()
                if head and set(current) != set(head):
                    add("MIGRATIONS", INFO, "Migrations pendentes: serão aplicadas por flask db upgrade.")
                else:
                    add("MIGRATIONS", INFO, "Schema na última migration.")
                if cfg.get("RLS_ENABLED"):
                    info = rls.status(conn)
                    not_forced = [t for t in rls.RLS_TABLES if t in info and not (info[t]["enabled"] and info[t]["forced"])]
                    if not_forced:
                        add(
                            "RLS_FORCED",
                            AVISO,
                            f"RLS_ENABLED=1, mas {len(not_forced)} tabela(s) sem ENABLE+FORCE: rode flask rls enable "
                            "(go-live exige; use --strict).",
                        )
                    else:
                        add("RLS_FORCED", INFO, "RLS ligado e forçado nas tabelas de cliente.")
                last_holiday = conn.execute(text("SELECT max(day) FROM holidays WHERE company_id IS NULL")).scalar()
                if last_holiday is None:
                    add("HOLIDAYS", AVISO, "Sem feriados nacionais: rode flask seed-holidays (prazo em dias úteis depende deles).")
                elif last_holiday.year < date.today().year + 1:
                    add(
                        "HOLIDAYS",
                        AVISO,
                        f"Feriados nacionais só até {last_holiday.year}: com RLS forçado o seed exige "
                        "flask rls disable → seed-holidays → flask rls enable (docs/plano/operacao.md).",
                    )
    except Exception as exc:  # noqa: BLE001 - a URL do banco leva senha: só o tipo
        add("DB_ONLINE", ERRO, f"Banco não respondeu ou consulta falhou ({exc.__class__.__name__}).")
    finally:
        engine.dispose()
    return found


def _migration_heads() -> list[str]:
    try:
        from alembic.config import Config as AlembicConfig
        from alembic.script import ScriptDirectory

        cfg = AlembicConfig()
        cfg.set_main_option("script_location", str(Path(__file__).resolve().parent.parent / "migrations"))
        return list(ScriptDirectory.from_config(cfg).get_heads())
    except Exception:  # noqa: BLE001
        return []


def build_config(name: str | None = None) -> tuple[dict, str]:
    """Config do ambiente SEM criar o app (nem validar): para ``scripts/config_check.py``."""
    from flask import Flask

    from app.config import get_config

    config = get_config(name)
    holder = Flask("configcheck")
    holder.config.from_object(config)
    holder.config.update(config.from_env())
    return dict(holder.config), config.ENV_NAME


def evaluate(
    cfg: dict,
    env_name: str,
    *,
    online: bool = False,
    strict: bool = False,
    ignore: tuple[str, ...] = (),
) -> tuple[list[Finding], bool]:
    """Devolve (achados, aprovado). Fora de produção/staging, erro vira aviso."""
    findings = collect(cfg, env_name)
    if online:
        findings += collect_online(cfg, env_name)
    ignored = {code.upper() for code in ignore}
    result: list[Finding] = []
    for f in findings:
        if f.code.upper() in ignored:
            result.append(Finding(f.code, INFO, f"{f.message} (ignorado por --ignorar)"))
            continue
        if f.level == ERRO and env_name not in PRODUCTION_LIKE:
            f = Finding(f.code, AVISO, f.message)
        result.append(f)
    order = {ERRO: 0, AVISO: 1, INFO: 2}
    result.sort(key=lambda f: order[f.level])
    failing = {ERRO, AVISO} if strict and env_name in PRODUCTION_LIKE else {ERRO}
    return result, not any(f.level in failing for f in result)
