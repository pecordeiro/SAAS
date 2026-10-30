"""Regras de conta e equipe (Fase 5): cadastro, confirmação de e-mail, reset de senha,
convites, membros, perfil e sessões.

Tokens: ver ``app/services/tokens.py`` (só o SHA-256 no banco, uso único, expiração).
Mensagens de erro em português vão direto para a tela (``AccountError``).

RLS (ADR-0003): confirmação de e-mail e reset de senha só tocam tabelas globais
(``users``, ``email_confirmations``, ``password_resets`` — sem RLS), então funcionam com
RLS ligado. O convite é lido pelo hash do token com a política ``invitations_by_token``
(``rls.set_context(token_hash=...)``); depois de achado, a empresa do convite vira o
contexto para gravar o vínculo.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta

from flask import has_request_context
from flask_login import current_user
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app import rls
from app.extensions import db
from app.models import (
    ROLE_LEVEL,
    ROLE_OWNER,
    ROLE_SUPERVISOR,
    ROLES,
    Company,
    EmailConfirmation,
    Invitation,
    Membership,
    PasswordReset,
    Subscription,
    User,
)
from app.services import audit, entitlements
from app.services.email import external_url, send_template
from app.services.passwords import hash_password, verify_password
from app.models.billing import SUB_TRIALING
from app.services.tokens import aware, hash_token, is_expired, looks_valid, new_token, utcnow

CONFIRMATION_TTL = timedelta(hours=24)
UNCONFIRMED_GRACE = timedelta(days=7)
RESET_TTL = timedelta(hours=1)
INVITE_TTL = timedelta(days=7)

# Estados de um token apresentado.
VALID = "valid"
EXPIRED = "expired"
USED = "used"
INVALID = "invalid"


class AccountError(Exception):
    """Regra de negócio violada; a mensagem vai para a tela."""


def normalize_email(email: str | None) -> str:
    return (email or "").strip().lower()


def find_user_by_email(email: str) -> User | None:
    return db.session.execute(select(User).where(func.lower(User.email) == normalize_email(email))).scalar_one_or_none()


def bump_session_version(user: User) -> None:
    """Derruba todas as sessões abertas do usuário (o id da sessão leva a versão)."""
    user.session_version = (user.session_version or 1) + 1


# --------------------------------------------------------------------------- cadastro


def signup(company_name: str, name: str, email: str, password: str) -> None:
    """Cria empresa + owner e manda a confirmação. E-mail já cadastrado: a MESMA resposta para
    quem chama (nada de erro) e um aviso vai para o dono da conta. O hash da senha é calculado
    nos dois caminhos para o tempo de resposta não denunciar o cadastro."""
    email = normalize_email(email)
    password_hash = hash_password(password)
    existing = find_user_by_email(email)
    if existing is not None:
        _notify_signup_attempt(existing)
        return
    company = Company(name=company_name)
    user = User(email=email, name=name, password_hash=password_hash)
    db.session.add_all([company, user])
    db.session.flush()
    # RLS: o vínculo novo só pode ser gravado com a empresa recém-criada no contexto.
    rls.set_context(company_id=company.id, user_id=user.id)
    db.session.add(Membership(company_id=company.id, user_id=user.id, role=ROLE_OWNER))
    _start_trial(company)
    try:
        db.session.flush()
    except IntegrityError:  # corrida: outro cadastro com o mesmo e-mail entre a busca e o insert
        db.session.rollback()
        existing = find_user_by_email(email)
        if existing is not None:
            _notify_signup_attempt(existing)
        return
    send_email_confirmation(user, email)
    db.session.commit()


def _start_trial(company: Company) -> None:
    """Teste grátis: assinatura trialing de TRIAL_DAYS no plano de teste (DEFAULT_TRIAL_PLAN,
    só Essencial ou Profissional; Etapa B). O provedor de verdade (Asaas) entra na Fase 8."""
    from flask import current_app

    from app.services.entitlements import trial_plan

    plan = trial_plan()
    db.session.add(
        Subscription(
            company_id=company.id,
            plan_id=plan.id,
            provider="fake",
            status=SUB_TRIALING,
            trial_ends_at=utcnow() + timedelta(days=int(current_app.config.get("TRIAL_DAYS", 14))),
        )
    )


def _notify_signup_attempt(user: User) -> None:
    send_template(
        user.email,
        "Tentativa de cadastro com o seu e-mail",
        "signup_existing",
        name=user.name,
        login_url=external_url("auth.login"),
        reset_url=external_url("auth.forgot_password"),
    )


# --------------------------------------------------------------------------- confirmação


def send_email_confirmation(user: User, email: str | None = None) -> None:
    """Gera token (24 h) para confirmar ``email`` (o atual ou um novo, na troca) e envia."""
    email = normalize_email(email or user.email)
    token, token_hash = new_token()
    db.session.add(
        EmailConfirmation(user_id=user.id, email=email, token_hash=token_hash, expires_at=utcnow() + CONFIRMATION_TTL)
    )
    db.session.flush()
    send_template(
        email,
        "Confirme seu e-mail" if email == normalize_email(user.email) else "Confirme seu novo e-mail",
        "confirm_email",
        name=user.name,
        url=external_url("account.confirm_email", token=token),
        change=email != normalize_email(user.email),
    )


def needs_confirmation(user: User) -> bool:
    """Sem confirmação o acesso vale 7 dias desde o cadastro; depois, só confirmando."""
    if user.email_confirmed_at is not None:
        return False
    created = aware(user.created_at) or utcnow()
    return utcnow() - created > UNCONFIRMED_GRACE


def _lookup(model, token: str | None):
    if not looks_valid(token):
        return None, INVALID
    row = db.session.execute(select(model).where(model.token_hash == hash_token(token))).scalar_one_or_none()
    if row is None:
        return None, INVALID
    if row.used_at is not None:
        return row, USED
    if is_expired(row.expires_at):
        return row, EXPIRED
    return row, VALID


def check_confirmation(token: str | None) -> str:
    return _lookup(EmailConfirmation, token)[1]


def confirm_email(token: str | None) -> tuple[str, User | None]:
    """Consome o token. Devolve (estado, usuário). Troca de e-mail: aplica o novo endereço."""
    row, state = _lookup(EmailConfirmation, token)
    if state != VALID:
        return state, None
    # Trava a linha (PostgreSQL): dois cliques simultâneos não consomem o mesmo token.
    row = db.session.execute(
        select(EmailConfirmation).where(EmailConfirmation.id == row.id, EmailConfirmation.used_at.is_(None)).with_for_update()
    ).scalar_one_or_none()
    if row is None:
        return USED, None
    user = db.session.get(User, row.user_id)
    if user is None or not user.active:
        return INVALID, None
    now = utcnow()
    new_email = normalize_email(row.email)
    if new_email != normalize_email(user.email):
        other = find_user_by_email(new_email)
        if other is not None and other.id != user.id:
            row.used_at = now
            db.session.commit()
            raise AccountError("Este e-mail já está em uso por outra conta.")
        old_email = user.email
        user.email = new_email
        send_template(old_email, "Seu e-mail de acesso foi trocado", "email_changed", name=user.name, new_email=new_email)
    user.email_confirmed_at = now
    # Uso único: este e os demais pendentes do usuário deixam de valer.
    for pending in db.session.execute(
        select(EmailConfirmation).where(EmailConfirmation.user_id == user.id, EmailConfirmation.used_at.is_(None))
    ).scalars():
        pending.used_at = now
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise AccountError("Este e-mail já está em uso por outra conta.") from None
    return VALID, user


# --------------------------------------------------------------------------- senha


def request_password_reset(email: str) -> None:
    """Sempre a mesma resposta para quem chama. Só envia se a conta existe e está ativa."""
    user = find_user_by_email(email)
    if user is None or not user.active:
        return
    token, token_hash = new_token()
    db.session.add(PasswordReset(user_id=user.id, token_hash=token_hash, expires_at=utcnow() + RESET_TTL))
    db.session.flush()
    send_template(user.email, "Redefinir a senha", "reset_password", name=user.name, url=external_url("auth.reset_password", token=token))
    db.session.commit()


def check_reset(token: str | None) -> str:
    return _lookup(PasswordReset, token)[1]


def reset_password(token: str | None, new_password: str) -> tuple[str, User | None]:
    row, state = _lookup(PasswordReset, token)
    if state != VALID:
        return state, None
    row = db.session.execute(
        select(PasswordReset).where(PasswordReset.id == row.id, PasswordReset.used_at.is_(None)).with_for_update()
    ).scalar_one_or_none()
    if row is None:
        return USED, None
    user = db.session.get(User, row.user_id)
    if user is None or not user.active:
        return INVALID, None
    now = utcnow()
    user.password_hash = hash_password(new_password)
    bump_session_version(user)  # todas as sessões abertas caem
    if user.email_confirmed_at is None:
        # O link chegou no e-mail: o reset prova a posse. Numa conta nunca confirmada, quem a
        # criou pode não ser o dono do e-mail (pre-account takeover): apaga o MFA dele e os
        # códigos de recuperação, e marca o e-mail como confirmado.
        from app.services import mfa

        mfa.disable(user)
        user.email_confirmed_at = now
        _revoke_pre_confirmation_access(user)
    for pending in db.session.execute(
        select(PasswordReset).where(PasswordReset.user_id == user.id, PasswordReset.used_at.is_(None))
    ).scalars():
        pending.used_at = now
    from app.services import lockout

    lockout.register_success(user.email)
    db.session.commit()
    send_template(user.email, "Sua senha foi trocada", "password_changed", name=user.name, reset_url=external_url("auth.forgot_password"))
    return VALID, user


def _revoke_pre_confirmation_access(user: User) -> None:
    """Fase 7 — conta tomada de volta pelo dono do e-mail (reset numa conta nunca confirmada).

    Quem cadastrou o e-mail alheio pode ter deixado acessos que sobrevivem à troca de senha
    (as sessões já caem pelo ``session_version``): tokens da API e convites pendentes das
    empresas em que a conta é proprietária. Revoga os dois e audita. Vínculos de terceiros
    que já aceitaram convite ficam visíveis em Usuários para o dono revisar (documentado em
    docs/plano/seguranca.md)."""
    from app import rls
    from app.models import ApiToken, Invitation
    from app.services import api_tokens

    rls.set_context(user_id=user.id)
    owned = list(
        db.session.execute(
            select(Membership.company_id).where(
                Membership.user_id == user.id, Membership.role == ROLE_OWNER, Membership.active.is_(True)
            )
        ).scalars()
    )
    now = utcnow()
    for company_id in owned:
        rls.set_context(company_id=company_id)
        revoked_tokens = 0
        for token in db.session.execute(
            select(ApiToken).where(ApiToken.company_id == company_id, ApiToken.revoked_at.is_(None))
        ).scalars():
            if api_tokens.revoke(token, user.id):
                revoked_tokens += 1
        revoked_invites = 0
        for invitation in db.session.execute(
            select(Invitation).where(
                Invitation.company_id == company_id,
                Invitation.used_at.is_(None),
                Invitation.revoked_at.is_(None),
            )
        ).scalars():
            invitation.revoked_at = now
            revoked_invites += 1
        if revoked_tokens or revoked_invites:
            _audit(
                audit.ACCOUNT_CLAIMED_BY_RESET,
                company_id,
                "user",
                user.id,
                {"api_tokens_revoked": revoked_tokens, "invitations_revoked": revoked_invites},
            )
        db.session.flush()
    rls.set_context(company_id=None)


def change_password(user: User, current: str, new_password: str) -> None:
    if not verify_password(user.password_hash, current):
        raise AccountError("Senha atual incorreta.")
    user.password_hash = hash_password(new_password)
    bump_session_version(user)
    db.session.commit()
    send_template(user.email, "Sua senha foi trocada", "password_changed", name=user.name, reset_url=external_url("auth.forgot_password"))


def request_email_change(user: User, password: str, new_email: str) -> None:
    """Manda a confirmação para o NOVO endereço; o e-mail só muda ao confirmar. Se o novo
    endereço já tem conta, a resposta é a mesma (sem enumerar) e o aviso vai para ele."""
    if not verify_password(user.password_hash, password):
        raise AccountError("Senha atual incorreta.")
    if user.email_confirmed_at is None:
        # Sem provar a posse do e-mail atual, a conta pode ser de quem cadastrou o e-mail
        # alheio (pre-account takeover): nada de mudar o e-mail antes de confirmar.
        raise AccountError("Confirme o seu e-mail atual antes de trocar.")
    new_email = normalize_email(new_email)
    if new_email == normalize_email(user.email):
        raise AccountError("Este já é o seu e-mail.")
    other = find_user_by_email(new_email)
    if other is not None:
        _notify_signup_attempt(other)
        return
    send_email_confirmation(user, new_email)
    db.session.commit()


# --------------------------------------------------------------------------- plano


def _pending_invites_filter(company_id: uuid.UUID):
    return (
        Invitation.company_id == company_id,
        Invitation.used_at.is_(None),
        Invitation.revoked_at.is_(None),
        Invitation.expires_at > utcnow(),
    )


def _ensure_seat(company: Company, adding: int = 1) -> None:
    """Limite de usuários do plano (vínculos ativos + convites pendentes): fonte única em
    ``entitlements.check_can_add_user`` (PlanLimitError → HTTP 402)."""
    entitlements.check_can_add_user(company, adding=adding)


def _audit(action, company_id, object_type=None, object_id=None, details=None, actor_user_id=None):
    if actor_user_id is None and has_request_context() and current_user.is_authenticated:
        actor_user_id = current_user.id
    audit.record(
        action, company_id=company_id, actor_user_id=actor_user_id, object_type=object_type, object_id=object_id, details=details
    )


# --------------------------------------------------------------------------- convites


def can_manage_invite_role(actor: Membership, role: str) -> bool:
    """Owner convida qualquer papel; supervisor convida supervisor/operador (nunca owner)."""
    if role not in ROLES:
        return False
    if actor.is_support:
        # Fase 7: acesso de suporte é temporário — não pode criar acesso permanente (convite).
        return False
    if actor.role == ROLE_OWNER:
        return True
    return actor.role == ROLE_SUPERVISOR and ROLE_LEVEL[role] <= ROLE_LEVEL[ROLE_SUPERVISOR]


def list_pending_invites(company_id: uuid.UUID) -> list[Invitation]:
    return list(
        db.session.execute(
            select(Invitation).where(*_pending_invites_filter(company_id)).order_by(Invitation.created_at.desc())
        ).scalars()
    )


def _send_invite(invitation: Invitation, company: Company, inviter: User, token: str) -> None:
    from app.models import ROLE_LABELS

    send_template(
        invitation.email,
        f"Convite para {company.name} na Teroz",
        "invite",
        company_name=company.name,
        inviter_name=inviter.name,
        role_label=ROLE_LABELS.get(invitation.role, invitation.role),
        url=external_url("team.accept_invite", token=token),
        expires_at=invitation.expires_at,
    )


def invite(company: Company, actor: Membership, email: str, role: str) -> Invitation:
    email = normalize_email(email)
    if not can_manage_invite_role(actor, role):
        raise AccountError("Você não pode convidar alguém com esse papel.")
    user = find_user_by_email(email)
    if user is not None:
        member = db.session.execute(
            select(Membership).where(Membership.company_id == company.id, Membership.user_id == user.id)
        ).scalar_one_or_none()
        if member is not None and member.active:
            raise AccountError("Esta pessoa já faz parte da empresa.")
        if member is not None and actor.role != ROLE_OWNER:
            # Aceitar reativaria um vínculo desativado: decisão só do proprietário.
            raise AccountError("Esta pessoa foi desativada. Só o proprietário pode convidá-la de novo.")
    pending = db.session.execute(
        select(Invitation).where(*_pending_invites_filter(company.id), Invitation.email == email)
    ).scalar_one_or_none()
    if pending is None:
        _ensure_seat(company)
    else:  # reconvidar o mesmo e-mail troca o convite pendente (não ocupa outra vaga)
        if not can_manage_invite_role(actor, pending.role):
            raise AccountError("Você não pode alterar este convite.")
        pending.revoked_at = utcnow()
    token, token_hash = new_token()
    invitation = Invitation(
        company_id=company.id,
        email=email,
        role=role,
        token_hash=token_hash,
        invited_by_user_id=actor.user_id,
        expires_at=utcnow() + INVITE_TTL,
    )
    db.session.add(invitation)
    db.session.flush()
    _audit(audit.INVITATION_CREATED, company.id, "invitation", invitation.id, {"email": email, "role": role})
    _send_invite(invitation, company, actor.user, token)
    db.session.commit()
    return invitation


def resend_invite(company: Company, actor: Membership, invitation: Invitation) -> None:
    """Novo token e novo prazo de 7 dias; o link anterior deixa de valer."""
    if invitation.used_at is not None or invitation.revoked_at is not None:
        raise AccountError("Este convite não está mais pendente.")
    if not can_manage_invite_role(actor, invitation.role):
        raise AccountError("Você não pode alterar este convite.")
    if is_expired(invitation.expires_at):
        _ensure_seat(company)  # vencido não ocupava vaga
    token, token_hash = new_token()
    invitation.token_hash = token_hash
    invitation.expires_at = utcnow() + INVITE_TTL
    _audit(audit.INVITATION_RESENT, company.id, "invitation", invitation.id, {"email": invitation.email})
    _send_invite(invitation, company, actor.user, token)
    db.session.commit()


def revoke_invite(company: Company, actor: Membership, invitation: Invitation) -> None:
    if invitation.used_at is not None or invitation.revoked_at is not None:
        raise AccountError("Este convite não está mais pendente.")
    if not can_manage_invite_role(actor, invitation.role):
        raise AccountError("Você não pode alterar este convite.")
    invitation.revoked_at = utcnow()
    _audit(audit.INVITATION_REVOKED, company.id, "invitation", invitation.id, {"email": invitation.email})
    db.session.commit()


def lookup_invitation(token: str | None) -> tuple[Invitation | None, str]:
    """Busca o convite pelo hash do token, antes de saber a empresa (política RLS por token)."""
    if not looks_valid(token):
        return None, INVALID
    token_hash = hash_token(token)
    rls.set_context(token_hash=token_hash)
    invitation = db.session.execute(select(Invitation).where(Invitation.token_hash == token_hash)).scalar_one_or_none()
    if invitation is None or invitation.revoked_at is not None:
        return None, INVALID
    if invitation.used_at is not None:
        return invitation, USED
    if is_expired(invitation.expires_at):
        return invitation, EXPIRED
    return invitation, VALID


@dataclass
class AcceptResult:
    user: User
    membership: Membership


def _consume_invitation(invitation: Invitation, user: User) -> Membership:
    # O token já provou o convite: a empresa dele vira o contexto para gravar o vínculo.
    rls.set_context(company_id=invitation.company_id, user_id=user.id)
    locked = db.session.execute(
        select(Invitation).where(Invitation.id == invitation.id, Invitation.used_at.is_(None)).with_for_update()
    ).scalar_one_or_none()
    if locked is None:
        raise AccountError("Este convite já foi usado.")
    # O convite pendente já ocupa vaga (adding=0); se o plano encolheu nesse meio-tempo, 402.
    company = db.session.get(Company, invitation.company_id)
    entitlements.ensure_writable(company)  # empresa em modo leitura não ganha gente (402)
    _ensure_seat(company, adding=0)
    member = db.session.execute(
        select(Membership).where(Membership.company_id == invitation.company_id, Membership.user_id == user.id)
    ).scalar_one_or_none()
    if member is not None and member.active:
        raise AccountError("Você já faz parte desta empresa.")
    if member is None:
        member = Membership(company_id=invitation.company_id, user_id=user.id, role=invitation.role)
        db.session.add(member)
    else:
        # Reativar vínculo desativado só com convite criado por quem é proprietário ativo.
        if not _is_active_owner(invitation.company_id, invitation.invited_by_user_id):
            raise AccountError("Este convite não pode reativar o seu acesso. Fale com o proprietário da empresa.")
        member.active = True
        member.role = invitation.role
    locked.used_at = utcnow()
    db.session.flush()
    _audit(
        audit.INVITATION_ACCEPTED, invitation.company_id, "membership", member.id,
        {"email": invitation.email, "role": invitation.role}, actor_user_id=user.id,
    )
    return member


def _is_active_owner(company_id: uuid.UUID, user_id: uuid.UUID | None) -> bool:
    if user_id is None:
        return False
    return (
        db.session.execute(
            select(Membership.id).where(
                Membership.company_id == company_id,
                Membership.user_id == user_id,
                Membership.role == ROLE_OWNER,
                Membership.active.is_(True),
            )
        ).first()
        is not None
    )


def accept_invite_existing(invitation: Invitation, user: User) -> Membership:
    """Usuário logado aceita: o e-mail da conta precisa ser o do convite."""
    if normalize_email(user.email) != normalize_email(invitation.email):
        raise AccountError("Este convite foi enviado para outro e-mail. Saia e entre com a conta certa.")
    member = _consume_invitation(invitation, user)
    db.session.commit()
    return member


def accept_invite_new(invitation: Invitation, name: str, password: str) -> AcceptResult:
    """Sem conta com o e-mail do convite: cria (o e-mail já fica confirmado — o link chegou nele)."""
    if find_user_by_email(invitation.email) is not None:
        raise AccountError("Já existe conta com este e-mail. Entre para aceitar o convite.")
    user = User(email=normalize_email(invitation.email), name=name, password_hash=hash_password(password), email_confirmed_at=utcnow())
    db.session.add(user)
    db.session.flush()
    member = _consume_invitation(invitation, user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise AccountError("Já existe conta com este e-mail. Entre para aceitar o convite.") from None
    return AcceptResult(user=user, membership=member)


# --------------------------------------------------------------------------- membros


def list_members(company_id: uuid.UUID) -> list[Membership]:
    return list(
        db.session.execute(
            select(Membership)
            .join(User, User.id == Membership.user_id)
            .where(Membership.company_id == company_id)
            .order_by(Membership.active.desc(), User.name)
        ).scalars()
    )


def _active_owner_ids(company_id: uuid.UUID) -> list[uuid.UUID]:
    # FOR UPDATE: duas mudanças simultâneas não removem os dois últimos owners (PostgreSQL).
    return list(
        db.session.execute(
            select(Membership.id)
            .where(Membership.company_id == company_id, Membership.role == ROLE_OWNER, Membership.active.is_(True))
            .with_for_update()
        ).scalars()
    )


def _guard_last_owner(member: Membership) -> None:
    if member.role == ROLE_OWNER and member.active:
        owners = _active_owner_ids(member.company_id)
        if owners == [member.id] or len(owners) <= 1:
            raise AccountError("A empresa precisa de pelo menos um proprietário ativo.")


def change_role(member: Membership, role: str) -> None:
    if role not in ROLES:
        raise AccountError("Papel inválido.")
    if role == member.role:
        return
    if role == ROLE_OWNER and member.is_support:
        raise AccountError("Acesso de suporte não pode virar proprietário.")
    if role != ROLE_OWNER:
        _guard_last_owner(member)
    old = member.role
    member.role = role
    _audit(audit.ROLE_CHANGED, member.company_id, "membership", member.id, {"from": old, "to": role})
    db.session.commit()


def deactivate_member(member: Membership) -> None:
    """Desativa o vínculo: na próxima requisição a pessoa perde a empresa (tenancy confere o
    vínculo a cada requisição). Se não sobrar nenhum vínculo ativo, as sessões dela caem."""
    if not member.active:
        return
    _guard_last_owner(member)
    member.active = False
    others = db.session.execute(
        select(func.count()).select_from(Membership).where(
            Membership.user_id == member.user_id, Membership.active.is_(True), Membership.id != member.id
        )
    ).scalar_one()
    if not others:
        bump_session_version(member.user)
    # Etapa D: quem sai da equipe deixa de ser responsável pelas atividades desta empresa.
    from app.services.projects import clear_assignments

    cleared = clear_assignments(member.company_id, member.user_id)
    _audit(
        audit.MEMBER_DEACTIVATED, member.company_id, "membership", member.id,
        {"user_id": str(member.user_id), "assignments_cleared": cleared},
    )
    db.session.commit()


def reactivate_member(member: Membership) -> None:
    if member.active:
        return
    _ensure_seat(db.session.get(Company, member.company_id))
    member.active = True
    _audit(audit.MEMBER_REACTIVATED, member.company_id, "membership", member.id, {"user_id": str(member.user_id)})
    db.session.commit()


def active_memberships(user_id: uuid.UUID) -> list[Membership]:
    rls.set_context(user_id=user_id)
    return list(
        db.session.execute(
            select(Membership)
            .join(Company, Company.id == Membership.company_id)
            .where(Membership.user_id == user_id, Membership.usable())
            .order_by(Company.name)
        ).scalars()
    )
