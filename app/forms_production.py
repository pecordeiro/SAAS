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
    RadioField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import AnyOf, DataRequired, InputRequired, Length, NumberRange, Optional, ValidationError

from app.forms import BaseForm, ProjectForm, StageSlotForm, _strip
from app.models import PROGRESS_DETAILED, PROGRESS_SIMPLE
from app.services.projects import SIMPLE_DEFAULT_MINUTES, NewActivity, NewStage

MAX_TEMPLATE_STAGES = 60


class ProjectFromTemplateForm(ProjectForm):
    """Novo projeto: com modelo (cópia da versão atual) ou digitando as etapas.

    R4: sem modelo, o projeto começa no modo SIMPLES (padrão; a etapa recebe o % direto e as
    atividades ficam opcionais: uma linha só, que dá o tempo da etapa). Com modelo, o projeto
    é detalhado (o modelo traz as subatividades)."""

    template_id = SelectField("Modelo de etapas", choices=[], validate_choice=False, default="")
    progress_mode = RadioField(
        "Como lançar o progresso",
        choices=[(PROGRESS_SIMPLE, "Simples"), (PROGRESS_DETAILED, "Detalhado")],
        validate_choice=False,  # a tela marca “Simples”; POST sem o campo (API/testes antigos) = detalhado
    )

    @property
    def chosen_mode(self) -> str:
        if self.template_id.data:
            return PROGRESS_DETAILED
        return PROGRESS_SIMPLE if self.progress_mode.data == PROGRESS_SIMPLE else PROGRESS_DETAILED

    def validate(self, extra_validators=None):
        simple = self.chosen_mode == PROGRESS_SIMPLE
        for slot in self.stages:
            slot.form.allow_without_activities = simple
        return super().validate(extra_validators)

    def validate_stages(self, field):
        if self.template_id.data:
            return  # etapas vêm do modelo
        super().validate_stages(field)

    def new_stages(self) -> list[NewStage]:
        stages = super().new_stages()
        if self.chosen_mode != PROGRESS_SIMPLE:
            return stages
        return [
            NewStage(
                name=s.name,
                activities=[NewActivity(name=s.name, ideal_minutes=s.activities[0].ideal_minutes if s.activities else SIMPLE_DEFAULT_MINUTES)],
                checklist=s.checklist,
                checklist_required=s.checklist_required,
            )
            for s in stages
        ]


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


class RestoreForm(BaseForm):
    """R8 — confirmar a restauração: o instante digitado (fuso da empresa) e o token da prévia
    (assinatura do estado mostrado; diferente do atual → 409)."""

    ate = StringField("Data e hora", filters=[_strip], validators=[DataRequired(), Length(max=16)])
    token = HiddenField(validators=[DataRequired(), Length(max=64)])
    confirm = BooleanField("Confirmo", validators=[DataRequired(message="Marque a confirmação.")])


class TemplateForm(BaseForm):
    name = StringField("Nome do modelo", filters=[_strip], validators=[DataRequired(), Length(max=160)])
    description = TextAreaField("Descrição", filters=[_strip], validators=[Optional(), Length(max=2000)])
    stages = FieldList(FormField(StageSlotForm), min_entries=1, max_entries=MAX_TEMPLATE_STAGES)

    def validate_stages(self, field):
        if not any(slot.form.name.data for slot in field):
            raise ValidationError("Inclua pelo menos uma etapa.")

    def new_stages(self) -> list[NewStage]:
        return [
            NewStage(
                name=slot.form.name.data,
                activities=slot.form.parsed,
                checklist=getattr(slot.form, "parsed_checklist", []),
                checklist_required=bool(slot.form.checklist_required.data),
            )
            for slot in self.stages
            if slot.form.name.data
        ]


class ImportForm(BaseForm):
    file = FileField("Arquivo (.csv ou .xlsx)")
    name = StringField("Nome do projeto", filters=[_strip], validators=[Optional(), Length(max=160)])
    # R7: mesmo num formato reconhecido sozinho, a pessoa pode preferir escolher as colunas.
    map_columns = BooleanField("Quero escolher as colunas")


def _column_choice(label: str) -> SelectField:
    return SelectField(label, choices=[], validate_choice=False, default="")


class ImportMapForm(BaseForm):
    """R7 — etapa 2 da importação com mapeamento. ``grid`` é a planilha lida na etapa 1,
    ASSINADA (empresa + usuário + validade); os campos de coluna levam o índice (0-based) ou
    vazio (“não usar”). Os nomes dos campos são as chaves de ``import_mapping.FIELDS``."""

    grid = HiddenField(validators=[DataRequired()])
    current_sheet = HiddenField()
    sheet = SelectField("Aba", choices=[], validate_choice=False)
    header_row = IntegerField("Linha do cabeçalho", validators=[Optional(), NumberRange(min=1, max=5000)])
    etapa = _column_choice("Etapa")
    subatividade = _column_choice("Subatividade")
    tempo = _column_choice("Tempo ideal (min)")
    previstas = _column_choice("Previstas (meta)")
    concluidas = _column_choice("Concluídas (peças)")
    percentual = _column_choice("% concluído")
    prazo = _column_choice("Prazo (data)")
    quantity = IntegerField("Meta (unidades previstas)", validators=[Optional(), NumberRange(min=1, max=100000)])
    name = StringField("Nome do projeto", filters=[_strip], validators=[Optional(), Length(max=160)])
    # Botões ``name="action"``: “ver” relê a aba/cabeçalho; “previa” (padrão) gera a prévia.
    action = StringField(validators=[Optional(), AnyOf(["previa", "ver"])])


class ImportManyForm(BaseForm):
    """R7 — arquivo com vários projetos: ``payload`` = lista assinada (empresa + usuário + 1 h)
    dos projetos lidos; os escolhidos vêm em ``pick`` (índices, lidos de ``request.form``)."""

    payload = HiddenField(validators=[DataRequired()])


class ImportConfirmForm(BaseForm):
    payload = HiddenField(validators=[DataRequired()])
    name = StringField("Nome do projeto", filters=[_strip], validators=[Optional(), Length(max=160)])
