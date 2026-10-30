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
- Sessão que caiu no meio de um pedido do HTMX: o 302 para o login vira 401 + ``HX-Redirect``
  (sem isso o XHR segue o redirecionamento, recebe a página de login com 200 e a tela marca
  “salvo” sem ter salvo).
"""

from __future__ import annotations

import io
import secrets
from urllib.parse import urlsplit

from flask import Flask, Request, current_app, g, request, url_for

NONCE_BYTES = 18

PERMISSIONS_POLICY = (
    "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), "
    "microphone=(), payment=(), usb=(), browsing-topics=()"
)
HSTS = "max-age=63072000; includeSubDomains"


# Etapa G: rotas de upload com teto próprio (chave de config), maior que MAX_CONTENT_LENGTH.
# Só elas; qualquer outra rota continua com o teto global (≈ 2,25 MB).
UPLOAD_LIMIT_BY_ENDPOINT = {
    "qualidade.photo_upload": "PHOTO_MAX_REQUEST_BYTES",
    "identidade.file_upload": "PHOTO_MAX_REQUEST_BYTES",  # ADR-0019: logo/foto do briefing
}


class InMemoryUploadRequest(Request):
    """Arquivos de formulário em memória: nada de upload em disco (nem temporário).

    O tamanho é limitado por ``MAX_CONTENT_LENGTH`` antes de o corpo ser lido, então a
    memória por requisição tem teto (≈ 2,25 MB; upload de foto ≈ 5,25 MB — Etapa G)."""

    @property
    def max_content_length(self) -> int | None:  # type: ignore[override]
        if self._max_content_length is not None:
            return self._max_content_length
        rule = self.url_rule
        key = UPLOAD_LIMIT_BY_ENDPOINT.get(rule.endpoint) if rule is not None else None
        if key and current_app:
            return int(current_app.config[key])
        return super().max_content_length

    @max_content_length.setter
    def max_content_length(self, value: int | None) -> None:
        self._max_content_length = value

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


REDIRECT_CODES = (301, 302, 303, 307, 308)


def _htmx_login_redirect(response):
    """Pedido do HTMX com a sessão já encerrada (senha trocada em outro aparelho, conta desativada,
    tempo esgotado): o Flask-Login responde 302 para o login, o XHR segue sozinho e recebe a página
    de login com 200, e a tela trataria como sucesso. Aqui o 302 vira 401 com ``HX-Redirect``: o
    htmx leva o navegador ao login, que depois volta para a página em que a pessoa estava."""
    if request.headers.get("HX-Request") != "true" or response.status_code not in REDIRECT_CODES:
        return response
    login_path = url_for("auth.login")
    if urlsplit(response.headers.get("Location", "")).path != login_path:
        return response
    from app.blueprints.auth import safe_next

    current = urlsplit(request.headers.get("HX-Current-URL", ""))
    same_host = not current.netloc or current.netloc == request.host
    back = safe_next(current.path + (f"?{current.query}" if current.query else "")) if same_host and current.path else None
    response.status_code = 401
    response.headers["HX-Redirect"] = url_for("auth.login", next=back) if back else login_path
    del response.headers["Location"]
    response.set_data(b"")
    return response


def init_app(app: Flask) -> None:
    """Chamar depois de registrar os blueprints."""
    _check_cookie_config(app)
    app.request_class = InMemoryUploadRequest
    app.after_request(_apply_headers)
    app.after_request(_htmx_login_redirect)
    app.jinja_env.globals["csp_nonce"] = csp_nonce
    _limit_webhook_blueprints(app)
