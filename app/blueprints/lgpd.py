"""Fase 7 — Privacidade e dados da empresa (/app/privacidade), só proprietário.

- Exportar: POST (CSRF + auditoria) devolve ZIP de CSVs só com dados da empresa da sessão.
- Excluir: pede senha + nome da empresa; agenda a exclusão com carência de 30 dias
  (cancelável). O apagamento definitivo é do comando ``flask lgpd-purge``.
- Comandos de plataforma (``cli_group=None`` → ``flask lgpd-purge``, ``flask lgpd-retencao``,
  ``flask suporte ...``, ``flask mfa-rotacionar``).

Sem rota com ``<uuid>``: a empresa vem só da sessão (tenancy). Todas as rotas aceitam modo
leitura (exportar e excluir são direitos do titular mesmo com a assinatura vencida).
"""

from __future__ import annotations

import getpass
import os

import click
from flask.cli import AppGroup
from flask import Blueprint, Response, current_app, flash, g, redirect, render_template, url_for
from flask_login import current_user

from app.extensions import db, limiter
from app.forms_accounts import CompanyDeletionForm, TokenActionForm
from app.models import ROLE_OWNER
from app.services import lgpd
from app.services.passwords import verify_password
from app.tenancy import tenant_required

bp = Blueprint("lgpd", __name__, url_prefix="/app/privacidade", cli_group=None)


def _limit(key: str, default: str):
    return lambda: current_app.config.get(key, default)


def _page(status: int = 200, form: CompanyDeletionForm | None = None, error: str | None = None):
    company = g.company
    return render_template(
        "lgpd/index.html",
        action_form=TokenActionForm(formdata=None),
        form=form or CompanyDeletionForm(formdata=None),
        deletion_requested_at=company.deletion_requested_at,
        purge_at=lgpd.purge_date(company),
        grace_days=lgpd.grace_days(),
        error=error,
    ), status


@bp.get("")
@tenant_required(ROLE_OWNER, allow_read_only=True)
def index():
    return _page()


@bp.post("/exportar")
@limiter.limit(_limit("LGPD_EXPORT_RATE_LIMIT", "3 per hour"))
@tenant_required(ROLE_OWNER, allow_read_only=True)
def export():
    form = TokenActionForm()
    if not form.validate_on_submit():
        return _page(400, error="Formulário expirado. Tente de novo.")
    data, counts = lgpd.export_company(g.company)
    lgpd.record_export(g.company, current_user.id, counts)
    db.session.commit()
    response = Response(data, mimetype="application/zip")
    response.headers["Content-Disposition"] = f'attachment; filename="{lgpd.export_filename(g.company)}"'
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.post("/excluir")
@limiter.limit(_limit("LGPD_DELETE_RATE_LIMIT", "5 per hour"))
@tenant_required(ROLE_OWNER, allow_read_only=True)
def request_deletion():
    form = CompanyDeletionForm()
    if not form.validate_on_submit():
        return _page(400, form=form)
    if not verify_password(current_user.password_hash, form.password.data):
        return _page(400, form=form, error="Senha incorreta.")
    if form.company_name.data.strip().casefold() != (g.company.name or "").strip().casefold():
        return _page(400, form=form, error="O nome digitado não confere com o da empresa.")
    when = lgpd.request_deletion(g.company, current_user.id)
    db.session.commit()
    flash(f"Exclusão agendada para {when:%d/%m/%Y}. Você pode cancelar até lá.", "aviso")
    return redirect(url_for("lgpd.index"), 303)


@bp.post("/excluir/cancelar")
@tenant_required(ROLE_OWNER, allow_read_only=True)
def cancel_deletion():
    form = TokenActionForm()
    if not form.validate_on_submit():
        return _page(400, error="Formulário expirado. Tente de novo.")
    if lgpd.cancel_deletion(g.company, current_user.id):
        db.session.commit()
        flash("Exclusão cancelada. Nada foi apagado.", "sucesso")
    return redirect(url_for("lgpd.index"), 303)


# ---------------------------------------------------------------- linha de comando


def _operator(value: str | None) -> str:
    if value:
        return value
    try:
        return os.environ.get("OPERATOR") or getpass.getuser()
    except Exception:  # noqa: BLE001
        return "desconhecido"


@bp.cli.command("lgpd-purge")
@click.option("--dry-run", is_flag=True, help="Só mostra o que seria apagado.")
@click.option("--operador", default=None, help="Quem está rodando (vai para platform_audit_logs).")
def purge_command(dry_run: bool, operador: str | None) -> None:
    """Apaga definitivamente as empresas cuja carência de exclusão acabou (idempotente)."""
    results = lgpd.purge_due(operator=_operator(operador), dry_run=dry_run)
    if not results:
        click.echo("Nenhuma empresa com carência vencida.")
        return
    for r in results:
        total = sum(r.rows.values())
        verb = "seria apagada" if dry_run else "apagada"
        click.echo(f"Empresa {r.company_id} {verb}: {total} linha(s), até {r.users_deleted} usuário(s).")


@bp.cli.command("lgpd-retencao")
@click.option("--dry-run", is_flag=True, help="Só conta o que seria apagado.")
@click.option("--operador", default=None)
def retention_command(dry_run: bool, operador: str | None) -> None:
    """Aplica a política de retenção (docs/plano/lgpd.md)."""
    counts = lgpd.apply_retention(operator=_operator(operador), dry_run=dry_run)
    for name, n in counts.items():
        click.echo(f"{name:22} {n}")


suporte = AppGroup("suporte", help="Acesso temporário de suporte (auditado; avisa os proprietários).")


@suporte.command("conceder")
@click.argument("email")
@click.option("--empresa", "company_id", required=True, help="Id (UUID) da empresa.")
@click.option("--motivo", required=True, help="Motivo (chamado, pedido do cliente...). Vai para a auditoria e o e-mail.")
@click.option("--horas", type=int, default=4, show_default=True)
@click.option("--papel", type=click.Choice(["operator", "supervisor"]), default="operator", show_default=True)
@click.option("--autorizado-por", "authorized_by", required=True, help="Quem autorizou o acesso.")
def support_grant(email, company_id, motivo, horas, papel, authorized_by):
    from app.services import support

    try:
        member = support.grant(
            email=email, company_id=company_id, reason=motivo, hours=horas, role=papel, operator=authorized_by
        )
    except support.SupportError as exc:
        raise click.ClickException(str(exc)) from None
    click.echo(f"Acesso concedido até {member.expires_at:%d/%m/%Y %H:%M} UTC. Proprietários avisados por e-mail.")


@suporte.command("revogar")
@click.argument("email")
@click.option("--empresa", "company_id", required=True)
@click.option("--autorizado-por", "authorized_by", default=None)
def support_revoke(email, company_id, authorized_by):
    from app.services import support

    try:
        changed = support.revoke(email=email, company_id=company_id, operator=_operator(authorized_by))
    except support.SupportError as exc:
        raise click.ClickException(str(exc)) from None
    click.echo("Acesso revogado." if changed else "Nada a revogar.")


@suporte.command("listar")
def support_list():
    from app.services import support

    grants = support.active_grants()
    if not grants:
        click.echo("Nenhum acesso de suporte ativo.")
    for m in grants:
        click.echo(f"{m.user.email}  empresa={m.company_id}  papel={m.role}  até={m.expires_at:%d/%m/%Y %H:%M}")


@suporte.command("expirar")
def support_expire():
    """Desativa e audita os acessos vencidos (rodar no cron; o acesso já não valia)."""
    from app.services import support

    click.echo(f"{support.expire()} acesso(s) expirado(s).")


bp.cli.add_command(suporte)


@bp.cli.command("mfa-rotacionar")
def mfa_rotate():
    """Recifra os segredos TOTP com a primeira chave de MFA_ENCRYPTION_KEY."""
    from app.services import mfa

    click.echo(f"{mfa.rotate_all()} segredo(s) recifrado(s).")
