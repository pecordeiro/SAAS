"""Usuários e convites (/app/usuarios) e aceite de convite (/convite/<token>).

Papéis: supervisor vê a lista, convida supervisor/operador e reenvia/revoga esses convites;
mudar papel, desativar/reativar membro e exigir MFA são só do proprietário. Tudo pela
empresa da sessão (``get_or_404``): membro ou convite de outra empresa → 404.
"""

from __future__ import annotations

from flask import Blueprint, abort, flash, g, make_response, redirect, render_template, request, url_for
from flask_login import current_user, logout_user

from app.blueprints.auth import _limit, no_referrer, safe_next, start_session
from app.extensions import db, limiter
from app.forms_accounts import AcceptInviteNewForm, InviteForm, RoleForm, TokenActionForm
from app.models import ROLE_OWNER, ROLE_SUPERVISOR, Company, Invitation, Membership
from app.services import accounts
from app.services import audit_accounts as audit
from app.services.accounts import AccountError
from app.tenancy import get_or_404, tenant_required

bp = Blueprint("team", __name__)


def _page(status: int = 200, invite_form: InviteForm | None = None, error: str | None = None):
    company = g.company
    members = accounts.list_members(company.id)
    return render_template(
        "team/users.html",
        members=members,
        invites=accounts.list_pending_invites(company.id),
        invite_form=invite_form or InviteForm(formdata=None),
        action_form=TokenActionForm(formdata=None),
        seats=accounts.seats_used(company.id),
        max_users=accounts.max_users_for(company.id),
        is_owner=g.membership.role == ROLE_OWNER,
        can_require_mfa=accounts.plan_allows_mfa_requirement(company.id),
        error=error,
    ), status


@bp.get("/app/usuarios")
@tenant_required(ROLE_SUPERVISOR)
def users():
    return _page()


@bp.post("/app/usuarios/convidar")
@tenant_required(ROLE_SUPERVISOR)
@limiter.limit(_limit("INVITE_RATE_LIMIT"))
def invite():
    form = InviteForm()
    if form.validate_on_submit():
        try:
            accounts.invite(g.company, g.membership, form.email.data, form.role.data)
        except AccountError as exc:
            return _page(400, invite_form=form, error=str(exc))
        flash(f"Convite enviado para {form.email.data}.", "sucesso")
        return redirect(url_for("team.users"), code=303)
    return _page(400, invite_form=form)


def _invite_action(invitation_id, action):
    invitation = get_or_404(Invitation, invitation_id)
    try:
        action(g.company, g.membership, invitation)
    except AccountError as exc:
        return _page(400, error=str(exc))
    return None


@bp.post("/app/usuarios/convites/<uuid:invitation_id>/reenviar")
@tenant_required(ROLE_SUPERVISOR)
@limiter.limit(_limit("INVITE_RATE_LIMIT"))
def resend_invite(invitation_id):
    failed = _invite_action(invitation_id, accounts.resend_invite)
    if failed:
        return failed
    flash("Convite reenviado (vale por mais 7 dias).", "sucesso")
    return redirect(url_for("team.users"), code=303)


@bp.post("/app/usuarios/convites/<uuid:invitation_id>/revogar")
@tenant_required(ROLE_SUPERVISOR)
def revoke_invite(invitation_id):
    failed = _invite_action(invitation_id, accounts.revoke_invite)
    if failed:
        return failed
    flash("Convite cancelado.", "info")
    return redirect(url_for("team.users"), code=303)


@bp.post("/app/usuarios/<uuid:membership_id>/papel")
@tenant_required(ROLE_OWNER)
def change_role(membership_id):
    member = get_or_404(Membership, membership_id)
    form = RoleForm()
    if not form.validate_on_submit():
        return _page(400, error="Escolha um papel válido.")
    try:
        accounts.change_role(member, form.role.data)
    except AccountError as exc:
        return _page(400, error=str(exc))
    flash(f"Papel de {member.user.name} atualizado.", "sucesso")
    return redirect(url_for("team.users"), code=303)


@bp.post("/app/usuarios/<uuid:membership_id>/desativar")
@tenant_required(ROLE_OWNER)
def deactivate(membership_id):
    member = get_or_404(Membership, membership_id)
    try:
        accounts.deactivate_member(member)
    except AccountError as exc:
        return _page(400, error=str(exc))
    flash(f"{member.user.name} foi desativado e perdeu o acesso.", "info")
    return redirect(url_for("team.users"), code=303)


@bp.post("/app/usuarios/<uuid:membership_id>/reativar")
@tenant_required(ROLE_OWNER)
def reactivate(membership_id):
    member = get_or_404(Membership, membership_id)
    try:
        accounts.reactivate_member(member)
    except AccountError as exc:
        return _page(400, error=str(exc))
    flash(f"{member.user.name} foi reativado.", "sucesso")
    return redirect(url_for("team.users"), code=303)


@bp.post("/app/usuarios/seguranca/mfa")
@tenant_required(ROLE_OWNER)
def require_mfa():
    company = g.company
    if not accounts.plan_allows_mfa_requirement(company.id):
        return _page(403, error="Exigir MFA é um recurso do plano Empresa.")
    turn_on = request.form.get("exigir") == "1"
    if turn_on and not current_user.mfa_enabled:
        return _page(400, error="Ative a verificação em duas etapas na sua conta antes de exigir dos proprietários.")
    company.mfa_required = turn_on
    audit.record(company.id, "company.mfa_required", "company", company.id, {"value": turn_on})
    db.session.commit()
    flash("Exigência de MFA para proprietários " + ("ligada." if turn_on else "desligada."), "sucesso")
    return redirect(url_for("team.users"), code=303)


# --------------------------------------------------------------------------- aceite


def _accept_page(invitation, state, status=200, **ctx):
    response = make_response(render_template("team/accept.html", invitation=invitation, state=state, **ctx), status)
    return no_referrer(response)


@bp.route("/convite/<token>", methods=["GET", "POST"])
@limiter.limit(_limit("INVITE_RATE_LIMIT"), methods=["POST"])
def accept_invite(token: str):
    invitation, state = accounts.lookup_invitation(token)
    if state != accounts.VALID:
        return _accept_page(None, state, 400)
    company_name = db.session.get(Company, invitation.company_id).name
    existing = accounts.find_user_by_email(invitation.email)
    if current_user.is_authenticated:
        form = TokenActionForm()
        if request.method == "POST" and form.validate_on_submit():
            try:
                membership = accounts.accept_invite_existing(invitation, current_user)
            except AccountError as exc:
                return _accept_page(invitation, state, 400, company_name=company_name, error=str(exc), form=form, mode="logged")
            from app.tenancy import set_company

            set_company(membership)
            flash(f"Bem-vindo a {company_name}!", "sucesso")
            return no_referrer(redirect(url_for("app.projects"), code=303))
        mismatch = accounts.normalize_email(current_user.email) != invitation.email
        return _accept_page(invitation, state, company_name=company_name, form=form, mode="logged", mismatch=mismatch)
    if existing is not None:
        # Conta já existe: entra e volta para cá (o `next` é caminho interno).
        login_url = url_for("auth.login", next=safe_next(request.path))
        return _accept_page(invitation, state, company_name=company_name, mode="login", login_url=login_url)
    form = AcceptInviteNewForm()
    if form.validate_on_submit():
        try:
            result = accounts.accept_invite_new(invitation, form.name.data, form.password.data)
        except AccountError as exc:
            return _accept_page(invitation, state, 400, company_name=company_name, error=str(exc), form=form, mode="new")
        logout_user()
        start_session(result.user)
        from app.tenancy import set_company

        set_company(result.membership)
        flash(f"Conta criada. Bem-vindo a {company_name}!", "sucesso")
        return no_referrer(redirect(url_for("app.projects"), code=303))
    status = 400 if request.method == "POST" else 200
    return _accept_page(invitation, state, status, company_name=company_name, form=form, mode="new")
