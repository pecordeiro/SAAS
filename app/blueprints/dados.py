"""Importar e exportar (Fase 4) — supervisor+.

Exportar: CSV e XLSX do projeto (mesmas colunas da tela, células perigosas neutralizadas).
Importar: upload limitado e lido em memória → pré-visualização com erros por linha →
confirmação grava tudo numa transação. Entre a pré-visualização e a confirmação os dados
vão no formulário ASSINADOS (itsdangerous, com empresa e usuário dentro, validade de 1 h) e
são revalidados na confirmação.
"""

from __future__ import annotations

from flask import Blueprint, Response, current_app, flash, g, redirect, render_template, request, url_for
from flask_login import current_user
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.extensions import db
from app.forms_production import ImportConfirmForm, ImportForm
from app.models import ROLE_SUPERVISOR, Project
from app.services import entitlements, exporter, importer
from app.tenancy import get_or_404, tenant_required

bp = Blueprint("dados", __name__, url_prefix="/app")

PAYLOAD_SALT = "importacao-previa"
PAYLOAD_MAX_AGE = 60 * 60


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.secret_key, salt=PAYLOAD_SALT)


@bp.app_errorhandler(413)
def too_large(err):
    limit = int(current_app.config.get("IMPORT_MAX_BYTES", 2 * 1024 * 1024))
    return render_template("errors/400.html", message=f"Arquivo grande demais (máximo {limit // (1024 * 1024)} MB)."), 413


def _download(content: bytes, mimetype: str, filename: str) -> Response:
    response = Response(content, mimetype=mimetype)
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/projetos/<uuid:project_id>/exportar.csv")
@tenant_required(ROLE_SUPERVISOR)
def export_csv(project_id):
    project = get_or_404(Project, project_id, include_archived=True)
    return _download(exporter.to_csv(project), "text/csv; charset=utf-8", exporter.filename(project, "csv"))


@bp.get("/projetos/<uuid:project_id>/exportar.xlsx")
@tenant_required(ROLE_SUPERVISOR)
def export_xlsx(project_id):
    project = get_or_404(Project, project_id, include_archived=True)
    return _download(
        exporter.to_xlsx(project),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        exporter.filename(project, "xlsx"),
    )


@bp.get("/importar/modelo.csv")
@tenant_required(ROLE_SUPERVISOR)
def import_template():
    return _download(exporter.template_csv(), "text/csv; charset=utf-8", "modelo-importacao.csv")


def _page(form, status=200, **ctx):
    ctx.setdefault("result", None)
    ctx.setdefault("payload", None)
    ctx.setdefault("upload_error", None)
    return render_template("dados/import.html", form=form, **ctx), status


@bp.route("/importar", methods=["GET", "POST"])
@tenant_required(ROLE_SUPERVISOR)
def import_upload():
    form = ImportForm()
    if not form.is_submitted():
        return _page(form)
    if not form.validate():
        return _page(form, 400)
    limit = int(current_app.config.get("IMPORT_MAX_BYTES", 2 * 1024 * 1024))
    if request.content_length and request.content_length > limit + 64 * 1024:
        return _page(form, 413, upload_error=f"Arquivo maior que {limit // (1024 * 1024)} MB.")
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return _page(form, 400, upload_error="Escolha um arquivo .csv ou .xlsx.")
    data = upload.stream.read(limit + 1)
    try:
        result = importer.parse_upload(upload.filename, data, limit)
    except importer.ImportError_ as exc:
        return _page(form, 400, upload_error=str(exc))
    if not result.ok:
        return _page(form, 400, result=result)
    payload = _serializer().dumps(
        {"c": str(g.company.id), "u": str(current_user.id), "d": importer.to_payload(result)}
    )
    confirm = ImportConfirmForm(formdata=None, data={"payload": payload, "name": form.name.data or result.name})
    usage = entitlements.usage(g.company)
    return _page(form, result=result, confirm=confirm, usage=usage)


@bp.post("/importar/confirmar")
@tenant_required(ROLE_SUPERVISOR)
def import_confirm():
    form = ImportConfirmForm()
    if not form.validate():
        return _page(ImportForm(formdata=None), 400, upload_error="Pré-visualização inválida. Envie o arquivo de novo.")
    try:
        data = _serializer().loads(form.payload.data, max_age=PAYLOAD_MAX_AGE)
    except BadSignature:
        return _page(ImportForm(formdata=None), 400, upload_error="Pré-visualização expirada ou inválida. Envie o arquivo de novo.")
    if data.get("c") != str(g.company.id) or data.get("u") != str(current_user.id):
        return _page(ImportForm(formdata=None), 400, upload_error="Pré-visualização de outra sessão. Envie o arquivo de novo.")
    result = importer.from_payload(data.get("d") or {})
    if not result.ok:
        return _page(ImportForm(formdata=None), 400, result=result)
    project = importer.save(g.company, result, current_user.id, name=form.name.data or None)
    db.session.commit()
    flash(f"Projeto importado: {len(result.stages)} etapas, {result.activity_count} atividades.", "sucesso")
    return redirect(url_for("app.project_detail", project_id=project.id), 303)
