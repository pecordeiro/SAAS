"""Monta os dados do Painel (reestruturação R2) a partir dos resultados de ``calc``.

Sem Flask e sem banco: recebe objetos simples (etapas com ``id``/``name``, o ``ResultadoProjeto``
já calculado por ``app/services/calc.py``, datas e funções que montam links) e devolve dicts
prontos para o template e para o JSON dos gráficos (ECharts lê esse JSON e só desenha).
Números do negócio vêm do calc; aqui só se organiza, rotula e formata (ADR-0009).

Duas visões:
- ``painel_projeto``: um projeto (cabeçalho, 5 indicadores, gráficos por etapa, tabelas);
- ``painel_operacao``: todos os projetos ativos (as mesmas seções, com um projeto por linha).
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Callable, Sequence

from app.formatting import br_date_short, br_hours, br_number, br_pct
from app.services import calc, charts

NOMES_VISUAIS = {
    calc.VISUAL_CONCLUIDA: "Concluída",
    calc.VISUAL_EM_ANDAMENTO: "Em andamento",
    calc.VISUAL_AGUARDANDO: "Aguardando peça",
    calc.VISUAL_ATRASADA: "Atrasada",
    calc.VISUAL_NAO_INICIADA: "Não iniciada",
}


_NUMERO_NO_INICIO = re.compile(r"^\s*\d+\s*[.)\-–—:]\s*")


def rotulo_etapa(n: int, nome: str) -> str:
    """“3. Montagem”. Se o nome já começa com número (“1. Preparação”), não repete: evita
    “1. 1. Preparação” (nomes vindos da planilha de referência já trazem a numeração)."""
    nome = (nome or "").strip()
    return nome if _NUMERO_NO_INICIO.match(nome) else f"{n}. {nome}"


def _plural(n: int, um: str, varios: str) -> str:
    return f"{n} {um if n == 1 else varios}"


def _dias(n: float | int | None) -> str:
    if n is None:
        return "—"
    return _plural(int(n), "dia útil", "dias úteis") if float(n).is_integer() else f"{br_number(n, 1)} dias úteis"


def _du(n) -> str:
    """Forma curta para o rodapé do indicador: “16 d.u.” (dias úteis)."""
    return f"{br_number(n, 0) if float(n).is_integer() else br_number(n, 1)} d.u."


# ---------------------------------------------------------------- prazo e frase-resumo


def situacao_prazo(deadline: dict, concluido: bool, prazo: date | None) -> dict:
    """Texto curto do prazo a partir de ``deadline`` (contas de calc via blueprint)."""
    if concluido:
        return {"tone": "success", "text": "concluído", "short": "concluído", "until": None}
    if prazo is None:
        return {"tone": "neutral", "text": "sem prazo definido", "short": "sem prazo definido", "until": None}
    if deadline.get("overdue"):
        return {
            "tone": "danger",
            "text": f"o prazo ({br_date_short(prazo)}) passou há {_dias(deadline['overdue'])}",
            "short": f"vencido há {_du(deadline['overdue'])}",
            "until": 0,
        }
    if deadline.get("late"):
        return {
            "tone": "danger",
            "text": f"termina {br_date_short(deadline['forecast'])}, atraso de {_dias(deadline['delay'])}",
            "short": f"atraso de {_du(deadline['delay'])}",
            "until": deadline.get("until_due"),
        }
    if deadline.get("on_time"):
        return {
            "tone": "success",
            "text": f"termina {br_date_short(deadline['forecast'])}, folga de {_dias(deadline['slack'])}",
            "short": f"folga de {_du(deadline['slack'])}",
            "until": deadline.get("until_due"),
        }
    return {"tone": "neutral", "text": f"prazo {br_date_short(prazo)}", "short": f"prazo {br_date_short(prazo)}", "until": deadline.get("until_due")}


def frase_projeto(nome: str, prazo_txt: dict, contagem: dict[str, int]) -> str:
    """Ex.: “Lote 10: termina 14/11, folga de 17 dias úteis, 3 etapas atrasadas”."""
    partes = [prazo_txt["text"]]
    if contagem.get(calc.VISUAL_ATRASADA):
        partes.append(_plural(contagem[calc.VISUAL_ATRASADA], "etapa atrasada", "etapas atrasadas"))
    if contagem.get(calc.VISUAL_AGUARDANDO):
        partes.append(_plural(contagem[calc.VISUAL_AGUARDANDO], "etapa aguardando peça", "etapas aguardando peça"))
    return f"{nome}: " + ", ".join(partes)


def frase_operacao(projetos: Sequence[dict], contagem: dict[str, int]) -> str:
    """Ex.: “3 projetos ativos: 1 com atraso, 2 no prazo · 4 etapas atrasadas”."""
    if not projetos:
        return "Nenhum projeto ativo."
    atraso = sum(1 for p in projetos if p["prazo"]["tone"] == "danger")
    no_prazo = sum(1 for p in projetos if p["prazo"]["tone"] == "success")
    partes = [_plural(len(projetos), "projeto ativo", "projetos ativos")]
    detalhes = []
    if atraso:
        detalhes.append(f"{atraso} com atraso")
    if no_prazo:
        detalhes.append(f"{no_prazo} no prazo")
    frase = partes[0] + (": " + ", ".join(detalhes) if detalhes else "")
    extras = []
    if contagem.get(calc.VISUAL_ATRASADA):
        extras.append(_plural(contagem[calc.VISUAL_ATRASADA], "etapa atrasada", "etapas atrasadas"))
    if contagem.get(calc.VISUAL_AGUARDANDO):
        extras.append(_plural(contagem[calc.VISUAL_AGUARDANDO], "etapa aguardando peça", "etapas aguardando peça"))
    return frase + ("; " + ", ".join(extras) if extras else "") + "."


# ---------------------------------------------------------------- etapas de um projeto


def etapas_do_painel(
    stages: Sequence[Any], result: calc.ResultadoProjeto, fracao_decorrida: float | None, aguardando_ativo: bool = True
) -> list[dict]:
    """Uma linha por etapa: números do calc + situação visual.
    ``aguardando_ativo=False`` (R6: módulo “aguardando peça” desligado) ignora a marca."""
    atrasos = calc.etapas_atrasadas(result.etapas, fracao_decorrida)
    etapas = []
    for i, (stage, r, atrasada) in enumerate(zip(stages, result.etapas, atrasos), start=1):
        aguardando = aguardando_ativo and bool(getattr(stage, "waiting_part", False))
        visual = calc.status_visual(r.status, aguardando, atrasada)
        etapas.append(
            {
                "n": i,
                "id": stage.id,
                "name": stage.name,
                "label": rotulo_etapa(i, stage.name),
                "r": r,
                "waiting_part": aguardando,
                "part_expected_on": getattr(stage, "part_expected_on", None),
                "atrasada": atrasada,
                "visual": visual,
                "visual_nome": NOMES_VISUAIS[visual],
                "pct_unidades": calc.razao(r.unidades, r.previstas),
                "trabalhado_h": (r.tempo_total_min - r.tempo_restante_min) / 60,
                "falta_h": r.tempo_restante_min / 60,
                "total_h": r.tempo_total_min / 60,
            }
        )
    return etapas


def _rosca(contagem: dict[str, int], aguardando_ativo: bool = True) -> list[dict]:
    return [
        {"key": k, "name": NOMES_VISUAIS[k], "value": contagem[k]}
        for k in calc.VISUAIS
        if aguardando_ativo or k != calc.VISUAL_AGUARDANDO
    ]


def _pendencias(etapas: Sequence[dict], projeto: str | None = None) -> list[dict]:
    pend = []
    for e in etapas:
        if e["visual"] not in (calc.VISUAL_ATRASADA, calc.VISUAL_AGUARDANDO):
            continue
        extra = ""
        if e["visual"] == calc.VISUAL_AGUARDANDO and e["part_expected_on"]:
            extra = f"peça prevista {br_date_short(e['part_expected_on'])}"
        pend.append({"etapa": e, "projeto": projeto, "extra": extra})
    # atrasadas primeiro, depois aguardando peça (cada grupo na ordem das etapas)
    pend.sort(key=lambda p: 0 if p["etapa"]["visual"] == calc.VISUAL_ATRASADA else 1)
    return pend


def _equipe(horas_restantes: float, hours_per_day: float, people: int) -> list[dict]:
    linhas = []
    for p, dias in calc.equipe_x_prazo(horas_restantes, hours_per_day):
        linhas.append(
            {
                "people": p,
                "label": _plural(p, "pessoa", "pessoas"),
                "days": None if dias is None else round(dias, 2),
                "daysText": "—" if dias is None else br_number(dias, 1),
                "current": p == people,
                "teamHours": br_number(p * hours_per_day, 0),
            }
        )
    return linhas


def painel_projeto(
    stages: Sequence[Any],
    result: calc.ResultadoProjeto,
    *,
    nome: str,
    quantity: int,
    people: int,
    hours_per_day: float,
    prazo: date | None,
    deadline: dict,
    concluido: bool,
    fracao_decorrida: float | None,
    href_etapa: Callable[[Any], str],
    aguardando_ativo: bool = True,
) -> dict:
    """Tudo o que o painel de um projeto mostra, de cima para baixo (plano §4.2)."""
    etapas = etapas_do_painel(stages, result, fracao_decorrida, aguardando_ativo)
    contagem = calc.contagem_visual(e["visual"] for e in etapas)
    prazo_txt = situacao_prazo(deadline, concluido, prazo)
    equipe = _equipe(result.tempo_restante_h, hours_per_day, people)
    linhas = [
        {
            "n": e["n"],
            "label": e["label"],
            "visual": e["visual"],
            "weight": round(max(e["r"].peso_no_projeto, 0), 4),
            "weightText": br_pct(e["r"].peso_no_projeto, 1),
            "tasks": round(min(max(e["r"].progresso, 0), 1), 4),
            "tasksText": br_pct(e["r"].progresso, 0),
            "units": round(min(max(e["pct_unidades"], 0), 1), 4),
            "unitsText": br_pct(e["pct_unidades"], 0),
            "unitsFrac": f"{e['r'].unidades}/{e['r'].previstas}",
            "worked": round(e["trabalhado_h"], 2),
            "workedText": br_hours(e["trabalhado_h"]),
            "left": round(e["falta_h"], 2),
            "leftText": br_hours(e["falta_h"]),
            "status": e["visual_nome"],
            "href": href_etapa(e["id"]),
        }
        for e in etapas
    ]
    return {
        "kind": "projeto",
        "aguardando_ativo": aguardando_ativo,
        "frase": frase_projeto(nome, prazo_txt, contagem),
        "prazo": prazo_txt,
        "etapas": etapas,
        "medidor": charts.medidor(result.progresso_geral),
        "unidades_pct": calc.razao(result.unidades_concluidas, quantity),
        "unidades_etapas_pct": calc.razao(result.unidades_etapas, result.unidades_etapas_previstas),
        "contagem": contagem,
        "pendencias": [dict(x, href=href_etapa(x["etapa"]["id"])) for x in _pendencias(etapas)],
        "equipe": equipe,
        "equipe_atual": next((x for x in equipe if x["current"]), None),
        "sem_tempo": calc.etapas_sem_tempo(result.etapas),
        "grafico": {
            "kind": "etapas",
            "rows": linhas,
            "status": _rosca(contagem, aguardando_ativo),
            "team": {"rows": equipe, "due": prazo_txt["until"]},
        },
    }


# ---------------------------------------------------------------- operação (todos os projetos)


def painel_operacao(itens: Sequence[dict], href_etapa: Callable[[Any, Any], str], href_projeto: Callable[[Any], str],
                    aguardando_ativo: bool = True) -> dict:
    """Painel geral. ``itens``: um dict por projeto ativo com ``project``, ``stages``, ``result``,
    ``deadline``, ``concluido`` e ``fracao`` (calculados pelo blueprint via calc/svc)."""
    projetos = []
    todas = []
    for it in itens:
        p, r = it["project"], it["result"]
        etapas = etapas_do_painel(it["stages"], r, it["fracao"], aguardando_ativo)
        todas.extend(etapas)
        prazo_txt = situacao_prazo(it["deadline"], it["concluido"], p.due_date)
        projetos.append(
            {
                "project": p,
                "result": r,
                "etapas": etapas,
                "prazo": prazo_txt,
                "deadline": it["deadline"],
                "contagem": calc.contagem_visual(e["visual"] for e in etapas),
                "unidades_pct": calc.razao(r.unidades_concluidas, p.quantity),
                "href": href_projeto(p.id),
                "pendencias": [dict(x, projeto=p.name, href=href_etapa(p.id, x["etapa"]["id"])) for x in _pendencias(etapas)],
            }
        )
    resumo = calc.resumo_operacao([it["result"] for it in itens])
    contagem = calc.contagem_visual(e["visual"] for e in todas)
    # Próximo prazo: o projeto em aberto com a data de prazo mais próxima (KPI "dias úteis até o prazo").
    com_prazo = [p for p in projetos if p["project"].due_date and p["prazo"]["until"] is not None]
    proximo = min(com_prazo, key=lambda p: p["project"].due_date) if com_prazo else None
    linhas = [
        {
            "label": p["project"].name,
            "tasks": round(min(max(p["result"].progresso_geral, 0), 1), 4),
            "tasksText": br_pct(p["result"].progresso_geral, 0),
            "units": round(min(max(p["unidades_pct"], 0), 1), 4),
            "unitsText": br_pct(p["unidades_pct"], 0),
            "unitsFrac": f"{p['result'].unidades_concluidas}/{p['project'].quantity}",
            "worked": round(p["result"].tempo_trabalhado_h, 2),
            "workedText": br_hours(p["result"].tempo_trabalhado_h),
            "left": round(p["result"].tempo_restante_h, 2),
            "leftText": br_hours(p["result"].tempo_restante_h),
            "status": p["prazo"]["text"],
            "href": p["href"],
        }
        for p in projetos
    ]
    prazo_linhas = [
        {
            "label": p["project"].name,
            "need": None if p["result"].dias_uteis_restantes is None else round(p["result"].dias_uteis_restantes, 2),
            "needText": "—" if p["result"].dias_uteis_restantes is None else br_number(p["result"].dias_uteis_restantes, 1),
            "until": p["prazo"]["until"],
            "untilText": "—" if p["prazo"]["until"] is None else str(p["prazo"]["until"]),
            "href": p["href"],
        }
        for p in projetos
    ]
    return {
        "kind": "operacao",
        "aguardando_ativo": aguardando_ativo,
        "frase": frase_operacao(projetos, contagem),
        "projetos": projetos,
        "resumo": resumo,
        "medidor": charts.medidor(resumo.progresso_geral),
        "unidades_pct": calc.razao(resumo.unidades_concluidas, resumo.previstas),
        "contagem": contagem,
        "pendencias": [x for p in projetos for x in p["pendencias"]],
        "proximo": proximo,
        "grafico": {
            "kind": "projetos",
            "rows": linhas,
            "status": _rosca(contagem, aguardando_ativo),
            "deadline": {"rows": prazo_linhas},
        },
    }
