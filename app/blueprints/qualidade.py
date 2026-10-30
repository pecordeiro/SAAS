"""Etapa G — qualidade: evidências por atividade (comentários e fotos).

R6 (ADR-0017): três módulos OPCIONAIS moram aqui — ``fotos`` (evidências), ``checklist``
(checklist e inspeções) e ``unidades`` (número de série). Com o módulo desligado na empresa, a rota
responde 404 (``tenancy.tenant_required`` → ``modules.guard_endpoint``; mapa em services/modules.py).

Regras (CLAUDE.md): empresa SÓ da sessão (``tenant_required`` + ``get_or_404``; recurso de outra
empresa → 404), papéis na rota (esconder botão não substitui a recusa), POST com CSRF, foto
nunca em pasta pública — só por ``/app/fotos/<uuid>`` com Content-Type fixo, ``nosniff``,
``Cache-Control: private`` e CSP ``sandbox`` própria.
"""

from __future__ import annotations

from flask import Blueprint, Response, abort, current_app, flash, g, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db, limiter
from app.models import ROLE_OPERATOR, ROLE_SUPERVISOR, Activity, Project, Stage, Unit
from app.models.quality import (
    CHECKLIST_ITEM_MAX,
    CHECKLIST_NOTE_MAX,
    PHOTO_CAPTION_MAX,
    ActivityComment,
    ActivityPhoto,
    StageChecklistItem,
    StageInspection,
)
from app.services import audit, modules
from app.services import checklists as checklists_svc
from app.services import comments as comments_svc
from app.services import projects as projects_svc
from app.services import units as units_svc
from app.services import photos as photos_svc
from app.services import storage as storage_mod
from app.tenancy import get_or_404, tenant_required

bp = Blueprint("qualidade", __name__, url_prefix="/app")

PHOTO_CSP = "default-src 'none'; sandbox"


def _evidence_url(activity: Activity, anchor: str | None = None) -> str:
    return url_for("qualidade.evidence", activity_id=activity.id, _anchor=anchor)


def _evidence_page(activity: Activity, *, status: int = 200, comment_error: str | None = None,
                   photo_error: str | None = None, draft: str = ""):
    stage = activity.stage
    return (
        render_template(
            "qualidade/evidencias.html",
            activity=activity,
            stage=stage,
            project=stage.project,
            comments=comments_svc.list_for(activity),
            photos=photos_svc.list_for(activity),
            photos_enabled=photos_svc.enabled(),
            can_delete=g.membership.has_role(ROLE_SUPERVISOR),
            comment_max=comments_svc.max_chars(),
            caption_max=PHOTO_CAPTION_MAX,
            photo_max_mb=int(current_app.config.get("PHOTO_MAX_BYTES", 5 * 1024 * 1024)) // (1024 * 1024),
            photos_max=int(current_app.config.get("PHOTOS_MAX_PER_ACTIVITY", 20)),
            comment_error=comment_error,
            photo_error=photo_error,
            draft=draft,
        ),
        status,
    )


@bp.get("/atividades/<uuid:activity_id>/evidencias")
@tenant_required(ROLE_OPERATOR)
def evidence(activity_id):
    """Comentários e fotos da atividade (todos os membros veem; operador+ envia)."""
    return _evidence_page(get_or_404(Activity, activity_id))


@bp.post("/atividades/<uuid:activity_id>/comentarios")
@tenant_required(ROLE_OPERATOR)
def comment_create(activity_id):
    activity = get_or_404(Activity, activity_id)
    body = request.form.get("body", "")
    try:
        comments_svc.add_comment(activity, body, current_user.id)
    except comments_svc.CommentError as exc:
        db.session.rollback()
        return _evidence_page(activity, status=400, comment_error=str(exc), draft=body[: comments_svc.max_chars()])
    db.session.commit()
    flash("Comentário publicado.", "sucesso")
    return redirect(_evidence_url(activity, "comentarios"), 303)


@bp.post("/comentarios/<uuid:comment_id>/apagar")
@tenant_required(ROLE_SUPERVISOR)
def comment_delete(comment_id):
    comment = get_or_404(ActivityComment, comment_id)
    activity = comment.activity
    comments_svc.delete_comment(comment, current_user.id)
    db.session.commit()
    flash("Comentário apagado (registrado na auditoria).", "sucesso")
    return redirect(_evidence_url(activity, "comentarios"), 303)


def _photo_limit():
    return current_app.config.get("PHOTO_UPLOAD_RATE_LIMIT", "30 per minute; 300 per hour")


@bp.post("/atividades/<uuid:activity_id>/fotos")
@limiter.limit(_photo_limit)
@tenant_required(ROLE_OPERATOR)
def photo_upload(activity_id):
    """Upload de foto (operador+). Corpo até ``PHOTO_MAX_REQUEST_BYTES`` (security.py); a foto é
    validada pelo conteúdo e reencodada em ``photos.process``. O nome enviado é ignorado."""
    activity = get_or_404(Activity, activity_id)
    upload = request.files.get("photo")
    if upload is None or not upload.filename:
        return _evidence_page(activity, status=400, photo_error="Escolha uma foto.")
    limit = int(current_app.config.get("PHOTO_MAX_BYTES", 5 * 1024 * 1024))
    data = upload.stream.read(limit + 1)
    try:
        photo = photos_svc.add_photo(activity, data, current_user.id, request.form.get("caption"))
    except photos_svc.PhotoError as exc:
        db.session.rollback()
        return _evidence_page(activity, status=400, photo_error=str(exc))
    except storage_mod.StorageError:
        db.session.rollback()
        return _evidence_page(activity, status=503, photo_error="Não foi possível guardar a foto agora. Tente de novo.")
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        photos_svc.discard_objects(photo)
        raise
    flash("Foto enviada.", "sucesso")
    return redirect(_evidence_url(activity, "fotos"), 303)


@bp.get("/fotos/<uuid:photo_id>")
@tenant_required(ROLE_OPERATOR)
def photo_view(photo_id):
    """Serve a foto (ou ``?tamanho=mini``) só para membro da empresa dona; outra empresa → 404."""
    photo = get_or_404(ActivityPhoto, photo_id)
    mini = request.args.get("tamanho") == "mini"
    try:
        data = photos_svc.read(photo, mini=mini)
    except storage_mod.ObjectNotFound:
        abort(404)
    except storage_mod.StorageError:
        abort(503)
    response = Response(data, mimetype="image/jpeg")
    headers = response.headers
    headers["Content-Type"] = "image/jpeg"  # fixo: nunca o tipo enviado pelo usuário
    headers["X-Content-Type-Options"] = "nosniff"
    headers["Cache-Control"] = "private, max-age=300"
    headers["Vary"] = "Cookie"
    headers["Content-Disposition"] = f'inline; filename="foto-{photo.id}{"-mini" if mini else ""}.jpg"'
    headers["Content-Security-Policy"] = PHOTO_CSP
    headers["Cross-Origin-Resource-Policy"] = "same-origin"
    return response


@bp.post("/fotos/<uuid:photo_id>/apagar")
@tenant_required(ROLE_SUPERVISOR)
def photo_delete(photo_id):
    photo = get_or_404(ActivityPhoto, photo_id)
    activity = photo.activity
    try:
        photos_svc.delete_photo(photo, current_user.id)
    except storage_mod.StorageError:
        db.session.rollback()
        return _evidence_page(activity, status=503, photo_error="Não foi possível apagar a foto agora. Tente de novo.")
    db.session.commit()
    flash("Foto apagada (registrado na auditoria).", "sucesso")
    return redirect(_evidence_url(activity, "fotos"), 303)


# ================================================================ checklist de inspeção (bloco 2)
# supervisor+: itens e “exige checklist”; operador+: abrir, preencher e assinar; supervisor+:
# correção depois de assinada (nova linha + motivo). Assinatura = usuário da sessão + hora do
# servidor. “Exige” só sinaliza (ADR-0011).


def _units_for_select(stage: Stage) -> list:
    """Unidades do projeto para escolher na inspeção (opcional). R6: só com o módulo
    “número de série” ligado."""
    if not modules.is_enabled(g.company, modules.UNIDADES):
        return []
    return units_svc.list_units(stage.project)


def _checklist_page(stage: Stage, *, status: int = 200, error: str | None = None):
    return (
        render_template(
            "qualidade/checklist.html",
            stage=stage,
            project=stage.project,
            items=checklists_svc.active_items(stage),
            inspections=checklists_svc.inspections_for(stage),
            signal=checklists_svc.signals(stage.company_id, [stage])[stage.id],
            can_manage=g.membership.has_role(ROLE_SUPERVISOR),
            item_max=CHECKLIST_ITEM_MAX,
            error=error,
            units=_units_for_select(stage),
        ),
        status,
    )


@bp.get("/etapas/<uuid:stage_id>/checklist")
@tenant_required(ROLE_OPERATOR)
def checklist(stage_id):
    return _checklist_page(get_or_404(Stage, stage_id))


@bp.post("/etapas/<uuid:stage_id>/checklist/itens")
@tenant_required(ROLE_SUPERVISOR)
def checklist_item_add(stage_id):
    stage = get_or_404(Stage, stage_id)
    try:
        checklists_svc.add_item(stage, request.form.get("text"), current_user.id)
    except checklists_svc.ChecklistError as exc:
        db.session.rollback()
        return _checklist_page(stage, status=400, error=str(exc))
    db.session.commit()
    flash("Item incluído no checklist.", "sucesso")
    return redirect(url_for("qualidade.checklist", stage_id=stage.id), 303)


@bp.post("/checklist-itens/<uuid:item_id>/arquivar")
@tenant_required(ROLE_SUPERVISOR)
def checklist_item_archive(item_id):
    item = get_or_404(StageChecklistItem, item_id)
    stage = item.stage
    checklists_svc.archive_item(item, current_user.id)
    db.session.commit()
    flash("Item arquivado. Respostas antigas continuam guardadas.", "sucesso")
    return redirect(url_for("qualidade.checklist", stage_id=stage.id), 303)


@bp.post("/etapas/<uuid:stage_id>/checklist/exigir")
@tenant_required(ROLE_SUPERVISOR)
def checklist_required(stage_id):
    stage = get_or_404(Stage, stage_id)
    required = request.form.get("required") in {"y", "1", "on", "true"}
    checklists_svc.set_required(stage, required, current_user.id)
    db.session.commit()
    flash("A etapa passa a sinalizar checklist pendente." if required else "Checklist deixa de ser exigido.", "sucesso")
    return redirect(url_for("qualidade.checklist", stage_id=stage.id), 303)


@bp.post("/etapas/<uuid:stage_id>/inspecoes")
@tenant_required(ROLE_OPERATOR)
def inspection_start(stage_id):
    stage = get_or_404(Stage, stage_id)
    unit = None
    raw_unit = (request.form.get("unit_id") or "").strip()
    if raw_unit and not modules.is_enabled(g.company, modules.UNIDADES):
        raw_unit = ""  # R6: sem o módulo de número de série, a inspeção vale para a etapa inteira
    if raw_unit:
        unit = get_or_404(Unit, raw_unit)  # de outra empresa → 404
        if unit.project_id != stage.project_id:
            abort(404)
    try:
        inspection = checklists_svc.start_inspection(stage, current_user.id, unit=unit)
    except checklists_svc.ChecklistError as exc:
        db.session.rollback()
        return _checklist_page(stage, status=400, error=str(exc))
    db.session.commit()
    return redirect(url_for("qualidade.inspection", inspection_id=inspection.id), 303)


def _inspection_page(inspection: StageInspection, *, status: int = 200, error: str | None = None, posted=None):
    return (
        render_template(
            "qualidade/inspecao.html",
            inspection=inspection,
            stage=inspection.stage,
            project=inspection.stage.project,
            items=checklists_svc.items_of(inspection),
            current=checklists_svc.current_answers(inspection),
            history=checklists_svc.history_by_item(inspection),
            results=checklists_svc.RESULT_LABELS,
            can_correct=g.membership.has_role(ROLE_SUPERVISOR),
            note_max=CHECKLIST_NOTE_MAX,
            error=error,
            posted=posted or {},
        ),
        status,
    )


@bp.get("/inspecoes/<uuid:inspection_id>")
@tenant_required(ROLE_OPERATOR)
def inspection(inspection_id):
    return _inspection_page(get_or_404(StageInspection, inspection_id))


def _posted_answers(inspection: StageInspection) -> dict:
    out = {}
    for item in checklists_svc.items_of(inspection):
        result = request.form.get(f"resultado-{item.id}")
        if result:
            out[item.id] = checklists_svc.AnswerInput(result, request.form.get(f"obs-{item.id}"))
    return out


@bp.post("/inspecoes/<uuid:inspection_id>")
@tenant_required(ROLE_OPERATOR)
def inspection_save(inspection_id):
    """Salva o rascunho (``acao=salvar``) ou salva e assina (``acao=assinar``)."""
    inspection = get_or_404(StageInspection, inspection_id)
    answers = _posted_answers(inspection)
    try:
        version = int(request.form.get("version", ""))
    except ValueError:
        version = None
    sign = request.form.get("acao") == "assinar"
    try:
        checklists_svc.save_answers(inspection, answers, current_user.id, version)
        if sign:
            checklists_svc.sign(inspection, current_user.id, None)
    except checklists_svc.InspectionConflict as exc:
        db.session.rollback()
        return _inspection_page(get_or_404(StageInspection, inspection_id), status=409, error=str(exc))
    except checklists_svc.ChecklistError as exc:
        db.session.rollback()
        return _inspection_page(get_or_404(StageInspection, inspection_id), status=400, error=str(exc),
                                posted=answers)
    db.session.commit()
    flash("Inspeção assinada." if sign else "Rascunho salvo.", "sucesso")
    return redirect(url_for("qualidade.inspection", inspection_id=inspection.id), 303)


@bp.post("/inspecoes/<uuid:inspection_id>/corrigir")
@tenant_required(ROLE_SUPERVISOR)
def inspection_correct(inspection_id):
    inspection = get_or_404(StageInspection, inspection_id)
    item = get_or_404(StageChecklistItem, request.form.get("item_id", ""), include_archived=True)
    if item.stage_id != inspection.stage_id:
        abort(404)
    value = checklists_svc.AnswerInput(request.form.get("result", ""), request.form.get("note"))
    try:
        checklists_svc.correct(inspection, item, value, request.form.get("reason"), current_user.id)
    except checklists_svc.ChecklistError as exc:
        db.session.rollback()
        return _inspection_page(get_or_404(StageInspection, inspection_id), status=400, error=str(exc))
    db.session.commit()
    flash("Correção registrada. A resposta anterior continua no histórico.", "sucesso")
    return redirect(url_for("qualidade.inspection", inspection_id=inspection.id, _anchor=f"item-{item.id}"), 303)


# ================================================================ unidades / número de série (bloco 3)
# Rastreabilidade (não muda o cálculo). Supervisor+ cria e muda status; operador+ vê, busca e
# registra uma atividade numa unidade. Limite = quantidade do projeto (no serviço).


def _int_form(name: str, default: int | None = None) -> int | None:
    try:
        return int((request.form.get(name) or "").strip())
    except ValueError:
        return default


def _units_page(project: Project, *, status: int = 200, error: str | None = None, form=None):
    q = (request.args.get("q") or "").strip()[:60]
    units = units_svc.search(q, project) if q else units_svc.list_units(project)
    return (
        render_template(
            "qualidade/unidades.html",
            project=project,
            units=units,
            total=units_svc.count_units(project),
            q=q,
            labels=units_svc.STATUS_LABELS,
            can_manage=g.membership.has_role(ROLE_SUPERVISOR),
            error=error,
            form=form or {},
        ),
        status,
    )


@bp.get("/projetos/<uuid:project_id>/unidades")
@tenant_required(ROLE_OPERATOR)
def units(project_id):
    return _units_page(get_or_404(Project, project_id))


@bp.post("/projetos/<uuid:project_id>/unidades/gerar")
@tenant_required(ROLE_SUPERVISOR)
def units_generate(project_id):
    project = get_or_404(Project, project_id)
    try:
        created = units_svc.generate(
            project,
            request.form.get("prefix"),
            _int_form("start", -1),
            _int_form("count", 0),
            _int_form("width", 0),
            current_user.id,
        )
    except units_svc.UnitError as exc:
        db.session.rollback()
        return _units_page(project, status=400, error=str(exc), form=request.form)
    db.session.commit()
    flash(f"{len(created)} números de série cadastrados.", "sucesso")
    return redirect(url_for("qualidade.units", project_id=project.id), 303)


@bp.post("/projetos/<uuid:project_id>/unidades/importar")
@tenant_required(ROLE_SUPERVISOR)
def units_import(project_id):
    project = get_or_404(Project, project_id)
    try:
        created = units_svc.import_list(project, request.form.get("serials"), current_user.id)
    except units_svc.UnitError as exc:
        db.session.rollback()
        return _units_page(project, status=400, error=str(exc), form=request.form)
    db.session.commit()
    flash(f"{len(created)} números de série cadastrados.", "sucesso")
    return redirect(url_for("qualidade.units", project_id=project.id), 303)


@bp.get("/unidades")
@tenant_required(ROLE_OPERATOR)
def units_search():
    """Busca por número de série em todos os projetos ativos da empresa da sessão."""
    q = (request.args.get("q") or "").strip()[:60]
    return render_template(
        "qualidade/unidades_busca.html", q=q, units=units_svc.search(q), labels=units_svc.STATUS_LABELS
    )


def _unit_page(unit: Unit, *, status: int = 200, error: str | None = None):
    project = unit.project
    hist = units_svc.history(unit)
    activities = [
        (stage, activity)
        for stage in projects_svc.active_stages(project)
        for activity in projects_svc.active_activities(stage)
    ]
    return (
        render_template(
            "qualidade/unidade.html",
            unit=unit,
            project=project,
            h=hist,
            labels=units_svc.STATUS_LABELS,
            action_labels=audit.ACTION_LABELS,
            results=checklists_svc.RESULT_LABELS,
            activities=activities,
            can_manage=g.membership.has_role(ROLE_SUPERVISOR),
            error=error,
        ),
        status,
    )


@bp.get("/unidades/<uuid:unit_id>")
@tenant_required(ROLE_OPERATOR)
def unit_detail(unit_id):
    """Histórico completo da unidade (lançamentos, inspeções, mudanças de status)."""
    return _unit_page(get_or_404(Unit, unit_id, include_archived=True))


@bp.post("/unidades/<uuid:unit_id>/status")
@tenant_required(ROLE_SUPERVISOR)
def unit_status(unit_id):
    unit = get_or_404(Unit, unit_id)
    try:
        units_svc.set_status(unit, request.form.get("status", ""), current_user.id, _int_form("version"))
    except units_svc.UnitConflict as exc:
        db.session.rollback()
        return _unit_page(get_or_404(Unit, unit_id), status=409, error=str(exc))
    except units_svc.UnitError as exc:
        db.session.rollback()
        return _unit_page(get_or_404(Unit, unit_id), status=400, error=str(exc))
    db.session.commit()
    flash("Situação da unidade atualizada.", "sucesso")
    return redirect(url_for("qualidade.unit_detail", unit_id=unit.id), 303)


@bp.post("/unidades/<uuid:unit_id>/registrar")
@tenant_required(ROLE_OPERATOR)
def unit_register(unit_id):
    """+1 peça na atividade escolhida, ligada a esta unidade. Atividade de outro projeto/empresa → 404."""
    unit = get_or_404(Unit, unit_id)
    activity = get_or_404(Activity, request.form.get("activity_id", ""))
    if activity.stage.project_id != unit.project_id:
        abort(404)
    try:
        units_svc.register_for_unit(unit, activity, current_user.id, _int_form("version"))
    except projects_svc.ConflictError as exc:
        db.session.rollback()
        return _unit_page(get_or_404(Unit, unit_id), status=409, error=str(exc))
    except (units_svc.UnitError, projects_svc.ProgressError) as exc:
        db.session.rollback()
        return _unit_page(get_or_404(Unit, unit_id), status=400, error=str(exc))
    db.session.commit()
    flash(f"+1 em {activity.name} · unidade {unit.serial}.", "sucesso")
    return redirect(url_for("qualidade.unit_detail", unit_id=unit.id), 303)
