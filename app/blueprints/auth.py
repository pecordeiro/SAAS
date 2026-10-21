"""Cadastro de empresa, entrar (com bloqueio progressivo e MFA), sair, esqueci a senha."""

from __future__ import annotations

import time
import uuid
from urllib.parse import urlsplit

from flask import Blueprint, current_app, flash, make_response, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db, limiter
from app.forms import LoginForm, LogoutForm, SignupForm
from app.forms_accounts import ForgotPasswordForm, MfaLoginForm, ResetPasswordForm, TokenActionForm
from app.models import User
from app.services import accounts, lockout, mfa, trusted_device
from app.services.passwords import hash_password, needs_rehash, verify_password
from app.services.tokens import utcnow
from app.tenancy import first_active_membership, set_company

bp = Blueprint("auth", __name__)

GENERIC_LOGIN_ERROR = "E-mail ou senha incorretos."
GENERIC_MFA_ERROR = "Código inválido. Confira o aplicativo e tente de novo."
FORGOT_MESSAGE = "Se houver conta com esse e-mail, enviamos um link válido por 1 hora."
MFA_PENDING_KEY = "mfa_pending"
MFA_PENDING_SECONDS = 300
SIGNUP_EMAIL_KEY = "signup_email"


def safe_next(target: str | None) -> str | None:
    """Aceita só caminho interno ("/app/..."); qualquer outra coisa vira None (sem open redirect)."""
    if not target or not isinstance(target, str):
        return None
    target = target.strip()
    if not target.startswith("/") or target.startswith("//") or "\\" in target:
        return None
    if any(ord(ch) < 32 for ch in target):
        return None
    parts = urlsplit(target)
    if parts.scheme or parts.netloc:
        return None
    return target


def _limit(key: str):
    return lambda: current_app.config[key]


@bp.after_app_request
def _trusted_device_cookie(response):
    return trusted_device.apply(response)


def lock_message(status: lockout.LockStatus) -> str:
    unit = "minuto" if status.minutes == 1 else "minutos"
    return f"Muitas tentativas. Tente de novo em {status.minutes} {unit}."


def no_referrer(response):
    """Páginas com token na URL: o token não vaza no Referer de links externos."""
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


def start_session(user: User) -> None:
    # Sessão nova a cada login (evita fixação de sessão).
    session.clear()
    login_user(user)
    session.permanent = True
    user.last_login_at = utcnow()
    trusted_device.remember(user.id)  # cookie de dispositivo confiável (after_app_request)
    membership = first_active_membership(user.id)
    if membership is not None:
        set_company(membership)
    db.session.commit()


# --------------------------------------------------------------------------- cadastro


@bp.route("/cadastro", methods=["GET", "POST"])
@limiter.limit(_limit("SIGNUP_RATE_LIMIT"), methods=["POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("app.home"))
    form = SignupForm()
    if form.validate_on_submit():
        # Sem enumeração: e-mail novo ou já cadastrado → mesma resposta (o dono recebe aviso).
        accounts.signup(form.company_name.data, form.name.data, form.email.data, form.password.data)
        session[SIGNUP_EMAIL_KEY] = form.email.data
        return redirect(url_for("auth.signup_done"), code=303)
    status = 400 if request.method == "POST" else 200
    return render_template("auth/signup.html", form=form), status


@bp.get("/cadastro/confirme")
def signup_done():
    email = session.get(SIGNUP_EMAIL_KEY)
    if not email:
        return redirect(url_for("auth.signup"))
    return render_template("auth/signup_done.html", email=email, form=TokenActionForm())


@bp.post("/cadastro/reenviar")
@limiter.limit(_limit("EMAIL_RESEND_RATE_LIMIT"))
def signup_resend():
    email = session.get(SIGNUP_EMAIL_KEY)
    if email:
        user = accounts.find_user_by_email(email)
        if user is not None and user.active and user.email_confirmed_at is None:
            accounts.send_email_confirmation(user)
            db.session.commit()
    flash("Se o cadastro estiver pendente, enviamos um novo link de confirmação.", "info")
    return redirect(url_for("auth.signup_done"), code=303)


# --------------------------------------------------------------------------- entrar


@bp.route("/entrar", methods=["GET", "POST"])
@limiter.limit(_limit("LOGIN_RATE_LIMIT"), methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("app.home"))
    form = LoginForm()
    if request.method == "GET":
        form.next.data = safe_next(request.args.get("next")) or ""
    error = None
    status_code = 400 if request.method == "POST" else 200
    if form.validate_on_submit():
        email = form.email.data
        ip = request.remote_addr
        # Conta bloqueada: nunca verifica. IP bloqueado: só verifica para conta que já entrou
        # neste navegador (cookie de dispositivo confiável) — barra password spraying sem
        # trancar quem já usa o sistema atrás do mesmo NAT/proxy.
        locked = lockout.status(email, None)
        ip_locked = lockout.status(None, ip)
        user = accounts.find_user_by_email(email) if not locked.locked else None
        if locked.locked:
            error, status_code = lock_message(locked), 429
        elif ip_locked.locked and (user is None or not trusted_device.is_trusted(user.id)):
            error, status_code = lock_message(ip_locked), 429
        else:
            valid = verify_password(user.password_hash if user else None, form.password.data)
            if user is not None and valid and user.active:
                if needs_rehash(user.password_hash):
                    user.password_hash = hash_password(form.password.data)
                next_url = safe_next(form.next.data)
                if user.mfa_enabled:
                    db.session.commit()
                    session.clear()
                    session[MFA_PENDING_KEY] = {
                        "uid": str(user.id),
                        "v": user.session_version,
                        "at": int(time.time()),
                        "next": next_url or "",
                    }
                    return redirect(url_for("auth.login_mfa"), code=303)
                lockout.register_success(email)
                start_session(user)
                return redirect(next_url or url_for("app.home"))
            after = lockout.register_failure(email, ip)
            if after.locked:
                error, status_code = lock_message(after), 429
            else:
                error = GENERIC_LOGIN_ERROR
    return render_template("auth/login.html", form=form, error=error), status_code


def _pending_mfa_user() -> tuple[User | None, dict]:
    data = session.get(MFA_PENDING_KEY) or {}
    if not data or int(time.time()) - int(data.get("at", 0)) > MFA_PENDING_SECONDS:
        return None, {}
    try:
        user = db.session.get(User, uuid.UUID(str(data.get("uid"))))
    except ValueError:
        return None, {}
    if user is None or not user.active or not user.mfa_enabled or user.session_version != data.get("v"):
        return None, {}
    return user, data


@bp.route("/entrar/mfa", methods=["GET", "POST"])
@limiter.limit(_limit("MFA_RATE_LIMIT"), methods=["POST"])
def login_mfa():
    user, data = _pending_mfa_user()
    if user is None:
        session.pop(MFA_PENDING_KEY, None)
        flash("Entre de novo para continuar.", "info")
        return redirect(url_for("auth.login"))
    form = MfaLoginForm()
    error = None
    status_code = 400 if request.method == "POST" else 200
    if form.validate_on_submit():
        ip = request.remote_addr
        locked = lockout.status(user.email, None)
        if locked.locked:
            error, status_code = lock_message(locked), 429
        elif mfa.verify_user_totp(user, form.code.data) or mfa.use_recovery_code(user, form.code.data):
            lockout.register_success(user.email)
            next_url = safe_next(data.get("next"))
            start_session(user)
            return redirect(next_url or url_for("app.home"))
        else:
            db.session.rollback()
            after = lockout.register_failure(user.email, ip)
            error, status_code = (lock_message(after), 429) if after.locked else (GENERIC_MFA_ERROR, 400)
    return render_template("auth/login_mfa.html", form=form, error=error), status_code


@bp.post("/sair")
@login_required
def logout():
    """Sai SÓ desta sessão (limpa o cookie). Para derrubar as demais: “Sair de todos os
    dispositivos” no perfil, que incrementa session_version."""
    form = LogoutForm()
    if not form.validate_on_submit():  # CSRF já validado globalmente; mantido por clareza
        return redirect(url_for("app.home"))
    logout_user()
    session.clear()
    flash("Você saiu.", "info")
    return redirect(url_for("auth.login"))


# --------------------------------------------------------------------------- senha


@bp.route("/senha/esqueci", methods=["GET", "POST"])
@limiter.limit(_limit("PASSWORD_RESET_RATE_LIMIT"), methods=["POST"])
def forgot_password():
    form = ForgotPasswordForm()
    sent = False
    if form.validate_on_submit():
        accounts.request_password_reset(form.email.data)
        sent = True
    status_code = 400 if request.method == "POST" and not sent else 200
    return render_template("auth/forgot.html", form=form, sent=sent, message=FORGOT_MESSAGE), status_code


@bp.route("/senha/redefinir/<token>", methods=["GET", "POST"])
@limiter.limit(_limit("PASSWORD_RESET_RATE_LIMIT"), methods=["POST"])
def reset_password(token: str):
    form = ResetPasswordForm()
    state = accounts.check_reset(token)
    status_code = 200
    if state == accounts.VALID and form.validate_on_submit():
        state, _user = accounts.reset_password(token, form.password.data)
        if state == accounts.VALID:
            logout_user()
            session.clear()
            flash("Senha trocada. Entre com a nova senha.", "sucesso")
            return no_referrer(redirect(url_for("auth.login"), code=303))
    if state != accounts.VALID:
        status_code = 400
    elif request.method == "POST":
        status_code = 400
    response = make_response(render_template("auth/reset.html", form=form, state=state), status_code)
    return no_referrer(response)
