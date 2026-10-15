"""Área logada (/app). Toda rota passa por tenant_required e consulta via tenancy."""

from __future__ import annotations

import math
import uuid
from collections import OrderedDict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from flask import Blueprint, Response, abort, flash, g, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.formatting import br_hours, local_dt
from app.forms import ActivityForm, ProgressForm, StageForm
from app.forms_production import ProjectFromTemplateForm
from app.models import ROLE_OPERATOR, ROLE_SUPERVISOR, Activity, Project, Stage, Template
from app.services import audit, calc, exporter
from app.services import projects as svc
from app.services import templates as tsvc
from app.services.holidays import holidays_for
from app.services.projects import ConflictError, NewActivity, ProgressError
from app.tenancy import get_or_404, tenant_required

bp = Blueprint("app", __name__, url_prefix="/app")

PROJECTS_PER_PAGE = 20
HISTORY_PER_PAGE = 25

STATUS_TABS = (("ativos", "Ativos"), ("concluidos", "Concluídos"), ("todos", "Todos"))
DEADLINE_FILTERS = (
    ("", "Qualquer prazo"),
    ("atraso", "Com atraso previsto"),
    ("semana", "Vence em 7 dias"),
    ("sem", "Sem prazo"),
)


def _is_htmx() -> bool:
    """Requisição feita pelo HTMX para trocar pedaços (não a navegação “boosted”)."""
    return request.headers.get("HX-Request") == "true" and not request.headers.get("HX-Boosted")


def _today() -> date:
    """Hoje no fuso da empresa (o servidor roda em UTC)."""
    try:
        return datetime.now(ZoneInfo(g.company.timezone)).date()
    except Exception:  # noqa: BLE001 - fuso inválido cai no padrão
        return date.today()


def _int_arg(name: str, default: int = 1) -> int:
    try:
        return max(1, int(request.args.get(name, default)))
    except (TypeError, ValueError):
        return default


def _uuid_arg(name: str) -> uuid.UUID | None:
    raw = request.args.get(name, "")
    try:
        return uuid.UUID(raw) if raw else None
    except ValueError:
        return None


@bp.get("/")
@tenant_required(ROLE_OPERATOR)
def home():
    return redirect(url_for("app.projects"))


def _project_status(project: Project, result: calc.ResultadoProjeto) -> str:
    """Situação do projeto para o selo: mesma regra de status das etapas (calc), aplicada às unidades prontas."""
    return calc.status_etapa(result.unidades_concluidas, project.quantity, result.progresso_geral)


def _deadline(project: Project, result: calc.ResultadoProjeto, status: str) -> dict:
    """Término previsto, atraso e folga em dias úteis (datas e contas vêm de svc/calc)."""
    today = _today()
    forecast = svc.forecast_end(project, result, g.company, today)
    done = status == calc.STATUS_CONCLUIDA
    late = bool(not done and forecast and project.due_date and forecast > project.due_date)
    on_time = bool(not done and forecast and project.due_date and not late)
    delay = svc.delay_workdays(project, forecast, g.company) if late else 0
    holidays, days = holidays_for(g.company.id), g.company.workdays()
    due = project.due_date
    return {
        "forecast": forecast,
        "late": late,
        "on_time": on_time,
        "delay": delay,
        # dias úteis de hoje até o prazo (0 se já passou) e quanto o prazo já passou
        "until_due": calc.dias_uteis_entre(today, due, holidays, days) if due and due > today and not done else 0,
        "overdue": calc.dias_uteis_entre(due, today, holidays, days) if due and today > due and not done else 0,
        "slack": calc.dias_uteis_entre(forecast, due, holidays, days) if on_time else 0,
    }


def _list_item(project: Project) -> dict:
    result = svc.summary(project)
    status = _project_status(project, result)
    return {"project": project, "result": result, "status": status, "deadline": _deadline(project, result, status)}


def _filtered_projects() -> tuple[list[dict], dict]:
    """Projetos da lista com os filtros da URL (status, prazo, busca) e as contagens das abas."""
    status = request.args.get("status", "ativos")
    status = status if status in svc.PROJECT_FILTERS else "ativos"
    deadline = request.args.get("prazo", "")
    deadline = deadline if deadline in dict(DEADLINE_FILTERS) else ""
    q = (request.args.get("q") or "").strip()[:80]
    items = [_list_item(p) for p in svc.list_projects(status, q)]
    if deadline == "atraso":
        items = [i for i in items if i["deadline"]["late"]]
    elif deadline == "semana":
        today = _today()
        items = [
            i
            for i in items
            if i["project"].due_date
            and 0 <= (i["project"].due_date - today).days <= 7
            and i["status"] != calc.STATUS_CONCLUIDA
        ]
    elif deadline == "sem":
        items = [i for i in items if i["project"].due_date is None]
    return items, {"status": status, "prazo": deadline, "q": q}


@bp.get("/projetos")
@tenant_required(ROLE_OPERATOR)
def projects():
    items, filters = _filtered_projects()
    page = _int_arg("page")
    pages = max(1, math.ceil(len(items) / PROJECTS_PER_PAGE))
    page = min(page, pages)
    visible = items[(page - 1) * PROJECTS_PER_PAGE : page * PROJECTS_PER_PAGE]
    return render_template(
        "app/projects.html",
        items=visible,
        total=len(items),
        page=page,
        pages=pages,
        per_page=PROJECTS_PER_PAGE,
        filters=filters,
        counts=svc.count_projects_by_status(),
        status_tabs=STATUS_TABS,
        deadline_filters=DEADLINE_FILTERS,
        filtered=bool(filters["q"] or filters["prazo"]),
        can_create=g.membership.has_role(ROLE_SUPERVISOR),
    )


@bp.get("/projetos/exportar.csv")
@tenant_required(ROLE_SUPERVISOR)
def projects_export():
    """CSV da lista com os mesmos filtros da tela (supervisor+)."""
    items, _ = _filtered_projects()
    rows = [
        {
            "name": i["project"].name,
            "product": i["project"].product,
            "units": i["result"].unidades_concluidas,
            "quantity": i["project"].quantity,
            "progress": i["result"].progresso_geral,
            "hours_left": i["result"].tempo_restante_h,
            "due": i["project"].due_date,
            "forecast": i["deadline"]["forecast"],
            "status": i["status"],
        }
        for i in items
    ]
    response = Response(exporter.projects_csv(rows), mimetype="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = 'attachment; filename="projetos.csv"'
    response.headers["Cache-Control"] = "no-store"
    return response


# ---------------------------------------------------------------- novo projeto


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
            product=form.product.data,
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
    return (
        render_template(
            "app/project_new.html",
            form=form,
            templates=[(t, t.current_version, tsvc.minutes_per_unit(t.current_version)) for t in templates],
            has_templates=bool(templates),
            workdays=g.company.workdays(),
        ),
        status,
    )


def _decimal_arg(name: str, default: Decimal) -> Decimal:
    try:
        value = Decimal(request.args.get(name, "").replace(",", "."))
    except (InvalidOperation, AttributeError):
        return default
    return value if value.is_finite() else default


def _date_arg(name: str) -> date | None:
    try:
        return date.fromisoformat(request.args.get(name, ""))
    except ValueError:
        return None


@bp.get("/projetos/novo/resumo")
@tenant_required(ROLE_SUPERVISOR)
def project_new_summary():
    """Fragmento HTMX do “Resumo” do novo projeto: tempo total, dias úteis, término e prazo."""
    raw_template = request.args.get("template_id", "")
    if not raw_template:
        return render_template("app/_project_summary.html", state="no_template")
    template = get_or_404(Template, raw_template)  # de outra empresa → 404
    try:
        quantity = int(request.args.get("quantity", ""))
        people = int(request.args.get("people", "1") or 1)
    except ValueError:
        return render_template("app/_project_summary.html", state="invalid")
    hours = _decimal_arg("hours_per_day", Decimal("8"))
    if not (1 <= quantity <= 100000 and 1 <= people <= 1000 and Decimal("0.5") <= hours <= 24):
        return render_template("app/_project_summary.html", state="invalid")
    summary = svc.plan_summary(
        minutes_per_unit=tsvc.minutes_per_unit(template.current_version),
        quantity=quantity,
        people=people,
        hours_per_day=hours,
        start=_date_arg("start_date"),
        due=_date_arg("due_date"),
        company=g.company,
        today=_today(),
    )
    return render_template("app/_project_summary.html", state="ok", summary=summary, template=template)


# ---------------------------------------------------------------- detalhe


def _detail_ctx(project: Project, *, errors=None, conflicts=None, deltas=None) -> dict:
    result = svc.summary(project)
    stages = svc.active_stages(project)
    rows = []
    for stage, stage_result in zip(stages, result.etapas):
        activities = svc.active_activities(stage)
        rows.append((stage, stage_result, list(zip(activities, stage_result.atividades))))
    project_status = _project_status(project, result)
    deadline = _deadline(project, result, project_status)
    # Etapa atual = primeira não concluída: vem aberta; as demais ficam recolhidas.
    current_stage = next((s.id for s, sr, _ in rows if sr.status != calc.STATUS_CONCLUIDA), None)
    progress_series = [
        {"label": s.name, "value": sr.progresso, "max": 1, "text": f"{sr.progresso * 100:.0f}%", "done": sr.progresso >= 1}
        for s, sr, _ in rows
    ]
    hours_series = [
        {"label": s.name, "value": round(sr.tempo_restante_min / 60, 2), "text": br_hours(sr.tempo_restante_min / 60, True)}
        for s, sr, _ in rows
    ]
    return dict(
        project=project,
        result=result,
        rows=rows,
        project_status=project_status,
        deadline=deadline,
        current_stage=current_stage,
        recent=svc.history(project, limit=5),
        last_entries=svc.last_entries(project),
        # Etapa D: resumo por pessoa (7 dias) só para supervisor+ — contas em calc.py.
        people=(
            svc.people_progress(project, tz=g.company.timezone, today=_today(), days=7)[:5]
            if g.membership.has_role(ROLE_SUPERVISOR)
            else []
        ),
        forecast=deadline["forecast"],
        errors=errors or {},
        conflicts=conflicts or {},
        deltas=deltas or {},
        progress_form=ProgressForm(formdata=None),
        stage_form=StageForm(formdata=None),
        activity_form=ActivityForm(formdata=None),
        can_edit=g.membership.has_role(ROLE_SUPERVISOR),
        progress_series=progress_series,
        hours_series=hours_series,
        detail_url=url_for("app.project_detail", project_id=project.id),
        only_activity=None,
        toast=None,
        oob=False,
    )


def _render_detail(project: Project, *, errors=None, conflicts=None, deltas=None, status: int = 200,
                   only_activity=None, toast: str | None = None, fragment: bool = False):
    """Página inteira; com ``fragment`` (registro via HTMX), só os pedaços que mudam (hx-swap-oob)."""
    ctx = _detail_ctx(project, errors=errors, conflicts=conflicts, deltas=deltas)
    if fragment:
        ctx.update(only_activity=only_activity, toast=toast, oob=True)
        return render_template("app/detail/_oob.html", **ctx), status
    return render_template("app/project_detail.html", **ctx), status


@bp.get("/projetos/<uuid:project_id>")
@tenant_required(ROLE_OPERATOR)
def project_detail(project_id):
    project = get_or_404(Project, project_id)
    return _render_detail(project)


@bp.get("/projetos/<uuid:project_id>/atualizar")
@tenant_required(ROLE_OPERATOR)
def project_refresh(project_id):
    """Atualização leve do detalhe (a cada 30 s, só com a aba visível): só leitura, só pedaços."""
    project = get_or_404(Project, project_id)
    ctx = _detail_ctx(project)
    ctx.update(oob=True)
    response = Response(render_template("app/detail/_oob.html", **ctx), mimetype="text/html")
    response.headers["Cache-Control"] = "no-store"
    return response


# ---------------------------------------------------------------- progresso por pessoa (Etapa D)

PEOPLE_PERIOD_TABS = (("7", "7 dias"), ("30", "30 dias"), ("90", "90 dias"), ("tudo", "Tudo"))


@bp.get("/projetos/<uuid:project_id>/pessoas")
@tenant_required(ROLE_SUPERVISOR)
def project_people(project_id):
    """Peças, registros e horas-padrão por pessoa no período + atividades atribuídas.
    Supervisor+ (dado de desempenho individual). Tudo calculado no servidor (calc.py)."""
    project = get_or_404(Project, project_id)
    period = request.args.get("periodo", "7")
    period = period if period in svc.PEOPLE_PERIODS else "7"
    rows = svc.people_progress(project, tz=g.company.timezone, today=_today(), days=svc.PEOPLE_PERIODS[period])
    series = [
        {"label": r.user.name if r.user else "Pessoa removida", "value": max(r.result.pecas, 0), "text": f"{r.result.pecas}"}
        for r in rows
        if r.result.registros or r.result.desfeitos
    ]
    return render_template(
        "app/people.html", project=project, rows=rows, period=period, period_tabs=PEOPLE_PERIOD_TABS, series=series
    )


# ---------------------------------------------------------------- histórico


def _history_page(project: Project | None, general_route: bool = False):
    """Histórico com filtros (atividade, pessoa; projeto no geral) e paginação."""
    activity = None
    activity_id = _uuid_arg("atividade")
    if activity_id is not None:
        activity = get_or_404(Activity, activity_id, include_archived=True)
        if project is not None and activity.stage.project_id != project.id:
            abort(404)
    user_id = _uuid_arg("usuario")
    users = svc.history_users(project)
    if user_id is not None and user_id not in {u.id for u in users}:
        user_id = None
    page = _int_arg("page")
    entries, total = svc.history_page(
        project, activity_id=activity.id if activity else None, user_id=user_id, page=page, per_page=HISTORY_PER_PAGE
    )
    pages = max(1, math.ceil(total / HISTORY_PER_PAGE))
    if page > pages:
        page = pages
        entries, total = svc.history_page(
            project, activity_id=activity.id if activity else None, user_id=user_id, page=page, per_page=HISTORY_PER_PAGE
        )
    undone_by = svc.undo_entries(entries)
    undone = set(undone_by)
    totals = svc.running_totals(entries)
    # Agrupa por dia (fuso da empresa) para a lista.
    days: OrderedDict = OrderedDict()
    for entry in entries:
        days.setdefault(local_dt(entry.at, g.company.timezone).date(), []).append(entry)
    per_day = [
        {"label": day.strftime("%d/%m"), "value": max(total_day, 0), "text": f"{total_day:+d}"}
        for day, total_day in svc.pieces_per_day(
            project, activity_id=activity.id if activity else None, user_id=user_id, tz=g.company.timezone
        )
    ]
    activity_choices = []
    if project is not None:
        for stage in svc.active_stages(project):
            for act in svc.active_activities(stage):
                activity_choices.append((act.id, f"{stage.name} › {act.name}"))
    project_choices = [(p.id, p.name) for p in svc.list_projects("todos")] if project is None else []
    base_args = {"project_id": project.id} if (project is not None and general_route is False) else {}
    url_args = dict(
        base_args,
        projeto=project.id if (project is not None and general_route) else None,
        atividade=activity.id if activity else None,
        usuario=user_id,
    )
    return dict(
        history_endpoint="app.history" if general_route else "app.project_history",
        url_args=url_args,
        url_args_base=base_args,
        sel_project=None,
        project=project,
        entries=entries,
        days=days,
        per_day=per_day,
        undone=undone,
        undone_by=undone_by,
        totals=totals,
        total=total,
        page=page,
        pages=pages,
        per_page=HISTORY_PER_PAGE,
        users=users,
        activity_choices=activity_choices,
        project_choices=project_choices,
        sel_activity=activity.id if activity else None,
        sel_user=user_id,
        action_labels=audit.ACTION_LABELS,
        can_undo=g.membership.has_role(ROLE_SUPERVISOR),
        filtered=bool(activity or user_id),
    )


@bp.get("/projetos/<uuid:project_id>/historico")
@tenant_required(ROLE_OPERATOR)
def project_history(project_id):
    project = get_or_404(Project, project_id, include_archived=True)
    ctx = _history_page(project)
    ctx["changes"] = audit.for_object(g.company.id, "project", project.id)
    return render_template("app/history.html", **ctx)


@bp.get("/historico")
@tenant_required(ROLE_OPERATOR)
def history():
    """Histórico geral da empresa (todos os projetos); filtro opcional por projeto."""
    project = None
    project_id = _uuid_arg("projeto")
    if project_id is not None:
        project = get_or_404(Project, project_id, include_archived=True)
    ctx = _history_page(project, general_route=True)
    ctx["changes"] = audit.for_object(g.company.id, "project", project.id) if project else []
    ctx["general"] = True
    ctx["sel_project"] = project.id if project else None
    return render_template("app/history.html", **ctx)


# ---------------------------------------------------------------- etapas, atividades, registro


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
    raw_delta = form.delta.raw_data[0] if form.delta.raw_data else ""
    if not form.validate():
        return _render_detail(
            project,
            errors={activity.id: "Informe um número inteiro de peças (mínimo 1)."},
            deltas={activity.id: raw_delta},
            status=400,
            only_activity=activity.id,
            fragment=_is_htmx(),
        )
    delta = form.delta.data
    try:
        svc.register_progress(activity, delta, form.version.data, current_user.id)
    except ConflictError:
        db.session.rollback()
        # Valor ATUAL: recarrega e pede confirmação (nada foi gravado ainda).
        activity = get_or_404(Activity, activity_id)
        project = activity.stage.project
        faltam = max(0, project.quantity - activity.units_done)
        message = (
            f"Outra pessoa registrou antes: esta atividade agora está em {activity.units_done} de {project.quantity}."
        )
        if faltam == 0:
            message += " Ela já está completa; nada a somar."
        else:
            message += f" Confirme para somar +{min(delta, faltam)} sobre o valor atual."
        return _render_detail(
            project,
            errors={activity.id: message},
            conflicts={activity.id: faltam > 0},
            deltas={activity.id: min(delta, faltam) if faltam else 1},
            status=409,
            only_activity=activity.id,
            fragment=_is_htmx(),
        )
    except ProgressError as exc:
        return _render_detail(
            project,
            errors={activity.id: str(exc)},
            deltas={activity.id: delta},
            status=400,
            only_activity=activity.id,
            fragment=_is_htmx(),
        )
    db.session.commit()
    message = f"+{delta} em {activity.name} · {activity.units_done} de {project.quantity}"
    if _is_htmx():
        project = get_or_404(Project, project.id)
        return _render_detail(project, only_activity=activity.id, toast=message, fragment=True)
    flash(message, "sucesso")
    return redirect(url_for("app.project_detail", project_id=project.id, _anchor=f"atividade-{activity.id}"), 303)


@bp.get("/atividades/<uuid:activity_id>/previa")
@tenant_required(ROLE_OPERATOR)
def activity_preview(activity_id):
    """Texto do botão de registro (“+2 (→ 5 de 10)”) calculado no servidor, em fragmento HTMX.
    Só leitura; o navegador não decide nada (a gravação revalida tudo em register_progress)."""
    activity = get_or_404(Activity, activity_id)
    quantity = activity.stage.project.quantity
    faltam = max(0, quantity - activity.units_done)
    try:
        delta = int(request.args.get("delta", ""))
    except ValueError:
        return ""
    if delta < 1:
        return ""
    if delta > faltam:
        return f"+{delta} (faltam só {faltam})"
    return f"+{delta} (→ {activity.units_done + delta} de {quantity})"
