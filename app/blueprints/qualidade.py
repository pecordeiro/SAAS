"""Etapa G — qualidade: evidências por atividade (comentários e fotos).

Regras (CLAUDE.md): empresa SÓ da sessão (``tenant_required`` + ``get_or_404``; recurso de outra
empresa → 404), papéis na rota (esconder botão não substitui a recusa), POST com CSRF, foto
nunca em pasta pública — só por ``/app/fotos/<uuid>`` com Content-Type fixo, ``nosniff``,
``Cache-Control: private`` e CSP ``sandbox`` própria.
"""

from __future__ import annotations

from flask import Blueprint, Response, abort, current_app, flash, g, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db, limiter
from app.models import ROLE_OPERATOR, ROLE_SUPERVISOR, Activity
from app.models.quality import PHOTO_CAPTION_MAX, ActivityComment, ActivityPhoto
from app.services import comments as comments_svc
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
