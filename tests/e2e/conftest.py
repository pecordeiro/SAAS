"""Testes de navegador (Playwright + Chromium). Opcionais: `pytest -m e2e` ou RUN_E2E=1.

Sobem o app de verdade (werkzeug em thread, SQLite em arquivo temporário, e-mail no backend
console — o link de confirmação sai do outbox em memória) e monitoram a rede: qualquer
requisição para fora do próprio servidor reprova o teste.
Navegador: `playwright==1.55.0` com os navegadores de /opt/pw-browsers (PLAYWRIGHT_BROWSERS_PATH);
se a revisão não casar, usa E2E_CHROMIUM ou o chrome de /opt/pw-browsers/chromium-1194.
"""

from __future__ import annotations

import os
import socket
import threading
from pathlib import Path

import pytest

CHROME_FALLBACK = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_E2E") == "1" or "e2e" in (config.getoption("-m") or ""):
        return
    skip = pytest.mark.skip(reason="teste e2e: rode com RUN_E2E=1 ou -m e2e")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def live(tmp_path_factory):
    from werkzeug.serving import make_server

    from app import create_app
    from app.extensions import db
    from app.services.holidays import seed_national_holidays
    from app.services.plans import seed_plans

    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    db_file = tmp_path_factory.mktemp("e2e") / "e2e.db"
    app = create_app(
        "test",
        {
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
            "SECRET_KEY": "e2e-" + "x" * 32,
            "APP_BASE_URL": base,
            "RATELIMIT_ENABLED": False,
            "MAIL_BACKEND": "console",
        },
    )
    with app.app_context():
        db.create_all()
        seed_plans()
        from datetime import date

        seed_national_holidays(date.today().year, date.today().year + 1)
        db.session.commit()
    server = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    class Live:
        pass

    live_obj = Live()
    live_obj.app, live_obj.base = app, base
    yield live_obj
    server.shutdown()


@pytest.fixture(scope="session")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        try:
            chromium = pw.chromium.launch()
        except Exception:  # revisão do navegador não casa com a do pacote
            exe = os.environ.get("E2E_CHROMIUM") or CHROME_FALLBACK
            chromium = pw.chromium.launch(executable_path=exe)
        yield chromium
        chromium.close()


@pytest.fixture()
def make_page(browser, live):
    """Fábrica de páginas (viewport, JS ligado/desligado) que anota toda requisição de rede."""
    seen: list[str] = []
    contexts = []

    def factory(width=1280, height=900, js=True, context=None):
        ctx = context or browser.new_context(
            viewport={"width": width, "height": height}, java_script_enabled=js, locale="pt-BR", accept_downloads=True
        )
        if context is None:
            contexts.append(ctx)
        page = ctx.new_page()
        page.on("request", lambda req: seen.append(req.url))
        page.set_default_timeout(8000)
        return page

    yield factory
    for ctx in contexts:
        ctx.close()
    external = [u for u in seen if not (u.startswith(live.base) or u.startswith(("data:", "blob:", "about:")))]
    assert not external, f"requisição a outro domínio: {external}"


@pytest.fixture()
def tenant_a(live):
    """Empresa fictícia com owner/supervisor/operador e um projeto (senha em conftest.PASSWORD)."""
    from tests.conftest import make_tenant
    import uuid

    with live.app.app_context():
        from app.extensions import db  # noqa: F401

        label = "E" + uuid.uuid4().hex[:6]
        return make_tenant(label), label


def ui_login(page, base: str, email: str, password: str):
    page.goto(f"{base}/entrar")
    page.fill("#email", email)
    page.fill("#password", password)
    page.click("button[type=submit].btn--primary")
    page.wait_for_url(lambda url: "/entrar" not in url)
