"""Monta os dados do painel do projeto (Etapa E) a partir do resultado de ``calc``.

Sem Flask e sem banco: recebe nomes/ids das etapas e o ``ResultadoProjeto`` já calculado por
``app/services/calc.py`` e devolve dicts prontos para o template — números do negócio vêm do
calc, desenho (escalas, retângulos, arcos) vem de ``app/services/charts.py``. O template só
imprime (ADR-0009).
"""

from __future__ import annotations

from typing import Any, Sequence

from app.services import calc, charts

# Treemap: área do viewBox e tamanhos de fonte (unidades do viewBox).
TREEMAP_W, TREEMAP_H = 100.0, 64.0
TREEMAP_FONT = 3.2
TREEMAP_FAIXA = 1.3  # altura da faixa de progresso no pé de cada retângulo

STATUS_CLASSE = {
    calc.STATUS_CONCLUIDA: "done",
    calc.STATUS_EM_ANDAMENTO: "doing",
    calc.STATUS_NAO_INICIADA: "todo",
}


def build(
    stages: Sequence[Any],
    result: calc.ResultadoProjeto,
    *,
    quantity: int,
    people: int,
    hours_per_day: float,
) -> dict:
    """``stages``: objetos com ``id`` e ``name``, na mesma ordem de ``result.etapas``."""
    etapas = []
    for i, (stage, r) in enumerate(zip(stages, result.etapas), start=1):
        etapas.append(
            {
                "n": i,
                "id": stage.id,
                "name": stage.name,
                "r": r,
                "pct_unidades": calc.razao(r.unidades, r.previstas),
                "trabalhado_h": r.tempo_trabalhado_min / 60,
                "falta_h": r.tempo_restante_min / 60,
                "total_h": r.tempo_total_min / 60,
            }
        )

    contagem = calc.contagem_status(result.etapas)
    status_rosca = charts.rosca(
        [
            ("done", calc.STATUS_CONCLUIDA, contagem[calc.STATUS_CONCLUIDA]),
            ("doing", calc.STATUS_EM_ANDAMENTO, contagem[calc.STATUS_EM_ANDAMENTO]),
            ("todo", calc.STATUS_NAO_INICIADA, contagem[calc.STATUS_NAO_INICIADA]),
        ]
    )

    # Treemap: tamanho = peso da etapa no projeto; sem tempo definido não ocupa área.
    rects = charts.treemap([e["r"].peso_no_projeto for e in etapas], TREEMAP_W, TREEMAP_H)
    treemap = []
    for e, rect in zip(etapas, rects):
        if rect is None:
            continue
        mostra_nome = rect["w"] >= 15 and rect["h"] >= 9
        mostra_pct = rect["w"] >= 7 and rect["h"] >= 6
        nome = charts.cortar_texto(f"{e['n']}. {e['name']}", rect["w"] - 2, TREEMAP_FONT) if mostra_nome else ""
        curto = charts.cortar_texto(str(e["n"]), rect["w"] - 2, TREEMAP_FONT)
        treemap.append(
            {
                **rect,
                "etapa": e,
                "classe": STATUS_CLASSE[e["r"].status],
                "nome": nome,
                "curto": curto if (mostra_pct and not mostra_nome) else "",
                "mostra_pct": mostra_pct,
                "faixa_w": round(rect["w"] * min(max(e["r"].progresso, 0), 1), 3),
                "faixa_y": round(rect["y"] + rect["h"] - TREEMAP_FAIXA, 3),
            }
        )

    horas = charts.colunas(
        [
            {
                "label": str(e["n"]),
                "title": f"{e['n']}. {e['name']}",
                "valores": {"trabalhadas": e["trabalhado_h"], "faltam": e["falta_h"]},
            }
            for e in etapas
        ],
        ["trabalhadas", "faltam"],
        passo=22,
        largura_minima=300,
    )

    tabela_equipe = calc.equipe_x_prazo(result.tempo_restante_h, hours_per_day)
    equipe = charts.colunas(
        [
            {
                "label": f"{p} pessoa" if p == 1 else f"{p} pessoas",
                "title": f"{p} pessoa" if p == 1 else f"{p} pessoas",
                "valores": {"dias": dias or 0},
                "destaque": p == people,
                "dias": dias,
            }
            for p, dias in tabela_equipe
        ],
        ["dias"],
        passo=50,
        largura_coluna=0.5,
        largura_minima=0,
        margem_base=30,
    )
    for col, (_, dias) in zip(equipe["cols"], tabela_equipe):
        col["dias"] = dias

    return {
        "etapas": etapas,
        "quantity": quantity,
        "medidor": charts.medidor(result.progresso_geral),
        "unidades_pct": calc.razao(result.unidades_concluidas, quantity),
        "unidades_etapas_pct": calc.razao(result.unidades_etapas, result.unidades_etapas_previstas),
        "tarefas_pct": calc.razao(result.tarefas_concluidas, result.tarefas),
        "contagem": contagem,
        "rosca": status_rosca,
        "treemap": treemap,
        "treemap_w": TREEMAP_W,
        "treemap_h": TREEMAP_H,
        "treemap_font": TREEMAP_FONT,
        "sem_tempo": calc.etapas_sem_tempo(result.etapas),
        "horas": horas,
        "equipe": equipe,
        "equipe_atual": next((c for c in equipe["cols"] if c["destaque"]), None),
        "people": people,
        "hours_per_day": hours_per_day,
    }
