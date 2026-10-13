"""Páginas só para desenvolvimento. /estilo mostra tokens e componentes (design-system.md).

A rota existe em todos os ambientes, mas responde 404 fora de development (mesma resposta de
uma página inexistente), para não expor nada em produção.
"""

from __future__ import annotations

from flask import Blueprint, abort, current_app, render_template
from wtforms import EmailField, Form, IntegerField, PasswordField, SelectField, StringField, TextAreaField

bp = Blueprint("dev", __name__)

COLOR_TOKENS = [
    "bg", "surface", "surface-2", "text", "text-muted", "border", "border-subtle",
    "primary", "primary-hover", "primary-contrast", "primary-subtle", "accent", "accent-contrast",
    "success", "success-subtle", "warning", "warning-subtle", "danger", "danger-hover",
    "danger-contrast", "danger-subtle", "neutral", "neutral-subtle", "focus",
    "inverse-surface", "inverse-text", "track",
]
FONT_SIZES = [("sm", "14 px"), ("md", "16 px"), ("lg", "20 px"), ("xl", "24 px"), ("2xl", "32 px"), ("3xl", "48 px")]
SPACES = list(range(1, 13))
RADII = ["sm", "md", "lg", "pill"]
SHADOWS = ["1", "2", "3"]


class _DemoForm(Form):
    """Formulário de vitrine (sem CSRF: não é enviado a lugar nenhum)."""

    name = StringField("Nome do projeto")
    email = EmailField("E-mail")
    password = PasswordField("Senha")
    product = StringField("Produto")
    quantity = IntegerField("Quantidade de unidades")
    notes = TextAreaField("Observações")
    role = SelectField("Papel", choices=[("operator", "Operador"), ("supervisor", "Supervisor")])
    disabled = StringField("Somente leitura")


@bp.get("/estilo")
def style_guide():
    if current_app.config.get("ENV_NAME") != "development":
        abort(404)
    form = _DemoForm(data={"name": "Lote 2026-017", "email": "ana@exemplo", "disabled": "Metalúrgica Exemplo Ltda."})
    form.email.errors = ["Informe um e-mail válido, ex.: ana@empresa.com.br"]
    stages = [
        {"label": "Preparação de chassi", "value": 1.0, "max": 1, "text": "100%", "done": True},
        {"label": "Montagem mecânica", "value": 0.82, "max": 1, "text": "82%"},
        {"label": "Instalação elétrica", "value": 0.51, "max": 1, "text": "51%"},
        {"label": "Testes funcionais", "value": 0.20, "max": 1, "text": "20%"},
        {"label": "Embalagem e expedição", "value": 0.10, "max": 1, "text": "10%"},
    ]
    per_day = [
        {"label": "07/10", "value": 9}, {"label": "08/10", "value": 6}, {"label": "09/10", "value": 7},
        {"label": "12/10", "value": 3}, {"label": "13/10", "value": 9},
    ]
    return render_template(
        "dev/estilo.html",
        form=form,
        color_tokens=COLOR_TOKENS,
        font_sizes=FONT_SIZES,
        spaces=SPACES,
        radii=RADII,
        shadows=SHADOWS,
        stages=stages,
        per_day=per_day,
    )
