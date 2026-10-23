"""Telas de assinatura (Fase 8): assinatura atual, trocar plano (com projeção), dados de
cobrança, faturas e cancelar. Só o proprietário (owner) gerencia a cobrança: supervisor e
operador recebem 403. Todas as rotas aceitam empresa em modo leitura (é por aqui que ela
regulariza). A empresa vem só da sessão (tenancy); não há id de empresa em URL nem form.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import select
from wtforms import EmailField, HiddenField, StringField
from wtforms.validators import DataRequired, Email, Length, ValidationError

from app.extensions import db
from app.forms import BaseForm
from app.models import ROLE_OWNER, Plan
from app.services import entitlements
from app.services import plans as plan_catalog
from app.services.billing import service as billing
from app.services.billing.documents import is_valid_document
from app.services.billing.provider import PaymentProviderError
from app.tenancy import tenant_required

bp = Blueprint("billing", __name__, url_prefix="/app/assinatura")


def _strip(value):
    return value.strip() if isinstance(value, str) else value


def _document(form, field):
    if not is_valid_document(field.data):
        raise ValidationError("CPF ou CNPJ inválido: confira os números.")


class BillingInfoForm(BaseForm):
    name = StringField("Nome ou razão social", filters=[_strip], validators=[DataRequired(), Length(min=2, max=120)])
    cpf_cnpj = StringField("CPF ou CNPJ", filters=[_strip], validators=[DataRequired(), Length(max=18), _document])
    email = EmailField(
        "E-mail de cobrança",
        filters=[_strip, lambda v: v.lower() if isinstance(v, str) else v],
        validators=[DataRequired(), Email(check_deliverability=False), Length(max=254)],
    )
    plan = HiddenField()


class ConfirmForm(BaseForm):
    pass


def reais(cents) -> str:
    if cents is None:
        return "—"
    value = f"{int(cents) / 100:,.2f}"
    return value.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


bp.add_app_template_filter(reais, "reais")


@bp.app_context_processor
def inject_billing_banner():
    company = getattr(g, "company", None)
    if company is None or not request.path.startswith("/app"):
        return {"billing_banner": None}
    if not hasattr(g, "_billing_banner"):
        g._billing_banner = billing.banner(company)
    return {"billing_banner": g._billing_banner}


def _plans() -> list[Plan]:
    """Todos os planos ativos para exibir (sob consulta por último, sem botão de contratar)."""
    return plan_catalog.active_plans()


def _plan_or_404(code: str | None) -> Plan:
    """Só plano de autosserviço (com preço) pode ser escolhido pela tela; sob consulta → 404."""
    plan = db.session.execute(select(Plan).where(Plan.code == (code or ""), Plan.active.is_(True))).scalar_one_or_none()
    if plan is None or not plan_catalog.is_self_service(plan):
        abort(404)
    return plan


def _safe_checkout(url: str | None) -> bool:
    """Só redireciona para a página de pagamento do provedor (hosts conhecidos, https)."""
    if not url:
        return False
    parts = urlsplit(url)
    hosts = current_app.config.get("BILLING_CHECKOUT_HOSTS") or ()
    return parts.scheme == "https" and parts.hostname in hosts


def _owner():
    return tenant_required(ROLE_OWNER, allow_read_only=True)


@bp.get("")
@_owner()
def overview():
    company = g.company
    sub = billing.ensure_subscription(company)
    db.session.commit()
    usage = entitlements.usage(company)
    payments = billing.payments_for(sub)
    return render_template(
        "app/assinatura.html",
        sub=sub,
        usage=usage,
        open_payment=billing.open_payment(sub),
        payments=payments[:3],
        price=billing.price_for(sub, sub.plan),
        status_label=billing.STATUS_LABELS.get(sub.status, sub.status),
        status_tone=billing.STATUS_TONES.get(sub.status, "neutral"),
        payment_labels=billing.PAYMENT_LABELS,
        payment_tones=billing.PAYMENT_TONES,
        checkout=billing.needs_checkout(sub),
        managed=plan_catalog.is_managed(sub.plan),
        pending_upgrade=bool(sub.pending_plan and billing.is_upgrade(sub, sub.pending_plan)),
        can_cancel=sub.status not in ("canceled", "expired") and not plan_catalog.is_managed(sub.plan),
        confirm_form=ConfirmForm(formdata=None),
    )


@bp.get("/planos")
@_owner()
def plans():
    sub = billing.ensure_subscription(g.company)
    db.session.commit()
    plans = _plans()
    return render_template(
        "app/assinatura_planos.html",
        sub=sub,
        plans=plans,
        checkout=billing.needs_checkout(sub),
        managed_current=plan_catalog.is_managed(sub.plan) and sub.status not in ("canceled", "expired"),
        self_service={p.id: plan_catalog.is_self_service(p) for p in plans},
        trial={p.id: plan_catalog.has_trial(p) for p in plans},
        prices={p.id: billing.price_for(sub, p) for p in plans},
        implantacao_services=plan_catalog.IMPLANTACAO_SERVICES,
    )


@bp.route("/planos/<code>", methods=["GET", "POST"])
@_owner()
def plan_change(code):
    company = g.company
    plan = _plan_or_404(code)
    sub = billing.ensure_subscription(company)
    if billing.needs_checkout(sub):
        if request.method == "POST":
            abort(405)
        db.session.commit()
        return redirect(url_for("billing.billing_info", plano=plan.code))
    form = ConfirmForm()
    error = None
    if form.validate_on_submit():
        try:
            sub = billing.change_plan(company, plan, current_user.id)
            db.session.commit()
            if sub.plan_id == plan.id and sub.pending_plan_id is None:
                message = f"Plano {plan.name} em vigor."
            elif sub.pending_plan_at and billing.is_upgrade(sub, plan):
                message = f"Troca para {plan.name} pedida: os novos limites valem assim que a fatura no valor novo for paga."
            else:
                when = billing.local_date(sub.pending_plan_at).strftime("%d/%m/%Y")
                message = f"Troca para {plan.name} agendada: vale a partir de {when}, fim do período já pago."
            flash(message, "sucesso")
            return redirect(url_for("billing.overview"))
        except (billing.BillingError, PaymentProviderError) as exc:
            db.session.rollback()
            error = exc.message
            sub = billing.ensure_subscription(company)
    elif request.method == "POST":
        abort(400)
    status = 400 if error else 200
    return (
        render_template("app/assinatura_troca.html", projection=billing.projection(company, plan), sub=sub, form=form, error=error),
        status,
    )


@bp.route("/cobranca", methods=["GET", "POST"])
@_owner()
def billing_info():
    company = g.company
    sub = billing.ensure_subscription(company)
    form = BillingInfoForm()
    plan = None
    code = form.plan.data if request.method == "POST" else request.args.get("plano")
    if code:
        plan = _plan_or_404(code)
        form.plan.data = plan.code
    checkout = billing.needs_checkout(sub)
    if checkout and plan is None and not sub.provider_customer_id:
        db.session.commit()
        return redirect(url_for("billing.plans"))
    if request.method == "GET" and not form.email.data:
        form.email.data = current_user.email
        form.name.data = company.name
    error = None
    if form.validate_on_submit():
        info = billing.BillingInfo(form.name.data, form.cpf_cnpj.data, form.email.data)
        try:
            if checkout and plan is not None:
                invoice_url = billing.subscribe(company, plan, info, current_user.id)
                db.session.commit()
                if _safe_checkout(invoice_url):
                    return redirect(invoice_url, code=303)
                flash("Assinatura criada. A fatura aparece aqui assim que o Asaas gerar.", "sucesso")
                return redirect(url_for("billing.invoices"), code=303)
            billing.update_billing_info(company, info, current_user.id)
            db.session.commit()
            flash("Dados de cobrança atualizados.", "sucesso")
            return redirect(url_for("billing.overview"), code=303)
        except billing.BillingError as exc:
            db.session.rollback()
            error = exc.message
        except PaymentProviderError as exc:
            # Nada local muda; o serviço já gravou à parte só o cliente criado no provedor.
            db.session.rollback()
            error = exc.message
            sub = billing.ensure_subscription(company)
    status = 400 if (error or form.errors) else 200
    return (
        render_template(
            "app/assinatura_cobranca.html",
            form=form,
            plan=plan,
            plan_trial=bool(plan and plan_catalog.has_trial(plan)),
            checkout=checkout,
            error=error,
            sub=sub,
        ),
        status,
    )


@bp.get("/faturas")
@_owner()
def invoices():
    sub = billing.ensure_subscription(g.company)
    db.session.commit()
    return render_template(
        "app/assinatura_faturas.html",
        sub=sub,
        payments=billing.payments_for(sub),
        payment_labels=billing.PAYMENT_LABELS,
        payment_tones=billing.PAYMENT_TONES,
    )


@bp.post("/cancelar")
@_owner()
def cancel():
    form = ConfirmForm()
    if not form.validate_on_submit():
        abort(400)
    try:
        sub = billing.cancel(g.company, current_user.id)
        db.session.commit()
    except (billing.BillingError, PaymentProviderError) as exc:
        db.session.rollback()
        flash(exc.message, "erro")
        return redirect(url_for("billing.overview"), code=303)
    until = billing.local_date(sub.current_period_end).strftime("%d/%m/%Y") if sub.current_period_end else None
    flash(
        f"Assinatura cancelada. Acesso completo até {until}." if until and sub.status == "canceled" else "Assinatura cancelada.",
        "sucesso",
    )
    return redirect(url_for("billing.overview"), code=303)
