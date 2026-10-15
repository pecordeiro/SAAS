"""Geometria dos gráficos SVG (app/services/charts.py, Etapa E): pura e coerente."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.services import charts

CHARTS_PATH = Path(__file__).resolve().parents[1] / "app" / "services" / "charts.py"


def test_charts_e_puro():
    tree = ast.parse(CHARTS_PATH.read_text(encoding="utf-8"))
    importados: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            importados.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            importados.add(node.module.split(".")[0])
    assert not importados & {"flask", "sqlalchemy", "app", "werkzeug", "flask_login", "jinja2"}


def test_medidor_limita_e_proporciona():
    assert charts.medidor(0.5)["preenchido"].startswith("37.50 ")  # 75% × 0,5
    assert charts.medidor(2)["pct"] == 1.0 and charts.medidor(-1)["pct"] == 0.0
    assert charts.medidor(float("nan"))["pct"] == 0.0


def test_rosca_fracoes_somam_100_e_pulam_zeros():
    r = charts.rosca([("a", "A", 1), ("b", "B", 14), ("c", "C", 9), ("d", "D", 0)])
    assert r["total"] == 24
    assert sum(s["pct"] for s in r["segmentos"]) == pytest.approx(1.0)
    assert r["segmentos"][3]["arc"] is None
    # o segundo arco começa depois do primeiro (offset negativo = avança no sentido horário)
    assert float(r["segmentos"][1]["arc"]["offset"]) == pytest.approx(-100 / 24, abs=1e-3)


def test_rosca_vazia_e_segmento_unico():
    assert charts.rosca([("a", "A", 0)])["segmentos"][0]["arc"] is None
    unico = charts.rosca([("a", "A", 5), ("b", "B", 0)])["segmentos"][0]["arc"]
    assert unico["dash"].startswith("100.000 ")  # sem fresta quando só há um arco


@pytest.mark.parametrize("maximo,esperado", [(0, 4), (3.7, 4), (21.7, 40), (160.5, 200), (0.9, 1)])
def test_teto_bonito(maximo, esperado):
    teto, passo = charts.teto_bonito(maximo)
    assert teto == pytest.approx(esperado)
    assert teto >= maximo and passo * 4 == pytest.approx(teto)


def test_colunas_empilhadas_somam_a_altura_do_total():
    itens = [
        {"label": "1", "valores": {"feito": 3, "falta": 2}},
        {"label": "2", "valores": {"feito": 0, "falta": 10}, "destaque": True},
    ]
    g = charts.colunas(itens, ["feito", "falta"], altura=100)
    assert g["teto"] == 10
    c1, c2 = g["cols"]
    assert sum(s["h"] for s in c1["segs"]) == pytest.approx(50)  # 5 de 10 → metade da altura
    assert c2["segs"][1]["h"] == pytest.approx(100) and c2["destaque"]
    assert c1["segs"][1]["y"] + c1["segs"][1]["h"] == pytest.approx(c1["segs"][0]["y"], abs=0.02)  # empilha
    assert [t["value"] for t in g["ticks"]] == [0, 2.5, 5, 7.5, 10]


def test_treemap_preenche_a_area_e_proporciona():
    pesos = [6, 6, 4, 3, 2, 2, 1, 0]
    rects = charts.treemap(pesos, 100, 70)
    assert rects[-1] is None  # peso 0 não ocupa área
    area_total = sum(r["w"] * r["h"] for r in rects if r)
    assert area_total == pytest.approx(100 * 70, rel=1e-3)
    for p, r in zip(pesos, rects):
        if r:
            assert r["w"] * r["h"] == pytest.approx(p / sum(pesos) * 7000, rel=1e-2)
            assert -1e-6 <= r["x"] and r["x"] + r["w"] <= 100.001 and r["y"] + r["h"] <= 70.001


def test_treemap_vazio_e_um_so():
    assert charts.treemap([0, 0]) == [None, None]
    assert charts.treemap([5], 100, 70)[0] == {"x": 0.0, "y": 0.0, "w": 100.0, "h": 70.0}


def test_cortar_texto():
    assert charts.cortar_texto("Montagem do suporte", 100, 3) == "Montagem do suporte"
    assert charts.cortar_texto("Montagem do suporte", 20, 3).endswith("…")
    assert charts.cortar_texto("Montagem", 1, 3) == ""
