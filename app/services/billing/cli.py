"""Comandos de cobrança.

- ``flask billing-reconcile``: confere toda assinatura com o provedor (status da assinatura e
  das cobranças) e recalcula o estado local (carência vencida → modo leitura, teste vencido,
  cancelada no fim do período). Idempotente: rodar de novo sem mudança no provedor não
  altera nada. Feito para rodar 1x/dia no worker (Fase 10) e depois de falha de webhook.
- ``flask billing-admin extend-trial|discount --company <uuid> --reason "..."``: ações do
  admin da plataforma, sempre com motivo em ``audit_logs``.
"""

from __future__ import annotations

import uuid

import click
from flask import Flask
from flask.cli import AppGroup

from app import rls
from app.extensions import db
from app.models import Company
from app.services.billing import service as billing
from app.services.billing.provider import PaymentProviderError


def _company(raw: str) -> Company:
    try:
        company_id = uuid.UUID(raw)
    except ValueError:
        raise click.ClickException("--company deve ser o id (UUID) da empresa.") from None
    company = db.session.get(Company, company_id)
    if company is None:
        raise click.ClickException("Empresa não encontrada.")
    rls.set_context(company_id=company.id)
    return company


def register_cli(app: Flask) -> None:
    @app.cli.command("billing-reconcile")
    def billing_reconcile() -> None:
        """Corrige divergências entre as assinaturas locais e o provedor (idempotente)."""
        result = billing.reconcile_all()
        click.echo(
            f"Assinaturas conferidas: {result['checked']} · corrigidas: {result['changed']} · "
            f"erros de provedor: {result['errors']}"
        )
        if result["errors"]:
            raise SystemExit(1)

    admin = AppGroup("billing-admin", help="Ações do admin da plataforma (auditadas, com motivo).")

    @admin.command("extend-trial")
    @click.option("--company", "company_id", required=True, help="Id (UUID) da empresa.")
    @click.option("--days", type=int, required=True, help="Dias a mais de teste grátis (1–90).")
    @click.option("--reason", required=True, help="Motivo (obrigatório, vai para audit_logs).")
    def extend_trial(company_id: str, days: int, reason: str) -> None:
        company = _company(company_id)
        try:
            sub = billing.admin_extend_trial(company, days, reason)
            db.session.commit()
        except billing.BillingError as exc:
            db.session.rollback()
            raise click.ClickException(exc.message) from None
        click.echo(f"Teste grátis de {company.name} até {sub.trial_ends_at:%d/%m/%Y %H:%M} UTC.")

    @admin.command("discount")
    @click.option("--company", "company_id", required=True, help="Id (UUID) da empresa.")
    @click.option("--percent", type=int, required=True, help="Desconto em % sobre o plano (0 remove).")
    @click.option("--reason", required=True, help="Motivo (obrigatório, vai para audit_logs).")
    def discount(company_id: str, percent: int, reason: str) -> None:
        company = _company(company_id)
        try:
            sub = billing.admin_discount(company, percent, reason)
            db.session.commit()
        except (billing.BillingError, PaymentProviderError) as exc:
            db.session.rollback()
            raise click.ClickException(exc.message) from None
        click.echo(
            f"Desconto de {sub.discount_percent or 0}% para {company.name}: "
            f"R$ {billing.price_for(sub, sub.plan) / 100:.2f}/mês."
        )

    app.cli.add_command(admin)
