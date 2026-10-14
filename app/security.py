"""Fase 7 — camada HTTP de segurança num lugar só.

- CSP estrita com nonce por requisição (sem ``unsafe-inline``); ``csp_nonce()`` no Jinja
  para o raro ``<script nonce="...">`` (hoje nenhum template precisa: todo JS é arquivo).
- HSTS fora de development/test, Permissions-Policy, X-Content-Type-Options,
  Referrer-Policy, COOP/CORP, X-Frame-Options e ``Cache-Control: no-store`` em página de
  usuário logado.
- Cookies: o Flask já usa ``__Host-session``/``__Host-remember`` (config.py); aqui só a
  conferência de que produção não sobe com cookie inseguro.
- Uploads: o corpo multipart fica em memória (``BytesIO``), nunca em arquivo temporário;
  o teto continua sendo ``MAX_CONTENT_LENGTH`` (413 antes de ler o corpo).
- Rate limit dos webhooks: qualquer blueprint cujo nome tenha "webhook" recebe
  ``WEBHOOK_RATE_LIMIT`` por IP (a Fase 8 só registra o blueprint).
- Chaves de assinatura com rotação (``SECRET_KEY_FALLBACKS``).
"""

from __future__ import annotations

import io
import secrets

from flask import Flask, Request, current_app, g, request

NONCE_BYTES = 18

PERMISSIONS_POLICY = (
    "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), "
    "microphone=(), payment=(), usb=(), browsing-topics=()"
)
HSTS = "max-age=63072000; includeSubDomains"


class InMemoryUploadRequest(Request):
    """Arquivos de formulário em memória: nada de upload em disco (nem temporário).

    O tamanho é limitado por ``MAX_CONTENT_LENGTH`` antes de o corpo ser lido, então a
    memória por requisição tem teto (≈ 2,25 MB)."""

    def _get_file_stream(self, total_content_length, content_type, filename=None, content_length=None):  # noqa: D401
        return io.BytesIO()


def csp_nonce() -> str:
    """Nonce da requisição atual (o mesmo valor vai no cabeçalho CSP)."""
    nonce = g.get("csp_nonce")
    if nonce is None:
        nonce = secrets.token_urlsafe(NONCE_BYTES)
        g.csp_nonce = nonce
    return nonce


def content_security_policy(nonce: str) -> str:
    return "; ".join(
        (
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}'",
            "style-src 'self'",
            "img-src 'self' data:",
            "font-src 'self'",
            "connect-src 'self'",
            "object-src 'none'",
            "base-uri 'none'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        )
    )


def is_production_like(app: Flask | None = None) -> bool:
    app = app or current_app
    return app.config.get("ENV_NAME") not in {"development", "test"}


def signing_keys(app: Flask | None = None) -> list[str]:
    """Chaves para ``itsdangerous`` (a ÚLTIMA assina; as anteriores só validam)."""
    app = app or current_app
    return [*(app.config.get("SECRET_KEY_FALLBACKS") or []), app.config["SECRET_KEY"]]


def _check_cookie_config(app: Flask) -> None:
    if not is_production_like(app):
        return
    problems = []
    for prefix in ("SESSION", "REMEMBER"):
        if not app.config.get(f"{prefix}_COOKIE_SECURE"):
            problems.append(f"{prefix}_COOKIE_SECURE")
        if not app.config.get(f"{prefix}_COOKIE_HTTPONLY"):
            problems.append(f"{prefix}_COOKIE_HTTPONLY")
        if not str(app.config.get(f"{prefix}_COOKIE_NAME", "")).startswith("__Host-"):
            problems.append(f"{prefix}_COOKIE_NAME sem __Host-")
    if app.config.get("SESSION_COOKIE_DOMAIN"):
        problems.append("SESSION_COOKIE_DOMAIN (incompatível com __Host-)")
    if problems:
        raise RuntimeError("Cookies inseguros em produção: " + ", ".join(problems))


def _apply_headers(response):
    headers = response.headers
    headers.setdefault("Content-Security-Policy", content_security_policy(csp_nonce()))
    headers.setdefault("X-Content-Type-Options", "nosniff")
    headers.setdefault("X-Frame-Options", "DENY")
    headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    headers.setdefault("Permissions-Policy", PERMISSIONS_POLICY)
    headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    if is_production_like():
        headers.setdefault("Strict-Transport-Security", HSTS)
    if request.endpoint != "static" and "Cache-Control" not in headers:
        from flask_login import current_user

        if current_user and current_user.is_authenticated:
            # Página com dado de empresa não fica em cache de navegador/proxy compartilhado.
            headers["Cache-Control"] = "no-store"
    return response


_WEBHOOK_BLUEPRINTS_LIMITED: set[str] = set()


def _limit_webhook_blueprints(app: Flask) -> None:
    """Limite por IP em todo blueprint de webhook (o ``limiter`` é global ao processo, então
    cada blueprint entra uma vez só; o valor é lido do app da requisição)."""
    from app.extensions import limiter

    for name, blueprint in app.blueprints.items():
        if "webhook" in name and name not in _WEBHOOK_BLUEPRINTS_LIMITED:
            limiter.limit(lambda: current_app.config.get("WEBHOOK_RATE_LIMIT", "120 per minute"))(blueprint)
            _WEBHOOK_BLUEPRINTS_LIMITED.add(name)


def init_app(app: Flask) -> None:
    """Chamar depois de registrar os blueprints."""
    _check_cookie_config(app)
    app.request_class = InMemoryUploadRequest
    app.after_request(_apply_headers)
    app.jinja_env.globals["csp_nonce"] = csp_nonce
    _limit_webhook_blueprints(app)
