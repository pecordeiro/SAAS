"""Telas da base (reestruturação R3–R5): Preencher etapas, Meta e equipe e Como funciona.

Preencher etapas (plano §4.3): lista das etapas à esquerda e a tabela da etapa à direita, com
células amarelas que salvam AO SAIR DO CAMPO (static/js/preencher.js manda um POST pequeno por
célula via HTMX; a resposta traz, fora de banda, os números recalculados pelo servidor). Sem JS,
cada linha tem o botão “Salvar”. Modo simples (R4): a etapa recebe o % direto.

Regras (ADR-0009): o projeto vem sempre da empresa da sessão (``get_or_404``; outra empresa →
404); operador só lança peças (ou o % no modo simples) e só para cima; supervisor+ edita a
estrutura e corrige para baixo. Esconder a célula nunca substitui a recusa da rota (403).
Contas só em calc.py.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.formatting import br_number
from app.forms import BaseForm
from app.models import PROGRESS_DETAILED, PROGRESS_SIMPLE, ROLE_OPERATOR, ROLE_SUPERVISOR, Activity, Project, Stage
from app.services import calc, dashboard, modules
from app.services import projects as svc
from app.services.holidays import holidays_for
from app.tenancy import get_or_404, tenant_required

bp = Blueprint("preencher", __name__, url_prefix="/app")

FIELD_LABELS = {
    "name": "Nome",
    "ideal_minutes": "Tempo ideal",
    "units_done": "Peças concluídas",
    "percent": "% concluído",
}


# ---------------------------------------------------------------- utilidades


@bp.app_template_filter("minutos")
def minutes_text(value) -> str:
    """Minutos como a pessoa digita: “15”, “7,5”, “12,25” (sem zeros sobrando)."""
    if value is None:
        return ""
    text = br_number(value, 2)
    return text.rstrip("0").rstrip(",") if "," in text else text


def _is_htmx() -> bool:
    return request.headers.get("HX-Request") == "true" and not request.headers.get("HX-Boosted")


def _tz() -> ZoneInfo:
    try:
        return ZoneInfo(g.company.timezone)
    except Exception:  # noqa: BLE001 - fuso inválido cai no padrão
        return ZoneInfo("America/Sao_Paulo")


def _today() -> date:
    return datetime.now(_tz()).date()


def _now_local() -> datetime:
    return datetime.now(_tz())


def _can_edit() -> bool:
    return g.membership.has_role(ROLE_SUPERVISOR)


def _modo() -> str:
    """Modo da tela “Preencher etapas”: ``registrar`` (padrão: lançar peças) ou ``configurar``
    (nomes, tempos, pesos, ordem, incluir e apagar). Configurar é só de supervisor+; o modo só
    muda o que aparece (as rotas continuam checando o papel)."""
    return "configurar" if _can_edit() and request.values.get("modo") == "configurar" else "registrar"


def _version(raw) -> int | None:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value >= 1 else None


def _csrf_ok() -> None:
    if not BaseForm().validate():
        abort(400)


def _current_project() -> Project | None:
    """Projeto das telas: o da URL (?projeto=, SEMPRE na empresa da sessão — outra → 404) ou,
    sem ele, o ativo mais recente."""
    raw = request.args.get("projeto", "")
    if raw:
        try:
            return get_or_404(Project, uuid.UUID(raw))
        except ValueError:
            abort(404)
    active = svc.list_projects("ativos")
    if active:
        return active[0]
    every = svc.list_projects("todos")
    return every[0] if every else None


def _no_project_redirect():
    flash("Crie um projeto para começar." if _can_edit() else "Ainda não há projetos.", "info")
    return redirect(url_for("app.project_new" if _can_edit() else "app.projects"), 303)


def _project_choices(project: Project) -> list[tuple]:
    choices = [(p.id, p.name) for p in svc.list_projects("ativos")]
    if project.id not in {pid for pid, _ in choices}:
        choices.insert(0, (project.id, project.name))
    return choices


def _who_when() -> str:
    return f"{current_user.name}, {_now_local():%H:%M}"


# ---------------------------------------------------------------- Preencher etapas: contexto


def _fill_ctx(project: Project, stage_id: uuid.UUID | None) -> dict:
    """Tudo o que a tela mostra, já calculado (calc.py via svc.summary)."""
    result = svc.summary(project)
    stages = svc.active_stages(project)
    fracao = calc.fracao_prazo_decorrida(
        project.start_date, project.due_date, _today(), holidays_for(g.company.id), g.company.workdays()
    )
    late = calc.etapas_atrasadas(result.etapas, fracao) if stages else ()
    waiting_on = modules.is_enabled(g.company, modules.AGUARDANDO_PECA)  # R6: módulo opcional
    items = []
    for n, (stage, sr) in enumerate(zip(stages, result.etapas), start=1):
        visual = calc.status_visual(sr.status, waiting_on and stage.waiting_part, late[n - 1] if late else False)
        items.append(
            {
                "stage": stage,
                "r": sr,
                "n": n,
                "label": dashboard.rotulo_etapa(n, stage.name),
                "visual": visual,
                "visual_label": dashboard.NOMES_VISUAIS[visual],
                "units_ratio": calc.razao(sr.unidades, sr.previstas),
            }
        )
    selected = next((i for i in items if i["stage"].id == stage_id), items[0] if items else None)
    rows = []
    archived_acts = []
    if selected is not None:
        stage = selected["stage"]
        rows = list(zip(svc.active_activities(stage), selected["r"].atividades))
        archived_acts = svc.archived_activities(stage)
    simple = svc.is_simple(project)
    return dict(
        project=project,
        result=result,
        items=items,
        sel=selected,
        rows=rows,
        simple=simple,
        simple_activity=rows[0][0] if simple and rows else None,
        simple_result=rows[0][1] if simple and rows else None,
        last=svc.last_entries(project),
        archived_stages=svc.archived_stages(project),
        archived_activities=archived_acts,
        can_edit=_can_edit(),
        project_choices=_project_choices(project),
        quantity=project.quantity,
        modo=_modo(),
    )


def _fill_url(project_id, stage_id=None, anchor=None) -> str:
    modo = "configurar" if _modo() == "configurar" else None
    return url_for("preencher.fill", projeto=project_id, etapa=stage_id, modo=modo, _anchor=anchor)


def _respond(project: Project, stage: Stage | None, *, message: str, error: bool = False, status: int = 200,
             focus: str | None = None, full_panel: bool = False, activity: Activity | None = None):
    """HTMX: só os pedaços que mudam (fora de banda). Sem JS: volta à tela (flash)."""
    if _is_htmx():
        db.session.expire_all()
        project = get_or_404(Project, project.id)
        ctx = _fill_ctx(project, stage.id if stage else None)
        ctx.update(message=message, error=error, full_panel=full_panel, version_for=activity, oob=True)
        return render_template("preencher/_oob.html", **ctx), status
    if status >= 400:
        db.session.rollback()
        flash(message, "erro")
    else:
        flash(message, "sucesso")
    return redirect(_fill_url(project.id, stage.id if stage else None, focus), 303)


# ---------------------------------------------------------------- Preencher etapas: telas


@bp.get("/preencher")
@tenant_required(ROLE_OPERATOR)
def fill():
    """Tela “Preencher etapas” (R3). ``?projeto=`` (empresa da sessão) e ``?etapa=``."""
    project = _current_project()
    if project is None:
        return _no_project_redirect()
    raw = request.args.get("etapa", "")
    try:
        stage_id = uuid.UUID(raw) if raw else None
    except ValueError:
        stage_id = None
    ctx = _fill_ctx(project, stage_id)
    ctx.update(message=None, error=False, oob=False, full_panel=False, version_for=None)
    return render_template("preencher/fill.html", **ctx)


@bp.post("/preencher/atividades/<uuid:activity_id>")
@tenant_required(ROLE_OPERATOR)
def activity_cells(activity_id):
    """Células de UMA subatividade (modo detalhado). Com ``campo`` (JS), só aquele campo;
    sem ele (botão Salvar, sem JS), todos os que mudaram. ``version`` = a que a tela leu."""
    _csrf_ok()
    activity = get_or_404(Activity, activity_id)
    stage, project = activity.stage, activity.stage.project
    if svc.is_simple(project):
        abort(404)
    field = request.form.get("campo") or None
    if field is not None and field not in ("name", "ideal_minutes", "units_done"):
        abort(400)
    fields = [field] if field else [f for f in ("name", "ideal_minutes", "units_done") if f in request.form]
    version = _version(request.form.get("version"))
    changes: dict = {}
    try:
        if "name" in fields and request.form.get("name", "").strip() != activity.name:
            changes["name"] = svc._clean_name(request.form.get("name"), "subatividade")
        if "ideal_minutes" in fields:
            minutes = svc.parse_minutes(request.form.get("ideal_minutes"))
            if minutes != activity.ideal_minutes:
                changes["ideal_minutes"] = minutes
        if "units_done" in fields:
            pieces = svc.parse_pieces(request.form.get("units_done"), project.quantity)
            if pieces != activity.units_done:
                changes["units_done"] = pieces
    except (svc.EditError, svc.ProgressError) as exc:
        return _respond(project, stage, message=str(exc), error=True, status=400, activity=activity)
    if ("name" in changes or "ideal_minutes" in changes) and not _can_edit():
        abort(403)  # operador só lança peças
    if not changes:
        return _respond(project, stage, message="Nada mudou.", activity=activity)
    try:
        if "name" in changes or "ideal_minutes" in changes:
            svc.update_activity(
                activity, changes.get("name", activity.name), changes.get("ideal_minutes", activity.ideal_minutes),
                version, user_id=current_user.id,
            )
            version = activity.version
        if "units_done" in changes:
            svc.set_units_done(activity, changes["units_done"], version, current_user.id, can_decrease=_can_edit())
    except (svc.EditConflict, svc.ConflictError):
        db.session.rollback()
        current = get_or_404(Activity, activity_id)
        message = (
            f"Outra pessoa mudou “{current.name}” enquanto você editava: agora "
            f"{br_number(current.ideal_minutes, 2)} min e {current.units_done} de {project.quantity} peças. "
            "O seu valor ficou no campo: saia dele de novo para salvar por cima."
        )
        return _respond(current.stage.project, current.stage, message=message, error=True, status=409, activity=current)
    except (svc.EditError, svc.ProgressError) as exc:
        db.session.rollback()
        return _respond(project, stage, message=str(exc), error=True, status=400, activity=activity)
    db.session.commit()
    what = ", ".join(FIELD_LABELS[f].lower() for f in changes)
    return _respond(project, stage, message=f"Salvo ({what} de “{activity.name}”) · {_who_when()}", activity=activity)


@bp.post("/preencher/etapas/<uuid:stage_id>/atividades")
@tenant_required(ROLE_SUPERVISOR)
def activity_new(stage_id):
    """Linha vazia no fim da tabela: nova subatividade (nome, tempo e peças opcionais)."""
    _csrf_ok()
    stage = get_or_404(Stage, stage_id)
    project = stage.project
    if svc.is_simple(project):
        return _respond(project, stage, message="No modo simples a etapa não tem subatividades. Troque o modo em Meta e equipe.",
                        error=True, status=400)
    try:
        name = svc._clean_name(request.form.get("name"), "subatividade")
        raw_minutes = (request.form.get("ideal_minutes") or "").strip()
        minutes = svc.parse_minutes(raw_minutes) if raw_minutes else Decimal("0")
        raw_pieces = (request.form.get("units_done") or "").strip()
        pieces = svc.parse_pieces(raw_pieces, project.quantity) if raw_pieces else 0
    except (svc.EditError, svc.ProgressError) as exc:
        return _respond(project, stage, message=str(exc), error=True, status=400, full_panel=True)
    activity = svc.add_activity(stage, svc.NewActivity(name=name, ideal_minutes=minutes))
    if pieces:
        svc.register_progress(activity, pieces, activity.version, current_user.id)
    db.session.commit()
    return _respond(project, stage, message=f"Subatividade “{name}” incluída · {_who_when()}", full_panel=True,
                    focus="nova-nome")


@bp.post("/preencher/etapas/<uuid:stage_id>")
@tenant_required(ROLE_OPERATOR)
def stage_cells(stage_id):
    """Células da etapa: nome (supervisor+, com ``version`` da etapa) e, no modo simples, o %
    (operador também) e o tempo da etapa (supervisor+), com ``activity_version``."""
    _csrf_ok()
    stage = get_or_404(Stage, stage_id)
    project = stage.project
    simple = svc.is_simple(project)
    field = request.form.get("campo") or None
    allowed = ("name", "percent", "ideal_minutes") if simple else ("name",)
    if field is not None and field not in allowed:
        abort(400)
    fields = [field] if field else [f for f in allowed if f in request.form]
    activity = svc.active_activities(stage)[0] if simple and svc.active_activities(stage) else None
    changes: dict = {}
    try:
        if "name" in fields and (request.form.get("name") or "").strip() != stage.name:
            changes["name"] = svc._clean_name(request.form.get("name"), "etapa")
        if "ideal_minutes" in fields:
            minutes = svc.parse_minutes(request.form.get("ideal_minutes"))
            if activity is None or minutes != activity.ideal_minutes:
                changes["ideal_minutes"] = minutes
        if "percent" in fields:
            pct = svc.parse_percent(request.form.get("percent"))
            target = calc.pecas_de_percentual(float(pct) / 100, project.quantity)
            if activity is None or target != activity.units_done:
                changes["percent"] = pct
    except (svc.EditError, svc.ProgressError) as exc:
        return _respond(project, stage, message=str(exc), error=True, status=400)
    if ("name" in changes or "ideal_minutes" in changes) and not _can_edit():
        abort(403)
    if not changes:
        return _respond(project, stage, message="Nada mudou.")
    try:
        if "name" in changes:
            svc.rename_stage(stage, changes["name"], _version(request.form.get("version")), current_user.id)
        act_version = _version(request.form.get("activity_version"))
        if "ideal_minutes" in changes:
            activity = svc.simple_activity(stage)
            svc.update_activity(activity, activity.name, changes["ideal_minutes"], act_version, user_id=current_user.id)
            act_version = activity.version
        if "percent" in changes:
            svc.set_stage_percent(stage, changes["percent"], act_version, current_user.id, can_decrease=_can_edit())
    except (svc.EditConflict, svc.ConflictError):
        db.session.rollback()
        current = get_or_404(Stage, stage_id)
        message = (
            f"Outra pessoa mudou a etapa “{current.name}” enquanto você editava. Os números ao lado já são os de agora; "
            "o seu valor ficou no campo: saia dele de novo para salvar por cima."
        )
        return _respond(current.project, current, message=message, error=True, status=409)
    except (svc.EditError, svc.ProgressError) as exc:
        db.session.rollback()
        return _respond(project, stage, message=str(exc), error=True, status=400)
    db.session.commit()
    if "percent" in changes:
        db.session.refresh(stage)
        done = svc.active_activities(stage)[0].units_done
        what = f"{changes['percent']:.1f}".replace(".", ",").replace(",0", "") + "%"
        message = f"Salvo: {stage.name} em {what} ({done} de {project.quantity} unidades) · {_who_when()}"
    else:
        message = f"Salvo ({', '.join(FIELD_LABELS[f].lower() for f in changes)} da etapa) · {_who_when()}"
    return _respond(project, stage, message=message)


@bp.post("/preencher/projetos/<uuid:project_id>/etapas")
@tenant_required(ROLE_SUPERVISOR)
def stage_new(project_id):
    _csrf_ok()
    project = get_or_404(Project, project_id)
    try:
        name = svc._clean_name(request.form.get("name"), "etapa")
    except svc.EditError as exc:
        flash(str(exc), "erro")
        return redirect(_fill_url(project.id), 303)
    stage = svc.add_stage(project, name, [])
    db.session.commit()
    flash(f"Etapa “{name}” incluída.", "sucesso")
    return redirect(_fill_url(project.id, stage.id, "nome-etapa"), 303)


QUICK_PROJECT_STAGES = 5  # painel do dono: projeto novo nasce com 5 etapas
QUICK_PROJECT_QUANTITY = 10  # meta inicial (ajustável em Meta e equipe)


@bp.post("/preencher/projetos/novo")
@tenant_required(ROLE_SUPERVISOR)
def project_quick_new():
    """“+ Novo projeto” do topo das telas (painel do dono): só o nome; nasce no modo simples
    com 5 etapas (“Etapa 1” … “Etapa 5”) e meta 10. Limite do plano conferido em create_project."""
    _csrf_ok()
    name = " ".join((request.form.get("name") or "").split())
    if not name or len(name) > 160:
        flash("Digite um nome para o projeto (até 160 caracteres).", "erro")
        return redirect(request.referrer or url_for("preencher.fill"), 303)
    if any(p.name.casefold() == name.casefold() for p in svc.list_projects("todos")):
        flash("Já existe um projeto com esse nome.", "erro")
        return redirect(url_for("preencher.fill"), 303)
    project = svc.create_project(
        g.company, name=name, quantity=QUICK_PROJECT_QUANTITY, start_date=_today(), due_date=None, people=1,
        hours_per_day=Decimal("8"), stages=[svc.NewStage(name=f"Etapa {i}") for i in range(1, QUICK_PROJECT_STAGES + 1)],
        progress_mode=PROGRESS_SIMPLE, source="quick",
    )
    db.session.commit()
    flash(f"Projeto “{name}” criado com {QUICK_PROJECT_STAGES} etapas. Dê nome a elas e ajuste a meta em Meta e equipe.", "sucesso")
    return redirect(_fill_url(project.id, anchor="nome-etapa"), 303)


@bp.post("/preencher/etapas/<uuid:stage_id>/desfazer-exclusao")
@tenant_required(ROLE_SUPERVISOR)
def stage_unarchive(stage_id):
    """Desfaz “Excluir etapa” (a exclusão é um arquivamento; nada se perde)."""
    _csrf_ok()
    stage = get_or_404(Stage, stage_id, include_archived=True)
    if stage.project.archived_at is not None:
        abort(404)
    try:
        svc.unarchive_stage(stage, current_user.id)
    except svc.EditError as exc:
        db.session.rollback()
        flash(str(exc), "erro")
        return redirect(_fill_url(stage.project_id), 303)
    db.session.commit()
    flash(f"Etapa “{stage.name}” de volta.", "sucesso")
    return redirect(_fill_url(stage.project_id, stage.id), 303)


@bp.post("/preencher/atividades/<uuid:activity_id>/desfazer-exclusao")
@tenant_required(ROLE_SUPERVISOR)
def activity_unarchive(activity_id):
    _csrf_ok()
    activity = get_or_404(Activity, activity_id, include_archived=True)
    stage = activity.stage
    if stage.project.archived_at is not None:
        abort(404)
    try:
        svc.unarchive_activity(activity, current_user.id)
    except svc.EditError as exc:
        db.session.rollback()
        flash(str(exc), "erro")
        return redirect(_fill_url(stage.project_id, stage.id), 303)
    db.session.commit()
    flash(f"Subatividade “{activity.name}” de volta.", "sucesso")
    return redirect(_fill_url(stage.project_id, stage.id), 303)


# ---------------------------------------------------------------- Meta e equipe (R5)


def _team_ctx(project: Project) -> dict:
    # Mesmas contas de prazo do painel (término previsto, folga/atraso e dias úteis até o prazo).
    from app.blueprints.app import _deadline, _project_status

    result = svc.summary(project)
    team = calc.resumo_equipe(result, project.people, float(project.hours_per_day))
    forecast = svc.forecast_end(project, result, g.company, _today())
    status = _project_status(project, result)
    prazo = dashboard.situacao_prazo(_deadline(project, result, status), status == calc.STATUS_CONCLUIDA, project.due_date)
    return dict(
        project=project,
        result=result,
        team=team,
        forecast=forecast,
        prazo=prazo,
        can_edit=_can_edit(),
        project_choices=_project_choices(project),
        simple=svc.is_simple(project),
        modes=((PROGRESS_SIMPLE, "Simples", "Você lança o % de cada etapa."),
               (PROGRESS_DETAILED, "Detalhado", "Subatividades com tempo ideal e peças, igual à planilha.")),
    )


@bp.get("/meta-e-equipe")
@tenant_required(ROLE_OPERATOR)
def goal_team():
    """Tela “Meta e equipe” (R5): meta, pessoas, horas por dia, prazo e modo; dias úteis e
    “E se mudar o tamanho da equipe?” (aba Equipe). Operador só vê."""
    project = _current_project()
    if project is None:
        return _no_project_redirect()
    return render_template("preencher/goal_team.html", **_team_ctx(project), message=None, error=False, oob=False)


def _parse_team_field(name: str, raw: str | None):
    raw = (raw or "").strip()
    if name == "name":
        raw = " ".join(raw.split())
        if not raw or len(raw) > 160:
            raise svc.EditError("Informe o nome do projeto (até 160 caracteres).")
        return raw
    if name == "quantity":
        if not raw.isdigit() or not 1 <= int(raw) <= 100000:
            raise svc.EditError("A meta é um número inteiro de 1 a 100000.")
        return int(raw)
    if name == "people":
        if not raw.isdigit() or not 1 <= int(raw) <= 1000:
            raise svc.EditError("Pessoas: um número inteiro de 1 a 1000.")
        return int(raw)
    if name == "hours_per_day":
        try:
            value = Decimal(raw.replace(",", "."))
        except InvalidOperation:
            value = None
        if value is None or not value.is_finite() or not Decimal("0.5") <= value <= 24 or value != value.quantize(Decimal("0.01")):
            raise svc.EditError("Horas por dia: de 0,5 a 24 (até 2 casas, ex.: 7,5).")
        return value
    if name == "due_date":
        if not raw:
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError:
            raise svc.EditError("Prazo: use uma data válida (dd/mm/aaaa).") from None
    raise svc.EditError("Campo desconhecido.")


TEAM_FIELDS = ("name", "quantity", "people", "hours_per_day", "due_date")
TEAM_LABELS = {"name": "nome do projeto", "quantity": "meta", "people": "pessoas", "hours_per_day": "horas por dia", "due_date": "prazo"}


@bp.post("/meta-e-equipe/<uuid:project_id>")
@tenant_required(ROLE_SUPERVISOR)
def goal_team_save(project_id):
    """Salva meta, pessoas, horas por dia e prazo (um campo com ``campo``, ou todos sem JS)."""
    _csrf_ok()
    project = get_or_404(Project, project_id)
    field = request.form.get("campo") or None
    if field is not None and field not in TEAM_FIELDS:
        abort(400)
    fields = [field] if field else [f for f in TEAM_FIELDS if f in request.form]
    values = dict(
        name=project.name,
        quantity=project.quantity, people=project.people, hours_per_day=project.hours_per_day,
        due_date=project.due_date,
    )
    changed = []
    try:
        for name in fields:
            value = _parse_team_field(name, request.form.get(name))
            if value != values[name]:
                values[name] = value
                changed.append(name)
        if changed:
            svc.update_project(
                project, product=project.product, start_date=project.start_date, user_id=current_user.id, **values,
            )
    except svc.EditError as exc:
        db.session.rollback()
        return _team_respond(project_id, str(exc), error=True, status=400)
    if not changed:
        return _team_respond(project_id, "Nada mudou.")
    db.session.commit()
    message = f"Salvo ({', '.join(TEAM_LABELS[c] for c in changed)}) · {_who_when()}"
    if "quantity" in changed and svc.is_simple(project):
        message += ". No modo simples as unidades lançadas ficam; o % das etapas muda com a meta."
    return _team_respond(project_id, message)


def _team_respond(project_id, message: str, *, error: bool = False, status: int = 200):
    project = get_or_404(Project, project_id)
    if _is_htmx():
        db.session.expire_all()
        project = get_or_404(Project, project_id)
        return render_template("preencher/_equipe_oob.html", **_team_ctx(project), message=message, error=error, oob=True), status
    if status >= 400:
        return render_template("preencher/goal_team.html", **_team_ctx(project), message=message, error=True, oob=False), status
    flash(message, "sucesso")
    return redirect(url_for("preencher.goal_team", projeto=project_id), 303)


@bp.post("/meta-e-equipe/<uuid:project_id>/modo")
@tenant_required(ROLE_SUPERVISOR)
def mode_save(project_id):
    """Troca o modo de progresso (R4). Detalhado → simples só com ≤ 1 subatividade por etapa."""
    _csrf_ok()
    project = get_or_404(Project, project_id)
    mode = request.form.get("progress_mode", "")
    try:
        changed = svc.set_progress_mode(project, mode, current_user.id)
    except svc.EditError as exc:
        db.session.rollback()
        project = get_or_404(Project, project_id)
        return render_template("preencher/goal_team.html", **_team_ctx(project), message=str(exc), error=True, oob=False), 400
    db.session.commit()
    if changed:
        flash("Modo simples ligado: lance o % de cada etapa." if mode == PROGRESS_SIMPLE
              else "Modo detalhado ligado: lance as peças de cada subatividade.", "sucesso")
    return redirect(url_for("preencher.goal_team", projeto=project_id), 303)


# ---------------------------------------------------------------- Como funciona (R5)


@bp.get("/como-funciona")
@tenant_required(ROLE_OPERATOR)
def how():
    """Tela “Como funciona” (R5): cada conta, como é feita e um exemplo com os números atuais
    do projeto (texto montado em calc.como_funciona)."""
    project = _current_project()
    if project is None:
        return _no_project_redirect()
    stages = svc.active_stages(project)
    names = [s.name for s in stages]
    acts = [[a.name for a in svc.active_activities(s)] for s in stages]
    rows = calc.como_funciona(
        svc.to_calc(project), names, acts, project.quantity, project.people, float(project.hours_per_day),
        simples=svc.is_simple(project),
    )
    return render_template(
        "preencher/how.html", project=project, rows=rows, simple=svc.is_simple(project),
        project_choices=_project_choices(project),
    )
