"""Etapa H — comandos de operação: ``config-check``, ``mail-test``, ``storage-test``.

Nenhum deles imprime segredo: só nomes de variáveis, o domínio do remetente e o resultado.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

import click
from flask import Flask, current_app

from app import configcheck


def _mask(address: str) -> str:
    return "***@" + address.rsplit("@", 1)[-1] if "@" in address else "***"


def register_ops_cli(app: Flask) -> None:
    @app.cli.command("config-check")
    @click.option("--online", is_flag=True, help="Também confere banco, papel do banco, RLS, migrations e Redis (rede).")
    @click.option("--strict", is_flag=True, help="Avisos também reprovam (use no go-live).")
    @click.option("--ignorar", "ignore", multiple=True, metavar="CODIGO", help="Ignora um achado pelo código (repita).")
    def config_check(online: bool, strict: bool, ignore: tuple[str, ...]) -> None:
        """Confere a configuração de produção; sai com código 1 se algo bloqueia o deploy."""
        env_name = current_app.config.get("ENV_NAME", "production")
        findings, ok = configcheck.evaluate(
            dict(current_app.config), env_name, online=online, strict=strict, ignore=tuple(ignore)
        )
        click.echo(f"config-check · ambiente={env_name} · online={'sim' if online else 'não'} · strict={'sim' if strict else 'não'}")
        for finding in findings:
            click.echo(finding.line())
        errors = sum(f.level == configcheck.ERRO for f in findings)
        warnings = sum(f.level == configcheck.AVISO for f in findings)
        click.echo(f"{errors} erro(s), {warnings} aviso(s).")
        if not ok:
            click.echo("REPROVADO: corrija os itens acima antes do deploy.", err=True)
            raise SystemExit(1)
        click.echo("APROVADO.")

    @app.cli.command("mail-test")
    @click.argument("destino")
    def mail_test(destino: str) -> None:
        """Envia um e-mail de teste pelo backend configurado (confere Resend, remetente e DNS)."""
        from email_validator import EmailNotValidError, validate_email

        from app.services import email as email_svc

        try:
            to = validate_email(destino, check_deliverability=False).normalized
        except EmailNotValidError:
            raise click.ClickException("Endereço de destino inválido.") from None
        sender = email_svc.get_sender()
        backend = "console" if isinstance(sender, email_svc.ConsoleEmailSender) else "resend"
        env_name = current_app.config.get("ENV_NAME")
        from_domain = str(current_app.config.get("MAIL_FROM") or "").rsplit("@", 1)[-1].rstrip(">").strip()
        click.echo(f"backend={backend} · remetente=@{from_domain} · destino={_mask(to)} · ambiente={env_name}")
        if backend == "console" and env_name not in {"development", "test"}:
            raise click.ClickException(
                "Backend console: nada seria entregue. Defina RESEND_API_KEY (ou MAIL_BACKEND=resend)."
            )
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        text = (
            "Teste de envio do Controle de Produção.\n\n"
            f"Enviado em {now} pelo ambiente {env_name}.\n"
            "Se esta mensagem chegou na CAIXA DE ENTRADA (não no spam), o envio está funcionando.\n"
            "Para conferir SPF, DKIM e DMARC, abra os cabeçalhos da mensagem e procure\n"
            "'Authentication-Results': spf=pass, dkim=pass, dmarc=pass.\n"
        )
        html = "<p>" + text.replace("\n\n", "</p><p>").replace("\n", "<br>") + "</p>"
        message = email_svc.EmailMessage(to=to, subject=f"[teste] Controle de Produção — {now}", text=text, html=html)
        started = time.perf_counter()
        try:
            email_svc.send_now(message)
        except email_svc.EmailError:
            raise click.ClickException(
                "Falha ao enviar (veja a linha de log do Resend acima). Causas comuns: domínio do MAIL_FROM não "
                "verificado no Resend, RESEND_API_KEY inválida ou sem permissão de envio, rede bloqueada."
            ) from None
        click.echo(f"Enviado em {(time.perf_counter() - started) * 1000:.0f} ms. Confira a caixa de entrada e os cabeçalhos.")

    @app.cli.command("storage-test")
    def storage_test() -> None:
        """Grava, lê, compara e apaga um objeto de teste no armazenamento de fotos (R2/S3)."""
        from app.services import storage as storage_svc

        store = storage_svc.get_storage()
        if not store.enabled:
            raise click.ClickException("Armazenamento desligado (STORAGE_BACKEND vazio/none).")
        key = storage_svc.photo_key(uuid.uuid4(), uuid.uuid4())
        payload = b"controle-storage-test-" + uuid.uuid4().bytes
        click.echo(f"backend={store.name}")
        try:
            store.put(key, payload, "image/jpeg")
            click.echo("PUT ok")
            if store.get(key) != payload:
                raise click.ClickException("GET devolveu conteúdo diferente do gravado.")
            click.echo("GET ok (conteúdo idêntico)")
        except storage_svc.StorageError as exc:
            raise click.ClickException(f"Falha no armazenamento: {exc}") from None
        finally:
            try:
                store.delete(key)
                click.echo("DELETE ok")
            except storage_svc.StorageError:
                click.echo("DELETE falhou: apague o objeto de teste manualmente.", err=True)
        click.echo("Armazenamento OK.")

    @app.cli.command("sentry-test")
    def sentry_test() -> None:
        """Manda um evento de teste ao Sentry com dados “sensíveis” falsos para provar o filtro."""
        if not current_app.config.get("SENTRY_DSN"):
            raise click.ClickException("SENTRY_DSN ausente: o Sentry está desligado neste ambiente.")
        import sentry_sdk

        with sentry_sdk.new_scope() as scope:
            scope.set_user({"id": "usuario-de-teste", "email": "pessoa@exemplo.com", "ip_address": "203.0.113.7"})
            scope.set_extra("token", "cp_abcdefghijklmnopqrstuvwxyz012345")
            scope.set_extra("contato", "pessoa@exemplo.com")
            scope.set_tag("origem", "flask sentry-test")
            event_id = sentry_sdk.capture_message("Teste de integração do Sentry (flask sentry-test)", level="info")
        sentry_sdk.flush(timeout=10)
        click.echo(f"Evento enviado (id {event_id}).")
        click.echo("Abra-o no Sentry: token deve estar [filtrado], e-mail [e-mail] e o usuário só com o id.")
