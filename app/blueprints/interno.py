"""Etapa C — painel interno da equipe (/interno).

Só para ``User.is_staff`` com MFA (``staff.is_staff``): qualquer outra pessoa, logada ou não,
recebe 404 (a rota não revela que existe). Painel só para ACOMPANHAR as requisições de
identidade visual: contato do cliente, estado e anotação. Não entra em dados de produção das
empresas. Cada mudança vai para ``platform_audit_logs``.
"""

from __future__ import annotations

import getpass
import os
from functools import wraps

import click
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask.cli import AppGroup
from flask_login import current_user
from wtforms import SelectField, TextAreaField
from wtforms.validators import DataRequired, Length

from app.forms import BaseForm, _strip
from app.models import VISUAL_STATUSES
from app.services import staff

bp = Blueprint("interno", __name__, url_prefix="/interno")


class VisualStatusForm(BaseForm):
    status = SelectField("Estado", choices=[(k, staff.STATUS_LABELS[k]) for k in VISUAL_STATUSES], validators=[DataRequired()])
    notes = TextAreaField("Anotação interna", filters=[_strip], validators=[Length(max=staff.MAX_NOTES)])


def staff_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not staff.is_staff(current_user):
            abort(404)
        return view(*args, **kwargs)

    return wrapper


@bp.after_request
def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("")
@staff_required
def index():
    status = request.args.get("estado")
    return render_template(
        "interno/index.html",
        requests=staff.list_requests(status),
        status=status if status in VISUAL_STATUSES else None,
        labels=staff.STATUS_LABELS,
    )


@bp.get("/requisicoes/<uuid:request_id>")
@staff_required
def detail(request_id):
    item = staff.get_request(request_id)
    if item is None:
        abort(404)
    form = VisualStatusForm(formdata=None, data={"status": item.status, "notes": item.notes or ""})
    return render_template("interno/detail.html", item=item, form=form, labels=staff.STATUS_LABELS)


@bp.post("/requisicoes/<uuid:request_id>/estado")
@staff_required
def change_status(request_id):
    item = staff.get_request(request_id)
    if item is None:
        abort(404)
    form = VisualStatusForm()
    if form.validate_on_submit():
        try:
            staff.set_status(item, form.status.data, form.notes.data, current_user)
        except staff.StaffError as exc:
            form.notes.errors.append(str(exc))
        else:
            flash("Requisição atualizada.", "success")
            return redirect(url_for("interno.detail", request_id=item.id), code=303)
    return render_template("interno/detail.html", item=item, form=form, labels=staff.STATUS_LABELS), 400


# ---------------------------------------------------------------- linha de comando

staff_cli = AppGroup("staff", help="Equipe da plataforma (painel /interno; auditado).")


def _operator(value: str | None) -> str:
    if value:
        return value
    try:
        return os.environ.get("OPERATOR") or getpass.getuser()
    except Exception:  # noqa: BLE001
        return "desconhecido"


@staff_cli.command("conceder")
@click.argument("email")
@click.option("--motivo", required=True)
@click.option("--autorizado-por", "authorized_by", default=None)
def staff_grant(email, motivo, authorized_by):
    try:
        user = staff.grant(email, motivo, _operator(authorized_by))
    except staff.StaffError as exc:
        raise click.ClickException(str(exc)) from None
    click.echo(f"{user.email} agora é da equipe (acessa /interno).")


@staff_cli.command("revogar")
@click.argument("email")
@click.option("--motivo", required=True)
@click.option("--autorizado-por", "authorized_by", default=None)
def staff_revoke(email, motivo, authorized_by):
    try:
        user = staff.revoke(email, motivo, _operator(authorized_by))
    except staff.StaffError as exc:
        raise click.ClickException(str(exc)) from None
    click.echo(f"{user.email} saiu da equipe; sessões abertas derrubadas.")


@staff_cli.command("listar")
def staff_list():
    users = staff.list_staff()
    if not users:
        click.echo("Ninguém na equipe.")
    for user in users:
        click.echo(f"{user.email}  mfa={'sim' if user.mfa_enabled else 'não'}")

