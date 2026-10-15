"""Geometria dos gráficos SVG do painel (Etapa E).

PURO como calc.py: sem Flask, sem banco, só números e dicts. Aqui só há **desenho** (escalas,
retângulos, arcos); toda regra de negócio (progresso, horas, dias úteis, status) já vem pronta
de ``app/services/calc.py``. O template apenas imprime o que estas funções devolvem
(ADR-0009): nada de conta no navegador, nada de ``style=`` (CSP) — só atributos de geometria.

Convenções: coordenadas no sistema do ``viewBox`` de cada gráfico; arcos de rosca e medidor
usam ``pathLength="100"`` + ``stroke-dasharray`` (sem trigonometria no template).
"""

from __future__ import annotations

import math
from typing import Sequence

# ---------------------------------------------------------------------------
# Medidor (progresso geral) e rosca (status das etapas)
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


def rosca(segmentos: Sequence[tuple[str, str, float]]) -> dict:
    """Segmentos ``(chave, rótulo, valor)`` → arcos da rosca. Valores ≤ 0 não desenham arco.

    Cada arco: ``dash`` (dasharray) e ``offset`` (dashoffset) para um círculo com
    ``pathLength="100"`` girado em −90° (começa no topo, sentido horário).
    """
    total = sum(max(v, 0) for _, _, v in segmentos)
    arcos = []
    inicio = 0.0
    visiveis = sum(1 for _, _, v in segmentos if v > 0)
    vao = 0.8 if visiveis > 1 else 0.0  # fresta entre arcos (decorativa)
    for chave, rotulo, valor in segmentos:
        fracao = (max(valor, 0) / total * 100) if total else 0.0
        arco = None
        if valor > 0 and total:
            tamanho = max(fracao - vao, 0.01)
            arco = {"dash": f"{tamanho:.3f} {100 - tamanho:.3f}", "offset": f"{-inicio:.3f}"}
        arcos.append({"key": chave, "label": rotulo, "value": valor, "pct": fracao / 100, "arc": arco})
        inicio += fracao
    return {"total": total, "segmentos": arcos}


# ---------------------------------------------------------------------------
# Escalas
# ---------------------------------------------------------------------------


def teto_bonito(maximo: float, divisoes: int = 4) -> tuple[float, float]:
    """Menor teto “redondo” ≥ máximo e o passo entre as linhas de grade (``divisoes`` faixas)."""
    if not maximo or maximo <= 0:
        return float(divisoes), 1.0
    bruto = maximo / divisoes
    expoente = math.floor(math.log10(bruto))
    base = 10**expoente
    for fator in (1, 2, 2.5, 5, 10):
        passo = fator * base
        if passo * divisoes >= maximo - 1e-12:
            return passo * divisoes, passo
    return 10 * base * divisoes, 10 * base  # inalcançável; por segurança


# ---------------------------------------------------------------------------
# Colunas (simples ou empilhadas)
# ---------------------------------------------------------------------------


def colunas(
    itens: Sequence[dict],
    series: Sequence[str],
    *,
    passo: float = 24.0,
    altura: float = 140.0,
    margem_esq: float = 30.0,
    margem_dir: float = 6.0,
    margem_topo: float = 14.0,
    margem_base: float = 18.0,
    largura_coluna: float = 0.62,
    divisoes: int = 4,
    largura_minima: float = 0.0,
) -> dict:
    """Colunas empilhadas na ordem de ``series`` (a primeira fica embaixo).

    Cada item: ``{"label", "title", "valores": {serie: número}, "destaque": bool (opcional)}``.
    Devolve o viewBox, a grade (``ticks`` com valor numérico — o template formata) e, por item,
    os segmentos já em coordenadas do viewBox.
    """
    totais = [sum(max(i["valores"].get(s, 0) or 0, 0) for s in series) for i in itens]
    teto, passo_grade = teto_bonito(max(totais) if totais else 0, divisoes)
    largura_plot = max(len(itens) * passo, largura_minima - margem_esq - margem_dir)
    largura = margem_esq + largura_plot + margem_dir
    altura_total = margem_topo + altura + margem_base
    base_y = margem_topo + altura
    passo_real = largura_plot / len(itens) if itens else passo
    w = passo_real * largura_coluna
    ticks = []
    for k in range(divisoes + 1):
        valor = passo_grade * k
        ticks.append({"value": valor, "y": round(base_y - valor / teto * altura, 2)})
    cols = []
    for idx, item in enumerate(itens):
        x = margem_esq + passo_real * idx + (passo_real - w) / 2
        y_atual = base_y
        segs = []
        for s in series:
            v = max(item["valores"].get(s, 0) or 0, 0)
            h = v / teto * altura
            y_atual -= h
            segs.append({"serie": s, "valor": v, "x": round(x, 2), "y": round(y_atual, 2), "w": round(w, 2), "h": round(h, 2)})
        total = sum(max(item["valores"].get(s, 0) or 0, 0) for s in series)
        cols.append(
            {
                "label": item["label"],
                "title": item.get("title", item["label"]),
                "destaque": bool(item.get("destaque")),
                "cx": round(x + w / 2, 2),
                "x": round(x, 2),
                "w": round(w, 2),
                "topo": round(base_y - total / teto * altura, 2),
                "total": total,
                "segs": segs,
            }
        )
    return {
        "w": round(largura, 2),
        "h": round(altura_total, 2),
        "x0": margem_esq,
        "x1": round(largura - margem_dir, 2),
        "base": round(base_y, 2),
        "label_y": round(base_y + 13, 2),
        "ticks": ticks,
        "cols": cols,
        "teto": teto,
    }


# ---------------------------------------------------------------------------
# Treemap (retângulos proporcionais ao peso; algoritmo “squarified”)
# ---------------------------------------------------------------------------


def _pior_razao(linha: list[float], lado: float) -> float:
    soma = sum(linha)
    if soma <= 0 or lado <= 0:
        return math.inf
    return max(max(lado * lado * a / (soma * soma), soma * soma / (lado * lado * a)) for a in linha)


def treemap(pesos: Sequence[float], largura: float = 100.0, altura: float = 70.0) -> list[dict | None]:
    """Retângulos ``{x, y, w, h}`` na mesma ordem de ``pesos``; ``None`` para peso ≤ 0.

    Áreas proporcionais aos pesos (preenchem exatamente largura × altura). O arredondamento
    para 3 casas não deixa vãos visíveis.
    """
    saida: list[dict | None] = [None] * len(pesos)
    indices = [i for i, p in sorted(enumerate(pesos), key=lambda t: -t[1]) if p and p > 0]
    total = sum(pesos[i] for i in indices)
    if not indices or total <= 0:
        return saida
    area_total = largura * altura
    areas = {i: pesos[i] / total * area_total for i in indices}
    x, y, w, h = 0.0, 0.0, float(largura), float(altura)
    fila = list(indices)
    while fila:
        lado = min(w, h)
        linha = [fila[0]]
        resto = fila[1:]
        while resto and _pior_razao([areas[i] for i in linha + [resto[0]]], lado) <= _pior_razao(
            [areas[i] for i in linha], lado
        ):
            linha.append(resto.pop(0))
        soma = sum(areas[i] for i in linha)
        if w >= h:  # coluna à esquerda
            larg_col = soma / h if h else 0
            yy = y
            for i in linha:
                hh = areas[i] / larg_col if larg_col else 0
                saida[i] = {"x": round(x, 3), "y": round(yy, 3), "w": round(larg_col, 3), "h": round(hh, 3)}
                yy += hh
            x += larg_col
            w -= larg_col
        else:  # faixa no topo
            alt_faixa = soma / w if w else 0
            xx = x
            for i in linha:
                ww = areas[i] / alt_faixa if alt_faixa else 0
                saida[i] = {"x": round(xx, 3), "y": round(y, 3), "w": round(ww, 3), "h": round(alt_faixa, 3)}
                xx += ww
            y += alt_faixa
            h -= alt_faixa
        fila = resto
    return saida


def cortar_texto(texto: str, largura: float, corpo: float, fator: float = 0.56) -> str:
    """Corta ``texto`` para caber em ``largura`` (unidades do viewBox) com fonte ``corpo``."""
    maximo = int(largura / (corpo * fator))
    if maximo <= 0:
        return ""
    if len(texto) <= maximo:
        return texto
    return texto[: max(maximo - 1, 1)].rstrip() + "…"
