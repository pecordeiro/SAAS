"""Identidade Teroz (ADR-0020): logotipo vetorial, variantes, ícones e troca claro/escuro sem JavaScript."""

import struct
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "app" / "static" / "img"

SVGS = [
    "logo.svg", "logo-escuro.svg", "logo-1cor.svg", "simbolo.svg", "simbolo-escuro.svg",
    "favicon.svg", "icone-claro.svg", "icone-oliva.svg", "icone-preto.svg",
]


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def test_variantes_do_logotipo_sao_svg_validos_e_seguros():
    for name in SVGS:
        text = (IMG / name).read_text(encoding="utf-8")
        root = ElementTree.fromstring(text)
        assert root.tag.endswith("svg"), name
        low = text.lower()
        assert "<script" not in low and "onload" not in low and "<foreignobject" not in low, name
        assert "viewbox" in low, name


def test_logotipo_horizontal_e_simbolo_tem_proporcao_esperada():
    box = ElementTree.fromstring((IMG / "logo.svg").read_text()).get("viewBox").split()
    w, h = float(box[2]), float(box[3])
    assert abs(w / h - 3.876) < 0.05  # usada em components/brand.html
    sbox = ElementTree.fromstring((IMG / "simbolo.svg").read_text()).get("viewBox").split()
    assert abs(float(sbox[2]) / float(sbox[3]) - 1.696) < 0.02


def test_icones_png_tem_os_tamanhos_certos():
    assert _png_size(IMG / "favicon-16.png") == (16, 16)
    assert _png_size(IMG / "favicon-32.png") == (32, 32)
    assert _png_size(IMG / "apple-touch-icon.png") == (180, 180)
    assert _png_size(IMG / "og-image.png") == (1200, 630)


def test_paginas_trazem_logotipo_claro_e_escuro_e_favicons(tenants, client):
    html = client.get("/").get_data(as_text=True)
    assert "img/logo.svg" in html and "img/logo-escuro.svg" in html
    assert 'rel="icon"' in html and "favicon-16.png" in html and "favicon-32.png" in html
    assert "style=" not in html  # CSP estrita: nenhum estilo em linha


def test_css_troca_logotipo_por_tema_sem_javascript():
    css = (ROOT / "app" / "static" / "css" / "layout.css").read_text(encoding="utf-8")
    assert ".brand__logo--escuro { display: none; }" in css
    assert 'data-theme="dark"] .brand__logo--escuro' in css
    assert "prefers-color-scheme: dark" in css


def test_area_logada_mostra_so_o_simbolo(client, app, tenants):
    from tests.conftest import login

    login(client, app, tenants[0].owner_email)
    html = client.get("/app/").get_data(as_text=True)
    assert "img/simbolo.svg" in html and "img/simbolo-escuro.svg" in html
