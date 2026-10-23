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
from app.forms_production import ImportConfirmForm, ImportForm, ImportManyForm, ImportMapForm
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
    if request.endpoint == "dados.import_upload":
        # R7: o corpo é recusado antes da rota (sem empresa carregada); a página de erro diz o
        # limite e o que fazer (o passo 1 também avisa o limite antes do envio).
        return render_template("errors/400.html", message=_too_large_message()), 413
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


def _limit_mb() -> int:
    return int(current_app.config.get("IMPORT_MAX_BYTES", 2 * 1024 * 1024)) // (1024 * 1024)


def _too_large_message() -> str:
    return f"Arquivo grande demais: o limite é {_limit_mb()} MB. Deixe só a aba com os dados e envie de novo."


def _page(form, status=200, **ctx):
    """Passo 1 (enviar) ou, com ``result``, passo 3 (prévia ou erros por linha)."""
    ctx.setdefault("result", None)
    ctx.setdefault("payload", None)
    ctx.setdefault("upload_error", None)
    ctx.setdefault("back", None)
    ctx.setdefault("confirm", None)
    ctx.setdefault("usage", None)
    return render_template("dados/import.html", form=form, limit_mb=_limit_mb(), **ctx), status


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
        return _page(form, 413, upload_error=_too_large_message())
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return _page(form, 400, upload_error="Escolha um arquivo .xlsx ou .csv para enviar.")
    data = upload.stream.read(limit + 1)
    try:
        grid = importer.load_grid(upload.filename, data, limit)
        if not form.map_columns.data:
            found = importer.parse_reference_many(grid)
            if len(found) >= 2:
                return _projects_page(found)
        result = None if form.map_columns.data else importer.auto_parse(grid)
        if result is None:
            return _mapping_page(grid, name=form.name.data)
    except importer.ImportError_ as exc:
        return _page(form, 400, upload_error=str(exc))
    return _preview(form, result, form.name.data)


def _preview(form, result, name, status_error=400, back=None):
    """Prévia (ou erros) de um ``ImportResult``: o mesmo caminho para os dois fluxos.
    ``back`` (fluxo de colunas): dados para o botão “Voltar às colunas” sem reenviar o arquivo."""
    if not result.ok:
        return _page(form, status_error, result=result, back=back)
    payload = _serializer().dumps(
        {"c": str(g.company.id), "u": str(current_user.id), "d": importer.to_payload(result)}
    )
    confirm = ImportConfirmForm(formdata=None, data={"payload": payload, "name": name or result.name})
    usage = entitlements.usage(g.company)
    return _page(form, result=result, confirm=confirm, usage=usage, back=back)


# ---------------------------------------------------------------- R7: mapeamento de colunas


def _mapping_page(grid, *, name=None, sheet=None, header_row=None, chosen=None, token=None, quantity=None,
                  result=None, status=200, map_errors=None):
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
    # Na tela a escolha é por COLUNA (“Isto é…”): coluna ↦ campo.
    column_field = {idx: key for key, idx in selected.items() if isinstance(idx, int) and idx >= 0}
    return render_template(
        "dados/import_map.html", form=form, inspection=inspection, result=result,
        column_field=column_field, column_choices=mapping_svc.COLUMN_CHOICES,
        mode=mapping_svc.mode_of(selected), has_stage=selected.get(mapping_svc.F_STAGE) is not None,
        map_errors=map_errors or [], limit_mb=_limit_mb(),
    ), status


def _columns_from_form(values) -> dict[int, str] | None:
    """``col_<índice>`` = chave do campo (a escolha da tela). ``None`` se o formulário não traz
    nenhuma (formato antigo: um select por campo, ``etapa=<índice>``)."""
    out: dict[int, str] = {}
    for key, value in values.items():
        if not key.startswith(mapping_svc.COLUMN_PREFIX):
            continue
        try:
            idx = int(key[len(mapping_svc.COLUMN_PREFIX):])
        except ValueError:
            continue
        if 0 <= idx < importer.MAX_GRID_COLS:
            out[idx] = (value or "").strip()
    return out or None


@bp.get("/importar/colunas/modo")
@tenant_required(ROLE_SUPERVISOR)
def import_columns_mode():
    """Aviso do modo (simples × detalhado) para a escolha atual das colunas — o servidor decide,
    a tela só troca o trecho (HTMX). Não lê nem grava dados da empresa."""
    mapping, errors = mapping_svc.mapping_from_columns(_columns_from_form(request.args) or {})
    return render_template(
        "dados/_import_mode.html", mode=mapping_svc.mode_of(mapping),
        has_stage=mapping.get(mapping_svc.F_STAGE) is not None, map_errors=errors,
    )


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
        by_column = _columns_from_form(request.form)
        if by_column is None:
            chosen, map_errors = {k: _int_or_none(getattr(form, k).data) for k in mapping_svc.FIELD_KEYS}, []
        else:
            chosen, map_errors = mapping_svc.mapping_from_columns(by_column)
        common = {"name": form.name.data, "sheet": sheet, "token": form.grid.data, "quantity": form.quantity.data}
        if form.action.data == "ver" or not same_sheet:
            return _mapping_page(grid, header_row=header_row, chosen=chosen if same_sheet else None, **common)
        inspection = mapping_svc.inspect(grid, sheet, header_row)
        if map_errors:
            return _mapping_page(grid, header_row=inspection.header_row, chosen=chosen, map_errors=map_errors,
                                 status=400, **common)
        result = mapping_svc.parse_mapped(
            grid, inspection.sheet, inspection.header_row, chosen, quantity=form.quantity.data, name=form.name.data
        )
        if not result.ok and all(e.column in ("colunas", "aba") for e in result.errors):
            # Erro de mapeamento (coluna repetida, sem etapa): fica no passo 2.
            return _mapping_page(grid, header_row=inspection.header_row, chosen=chosen,
                                 map_errors=[e.message for e in result.errors], status=400, **common)
    except importer.ImportError_ as exc:
        return _page(ImportForm(formdata=None), 400, upload_error=str(exc))
    back = {
        "grid": form.grid.data, "sheet": inspection.sheet, "header_row": inspection.header_row,
        "columns": {idx: key for key, idx in chosen.items() if isinstance(idx, int) and idx >= 0},
        "quantity": form.quantity.data, "name": form.name.data,
    }
    return _preview(ImportForm(formdata=None), result, form.name.data, back=back)


# ---------------------------------------------------------------- R7: vários projetos no arquivo

MANY_SALT = "importacao-varios"


def _many_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(signing_keys(), salt=MANY_SALT)


def _sign_many(results) -> str:
    return _many_serializer().dumps(
        {"c": str(g.company.id), "u": str(current_user.id), "d": [importer.to_payload(r) for r in results]}
    )


def _load_many(token: str) -> list | None:
    """Lista de ``ImportResult`` revalidados, ou ``None`` se a assinatura/sessão não confere."""
    try:
        data = _many_serializer().loads(token, max_age=PAYLOAD_MAX_AGE)
    except BadSignature:
        return None
    if data.get("c") != str(g.company.id) or data.get("u") != str(current_user.id):
        return None
    items = data.get("d")
    if not isinstance(items, list) or not 1 <= len(items) <= importer.MAX_GRID_SHEETS:
        return None
    return [importer.from_payload(item if isinstance(item, dict) else {}) for item in items]


def _limit_message(usage, chosen: int) -> str | None:
    """Mensagem clara quando os projetos escolhidos passam do limite do plano (a recusa de
    verdade é o ``check_can_create_project`` na confirmação)."""
    if usage["max_projects"] is None or usage["projects"] + chosen <= usage["max_projects"]:
        return None
    free = max(usage["max_projects"] - usage["projects"], 0)
    return (
        f"Seu plano {usage['plan'].name} permite {usage['max_projects']} projetos ativos e já há "
        f"{usage['projects']}. Dá para importar {free} agora: desmarque {chosen - free} "
        f"ou arquive projetos antes."
    )


def _projects_page(found, *, status=200, error=None, picked=None):
    """Passo 2 do arquivo com vários projetos: lista para escolher (todos marcados)."""
    ok = [result for _, result in found if result.ok]
    rows, i = [], 0
    for project, result in found:
        rows.append((project, result, i if result.ok else None))
        i += 1 if result.ok else 0
    usage = entitlements.usage(g.company)
    picked = set(range(len(ok))) if picked is None else picked
    form = ImportManyForm(formdata=None, data={"payload": _sign_many(ok)}) if ok else None
    return render_template(
        "dados/import_projects.html", step=2, rows=rows, ok_count=len(ok), form=form, usage=usage,
        picked=picked, error=error, limit_message=_limit_message(usage, len(picked)), limit_mb=_limit_mb(),
    ), status


def _picks(total: int) -> list[int]:
    out = []
    for raw in request.form.getlist("pick"):
        try:
            idx = int(raw)
        except ValueError:
            continue
        if 0 <= idx < total and idx not in out:
            out.append(idx)
    return sorted(out)


@bp.post("/importar/projetos")
@limiter.limit(_import_limit)
@tenant_required(ROLE_SUPERVISOR)
def import_projects():
    """Passo 2 → 3: os projetos escolhidos viram a prévia (nova lista assinada, só com eles)."""
    form = ImportManyForm()
    results = _load_many(form.payload.data or "") if form.validate() else None
    if results is None:
        return _page(ImportForm(formdata=None), 400, upload_error="Prévia expirada ou de outra sessão. Envie o arquivo de novo.")
    picks = _picks(len(results))
    if request.form.get("action") == "voltar":
        return _projects_page([(None, r) for r in results], picked=set(picks))
    if not picks:
        found = [(None, r) for r in results]
        return _projects_page(found, status=400, picked=set(), error="Marque ao menos um projeto para importar.")
    chosen = [results[i] for i in picks]
    usage = entitlements.usage(g.company)
    confirm = ImportManyForm(formdata=None, data={"payload": _sign_many(chosen)})
    return render_template(
        "dados/import_projects.html", step=3, chosen=chosen, form=confirm, usage=usage,
        limit_message=_limit_message(usage, len(chosen)), back_payload=form.payload.data, picks=picks,
        limit_mb=_limit_mb(),
    )


@bp.post("/importar/confirmar-varios")
@limiter.limit(_import_limit)
@tenant_required(ROLE_SUPERVISOR)
def import_confirm_many():
    """Cria um projeto por item escolhido, numa transação só. Limite do plano conferido no
    servidor ANTES de gravar (e de novo em cada ``create_project``)."""
    form = ImportManyForm()
    results = _load_many(form.payload.data or "") if form.validate() else None
    if results is None or any(not r.ok for r in results):
        return _page(ImportForm(formdata=None), 400, upload_error="Prévia expirada ou inválida. Envie o arquivo de novo.")
    usage = entitlements.usage(g.company)
    message = _limit_message(usage, len(results))
    if message:
        return render_template(
            "dados/import_projects.html", step=3, chosen=results, form=form, usage=usage,
            limit_message=message, back_payload=None, picks=[], limit_mb=_limit_mb(), blocked=True,
        ), 402
    entitlements.check_can_create_project(g.company, adding=len(results))
    projects = [importer.save(g.company, r, current_user.id) for r in results]
    db.session.commit()
    flash(
        f"{len(projects)} {'projeto importado' if len(projects) == 1 else 'projetos importados'}: "
        + ", ".join(p.name for p in projects) + ".",
        "sucesso",
    )
    return redirect(url_for("app.projects"), 303)


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
