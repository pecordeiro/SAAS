"""Exportação no LAYOUT DA BASE (R7, plano §4.6): o .xlsx sai igual à planilha de
acompanhamento de referência (``docs/referencia/acompanhamento_montagem_v4.xlsx``), COM AS
FÓRMULAS, para continuar funcionando no Excel/LibreOffice depois de baixado.

Aba “Acompanhamento”: título (nome do projeto), meta, indicadores do topo, um bloco por
etapa (subatividades, tempo ideal, peso, peças, %, tempos, total e unidades concluídas),
“RESUMO FINAL” com Indicadores, Tabela 1 (progresso por etapa) e Tabela 2 (unidades
concluídas por etapa, com status colorido). Aba “Equipe”: tempo que falta, pessoas, horas por
dia, dias úteis, cenários de 1 a 6 pessoas e as datas do projeto.

As fórmulas são as MESMAS da referência (só mudam as linhas, que dependem do número de
etapas e subatividades); ``calc.py`` reproduz essas fórmulas, e o teste
``tests/test_r7_planilha.py`` recalcula o arquivo no LibreOffice e compara com o calc.
Só entram etapas e subatividades ATIVAS (as arquivadas ficam na exportação em lista,
``exporter.to_xlsx``/``to_csv``).

O mesmo arquivo volta pela importação: ``importer.parse_reference`` lê os blocos (nome,
tempo ideal, peças), a meta e a aba Equipe (pessoas, horas, início e prazo).

Segurança: todo texto vindo do usuário (nome do projeto, etapas, subatividades) passa por
``exporter.neutralize`` e é gravado como texto (nunca fórmula). As únicas fórmulas do
arquivo são as escritas aqui, montadas só com endereços de células.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from app.models import Project
from app.services.exporter import neutralize
from app.services.projects import active_activities, active_stages

SHEET_MAIN = "Acompanhamento"
SHEET_TEAM = "Equipe"

FIRST_BLOCK_ROW = 12
MIN_ACTIVITY_ROWS = 8  # como a referência: linhas amarelas vazias para acrescentar no Excel
EXTRA_ACTIVITY_ROWS = 2
TEAM_SCENARIOS = 6  # Equipe!A13:A18 (1 a 6 pessoas), igual à referência

STATUS_DONE = "Concluída"
STATUS_DOING = "Em andamento"
STATUS_TODO = "Não iniciada"

# Cores da referência (o arquivo é do cliente: não usa os tokens do site, que são CSS).
DARK = "1F3864"
HEADER = "D9E2F3"
TOTAL = "F2F2F2"
INPUT = "FFF9DB"
INPUT_FONT = "0000FF"
MUTED = "595959"
SIDE = "808080"
WARN = "C00000"
LINK = "0563C1"
FONT = "Arial"

FMT_INT = "0"
FMT_MIN = "#,##0"
FMT_MIN_TOTAL = '#,##0" min"'
FMT_HOURS = "#,##0.0"
FMT_PCT = "0%"
FMT_PCT1 = "0.0%"
FMT_DATE = "DD/MM/YYYY"


@dataclass(frozen=True)
class Block:
    title: int  # linha do título da etapa
    first: int  # primeira linha de subatividade
    last: int  # última linha de subatividade (inclui as vazias)
    total: int  # “Total da etapa”

    @property
    def planned(self) -> int:  # “Unidades previstas”
        return self.title + 1

    def rng(self, col: str) -> str:
        return f"{col}{self.first}:{col}{self.last}"


@dataclass(frozen=True)
class Layout:
    """Endereços de tudo que as fórmulas cruzam (calculado antes de escrever)."""

    blocks: tuple[Block, ...]
    summary: int  # “RESUMO FINAL”
    indicators: int  # primeira linha de indicador
    t1_header: int
    t1_first: int
    t1_last: int
    t1_total: int
    t2_header: int
    t2_first: int
    t2_last: int
    t2_total: int

    @property
    def ind(self) -> dict[str, int]:
        keys = ("units", "stages", "tasks", "units_sum", "worked", "unit_time", "left", "days", "no_time")
        return {k: self.indicators + i for i, k in enumerate(keys)}


def plan_layout(activity_counts: list[int]) -> Layout:
    blocks = []
    row = FIRST_BLOCK_ROW
    for count in activity_counts:
        n = max(MIN_ACTIVITY_ROWS, count + EXTRA_ACTIVITY_ROWS)
        first = row + 3
        last = first + n - 1
        blocks.append(Block(row, first, last, last + 1))
        row = last + 1 + 4  # total, “unidades ÷ previstas”, 2 linhas vazias
    summary = (blocks[-1].total + 5) if blocks else FIRST_BLOCK_ROW
    indicators = summary + 4
    rows_in_tables = max(1, len(blocks))
    t1_header = summary + 16
    t1_first = t1_header + 1
    t1_last = t1_first + rows_in_tables - 1
    t1_total = t1_last + 1
    t2_header = t1_total + 4
    t2_first = t2_header + 1
    t2_last = t2_first + rows_in_tables - 1
    return Layout(
        tuple(blocks), summary, indicators, t1_header, t1_first, t1_last, t1_last + 1,
        t2_header, t2_first, t2_last, t2_last + 1,
    )


# ---------------------------------------------------------------- estilos


def _styles():
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    thin = Side(style="thin", color="BFBFBF")
    return {
        "Font": Font,
        "fill": lambda color: PatternFill("solid", fgColor=color),
        "border": Border(left=thin, right=thin, top=thin, bottom=thin),
        "wrap": Alignment(wrap_text=True, vertical="top"),
        "center": Alignment(horizontal="center", vertical="center"),
    }


class _Writer:
    def __init__(self, ws):
        self.ws = ws
        self.s = _styles()

    def put(self, ref: str, value, *, fmt: str | None = None, bold=False, color: str | None = None,
            fill: str | None = None, size: int | None = None, text=False, border=False):
        cell = self.ws[ref]
        if text:
            value = neutralize(value)
        cell.value = value
        if text or (isinstance(value, str) and not value.startswith("=")):
            cell.data_type = "s"  # texto do usuário nunca vira fórmula
        cell.font = self.s["Font"](name=FONT, bold=bold, color=color, size=size or 10)
        if fmt:
            cell.number_format = fmt
        if fill:
            cell.fill = self.s["fill"](fill)
        if border:
            cell.border = self.s["border"]
        return cell

    def formula(self, ref: str, expr: str, **kw):
        assert expr.startswith("="), expr
        return self.put(ref, expr, **kw)

    def input(self, ref: str, value, *, fmt: str | None = None, text=False, bold=False):
        return self.put(ref, value, fmt=fmt, fill=INPUT, color=INPUT_FONT, text=text, bold=bold, border=True)

    def header(self, row: int, labels: list[str], *, fill=HEADER, color=DARK):
        for i, label in enumerate(labels):
            self.put(f"{chr(65 + i)}{row}", label, bold=True, fill=fill, color=color, border=True)

    def band(self, row: int, cols: str, fill: str):
        for col in cols:
            cell = self.ws[f"{col}{row}"]
            cell.fill = self.s["fill"](fill)


# ---------------------------------------------------------------- aba Acompanhamento


def _main_sheet(ws, project: Project, stages: list, lay: Layout) -> None:
    from openpyxl.worksheet.hyperlink import Hyperlink

    w = _Writer(ws)
    w.put("A1", project.name, bold=True, color=DARK, size=14, text=True)
    w.put(
        "A2",
        "Preencha só as células amarelas: nome e tempo ideal de cada subatividade, a meta e as peças "
        "concluídas. As outras células são fórmulas e se recalculam sozinhas.",
        color=MUTED,
    )
    w.put(
        "A3",
        f"Exportado da Teroz em {datetime.now(timezone.utc):%d/%m/%Y}. "
        "Para devolver ao site, importe este arquivo.",
        color=MUTED,
    )
    ind = lay.ind
    w.put("A4", "Meta: quantas unidades vamos montar (previstas)", bold=True)
    w.input("B4", int(project.quantity), fmt=FMT_INT, bold=True)
    rows = (
        ("Unidades concluídas (prontas em todas as etapas)", f'=B{ind["units"]}&" de "&C{ind["units"]}', None),
        ("Progresso geral (pelas tarefas)", f'=D{ind["worked"]}', FMT_PCT1),
        ("Unidades concluídas (soma das etapas)", f'=B{ind["units_sum"]}&" de "&C{ind["units_sum"]}', None),
        ("Tempo que falta (h)", f'=B{ind["left"]}', FMT_HOURS),
        ("Dias úteis restantes (aba Equipe)", f'=B{ind["days"]}', FMT_HOURS),
    )
    for i, (label, expr, fmt) in enumerate(rows, start=5):
        w.put(f"A{i}", label, bold=True)
        w.formula(f"B{i}", expr, fmt=fmt, bold=True)
    link = w.put("A10", "Ir para o resumo final ↓", color=LINK)
    link.hyperlink = Hyperlink(ref="A10", location=f"'{SHEET_MAIN}'!A{lay.summary}")

    for j, (stage, block) in enumerate(zip(stages, lay.blocks)):
        _block(w, stage, block, lay.t1_first + j)

    # ---------------- resumo final
    w.put(f"A{lay.summary}", "RESUMO FINAL", bold=True, color="FFFFFF", fill=DARK)
    w.band(lay.summary, "BCDEFG", DARK)
    w.put(f"A{lay.indicators - 2}", "Indicadores", bold=True, color=DARK)
    w.header(lay.indicators - 1, ["Indicador", "Feito", "Total", "%"])
    t1 = (lay.t1_first, lay.t1_last, lay.t1_total)
    t2 = (lay.t2_first, lay.t2_last, lay.t2_total)
    indicators = (
        ("units", "Unidades concluídas (prontas em todas as etapas)", f"=MIN(B{t2[0]}:B{t2[1]})", "=$B$4", FMT_INT),
        ("stages", "Etapas concluídas", f'=COUNTIF(F{t2[0]}:F{t2[1]},"{STATUS_DONE}")', f"=COUNTA(A{t2[0]}:A{t2[1]})", FMT_INT),
        ("tasks", "Tarefas (subatividades) concluídas", '=SUMIF(O:O,"Tarefas 100%",P:P)', '=SUMIF(O:O,"Tarefas",P:P)', FMT_INT),
        ("units_sum", "Unidades concluídas (soma das etapas)", f"=B{t2[2]}", f"=C{t2[2]}", FMT_INT),
        ("worked", "Tempo trabalhado (h) = progresso geral", f"=F{t1[2]}-G{t1[2]}", f"=F{t1[2]}", FMT_HOURS),
        ("unit_time", "Tempo de 1 unidade (h)", f"=B{t1[2]}/60", None, FMT_HOURS),
        ("left", "Tempo que falta (h)", f"=G{t1[2]}", None, FMT_HOURS),
        ("days", "Dias úteis restantes (aba Equipe)", f"={SHEET_TEAM}!B8", None, FMT_HOURS),
        ("no_time", "Etapas ainda sem tempo definido", f"=COUNTIF(B{t1[0]}:B{t1[1]},0)", None, FMT_INT),
    )
    for key, label, done, total, fmt in indicators:
        r = ind[key]
        w.put(f"A{r}", label, border=True)
        w.formula(f"B{r}", done, fmt=fmt, bold=True, border=True)
        if total:
            w.formula(f"C{r}", total, fmt=fmt, border=True)
            w.formula(f"D{r}", f"=IF(C{r}>0,B{r}/C{r},0)", fmt=FMT_PCT1, bold=True, border=True)
    w.put(f"O{ind['units']}", "Concluído", color=SIDE)
    w.formula(f"P{ind['units']}", f"=D{ind['worked']}", fmt=FMT_PCT, color=SIDE)
    w.put(f"O{ind['units'] + 1}", "Falta", color=SIDE)
    w.formula(f"P{ind['units'] + 1}", f"=1-P{ind['units']}", fmt=FMT_PCT, color=SIDE)

    # ---------------- Tabela 1
    w.put(
        f"A{lay.t1_header - 1}",
        "Tabela 1 – Progresso por etapa pelas tarefas (peças concluídas de cada subatividade, sobre as previstas)",
        bold=True, color=DARK,
    )
    w.header(lay.t1_header, ["Etapa", "Tempo por unidade (min)", "Peso no projeto", "Previstas", "Progresso",
                             "Tempo total (h)", "Tempo que falta (h)"])
    tot = lay.t1_total
    for j, block in enumerate(lay.blocks):
        r = lay.t1_first + j
        w.formula(f"A{r}", f"=A{block.title}", border=True)
        w.formula(f"B{r}", f"=B{block.total}", fmt=FMT_MIN, border=True)
        w.formula(f"C{r}", f"=IF($B${tot}=0,0,B{r}/$B${tot})", fmt=FMT_PCT1, border=True)
        w.formula(f"D{r}", f"=B{block.planned}", fmt=FMT_INT, border=True)
        w.formula(f"E{r}", f"=E{block.total}", fmt=FMT_PCT1, border=True)
        w.formula(f"F{r}", f"=B{r}*D{r}/60", fmt=FMT_HOURS, border=True)
        w.formula(f"G{r}", f"=F{r}*(1-E{r})", fmt=FMT_HOURS, border=True)
    first, last = lay.t1_first, lay.t1_last
    w.put(f"A{tot}", "Total", bold=True, fill=TOTAL, border=True)
    for col, fmt in (("B", FMT_MIN), ("C", FMT_PCT1), ("D", FMT_INT), ("F", FMT_HOURS), ("G", FMT_HOURS)):
        w.formula(f"{col}{tot}", f"=SUM({col}{first}:{col}{last})", fmt=fmt, bold=True, fill=TOTAL, border=True)
    w.formula(f"E{tot}", f"=IF(F{tot}=0,0,1-G{tot}/F{tot})", fmt=FMT_PCT1, bold=True, fill=TOTAL, border=True)

    # ---------------- Tabela 2
    w.put(
        f"A{lay.t2_header - 1}",
        "Tabela 2 – Unidades concluídas por etapa (feitas ÷ previstas, sem contar as parciais)",
        bold=True, color=DARK,
    )
    w.header(lay.t2_header, ["Etapa", "Feitas", "Previstas", "Feitas/Previstas", "% concluída", "Status"])
    for j, block in enumerate(lay.blocks):
        r = lay.t2_first + j
        t1_row = lay.t1_first + j
        w.formula(f"A{r}", f"=A{block.title}", border=True)
        w.formula(f"B{r}", f"=F{block.planned}", fmt=FMT_INT, border=True)
        w.formula(f"C{r}", f"=B{block.planned}", fmt=FMT_INT, border=True)
        w.formula(f"D{r}", f'=B{r}&"/"&C{r}', border=True)
        w.formula(f"E{r}", f"=IF(C{r}>0,B{r}/C{r},0)", fmt=FMT_PCT1, border=True)
        w.formula(
            f"F{r}",
            f'=IF(AND(C{r}>0,B{r}>=C{r}),"{STATUS_DONE}",IF(OR(B{r}>0,E{t1_row}>0),"{STATUS_DOING}","{STATUS_TODO}"))',
            border=True,
        )
    tot2 = lay.t2_total
    w.put(f"A{tot2}", "Total", bold=True, fill=TOTAL, border=True)
    w.formula(f"B{tot2}", f"=SUM(B{lay.t2_first}:B{lay.t2_last})", fmt=FMT_INT, bold=True, fill=TOTAL, border=True)
    w.formula(f"C{tot2}", f"=SUM(C{lay.t2_first}:C{lay.t2_last})", fmt=FMT_INT, bold=True, fill=TOTAL, border=True)
    w.formula(f"D{tot2}", f'=B{tot2}&"/"&C{tot2}', bold=True, fill=TOTAL, border=True)
    w.formula(f"E{tot2}", f"=IF(C{tot2}>0,B{tot2}/C{tot2},0)", fmt=FMT_PCT1, bold=True, fill=TOTAL, border=True)

    _conditional(ws, lay)
    _validation(ws, lay)
    for col, width in {"A": 46, "B": 16, "C": 15, "D": 16, "E": 15, "F": 16, "G": 17, "O": 13, "P": 8}.items():
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "B2"


def _block(w: _Writer, stage, block: Block, t1_row: int) -> None:
    r, p, t = block.title, block.planned, block.total
    w.put(f"A{r}", stage.name, bold=True, color="FFFFFF", fill=DARK, text=True)
    w.band(r, "BCD", DARK)
    w.put(f"E{r}", "Peso no projeto", bold=True, color="FFFFFF", fill=DARK)
    w.formula(f"F{r}", f"=C{t1_row}", fmt=FMT_PCT1, bold=True, color="FFFFFF", fill=DARK)
    w.band(r, "G", DARK)
    w.put(f"A{p}", "Unidades previstas", bold=True, fill=TOTAL)
    w.formula(f"B{p}", "=$B$4", fmt=FMT_INT, bold=True, fill=TOTAL)
    w.band(p, "CD", TOTAL)
    w.put(f"E{p}", "Unidades concluídas", bold=True, fill=TOTAL)
    w.formula(f"F{p}", f"=IF(COUNT({block.rng('E')})=0,0,ROUND(MIN({block.rng('E')})*B{p},0))", fmt=FMT_INT,
              bold=True, fill=TOTAL)
    w.band(p, "G", TOTAL)
    w.header(r + 2, ["Subatividade", "Tempo ideal (min)", "Peso na etapa", "Peças concluídas", "% concluído",
                     "Tempo total (min)", "Tempo que falta (min)"])
    activities = active_activities(stage)
    for i in range(block.first, block.last + 1):
        k = i - block.first
        if k < len(activities):
            a = activities[k]
            w.input(f"A{i}", a.name, text=True)
            w.input(f"B{i}", _number(a.ideal_minutes))
            w.input(f"D{i}", int(a.units_done), fmt=FMT_INT)
        else:
            for col in "ABD":
                w.input(f"{col}{i}", None)
        w.formula(f"C{i}", f'=IF(OR(A{i}="",$B${t}=0),"",N(B{i})/$B${t})', fmt=FMT_PCT, border=True)
        w.formula(f"E{i}", f'=IF(A{i}="","",IF($B${p}>0,MIN(1,N(D{i})/$B${p}),0))', fmt=FMT_PCT, border=True)
        w.formula(f"F{i}", f'=IF(A{i}="","",N(B{i})*$B${p})', fmt=FMT_MIN, border=True)
        w.formula(f"G{i}", f'=IF(A{i}="","",N(B{i})*($B${p}-MIN($B${p},N(D{i}))))', fmt=FMT_MIN, border=True)
    w.put(f"A{t}", "Total da etapa (progresso pelas tarefas)", bold=True, fill=TOTAL)
    w.formula(f"B{t}", f"=SUM({block.rng('B')})", fmt=FMT_MIN_TOTAL, bold=True, fill=TOTAL)
    w.band(t, "CD", TOTAL)
    w.formula(
        f"E{t}",
        f"=IF(B{t}>0,SUMPRODUCT({block.rng('B')},{block.rng('E')})/B{t},"
        f"IF(COUNT({block.rng('E')})=0,0,SUM({block.rng('E')})/COUNT({block.rng('E')})))",
        fmt=FMT_PCT1, bold=True, fill=TOTAL,
    )
    w.formula(f"F{t}", f"=SUM({block.rng('F')})", fmt=FMT_MIN, bold=True, fill=TOTAL)
    w.formula(f"G{t}", f"=SUM({block.rng('G')})", fmt=FMT_MIN, bold=True, fill=TOTAL)
    w.put(f"A{t + 1}", "Unidades concluídas ÷ previstas (menor nº de peças entre as subatividades)", bold=True,
          fill=TOTAL)
    w.band(t + 1, "BC", TOTAL)
    w.formula(f"D{t + 1}", f'=F{p}&"/"&B{p}', bold=True, fill=TOTAL)
    w.formula(f"E{t + 1}", f"=IF(B{p}>0,MIN(1,F{p}/B{p}),0)", fmt=FMT_PCT1, bold=True, fill=TOTAL)
    # Colunas laterais (cinza) que o resumo soma com SUMIF, como na referência.
    for row, label, expr, fmt in (
        (r, "Concluído", f"=E{t}", FMT_PCT),
        (r + 1, "Falta", f"=1-P{r}", FMT_PCT),
        (block.first, "Tarefas", f"=COUNTA({block.rng('A')})", FMT_INT),
        (block.first + 1, "Tarefas 100%", f'=COUNTIF({block.rng("E")},">=1")', FMT_INT),
    ):
        w.put(f"O{row}", label, color=SIDE)
        w.formula(f"P{row}", expr, fmt=fmt, color=SIDE)


def _number(value):
    d = Decimal(str(value or 0))
    return int(d) if d == d.to_integral_value() else float(d)


def _conditional(ws, lay: Layout) -> None:
    from openpyxl.formatting.rule import CellIsRule, DataBarRule
    from openpyxl.styles import Font, PatternFill

    bar = DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color="5B9BD5")
    ws.conditional_formatting.add(f"E{lay.t1_first}:E{lay.t1_last}", bar)
    ws.conditional_formatting.add(f"E{lay.t2_first}:E{lay.t2_last}", bar)
    status = f"F{lay.t2_first}:F{lay.t2_last}"
    for text, fill, font in (
        (STATUS_DONE, "C6EFCE", "006100"),
        (STATUS_DOING, "FFEB9C", "9C5700"),
        (STATUS_TODO, "F2F2F2", "595959"),
    ):
        ws.conditional_formatting.add(
            status,
            CellIsRule(operator="equal", formula=[f'"{text}"'], fill=PatternFill("solid", bgColor=fill),
                       font=Font(color=font, bold=True)),
        )


def _validation(ws, lay: Layout) -> None:
    from openpyxl.worksheet.datavalidation import DataValidation

    minutes = DataValidation(type="decimal", operator="greaterThanOrEqual", formula1="0", allow_blank=True,
                             error="Tempo ideal em minutos (número ≥ 0).", showErrorMessage=True)
    pieces = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0", allow_blank=True,
                            error="Peças concluídas (número inteiro ≥ 0).", showErrorMessage=True)
    meta = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="1",
                          error="Meta: número inteiro ≥ 1.", showErrorMessage=True)
    for dv in (minutes, pieces, meta):
        ws.add_data_validation(dv)
    meta.add("B4")
    for block in lay.blocks:
        minutes.add(block.rng("B"))
        pieces.add(block.rng("D"))


# ---------------------------------------------------------------- aba Equipe


def _team_sheet(ws, project: Project, lay: Layout) -> None:
    from openpyxl.worksheet.datavalidation import DataValidation

    w = _Writer(ws)
    w.put("A1", "Equipe e prazo", bold=True, color=DARK, size=14)
    w.put("A2", "Relação simples: dias úteis = horas de trabalho ÷ (pessoas × horas por dia). "
                "Considera que as pessoas trabalham em paralelo.", color=MUTED)
    tot = lay.t1_total
    items = (
        (4, "Tempo que falta (h)", f"={SHEET_MAIN}!G{tot}", FMT_HOURS),
        (5, "Tempo total da meta (h)", f"={SHEET_MAIN}!F{tot}", FMT_HOURS),
        (8, "Dias úteis restantes", '=IF(B6*B7>0,B4/(B6*B7),"")', FMT_HOURS),
        (9, "Dias úteis para a meta inteira", '=IF(B6*B7>0,B5/(B6*B7),"")', FMT_HOURS),
    )
    for row, label, expr, fmt in items:
        w.put(f"A{row}", label, bold=True)
        w.formula(f"B{row}", expr, fmt=fmt, bold=True)
    w.put("A6", "Pessoas montando", bold=True)
    w.input("B6", int(project.people), fmt=FMT_INT, bold=True)
    w.put("A7", "Horas de trabalho por dia (por pessoa)", bold=True)
    w.input("B7", _number(project.hours_per_day), fmt="0.0", bold=True)
    w.put("A11", "E se mudar o tamanho da equipe?", bold=True, color=DARK)
    w.header(12, ["Pessoas", "Horas por dia (equipe)", "Dias úteis restantes"])
    for i in range(TEAM_SCENARIOS):
        r = 13 + i
        w.put(f"A{r}", i + 1, fmt=FMT_INT, border=True)
        w.formula(f"B{r}", f"=A{r}*$B$7", fmt=FMT_HOURS, border=True)
        w.formula(f"C{r}", f'=IF(B{r}>0,$B$4/B{r},"")', fmt=FMT_HOURS, border=True)
    w.put("A20", "Datas do projeto", bold=True, color=DARK)
    w.put("A21", "Início do projeto", bold=True)
    w.input("B21", project.start_date, fmt=FMT_DATE)
    w.put("A22", "Prazo de entrega", bold=True)
    w.input("B22", project.due_date, fmt=FMT_DATE)
    people = DataValidation(type="whole", operator="between", formula1="1", formula2="1000",
                            error="Pessoas: inteiro de 1 a 1000.", showErrorMessage=True)
    hours = DataValidation(type="decimal", operator="between", formula1="0.5", formula2="24",
                           error="Horas por dia: de 0,5 a 24.", showErrorMessage=True)
    dates = DataValidation(type="date", operator="greaterThan", formula1="1", allow_blank=True,
                           error="Use uma data (dd/mm/aaaa).", showErrorMessage=True)
    for dv, ref in ((people, "B6"), (hours, "B7"), (dates, "B21:B22")):
        ws.add_data_validation(dv)
        dv.add(ref)
    for col, width in {"A": 44, "B": 18, "C": 22}.items():
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A3"


# ---------------------------------------------------------------- entrada


def build_workbook(project: Project):
    from openpyxl import Workbook

    stages = active_stages(project)
    lay = plan_layout([len(active_activities(s)) for s in stages])
    wb = Workbook()
    main = wb.active
    main.title = SHEET_MAIN
    team = wb.create_sheet(SHEET_TEAM)
    _main_sheet(main, project, stages, lay)
    _team_sheet(team, project, lay)
    for ws in (main, team):
        ws.page_setup.orientation = "landscape"
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
    wb.calculation.fullCalcOnLoad = True  # Excel recalcula ao abrir (o openpyxl não grava valores)
    return wb, lay


def to_xlsx_layout(project: Project) -> bytes:
    wb, _ = build_workbook(project)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()

