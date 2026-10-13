"""Regras de cálculo do Controle de Produção.

Reproduz as fórmulas da planilha de referência
``docs/referencia/acompanhamento_montagem_v4.xlsx`` (ver ``docs/plano/arquitetura.md`` §1.1).

Este módulo é PURO: não importa Flask, SQLAlchemy nem nada de banco. Recebe tipos simples
(números, datas, dataclasses) e devolve tipos simples. Tempos de atividade em minutos por
unidade ("tempo ideal"); horas só nos resumos.

Correspondência com a planilha (aba Acompanhamento, etapa nas linhas 12–24):
- peso na etapa ............ C15 = B15 / B23
- % da subatividade ........ E15 = MIN(1, D15 / B13)  (0 se previstas = 0)
- tempo total .............. F15 = B15 * B13
- tempo que falta .......... G15 = B15 * (B13 - MIN(B13, D15))
- progresso da etapa ....... E23 = SUMPRODUCT(B, E) / B23; se B23 = 0, média simples de E
- unidades da etapa ........ F13 = ROUND(MIN(E) * B13, 0)  (0 se não há subatividade)
- peso da etapa no robô .... C390 = B390 / B414
- status ................... F419
- robôs concluídos ......... B377 = MIN(unidades de todas as etapas)
- progresso geral .......... E414 = 1 - G414 / F414
- dias úteis restantes ..... Equipe!B8 = horas que faltam / (pessoas * horas por dia)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Iterable, Sequence

STATUS_CONCLUIDA = "Concluída"
STATUS_EM_ANDAMENTO = "Em andamento"
STATUS_NAO_INICIADA = "Não iniciada"

# Segunda a sexta (date.weekday(): segunda = 0 ... domingo = 6).
DIAS_SEMANA_PADRAO: tuple[int, ...] = (0, 1, 2, 3, 4)


# ---------------------------------------------------------------------------
# Tipos de entrada e saída
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Atividade:
    """Uma subatividade: tempo ideal por unidade (min) e peças já concluídas."""

    ideal_min: float = 0.0
    pecas: int = 0


@dataclass(frozen=True)
class Etapa:
    """Uma etapa com suas subatividades e as unidades previstas."""

    atividades: Sequence[Atividade] = field(default_factory=tuple)
    previstas: int = 0


@dataclass(frozen=True)
class ResultadoAtividade:
    peso: float
    pct: float
    tempo_total_min: float
    tempo_restante_min: float
    faltam: int


@dataclass(frozen=True)
class ResultadoEtapa:
    tempo_unidade_min: float  # soma dos tempos ideais (tempo de 1 unidade na etapa)
    peso_no_projeto: float
    progresso: float  # progresso pelas tarefas (Tabela 1)
    unidades: int  # unidades concluídas (Tabela 2)
    previstas: int
    status: str
    tempo_total_min: float
    tempo_restante_min: float
    tarefas: int
    tarefas_concluidas: int
    atividades: tuple[ResultadoAtividade, ...]


@dataclass(frozen=True)
class ResultadoProjeto:
    etapas: tuple[ResultadoEtapa, ...]
    unidades_concluidas: int  # equipamentos prontos (mínimo entre as etapas)
    previstas: int
    unidades_etapas: int  # soma das unidades concluídas das etapas
    unidades_etapas_previstas: int
    etapas_concluidas: int
    tarefas: int
    tarefas_concluidas: int
    tempo_unidade_min: float
    tempo_total_min: float
    tempo_restante_min: float
    progresso_geral: float
    dias_uteis_restantes: float | None

    @property
    def tempo_total_h(self) -> float:
        return self.tempo_total_min / 60

    @property
    def tempo_restante_h(self) -> float:
        return self.tempo_restante_min / 60


# ---------------------------------------------------------------------------
# Funções elementares
# ---------------------------------------------------------------------------


def arredondar(valor: float) -> int:
    """ROUND(x, 0) do Excel: metade para longe do zero (o round() do Python é bancário)."""
    if valor >= 0:
        return int(math.floor(valor + 0.5))
    return -int(math.floor(-valor + 0.5))


def peso_atividade(ideal_min: float, soma_tempos_etapa: float) -> float:
    """Peso da subatividade na etapa: tempo ideal ÷ soma dos tempos da etapa (0 se soma = 0)."""
    if not soma_tempos_etapa:
        return 0.0
    return (ideal_min or 0) / soma_tempos_etapa


def peso_etapa(tempo_etapa_min: float, tempo_unidade_min: float) -> float:
    """Peso da etapa no equipamento: tempo da etapa ÷ tempo de 1 unidade (0 se total = 0)."""
    if not tempo_unidade_min:
        return 0.0
    return (tempo_etapa_min or 0) / tempo_unidade_min


def pct_atividade(pecas: int, previstas: int) -> float:
    """% concluído da subatividade: min(1, peças ÷ previstas); 0 se previstas ≤ 0."""
    if previstas <= 0:
        return 0.0
    return min(1.0, (pecas or 0) / previstas)


def tempo_total_min(ideal_min: float, previstas: int) -> float:
    """Tempo total da subatividade: tempo ideal × previstas."""
    return (ideal_min or 0) * previstas


def tempo_restante_min(ideal_min: float, previstas: int, pecas: int) -> float:
    """Tempo que falta: tempo ideal × (previstas − min(previstas, peças))."""
    return (ideal_min or 0) * (previstas - min(previstas, pecas or 0))


def progresso_tarefas(atividades: Sequence[Atividade], previstas: int) -> float:
    """Progresso da etapa pelas tarefas: Σ(tempo × %) ÷ Σ tempo.

    Se a soma dos tempos for 0, usa a média simples dos %; sem subatividade, 0.
    """
    if not atividades:
        return 0.0
    pcts = [pct_atividade(a.pecas, previstas) for a in atividades]
    soma_tempos = sum((a.ideal_min or 0) for a in atividades)
    if soma_tempos > 0:
        return sum((a.ideal_min or 0) * p for a, p in zip(atividades, pcts)) / soma_tempos
    return sum(pcts) / len(pcts)


def unidades_etapa(atividades: Sequence[Atividade], previstas: int) -> int:
    """Unidades concluídas da etapa: round(min(%) × previstas).

    Uma unidade só está pronta depois de passar por todas as subatividades.
    """
    if not atividades:
        return 0
    menor = min(pct_atividade(a.pecas, previstas) for a in atividades)
    return arredondar(menor * previstas)


def unidades_projeto(unidades_por_etapa: Iterable[int]) -> int:
    """Equipamentos concluídos: menor número de unidades entre todas as etapas (0 se nenhuma)."""
    valores = list(unidades_por_etapa)
    return min(valores) if valores else 0


def status_etapa(feitas: int, previstas: int, progresso: float) -> str:
    """Concluída se feitas ≥ previstas (> 0); Em andamento se feitas > 0 ou progresso > 0."""
    if previstas > 0 and feitas >= previstas:
        return STATUS_CONCLUIDA
    if feitas > 0 or progresso > 0:
        return STATUS_EM_ANDAMENTO
    return STATUS_NAO_INICIADA


def progresso_geral(tempo_restante: float, tempo_total: float) -> float:
    """Progresso ponderado por tempo: 1 − que falta ÷ total (0 se total = 0)."""
    if not tempo_total:
        return 0.0
    return 1 - tempo_restante / tempo_total


def dias_uteis_restantes(horas: float, pessoas: int, horas_dia: float) -> float | None:
    """Dias úteis = horas que faltam ÷ (pessoas × horas por dia). None se a equipe for 0."""
    capacidade = (pessoas or 0) * (horas_dia or 0)
    if capacidade <= 0:
        return None
    return horas / capacidade


def prazo_em_data(
    inicio: date,
    dias: float,
    feriados: Iterable[date] = (),
    dias_semana: Iterable[int] = DIAS_SEMANA_PADRAO,
) -> date:
    """Data em que terminam `dias` dias úteis contados a partir de `inicio` (inclusive).

    Dias fracionados ocupam o dia inteiro (3,2 dias → 4º dia útil). Fins de semana (dias
    fora de `dias_semana`, com segunda = 0) e `feriados` são pulados. Com `dias` ≤ 0 devolve
    `inicio`. Melhoria sobre a planilha, que só divide.
    """
    necessarios = math.ceil(dias - 1e-9) if dias > 0 else 0
    if necessarios <= 0:
        return inicio
    uteis = set(dias_semana)
    if not uteis:
        raise ValueError("dias_semana não pode ser vazio")
    nao_uteis = set(feriados)
    atual = inicio
    contados = 0
    while True:
        if atual.weekday() in uteis and atual not in nao_uteis:
            contados += 1
            if contados == necessarios:
                return atual
        atual += timedelta(days=1)


# ---------------------------------------------------------------------------
# Resumos
# ---------------------------------------------------------------------------


def _resumo_etapa(etapa: Etapa, tempo_unidade_projeto: float) -> ResultadoEtapa:
    previstas = etapa.previstas
    soma = sum((a.ideal_min or 0) for a in etapa.atividades)
    atividades = tuple(
        ResultadoAtividade(
            peso=peso_atividade(a.ideal_min, soma),
            pct=pct_atividade(a.pecas, previstas),
            tempo_total_min=tempo_total_min(a.ideal_min, previstas),
            tempo_restante_min=tempo_restante_min(a.ideal_min, previstas, a.pecas),
            faltam=max(0, previstas - (a.pecas or 0)),
        )
        for a in etapa.atividades
    )
    progresso = progresso_tarefas(etapa.atividades, previstas)
    unidades = unidades_etapa(etapa.atividades, previstas)
    return ResultadoEtapa(
        tempo_unidade_min=soma,
        peso_no_projeto=peso_etapa(soma, tempo_unidade_projeto),
        progresso=progresso,
        unidades=unidades,
        previstas=previstas,
        status=status_etapa(unidades, previstas, progresso),
        tempo_total_min=sum(r.tempo_total_min for r in atividades),
        tempo_restante_min=sum(r.tempo_restante_min for r in atividades),
        tarefas=len(atividades),
        tarefas_concluidas=sum(1 for r in atividades if r.pct >= 1),
        atividades=atividades,
    )


def resumo_etapa(etapa: Etapa, tempo_unidade_projeto: float = 0.0) -> ResultadoEtapa:
    """Todos os indicadores de uma etapa."""
    return _resumo_etapa(etapa, tempo_unidade_projeto)


def resumo_projeto(
    etapas: Sequence[Etapa],
    quantidade: int,
    pessoas: int = 1,
    horas_dia: float = 8.0,
) -> ResultadoProjeto:
    """Indicadores do projeto inteiro (resumo final + aba Equipe da planilha)."""
    tempo_unidade = sum(sum((a.ideal_min or 0) for a in e.atividades) for e in etapas)
    resultados = tuple(_resumo_etapa(e, tempo_unidade) for e in etapas)
    total = sum(r.tempo_total_min for r in resultados)
    restante = sum(r.tempo_restante_min for r in resultados)
    return ResultadoProjeto(
        etapas=resultados,
        unidades_concluidas=unidades_projeto(r.unidades for r in resultados),
        previstas=quantidade,
        unidades_etapas=sum(r.unidades for r in resultados),
        unidades_etapas_previstas=sum(r.previstas for r in resultados),
        etapas_concluidas=sum(1 for r in resultados if r.status == STATUS_CONCLUIDA),
        tarefas=sum(r.tarefas for r in resultados),
        tarefas_concluidas=sum(r.tarefas_concluidas for r in resultados),
        tempo_unidade_min=tempo_unidade,
        tempo_total_min=total,
        tempo_restante_min=restante,
        progresso_geral=progresso_geral(restante, total),
        dias_uteis_restantes=dias_uteis_restantes(restante / 60, pessoas, horas_dia),
    )
