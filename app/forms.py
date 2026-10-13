"""Formulários (Flask-WTF: CSRF em todo POST)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DecimalField,
    EmailField,
    FieldList,
    Form,
    FormField,
    HiddenField,
    IntegerField,
    PasswordField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, InputRequired, Length, NumberRange, Optional, ValidationError

from app.services.projects import NewActivity, NewStage

MAX_STAGE_SLOTS = 6
MAX_ACTIVITIES_PER_STAGE = 50


class BaseForm(FlaskForm):
    """Mensagens padrão do WTForms em português (com WTF_I18N_ENABLED=False na config)."""

    class Meta:
        locales = ("pt_BR", "pt")


def _strip(value):
    return value.strip() if isinstance(value, str) else value


class SignupForm(BaseForm):
    company_name = StringField("Nome da empresa", filters=[_strip], validators=[DataRequired(), Length(max=120)])
    name = StringField("Seu nome", filters=[_strip], validators=[DataRequired(), Length(max=120)])
    email = EmailField(
        "E-mail",
        filters=[_strip, lambda v: v.lower() if isinstance(v, str) else v],
        validators=[DataRequired(), Email(check_deliverability=False), Length(max=254)],
    )
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=10, max=128)])
    password_confirm = PasswordField(
        "Repita a senha", validators=[DataRequired(), EqualTo("password", message="As senhas não conferem.")]
    )


class LoginForm(BaseForm):
    email = EmailField(
        "E-mail",
        filters=[_strip, lambda v: v.lower() if isinstance(v, str) else v],
        validators=[DataRequired(), Length(max=254)],
    )
    password = PasswordField("Senha", validators=[DataRequired(), Length(max=128)])
    next = HiddenField()


class LogoutForm(BaseForm):
    pass


def parse_activities(text: str | None) -> list[NewActivity]:
    """Uma atividade por linha: ``Nome; minutos``. Linhas vazias são ignoradas."""
    activities: list[NewActivity] = []
    for number, raw_line in enumerate((text or "").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        name, sep, minutes = line.rpartition(";")
        if not sep:
            raise ValidationError(f"Linha {number}: use o formato “Nome; minutos”.")
        name = name.strip()
        if not name or len(name) > 160:
            raise ValidationError(f"Linha {number}: nome da atividade vazio ou longo demais.")
        try:
            value = Decimal(minutes.strip().replace(",", "."))
        except InvalidOperation:
            raise ValidationError(f"Linha {number}: tempo ideal inválido.") from None
        if not value.is_finite() or value < 0 or value > Decimal("100000"):
            raise ValidationError(f"Linha {number}: tempo ideal deve ficar entre 0 e 100000 minutos.")
        activities.append(NewActivity(name=name, ideal_minutes=value.quantize(Decimal("0.01"))))
    if len(activities) > MAX_ACTIVITIES_PER_STAGE:
        raise ValidationError(f"No máximo {MAX_ACTIVITIES_PER_STAGE} atividades por etapa.")
    return activities


class StageSlotForm(Form):
    class Meta:
        locales = ("pt_BR", "pt")

    name = StringField("Etapa", filters=[_strip], validators=[Optional(), Length(max=160)])
    activities = TextAreaField("Atividades (uma por linha: Nome; minutos por unidade)")

    def validate_activities(self, field):
        parsed = parse_activities(field.data)
        if parsed and not self.name.data:
            raise ValidationError("Dê um nome à etapa.")
        if self.name.data and not parsed:
            raise ValidationError("Inclua pelo menos uma atividade.")
        self.parsed = parsed


class ProjectForm(BaseForm):
    name = StringField("Nome do projeto", filters=[_strip], validators=[DataRequired(), Length(max=160)])
    quantity = IntegerField(
        "Quantidade de equipamentos", validators=[InputRequired(), NumberRange(min=1, max=100000)]
    )
    start_date = DateField("Início", validators=[Optional()])
    due_date = DateField("Prazo", validators=[Optional()])
    people = IntegerField("Pessoas montando", default=1, validators=[InputRequired(), NumberRange(min=1, max=1000)])
    hours_per_day = DecimalField(
        "Horas por dia (por pessoa)", default=Decimal("8"), places=2,
        validators=[InputRequired(), NumberRange(min=Decimal("0.5"), max=Decimal("24"))],
    )
    stages = FieldList(FormField(StageSlotForm), min_entries=MAX_STAGE_SLOTS, max_entries=MAX_STAGE_SLOTS)

    def validate_due_date(self, field):
        if field.data and self.start_date.data and field.data < self.start_date.data:
            raise ValidationError("O prazo não pode ser antes do início.")

    def validate_stages(self, field):
        if not any(slot.form.name.data for slot in field):
            raise ValidationError("Inclua pelo menos uma etapa.")

    def new_stages(self) -> list[NewStage]:
        return [
            NewStage(name=slot.form.name.data, activities=slot.form.parsed)
            for slot in self.stages
            if slot.form.name.data
        ]


class StageForm(BaseForm):
    name = StringField("Nova etapa", filters=[_strip], validators=[DataRequired(), Length(max=160)])


class ActivityForm(BaseForm):
    name = StringField("Nova atividade", filters=[_strip], validators=[DataRequired(), Length(max=160)])
    ideal_minutes = DecimalField(
        "Tempo ideal (min por unidade)", places=2,
        validators=[InputRequired(), NumberRange(min=Decimal("0"), max=Decimal("100000"))],
    )


class ProgressForm(BaseForm):
    delta = IntegerField("Peças concluídas agora", validators=[InputRequired(), NumberRange(min=1, max=100000)])
    version = IntegerField(validators=[Optional()])
