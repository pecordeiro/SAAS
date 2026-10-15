"""Formulários da Fase 4 (modelos, edição, importação). Separados de ``forms.py`` para não
misturar com contas/login. Todos herdam o CSRF do Flask-WTF."""

from __future__ import annotations

from decimal import Decimal

from flask_wtf.file import FileField
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    FieldList,
    FormField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import AnyOf, DataRequired, InputRequired, Length, NumberRange, Optional, ValidationError

from app.forms import BaseForm, ProjectForm, StageSlotForm, _strip
from app.services.projects import NewStage

MAX_TEMPLATE_STAGES = 60


class ProjectFromTemplateForm(ProjectForm):
    """Novo projeto: com modelo (cópia da versão atual) ou digitando as etapas."""

    template_id = SelectField("Modelo de etapas", choices=[], validate_choice=False, default="")

    def validate_stages(self, field):
        if self.template_id.data:
            return  # etapas vêm do modelo
        super().validate_stages(field)


class ProjectEditForm(BaseForm):
    name = StringField("Nome do projeto", filters=[_strip], validators=[DataRequired(), Length(max=160)])
    product = StringField("Produto", filters=[_strip], validators=[Optional(), Length(max=160)])
    quantity = IntegerField("Quantidade de equipamentos", validators=[InputRequired(), NumberRange(min=1, max=100000)])
    start_date = DateField("Início", validators=[Optional()])
    due_date = DateField("Prazo", validators=[Optional()])
    people = IntegerField("Pessoas na equipe", validators=[InputRequired(), NumberRange(min=1, max=1000)])
    hours_per_day = DecimalField(
        "Horas por dia", places=2, validators=[InputRequired(), NumberRange(min=Decimal("0.5"), max=Decimal("24"))]
    )

    def validate_due_date(self, field):
        if field.data and self.start_date.data and field.data < self.start_date.data:
            raise ValidationError("O prazo não pode ser antes do início.")


class RenameForm(BaseForm):
    name = StringField("Nome", filters=[_strip], validators=[DataRequired(), Length(max=160)])
    # Etapa D: versão que a tela leu (controle otimista → 409 com o valor atual).
    version = IntegerField(validators=[Optional(), NumberRange(min=1)])


class ActivityEditForm(BaseForm):
    name = StringField("Atividade", filters=[_strip], validators=[DataRequired(), Length(max=160)])
    ideal_minutes = DecimalField(
        "Tempo ideal (min)", places=2, validators=[InputRequired(), NumberRange(min=Decimal("0"), max=Decimal("100000"))]
    )
    version = IntegerField(validators=[Optional(), NumberRange(min=1)])


class AssignForm(BaseForm):
    """Etapa D: responsável da atividade. Vazio = sem responsável. O id é só uma intenção:
    o serviço confere que é membro ativo da empresa da sessão."""

    assignee_id = StringField(filters=[_strip], validators=[Optional(), Length(max=36)])


class WaitingPartForm(BaseForm):
    """Etapa F: “aguardando peça” (supervisor+). Só sinaliza; o serviço revalida tudo."""

    waiting = BooleanField("Aguardando peça")
    expected_on = DateField("Previsão de chegada", validators=[Optional()])
    note = StringField("Observação", filters=[_strip], validators=[Optional(), Length(max=140)])
    version = IntegerField(validators=[Optional(), NumberRange(min=1)])


class PositionForm(BaseForm):
    """Etapa D: mover a atividade (arrastar ou “Mover para”). O navegador só manda a
    intenção; etapa, posição e versão são conferidas no servidor."""

    stage_id = StringField(filters=[_strip], validators=[DataRequired(), Length(max=36)])
    position = IntegerField(validators=[InputRequired(), NumberRange(min=0, max=100000)])
    version = IntegerField(validators=[Optional(), NumberRange(min=1)])


class MoveForm(BaseForm):
    direction = HiddenField(validators=[AnyOf(["up", "down"])])


class ConfirmForm(BaseForm):
    """Ações destrutivas/administrativas: o POST precisa trazer confirm=1."""

    confirm = BooleanField("Confirmo", validators=[DataRequired(message="Marque a confirmação.")])
    version_id = HiddenField()


class TemplateForm(BaseForm):
    name = StringField("Nome do modelo", filters=[_strip], validators=[DataRequired(), Length(max=160)])
    description = TextAreaField("Descrição", filters=[_strip], validators=[Optional(), Length(max=2000)])
    stages = FieldList(FormField(StageSlotForm), min_entries=1, max_entries=MAX_TEMPLATE_STAGES)

    def validate_stages(self, field):
        if not any(slot.form.name.data for slot in field):
            raise ValidationError("Inclua pelo menos uma etapa.")

    def new_stages(self) -> list[NewStage]:
        return [NewStage(name=slot.form.name.data, activities=slot.form.parsed) for slot in self.stages if slot.form.name.data]


class ImportForm(BaseForm):
    file = FileField("Arquivo (.csv ou .xlsx)")
    name = StringField("Nome do projeto", filters=[_strip], validators=[Optional(), Length(max=160)])


class ImportConfirmForm(BaseForm):
    payload = HiddenField(validators=[DataRequired()])
    name = StringField("Nome do projeto", filters=[_strip], validators=[Optional(), Length(max=160)])
