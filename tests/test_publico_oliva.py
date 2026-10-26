"""R10 (ADR-0016): site público na identidade oliva. Páginas, textos-chave, só tokens, CSP e fontes locais."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.blueprints.public import THEME_COLORS

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
PAGES = ("/", "/precos", "/como-funciona", "/termos", "/privacidade", "/contato")


def _tokens() -> str:
    return (STATIC / "css" / "tokens.css").read_text(encoding="utf-8")


def _token_value(name: str, block: str | None = None) -> str:
    text = block if block is not None else _tokens()
    return re.search(rf"--{name}:\s*(#[0-9A-Fa-f]{{6}})", text).group(1).upper()


@pytest.mark.parametrize("path", PAGES)
def test_paginas_publicas_respondem_e_usam_a_marca(client, path):
    response = client.get(path)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "site--marca" in html
    assert 'rel="canonical"' in html and 'property="og:title"' in html and 'name="description"' in html
    assert html.count('name="theme-color"') == 2
    assert "publico" in html and "dm-sans-latin-400-normal.woff2" in html
    # Sem estilo inline, sem script inline e sem recurso externo (CSP default-src 'self').
    assert not re.search(r"\sstyle=", html)
    assert not re.search(r"<style\b", html)
    assert not re.search(r"<script(?![^>]*\bsrc=)", html)
    assert not re.search(r"<script\b[^>]*src=\"https?://|<link\b[^>]*rel=\"(?:stylesheet|preload)\"[^>]*https?://", html)


def test_titulo_e_textos_chave_do_inicio(client):
    html = client.get("/").get_data(as_text=True)
    for text in ("Saiba", "lote.", "Três passos, sem treinamento longo.", "Funciona com a planilha que você já tem.",
                 "Perguntas frequentes", "Descubra onde cada lote está hoje.", "Começar teste grátis de 14 dias"):
        assert text in html, text
    # preços e limites vêm da tabela plans
    assert "249,90" in html and "Sob orçamento" in html and "Recomendado" in html


def test_precos_mostra_14_dias_gratis(client):
    html = client.get("/precos").get_data(as_text=True)
    # Regressão: o macro do card perdia trial_days e saía "dias grátis, sem cartão" sem o número.
    assert html.count("<span>14 dias grátis, sem cartão</span>") == 2  # cards do Essencial e do Profissional
    assert "<span> dias grátis" not in html
    assert "Preço por empresa, não por pessoa." in html


def test_como_funciona_com_a_sua_planilha(client):
    html = client.get("/como-funciona").get_data(as_text=True)
    assert "Como funciona com a sua planilha" in html and "Quais colunas são quais?" in html
    assert "/como-funciona" in client.get("/sitemap.xml").get_data(as_text=True)


def test_area_logada_e_login_nao_usam_a_marca(client):
    html = client.get("/entrar").get_data(as_text=True)
    assert "site--marca" not in html


def test_theme_color_confere_com_tokens():
    tokens = _tokens()
    assert THEME_COLORS["marca"]["light"] == _token_value("color-brand-bg")
    assert THEME_COLORS["app"]["light"] == _token_value("color-bg")
    dark = tokens.split(":root[data-theme=\"dark\"] {")[1]
    assert THEME_COLORS["marca"]["dark"] == _token_value("color-brand-bg", dark)
    assert THEME_COLORS["app"]["dark"] == _token_value("color-bg", dark)


def test_fontes_da_marca_locais_com_licenca():
    for name in ("newsreader-latin-400-normal.woff2", "newsreader-latin-400-italic.woff2",
                 "dm-sans-latin-400-normal.woff2", "dm-sans-latin-700-normal.woff2"):
        assert (STATIC / "fonts" / name).read_bytes()[:4] == b"wOF2", name
    for name in ("OFL-Newsreader.txt", "OFL-DMSans.txt"):
        assert "SIL Open Font License" in (STATIC / "fonts" / name).read_text(encoding="utf-8")
    base = (STATIC / "css" / "base.css").read_text(encoding="utf-8")
    assert 'font-family: "Newsreader"' in base and 'font-family: "DM Sans"' in base


def test_marca_so_no_site_publico():
    """Tokens de marca ficam fora da área logada: só publico.css, tokens.css e o logotipo os usam."""
    users = [p.name for p in (STATIC / "css").glob("*.css") if "--color-brand" in p.read_text(encoding="utf-8")]
    assert sorted(users) == ["publico.css", "tokens.css"]
    for path in (ROOT / "app" / "templates").rglob("*.html"):
        assert "color-brand" not in path.read_text(encoding="utf-8"), path.name


def test_dados_nao_usam_a_cor_da_marca():
    """O anel e a esteira do painel de exemplo usam só cores de status."""
    css = (STATIC / "css" / "publico.css").read_text(encoding="utf-8")
    for selector in (".pub-ring__fg", ".pub-seg--done", ".pub-seg--doing", ".pub-seg--todo", ".pub-dot--done", ".pub-dot--doing", ".pub-dot--todo"):
        rule = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css).group(1)
        assert "color-status" in rule and "color-brand" not in rule, selector


def test_animacoes_respeitam_movimento_reduzido():
    css = (STATIC / "css" / "publico.css").read_text(encoding="utf-8")
    js = (STATIC / "js" / "publico.js").read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in css and "prefers-reduced-motion: reduce" in js
    assert "IntersectionObserver" in js
    assert "eval(" not in js and "innerHTML" not in js
