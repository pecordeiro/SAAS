"""Etapa C — painel interno da equipe (/interno).

Só para ``User.is_staff`` com MFA (``staff.is_staff``): qualquer outra pessoa, logada ou não,
recebe 404 (a rota não revela que existe). Painel só para ACOMPANHAR as requisições de
identidade visual: contato do cliente, estado e anotação. Não entra em dados de produção das
empresas. Cada mudança vai para ``platform_audit_logs``.

ADR-0019: horários da ligação (``/interno/horarios``): a equipe cria e remove horários (dado da
plataforma), vê as reservas (empresa, contato da ligação, data) e decide os pedidos de mudança
(libera o horário ou mantém). O painel NÃO lê o conteúdo do briefing nem as imagens: isso é
leitura entre empresas e fica para outro ADR. POST com CSRF e limite por IP (``INTERNO_RATE_LIMIT``).
"""

from __future__ import annotations

import getpass
import os
from functools import wraps

import click
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask.cli import AppGroup
from flask_login import current_user
from wtforms import DateField, IntegerField, SelectField, TextAreaField, TimeField
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange

from app.extensions import db, limiter
from app.forms import BaseForm, _strip
from app.models import VISUAL_STATUSES, CallSlot
from app.services import agenda
from app.services import email as email_svc
from app.services import staff

bp = Blueprint("interno", __name__, url_prefix="/interno")


class VisualStatusForm(BaseForm):
    status = SelectField("Estado", choices=[(k, staff.STATUS_LABELS[k]) for k in VISUAL_STATUSES], validators=[DataRequired()])
    notes = TextAreaField("Anotação interna", filters=[_strip], validators=[Length(max=staff.MAX_NOTES)])


class SlotForm(BaseForm):
    day = DateField("Data", validators=[InputRequired(message="Informe a data.")])
    at = TimeField("Hora (Brasília)", validators=[InputRequired(message="Informe a hora.")])
    duration = IntegerField(
        "Duração (minutos)",
        default=30,
        validators=[InputRequired(), NumberRange(min=agenda.DURATION_MIN, max=agenda.DURATION_MAX)],
    )


def _interno_limit():
    return current_app.config.get("INTERNO_RATE_LIMIT", "60 per minute")


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
    return render_template(
        "interno/detail.html", item=item, form=form, labels=staff.STATUS_LABELS,
        slot=agenda.slot_for_request(item.id), local=agenda.local, change_labels=agenda.CHANGE_LABELS,
    )


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
    return render_template(
        "interno/detail.html", item=item, form=form, labels=staff.STATUS_LABELS,
        slot=agenda.slot_for_request(item.id), local=agenda.local, change_labels=agenda.CHANGE_LABELS,
    ), 400


# ---------------------------------------------------------------- horários da ligação (ADR-0019)


def _slots_page(form: SlotForm | None = None, *, status: int = 200, error: str | None = None):
    slots = agenda.staff_slots()
    return (
        render_template(
            "interno/horarios.html",
            form=form or SlotForm(formdata=None),
            slots=slots,
            requests=agenda.requests_by_id({s.visual_request_id for s in slots}),
            local=agenda.local,
            change_labels=agenda.CHANGE_LABELS,
            error=error,
        ),
        status,
    )


@bp.get("/horarios")
@staff_required
def slots():
    return _slots_page()


@bp.post("/horarios")
@limiter.limit(_interno_limit, exempt_when=lambda: not staff.is_staff(current_user))
@staff_required
def slot_create():
    form = SlotForm()
    if not form.validate_on_submit():
        return _slots_page(form, status=400)
    try:
        slot = agenda.create_slot(form.day.data, form.at.data, form.duration.data, current_user)
    except agenda.AgendaError as exc:
        db.session.rollback()
        return _slots_page(form, status=400, error=str(exc))
    flash(f"Horário criado: {agenda.local(slot.starts_at).strftime('%d/%m/%Y %H:%M')} (Brasília).", "success")
    return redirect(url_for("interno.slots"), code=303)


def _slot_or_404(slot_id) -> CallSlot:
    slot = db.session.get(CallSlot, slot_id)
    if slot is None:
        abort(404)
    return slot


@bp.post("/horarios/<uuid:slot_id>/remover")
@limiter.limit(_interno_limit, exempt_when=lambda: not staff.is_staff(current_user))
@staff_required
def slot_remove(slot_id):
    slot = _slot_or_404(slot_id)
    try:
        agenda.remove_slot(slot, current_user)
    except agenda.AgendaError as exc:
        db.session.rollback()
        return _slots_page(status=409, error=str(exc))
    flash("Horário removido.", "success")
    return redirect(url_for("interno.slots"), code=303)


@bp.post("/horarios/<uuid:slot_id>/reserva")
@limiter.limit(_interno_limit, exempt_when=lambda: not staff.is_staff(current_user))
@staff_required
def slot_decide(slot_id):
    """``acao=liberar`` cancela a reserva e libera o horário; ``acao=manter`` recusa o pedido."""
    slot = _slot_or_404(slot_id)
    action = request.form.get("acao")
    when = agenda.local(slot.starts_at).strftime("%d/%m/%Y às %H:%M")
    try:
        if action == "liberar":
            request_ = agenda.release(slot, current_user)
            outcome = "cancelada"
        elif action == "manter":
            request_ = agenda.decline(slot, current_user)
            outcome = "mantida"
        else:
            return _slots_page(status=400, error="Ação inválida.")
    except agenda.AgendaError as exc:
        db.session.rollback()
        return _slots_page(status=409, error=str(exc))
    if request_ is not None and request_.contact_email:
        email_svc.send_template(
            request_.contact_email,
            "Sua ligação de identidade visual",
            "call_change_decided",
            name=request_.contact_name,
            when=when,
            outcome=outcome,
            url=email_svc.external_url("identidade.call"),
        )
    flash("Reserva cancelada e horário liberado." if action == "liberar" else "Pedido recusado; a reserva continua.", "success")
    return redirect(url_for("interno.slots"), code=303)


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

