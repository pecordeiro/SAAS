"""Área logada (/app). Toda rota passa por tenant_required e consulta via tenancy."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, flash, g, redirect, render_template, url_for
from flask_login import current_user

from app.extensions import db
from app.forms import ActivityForm, ProgressForm, ProjectForm, StageForm
from app.models import ROLE_OPERATOR, ROLE_SUPERVISOR, Activity, Project, Stage
from app.services import projects as svc
from app.services.projects import ConflictError, NewActivity, ProgressError
from app.tenancy import get_or_404, tenant_required

bp = Blueprint("app", __name__, url_prefix="/app")


@bp.get("/")
@tenant_required(ROLE_OPERATOR)
def home():
    return redirect(url_for("app.projects"))


@bp.get("/projetos")
@tenant_required(ROLE_OPERATOR)
def projects():
    items = [(p, svc.summary(p)) for p in svc.list_projects()]
    return render_template("app/projects.html", items=items)


@bp.route("/projetos/novo", methods=["GET", "POST"])
@tenant_required(ROLE_SUPERVISOR)
def project_new():
    form = ProjectForm()
    if form.validate_on_submit():
        project = svc.create_project(
            g.company,
            name=form.name.data,
            quantity=form.quantity.data,
            start_date=form.start_date.data,
            due_date=form.due_date.data,
            people=form.people.data,
            hours_per_day=form.hours_per_day.data,
            stages=form.new_stages(),
        )
        db.session.commit()
        flash("Projeto criado.", "sucesso")
        return redirect(url_for("app.project_detail", project_id=project.id), 303)
    status = 400 if form.is_submitted() else 200
    return render_template("app/project_new.html", form=form), status


def _render_detail(project: Project, *, errors: dict | None = None, status: int = 200):
    result = svc.summary(project)
    stages = svc.active_stages(project)
    rows = []
    for stage, stage_result in zip(stages, result.etapas):
        activities = svc.active_activities(stage)
        rows.append((stage, stage_result, list(zip(activities, stage_result.atividades))))
    can_edit = g.membership.has_role(ROLE_SUPERVISOR)
    return (
        render_template(
            "app/project_detail.html",
            project=project,
            result=result,
            rows=rows,
            forecast=svc.forecast_end(project, result, g.company, date.today()),
            errors=errors or {},
            progress_form=ProgressForm(formdata=None),
            stage_form=StageForm(formdata=None),
            activity_form=ActivityForm(formdata=None),
            can_edit=can_edit,
        ),
        status,
    )


@bp.get("/projetos/<uuid:project_id>")
@tenant_required(ROLE_OPERATOR)
def project_detail(project_id):
    project = get_or_404(Project, project_id)
    return _render_detail(project)


@bp.get("/projetos/<uuid:project_id>/historico")
@tenant_required(ROLE_OPERATOR)
def project_history(project_id):
    project = get_or_404(Project, project_id)
    return render_template("app/history.html", project=project, entries=svc.history(project))


@bp.post("/projetos/<uuid:project_id>/etapas")
@tenant_required(ROLE_SUPERVISOR)
def stage_create(project_id):
    project = get_or_404(Project, project_id)
    form = StageForm()
    if not form.validate():
        return _render_detail(project, errors={"stage": "Informe o nome da etapa."}, status=400)
    svc.add_stage(project, form.name.data, [])
    db.session.commit()
    flash("Etapa incluída.", "sucesso")
    return redirect(url_for("app.project_detail", project_id=project.id), 303)


@bp.get("/etapas/<uuid:stage_id>")
@tenant_required(ROLE_OPERATOR)
def stage_detail(stage_id):
    stage = get_or_404(Stage, stage_id)
    return redirect(url_for("app.project_detail", project_id=stage.project_id, _anchor=f"etapa-{stage.id}"))


@bp.post("/etapas/<uuid:stage_id>/atividades")
@tenant_required(ROLE_SUPERVISOR)
def activity_create(stage_id):
    stage = get_or_404(Stage, stage_id)
    form = ActivityForm()
    if not form.validate():
        return _render_detail(stage.project, errors={stage.id: "Informe nome e tempo ideal (min) válidos."}, status=400)
    svc.add_activity(stage, NewActivity(name=form.name.data, ideal_minutes=form.ideal_minutes.data))
    db.session.commit()
    flash("Atividade incluída.", "sucesso")
    return redirect(url_for("app.project_detail", project_id=stage.project_id, _anchor=f"etapa-{stage.id}"), 303)


@bp.get("/atividades/<uuid:activity_id>")
@tenant_required(ROLE_OPERATOR)
def activity_detail(activity_id):
    activity = get_or_404(Activity, activity_id)
    return redirect(
        url_for("app.project_detail", project_id=activity.stage.project_id, _anchor=f"atividade-{activity.id}")
    )


@bp.post("/atividades/<uuid:activity_id>/registrar")
@tenant_required(ROLE_OPERATOR)
def activity_progress(activity_id):
    activity = get_or_404(Activity, activity_id)
    project = activity.stage.project
    form = ProgressForm()
    if not form.validate():
        return _render_detail(project, errors={activity.id: "Informe um número inteiro de peças (mínimo 1)."}, status=400)
    try:
        svc.register_progress(activity, form.delta.data, form.version.data, current_user.id)
    except ConflictError as exc:
        db.session.rollback()
        project = get_or_404(Project, project.id)
        return _render_detail(project, errors={activity_id: str(exc)}, status=409)
    except ProgressError as exc:
        return _render_detail(project, errors={activity.id: str(exc)}, status=400)
    db.session.commit()
    flash(f"{form.delta.data} peça(s) registrada(s) em “{activity.name}”.", "sucesso")
    return redirect(url_for("app.project_detail", project_id=project.id, _anchor=f"atividade-{activity.id}"), 303)
