"""Fase 7 — cabeçalhos/CSP, cookies, rate limit, uploads, logs, Sentry, API e MFA."""

from __future__ import annotations

import io
import json
import logging
import re
import struct
import zipfile

import pytest

from app import create_app, security
from app.extensions import db
from app.logging_config import JsonFormatter, RequestContextFilter, sentry_before_send
from app.services import importer
from tests.conftest import PASSWORD, login, make_tenant, post, text_of

PROD = {
    "SECRET_KEY": "k" * 64,
    "SQLALCHEMY_DATABASE_URI": "sqlite://",
    "RATELIMIT_STORAGE_URI": "redis://127.0.0.1:6399/0",  # cliente preguiçoso: não conecta no init
    "RATELIMIT_ENABLED": False,
    "APP_BASE_URL": "https://app.exemplo.com.br",
}


@pytest.fixture()
def prod_app():
    app = create_app("production", dict(PROD))
    with app.app_context():
        db.create_all()
        from app.services.plans import seed_plans

        seed_plans()
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


# ---------------------------------------------------------------- CSP e cabeçalhos


def _csp(response) -> dict[str, str]:
    out = {}
    for part in response.headers["Content-Security-Policy"].split(";"):
        name, _, value = part.strip().partition(" ")
        out[name] = value
    return out


def test_csp_estrita_com_nonce_por_requisicao(client):
    first, second = client.get("/"), client.get("/entrar")
    csp = _csp(first)
    assert "unsafe-inline" not in first.headers["Content-Security-Policy"]
    assert "unsafe-eval" not in first.headers["Content-Security-Policy"]
    assert re.fullmatch(r"'self' 'nonce-[A-Za-z0-9_-]{20,}'", csp["script-src"])
    assert csp["style-src"] == "'self'"
    assert csp["frame-ancestors"] == "'none'" and csp["base-uri"] == "'none'"
    assert csp["form-action"] == "'self'" and csp["object-src"] == "'none'"
    assert _csp(second)["script-src"] != csp["script-src"]  # nonce novo a cada resposta


def test_csp_nonce_no_jinja_e_o_mesmo_do_cabecalho(app):
    from flask import render_template_string

    with app.test_request_context("/"):
        html = render_template_string('<script nonce="{{ csp_nonce() }}"></script>')
        response = app.make_response(html)
        response = app.process_response(response)
        nonce = re.search(r'nonce="([^"]+)"', html).group(1)
        assert f"'nonce-{nonce}'" in response.headers["Content-Security-Policy"]


def test_cabecalhos_de_seguranca(client):
    response = client.get("/")
    h = response.headers
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["X-Frame-Options"] == "DENY"
    assert h["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in h["Permissions-Policy"] and "geolocation=()" in h["Permissions-Policy"]
    assert h["Cross-Origin-Opener-Policy"] == "same-origin"
    assert "Strict-Transport-Security" not in h  # test/dev: sem HSTS (localhost em http)


def test_pagina_logada_nao_fica_em_cache(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    assert client.get("/app/projetos").headers["Cache-Control"] == "no-store"


# ---------------------------------------------------------------- produção: HSTS e cookies


def test_producao_hsts_e_cookie_de_sessao_seguro(prod_app):
    client = prod_app.test_client()
    response = client.get("/entrar", base_url="https://app.exemplo.com.br")
    assert response.headers["Strict-Transport-Security"].startswith("max-age=63072000")
    cookies = response.headers.getlist("Set-Cookie")
    session_cookie = next(c for c in cookies if c.startswith("__Host-session="))
    for flag in ("Secure", "HttpOnly", "SameSite=Lax", "Path=/"):
        assert flag in session_cookie
    assert "Domain=" not in session_cookie


def test_producao_login_grava_cookie_de_dispositivo_host(prod_app):
    with prod_app.app_context():
        a = make_tenant("A")
    client = prod_app.test_client()
    base = "https://app.exemplo.com.br"
    page = client.get("/entrar", base_url=base).get_data(as_text=True)
    token = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', page).group(1)
    response = client.post(
        "/entrar",
        data={"email": a.owner_email, "password": PASSWORD, "csrf_token": token},
        base_url=base,
        headers={"Referer": base + "/entrar"},  # HTTPS: Flask-WTF confere a origem
    )
    assert response.status_code in (302, 303)
    cookies = response.headers.getlist("Set-Cookie")
    device = next(c for c in cookies if c.startswith("__Host-dispositivo="))
    assert "Secure" in device and "HttpOnly" in device and "SameSite=Lax" in device
    session_cookie = next(c for c in cookies if c.startswith("__Host-session="))
    assert "Secure" in session_cookie and "HttpOnly" in session_cookie
    assert prod_app.config["REMEMBER_COOKIE_NAME"] == "__Host-remember"


def test_producao_recusa_cookie_inseguro():
    with pytest.raises(RuntimeError, match="Cookies inseguros"):
        create_app("production", {**PROD, "SESSION_COOKIE_SECURE": False})


def test_producao_sem_redis_falha_com_mensagem_clara(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("RATELIMIT_STORAGE_URI", raising=False)
    overrides = {k: v for k, v in PROD.items() if k not in {"RATELIMIT_STORAGE_URI", "RATELIMIT_ENABLED"}}
    with pytest.raises(RuntimeError, match="Redis"):
        create_app("production", overrides)


def test_redis_url_vira_storage_do_rate_limit(monkeypatch):
    from app.config import ProductionConfig

    monkeypatch.delenv("RATELIMIT_STORAGE_URI", raising=False)
    monkeypatch.setenv("REDIS_URL", "redis://cache:6379/0")
    assert ProductionConfig.from_env()["RATELIMIT_STORAGE_URI"] == "redis://cache:6379/0"


# ---------------------------------------------------------------- rate limit


def test_importacao_tem_rate_limit_429(app_factory):
    app = app_factory({"RATELIMIT_ENABLED": True, "IMPORT_RATE_LIMIT": "2 per minute"})
    with app.app_context():
        a, _ = make_tenant("A"), make_tenant("B")
    client = app.test_client()
    login(client, app, a.owner_email)
    codes = [
        post(client, app, "/app/importar", {"file": (io.BytesIO(b"x;y\n"), "a.csv")}, content_type="multipart/form-data").status_code
        for _ in range(3)
    ]
    assert codes[-1] == 429 and 429 not in codes[:2]


def test_exportacao_lgpd_tem_rate_limit_429(app_factory):
    app = app_factory({"RATELIMIT_ENABLED": True, "LGPD_EXPORT_RATE_LIMIT": "1 per hour"})
    with app.app_context():
        a = make_tenant("A")
    client = app.test_client()
    login(client, app, a.owner_email)
    assert post(client, app, "/app/privacidade/exportar").status_code == 200
    assert post(client, app, "/app/privacidade/exportar").status_code == 429


def test_blueprint_de_webhook_ganha_rate_limit(app_factory):
    from flask import Blueprint

    app = app_factory({"RATELIMIT_ENABLED": True, "WEBHOOK_RATE_LIMIT": "2 per minute"})
    bp = Blueprint("webhooks_teste_f7", __name__)

    @bp.post("/webhooks/teste-f7")
    def hook():
        return "ok"

    app.register_blueprint(bp)
    security._limit_webhook_blueprints(app)
    from app.extensions import csrf

    csrf.exempt(bp)
    client = app.test_client()
    codes = [client.post("/webhooks/teste-f7").status_code for _ in range(3)]
    assert codes == [200, 200, 429]


# ---------------------------------------------------------------- uploads


def test_upload_acima_do_limite_413_sem_ler_o_corpo(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    big = b"x" * (app.config["MAX_CONTENT_LENGTH"] + 1)
    response = post(client, app, "/app/importar", {"file": (io.BytesIO(big), "a.csv")}, content_type="multipart/form-data")
    assert response.status_code == 413


def test_upload_fica_em_memoria(app):
    data = {"file": (io.BytesIO(b"a" * (600 * 1024)), "a.csv")}  # > 500 KB: Werkzeug iria para disco
    with app.test_request_context("/x", method="POST", data=data, content_type="multipart/form-data"):
        from flask import request

        assert isinstance(request.files["file"].stream, io.BytesIO)


def _xlsx_with(name: str, payload: bytes, compress=zipfile.ZIP_DEFLATED) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=compress) as zf:
        zf.writestr("[Content_Types].xml", b'<?xml version="1.0"?><Types/>')
        zf.writestr(name, payload)
    return out.getvalue()


def test_zip_bomb_pelo_tamanho_real_recusado():
    bomb = _xlsx_with("xl/worksheets/sheet1.xml", b"0" * (importer.MAX_UNCOMPRESSED + 1024))
    assert len(bomb) < 200 * 1024  # pequeno compactado
    with pytest.raises(importer.ImportError_, match="grande demais"):
        importer.parse_upload("x.xlsx", bomb, 10**7)


def test_zip_bomb_com_tamanho_declarado_falso_recusado():
    """Cabeçalho mente (tamanho descompactado minúsculo): a checagem pelo declarado passa,
    mas a leitura real não aceita o arquivo."""
    data = bytearray(_xlsx_with("xl/worksheets/sheet1.xml", b"0" * (importer.MAX_UNCOMPRESSED + 1024)))
    # Reescreve o file_size no diretório central (offset 24 do registro PK\x01\x02) e no local.
    for sig, offset in ((b"PK\x01\x02", 24), (b"PK\x03\x04", 22)):
        start = 0
        while (pos := data.find(sig, start)) != -1:
            struct.pack_into("<I", data, pos + offset, 10)
            start = pos + 4
    with pytest.raises(importer.ImportError_):
        importer.parse_upload("x.xlsx", bytes(data), 10**7)


def test_xlsx_com_dtd_xxe_recusado():
    xxe = (
        b'<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
        b'<worksheet><sheetData><row><c t="inlineStr"><is><t>&x;</t></is></c></row></sheetData></worksheet>'
    )
    with pytest.raises(importer.ImportError_, match="DTD"):
        importer.parse_upload("x.xlsx", _xlsx_with("xl/worksheets/sheet1.xml", xxe), 10**7)


def test_openpyxl_usa_defusedxml():
    from openpyxl.xml import DEFUSEDXML

    assert DEFUSEDXML is True


# ---------------------------------------------------------------- logs e request_id


def test_request_id_aceito_so_com_formato_seguro(client):
    ok = client.get("/health", headers={"X-Request-ID": "abc-123_XYZ.789"})
    assert ok.headers["X-Request-ID"] == "abc-123_XYZ.789"
    bad = client.get("/health", headers={"X-Request-ID": "id com espaco; e=1 " * 2})
    assert re.fullmatch(r"[0-9a-f]{32}", bad.headers["X-Request-ID"])
    short = client.get("/health", headers={"X-Request-ID": "<script>"})
    assert re.fullmatch(r"[0-9a-f]{32}", short.headers["X-Request-ID"])


def test_log_de_acesso_usa_molde_da_rota_e_nao_o_token(client, caplog):
    caplog.set_level(logging.INFO, logger="app.access")
    token = "SegredoDoConviteAbcdefghijklmnopqrstuvwxyz0123"
    client.get(f"/convite/{token}")
    records = [r for r in caplog.records if r.name == "app.access"]
    assert records and records[-1].route == "/convite/<token>"
    formatted = JsonFormatter().format(records[-1])
    assert token not in formatted and json.loads(formatted)["route"] == "/convite/<token>"


def test_formatter_json_filtra_segredos_e_emails():
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "login de maria@exemplo.com token %s", ("cp_abcdefghijklmnop",), None)
    record.password = "123"
    record.user_id = "3f2b8c1e-1234-4abc-9def-0123456789ab"
    RequestContextFilter().filter(record)
    out = json.loads(JsonFormatter().format(record))
    assert "maria@" not in out["msg"] and "cp_abc" not in out["msg"]
    assert out["password"] == "[filtrado]"
    assert out["user_id"] == "3f2b8c1e-1234-4abc-9def-0123456789ab"


def test_sentry_before_send_remove_pii_e_segredos():
    event = {
        "request": {
            "url": "https://app/redefinir-senha/AbCdEfGhIjKlMnOpQrStUvWxYz0123456789abcd?x=1",
            "headers": {"Cookie": "session=1", "Authorization": "Bearer cp_x", "asaas-access-token": "t", "User-Agent": "ua"},
            "cookies": {"session": "1"},
            "data": {"password": "x"},
            "query_string": "token=1",
        },
        "user": {"id": "u1", "email": "a@b.com", "ip_address": "1.2.3.4"},
        "extra": {"senha": "x", "api_key": "y", "ok": "valor"},
        "breadcrumbs": {"values": [{"message": "e-mail a@b.com", "data": {"token": "z"}}]},
        "exception": {"values": [{"value": "falhou para a@b.com", "stacktrace": {"frames": [{"vars": {"password": "x"}}]}}]},
    }
    out = sentry_before_send(event, {})
    req = out["request"]
    assert "cookies" not in req and "data" not in req and "query_string" not in req
    assert req["headers"]["Cookie"] == "[filtrado]" and req["headers"]["Authorization"] == "[filtrado]"
    assert req["headers"]["asaas-access-token"] == "[filtrado]" and req["headers"]["User-Agent"] == "ua"
    assert "AbCdEf" not in req["url"] and "?" not in req["url"]
    assert out["user"] == {"id": "u1"}
    assert out["extra"] == {"senha": "[filtrado]", "api_key": "[filtrado]", "ok": "valor"}
    crumb = out["breadcrumbs"]["values"][0]
    assert "a@b.com" not in crumb["message"] and crumb["data"]["token"] == "[filtrado]"
    exc = out["exception"]["values"][0]
    assert "a@b.com" not in exc["value"] and "vars" not in exc["stacktrace"]["frames"][0]


def test_sentry_inicia_so_com_dsn(app_factory, monkeypatch):
    calls = []
    import sentry_sdk

    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: calls.append(kw))
    from app import logging_config

    app = app_factory()
    logging_config._init_sentry(app)
    assert calls == []
    app.config["SENTRY_DSN"] = "https://chave@exemplo.invalid/1"
    logging_config._init_sentry(app)
    assert calls and calls[0]["send_default_pii"] is False and calls[0]["max_request_body_size"] == "never"
    assert calls[0]["include_local_variables"] is False and calls[0]["before_send"] is sentry_before_send


# ---------------------------------------------------------------- API: chave do rate limit


def test_api_token_invalido_usa_chave_por_ip(app_factory):
    from app.blueprints import api_v1
    from app.models import Company
    from app.services import api_tokens

    app = app_factory({"FEATURE_PUBLIC_API": True})
    with app.app_context():
        a = make_tenant("A", plan="empresa")
        created = api_tokens.create_token(db.session.get(Company, a.company_id), name="X", scopes=["read:projects"], expires_in_days=1, user_id=None)
        db.session.commit()
        token_id = created.token.id
    for header, expected in (
        ("Bearer cp_inventado" + "x" * 40, "ip:"),
        ("Bearer qualquer-coisa", "ip:"),
        (None, "ip:"),
        (f"Bearer {created.raw}", f"tok:{token_id}"),
    ):
        headers = {"Authorization": header} if header else {}
        with app.test_request_context("/api/v1/projects", headers=headers, environ_base={"REMOTE_ADDR": "9.9.9.9"}):
            key = api_v1.token_key()
            assert key.startswith(expected)
            assert created.raw not in key


def test_api_rate_limit_com_tokens_inventados_conta_no_mesmo_balde(app_factory):
    app = app_factory({"FEATURE_PUBLIC_API": True, "RATELIMIT_ENABLED": True, "API_RATE_LIMIT": "3 per minute"})
    client = app.test_client()
    codes = [client.get("/api/v1/projects", headers={"Authorization": f"Bearer cp_chute{i:040d}"}).status_code for i in range(4)]
    assert codes == [401, 401, 401, 429]


# ---------------------------------------------------------------- conta tomada de volta pelo dono do e-mail


def test_reset_em_conta_nao_confirmada_revoga_tokens_e_convites(app_factory):
    import re as _re

    from app.models import ApiToken, Company, Invitation, User
    from app.services import api_tokens
    from app.services.email import outbox

    app = app_factory({"FEATURE_PUBLIC_API": True})
    with app.app_context():
        a = make_tenant("A", plan="empresa")
        owner = db.session.get(User, a.owner_id)
        owner.email_confirmed_at = None  # conta criada por quem não é dono do e-mail
        created = api_tokens.create_token(db.session.get(Company, a.company_id), name="Atacante", scopes=["read:projects"], expires_in_days=30, user_id=owner.id)
        from datetime import timedelta

        from app.services.tokens import new_token, utcnow

        db.session.add(Invitation(company_id=a.company_id, email="cumplice@x.com", role="owner", token_hash=new_token()[1], expires_at=utcnow() + timedelta(days=7), invited_by_user_id=owner.id))
        db.session.commit()
        token_id, raw_token = created.token.id, created.raw
    client = app.test_client()
    post(client, app, "/senha/esqueci", {"email": a.owner_email})
    token = _re.search(r"/senha/redefinir/([A-Za-z0-9_-]+)", outbox(app)[-1].text).group(1)
    response = post(client, app, f"/senha/redefinir/{token}", {"password": "nova-senha-forte-1", "password_confirm": "nova-senha-forte-1"})
    assert response.status_code in (302, 303)
    with app.app_context():
        assert db.session.get(ApiToken, token_id).revoked_at is not None
        assert all(i.revoked_at is not None for i in db.session.query(Invitation).all())
    assert client.get("/api/v1/projects", headers={"Authorization": f"Bearer {raw_token}"}).status_code == 401


# ---------------------------------------------------------------- MFA: rotação com MultiFernet


def test_mfa_rotacao_de_chave_com_multifernet(app_factory):
    from app.models import User
    from app.services import mfa

    app = app_factory({"MFA_ENCRYPTION_KEY": "chave-antiga"})
    with app.app_context():
        a = make_tenant("A")
        user = db.session.get(User, a.owner_id)
        user.totp_secret_enc = mfa.encrypt_secret("JBSWY3DPEHPK3PXP")
        db.session.commit()
        app.config["MFA_ENCRYPTION_KEY"] = "chave-nova,chave-antiga"
        assert mfa.decrypt_secret(user.totp_secret_enc) == "JBSWY3DPEHPK3PXP"
        assert mfa.rotate_all() == 1
        app.config["MFA_ENCRYPTION_KEY"] = "chave-nova"
        assert mfa.decrypt_secret(db.session.get(User, a.owner_id).totp_secret_enc) == "JBSWY3DPEHPK3PXP"


def test_secret_key_fallbacks_valida_assinatura_antiga(app_factory):
    from itsdangerous import URLSafeTimedSerializer

    app = app_factory({"SECRET_KEY": "nova", "SECRET_KEY_FALLBACKS": ["antiga"]})
    old = URLSafeTimedSerializer("antiga", salt="s").dumps({"x": 1})
    with app.app_context():
        assert URLSafeTimedSerializer(security.signing_keys(), salt="s").loads(old) == {"x": 1}
        assert security.signing_keys()[-1] == "nova"


def test_texto_da_pagina_de_privacidade(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    page = text_of(client.get("/app/privacidade"))
    assert "Exportar todos os dados" in page and "Excluir a empresa" in page
    login(client2 := app.test_client(), app, a.operator_email)
    assert client2.get("/app/privacidade").status_code == 403
