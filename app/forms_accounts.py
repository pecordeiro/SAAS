"""Formulários da Fase 5 (contas, equipe, MFA). Separados de forms.py para não colidir
com a Fase 4."""

from __future__ import annotations

from wtforms import EmailField, HiddenField, PasswordField, RadioField, StringField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from app.forms import BaseForm, _strip
from app.models import ROLE_OPERATOR, ROLE_OWNER, ROLE_SUPERVISOR


def _lower(value):
    return value.lower() if isinstance(value, str) else value


def _email_field(label: str = "E-mail") -> EmailField:
    return EmailField(
        label,
        filters=[_strip, _lower],
        validators=[DataRequired(), Email(check_deliverability=False), Length(max=254)],
    )


def _new_password(label: str = "Nova senha") -> PasswordField:
    return PasswordField(label, validators=[DataRequired(), Length(min=10, max=128)])


def _confirm(label: str = "Repita a nova senha", target: str = "password") -> PasswordField:
    return PasswordField(label, validators=[DataRequired(), EqualTo(target, message="As senhas não conferem.")])


class ForgotPasswordForm(BaseForm):
    email = _email_field()


class ResetPasswordForm(BaseForm):
    password = _new_password()
    password_confirm = _confirm()


class MfaLoginForm(BaseForm):
    code = StringField("Código", filters=[_strip], validators=[DataRequired(), Length(max=20)])


class TokenActionForm(BaseForm):
    """Só CSRF: confirmar e-mail, aceitar convite logado, ações por botão."""


class ProfileNameForm(BaseForm):
    name = StringField("Nome", filters=[_strip], validators=[DataRequired(), Length(max=120)])


class ProfileEmailForm(BaseForm):
    email = _email_field("Novo e-mail")
    current_password = PasswordField("Senha atual", validators=[DataRequired(), Length(max=128)])


class ProfilePasswordForm(BaseForm):
    current_password = PasswordField("Senha atual", validators=[DataRequired(), Length(max=128)])
    password = _new_password()
    password_confirm = _confirm()


class MfaSetupForm(BaseForm):
    code = StringField("Código de 6 dígitos", filters=[_strip], validators=[DataRequired(), Length(min=6, max=7)])


class MfaDisableForm(BaseForm):
    current_password = PasswordField("Senha atual", validators=[DataRequired(), Length(max=128)])
    code = StringField("Código do aplicativo ou de recuperação", filters=[_strip], validators=[DataRequired(), Length(max=20)])


class MfaRegenerateForm(BaseForm):
    current_password = PasswordField("Senha atual", validators=[DataRequired(), Length(max=128)])


ROLE_CHOICES = [
    (ROLE_OPERATOR, "Operador — registra peças"),
    (ROLE_SUPERVISOR, "Supervisor — monta projetos e exporta"),
    (ROLE_OWNER, "Proprietário — tudo, inclusive assinatura"),
]


class InviteForm(BaseForm):
    email = _email_field()
    role = RadioField("Papel", choices=ROLE_CHOICES, default=ROLE_OPERATOR, validators=[DataRequired()])


class RoleForm(BaseForm):
    role = RadioField("Papel", choices=ROLE_CHOICES, validators=[DataRequired()])


class AcceptInviteNewForm(BaseForm):
    name = StringField("Seu nome", filters=[_strip], validators=[DataRequired(), Length(max=120)])
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=10, max=128)])
    password_confirm = _confirm("Repita a senha")


class SwitchCompanyForm(BaseForm):
    company_id = HiddenField(validators=[DataRequired()])


# ---------------------------------------------------------------- Fase 7 (LGPD)


class CompanyDeletionForm(BaseForm):
    """Pedir a exclusão da empresa: senha do proprietário + nome da empresa digitado."""

    password = PasswordField("Sua senha", validators=[DataRequired(), Length(max=128)])
    company_name = StringField("Digite o nome da empresa para confirmar", filters=[_strip], validators=[DataRequired(), Length(max=120)])
