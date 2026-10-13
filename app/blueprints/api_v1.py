"""API pública v1 (Fase 9) e tela de tokens. Registrada SÓ com ``FEATURE_PUBLIC_API`` ligada.

API (``/api/v1``, contrato em docs/api/openapi.yaml):
- Autenticação exclusiva por ``Authorization: Bearer cp_...``. Cookie de sessão NÃO autentica
  (a empresa vem do token, nunca da sessão) e o blueprint é isento de CSRF (sem cookie, não há
  o que forjar).
- Ordem das recusas: 401 (sem token / inválido / revogado / expirado) → 403 (plano sem a
  feature ``api``) → 403 (token sem o escopo da rota) → 404 (recurso de outra empresa).
- Erros em ``application/problem+json`` (RFC 9457); datas ISO 8601 em UTC.
- Rate limit por token (e um teto por IP); toda chamada de token conhecido vai para
  ``audit_logs`` (sem o token) e atualiza ``last_used_at``.
- Rotas ainda não implementadas respondem 501 (stubs do contrato).

Tela (``/app/integracoes/api``): só o proprietário cria/revoga tokens; o token puro aparece
uma única vez, na resposta da criação.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import logging
import uuid
from datetime import date, datetime, timezone
from functools import wraps

from flask import Blueprint, current_app, flash, g, jsonify, make_response, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import and_, or_, select
from werkzeug.exceptions import HTTPException
from wtforms import SelectField, SelectMultipleField, StringField
from wtforms.validators import DataRequired, Length

from app import rls
from app.extensions import csrf, db, limiter
from app.forms import BaseForm
from app.models import ROLE_OWNER, ApiClient, ApiToken, Company, Project
from app.services import api_tokens as tokens
from app.services import calc, entitlements
from app.services import projects as svc
from app.tenancy import get_or_404, scoped, tenant_required

log = logging.getLogger(__name__)

PROBLEM_TYPE = "urn:controle-producao:problem:"
PROBLEM_MIME = "application/problem+json"
DEFAULT_PAGE = 25
MAX_PAGE = 100

bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")
ui_bp = Blueprint("api_tokens_ui", __name__, url_prefix="/app/integracoes")

csrf.exempt(bp)


# ---------------------------------------------------------------- erros (RFC 9457)


def problem(status: int, title: str, code: str, detail: str | None = None, headers: dict | None = None):
    body = {"type": PROBLEM_TYPE + code.replace("_", "-"), "title": title, "status": status, "code": code}
    if detail:
        body["detail"] = detail
    body["instance"] = request.path
    response = make_response(jsonify(body), status)
    response.headers["Content-Type"] = PROBLEM_MIME
    for key, value in (headers or {}).items():
        response.headers[key] = value
    return response


_HTTP_TITLES = {
    400: ("Requisição inválida", "bad_request"),
    404: ("Recurso não encontrado", "not_found"),
    405: ("Método não permitido", "method_not_allowed"),
    413: ("Corpo grande demais", "payload_too_large"),
    429: ("Muitas requisições", "rate_limited"),
}


def _http_error(exc: HTTPException):
    status = exc.code or 500
    title, code = _HTTP_TITLES.get(status, ("Erro", "error"))
    return problem(status, title, code)


# Por código (e não só pela classe): o Flask procura o handler do código antes do da classe, e o
# app já tem handlers HTML por código (404, 429...) que ganhariam do handler genérico do blueprint.
for _status in _HTTP_TITLES:
    bp.register_error_handler(_status, _http_error)
bp.register_error_handler(HTTPException, _http_error)


@bp.errorhandler(entitlements.EntitlementError)
def _entitlement_error(exc: entitlements.EntitlementError):
    db.session.rollback()
    return problem(exc.status_code, exc.title, "plan_limit", exc.message)


@bp.errorhandler(Exception)
def _unexpected(exc: Exception):
    if isinstance(exc, HTTPException):  # pragma: no cover - tratado acima
        return _http_error(exc)
    db.session.rollback()
    log.exception("Erro inesperado na API")  # sem cabeçalhos nem corpo: nunca o token
    return problem(500, "Erro interno", "internal_error")


def _unauthorized(code: str, detail: str):
    challenge = 'Bearer realm="api"' if code == "missing_token" else f'Bearer realm="api", error="invalid_token"'
    return problem(401, "Não autenticado", code, detail, headers={"WWW-Authenticate": challenge})


# ---------------------------------------------------------------- rate limit


def _presented_token() -> str | None:
    header = request.headers.get("Authorization", "")
    scheme, _, value = header.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()


def token_key() -> str:
    """Chave do limite: SHA-256 do token apresentado (nunca o texto puro); sem token, o IP."""
    raw = _presented_token()
    if raw is None:
        return "ip:" + (request.remote_addr or "?")
    return "tok:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ip_key() -> str:
    return "ip:" + (request.remote_addr or "?")


limiter.limit(lambda: current_app.config.get("API_RATE_LIMIT", "120 per minute"), key_func=token_key)(bp)
limiter.limit(lambda: current_app.config.get("API_RATE_LIMIT_IP", "600 per minute"), key_func=ip_key)(bp)


# ---------------------------------------------------------------- autenticação


@bp.before_request
def authenticate():
    g.api_token = None
    # A sessão de navegador não vale aqui: empresa e usuário só existem se o token existir.
    g.company = None
    g.membership = None
    rls.set_context(company_id=None, user_id=None)

    raw = _presented_token()
    if raw is None:
        return _unauthorized("missing_token", "Envie o cabeçalho Authorization: Bearer <token>.")
    token = tokens.find_by_raw(raw)
    if token is None:
        return _unauthorized(tokens.INVALID, "Token inválido.")
    g.api_token = token
    g.api_scopes = frozenset(token.scopes or [])
    company = db.session.get(Company, token.company_id)
    g.company = company
    rls.set_context(company_id=token.company_id)
    try:
        tokens.check_usable(token)
    except tokens.TokenError as exc:
        detail = "Token revogado." if exc.code == tokens.REVOKED else "Token expirado."
        return _unauthorized(exc.code, detail)
    if not entitlements.has_feature(company, "api"):
        return problem(
            403,
            "Recurso indisponível no plano",
            "plan_feature_unavailable",
            f"A API não está disponível no plano {entitlements.effective_plan(company).name}.",
        )
    return None


@bp.after_request
def record_call(response):
    """Auditoria + ``last_used_at`` de toda chamada com token conhecido (nunca grava o token)."""
    token = getattr(g, "api_token", None)
    if token is None:
        return _no_store(response)
    try:
        from app.services import audit

        audit.record(
            tokens.API_REQUEST,
            company_id=token.company_id,
            actor_user_id=None,
            object_type="api_token",
            object_id=token.id,
            details={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "prefix": token.token_prefix,
            },
        )
        if response.status_code != 401:
            token.last_used_at = datetime.now(timezone.utc)
        db.session.commit()
    except Exception:  # pragma: no cover - a resposta ao cliente não deve cair por falha de auditoria
        db.session.rollback()
        log.exception("Falha ao auditar chamada da API")
    return _no_store(response)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    return response


def require_scope(scope: str):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if scope not in g.api_scopes:
                return problem(
                    403,
                    "Escopo insuficiente",
                    "insufficient_scope",
                    f"O token não tem o escopo {scope}.",
                    headers={"WWW-Authenticate": f'Bearer realm="api", error="insufficient_scope", scope="{scope}"'},
                )
            return view(*args, **kwargs)

        return wrapper

    return decorator


# ---------------------------------------------------------------- serialização


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def iso_date(value: date | None) -> str | None:
    return value.isoformat() if value else None


_STATUS = {
    calc.STATUS_CONCLUIDA: "done",
    calc.STATUS_EM_ANDAMENTO: "in_progress",
    calc.STATUS_NAO_INICIADA: "not_started",
}


def project_json(project: Project) -> dict:
    return {
        "id": str(project.id),
        "name": project.name,
        "status": project.status,
        "quantity": project.quantity,
        "people": project.people,
        "hours_per_day": float(project.hours_per_day),
        "start_date": iso_date(project.start_date),
        "due_date": iso_date(project.due_date),
        "created_at": iso(project.created_at),
    }


def summary_json(project: Project) -> dict:
    result = svc.summary(project)
    stages = []
    for stage, stage_result in zip(svc.active_stages(project), result.etapas):
        activities = svc.active_activities(stage)
        stages.append(
            {
                "id": str(stage.id),
                "name": stage.name,
                "status": _STATUS[stage_result.status],
                "progress": stage_result.progresso,
                "units_completed": stage_result.unidades,
                "units_planned": stage_result.previstas,
                "tasks": stage_result.tarefas,
                "tasks_completed": stage_result.tarefas_concluidas,
                "total_minutes": stage_result.tempo_total_min,
                "remaining_minutes": stage_result.tempo_restante_min,
                "activities": [
                    {
                        "id": str(a.id),
                        "name": a.name,
                        "units_completed": a.units_done,
                        "units_remaining": r.faltam,
                        "progress": r.pct,
                        "version": a.version,
                    }
                    for a, r in zip(activities, stage_result.atividades)
                ],
            }
        )
    status = calc.status_etapa(result.unidades_concluidas, project.quantity, result.progresso_geral)
    forecast = svc.forecast_end(project, result, g.company, date.today())
    return {
        "project_id": str(project.id),
        "status": _STATUS[status],
        "units_completed": result.unidades_concluidas,
        "units_planned": result.previstas,
        "progress": result.progresso_geral,
        "stages_completed": result.etapas_concluidas,
        "stages_total": len(result.etapas),
        "tasks": result.tarefas,
        "tasks_completed": result.tarefas_concluidas,
        "unit_minutes": result.tempo_unidade_min,
        "total_minutes": result.tempo_total_min,
        "remaining_minutes": result.tempo_restante_min,
        "remaining_workdays": result.dias_uteis_restantes,
        "forecast_end": iso_date(forecast),
        "due_date": iso_date(project.due_date),
        "stages": stages,
    }


# ---------------------------------------------------------------- cursor


def encode_cursor(project: Project) -> str:
    created = project.created_at if project.created_at.tzinfo else project.created_at.replace(tzinfo=timezone.utc)
    raw = f"{created.astimezone(timezone.utc).isoformat()}|{project.id}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def decode_cursor(value: str) -> tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)).decode()
        stamp, _, ident = raw.partition("|")
        created = datetime.fromisoformat(stamp)
        if created.tzinfo is None:
            raise ValueError
        return created, uuid.UUID(ident)
    except (ValueError, UnicodeDecodeError, binascii.Error):
        raise ValueError("cursor inválido") from None


# ---------------------------------------------------------------- rotas


@bp.get("/projects")
@require_scope(tokens.SCOPE_READ_PROJECTS)
def list_projects():
    try:
        limit = int(request.args.get("limit", DEFAULT_PAGE))
    except ValueError:
        return problem(400, "Parâmetro inválido", "invalid_parameter", "limit deve ser um inteiro.")
    if not 1 <= limit <= MAX_PAGE:
        return problem(400, "Parâmetro inválido", "invalid_parameter", f"limit deve estar entre 1 e {MAX_PAGE}.")
    query = scoped(Project).where(Project.archived_at.is_(None))
    cursor = request.args.get("cursor")
    if cursor:
        try:
            created, ident = decode_cursor(cursor)
        except ValueError:
            return problem(400, "Parâmetro inválido", "invalid_parameter", "cursor inválido.")
        query = query.where(
            or_(Project.created_at < created, and_(Project.created_at == created, Project.id < ident))
        )
    rows = list(
        db.session.execute(query.order_by(Project.created_at.desc(), Project.id.desc()).limit(limit + 1)).scalars()
    )
    page = rows[:limit]
    return jsonify(
        {"data": [project_json(p) for p in page], "next_cursor": encode_cursor(page[-1]) if len(rows) > limit else None}
    )


@bp.get("/projects/<uuid:project_id>/summary")
@require_scope(tokens.SCOPE_READ_PROJECTS)
def project_summary(project_id):
    project = get_or_404(Project, project_id)
    return jsonify(summary_json(project))


def _not_implemented():
    return problem(501, "Não implementado", "not_implemented", "Rota reservada no contrato; ainda não disponível.")


@bp.get("/projects/<uuid:project_id>")
@require_scope(tokens.SCOPE_READ_PROJECTS)
def project_detail(project_id):
    return _not_implemented()


@bp.get("/projects/<uuid:project_id>/events")
@require_scope(tokens.SCOPE_READ_PROJECTS)
def project_events(project_id):
    return _not_implemented()


@bp.post("/activities/<uuid:activity_id>/progress")
@require_scope(tokens.SCOPE_WRITE_PROGRESS)
def activity_progress(activity_id):
    return _not_implemented()


@bp.route("/<path:rest>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def unknown(rest):
    return problem(404, "Recurso não encontrado", "not_found")


# ---------------------------------------------------------------- tela de tokens (/app/integracoes/api)


class TokenForm(BaseForm):
    name = StringField("Nome da integração", filters=[lambda v: v.strip() if isinstance(v, str) else v], validators=[DataRequired(), Length(max=120)])
    scopes = SelectMultipleField("Permissões", choices=[(k, v) for k, v in tokens.SCOPES.items()])
    expires = SelectField("Validade", choices=list(tokens.EXPIRY_CHOICES), default="90")


class RevokeForm(BaseForm):
    pass


def _page(form: TokenForm, *, new_token: str | None = None, status: int = 200, error: str | None = None):
    company = g.company
    items = [(t, tokens.status_of(t)) for t in tokens.list_tokens(company.id)]
    response = make_response(
        render_template(
            "app/api_tokens.html",
            form=form,
            revoke_form=RevokeForm(formdata=None),
            items=items,
            new_token=new_token,
            has_api=entitlements.has_feature(company, "api"),
            plan=entitlements.effective_plan(company),
            scopes=tokens.SCOPES,
            error=error,
        ),
        status,
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@ui_bp.get("/api")
@tenant_required(ROLE_OWNER)
def tokens_index():
    return _page(TokenForm(formdata=None))


@ui_bp.post("/api")
@tenant_required(ROLE_OWNER)
def tokens_create():
    entitlements.require_feature(g.company, "api", "A API")
    form = TokenForm()
    if not form.validate() or not form.scopes.data:
        return _page(form, status=400, error="Informe o nome e escolha ao menos uma permissão.")
    taken = db.session.execute(
        select(ApiClient.id).where(ApiClient.company_id == g.company.id, ApiClient.name == form.name.data)
    ).first()
    if taken:
        return _page(form, status=400, error="Já existe uma integração com esse nome.")
    created = tokens.create_token(
        g.company,
        name=form.name.data,
        scopes=form.scopes.data,
        expires_in_days=int(form.expires.data) or None,
        user_id=current_user.id,
    )
    db.session.commit()
    return _page(TokenForm(formdata=None), new_token=created.raw, status=201)


@ui_bp.post("/api/<uuid:token_id>/revogar")
@tenant_required(ROLE_OWNER)
def tokens_revoke(token_id):
    token = get_or_404(ApiToken, token_id)
    if not RevokeForm().validate():
        return _page(TokenForm(formdata=None), status=400, error="Formulário expirado. Tente de novo.")
    if tokens.revoke(token, current_user.id):
        db.session.commit()
        flash("Token revogado.", "sucesso")
    return redirect(url_for("api_tokens_ui.tokens_index"), 303)
