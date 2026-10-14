"""Área logada (/app). Toda rota passa por tenant_required e consulta via tenancy."""

from __future__ import annotations

from collections import OrderedDict
from datetime import date

from flask import Blueprint, flash, g, redirect, render_template, url_for
from flask_login import current_user

from app.extensions import db
from app.forms import ActivityForm, ProgressForm, StageForm
from app.forms_production import ProjectFromTemplateForm
from app.models import ROLE_OPERATOR, ROLE_SUPERVISOR, Activity, Project, Stage, Template
from app.formatting import local_dt
from app.services import audit, calc
from app.services import projects as svc
from app.services import templates as tsvc
from app.services.projects import ConflictError, NewActivity, ProgressError
from app.tenancy import get_or_404, tenant_required

bp = Blueprint("app", __name__, url_prefix="/app")


@bp.get("/")
@tenant_required(ROLE_OPERATOR)
def home():
    return redirect(url_for("app.projects"))


def _project_status(project: Project, result: calc.ResultadoProjeto) -> str:
    """Situação do projeto para o selo: mesma regra de status das etapas (calc), aplicada às unidades prontas."""
    return calc.status_etapa(result.unidades_concluidas, project.quantity, result.progresso_geral)


def _deadline(project: Project, result: calc.ResultadoProjeto, status: str) -> dict:
    """Término previsto e se cabe no prazo (só exibição; datas vêm de svc/calc)."""
    forecast = svc.forecast_end(project, result, g.company, date.today())
    late = bool(
        status != calc.STATUS_CONCLUIDA and forecast and project.due_date and forecast > project.due_date
    )
    on_time = bool(status != calc.STATUS_CONCLUIDA and forecast and project.due_date and not late)
    delay = svc.delay_workdays(project, forecast, g.company) if late else 0
    return {"forecast": forecast, "late": late, "on_time": on_time, "delay": delay}


@bp.get("/projetos")
@tenant_required(ROLE_OPERATOR)
def projects():
    items = []
    for project in svc.list_projects():
        result = svc.summary(project)
        status = _project_status(project, result)
        items.append((project, result, status, _deadline(project, result, status)))
    return render_template("app/projects.html", items=items)


@bp.route("/projetos/novo", methods=["GET", "POST"])
@tenant_required(ROLE_SUPERVISOR)
def project_new():
    form = ProjectFromTemplateForm()
    templates = tsvc.list_templates()
    form.template_id.choices = [("", "Sem modelo (digitar as etapas)")] + [
        (str(t.id), f"{t.name} · v{t.current_version.number if t.current_version else 1}") for t in templates
    ]
    if form.validate_on_submit():
        fields = dict(
            name=form.name.data,
            quantity=form.quantity.data,
            start_date=form.start_date.data,
            due_date=form.due_date.data,
            people=form.people.data,
            hours_per_day=form.hours_per_day.data,
        )
        if form.template_id.data:
            # Id do formulário SEMPRE resolvido na empresa da sessão (outra empresa → 404).
            template = get_or_404(Template, form.template_id.data)
            project = tsvc.create_project_from_template(g.company, template, **fields)
        else:
            project = svc.create_project(g.company, stages=form.new_stages(), **fields)
        db.session.commit()
        flash("Projeto criado.", "sucesso")
        return redirect(url_for("app.project_detail", project_id=project.id), 303)
    status = 400 if form.is_submitted() else 200
    return render_template("app/project_new.html", form=form, has_templates=bool(templates)), status


def _render_detail(project: Project, *, errors: dict | None = None, status: int = 200):
    result = svc.summary(project)
    stages = svc.active_stages(project)
    rows = []
    for stage, stage_result in zip(stages, result.etapas):
        activities = svc.active_activities(stage)
        rows.append((stage, stage_result, list(zip(activities, stage_result.atividades))))
    can_edit = g.membership.has_role(ROLE_SUPERVISOR)
    project_status = _project_status(project, result)
    deadline = _deadline(project, result, project_status)
    # Etapa atual = primeira não concluída: vem aberta; as demais ficam recolhidas.
    current_stage = next((s.id for s, sr, _ in rows if sr.status != calc.STATUS_CONCLUIDA), None)
    return (
        render_template(
            "app/project_detail.html",
            project=project,
            result=result,
            rows=rows,
            project_status=project_status,
            deadline=deadline,
            current_stage=current_stage,
            recent=svc.history(project, limit=5),
            forecast=deadline["forecast"],
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
    project = get_or_404(Project, project_id, include_archived=True)
    entries = svc.history(project)
    undone = svc.undone_ids(entries)
    changes = audit.for_object(g.company.id, "project", project.id)
    # Agrupa por dia (fuso da empresa) para a lista e para o gráfico “peças por dia”.
    days: OrderedDict = OrderedDict()
    for entry in entries:
        days.setdefault(local_dt(entry.at, g.company.timezone).date(), []).append(entry)
    per_day = [
        {"label": day.strftime("%d/%m"), "value": sum(e.delta for e in items)}
        for day, items in list(days.items())[:14][::-1]
    ]
    return render_template(
        "app/history.html",
        project=project,
        entries=entries,
        days=days,
        per_day=per_day,
        undone=undone,
        changes=changes,
        action_labels=audit.ACTION_LABELS,
        can_undo=g.membership.has_role(ROLE_SUPERVISOR),
    )


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
    flash(f"+{form.delta.data} em {activity.name} · {activity.units_done} de {project.quantity}", "sucesso")
    return redirect(url_for("app.project_detail", project_id=project.id, _anchor=f"atividade-{activity.id}"), 303)
