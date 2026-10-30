"""Configurações da empresa (/app/empresa) — só o proprietário (telas.md §13).

Dados (nome, CNPJ), calendário (jornada, dias de trabalho) e feriados da empresa. A empresa
é SEMPRE a da sessão; o id do feriado é resolvido nela (de outra empresa, ou nacional → 404).

R6 (ADR-0017): Configurações › Módulos (``/app/empresa/modulos``) liga e desliga os módulos
opcionais da empresa da sessão. Só o proprietário; cada mudança vai para ``audit_logs``.
"""

from __future__ import annotations

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.forms import BaseForm
from app.forms_company import CompanyForm, HolidayForm
from app.models import ROLE_OWNER, Holiday
from app.services import company as svc
from app.services import entitlements, modules
from app.tenancy import get_or_404, tenant_required

bp = Blueprint("empresa", __name__, url_prefix="/app/empresa")


def _page(form: CompanyForm, holiday_form: HolidayForm | None = None, *, status: int = 200, error: str | None = None,
          holiday_error: str | None = None):
    return (
        render_template(
            "empresa/settings.html",
            form=form,
            holiday_form=holiday_form or HolidayForm(formdata=None),
            holidays=svc.list_company_holidays(),
            national=svc.upcoming_national_holidays(),
            weekdays=svc.WEEKDAYS,
            selected_days=set(form.workdays.data or []),
            error=error,
            holiday_error=holiday_error,
        ),
        status,
    )


@bp.route("", methods=["GET", "POST"])
@tenant_required(ROLE_OWNER)
def settings():
    company = g.company
    probe = CompanyForm()
    if probe.is_submitted():
        form = probe
    else:
        form = CompanyForm(
            formdata=None,
            data={
                "name": company.name,
                "cnpj": company.cnpj or "",
                "daily_hours": company.daily_hours,
                "workdays": list(company.workdays()),
                "stalled_days": company.stalled_days,
            },
        )
    if form.validate_on_submit():
        try:
            svc.update_company(
                company,
                name=form.name.data,
                cnpj=form.cnpj.data,
                daily_hours=form.daily_hours.data,
                workdays=form.workdays.data or [],
                user_id=current_user.id,
                # R6: “etapa parada” é do módulo de alertas; desligado, o campo some e o valor fica.
                stalled_days=form.stalled_days.data if modules.is_enabled(company, modules.ALERTAS) else None,
            )
        except svc.CompanyError as exc:
            db.session.rollback()
            return _page(form, status=400, error=str(exc))
        db.session.commit()
        flash("Dados da empresa salvos.", "sucesso")
        return redirect(url_for("empresa.settings"), 303)
    return _page(form, status=400 if form.is_submitted() else 200)


@bp.post("/feriados")
@tenant_required(ROLE_OWNER)
def holiday_add():
    holiday_form = HolidayForm()
    if holiday_form.validate_on_submit():
        try:
            svc.add_holiday(g.company, holiday_form.day.data, holiday_form.name.data, current_user.id)
        except svc.CompanyError as exc:
            db.session.rollback()
            return _page(CompanyForm(formdata=None, data=_company_data()), holiday_form, status=400, holiday_error=str(exc))
        db.session.commit()
        flash("Feriado incluído.", "sucesso")
        return redirect(url_for("empresa.settings", _anchor="calendario"), 303)
    return _page(CompanyForm(formdata=None, data=_company_data()), holiday_form, status=400)


@bp.post("/feriados/<uuid:holiday_id>/remover")
@tenant_required(ROLE_OWNER)
def holiday_remove(holiday_id):
    holiday = get_or_404(Holiday, holiday_id)  # outra empresa ou nacional (company_id NULL) → 404
    svc.remove_holiday(holiday, current_user.id)
    db.session.commit()
    flash("Feriado removido.", "sucesso")
    return redirect(url_for("empresa.settings", _anchor="calendario"), 303)


def _company_data() -> dict:
    company = g.company
    return {
        "name": company.name,
        "cnpj": company.cnpj or "",
        "daily_hours": company.daily_hours,
        "workdays": list(company.workdays()),
        "stalled_days": company.stalled_days,
    }


# ---------------------------------------------------------------- módulos opcionais (R6)


class ModulesForm(BaseForm):
    """Só o CSRF: as chaves vêm como caixas ``modulo`` (valor = chave do módulo)."""


def _modules_page(*, status: int = 200, error: str | None = None):
    company = g.company
    on = modules.enabled_keys(company)
    plan = entitlements.effective_plan(company)
    items = [
        {
            "module": m,
            "enabled": m.key in on,
            # Recurso do plano (ex.: API): ligar o módulo não libera o que o plano não tem.
            "plan_missing": bool(m.plan_feature) and not entitlements.has_feature(company, m.plan_feature),
        }
        for m in modules.available()
    ]
    return (
        render_template("empresa/modulos.html", items=items, plan=plan, form=ModulesForm(formdata=None), error=error),
        status,
    )


@bp.route("/modulos", methods=["GET", "POST"], endpoint="modules")
@tenant_required(ROLE_OWNER)
def modules_settings():
    """Liga/desliga os módulos opcionais. O estado enviado é o estado inteiro: caixa marcada =
    ligado, desmarcada = desligado. Chave desconhecida ou indisponível → 400."""
    if request.method == "GET":
        return _modules_page()
    form = ModulesForm()
    if not form.validate_on_submit():
        abort(400)
    chosen = set(request.form.getlist("modulo"))
    available = [m.key for m in modules.available()]
    if chosen - set(available):
        return _modules_page(status=400, error="Módulo desconhecido. Recarregue a página e tente de novo.")
    try:
        changed = modules.set_modules(g.company, {k: k in chosen for k in available}, current_user.id)
    except modules.ModuleError:
        db.session.rollback()
        return _modules_page(status=400, error="Módulo desconhecido. Recarregue a página e tente de novo.")
    db.session.commit()
    if not changed:
        flash("Nada mudou nos módulos.", "info")
    else:
        names = ", ".join(f"{modules.BY_KEY[k].name} ({'ligado' if on else 'desligado'})" for k, on in changed)
        flash(f"Módulos salvos: {names}.", "sucesso")
    return redirect(url_for("empresa.modules"), 303)
