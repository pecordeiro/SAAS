"""Modelos de etapas (/app/modelos) — supervisor+ (telas.md §11)."""

from __future__ import annotations

import re

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.forms_production import MAX_TEMPLATE_STAGES, ConfirmForm, TemplateForm
from app.models import ROLE_SUPERVISOR, Template
from app.services import templates as tsvc
from app.services.exporter import br_decimal
from app.tenancy import get_or_404, tenant_required

bp = Blueprint("modelos", __name__, url_prefix="/app/modelos")


def _slot_data(template: Template | None) -> list[dict]:
    slots = []
    if template is not None and template.current_version is not None:
        for stage in template.current_version.stages:
            slots.append(
                {
                    "name": stage.name,
                    "activities": "\n".join(f"{a.name}; {br_decimal(a.ideal_minutes)}" for a in stage.activities),
                    "checklist": "\n".join(i.text for i in stage.checklist_items),
                    "checklist_required": stage.checklist_required,
                }
            )
    return slots + [{"name": "", "activities": "", "checklist": "", "checklist_required": False}] * 2


@bp.get("")
@tenant_required(ROLE_SUPERVISOR)
def index():
    items = [
        (t, t.current_version, tsvc.minutes_per_unit(t.current_version), tsvc.projects_using(t))
        for t in tsvc.list_templates()
    ]
    return render_template("modelos/index.html", items=items)


@bp.route("/novo", methods=["GET", "POST"])
@tenant_required(ROLE_SUPERVISOR)
def new():
    form = TemplateForm()
    if not form.is_submitted():
        form = TemplateForm(data={"stages": _slot_data(None)})
    if form.validate_on_submit():
        try:
            template = tsvc.create_template(
                g.company, form.name.data, form.new_stages(), created_by_user_id=current_user.id,
                description=form.description.data,
            )
        except tsvc.TemplateError as exc:
            form.name.errors.append(str(exc))
        else:
            db.session.commit()
            flash("Modelo criado (versão 1).", "sucesso")
            return redirect(url_for("modelos.edit", template_id=template.id), 303)
    status = 400 if form.is_submitted() else 200
    return render_template("modelos/edit.html", form=form, template=None, using=0), status


@bp.route("/<uuid:template_id>", methods=["GET", "POST"])
@tenant_required(ROLE_SUPERVISOR)
def edit(template_id):
    template = get_or_404(Template, template_id)
    probe = TemplateForm()
    if probe.is_submitted():
        form = probe
    else:
        form = TemplateForm(data={"name": template.name, "description": template.description or "", "stages": _slot_data(template)})
    if form.validate_on_submit():
        try:
            version = tsvc.update_template(
                template, name=form.name.data, description=form.description.data, stages=form.new_stages(),
                user_id=current_user.id,
            )
        except tsvc.TemplateError as exc:
            db.session.rollback()
            form.name.errors.append(str(exc))
        else:
            db.session.commit()
            if version is None:
                flash("Modelo salvo. As etapas não mudaram, então a versão continua a mesma.", "sucesso")
            else:
                flash(f"Versão {version.number} criada. Projetos existentes não mudam.", "sucesso")
            return redirect(url_for("modelos.edit", template_id=template.id), 303)
    status = 400 if form.is_submitted() else 200
    return (
        render_template(
            "modelos/edit.html", form=form, template=template, using=tsvc.projects_using(template),
            archive_form=ConfirmForm(formdata=None),
        ),
        status,
    )


@bp.get("/<uuid:template_id>/versoes")
@tenant_required(ROLE_SUPERVISOR)
def versions(template_id):
    template = get_or_404(Template, template_id)
    items = [(v, tsvc.minutes_per_unit(v)) for v in reversed(template.versions)]
    return render_template("modelos/versions.html", template=template, items=items)


@bp.post("/<uuid:template_id>/arquivar")
@tenant_required(ROLE_SUPERVISOR)
def archive(template_id):
    template = get_or_404(Template, template_id)
    tsvc.archive_template(template, current_user.id)
    db.session.commit()
    flash("Modelo arquivado. Os projetos criados dele continuam iguais.", "sucesso")
    return redirect(url_for("modelos.index"), 303)


# ---------------------------------------------------------------- linhas do editor (HTMX + sem JS)

MAX_ROW_ACTION_LEN = 20


def _slots_from_request() -> list[dict]:
    """Etapas como chegaram no formulário (nome + atividades), na ordem dos índices."""
    indexes = sorted(
        {int(m.group(1)) for key in request.form for m in [re.fullmatch(r"stages-(\d+)-name", key)] if m}
    )
    return [
        {
            "name": request.form.get(f"stages-{i}-name", ""),
            "activities": request.form.get(f"stages-{i}-activities", ""),
            "checklist": request.form.get(f"stages-{i}-checklist", ""),
            "checklist_required": bool(request.form.get(f"stages-{i}-checklist_required")),
        }
        for i in indexes
    ]


def _apply_row_action(slots: list[dict], action: str) -> list[dict]:
    """add | remove-N | up-N | down-N sobre a lista de etapas (sem validar nem gravar nada)."""
    kind, _, raw = action[:MAX_ROW_ACTION_LEN].partition("-")
    if kind == "add":
        if len(slots) < MAX_TEMPLATE_STAGES:
            slots.append({"name": "", "activities": "", "checklist": "", "checklist_required": False})
        return slots
    try:
        index = int(raw)
    except ValueError:
        return slots
    if not 0 <= index < len(slots):
        return slots
    if kind == "remove":
        slots.pop(index)
    elif kind in {"up", "down"}:
        other = index - 1 if kind == "up" else index + 1
        if 0 <= other < len(slots):
            slots[index], slots[other] = slots[other], slots[index]
    return slots


def _rows_response(template: Template | None):
    slots = _apply_row_action(_slots_from_request(), request.form.get("acao", ""))
    if not slots:
        slots = [{"name": "", "activities": "", "checklist": "", "checklist_required": False}]
    form = TemplateForm(
        formdata=None,
        data={"name": request.form.get("name", ""), "description": request.form.get("description", ""), "stages": slots},
    )
    htmx = request.headers.get("HX-Request") == "true" and not request.headers.get("HX-Boosted")
    ctx = dict(form=form, template=template, using=tsvc.projects_using(template) if template else 0)
    if htmx:
        return render_template("modelos/_stages.html", **ctx)
    if template is not None:
        ctx["archive_form"] = ConfirmForm(formdata=None)
    return render_template("modelos/edit.html", **ctx)


@bp.post("/linhas")
@tenant_required(ROLE_SUPERVISOR)
def rows_new():
    """Adicionar/remover/mover etapas no editor de um modelo novo (nada é gravado)."""
    return _rows_response(None)


@bp.post("/<uuid:template_id>/linhas")
@tenant_required(ROLE_SUPERVISOR)
def rows(template_id):
    """Idem para um modelo existente (o id é resolvido na empresa da sessão)."""
    return _rows_response(get_or_404(Template, template_id))
