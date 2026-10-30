"""Etapa H — scripts/smoke_check.py contra um servidor local de verdade."""

from __future__ import annotations

import importlib.util
import socket
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("smoke_check", ROOT / "scripts" / "smoke_check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


smoke = _load()


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    from werkzeug.serving import make_server

    from app import create_app
    from app.extensions import db
    from app.services.plans import seed_plans

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    db_file = tmp_path_factory.mktemp("smoke") / "smoke.db"
    app = create_app(
        "test",
        {
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
            "SECRET_KEY": "smoke-" + "x" * 32,
            "APP_BASE_URL": url,
            "RATELIMIT_ENABLED": False,
            "MAIL_BACKEND": "console",
            "ASAAS_WEBHOOK_TOKEN": "token-do-smoke-" + "y" * 20,
        },
    )
    with app.app_context():
        db.create_all()
        seed_plans()
        db.session.commit()
    server = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield url
    server.shutdown()


def test_smoke_passa_no_servidor_local(base, capsys):
    assert smoke.run(base, production=False, other_host=None) == 0, capsys.readouterr().out


def test_smoke_producao_reprova_texto_legal_em_rascunho_e_http(base, capsys):
    status = smoke.run(base, production=True, other_host=None)
    out = capsys.readouterr().out
    assert status == 1
    assert "[FALHA] termos/privacidade sem" in out
    assert "[FALHA] é https" in out


def test_smoke_detecta_servidor_fora_do_ar(capsys):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with pytest.raises(Exception):
        smoke.run(f"http://127.0.0.1:{port}", production=False, other_host=None)
