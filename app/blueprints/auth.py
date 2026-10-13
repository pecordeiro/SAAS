"""Cadastro de empresa, entrar e sair."""

from __future__ import annotations

from urllib.parse import urlsplit

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app import rls
from app.extensions import db, limiter
from app.forms import LoginForm, LogoutForm, SignupForm
from app.models import ROLE_OWNER, Company, Membership, User
from app.services.passwords import hash_password, needs_rehash, verify_password
from app.tenancy import first_active_membership, set_company

bp = Blueprint("auth", __name__)

GENERIC_LOGIN_ERROR = "E-mail ou senha incorretos."
SIGNUP_EMAIL_ERROR = "Não foi possível cadastrar com este e-mail. Se você já tem conta, entre."


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


def _login_rate_limit() -> str:
    return current_app.config["LOGIN_RATE_LIMIT"]


def _signup_rate_limit() -> str:
    return current_app.config["SIGNUP_RATE_LIMIT"]


def _start_session(user: User) -> None:
    # Sessão nova a cada login (evita fixação de sessão).
    session.clear()
    login_user(user)
    session.permanent = True
    membership = first_active_membership(user.id)
    if membership is not None:
        set_company(membership)


@bp.route("/cadastro", methods=["GET", "POST"])
@limiter.limit(_signup_rate_limit, methods=["POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("app.projects"))
    form = SignupForm()
    if form.validate_on_submit():
        exists = db.session.execute(
            select(User.id).where(func.lower(User.email) == form.email.data)
        ).first()
        if exists:
            form.email.errors.append(SIGNUP_EMAIL_ERROR)
        else:
            company = Company(name=form.company_name.data)
            user = User(email=form.email.data, name=form.name.data, password_hash=hash_password(form.password.data))
            db.session.add_all([company, user])
            db.session.flush()
            # RLS: o vínculo novo só pode ser gravado com a empresa recém-criada no contexto.
            rls.set_context(company_id=company.id, user_id=user.id)
            db.session.add(Membership(company_id=company.id, user_id=user.id, role=ROLE_OWNER))
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                form.email.errors.append(SIGNUP_EMAIL_ERROR)
            else:
                _start_session(user)
                flash("Empresa cadastrada. Bem-vindo!", "sucesso")
                return redirect(url_for("app.projects"))
    status = 400 if request.method == "POST" else 200
    return render_template("auth/signup.html", form=form), status


@bp.route("/entrar", methods=["GET", "POST"])
@limiter.limit(_login_rate_limit, methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("app.projects"))
    form = LoginForm()
    if request.method == "GET":
        form.next.data = safe_next(request.args.get("next")) or ""
    error = None
    if form.validate_on_submit():
        user = db.session.execute(select(User).where(User.email == form.email.data)).scalar_one_or_none()
        valid = verify_password(user.password_hash if user else None, form.password.data)
        if user is not None and valid and user.active:
            if needs_rehash(user.password_hash):
                user.password_hash = hash_password(form.password.data)
                db.session.commit()
            _start_session(user)
            return redirect(safe_next(form.next.data) or url_for("app.projects"))
        error = GENERIC_LOGIN_ERROR
    status = 400 if request.method == "POST" else 200
    return render_template("auth/login.html", form=form, error=error), status


@bp.post("/sair")
@login_required
def logout():
    form = LogoutForm()
    if not form.validate_on_submit():  # CSRF já validado globalmente; mantido por clareza
        return redirect(url_for("app.projects"))
    logout_user()
    session.clear()
    flash("Você saiu.", "info")
    return redirect(url_for("auth.login"))
