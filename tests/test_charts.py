"""Geometria do medidor SVG (app/services/charts.py): pura e coerente."""

from __future__ import annotations

import ast
from pathlib import Path

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
