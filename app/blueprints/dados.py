"""Importar e exportar (Fase 4) — supervisor+.

Exportar: CSV e XLSX do projeto (mesmas colunas da tela, células perigosas neutralizadas).
Importar: upload limitado e lido em memória → pré-visualização com erros por linha →
confirmação grava tudo numa transação. Entre a pré-visualização e a confirmação os dados
vão no formulário ASSINADOS (itsdangerous, com empresa e usuário dentro, validade de 1 h) e
são revalidados na confirmação.

R7 (planilha): ``/importar`` reconhece sozinho o CSV/XLSX do site e a planilha de referência;
qualquer outra planilha (ou “quero escolher as colunas”) vai para a etapa de COLUNAS
(``/importar/colunas``): a grade lida vai assinada no formulário (empresa + usuário + 1 h,
nada em disco), a pessoa escolhe aba, linha de cabeçalho e o mapeamento, e cai na mesma
prévia assinada → confirmar. Exportar no layout da base: ``/exportar-planilha.xlsx``
(abas Acompanhamento e Equipe, com fórmulas).
"""

from __future__ import annotations

from flask import Blueprint, Response, current_app, flash, g, redirect, render_template, request, url_for
from flask_login import current_user
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.extensions import db, limiter
from app.security import signing_keys
from app.forms_production import ImportConfirmForm, ImportForm, ImportMapForm
from app.models import ROLE_SUPERVISOR, Project
from app.services import entitlements, export_layout, exporter, importer
from app.services import import_mapping as mapping_svc
from app.tenancy import get_or_404, tenant_required

bp = Blueprint("dados", __name__, url_prefix="/app")

PAYLOAD_SALT = "importacao-previa"
PAYLOAD_MAX_AGE = 60 * 60
GRID_SALT = "importacao-colunas"
# A grade assinada vai num campo de formulário: o Werkzeug limita cada campo de texto a
# MAX_FORM_MEMORY_SIZE (500 kB por padrão). Acima disso, a pessoa deixa só a aba dos dados.
GRID_TOKEN_MAX = 400_000


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(signing_keys(), salt=PAYLOAD_SALT)


def _grid_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(signing_keys(), salt=GRID_SALT)


@bp.app_errorhandler(413)
def too_large(err):
    from flask import request

    key = "PHOTO_MAX_BYTES" if request.endpoint == "qualidade.photo_upload" else "IMPORT_MAX_BYTES"
    limit = int(current_app.config.get(key, 2 * 1024 * 1024))
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


@bp.get("/projetos/<uuid:project_id>/exportar-planilha.xlsx")
@tenant_required(ROLE_SUPERVISOR)
def export_layout_xlsx(project_id):
    """R7: .xlsx no layout da planilha de acompanhamento, com fórmulas."""
    project = get_or_404(Project, project_id, include_archived=True)
    return _download(
        export_layout.to_xlsx_layout(project),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        exporter.filename(project, "xlsx").replace(".xlsx", "-planilha.xlsx"),
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


def _import_limit():
    return current_app.config.get("IMPORT_RATE_LIMIT", "10 per minute; 60 per hour")


@bp.route("/importar", methods=["GET", "POST"])
@limiter.limit(_import_limit, methods=["POST"])  # Fase 7: upload é caro (parse em memória)
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
        grid = importer.load_grid(upload.filename, data, limit)
        result = None if form.map_columns.data else importer.auto_parse(grid)
        if result is None:
            return _mapping_page(grid, name=form.name.data)
    except importer.ImportError_ as exc:
        return _page(form, 400, upload_error=str(exc))
    return _preview(form, result, form.name.data)


def _preview(form, result, name, status_error=400):
    """Prévia (ou erros) de um ``ImportResult``: o mesmo caminho para os dois fluxos."""
    if not result.ok:
        return _page(form, status_error, result=result)
    payload = _serializer().dumps(
        {"c": str(g.company.id), "u": str(current_user.id), "d": importer.to_payload(result)}
    )
    confirm = ImportConfirmForm(formdata=None, data={"payload": payload, "name": name or result.name})
    usage = entitlements.usage(g.company)
    return _page(form, result=result, confirm=confirm, usage=usage)


# ---------------------------------------------------------------- R7: mapeamento de colunas


def _mapping_page(grid, *, name=None, sheet=None, header_row=None, chosen=None, token=None, quantity=None,
                  result=None, status=200):
    inspection = mapping_svc.inspect(grid, sheet, header_row)
    if token is None:
        token = _grid_serializer().dumps(
            {"c": str(g.company.id), "u": str(current_user.id), "g": mapping_svc.grid_to_data(grid)}
        )
        if len(token) > GRID_TOKEN_MAX:
            raise importer.ImportError_(
                "Planilha grande demais para escolher as colunas. Deixe só a aba com os dados e envie de novo."
            )
    selected = inspection.suggestion if chosen is None else chosen
    form = ImportMapForm(
        formdata=None,
        data={
            "grid": token, "current_sheet": inspection.sheet, "sheet": inspection.sheet,
            "header_row": inspection.header_row, "quantity": quantity, "name": name,
            **{k: ("" if selected.get(k) is None else str(selected[k])) for k in mapping_svc.FIELD_KEYS},
        },
    )
    form.sheet.choices = [(t, t) for t in inspection.sheets]
    choices = [("", "— não usar —")] + [(str(c.index), c.label) for c in inspection.columns]
    for key in mapping_svc.FIELD_KEYS:
        getattr(form, key).choices = choices
    return render_template(
        "dados/import_map.html", form=form, inspection=inspection, fields=mapping_svc.FIELDS, result=result,
    ), status


def _int_or_none(value):
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return -1  # índice inválido: validate_mapping recusa


@bp.post("/importar/colunas")
@limiter.limit(_import_limit)
@tenant_required(ROLE_SUPERVISOR)
def import_columns():
    form = ImportMapForm()
    if not form.validate():
        return _page(ImportForm(formdata=None), 400, upload_error="Dados inválidos. Envie o arquivo de novo.")
    try:
        data = _grid_serializer().loads(form.grid.data, max_age=PAYLOAD_MAX_AGE)
    except BadSignature:
        return _page(ImportForm(formdata=None), 400, upload_error="Planilha expirada ou inválida. Envie o arquivo de novo.")
    if data.get("c") != str(g.company.id) or data.get("u") != str(current_user.id):
        return _page(ImportForm(formdata=None), 400, upload_error="Planilha de outra sessão. Envie o arquivo de novo.")
    try:
        grid = mapping_svc.grid_from_data(data.get("g") or {})
        sheet = form.sheet.data or None
        same_sheet = sheet == (form.current_sheet.data or None)
        header_row = form.header_row.data if same_sheet else None
        chosen = {k: _int_or_none(getattr(form, k).data) for k in mapping_svc.FIELD_KEYS}
        common = {"name": form.name.data, "sheet": sheet, "token": form.grid.data, "quantity": form.quantity.data}
        if form.action.data == "ver" or not same_sheet:
            return _mapping_page(grid, header_row=header_row, chosen=chosen if same_sheet else None, **common)
        inspection = mapping_svc.inspect(grid, sheet, header_row)
        result = mapping_svc.parse_mapped(
            grid, inspection.sheet, inspection.header_row, chosen, quantity=form.quantity.data, name=form.name.data
        )
        if not result.ok:
            return _mapping_page(grid, header_row=inspection.header_row, chosen=chosen, result=result, status=400, **common)
    except importer.ImportError_ as exc:
        return _page(ImportForm(formdata=None), 400, upload_error=str(exc))
    return _preview(ImportForm(formdata=None), result, form.name.data)


@bp.post("/importar/confirmar")
@limiter.limit(_import_limit)
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
