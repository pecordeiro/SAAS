"""Conta do usuário (/conta): confirmar e-mail, perfil, sessões, MFA e troca de empresa.

Também registra as guardas que rodam DEPOIS de ``tenancy.load_company``:
- e-mail não confirmado há mais de 7 dias → só a tela de confirmação;
- empresa com ``mfa_required`` e usuário owner sem MFA → só a tela de ativar o MFA.
"""

from __future__ import annotations

import uuid

from flask import Blueprint, Flask, abort, flash, g, make_response, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, logout_user
from sqlalchemy import select

from app.blueprints.auth import _limit, no_referrer
from app.extensions import db, limiter
from app.forms_accounts import (
    MfaDisableForm,
    MfaRegenerateForm,
    MfaSetupForm,
    ProfileEmailForm,
    ProfileNameForm,
    ProfilePasswordForm,
    SwitchCompanyForm,
    TokenActionForm,
)
from app.models import ROLE_OWNER, Company, Membership
from app.services import accounts, mfa
from app.services.accounts import AccountError
from app.tenancy import set_company

bp = Blueprint("account", __name__, url_prefix="/conta")

MFA_SETUP_KEY = "mfa_setup"

# Endpoints liberados mesmo com confirmação vencida ou MFA obrigatório pendente.
_ALWAYS_ALLOWED = {"static", "auth.logout", "public.set_theme", "public.health", "public.index"}


def register_guards(app: Flask) -> None:
    """Chamado em create_app depois de ``app.before_request(load_company)``."""

    @app.before_request
    def account_guards():
        if not current_user.is_authenticated:
            return None
        endpoint = request.endpoint or ""
        if endpoint in _ALWAYS_ALLOWED or endpoint.startswith("account.") or endpoint.startswith("auth."):
            return None
        if endpoint == "team.accept_invite":
            return None
        if accounts.needs_confirmation(current_user):
            return redirect(url_for("account.confirm_required"))
        membership = getattr(g, "membership", None)
        company = getattr(g, "company", None)
        if (
            membership is not None
            and company is not None
            and company.mfa_required
            and membership.role == ROLE_OWNER
            and not current_user.mfa_enabled
        ):
            flash("A empresa exige verificação em duas etapas para proprietários. Ative para continuar.", "info")
            return redirect(url_for("account.mfa_setup"))
        return None

    @app.context_processor
    def account_context():
        if not current_user.is_authenticated:
            return {}
        return {
            "email_unconfirmed": current_user.email_confirmed_at is None,
            "company_count": len(accounts.active_memberships(current_user.id)),
        }


# --------------------------------------------------------------------------- confirmação


@bp.route("/confirmar/<token>", methods=["GET", "POST"])
@limiter.limit(_limit("EMAIL_RESEND_RATE_LIMIT"), methods=["POST"])
def confirm_email(token: str):
    form = TokenActionForm()
    state = accounts.check_confirmation(token)
    error = None
    if state == accounts.VALID and form.validate_on_submit():
        try:
            state, _user = accounts.confirm_email(token)
        except AccountError as exc:
            error = str(exc)
            state = accounts.INVALID
        if state == accounts.VALID:
            flash("E-mail confirmado.", "sucesso")
            target = url_for("app.projects") if current_user.is_authenticated else url_for("auth.login")
            return no_referrer(redirect(target, code=303))
    status_code = 200 if state == accounts.VALID and request.method == "GET" else 400
    return no_referrer(make_response(render_template("account/confirm.html", form=form, state=state, error=error), status_code))


@bp.get("/confirmar-email")
@login_required
def confirm_required():
    return render_template(
        "account/confirm_required.html",
        form=TokenActionForm(),
        blocked=accounts.needs_confirmation(current_user),
    )


@bp.post("/confirmar-email/reenviar")
@login_required
@limiter.limit(_limit("EMAIL_RESEND_RATE_LIMIT"))
def confirm_resend():
    if current_user.email_confirmed_at is None:
        accounts.send_email_confirmation(current_user)
        db.session.commit()
    flash(f"Enviamos um novo link para {current_user.email}.", "sucesso")
    return redirect(url_for("account.confirm_required"), code=303)


# --------------------------------------------------------------------------- perfil


def _profile(status: int = 200, **forms):
    forms.setdefault("name_form", ProfileNameForm(formdata=None, name=current_user.name))
    forms.setdefault("email_form", ProfileEmailForm(formdata=None))
    forms.setdefault("password_form", ProfilePasswordForm(formdata=None))
    forms.setdefault("sessions_form", TokenActionForm(formdata=None))
    return render_template(
        "account/profile.html",
        recovery_left=mfa.remaining_recovery_codes(current_user) if current_user.mfa_enabled else 0,
        **forms,
    ), status


@bp.get("/perfil")
@login_required
def profile():
    return _profile()


@bp.post("/perfil/nome")
@login_required
def profile_name():
    form = ProfileNameForm()
    if not form.validate_on_submit():
        return _profile(400, name_form=form)
    current_user.name = form.name.data
    db.session.commit()
    flash("Nome atualizado.", "sucesso")
    return redirect(url_for("account.profile"), code=303)


@bp.post("/perfil/email")
@login_required
@limiter.limit(_limit("EMAIL_RESEND_RATE_LIMIT"))
def profile_email():
    form = ProfileEmailForm()
    if form.validate_on_submit():
        try:
            accounts.request_email_change(current_user, form.current_password.data, form.email.data)
        except AccountError as exc:
            form.current_password.errors.append(str(exc)) if "Senha" in str(exc) else form.email.errors.append(str(exc))
        else:
            flash(f"Enviamos um link de confirmação para {form.email.data}. O e-mail só muda depois de confirmar.", "sucesso")
            return redirect(url_for("account.profile"), code=303)
    return _profile(400, email_form=form)


@bp.post("/perfil/senha")
@login_required
@limiter.limit(_limit("PASSWORD_RESET_RATE_LIMIT"))
def profile_password():
    form = ProfilePasswordForm()
    if form.validate_on_submit():
        try:
            accounts.change_password(current_user, form.current_password.data, form.password.data)
        except AccountError as exc:
            form.current_password.errors.append(str(exc))
        else:
            # As outras sessões caem (session_version mudou); esta continua com a versão nova.
            from app.blueprints.auth import start_session

            company_id = session.get("company_id")
            start_session(current_user._get_current_object())
            if company_id:
                session["company_id"] = company_id
            flash("Senha trocada. As outras sessões foram encerradas.", "sucesso")
            return redirect(url_for("account.profile"), code=303)
    return _profile(400, password_form=form)


@bp.post("/sair-de-todos")
@login_required
def logout_everywhere():
    accounts.bump_session_version(current_user)
    db.session.commit()
    logout_user()
    session.clear()
    flash("Você saiu de todos os dispositivos.", "info")
    return redirect(url_for("auth.login"), code=303)


# --------------------------------------------------------------------------- MFA


def _setup_secret(create: bool = True) -> str | None:
    enc = session.get(MFA_SETUP_KEY)
    secret = mfa.decrypt_secret(enc) if enc else None
    if secret is None and create:
        secret = mfa.new_secret()
        session[MFA_SETUP_KEY] = mfa.encrypt_secret(secret)  # cookie assinado: guarda só cifrado
    return secret


@bp.get("/mfa")
@login_required
def mfa_setup():
    if current_user.mfa_enabled:
        return redirect(url_for("account.profile"))
    secret = _setup_secret()
    response = make_response(render_template("account/mfa_setup.html", form=MfaSetupForm(formdata=None), secret=secret))
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/mfa/qr.svg")
@login_required
def mfa_qr():
    secret = _setup_secret(create=False)
    if secret is None or current_user.mfa_enabled:
        abort(404)
    response = make_response(mfa.qr_svg(mfa.provisioning_uri(secret, current_user.email)))
    response.headers["Content-Type"] = "image/svg+xml"
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.post("/mfa/ativar")
@login_required
@limiter.limit(_limit("MFA_RATE_LIMIT"))
def mfa_enable():
    if current_user.mfa_enabled:
        return redirect(url_for("account.profile"), code=303)
    form = MfaSetupForm()
    secret = _setup_secret(create=False)
    if secret is None:
        return redirect(url_for("account.mfa_setup"), code=303)
    if form.validate_on_submit():
        step = mfa.check_totp(secret, form.code.data)
        if step is not None:
            codes = mfa.enable(current_user, secret)
            current_user.totp_last_step = step
            db.session.commit()
            session.pop(MFA_SETUP_KEY, None)
            response = make_response(render_template("account/mfa_codes.html", codes=codes))
            response.headers["Cache-Control"] = "no-store"
            return response
        form.code.errors.append("Código inválido. Confira o horário do celular e tente de novo.")
    return render_template("account/mfa_setup.html", form=form, secret=secret), 400


def _owner_requires_mfa() -> bool:
    return bool(
        db.session.execute(
            select(Membership.id)
            .join(Company, Company.id == Membership.company_id)
            .where(
                Membership.user_id == current_user.id,
                Membership.active.is_(True),
                Membership.role == ROLE_OWNER,
                Company.mfa_required.is_(True),
            )
        ).first()
    )


@bp.post("/mfa/desativar")
@login_required
@limiter.limit(_limit("MFA_RATE_LIMIT"))
def mfa_disable():
    form = MfaDisableForm()
    if not current_user.mfa_enabled:
        return redirect(url_for("account.profile"), code=303)
    if form.validate_on_submit():
        from app.services.passwords import verify_password

        if _owner_requires_mfa():
            flash("Uma empresa em que você é proprietário exige MFA: não dá para desativar.", "erro")
            return redirect(url_for("account.profile"), code=303)
        if verify_password(current_user.password_hash, form.current_password.data) and (
            mfa.verify_user_totp(current_user, form.code.data) or mfa.use_recovery_code(current_user, form.code.data)
        ):
            mfa.disable(current_user)
            db.session.commit()
            flash("Verificação em duas etapas desativada.", "info")
            return redirect(url_for("account.profile"), code=303)
        db.session.rollback()
    flash("Senha ou código incorretos.", "erro")
    return redirect(url_for("account.profile"), code=303)


@bp.post("/mfa/codigos")
@login_required
@limiter.limit(_limit("MFA_RATE_LIMIT"))
def mfa_regenerate():
    form = MfaRegenerateForm()
    from app.services.passwords import verify_password

    if current_user.mfa_enabled and form.validate_on_submit() and verify_password(current_user.password_hash, form.current_password.data):
        codes = mfa.new_recovery_codes(current_user)
        db.session.commit()
        response = make_response(render_template("account/mfa_codes.html", codes=codes))
        response.headers["Cache-Control"] = "no-store"
        return response
    flash("Senha incorreta.", "erro")
    return redirect(url_for("account.profile"), code=303)


# --------------------------------------------------------------------------- empresas


@bp.get("/empresas")
@login_required
def companies():
    return render_template(
        "account/companies.html",
        memberships=accounts.active_memberships(current_user.id),
        form=SwitchCompanyForm(formdata=None),
    )


@bp.post("/empresas/trocar")
@login_required
def switch_company():
    """Única entrada de empresa vinda de formulário: vale só se o usuário tem vínculo ATIVO
    com ela (senão 404, sem revelar se a empresa existe)."""
    form = SwitchCompanyForm()
    if not form.validate_on_submit():
        abort(400)
    try:
        company_id = uuid.UUID(form.company_id.data)
    except ValueError:
        abort(404)
    membership = next((m for m in accounts.active_memberships(current_user.id) if m.company_id == company_id), None)
    if membership is None:
        abort(404)
    set_company(membership)
    flash(f"Agora você está em {membership.company.name}.", "sucesso")
    return redirect(url_for("app.projects"), code=303)
