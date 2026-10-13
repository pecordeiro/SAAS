"""Envio de e-mail transacional.

Interface ``EmailSender`` com dois backends:
- ``ConsoleEmailSender`` (development/test): guarda as mensagens em memória
  (``outbox(app)``, usado pelos testes) e, em development, grava um ``.eml`` em
  ``instance/emails/`` para abrir o link no navegador. NÃO imprime o corpo no log: o corpo
  leva tokens de uso único.
- ``ResendEmailSender``: API HTTP do Resend (``RESEND_API_KEY``, remetente ``MAIL_FROM``),
  com timeout. Loga só o status, nunca o corpo nem a chave.

Os textos ficam em ``app/templates/emails/<nome>.txt`` e ``.html`` (com a marca). Links
absolutos vêm de ``APP_BASE_URL`` (obrigatório fora de development/test: o host da
requisição pode ser forjado e envenenar o link de reset).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from email.message import EmailMessage as _MimeMessage
from pathlib import Path
from typing import Protocol

from flask import Flask, current_app, render_template, url_for

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str
    html: str


class EmailSender(Protocol):
    def send(self, message: EmailMessage) -> None: ...


class EmailError(RuntimeError):
    """Falha ao entregar a mensagem ao provedor (detalhes só no log, sem corpo)."""


def _mask(address: str) -> str:
    """Só o domínio vai para o log (e-mail é dado pessoal)."""
    return "***@" + address.rsplit("@", 1)[-1] if "@" in address else "***"


class ConsoleEmailSender:
    def __init__(self, app: Flask):
        self.app = app
        self.messages: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> None:
        self.messages.append(message)
        logger.info("e-mail (console) '%s' para %s", message.subject, _mask(message.to))
        if self.app.config.get("ENV_NAME") == "development":
            self._write_eml(message)

    def _write_eml(self, message: EmailMessage) -> None:
        folder = Path(self.app.instance_path) / "emails"
        folder.mkdir(parents=True, exist_ok=True)
        mime = _MimeMessage()
        mime["From"] = self.app.config["MAIL_FROM"]
        mime["To"] = message.to
        mime["Subject"] = message.subject
        mime.set_content(message.text)
        mime.add_alternative(message.html, subtype="html")
        path = folder / f"{len(self.messages):04d}.eml"
        path.write_bytes(bytes(mime))


class ResendEmailSender:
    background = True  # rede: entregue fora da requisição (ver deliver)

    def __init__(self, api_key: str, sender: str, timeout: float):
        self.api_key = api_key
        self.sender = sender
        self.timeout = timeout

    def send(self, message: EmailMessage) -> None:
        import requests

        try:
            response = requests.post(
                RESEND_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "from": self.sender,
                    "to": [message.to],
                    "subject": message.subject,
                    "text": message.text,
                    "html": message.html,
                },
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.error("Resend: falha de rede (%s)", exc.__class__.__name__)
            raise EmailError("falha ao enviar e-mail") from None
        if response.status_code >= 400:
            logger.error("Resend: HTTP %s ao enviar '%s'", response.status_code, message.subject)
            raise EmailError("falha ao enviar e-mail")
        logger.info("e-mail (resend) '%s' para %s", message.subject, _mask(message.to))


def _build_sender(app: Flask) -> EmailSender:
    backend = (app.config.get("MAIL_BACKEND") or "").lower()
    if not backend:
        backend = "resend" if app.config.get("RESEND_API_KEY") else "console"
    if backend == "resend":
        key = app.config.get("RESEND_API_KEY")
        if not key:
            raise RuntimeError("MAIL_BACKEND=resend exige RESEND_API_KEY.")
        return ResendEmailSender(key, app.config["MAIL_FROM"], float(app.config.get("MAIL_TIMEOUT_SECONDS", 10)))
    if backend != "console":
        raise RuntimeError(f"MAIL_BACKEND desconhecido: {backend!r}")
    if app.config.get("ENV_NAME") not in {"development", "test"}:
        logger.warning("E-mail em modo console fora de development/test: nada será entregue.")
    return ConsoleEmailSender(app)


def get_sender(app: Flask | None = None) -> EmailSender:
    app = app or current_app._get_current_object()  # type: ignore[attr-defined]
    sender = app.extensions.get("email_sender")
    if sender is None:
        sender = _build_sender(app)
        app.extensions["email_sender"] = sender
    return sender


def outbox(app: Flask) -> list[EmailMessage]:
    """Mensagens enviadas pelo backend console (testes)."""
    sender = get_sender(app)
    if not isinstance(sender, ConsoleEmailSender):
        raise RuntimeError("outbox só existe no backend console")
    return sender.messages


def external_url(endpoint: str, **values) -> str:
    """URL absoluta para e-mail. Fora de development/test exige APP_BASE_URL."""
    base = current_app.config.get("APP_BASE_URL")
    if base:
        return base.rstrip("/") + url_for(endpoint, **values)
    if current_app.config.get("ENV_NAME") in {"development", "test"}:
        return url_for(endpoint, _external=True, **values)
    raise RuntimeError("APP_BASE_URL é obrigatório para montar links de e-mail fora de development/test.")


def send_template(to: str, subject: str, template: str, **context) -> None:
    """Renderiza ``emails/<template>.txt`` e ``.html`` e envia."""
    context.setdefault("subject", subject)
    context.setdefault("site_url", _site_url())
    message = EmailMessage(
        to=to,
        subject=subject,
        text=render_template(f"emails/{template}.txt", **context),
        html=render_template(f"emails/{template}.html", **context),
    )
    deliver(message)


def _safe_send(sender: EmailSender, message: EmailMessage) -> None:
    try:
        sender.send(message)
    except EmailError:
        pass  # já logado pelo backend (sem corpo)
    except Exception as exc:  # noqa: BLE001 - falha de entrega nunca derruba a requisição
        logger.error("falha inesperada ao enviar e-mail '%s' (%s)", message.subject, exc.__class__.__name__)


def _executor(app: Flask):
    from concurrent.futures import ThreadPoolExecutor

    executor = app.extensions.get("email_executor")
    if executor is None:
        executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="email")
        app.extensions["email_executor"] = executor
    return executor


def deliver(message: EmailMessage) -> None:
    """Entrega sem bloquear a resposta nem vazar erro: backends de rede (``background =
    True``, ex. Resend) vão para uma thread de fundo; assim o tempo e o resultado da
    requisição não dependem de a mensagem existir/chegar (sem enumeração por tempo em
    “esqueci a senha” e no cadastro). O console entrega na hora (testes leem a caixa).
    Mensagem pendente na thread se perde se o processo cair: o outbox com worker (Fase 8)
    substitui isto."""
    app = current_app._get_current_object()  # type: ignore[attr-defined]
    sender = get_sender(app)
    if getattr(sender, "background", False):
        _executor(app).submit(_safe_send, sender, message)
    else:
        _safe_send(sender, message)


def _site_url() -> str:
    try:
        return external_url("public.index")
    except RuntimeError:
        return ""
