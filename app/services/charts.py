"""Geometria do medidor SVG do painel (Etapa E; R9 manteve só o medidor).

PURO como calc.py: sem Flask, sem banco, só números e dicts. Aqui só há **desenho** (o arco do
medidor); toda regra de negócio (progresso, horas, dias úteis, status) já vem pronta
de ``app/services/calc.py``. O template apenas imprime o que estas funções devolvem
(ADR-0009): nada de conta no navegador, nada de ``style=`` (CSP) — só atributos de geometria.

Convenções: coordenadas no sistema do ``viewBox`` de cada gráfico; o arco do medidor
usa ``pathLength="100"`` + ``stroke-dasharray`` (sem trigonometria no template).
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Medidor (progresso geral)
# ---------------------------------------------------------------------------

GAUGE_ARC = 75.0  # o medidor ocupa 270° (75% do círculo); o vão fica embaixo


def _limitar(valor: float, baixo: float = 0.0, alto: float = 1.0) -> float:
    if valor != valor:  # NaN
        return baixo
    return max(baixo, min(alto, valor))


def medidor(progresso: float) -> dict:
    """Arco de 270° com ``progresso`` (0–1) preenchido. Devolve os dasharray (pathLength = 100)."""
    p = _limitar(progresso)
    return {
        "trilho": f"{GAUGE_ARC:.2f} {100 - GAUGE_ARC + 1:.2f}",
        "preenchido": f"{GAUGE_ARC * p:.2f} {100 - GAUGE_ARC * p + 1:.2f}",
        "pct": p,
    }

