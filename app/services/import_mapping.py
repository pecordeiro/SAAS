"""Importar QUALQUER planilha (.xlsx/.csv) com mapeamento de colunas (R7, plano §4.6).

Etapa 1 — ``inspect``: com a grade já lida (``importer.load_grid``, mesmas proteções de
tamanho, zip bomb, DTD e senha), devolve as abas e, para a aba escolhida, a linha de
cabeçalho (detectada ou escolhida), as colunas com amostra de valores e uma SUGESTÃO de
mapeamento pelo nome da coluna (sem acento, sem caixa).

Etapa 2 — ``parse_mapped``: recebe o mapeamento (campo → índice da coluna) e devolve o mesmo
``ImportResult`` da importação de sempre, com erros por linha; depois a prévia assinada e o
``importer.save`` de hoje.

Campos: etapa (obrigatória), subatividade, tempo ideal (min), previstas/meta, concluídas/peças,
% concluído e prazo/data (todos opcionais).

- Com coluna de subatividade → modo detalhado: uma atividade por linha (a etapa vazia herda a
  da linha de cima, como em planilhas com células mescladas).
- Sem subatividade → modo SIMPLES (R4: o projeto é gravado com ``progress_mode = "simples"``):
  uma linha por etapa, com o % (ou as peças). Cada etapa tem a atividade interna com o nome da
  etapa e peças = % × meta (``calc.pecas_de_percentual``). Ver ``importer.ImportResult.mode``.

A grade pode ir ASSINADA no formulário entre as etapas (``grid_to_data``/``grid_from_data``):
nada é gravado em disco e a pessoa não precisa enviar o arquivo de novo.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from openpyxl.utils import get_column_letter

from app.services import calc
from app.services.importer import (
    MAX_ACTIVITIES_PER_STAGE,
    MAX_GRID_COLS,
    MAX_GRID_ROWS,
    MAX_GRID_SHEETS,
    MAX_QUANTITY,
    MAX_ROWS,
    MAX_STAGES,
    MODE_DETAILED,
    MODE_SIMPLE,
    Grid,
    ImportError_,
    ImportResult,
    Sheet,
    _clean,
    _date,
    _decimal,
    _int,
    _read_activity,
)
from app.services.projects import SIMPLE_DEFAULT_MINUTES, NewActivity, NewStage

F_STAGE = "etapa"
F_ACTIVITY = "subatividade"
F_MINUTES = "tempo"
F_PLANNED = "previstas"
F_DONE = "concluidas"
F_PCT = "percentual"
F_DUE = "prazo"

# Unidade da coluna de tempo. O servidor converte horas em minutos; o navegador só escolhe.
UNIT_MINUTES = "minutos"
UNIT_HOURS = "horas"
TIME_UNITS: tuple[tuple[str, str], ...] = ((UNIT_MINUTES, "Minutos"), (UNIT_HOURS, "Horas"))
TIME_UNIT_KEYS = tuple(k for k, _ in TIME_UNITS)
MINUTES_PER_HOUR = Decimal("60")
# Aviso de unidade provavelmente errada (só exibição; não bloqueia): média dos tempos positivos.
UNIT_WARN_MEAN_MINUTES_BELOW = Decimal("1")   # em minutos, média < 1 min sugere horas
UNIT_WARN_MEAN_HOURS_ABOVE = Decimal("24")    # em horas, média > 24 h por unidade sugere minutos

# Texto de ajuda por campo (curto, com exemplo), mostrado na tela de mapeamento.
FIELD_HELP: dict[str, str] = {
    F_STAGE: "O grupo de trabalho, ex.: Soldagem. É a única coluna obrigatória.",
    F_ACTIVITY: (
        "A tarefa dentro da etapa, ex.: Soldar suporte. Se a sua planilha não tem esse nível, "
        "deixe sem coluna e o projeto entra no modo simples."
    ),
    F_MINUTES: "Quanto tempo leva para fazer uma unidade, ex.: 12 (minutos) ou 0,2 (horas). Escolha a unidade abaixo.",
    F_PLANNED: (
        "Quantas unidades o projeto vai produzir, ex.: 200. Vale o mesmo número em todas as linhas; "
        "sem essa coluna, digite a meta em Projeto."
    ),
    F_DONE: "Quantas unidades já ficaram prontas naquela linha, ex.: 80.",
    F_PCT: "Quanto da etapa já está pronto, ex.: 45%, 45 ou 0,45. Serve quando a planilha não traz as peças.",
    F_DUE: "A data de entrega, ex.: 31/12/2026. Se houver várias datas, usamos a última.",
}

# (chave, rótulo na tela, obrigatório)
FIELDS: tuple[tuple[str, str, bool], ...] = (
    (F_STAGE, "Etapa", True),
    (F_ACTIVITY, "Subatividade", False),
    (F_MINUTES, "Tempo ideal (min)", False),
    (F_PLANNED, "Previstas (meta)", False),
    (F_DONE, "Concluídas (peças)", False),
    (F_PCT, "% concluído", False),
    (F_DUE, "Prazo (data)", False),
)
FIELD_KEYS = tuple(k for k, _, _ in FIELDS)
FIELD_LABELS = {k: label for k, label, _ in FIELDS}

HEADER_SCAN_ROWS = 30
SAMPLE_SIZE = 5
SAMPLE_CHARS = 60
DEFAULT_QUANTITY_PCT = 100  # só % sem meta: 100 guarda o % com 1 ponto de resolução

# Sinônimos (já normalizados): nome exato vale mais que “contém a palavra”.
SYNONYMS: dict[str, tuple[str, ...]] = {
    F_STAGE: ("etapa", "etapas", "fase", "estagio", "setor", "grupo", "secao", "posto", "macroetapa"),
    F_ACTIVITY: (
        "subatividade", "subatividades", "atividade", "atividades", "tarefa", "tarefas", "item",
        "operacao", "subetapa", "descricao", "servico",
    ),
    F_MINUTES: (
        "tempo ideal (min)", "tempo ideal", "tempo padrao", "tempo (min)", "tempo", "minutos", "min",
        "duracao", "duracao (min)",
    ),
    F_PLANNED: (
        "previstas", "unidades previstas", "meta", "quantidade", "qtd", "qtde", "previsto", "planejado",
        "planejadas", "total previsto",
    ),
    F_DONE: (
        "pecas concluidas", "concluidas", "concluido", "pecas", "feitas", "feito", "produzidas", "realizado",
        "realizadas", "unidades concluidas", "prontas", "qtd feita",
    ),
    F_PCT: (
        "% concluido", "%", "% da etapa", "percentual", "porcentagem", "progresso", "andamento",
        "% realizado", "concluido (%)", "% feito",
    ),
    F_DUE: ("prazo", "data", "entrega", "data de entrega", "previsao", "termino", "fim", "data fim"),
}
# Palavras que tiram a coluna do campo (ex.: “Tempo que falta” não é tempo ideal).
EXCLUDE: dict[str, tuple[str, ...]] = {
    F_MINUTES: ("falta", "restante", "total", "%"),
    F_PLANNED: ("%", "concluid", "feit"),
    F_DONE: ("%", "previst", "falta"),
    F_STAGE: ("%", "peso", "tempo", "total"),
    F_ACTIVITY: ("%", "tempo", "peso"),
}

TOTAL_ROW = re.compile(r"^(total|totais|soma|subtotal)\b")


def normalize(text) -> str:
    """Sem acento, minúsculas, espaços simples (para comparar nomes de coluna)."""
    raw = unicodedata.normalize("NFKD", _clean(text))
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return " ".join(raw.casefold().split())


def _score(field_key: str, header: str) -> int:
    if not header:
        return 0
    if any(word in header for word in EXCLUDE.get(field_key, ())):
        return 0
    synonyms = SYNONYMS[field_key]
    if header in synonyms:
        return 100 - synonyms.index(header)
    words = set(re.split(r"[^\w%]+", header))
    for i, synonym in enumerate(synonyms):
        if (" " in synonym and synonym in header) or synonym in words:
            return 50 - i
    return 0


def suggest(headers: list) -> dict[str, int | None]:
    """Mapeamento sugerido: cada campo ↦ índice (0-based) da coluna de maior pontuação; uma
    coluna serve um campo só (o de maior pontuação ganha)."""
    names = [normalize(h) for h in headers]
    candidates = sorted(
        ((_score(key, name), key, idx) for key in FIELD_KEYS for idx, name in enumerate(names)),
        key=lambda t: (-t[0], FIELD_KEYS.index(t[1]), t[2]),
    )
    mapping: dict[str, int | None] = {k: None for k in FIELD_KEYS}
    used: set[int] = set()
    for score, key, idx in candidates:
        if score <= 0:
            break
        if mapping[key] is None and idx not in used:
            mapping[key] = idx
            used.add(idx)
    return mapping


# Rótulos do select “Isto é…” da tela (uma escolha por COLUNA; R7 — tela). A ordem é a da tela.
COLUMN_CHOICES: tuple[tuple[str, str], ...] = (
    (F_STAGE, "Etapa"),
    (F_ACTIVITY, "Subatividade (opcional)"),
    (F_MINUTES, "Tempo ideal (opcional)"),
    (F_PLANNED, "Previstas / meta (opcional)"),
    (F_DONE, "Concluídas (opcional)"),
    (F_PCT, "% da etapa (opcional)"),
    (F_DUE, "Prazo (opcional)"),
)
COLUMN_PREFIX = "col_"


def mapping_from_columns(values: dict[int, str]) -> tuple[dict[str, int | None], list[str]]:
    """Inverte a escolha da tela (coluna ↦ campo) para o mapeamento (campo ↦ coluna).

    ``values``: índice da coluna (0-based) ↦ chave do campo (vazio = não usar). Um campo em
    duas colunas é erro (a pessoa escolhe uma); chave desconhecida é ignorada."""
    mapping: dict[str, int | None] = {k: None for k in FIELD_KEYS}
    errors: list[str] = []
    for idx in sorted(values):
        key = values[idx]
        if key not in FIELD_LABELS:
            continue
        if mapping[key] is not None:
            first = get_column_letter(mapping[key] + 1)
            errors.append(
                f"{FIELD_LABELS[key]} está em duas colunas ({first} e {get_column_letter(idx + 1)}). Escolha uma."
            )
            continue
        mapping[key] = idx
    return mapping, errors


def mode_of(mapping: dict[str, int | None]) -> str:
    """Modo que o mapeamento produz: com subatividade, detalhado; sem, simples."""
    return MODE_DETAILED if mapping.get(F_ACTIVITY) is not None else MODE_SIMPLE


# ---------------------------------------------------------------- etapa 1: inspeção


@dataclass
class Column:
    index: int  # 0-based
    letter: str
    header: str
    samples: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"{self.letter} · {self.header}" if self.header else f"Coluna {self.letter}"


@dataclass
class Inspection:
    sheets: list[str]
    sheet: str
    header_row: int  # 1-based, como no Excel
    columns: list[Column]
    suggestion: dict[str, int | None]
    rows: int  # linhas de dados depois do cabeçalho (não vazias)


def _display(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, bool):
        return "sim" if value else "não"
    if isinstance(value, float):
        text = f"{value:.4f}".rstrip("0").rstrip(".")
        return text.replace(".", ",")
    return _clean(value)[:SAMPLE_CHARS]


def detect_header_row(sheet: Sheet) -> int:
    """Linha de cabeçalho mais provável entre as primeiras: a que tem mais nomes de coluna
    reconhecidos e, no empate, mais textos (títulos de planilha costumam ter um texto só)."""
    best, best_key = 1, (-1, -1)
    for r in range(1, min(sheet.max_row, HEADER_SCAN_ROWS) + 1):
        values = sheet.rows[r - 1]
        texts = [v for v in values if isinstance(v, str) and v.strip()]
        if not texts:
            continue
        mapped = sum(1 for v in suggest(values).values() if v is not None)
        key = (mapped, len(texts))
        if key > best_key:
            best, best_key = r, key
    return best


def inspect(grid: Grid, sheet_title: str | None = None, header_row: int | None = None) -> Inspection:
    sheet = grid.sheet(sheet_title) or grid.sheet(None)
    if sheet is None or not sheet.rows:
        raise ImportError_("A planilha está vazia.")
    if header_row is None or not 1 <= header_row <= sheet.max_row:
        header_row = detect_header_row(sheet)
    header = sheet.rows[header_row - 1]
    data = [values for values in sheet.rows[header_row:] if any(_clean(v) for v in values)]
    width = max([len(header), *(len(v) for v in data[:MAX_ROWS])] or [0])
    columns = []
    for idx in range(min(width, MAX_GRID_COLS)):
        samples = []
        for values in data:
            if idx < len(values) and _clean(values[idx]):
                samples.append(_display(values[idx]))
                if len(samples) >= SAMPLE_SIZE:
                    break
        head = _clean(header[idx]) if idx < len(header) else ""
        if not head and not samples:
            continue
        columns.append(Column(idx, get_column_letter(idx + 1), head[:SAMPLE_CHARS], samples))
    suggestion = suggest(list(header))
    return Inspection(
        sheets=[s.title for s in grid.sheets],
        sheet=sheet.title,
        header_row=header_row,
        columns=columns,
        suggestion=suggestion,
        rows=len(data),
    )


# ---------------------------------------------------------------- etapa 2: mapeamento → resultado


def _pct(value) -> float:
    """% em qualquer forma comum: 0,45 · 45 · “45%” · “45,5 %”. Número ≤ 1 é fração (1 = 100%)."""
    if isinstance(value, bool):
        raise ValueError
    if isinstance(value, (int, float, Decimal)):
        d = Decimal(str(value))
        has_sign = False
    else:
        text = _clean(value).replace(" ", "")
        has_sign = text.endswith("%")
        d = _decimal(text.rstrip("%"))
    if has_sign or d > 1:
        d = d / 100
    if not Decimal("0") <= d <= Decimal("1"):
        raise ValueError
    return float(d)


def validate_mapping(mapping: dict, width: int) -> list[str]:
    errors = []
    if mapping.get(F_STAGE) is None:
        errors.append("Escolha a coluna da etapa.")
    seen: dict[int, str] = {}
    for key in FIELD_KEYS:
        idx = mapping.get(key)
        if idx is None:
            continue
        if not isinstance(idx, int) or not 0 <= idx < max(width, 1):
            errors.append(f"{FIELD_LABELS[key]}: coluna inexistente.")
        elif idx in seen:
            errors.append(f"{FIELD_LABELS[key]} e {FIELD_LABELS[seen[idx]]} usam a mesma coluna.")
        else:
            seen[idx] = key
    return errors


def parse_mapped(
    grid: Grid,
    sheet_title: str | None,
    header_row: int,
    mapping: dict[str, int | None],
    *,
    quantity: int | None = None,
    name: str | None = None,
    time_unit: str = UNIT_MINUTES,
) -> ImportResult:
    """Lê a aba com o mapeamento dado. ``quantity`` (meta digitada) vale mais que a coluna.

    ``time_unit``: unidade da coluna de tempo ("minutos" ou "horas"). Horas são convertidas aqui,
    em minutos, com os mesmos limites de sempre; qualquer outro valor é erro (sem padrão
    silencioso)."""
    result = ImportResult(source=grid.kind)
    if time_unit not in TIME_UNIT_KEYS:
        result.error(0, "unidade", "escolha minutos ou horas")
        return result
    sheet = grid.sheet(sheet_title)
    if sheet is None or not sheet.rows or not 1 <= header_row <= sheet.max_row:
        result.error(0, "aba", "aba ou linha de cabeçalho inválida")
        return result
    width = max(len(v) for v in sheet.rows) if sheet.rows else 0
    for message in validate_mapping(mapping, width):
        result.error(header_row, "colunas", message)
    if result.errors:
        return result
    base = (grid.filename or "").rsplit("/", 1)[-1].rsplit(".", 1)[0]
    result.name = (_clean(name) or base or sheet.title or "Projeto importado")[:160]
    simple = mapping.get(F_ACTIVITY) is None
    result.mode = MODE_SIMPLE if simple else MODE_DETAILED
    if mapping.get(F_MINUTES) is not None:
        result.time_unit = time_unit

    def get(values, key):
        idx = mapping.get(key)
        return values[idx] if idx is not None and idx < len(values) else None

    rows = [
        (sheet.line(i), values)
        for i, values in enumerate(sheet.rows)
        if i >= header_row and any(_clean(get(values, k)) for k in FIELD_KEYS if mapping.get(k) is not None)
    ]
    if len(rows) > MAX_ROWS:
        result.error(rows[MAX_ROWS][0], "arquivo", f"mais de {MAX_ROWS} linhas")
        return result
    if not rows:
        result.error(header_row + 1, "arquivo", "nenhuma linha de dados depois do cabeçalho")
        return result

    _read_quantity(result, rows, get, quantity)
    _read_due(result, rows, get)

    stages: dict[str, NewStage] = {}
    seen_times: list = []  # tempos como vieram na planilha (para o aviso de unidade)
    current: NewStage | None = None
    for line, values in rows:
        stage_name = _clean(get(values, F_STAGE))
        if stage_name and TOTAL_ROW.match(normalize(stage_name)):
            continue  # linha de total da planilha de origem
        activity_name = "" if simple else _clean(get(values, F_ACTIVITY))
        if not stage_name:
            if not simple and activity_name and current is not None:
                stage = current  # célula mesclada / etapa só na primeira linha do grupo
            else:
                result.error(line, FIELD_LABELS[F_STAGE], "vazia")
                continue
        else:
            if len(stage_name) > 160:
                result.error(line, FIELD_LABELS[F_STAGE], "nome com mais de 160 caracteres")
                continue
            stage = stages.get(stage_name)
            if stage is not None and simple:
                result.error(line, FIELD_LABELS[F_STAGE], f"“{stage_name}” repetida (sem subatividade, uma linha por etapa)")
                continue
            if stage is None:
                if len(stages) >= MAX_STAGES:
                    result.error(line, FIELD_LABELS[F_STAGE], f"mais de {MAX_STAGES} etapas")
                    continue
                stage = stages[stage_name] = NewStage(name=stage_name, activities=[])
        current = stage
        if simple:
            activity_name = stage.name
        elif not activity_name:
            continue  # etapa sem subatividade nesta linha
        units = _units(result, line, values, get)
        if units is False:
            continue
        raw_minutes = get(values, F_MINUTES)
        if simple and not _clean(raw_minutes):
            raw_minutes = SIMPLE_DEFAULT_MINUTES  # R4: etapa sem tempo pesa o padrão do modo simples
        else:
            seen_times.append(raw_minutes)
            raw_minutes = _to_minutes(raw_minutes, time_unit)
        activity = _read_activity(result, line, activity_name, raw_minutes, units, blank_is_zero=True)
        if activity is None:
            continue
        if len(stage.activities) >= MAX_ACTIVITIES_PER_STAGE:
            result.error(line, FIELD_LABELS[F_ACTIVITY], f"mais de {MAX_ACTIVITIES_PER_STAGE} atividades na etapa")
            continue
        stage.activities.append(activity)
    result.stages = list(stages.values())
    if not result.stages and not result.errors:
        result.error(header_row + 1, FIELD_LABELS[F_STAGE], "nenhuma etapa encontrada")
    if mapping.get(F_MINUTES) is not None:
        warning = unit_warning(seen_times, time_unit)
        if warning:
            result.warnings.append(warning)
    if mapping.get(F_DONE) is not None and mapping.get(F_PCT) is not None:
        result.notes.append("Com peças e % mapeados, valem as peças; o % foi usado só onde as peças estão vazias.")
    if simple:
        result.notes.append(
            "Sem subatividades: cada etapa entra com uma subatividade de mesmo nome (modo simples)."
        )
    return result


def _to_minutes(raw, unit: str):
    """Valor da célula de tempo em MINUTOS (``Decimal``). Em minutos, devolve a célula como veio.
    Valor ilegível volta como veio: ``_read_activity`` registra o erro da linha; o teto
    ``MAX_MINUTES`` também é conferido lá, já na unidade convertida."""
    if unit != UNIT_HOURS or not _clean(raw):
        return raw
    try:
        return _decimal(raw) * MINUTES_PER_HOUR
    except (ValueError, InvalidOperation):
        return raw


def unit_warning(raw_values, unit: str) -> str | None:
    """Aviso (não bloqueia) quando os tempos parecem estar em outra unidade: média dos valores
    positivos abaixo de 1 em minutos, ou acima de 24 em horas. ``None`` se tudo parece normal."""
    numbers = []
    for raw in raw_values:
        try:
            d = _decimal(raw) if _clean(raw) else None
        except (ValueError, InvalidOperation):
            continue
        if d is not None and d > 0:
            numbers.append(d)
    if not numbers:
        return None
    mean = sum(numbers) / len(numbers)
    shown = f"{mean:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    if unit == UNIT_MINUTES and mean < UNIT_WARN_MEAN_MINUTES_BELOW:
        return (
            f"Os tempos são muito pequenos para minutos (média de {shown}). Se a planilha usa horas, "
            "volte às colunas e escolha “Horas”."
        )
    if unit == UNIT_HOURS and mean > UNIT_WARN_MEAN_HOURS_ABOVE:
        return (
            f"Os tempos são muito grandes para horas (média de {shown}). Se a planilha usa minutos, "
            "volte às colunas e escolha “Minutos”."
        )
    return None


def _read_quantity(result: ImportResult, rows, get, quantity: int | None) -> None:
    if quantity is not None:
        if not 1 <= quantity <= MAX_QUANTITY:
            result.error(0, "meta", f"número inteiro entre 1 e {MAX_QUANTITY}")
        result.quantity = quantity
        return
    first_line = None
    for line, values in rows:
        raw = get(values, F_PLANNED)
        if not _clean(raw):
            continue
        try:
            value = _int(raw)
            if not 1 <= value <= MAX_QUANTITY:
                raise ValueError
        except ValueError:
            result.error(line, FIELD_LABELS[F_PLANNED], f"número inteiro entre 1 e {MAX_QUANTITY}")
            continue
        if first_line is None:
            result.quantity, first_line = value, line
        elif value != result.quantity:
            result.error(
                line, FIELD_LABELS[F_PLANNED],
                f"{value} diferente da linha {first_line} ({result.quantity}); o projeto tem uma meta só",
            )
    if result.quantity:
        return
    if any(_clean(get(v, F_DONE)) for _, v in rows):
        result.error(0, "meta", "com peças concluídas, informe a meta (coluna de previstas ou o número)")
        return
    if any(_clean(get(v, F_PCT)) for _, v in rows):
        result.quantity = DEFAULT_QUANTITY_PCT
        result.notes.append(f"Meta não informada: usamos {DEFAULT_QUANTITY_PCT} unidades para guardar o %. Ajuste depois.")
    else:
        result.quantity = 1
        result.notes.append("Meta não informada: usamos 1 unidade. Ajuste depois.")


def _read_due(result: ImportResult, rows, get) -> None:
    dates = set()
    for line, values in rows:
        raw = get(values, F_DUE)
        try:
            value = _date(raw.date() if isinstance(raw, datetime) else raw)
        except ValueError:
            result.error(line, FIELD_LABELS[F_DUE], "data inválida (use dd/mm/aaaa)")
            continue
        if value is not None:
            dates.add(value)
    if dates:
        result.due_date = max(dates)
        if len(dates) > 1:
            result.notes.append(f"Prazos diferentes por linha: usamos o último ({result.due_date:%d/%m/%Y}).")


def _units(result: ImportResult, line: int, values, get):
    """Peças da linha: coluna de peças; sem ela, % × meta. ``False`` = erro já registrado."""
    raw = get(values, F_DONE)
    if _clean(raw):
        return raw
    raw_pct = get(values, F_PCT)
    if not _clean(raw_pct):
        return None
    try:
        return calc.pecas_de_percentual(_pct(raw_pct), result.quantity)
    except (ValueError, InvalidOperation):
        result.error(line, FIELD_LABELS[F_PCT], "use um % entre 0 e 100 (ex.: 45%, 45 ou 0,45)")
        return False


# ---------------------------------------------------------------- grade ↔ JSON (formulário assinado)


def _json_value(value):
    if isinstance(value, datetime):
        value = value.date() if value.time() == datetime.min.time() else value
    if isinstance(value, date):
        return {"d": value.isoformat()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _from_json(value):
    if isinstance(value, dict):
        text = str(value.get("d", ""))
        try:
            return datetime.fromisoformat(text) if "T" in text else date.fromisoformat(text)
        except ValueError:
            return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def grid_to_data(grid: Grid) -> dict:
    return {
        "k": grid.kind,
        "f": grid.filename[:200],
        "s": [
            {"t": s.title, "r": [[_json_value(v) for v in row] for row in s.rows], "l": s.lines}
            for s in grid.sheets
        ],
    }


def grid_from_data(data: dict) -> Grid:
    """Reconstrói a grade com os mesmos tetos da leitura (não confia só na assinatura)."""
    try:
        sheets = []
        for s in list(data.get("s") or [])[:MAX_GRID_SHEETS]:
            rows = [[_from_json(v) for v in list(row)[:MAX_GRID_COLS]] for row in list(s["r"])[:MAX_GRID_ROWS]]
            lines = s.get("l")
            lines = [int(x) for x in lines][: len(rows)] if lines else None
            sheets.append(Sheet(str(s["t"])[:100], rows, lines))
        kind = "csv" if data.get("k") == "csv" else "xlsx"
        return Grid(kind, str(data.get("f") or "")[:200], sheets)
    except (KeyError, TypeError, ValueError):
        raise ImportError_("Dados da planilha inválidos; envie o arquivo de novo.") from None
