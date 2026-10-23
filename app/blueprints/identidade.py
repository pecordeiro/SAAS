"""ADR-0019 — briefing de identidade visual e agendamento da ligação (/app/identidade-visual).

Acesso (checado aqui, no servidor; o menu só esconde por conveniência — ADR-0009):
1. Login e empresa da sessão (``tenant_required``).
2. Plano em vigor sem a feature ``visual_custom`` → 404 para TODOS os papéis (a rota não existe
   para quem não contratou Empresa ou Implantação).
3. Papel diferente de proprietário → 403.
4. Escrita com a empresa em modo leitura → 402 (``entitlements.ensure_writable``).

Toda escrita: CSRF (Flask-WTF), campo armadilha (``website``: preenchido → 400, nada grava),
limite por IP e por empresa (``VISUAL_RATE_LIMIT_IP`` / ``VISUAL_RATE_LIMIT_COMPANY``). Ids da URL
são resolvidos na empresa da sessão (``get_or_404``: de outra empresa → 404). Imagens servidas só
por ``/app/identidade-visual/arquivos/<uuid>`` com tipo fixo, ``nosniff`` e CSP ``sandbox``.
"""

from __future__ import annotations

import logging
from functools import wraps
from itertools import groupby

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_limiter.util import get_remote_address
from flask_login import current_user
from wtforms import RadioField, StringField, TextAreaField
from wtforms.validators import Length, Optional

from app.extensions import db, limiter
from app.forms import BaseForm, _strip
from app.models import ROLE_OPERATOR, ROLE_OWNER, VISUAL_STATUSES
from app.models.visual import (
    EMAIL_MAX,
    FILE_LOGO,
    FILE_PRODUCT,
    NAME_MAX,
    PHONE_MAX,
    PREFS_MAX,
    PRODUCTS_MAX,
    SITES_MAX_CHARS,
    CallBooking,
    VisualBriefingFile,
)
from app.services import agenda as agenda_svc
from app.services import email as email_svc
from app.services import staff as staff_svc
from app.services import storage as storage_mod
from app.services import visual as visual_svc
from app.services.entitlements import ensure_writable
from app.tenancy import SAFE_METHODS, get_or_404, tenant_required

log = logging.getLogger(__name__)

bp = Blueprint("identidade", __name__, url_prefix="/app/identidade-visual")

FILE_CSP = "default-src 'none'; sandbox"
HONEYPOT = "website"


def _company_key() -> str:
    """Chave do limite por empresa: a empresa da sessão (cookie assinado pelo servidor)."""
    company = getattr(g, "company", None)
    raw = str(company.id) if company is not None else session.get("company_id")
    return f"identidade-empresa:{raw or get_remote_address()}"


# Limites do blueprint inteiro (só POST): por IP e por empresa.
limiter.limit(lambda: current_app.config.get("VISUAL_RATE_LIMIT_IP", "20 per minute; 200 per hour"), methods=["POST"])(bp)
limiter.limit(
    lambda: current_app.config.get("VISUAL_RATE_LIMIT_COMPANY", "30 per minute; 300 per hour"),
    key_func=_company_key,
    methods=["POST"],
)(bp)


def visual_owner_required(view):
    """Plano com ``visual_custom`` (senão 404) → proprietário (senão 403) → escrita (senão 402)."""

    @wraps(view)
    def inner(*args, **kwargs):
        if not visual_svc.available(g.company):
            abort(404)
        if not g.membership.has_role(ROLE_OWNER):
            abort(403)
        if request.method not in SAFE_METHODS:
            ensure_writable(g.company)
        return view(*args, **kwargs)

    # Papel mínimo baixo + leitura liberada: a ordem 404 → 403 → 402 fica toda aqui.
    return tenant_required(ROLE_OPERATOR, allow_read_only=True)(inner)


def honeypot_tripped() -> bool:
    return bool((request.form.get(HONEYPOT) or "").strip())


@bp.app_context_processor
def _menu():
    """Menu “Identidade visual” só para o proprietário com o plano (a rota recusa por conta própria)."""
    membership = getattr(g, "membership", None)
    company = getattr(g, "company", None)
    show = False
    if company is not None and membership is not None and membership.role == ROLE_OWNER:
        try:
            show = visual_svc.available(company)
        except Exception:  # noqa: BLE001 - menu nunca derruba a página
            show = False
    return {"visual_menu": show}


# ---------------------------------------------------------------- formulários


class BriefingForm(BaseForm):
    company_name = StringField("Nome da empresa", filters=[_strip], validators=[Optional(), Length(max=NAME_MAX)])
    products = TextAreaField("Produtos", filters=[_strip], validators=[Optional(), Length(max=PRODUCTS_MAX)])
    colors = StringField("Cores de preferência", filters=[_strip], validators=[Optional(), Length(max=PREFS_MAX)])
    fonts = StringField("Fontes de preferência", filters=[_strip], validators=[Optional(), Length(max=PREFS_MAX)])
    reference_sites = TextAreaField(
        "Sites de referência", filters=[_strip], validators=[Optional(), Length(max=SITES_MAX_CHARS)]
    )
    tone = RadioField(
        "Tom de voz",
        choices=[("", "Sem preferência"), ("formal", "Formal"), ("neutro", "Neutro"), ("descontraido", "Descontraído")],
        default="",
        validate_choice=False,  # o serviço valida (valor fora da lista → erro na tela)
    )
    contact_name = StringField("Nome do contato", filters=[_strip], validators=[Optional(), Length(max=NAME_MAX)])
    contact_phone = StringField("Telefone (com DDD)", filters=[_strip], validators=[Optional(), Length(max=PHONE_MAX)])
    contact_email = StringField("E-mail do contato", filters=[_strip], validators=[Optional(), Length(max=EMAIL_MAX)])


def _form_from(briefing) -> BriefingForm:
    if briefing is None:
        return BriefingForm(formdata=None, data={"company_name": g.company.name})
    return BriefingForm(
        formdata=None,
        data={
            "company_name": briefing.company_name or "",
            "products": briefing.products or "",
            "colors": briefing.colors or "",
            "fonts": briefing.fonts or "",
            "reference_sites": briefing.reference_sites or "",
            "tone": briefing.tone or "",
            "contact_name": briefing.contact_name or "",
            "contact_phone": briefing.contact_phone or "",
            "contact_email": briefing.contact_email or "",
        },
    )


def _step(status: str | None) -> int:
    """Posição do estado na trilha nova → preenchido → em andamento → entregue (1-based)."""
    if status not in VISUAL_STATUSES:
        return 1
    index = VISUAL_STATUSES.index(status) + 1
    return index + 1 if status == "delivered" else index  # entregue: todos os passos feitos


def _briefing_page(form: BriefingForm | None = None, *, status: int = 200, error: str | None = None,
                   file_error: str | None = None):
    company = g.company
    request_ = visual_svc.current_request(company.id)
    briefing = visual_svc.get_briefing(company.id)
    files = visual_svc.list_files(company.id)
    booking = agenda_svc.booking_for(company.id)
    return (
        render_template(
            "identidade/briefing.html",
            form=form or _form_from(briefing),
            request_=request_,
            briefing=briefing,
            editable=visual_svc.can_edit(request_),
            missing=visual_svc.missing_fields(briefing),
            step=_step(request_.status if request_ else None),
            labels=staff_svc.STATUS_LABELS,
            tone_labels=visual_svc.TONE_LABELS,
            logos=[f for f in files if f.kind == FILE_LOGO],
            photos=[f for f in files if f.kind == FILE_PRODUCT],
            photos_max=visual_svc.max_files(FILE_PRODUCT),
            storage_enabled=visual_svc.storage_enabled(),
            photo_max_mb=int(current_app.config.get("PHOTO_MAX_BYTES", 5 * 1024 * 1024)) // (1024 * 1024),
            booking=booking,
            error=error,
            file_error=file_error,
            honeypot=HONEYPOT,
        ),
        status,
    )


# ---------------------------------------------------------------- e-mails


def _staff_email(subject: str, template: str, **context) -> None:
    to = (current_app.config.get("STAFF_NOTIFY_EMAIL") or "").strip()
    if to:
        email_svc.send_template(to, subject, template, **context)


# ---------------------------------------------------------------- briefing


@bp.route("", methods=["GET", "POST"])
@visual_owner_required
def briefing():
    if request.method == "GET":
        return _briefing_page()
    if honeypot_tripped():
        abort(400)
    form = BriefingForm()
    if not form.validate_on_submit():
        return _briefing_page(form, status=400, error="Confira os campos destacados.")
    data = visual_svc.BriefingInput(**{name: form[name].data or "" for name in visual_svc.TEXT_FIELDS})
    try:
        _briefing, submitted = visual_svc.save_briefing(g.company, data, current_user.id)
    except visual_svc.VisualError as exc:
        db.session.rollback()
        return _briefing_page(form, status=400 if not isinstance(exc, visual_svc.LockedError) else 409, error=str(exc))
    company_name, company_id = g.company.name, g.company.id
    request_ = visual_svc.current_request(company_id)
    request_id = request_.id if request_ else None
    db.session.commit()
    if submitted:
        _staff_email(
            "Briefing de identidade visual preenchido",
            "staff_briefing_filled",
            company_name=company_name,
            url=email_svc.external_url("interno.detail", request_id=request_id) if request_id else email_svc.external_url("interno.index"),
        )
        flash("Briefing enviado. A equipe foi avisada e vai entrar em contato.", "sucesso")
    else:
        flash("Briefing salvo.", "sucesso")
    return redirect(url_for("identidade.briefing"), 303)


@bp.post("/arquivos")
@visual_owner_required
def file_upload():
    """Logo ou foto de produto. Corpo até ``PHOTO_MAX_REQUEST_BYTES`` (security.py); nome enviado
    só serve para conferir a extensão; o conteúdo é validado e reencodado (``photos.process``)."""
    if honeypot_tripped():
        abort(400)
    kind = request.form.get("tipo", "")
    upload = request.files.get("arquivo")
    if upload is None or not upload.filename:
        return _briefing_page(status=400, file_error="Escolha uma imagem.")
    limit = int(current_app.config.get("PHOTO_MAX_BYTES", 5 * 1024 * 1024))
    data = upload.stream.read(limit + 1)
    try:
        row = visual_svc.add_file(g.company, kind, upload.filename, data, current_user.id)
    except visual_svc.VisualError as exc:
        db.session.rollback()
        return _briefing_page(status=409 if isinstance(exc, visual_svc.LockedError) else 400, file_error=str(exc))
    except storage_mod.StorageError:
        db.session.rollback()
        return _briefing_page(status=503, file_error="Não foi possível guardar a imagem agora. Tente de novo.")
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        visual_svc.discard_objects(row)
        raise
    flash("Logo enviado." if kind == FILE_LOGO else "Foto de produto enviada.", "sucesso")
    return redirect(url_for("identidade.briefing", _anchor="imagens"), 303)


@bp.get("/arquivos/<uuid:file_id>")
@visual_owner_required
def file_view(file_id):
    row = get_or_404(VisualBriefingFile, file_id)
    mini = request.args.get("tamanho") == "mini"
    try:
        data = visual_svc.read_file(row, mini=mini)
    except storage_mod.ObjectNotFound:
        abort(404)
    except storage_mod.StorageError:
        abort(503)
    response = Response(data, mimetype="image/jpeg")
    headers = response.headers
    headers["Content-Type"] = "image/jpeg"
    headers["X-Content-Type-Options"] = "nosniff"
    headers["Cache-Control"] = "private, max-age=300"
    headers["Vary"] = "Cookie"
    headers["Content-Disposition"] = f'inline; filename="briefing-{row.id}{"-mini" if mini else ""}.jpg"'
    headers["Content-Security-Policy"] = FILE_CSP
    headers["Cross-Origin-Resource-Policy"] = "same-origin"
    return response


@bp.post("/arquivos/<uuid:file_id>/apagar")
@visual_owner_required
def file_delete(file_id):
    row = get_or_404(VisualBriefingFile, file_id)
    if honeypot_tripped():
        abort(400)
    try:
        visual_svc.delete_file(g.company, row, current_user.id)
    except visual_svc.VisualError as exc:
        db.session.rollback()
        return _briefing_page(status=409, file_error=str(exc))
    except storage_mod.StorageError:
        db.session.rollback()
        return _briefing_page(status=503, file_error="Não foi possível apagar a imagem agora. Tente de novo.")
    db.session.commit()
    flash("Imagem apagada.", "sucesso")
    return redirect(url_for("identidade.briefing", _anchor="imagens"), 303)


# ---------------------------------------------------------------- ligação


def _slot_groups(slots):
    """[(rótulo do dia em BRT, [horários])] — só apresentação (a validação é do servidor)."""
    return [
        (day, list(items))
        for day, items in groupby(slots, key=lambda s: agenda_svc.local(s.starts_at).date())
    ]


def _call_page(*, status: int = 200, error: str | None = None, contact_name: str | None = None,
               contact_phone: str | None = None, selected: str | None = None):
    company = g.company
    booking = agenda_svc.booking_for(company.id)
    briefing = visual_svc.get_briefing(company.id)
    slots = [] if booking is not None else agenda_svc.free_slots()
    return (
        render_template(
            "identidade/ligacao.html",
            booking=booking,
            groups=_slot_groups(slots),
            local=agenda_svc.local,
            change_labels=agenda_svc.CHANGE_LABELS,
            contact_name=contact_name if contact_name is not None else (briefing.contact_name if briefing else current_user.name) or "",
            contact_phone=contact_phone if contact_phone is not None else (briefing.contact_phone if briefing else "") or "",
            selected=selected,
            error=error,
            honeypot=HONEYPOT,
        ),
        status,
    )


@bp.route("/ligacao", methods=["GET", "POST"])
@visual_owner_required
def call():
    if request.method == "GET":
        return _call_page()
    if honeypot_tripped():
        abort(400)
    name, phone = request.form.get("contact_name"), request.form.get("contact_phone")
    slot_id = request.form.get("slot_id")
    try:
        contact = agenda_svc.validate_contact(name, phone)
        booking = agenda_svc.book(g.company, slot_id, contact, current_user.id)
    except agenda_svc.AgendaError as exc:
        db.session.rollback()
        return _call_page(
            status=409 if isinstance(exc, agenda_svc.SlotTaken) else 400,
            error=str(exc), contact_name=name or "", contact_phone=phone or "", selected=slot_id,
        )
    starts = agenda_svc.local(booking.slot.starts_at)
    duration = booking.slot.duration_minutes
    company_name, owner_email = g.company.name, current_user.email
    db.session.commit()
    when = starts.strftime("%d/%m/%Y às %H:%M")
    email_svc.send_template(
        owner_email,
        "Ligação de identidade visual marcada",
        "call_booked",
        name=current_user.name,
        when=when,
        duration=duration,
        url=email_svc.external_url("identidade.call"),
    )
    _staff_email(
        "Ligação de identidade visual marcada",
        "staff_call_booked",
        company_name=company_name,
        when=when,
        url=email_svc.external_url("interno.slots"),
    )
    flash(f"Ligação marcada para {when} (horário de Brasília).", "sucesso")
    return redirect(url_for("identidade.call"), 303)


@bp.post("/ligacao/<uuid:booking_id>/pedido")
@visual_owner_required
def call_change(booking_id):
    booking = get_or_404(CallBooking, booking_id)
    if honeypot_tripped():
        abort(400)
    kind = request.form.get("tipo", "")
    try:
        agenda_svc.request_change(g.company, booking, kind, current_user.id)
    except agenda_svc.AgendaError as exc:
        db.session.rollback()
        return _call_page(status=400, error=str(exc))
    when = agenda_svc.local(booking.slot.starts_at).strftime("%d/%m/%Y às %H:%M")
    company_name = g.company.name
    db.session.commit()
    _staff_email(
        "Pedido de mudança na ligação de identidade visual",
        "staff_call_change_request",
        company_name=company_name,
        when=when,
        kind=agenda_svc.CHANGE_LABELS.get(kind, kind),
        url=email_svc.external_url("interno.slots"),
    )
    flash("Pedido enviado. A equipe vai responder por e-mail.", "sucesso")
    return redirect(url_for("identidade.call"), 303)
