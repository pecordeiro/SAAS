"""Fase 7 — logs estruturados (JSON) com ``request_id`` e Sentry opcional com filtro.

Regras (docs/plano/seguranca.md, docs/plano/lgpd.md):
- Uma linha JSON por evento em stdout (o host guarda; retenção de 6 meses).
- ``request_id``: o ``X-Request-ID`` do proxy só é aceito se tiver formato seguro
  (``[A-Za-z0-9._-]{8,64}``); senão é gerado. Volta na resposta para o suporte achar o log.
- A linha de acesso registra a ROTA (molde, ex. ``/convite/<token>``), nunca o caminho real
  nem a query string: tokens de convite/reset/confirmação viajam no caminho.
- Nada de e-mail, IP completo, cookie, cabeçalho ``Authorization``, senha ou token. O
  usuário aparece só pelo id (pseudônimo) e a empresa pelo id.
- Sentry só com ``SENTRY_DSN``: ``send_default_pii=False``, sem corpo de requisição, sem
  variáveis locais e ``before_send`` que remove cookies, Authorization, senhas e tokens.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
import uuid
from datetime import datetime, timezone

from flask import Flask, g, has_request_context, request

REQUEST_ID_HEADER = "X-Request-ID"
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")

# Chaves cujo valor nunca sai do processo (logs extras e eventos do Sentry).
SENSITIVE_KEY = re.compile(
    r"pass|senha|secret|token|auth|cookie|session|csrf|api[-_]?key|asaas|signature|cpf|cnpj|totp|code|dsn",
    re.IGNORECASE,
)
# Sequências com cara de token (url-safe longo, hex de hash, Bearer cp_...). UUID canônico
# (ids de usuário/empresa, pseudônimos) não é token e passa.
_UUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
_TOKENISH = re.compile(
    r"cp_[A-Za-z0-9_-]{8,}"
    r"|(?<![A-Za-z0-9_-])(?!" + _UUID + r"(?![A-Za-z0-9_-]))[A-Za-z0-9_-]{32,}"
)
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
FILTERED = "[filtrado]"

_STANDARD_ATTRS = set(vars(logging.LogRecord("x", 0, "", 0, "", None, None))) | {"message", "asctime"}


def scrub_text(value: str) -> str:
    """Remove e-mails e sequências com cara de token de um texto livre."""
    return _TOKENISH.sub(FILTERED, _EMAIL.sub("[e-mail]", value))


def scrub(value, depth: int = 0):
    """Cópia de ``value`` sem valores de chaves sensíveis (recursivo, com limite)."""
    if depth > 8:
        return FILTERED
    if isinstance(value, dict):
        return {
            k: (FILTERED if isinstance(k, str) and SENSITIVE_KEY.search(k) else scrub(v, depth + 1))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [scrub(v, depth + 1) for v in value]
    if isinstance(value, str):
        return scrub_text(value)
    return value


def current_request_id() -> str | None:
    if not has_request_context():
        return None
    return g.get("request_id")


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = current_request_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": scrub_text(record.getMessage()),
        }
        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id
        for key, value in record.__dict__.items():
            if key in _STANDARD_ATTRS or key in payload or key == "request_id" or key.startswith("_"):
                continue
            payload[key] = FILTERED if SENSITIVE_KEY.search(key) else scrub(value)
        if record.exc_info:
            # Tipo e traceback; a mensagem da exceção passa pelo mesmo filtro.
            payload["exc"] = scrub_text(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False, default=str)


def _configure_root(app: Flask) -> None:
    root = logging.getLogger()
    if getattr(root, "_controle_configured", False):
        for handler in root.handlers:
            if getattr(handler, "_controle", False):
                handler.setFormatter(_formatter(app))
        return
    handler = logging.StreamHandler(sys.stdout)
    handler._controle = True  # type: ignore[attr-defined]
    handler.setFormatter(_formatter(app))
    handler.addFilter(RequestContextFilter())
    root.addHandler(handler)
    root.setLevel(str(app.config.get("LOG_LEVEL") or "INFO").upper())
    root._controle_configured = True  # type: ignore[attr-defined]
    # O log de acesso do Werkzeug escreve o caminho real (com tokens): fica só em WARNING.
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def _formatter(app: Flask) -> logging.Formatter:
    if app.config.get("LOG_JSON"):
        return JsonFormatter()
    return logging.Formatter("%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s")


access_log = logging.getLogger("app.access")


def _begin_request() -> None:
    incoming = request.headers.get(REQUEST_ID_HEADER, "")
    g.request_id = incoming if _SAFE_REQUEST_ID.match(incoming) else uuid.uuid4().hex
    g.request_started = time.perf_counter()


def _end_request(response):
    request_id = g.get("request_id")
    if request_id:
        response.headers[REQUEST_ID_HEADER] = request_id
    if request.endpoint == "static":
        return response
    started = g.get("request_started")
    company = g.get("company")
    try:
        from flask_login import current_user

        user_id = str(current_user.id) if current_user and current_user.is_authenticated else None
    except Exception:  # noqa: BLE001 - log nunca derruba a resposta
        user_id = None
    access_log.info(
        "request",
        extra={
            "method": request.method,
            "route": request.url_rule.rule if request.url_rule is not None else "<sem rota>",
            "status": response.status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 1) if started else None,
            "user_id": user_id,
            "company_id": str(company.id) if company is not None else None,
        },
    )
    return response


# ---------------------------------------------------------------- Sentry

_DROP_HEADERS = {"cookie", "authorization", "x-csrftoken", "x-csrf-token", "asaas-access-token", "proxy-authorization"}


def sentry_before_send(event: dict, hint: dict | None = None) -> dict:
    """Remove cookies, Authorization, senhas, tokens, e-mails e IP antes de sair do processo."""
    req = event.get("request")
    if isinstance(req, dict):
        req.pop("cookies", None)
        req.pop("data", None)
        req.pop("query_string", None)
        req.pop("env", None)
        headers = req.get("headers")
        if isinstance(headers, dict):
            req["headers"] = {
                k: (FILTERED if k.lower() in _DROP_HEADERS or SENSITIVE_KEY.search(k) else v)
                for k, v in headers.items()
            }
        if isinstance(req.get("url"), str):
            req["url"] = scrub_text(req["url"].split("?", 1)[0])
    user = event.get("user")
    if isinstance(user, dict):
        event["user"] = {"id": user["id"]} if "id" in user else {}
    for key in ("extra", "contexts", "tags"):
        if isinstance(event.get(key), dict):
            event[key] = scrub(event[key])
    crumbs = event.get("breadcrumbs")
    if isinstance(crumbs, dict) and isinstance(crumbs.get("values"), list):
        for crumb in crumbs["values"]:
            if isinstance(crumb, dict):
                if isinstance(crumb.get("message"), str):
                    crumb["message"] = scrub_text(crumb["message"])
                if isinstance(crumb.get("data"), dict):
                    crumb["data"] = scrub(crumb["data"])
    if isinstance(event.get("logentry"), dict):
        entry = event["logentry"]
        if isinstance(entry.get("message"), str):
            entry["message"] = scrub_text(entry["message"])
        entry.pop("params", None)
    for exc in (event.get("exception") or {}).get("values", []) or []:
        if isinstance(exc, dict) and isinstance(exc.get("value"), str):
            exc["value"] = scrub_text(exc["value"])
        for frame in ((exc or {}).get("stacktrace") or {}).get("frames", []) or []:
            if isinstance(frame, dict):
                frame.pop("vars", None)
    return event


def _init_sentry(app: Flask) -> None:
    dsn = app.config.get("SENTRY_DSN")
    if not dsn:
        return
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init(
        dsn=dsn,
        environment=app.config.get("ENV_NAME"),
        integrations=[FlaskIntegration()],
        send_default_pii=False,
        include_local_variables=False,
        max_request_body_size="never",
        traces_sample_rate=float(app.config.get("SENTRY_TRACES_SAMPLE_RATE") or 0.0),
        before_send=sentry_before_send,
        before_send_transaction=sentry_before_send,
    )


def init_app(app: Flask) -> None:
    _configure_root(app)
    # fileConfig do Alembic (migrations no mesmo processo, ex. testes) desliga loggers já
    # criados; o log de acesso não pode sumir em silêncio.
    access_log.disabled = False
    app.before_request(_begin_request)
    app.after_request(_end_request)
    _init_sentry(app)
