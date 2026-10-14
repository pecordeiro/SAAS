"""Edição de projeto (Fase 4): dados, renomear/reordenar/arquivar etapas e atividades,
duplicar, arquivar, comparar/aplicar versão do modelo e desfazer registro (D13).

Tudo supervisor+, POST com CSRF, recursos resolvidos por ``get_or_404`` (empresa da sessão;
arquivado = 404). Também registra, para o app inteiro, a resposta 402 de
``entitlements.EntitlementError`` e o aviso de modo leitura no layout.
"""

from __future__ import annotations

from flask import Blueprint, abort, flash, g, redirect, render_template, url_for
from flask_login import current_user

from app.extensions import db
from app.forms_production import ActivityEditForm, ConfirmForm, MoveForm, ProjectEditForm, RenameForm
from app.models import ROLE_SUPERVISOR, Activity, Project, ProgressEntry, Stage
from app.services import entitlements
from app.services import projects as svc
from app.services import templates as tsvc
from app.tenancy import get_or_404, tenant_required

bp = Blueprint("edicao", __name__, url_prefix="/app")


@bp.app_errorhandler(entitlements.EntitlementError)
def entitlement_error(exc: entitlements.EntitlementError):
    db.session.rollback()
    return render_template("errors/402.html", title=exc.title, message=exc.message), exc.status_code


@bp.app_context_processor
def inject_read_only():
    company = getattr(g, "company", None)
    if company is None:
        return {"read_only": False}
    if not hasattr(g, "_read_only"):
        g._read_only = entitlements.is_read_only(company)
    return {"read_only": g._read_only}


# ---------------------------------------------------------------- projeto


def _edit_page(project: Project, form: ProjectEditForm, status: int = 200, error: str | None = None):
    stages = [(s, svc.active_activities(s)) for s in svc.active_stages(project)]
    return (
        render_template(
            "edicao/project_edit.html",
            project=project,
            form=form,
            stages=stages,
            error=error,
            comparison=tsvc.compare(project) if project.template_version_id else None,
            confirm_form=ConfirmForm(formdata=None),
        ),
        status,
    )


@bp.route("/projetos/<uuid:project_id>/editar", methods=["GET", "POST"])
@tenant_required(ROLE_SUPERVISOR)
def project_edit(project_id):
    project = get_or_404(Project, project_id)
    form = ProjectEditForm(obj=project)
    if form.validate_on_submit():
        try:
            svc.update_project(
                project,
                name=form.name.data,
                quantity=form.quantity.data,
                start_date=form.start_date.data,
                due_date=form.due_date.data,
                people=form.people.data,
                hours_per_day=form.hours_per_day.data,
                product=form.product.data,
                user_id=current_user.id,
            )
        except svc.EditError as exc:
            db.session.rollback()
            project = get_or_404(Project, project_id)
            return _edit_page(project, form, 400, str(exc))
        db.session.commit()
        flash("Projeto atualizado.", "sucesso")
        return redirect(url_for("edicao.project_edit", project_id=project.id), 303)
    return _edit_page(project, form, 400 if form.is_submitted() else 200)


@bp.post("/projetos/<uuid:project_id>/duplicar")
@tenant_required(ROLE_SUPERVISOR)
def project_duplicate(project_id):
    project = get_or_404(Project, project_id)
    copy = svc.duplicate_project(project, current_user.id)
    db.session.commit()
    flash("Projeto duplicado com progresso zerado.", "sucesso")
    return redirect(url_for("app.project_detail", project_id=copy.id), 303)


@bp.post("/projetos/<uuid:project_id>/arquivar")
@tenant_required(ROLE_SUPERVISOR)
def project_archive(project_id):
    project = get_or_404(Project, project_id)
    form = ConfirmForm()
    if not form.validate():
        flash("Marque a confirmação para arquivar.", "erro")
        return redirect(url_for("edicao.project_edit", project_id=project.id), 303)
    svc.archive_project(project, current_user.id)
    db.session.commit()
    flash("Projeto arquivado. O histórico continua guardado.", "sucesso")
    return redirect(url_for("app.projects"), 303)


@bp.get("/projetos/<uuid:project_id>/modelo")
@tenant_required(ROLE_SUPERVISOR)
def project_compare(project_id):
    project = get_or_404(Project, project_id)
    comparison = tsvc.compare(project)
    if comparison.current_version is None:
        abort(404)
    return render_template(
        "edicao/compare.html", project=project, comparison=comparison, confirm_form=ConfirmForm(formdata=None)
    )


@bp.post("/projetos/<uuid:project_id>/modelo/aplicar")
@tenant_required(ROLE_SUPERVISOR)
def project_apply_template(project_id):
    project = get_or_404(Project, project_id)
    form = ConfirmForm()
    if not form.validate():
        flash("Marque a confirmação para aplicar a versão do modelo.", "erro")
        return redirect(url_for("edicao.project_compare", project_id=project.id), 303)
    try:
        comparison = tsvc.apply_current_version(project, form.version_id.data, current_user.id)
    except tsvc.TemplateError as exc:
        db.session.rollback()
        flash(str(exc), "erro")
        return redirect(url_for("app.project_detail", project_id=project_id), 303)
    db.session.commit()
    flash(f"Versão {comparison.current_version.number} do modelo aplicada.", "sucesso")
    return redirect(url_for("app.project_detail", project_id=project.id), 303)


# ---------------------------------------------------------------- etapas


def _back(project_id):
    return redirect(url_for("edicao.project_edit", project_id=project_id), 303)


@bp.post("/etapas/<uuid:stage_id>/renomear")
@tenant_required(ROLE_SUPERVISOR)
def stage_rename(stage_id):
    stage = get_or_404(Stage, stage_id)
    form = RenameForm()
    if not form.validate():
        flash("Informe o nome da etapa.", "erro")
        return _back(stage.project_id)
    svc.rename_stage(stage, form.name.data)
    db.session.commit()
    flash("Etapa renomeada.", "sucesso")
    return _back(stage.project_id)


@bp.post("/etapas/<uuid:stage_id>/mover")
@tenant_required(ROLE_SUPERVISOR)
def stage_move(stage_id):
    stage = get_or_404(Stage, stage_id)
    form = MoveForm()
    if not form.validate():
        abort(400)
    svc.move_stage(stage, -1 if form.direction.data == "up" else 1)
    db.session.commit()
    return _back(stage.project_id)


@bp.post("/etapas/<uuid:stage_id>/arquivar")
@tenant_required(ROLE_SUPERVISOR)
def stage_archive(stage_id):
    stage = get_or_404(Stage, stage_id)
    svc.archive_stage(stage, current_user.id)
    db.session.commit()
    flash("Etapa arquivada. Os registros dela continuam no histórico.", "sucesso")
    return _back(stage.project_id)


# ---------------------------------------------------------------- atividades


@bp.post("/atividades/<uuid:activity_id>/editar")
@tenant_required(ROLE_SUPERVISOR)
def activity_edit(activity_id):
    activity = get_or_404(Activity, activity_id)
    form = ActivityEditForm()
    project_id = activity.stage.project_id
    if not form.validate():
        flash("Informe nome e tempo ideal (min) válidos.", "erro")
        return _back(project_id)
    svc.update_activity(activity, form.name.data, form.ideal_minutes.data)
    db.session.commit()
    flash("Atividade atualizada.", "sucesso")
    return _back(project_id)


@bp.post("/atividades/<uuid:activity_id>/mover")
@tenant_required(ROLE_SUPERVISOR)
def activity_move(activity_id):
    activity = get_or_404(Activity, activity_id)
    form = MoveForm()
    if not form.validate():
        abort(400)
    project_id = activity.stage.project_id
    svc.move_activity(activity, -1 if form.direction.data == "up" else 1)
    db.session.commit()
    return _back(project_id)


@bp.post("/atividades/<uuid:activity_id>/arquivar")
@tenant_required(ROLE_SUPERVISOR)
def activity_archive(activity_id):
    activity = get_or_404(Activity, activity_id)
    project_id = activity.stage.project_id
    svc.archive_activity(activity, current_user.id)
    db.session.commit()
    flash("Atividade arquivada. Os registros dela continuam no histórico.", "sucesso")
    return _back(project_id)


# ---------------------------------------------------------------- desfazer registro (D13)


@bp.route("/registros/<uuid:entry_id>/desfazer", methods=["GET", "POST"])
@tenant_required(ROLE_SUPERVISOR)
def entry_undo(entry_id):
    entry = get_or_404(ProgressEntry, entry_id)
    activity = entry.activity
    project = activity.stage.project
    if project.archived_at is not None or activity.archived_at is not None or activity.stage.archived_at is not None:
        abort(404)
    history_url = url_for("app.project_history", project_id=project.id)
    form = ConfirmForm()
    if form.is_submitted():
        if not form.validate():
            flash("Marque a confirmação para desfazer.", "erro")
            return redirect(url_for("edicao.entry_undo", entry_id=entry.id), 303)
        try:
            svc.undo_progress(entry, current_user.id)
        except svc.ProgressError as exc:
            db.session.rollback()
            flash(str(exc), "erro")
            return redirect(history_url, 303)
        db.session.commit()
        flash(f"Registro desfeito. {activity.name}: {activity.units_done} de {project.quantity}.", "sucesso")
        return redirect(history_url, 303)
    return render_template(
        "edicao/undo.html",
        entry=entry,
        activity=activity,
        project=project,
        undone=svc.is_undone(entry),
        form=ConfirmForm(formdata=None),
    )
