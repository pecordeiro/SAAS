"""Formulários das configurações da empresa (/app/empresa)."""

from __future__ import annotations

from decimal import Decimal

from wtforms import DateField, DecimalField, IntegerField, SelectMultipleField, StringField
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, Optional

from app.forms import BaseForm, _strip
from app.services.calc import DIAS_PARADA_MAX, DIAS_PARADA_MIN
from app.services.company import WEEKDAYS


class CompanyForm(BaseForm):
    name = StringField("Nome da empresa", filters=[_strip], validators=[DataRequired(), Length(max=120)])
    cnpj = StringField("CNPJ", filters=[_strip], validators=[Optional(), Length(max=18)])
    daily_hours = DecimalField(
        "Jornada padrão (horas por dia)",
        places=2,
        default=Decimal("8"),
        validators=[InputRequired(), NumberRange(min=Decimal("0.5"), max=Decimal("24"))],
    )
    workdays = SelectMultipleField(
        "Dias de trabalho",
        coerce=int,
        choices=[(n, long) for n, _short, long in WEEKDAYS],
        default=[0, 1, 2, 3, 4],
    )
    # Etapa F: alerta “etapa parada há X dias úteis” (o serviço valida de novo). Vazio mantém
    # o valor atual (formulários antigos sem o campo continuam válidos).
    stalled_days = IntegerField(
        "Alerta de etapa parada (dias úteis sem lançamento)",
        validators=[Optional(), NumberRange(min=DIAS_PARADA_MIN, max=DIAS_PARADA_MAX)],
    )


class HolidayForm(BaseForm):
    day = DateField("Data", validators=[DataRequired(message="Informe a data do feriado.")])
    name = StringField("Nome do feriado", filters=[_strip], validators=[DataRequired(), Length(max=120)])
