"""Base visual (Fase 2): só tokens, nada de CDN, /estilo só em development, tema e assets."""

from __future__ import annotations

import re
import struct
from pathlib import Path

import pytest

from app import create_app
from tests.conftest import login, post

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "app" / "templates"
STATIC = ROOT / "app" / "static"
CSS = STATIC / "css"

HEX_COLOR = re.compile(r"(?<![\w&])#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
COLOR_FUNC = re.compile(r"\b(?:rgba?|hsla?)\(", re.IGNORECASE)
PX_VALUE = re.compile(r"\d*\.?\d+px\b", re.IGNORECASE)
EXTERNAL_ASSET = re.compile(r"<(?:link|script)\b[^>]*https?://", re.IGNORECASE)


def _files(folder: Path, pattern: str) -> list[Path]:
    files = sorted(folder.rglob(pattern))
    assert files, f"nenhum arquivo {pattern} em {folder}"
    return files


def _offenders(files, *patterns) -> list[str]:
    found = []
    for path in files:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for pattern in patterns:
                for match in pattern.finditer(line):
                    found.append(f"{path.name}:{number}: {match.group(0)}")
    return found


# ---------------------------------------------------------------- só tokens


def test_templates_sem_cor_nem_px_soltos():
    offenders = _offenders(_files(TEMPLATES, "*.html"), HEX_COLOR, COLOR_FUNC, PX_VALUE)
    assert not offenders, "cor/px fora de tokens.css:\n" + "\n".join(offenders)


def test_css_de_componentes_so_usa_tokens():
    files = [p for p in _files(CSS, "*.css") if p.name != "tokens.css"]
    offenders = _offenders(files, HEX_COLOR, COLOR_FUNC, PX_VALUE)
    assert not offenders, "cor/px fora de tokens.css:\n" + "\n".join(offenders)


def test_css_em_camadas():
    for path in _files(CSS, "*.css"):
        if path.name == "tokens.css":
            continue
        text = path.read_text(encoding="utf-8")
        assert "@layer " in text, f"{path.name} fora de @layer"
    assert "@layer base, layout, components, utilities;" in (CSS / "base.css").read_text(encoding="utf-8")


def test_tokens_css_e_copia_do_handoff():
    assert (CSS / "tokens.css").read_bytes() == (ROOT / "docs" / "design" / "tokens.css").read_bytes()


def test_detector_pega_violacoes(tmp_path):
    sample = tmp_path / "x.html"
    sample.write_text('<p class="a">#fff</p>\n<div>rgb(1 2 3)</div>\n<span>12px</span>\n<a href="#fechar">ok</a>', encoding="utf-8")
    found = _offenders([sample], HEX_COLOR, COLOR_FUNC, PX_VALUE)
    assert len(found) == 3, found


# ---------------------------------------------------------------- CSP / CDN


def test_nenhum_asset_externo_nos_templates():
    offenders = _offenders(_files(TEMPLATES, "*.html"), EXTERNAL_ASSET)
    assert not offenders, "CDN/asset externo:\n" + "\n".join(offenders)


def test_sem_script_ou_estilo_inline_nos_templates():
    for path in _files(TEMPLATES, "*.html"):
        text = path.read_text(encoding="utf-8")
        # Bloco de dados JSON (não executa; a CSP não precisa liberar nada) é a única exceção.
        assert not re.search(r'<script(?![^>]*\bsrc=)(?![^>]*type="application/json")[^>]*>', text, re.IGNORECASE), f"script inline em {path.name}"
        assert not re.search(r"<style\b", text, re.IGNORECASE), f"<style> em {path.name}"
        assert not re.search(r"\sstyle=", text, re.IGNORECASE), f"atributo style em {path.name}"
        assert not re.search(r"\son[a-z]+=", text), f"handler inline em {path.name}"


def test_csp_estrita_e_htmx_sem_eval(client):
    response = client.get("/")
    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp and "unsafe-inline" not in csp and "unsafe-eval" not in csp
    html = response.get_data(as_text=True)
    assert '"allowEval":false' in html
    # Assets minificados com hash no nome (scripts/build_assets.py); sem build, os fontes.
    assert re.search(r"/static/(dist/htmx\.[0-9a-f]{10}\.js|js/htmx\.min\.js)", html)
    assert re.search(r"/static/(dist/app\.[0-9a-f]{10}\.js|js/app\.js)", html)


def test_assets_locais_existem():
    htmx = (STATIC / "js" / "htmx.min.js").read_text(encoding="utf-8")
    assert 'version:"2.0.4"' in htmx
    # ADR-0015: IBM Plex Sans 400 e 600, servida pelo próprio site; a Geist saiu.
    for name in ("ibm-plex-sans-latin-400-normal.woff2", "ibm-plex-sans-latin-600-normal.woff2"):
        assert (STATIC / "fonts" / name).read_bytes()[:4] == b"wOF2", name
    assert "SIL Open Font License" in (STATIC / "fonts" / "OFL-IBMPlexSans.txt").read_text(encoding="utf-8")
    assert not list((STATIC / "fonts").glob("geist-*"))
    # ECharts vendorizado (sem CDN, regra 8) com a licença Apache-2.0 e o NOTICE ao lado.
    vendor = STATIC / "vendor" / "echarts-5.5.1"
    assert 'version="5.5.1"' in (vendor / "echarts.min.js").read_text(encoding="utf-8")
    assert "Apache License" in (vendor / "LICENSE").read_text(encoding="utf-8")
    assert "Apache ECharts" in (vendor / "NOTICE").read_text(encoding="utf-8")


@pytest.mark.parametrize("name,size", [("favicon-32.png", (32, 32)), ("apple-touch-icon.png", (180, 180)), ("og-image.png", (1200, 630))])
def test_imagens_da_marca(name, size):
    data = (STATIC / "img" / name).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", data[16:24]) == size


def test_arquivos_estaticos_servidos(client):
    for path in ("/static/css/tokens.css", "/static/js/htmx.min.js", "/static/img/logo.svg", "/static/img/favicon.svg"):
        assert client.get(path).status_code == 200, path


# ---------------------------------------------------------------- /estilo


def _app(env: str):
    overrides = {"SQLALCHEMY_DATABASE_URI": "sqlite://", "SECRET_KEY": "x" * 32, "RATELIMIT_ENABLED": False,
                 "APP_BASE_URL": "https://app.exemplo.com.br"}
    return create_app(env, overrides)


@pytest.mark.parametrize("env", ["production", "staging", "test"])
def test_estilo_404_fora_de_development(env):
    app = _app(env)
    assert app.test_client().get("/estilo").status_code == 404


def test_estilo_em_development_mostra_componentes():
    app = _app("development")
    response = app.test_client().get("/estilo")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for marker in ("btn--primary", "btn--danger", "field--error", "stepper", "table--cards", "kpi__value",
                   "progress__bar", "badge--success", "alert--warning", "toast", "sheet--dialog", "empty",
                   "pagination", "chart-h", "chart-v", "bottom-nav", "sidebar__nav", "--color-primary"):
        assert marker in html, marker


# ---------------------------------------------------------------- tema


def test_tema_grava_cookie_e_volta_para_a_pagina(client, app):
    response = post(client, app, "/tema", {"tema": "dark", "next": "/entrar"})
    assert response.status_code == 303
    assert response.headers["Location"].endswith("/entrar")
    assert "tema=dark" in response.headers["Set-Cookie"]
    assert 'data-theme="dark"' in client.get("/entrar").get_data(as_text=True)
    post(client, app, "/tema", {"tema": "system", "next": "/entrar"})
    assert "data-theme" not in client.get("/entrar").get_data(as_text=True).split("<head>")[0]


def test_tema_rejeita_valor_invalido_e_open_redirect(client, app):
    assert post(client, app, "/tema", {"tema": "roxo"}).status_code == 400
    response = post(client, app, "/tema", {"tema": "light", "next": "https://evil.example/"})
    assert response.headers["Location"].endswith("/")
    assert "evil" not in response.headers["Location"]
    assert client.post("/tema", data={"tema": "dark"}).status_code == 400  # sem CSRF


def test_cookie_de_tema_invalido_e_ignorado(client):
    client.set_cookie("tema", '"><script>')
    html = client.get("/").get_data(as_text=True)
    assert "data-theme" not in html.split("<head>")[0]


# ---------------------------------------------------------------- telas


def test_layout_logado_tem_menu_empresa_e_papel(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    html = client.get("/app/projetos").get_data(as_text=True)
    assert "app-sidebar" in html and "bottom-nav" in html
    assert "Empresa A" in html and "Proprietário" in html
    assert 'name="tema"' in html


def test_detalhe_tem_registro_em_dois_toques(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    html = client.get(f"/app/projetos/{a.project_id}").get_data(as_text=True)
    # toque 1: link da atividade abre a folha (âncora, funciona sem JS) já com 1
    assert f'href="#registrar-{a.activity_id}"' in html
    assert f'id="registrar-{a.activity_id}"' in html
    assert 'name="delta" value="1"' in html
    # toque 2: botão Registrar do formulário POST (HTMX só melhora)
    assert f'action="/app/atividades/{a.activity_id}/registrar"' in html
    assert "data-register-label" in html and "+1 <span" in html
    assert f'hx-post="/app/atividades/{a.activity_id}/registrar"' in html and 'hx-swap="none"' in html


def test_erro_de_registro_reabre_a_folha(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    response = post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 50, "version": 1})
    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert f'class="sheet register is-open" id="registrar-{a.activity_id}"' in html
    assert "Máximo 10" in html


def test_paginas_de_erro_usam_layout_certo(client, app, tenants):
    assert "site-header" in client.get("/nao-existe").get_data(as_text=True)
    a, _ = tenants
    login(client, app, a.operator_email)
    html = client.get("/app/projetos/novo").get_data(as_text=True)
    assert "app-sidebar" in html and "Você não tem permissão" in html


def test_toast_de_registro(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    response = post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 2}, follow_redirects=True)
    assert "+2 em Atividade 1 · 2 de 10" in response.get_data(as_text=True)

