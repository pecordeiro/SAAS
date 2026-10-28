"""Edição de projeto (Fase 4): dados, renomear/reordenar/arquivar etapas e atividades,
duplicar, arquivar, comparar/aplicar versão do modelo, desfazer registro (D13) e restaurar o
projeto para uma data (R8).

Tudo supervisor+, POST com CSRF, recursos resolvidos por ``get_or_404`` (empresa da sessão;
arquivado = 404). Também registra, para o app inteiro, a resposta 402 de
``entitlements.EntitlementError`` e o aviso de modo leitura no layout.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import select

from app.extensions import db
from app.formatting import br_number
from app.forms import BaseForm
from app.forms_production import (
    ActivityEditForm,
    AssignForm,
    ConfirmForm,
    MoveForm,
    PositionForm,
    ProjectEditForm,
    RenameForm,
    RestoreForm,
)
from app.models import ROLE_SUPERVISOR, Activity, Project, ProgressEntry, Stage, User
from app.services import entitlements
from app.services import projects as svc
from app.services import restore as rsvc
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


def _edit_page(
    project: Project, form: ProjectEditForm, status: int = 200, error: str | None = None, conflict: dict | None = None
):
    stages = [(s, svc.active_activities(s)) for s in svc.active_stages(project)]
    return (
        render_template(
            "edicao/project_edit.html",
            project=project,
            form=form,
            stages=stages,
            error=error,
            conflict=conflict,
            members=svc.assignable_members(project.company_id),
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
    if _to_fill():
        flash(f"Projeto “{project.name}” apagado (arquivado). O histórico continua guardado.", "sucesso")
        return redirect(url_for("preencher.fill"), 303)
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


def _to_fill() -> bool:
    """R3: a ação veio de “Preencher etapas” (campo ``voltar=preencher``) e volta para lá."""
    return request.form.get("voltar") == "preencher"


def _back(project_id, stage_id=None):
    if _to_fill():
        # Volta ao mesmo modo de “Preencher etapas” (registrar ou configurar).
        modo = "configurar" if request.form.get("modo") == "configurar" else None
        return redirect(url_for("preencher.fill", projeto=project_id, etapa=stage_id, modo=modo), 303)
    return redirect(url_for("edicao.project_edit", project_id=project_id), 303)


def _fill_error(project_id, message: str, stage_id=None):
    """Erro/409 vindo de Preencher etapas: nada foi gravado; volta à tela com o aviso."""
    db.session.rollback()
    flash(message, "erro")
    return _back(project_id, stage_id)


def _conflict_page(project_id, obj_id, exc: svc.EditConflict, mine: dict, current_text: str):
    """409: nada foi gravado. A tela mostra o valor ATUAL e devolve o que a pessoa digitou,
    já com a versão atual — salvar de novo é a confirmação consciente de sobrescrever."""
    if _to_fill():
        return _fill_error(project_id, f"{exc} Agora: {current_text}. Confira e tente de novo.")
    db.session.rollback()
    project = get_or_404(Project, project_id)
    message = f"{exc} Agora: {current_text}. Confira e salve de novo para confirmar a sua versão."
    conflict = {"id": obj_id, "message": message, "mine": mine}
    return _edit_page(project, ProjectEditForm(obj=project), 409, conflict=conflict)


@bp.post("/etapas/<uuid:stage_id>/renomear")
@tenant_required(ROLE_SUPERVISOR)
def stage_rename(stage_id):
    stage = get_or_404(Stage, stage_id)
    form = RenameForm()
    if not form.validate():
        flash("Informe o nome da etapa.", "erro")
        return _back(stage.project_id)
    try:
        svc.rename_stage(stage, form.name.data, form.version.data, user_id=current_user.id)
    except svc.EditConflict as exc:
        return _conflict_page(
            stage.project_id, stage.id, exc, {"name": form.name.data}, f"“{exc.current['name']}”"
        )
    except svc.EditError as exc:
        db.session.rollback()
        flash(str(exc), "erro")
        return _back(stage.project_id)
    db.session.commit()
    flash("Etapa renomeada.", "sucesso")
    return _back(stage.project_id, stage.id)


@bp.post("/etapas/<uuid:stage_id>/mover")
@tenant_required(ROLE_SUPERVISOR)
def stage_move(stage_id):
    stage = get_or_404(Stage, stage_id)
    form = MoveForm()
    if not form.validate():
        abort(400)
    svc.move_stage(stage, -1 if form.direction.data == "up" else 1)
    db.session.commit()
    return _back(stage.project_id, stage.id)


@bp.post("/projetos/<uuid:project_id>/etapas/ordem")
@tenant_required(ROLE_SUPERVISOR)
def stages_reorder(project_id):
    """Etapa D (arrastar): recebe a ordem COMPLETA das etapas (campo ``order`` repetido).
    Id que não é etapa ativa deste projeto na empresa da sessão → 404; lista que não bate
    com as etapas atuais (alguém incluiu/arquivou) → 409 com a ordem atual na tela."""
    project = get_or_404(Project, project_id)
    if not BaseForm().validate():
        abort(400)
    ordered = request.form.getlist("order")
    if not ordered or len(ordered) > 500:
        abort(400)
    live = {str(s.id) for s in svc.active_stages(project)}
    for raw in ordered:
        if raw not in live:
            stage = get_or_404(Stage, raw)  # de outra empresa/arquivada/inexistente → 404
            if stage.project_id != project.id:
                abort(404)
    try:
        changed = svc.reorder_stages(project, ordered, current_user.id)
    except svc.OrderConflict as exc:
        if _to_fill():
            return _fill_error(project_id, str(exc))
        db.session.rollback()
        project = get_or_404(Project, project_id)
        return _edit_page(project, ProjectEditForm(obj=project), 409, error=str(exc))
    db.session.commit()
    if changed:
        flash("Ordem das etapas salva.", "sucesso")
    return _back(project.id)


@bp.post("/etapas/<uuid:stage_id>/arquivar")
@tenant_required(ROLE_SUPERVISOR)
def stage_archive(stage_id):
    stage = get_or_404(Stage, stage_id)
    svc.archive_stage(stage, current_user.id)
    db.session.commit()
    if _to_fill():
        flash(f"Etapa “{stage.name}” apagada. Para desfazer, use “Etapas apagadas” no fim da lista.", "sucesso")
        return _back(stage.project_id)
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
    try:
        svc.update_activity(activity, form.name.data, form.ideal_minutes.data, form.version.data, user_id=current_user.id)
    except svc.EditConflict as exc:
        cur = exc.current
        current_text = (
            f"“{cur['name']}”, {br_number(cur['ideal_minutes'], 2)} min, "
            f"{cur['units_done']} de {activity.stage.project.quantity} peças"
        )
        mine = {"name": form.name.data, "ideal_minutes": form.ideal_minutes.data}
        return _conflict_page(project_id, activity.id, exc, mine, current_text)
    except svc.EditError as exc:
        db.session.rollback()
        flash(str(exc), "erro")
        return _back(project_id)
    db.session.commit()
    flash("Atividade atualizada.", "sucesso")
    return _back(project_id)


@bp.post("/atividades/<uuid:activity_id>/responsavel")
@tenant_required(ROLE_SUPERVISOR)
def activity_assign(activity_id):
    """Etapa D: um responsável por atividade (supervisor+). Pessoa que não é membro ativo
    da empresa da sessão (outra empresa, desativada, inexistente, suporte) → 404."""
    activity = get_or_404(Activity, activity_id)
    form = AssignForm()
    if not form.validate():
        abort(400)
    raw = form.assignee_id.data or ""
    try:
        assignee_id = uuid.UUID(raw) if raw else None
    except ValueError:
        abort(404)
    project_id = activity.stage.project_id
    try:
        changed = svc.assign_activity(activity, assignee_id, current_user.id)
    except svc.AssignError:
        db.session.rollback()
        abort(404)
    db.session.commit()
    if changed:
        flash("Responsável definido." if assignee_id else "Atividade sem responsável.", "sucesso")
    return _back(project_id)


@bp.post("/atividades/<uuid:activity_id>/posicionar")
@tenant_required(ROLE_SUPERVISOR)
def activity_position(activity_id):
    """Etapa D: põe a atividade numa etapa (do MESMO projeto) e posição — arrastar ou o
    seletor “Mover para” (sem JS). Etapa de outra empresa/projeto → 404; versão velha → 409."""
    activity = get_or_404(Activity, activity_id)
    form = PositionForm()
    if not form.validate():
        abort(400)
    target = get_or_404(Stage, form.stage_id.data)
    project_id = activity.stage.project_id
    if target.project_id != project_id:
        abort(404)
    try:
        svc.move_activity_to(activity, target, form.position.data, form.version.data, current_user.id)
    except svc.EditConflict as exc:
        if _to_fill():
            return _fill_error(project_id, f"{exc} Confira onde ela está agora e mova de novo.", form.stage_id.data)
        db.session.rollback()
        project = get_or_404(Project, project_id)
        current = get_or_404(Activity, activity_id)
        message = (
            f"{exc} Agora ela está em “{current.stage.name}”. Confira a posição e mova de novo para confirmar."
        )
        conflict = {"id": current.id, "message": message, "mine": {"name": current.name, "ideal_minutes": current.ideal_minutes}}
        return _edit_page(project, ProjectEditForm(obj=project), 409, conflict=conflict)
    except svc.EditError:
        db.session.rollback()
        abort(404)
    db.session.commit()
    flash("Subatividade movida." if _to_fill() else "Atividade movida.", "sucesso")
    return _back(project_id, target.id)


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
    return _back(project_id, activity.stage_id)


@bp.post("/atividades/<uuid:activity_id>/arquivar")
@tenant_required(ROLE_SUPERVISOR)
def activity_archive(activity_id):
    activity = get_or_404(Activity, activity_id)
    project_id = activity.stage.project_id
    stage_id = activity.stage_id
    svc.archive_activity(activity, current_user.id)
    db.session.commit()
    if _to_fill():
        flash(f"Subatividade “{activity.name}” apagada. Para desfazer, use “Subatividades apagadas” abaixo da tabela.", "sucesso")
        return _back(project_id, stage_id)
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


# ---------------------------------------------------------------- restaurar (R8)


def _local_label(raw: str | None) -> str:
    """``AAAA-MM-DDTHH:MM`` → ``21/10/2026 às 10:30`` (só formatação)."""
    try:
        return datetime.strptime(raw or "", rsvc.INPUT_FORMAT).strftime("%d/%m/%Y às %H:%M")
    except ValueError:
        return (raw or "").replace("T", " ")


def _restore_page(project: Project, *, ate: str | None, status: int = 200, conflict: bool = False,
                  error: str | None = None):
    tz_name = g.company.timezone or rsvc.DEFAULT_TZ
    preview = None
    if ate and error is None:
        at = rsvc.parse_local(ate, tz_name)
        if at is None:
            error, status = "Data e hora inválidas. Escolha o dia e a hora no campo.", 400
        else:
            preview = rsvc.restore_preview(project, at)
    records = rsvc.restorations(project)
    actor_ids = {r.log.actor_user_id for r in records if r.log.actor_user_id}
    actors = (
        {u.id: u.name for u in db.session.execute(select(User).where(User.id.in_(actor_ids))).scalars()}
        if actor_ids else {}
    )
    return (
        render_template(
            "edicao/restore.html",
            project=project,
            ate=ate if preview else None,
            ate_label=_local_label(ate),
            now_local=rsvc.format_local(datetime.now(timezone.utc), tz_name),
            tz_label=tz_name,
            preview=preview,
            records=records,
            record_labels={r.restore_id: _local_label(r.target) for r in records},
            actors=actors,
            form=RestoreForm(formdata=None),
            confirm_form=ConfirmForm(formdata=None),
            conflict=conflict,
            error=error,
        ),
        status,
    )


@bp.get("/projetos/<uuid:project_id>/restaurar")
@tenant_required(ROLE_SUPERVISOR)
def project_restore(project_id):
    """Prévia: ``?ate=AAAA-MM-DDTHH:MM`` (fuso da empresa). Só leitura."""
    project = get_or_404(Project, project_id)
    return _restore_page(project, ate=(request.args.get("ate") or "").strip()[:16] or None)


@bp.post("/projetos/<uuid:project_id>/restaurar")
@tenant_required(ROLE_SUPERVISOR)
def project_restore_apply(project_id):
    """Aplica a restauração mostrada na prévia (token): mudou no meio → 409 com a prévia nova."""
    project = get_or_404(Project, project_id)
    form = RestoreForm()
    ate = (form.ate.data or "").strip()[:16]
    tz_name = g.company.timezone or rsvc.DEFAULT_TZ
    at = rsvc.parse_local(ate, tz_name)
    if not form.validate() or at is None:
        if at is None:
            return _restore_page(project, ate=None, status=400, error="Data e hora inválidas.")
        flash("Marque a confirmação para restaurar.", "erro")
        return redirect(url_for("edicao.project_restore", project_id=project.id, ate=ate), 303)
    try:
        result = rsvc.restore_apply(project, at, current_user.id, form.token.data, tz_name=tz_name)
    except rsvc.RestoreConflict:
        db.session.rollback()
        project = get_or_404(Project, project_id)
        return _restore_page(project, ate=ate, status=409, conflict=True)
    except rsvc.RestoreError as exc:
        db.session.rollback()
        flash(str(exc), "erro")
        return redirect(url_for("edicao.project_restore", project_id=project.id, ate=ate), 303)
    db.session.commit()
    flash(
        f"Projeto restaurado para {_local_label(ate)}: {len(result.entries)} "
        f"{'lançamento' if len(result.entries) == 1 else 'lançamentos'} no histórico.",
        "sucesso",
    )
    return redirect(url_for("edicao.project_restore", project_id=project.id), 303)


@bp.post("/projetos/<uuid:project_id>/restauracoes/<uuid:restore_id>/desfazer")
@tenant_required(ROLE_SUPERVISOR)
def project_restore_undo(project_id, restore_id):
    """Desfaz uma restauração inteira (lançamentos que invertem os dela). Outra empresa → 404."""
    project = get_or_404(Project, project_id)
    back = url_for("edicao.project_restore", project_id=project.id)
    form = ConfirmForm()
    try:
        if not form.validate():
            if not rsvc.restore_exists(project, restore_id):
                abort(404)
            flash("Marque a confirmação para desfazer a restauração.", "erro")
            return redirect(back, 303)
        rsvc.restore_undo(project, restore_id, current_user.id)
    except rsvc.RestoreNotFound:
        db.session.rollback()
        abort(404)
    except rsvc.RestoreError as exc:
        db.session.rollback()
        flash(str(exc), "erro")
        return redirect(back, 303)
    db.session.commit()
    flash("Restauração desfeita. Os lançamentos dela continuam no histórico.", "sucesso")
    return redirect(back, 303)
