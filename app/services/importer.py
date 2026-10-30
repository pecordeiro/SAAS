"""Importação de projeto: CSV (modelo do site / exportação), XLSX exportado pelo site (lista
plana ou layout da base), a planilha de referência ``acompanhamento_montagem_v4.xlsx`` e — R7 —
QUALQUER planilha .xlsx/.csv com mapeamento de colunas (``app/services/import_mapping.py``).

Fluxo: ``load_grid`` (arquivo em memória → ``Grid``: abas e linhas, com tetos) →
``auto_parse`` (formatos reconhecidos sozinhos) ou ``import_mapping.parse_mapped`` (colunas
escolhidas pela pessoa) → ``ImportResult`` com dados e erros por linha → pré-visualização →
``save`` grava TUDO numa transação só (quem chama faz o commit). Com qualquer erro, nada é
gravado. ``parse_upload`` = ``load_grid`` + ``auto_parse`` (comportamento da Fase 4).

Planilha de referência: o layout é descoberto pelos títulos da coluna A (como o teste de
paridade): “Meta…” (quantidade em B), blocos “Nome da etapa” → “Unidades previstas” →
“Subatividade” (cabeçalho) → atividades (A nome, B tempo ideal, D peças) → “Total da
etapa…”. Na aba “Equipe”: “Pessoas montando” e “Horas de trabalho por dia” (e, na
exportação do site, “Início do projeto” e “Prazo de entrega”).

Segurança: tamanho limitado (``IMPORT_MAX_BYTES``), tipo conferido pela extensão E pelo
conteúdo (XLSX = zip; o tamanho descompactado é conferido antes de abrir, contra zip bomb;
DTD/entidades e senha recusados), nada é gravado em disco, fórmulas não são avaliadas (só o
valor em cache).
"""

from __future__ import annotations

import csv
import io
import re
import uuid
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.extensions import db
from app.models import PROGRESS_DETAILED, PROGRESS_SIMPLE, Company, Project
from app.services import audit
from app.services.exporter import (
    COL_ACTIVITY,
    COL_DUE,
    COL_HOURS,
    COL_MINUTES,
    COL_PEOPLE,
    COL_PROJECT,
    COL_QUANTITY,
    COL_STAGE,
    COL_START,
    COL_STATUS,
    COL_UNITS,
    COLUMNS,
    STATUS_ACTIVE,
    STATUS_ARCHIVED,
    STATUS_STAGE_ARCHIVED,
)
from app.services.projects import NewActivity, NewStage, create_project, record_initial_progress

MAX_ROWS = 2000
MAX_STAGES = 100
MAX_ACTIVITIES_PER_STAGE = 200
MAX_MINUTES = Decimal("100000")
MAX_QUANTITY = 100000
MAX_UNCOMPRESSED = 30 * 1024 * 1024
MAX_ZIP_ENTRIES = 500

SOURCE_CSV = "csv"
SOURCE_XLSX = "xlsx"
SOURCE_REFERENCE = "planilha"

MODE_DETAILED = "detalhado"
MODE_SIMPLE = "simples"

REQUIRED = (COL_STAGE, COL_ACTIVITY, COL_MINUTES)


class ImportError_(Exception):
    """Arquivo recusado inteiro (tipo, tamanho, formato)."""


@dataclass
class RowError:
    line: int
    column: str
    message: str

    def __str__(self) -> str:
        return f"Linha {self.line}, {self.column}: {self.message}"


@dataclass
class ImportResult:
    source: str
    name: str = ""
    quantity: int = 0
    start_date: date | None = None
    due_date: date | None = None
    people: int = 1
    hours_per_day: Decimal = Decimal("8")
    stages: list[NewStage] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)
    # R7: avisos que não impedem a gravação (ex.: “meta não informada, usamos 100”).
    notes: list[str] = field(default_factory=list)
    # R7/R4: "detalhado" (subatividades) ou "simples" (só etapa + %). ``save`` grava o modo em
    # ``Project.progress_mode``; no simples cada etapa tem a atividade interna (nome da etapa,
    # peças = % × meta por ``calc.pecas_de_percentual``), a mesma representação da tela.
    mode: str = MODE_DETAILED
    # Planilha com mapeamento de colunas: unidade em que a coluna de tempo foi lida
    # (``import_mapping.UNIT_MINUTES``/``UNIT_HOURS``) ou ``None`` quando não há coluna de tempo.
    # Os tempos de ``stages`` já estão em MINUTOS; a prévia mostra a unidade para conferência.
    time_unit: str | None = None
    # Avisos que não impedem a gravação nem vão no payload (ex.: unidade de tempo provavelmente errada).
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def total_minutes(self) -> Decimal:
        """Soma do tempo ideal (minutos) de todas as atividades lidas, já convertido."""
        return sum((a.ideal_minutes for s in self.stages for a in s.activities), Decimal("0"))

    @property
    def activity_count(self) -> int:
        return sum(len(s.activities) for s in self.stages)

    def error(self, line: int, column: str, message: str) -> None:
        self.errors.append(RowError(line, column, message))


# ---------------------------------------------------------------- conversões


def _clean(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    # Desfaz a neutralização da exportação ('=..., '+..., '-..., '@...).
    if len(text) > 1 and text[0] == "'" and text[1] in "=+-@\t\r":
        text = text[1:]
    return text


def _decimal(value) -> Decimal:
    if isinstance(value, bool):
        raise ValueError
    if isinstance(value, (int, float, Decimal)):
        d = Decimal(str(value))
    else:
        text = _clean(value).replace(" ", "")
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        try:
            d = Decimal(text)
        except InvalidOperation:
            raise ValueError from None
    if not d.is_finite():
        raise ValueError
    return d


def _int(value) -> int:
    d = _decimal(value)
    if d != d.to_integral_value():
        raise ValueError
    return int(d)


def _date(value) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _clean(value)
    if not text:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError


def _norm_header(text) -> str:
    return " ".join(_clean(text).split()).casefold()


HEADER_KEYS = {_norm_header(c): c for c in COLUMNS}


# ---------------------------------------------------------------- linhas planas (CSV / XLSX do site)


def _parse_flat(result: ImportResult, header: list, data_rows) -> ImportResult:
    """``data_rows``: iterável de (número da linha no arquivo, lista de valores)."""
    index: dict[str, int] = {}
    for pos, raw in enumerate(header):
        key = HEADER_KEYS.get(_norm_header(raw))
        if key and key not in index:
            index[key] = pos
    missing = [c for c in (COL_PROJECT, COL_QUANTITY, *REQUIRED) if c not in index]
    if missing:
        result.error(1, "cabeçalho", "faltam as colunas " + ", ".join(f"“{c}”" for c in missing))
        return result

    def get(values, column):
        pos = index.get(column)
        return values[pos] if pos is not None and pos < len(values) else None

    stages: dict[str, NewStage] = {}
    first = True
    count = 0
    for line, values in data_rows:
        if all(_clean(v) == "" for v in values):
            continue
        count += 1
        if count > MAX_ROWS:
            result.error(line, "arquivo", f"mais de {MAX_ROWS} linhas")
            break
        if first:
            first = False
            _read_project_fields(result, line, lambda c: get(values, c))
        stage_name = _clean(get(values, COL_STAGE))
        if not stage_name:
            result.error(line, COL_STAGE, "vazia")
            continue
        if len(stage_name) > 160:
            result.error(line, COL_STAGE, "nome com mais de 160 caracteres")
            continue
        status = _clean(get(values, COL_STATUS)).casefold() or STATUS_ACTIVE
        if status not in (STATUS_ACTIVE, STATUS_ARCHIVED, STATUS_STAGE_ARCHIVED):
            result.error(line, COL_STATUS, "use ativa, arquivada ou etapa arquivada")
            continue
        stage = stages.get(stage_name)
        if stage is None:
            if len(stages) >= MAX_STAGES:
                result.error(line, COL_STAGE, f"mais de {MAX_STAGES} etapas")
                continue
            stage = stages[stage_name] = NewStage(name=stage_name, activities=[])
        if status == STATUS_STAGE_ARCHIVED:
            stage.archived = True
        activity_name = _clean(get(values, COL_ACTIVITY))
        if not activity_name:
            continue  # etapa sem atividade
        activity = _read_activity(result, line, activity_name, get(values, COL_MINUTES), get(values, COL_UNITS))
        if activity is None:
            continue
        activity.archived = status == STATUS_ARCHIVED
        if len(stage.activities) >= MAX_ACTIVITIES_PER_STAGE:
            result.error(line, COL_ACTIVITY, f"mais de {MAX_ACTIVITIES_PER_STAGE} subatividades na etapa")
            continue
        stage.activities.append(activity)
    if first:
        result.error(2, "arquivo", "nenhuma linha de dados")
    result.stages = list(stages.values())
    return result


def _read_project_fields(result: ImportResult, line: int, get) -> None:
    result.name = _clean(get(COL_PROJECT))[:160]
    if not result.name:
        result.error(line, COL_PROJECT, "informe o nome do projeto na primeira linha")
    try:
        result.quantity = _int(get(COL_QUANTITY))
        if not 1 <= result.quantity <= MAX_QUANTITY:
            raise ValueError
    except ValueError:
        result.error(line, COL_QUANTITY, f"número inteiro entre 1 e {MAX_QUANTITY}")
    for column, attr in ((COL_START, "start_date"), (COL_DUE, "due_date")):
        try:
            setattr(result, attr, _date(get(column)))
        except ValueError:
            result.error(line, column, "data inválida (use dd/mm/aaaa)")
    if result.start_date and result.due_date and result.due_date < result.start_date:
        result.error(line, COL_DUE, "antes do início")
    raw_people = get(COL_PEOPLE)
    if _clean(raw_people):
        try:
            result.people = _int(raw_people)
            if not 1 <= result.people <= 1000:
                raise ValueError
        except ValueError:
            result.error(line, COL_PEOPLE, "número inteiro entre 1 e 1000")
    raw_hours = get(COL_HOURS)
    if _clean(raw_hours):
        try:
            result.hours_per_day = _decimal(raw_hours).quantize(Decimal("0.01"))
            if not Decimal("0.5") <= result.hours_per_day <= Decimal("24"):
                raise ValueError
        except (ValueError, InvalidOperation):
            result.error(line, COL_HOURS, "número entre 0,5 e 24")


def _read_activity(
    result: ImportResult, line: int, name: str, raw_minutes, raw_units, blank_is_zero: bool = False
) -> NewActivity | None:
    """``blank_is_zero``: planilha de referência, onde tempo vazio vale 0 (N() do Excel)."""
    ok = True
    if blank_is_zero and raw_minutes in (None, ""):
        raw_minutes = 0
    if len(name) > 160:
        result.error(line, COL_ACTIVITY, "nome com mais de 160 caracteres")
        ok = False
    minutes = Decimal("0")
    try:
        minutes = _decimal(raw_minutes)
        if minutes < 0 or minutes > MAX_MINUTES:
            raise ValueError
        minutes = minutes.quantize(Decimal("0.01"))
    except (ValueError, InvalidOperation):
        result.error(line, "tempo ideal", "número inválido")
        ok = False
    units = 0
    if _clean(raw_units):
        try:
            units = _int(raw_units)
            if units < 0:
                raise ValueError
        except ValueError:
            result.error(line, COL_UNITS, "número inteiro inválido")
            ok = False
    if result.quantity and units > result.quantity:
        result.error(line, COL_UNITS, f"maior que a quantidade ({result.quantity})")
        ok = False
    return NewActivity(name=name, ideal_minutes=minutes, units_done=units) if ok else None


# ---------------------------------------------------------------- grade em memória (R7)
#
# Todo arquivo aceito vira uma ``Grid``: abas com as linhas de valores (texto, número, data),
# já com tetos de linhas/colunas. A detecção automática (formato do site, planilha de
# referência) e o mapeamento de colunas (``import_mapping``) leem a mesma grade, que também
# pode ir assinada no formulário entre a etapa de colunas e a prévia (nada vai para o disco).

MAX_GRID_ROWS = 5000
MAX_GRID_COLS = 60
MAX_GRID_SHEETS = 30
TEXT_DEMAIS = "Planilha com texto demais. Deixe só a aba com os dados e tente de novo."
MAX_CELL_CHARS = 1000        # nomes já são cortados em 160; o resto de uma célula nunca é usado
MAX_GRID_CHARS = 5_000_000   # texto total da grade: um .xlsx pequeno pode repetir a mesma célula grande 100 mil vezes


@dataclass
class Sheet:
    title: str
    rows: list[list]
    # Número da linha no arquivo de cada item de ``rows`` (no CSV, um campo entre aspas pode
    # ocupar várias linhas; no XLSX é sempre índice + 1).
    lines: list[int] | None = None

    @property
    def max_row(self) -> int:
        return len(self.rows)

    def value(self, row: int, col: int):
        """Valor da célula (1-based, como no Excel); fora da grade = None."""
        if 1 <= row <= len(self.rows):
            values = self.rows[row - 1]
            if 1 <= col <= len(values):
                return values[col - 1]
        return None

    def line(self, index: int) -> int:
        """Linha no arquivo do item ``index`` (0-based) de ``rows``."""
        if self.lines and index < len(self.lines):
            return self.lines[index]
        return index + 1


@dataclass
class Grid:
    kind: str  # SOURCE_CSV | SOURCE_XLSX
    filename: str
    sheets: list[Sheet]

    def sheet(self, title: str | None) -> Sheet | None:
        if title is None:
            return self.sheets[0] if self.sheets else None
        return next((s for s in self.sheets if s.title == title), None)


def _trim(values: list) -> list:
    while values and (values[-1] is None or (isinstance(values[-1], str) and not values[-1].strip())):
        values.pop()
    return values


def _csv_grid(data: bytes, filename: str = "") -> Grid:
    if b"\x00" in data:
        raise ImportError_("O arquivo não parece um CSV de texto.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("cp1252", errors="replace")
    first_line = text.split("\n", 1)[0]
    delimiter = max((";", ",", "\t"), key=first_line.count)
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    rows: list[list] = []
    lines: list[int] = []
    total = 0
    try:
        for row in reader:
            if len(rows) >= MAX_GRID_ROWS:
                break
            row = [c[:MAX_CELL_CHARS] for c in row[:MAX_GRID_COLS]]
            total += sum(len(c) for c in row)
            if total > MAX_GRID_CHARS:
                raise ImportError_(TEXT_DEMAIS)
            rows.append(row)
            lines.append(reader.line_num)
    except csv.Error as exc:  # pragma: no cover - CSV malformado raro
        raise ImportError_(f"CSV inválido: {exc}") from None
    return Grid(SOURCE_CSV, filename, [Sheet("CSV", rows, lines)])


def _cell_value(value):
    """Valores do openpyxl para a grade: só tipos simples (vão em JSON no formulário)."""
    if isinstance(value, str):
        return value[:MAX_CELL_CHARS]
    if value is None or isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.date() if value.time() == datetime.min.time() else value
    if isinstance(value, date):
        return value
    return str(value)


def _xlsx_grid(data: bytes, filename: str = "") -> Grid:
    wb = _open_workbook(data)
    sheets = []
    total = 0
    for ws in wb.worksheets[:MAX_GRID_SHEETS]:
        rows = []
        for values in ws.iter_rows(
            min_row=1,
            max_row=min(ws.max_row or 1, MAX_GRID_ROWS),
            max_col=min(ws.max_column or 1, MAX_GRID_COLS),
            values_only=True,
        ):
            row = _trim([_cell_value(v) for v in values])
            total += sum(len(v) for v in row if isinstance(v, str))
            if total > MAX_GRID_CHARS:
                raise ImportError_(TEXT_DEMAIS)
            rows.append(row)
        while rows and not rows[-1]:
            rows.pop()
        sheets.append(Sheet(str(ws.title), rows))
    return Grid(SOURCE_XLSX, filename, sheets)


def load_grid(filename: str, data: bytes, max_bytes: int) -> Grid:
    """Confere tamanho e tipo (extensão + conteúdo) e lê o arquivo em memória numa grade."""
    if not data:
        raise ImportError_("Escolha um arquivo .csv ou .xlsx.")
    if len(data) > max_bytes:
        raise ImportError_(f"Arquivo maior que {max_bytes // (1024 * 1024)} MB.")
    ext = (filename or "").rsplit(".", 1)[-1].lower() if "." in (filename or "") else ""
    is_zip = data[:4] == b"PK\x03\x04"
    if ext == "xlsx" and is_zip:
        return _xlsx_grid(data, filename)
    if ext == "csv" and not is_zip:
        return _csv_grid(data, filename)
    raise ImportError_("Envie um arquivo .csv ou .xlsx (o conteúdo precisa bater com a extensão).")


# ---------------------------------------------------------------- formatos reconhecidos sozinhos

SITE_HEADER = frozenset(_norm_header(c) for c in (COL_STAGE, COL_ACTIVITY, COL_MINUTES))
SITE_HEADER_FULL = SITE_HEADER | {_norm_header(COL_PROJECT), _norm_header(COL_QUANTITY)}


def _flat_rows(sheet: Sheet):
    return ((sheet.line(i), list(values)) for i, values in enumerate(sheet.rows) if i > 0)


def auto_parse(grid: Grid, strict: bool = True) -> ImportResult | None:
    """Formatos que o sistema reconhece sem mapeamento: CSV/XLSX do próprio site (cabeçalho na
    linha 1) e a planilha de referência (blocos de etapa). ``None`` = precisa mapear colunas.

    ``strict=False`` mantém o comportamento antigo de ``parse_upload``: sem formato
    reconhecido, devolve os erros do formato mais provável (CSV do site ou referência)."""
    header_set = SITE_HEADER_FULL if strict else SITE_HEADER
    for sheet in grid.sheets:
        header = sheet.rows[0] if sheet.rows else []
        if {_norm_header(h) for h in header} >= header_set:
            return _parse_flat(ImportResult(source=grid.kind), header, _flat_rows(sheet))
    if grid.kind == SOURCE_XLSX:
        if not strict or any(_find_blocks(s) for s in grid.sheets):
            return parse_reference(grid)
        return None
    if strict:
        return None
    result = ImportResult(source=SOURCE_CSV)
    sheet = grid.sheets[0]
    if not sheet.rows:
        result.error(1, "arquivo", "vazio")
        return result
    return _parse_flat(result, sheet.rows[0], _flat_rows(sheet))


def parse_csv(data: bytes) -> ImportResult:
    return auto_parse(_csv_grid(data), strict=False)


# ---------------------------------------------------------------- XLSX (proteções)


_DTD_MARKERS = tuple(
    marker.encode(enc) for marker in ("<!DOCTYPE", "<!ENTITY") for enc in ("utf-8", "utf-16-le", "utf-16-be")
)
_SCAN_CHUNK = 64 * 1024


def _inspect_zip(data: bytes) -> None:
    """Fase 7: confere o zip pelo que REALMENTE sai da descompressão (não pelo tamanho
    declarado no cabeçalho, que o atacante escolhe) e recusa XML com DTD/entidades (XXE e
    "billion laughs" — uma planilha legítima nunca tem DOCTYPE)."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            infos = zf.infolist()
            if len(infos) > MAX_ZIP_ENTRIES or sum(i.file_size for i in infos) > MAX_UNCOMPRESSED:
                raise ImportError_("Planilha grande demais depois de descompactada.")
            total = 0
            for info in infos:
                if info.is_dir():
                    continue
                if info.flag_bits & 0x1:
                    raise ImportError_("Planilha protegida por senha não é aceita.")
                tail = b""
                with zf.open(info) as member:
                    while True:
                        chunk = member.read(_SCAN_CHUNK)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_UNCOMPRESSED:
                            raise ImportError_("Planilha grande demais depois de descompactada.")
                        window = tail + chunk
                        if any(marker in window for marker in _DTD_MARKERS):
                            raise ImportError_("Planilha com definição de documento (DTD) não é aceita.")
                        tail = window[-32:]
    except (zipfile.BadZipFile, zipfile.LargeZipFile, EOFError, NotImplementedError, RuntimeError, ValueError, OSError) as exc:
        if isinstance(exc, ImportError_):
            raise
        raise ImportError_("O arquivo não é uma planilha .xlsx válida.") from None


def _open_workbook(data: bytes):
    _inspect_zip(data)
    import warnings

    from openpyxl import load_workbook

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return load_workbook(io.BytesIO(data), data_only=True)
    except Exception:  # noqa: BLE001 - qualquer falha do openpyxl = arquivo inválido
        raise ImportError_("Não foi possível ler a planilha .xlsx.") from None


# ---------------------------------------------------------------- planilha de referência


def _a(ws: Sheet, row: int) -> str:
    return _clean(ws.value(row, 1))


def parse_reference(grid: Grid) -> ImportResult:
    """Layout da planilha de referência (e da exportação “layout da base”, que é o mesmo):
    título em A1, “Meta…” com a quantidade em B, blocos de etapa; na aba Equipe, pessoas,
    horas por dia e (só na exportação do site) início e prazo.

    Arquivo com VÁRIOS projetos (abas “<Nome> - Acompanhamento”…): este lê o primeiro (o
    principal, abas sem prefixo); ``parse_reference_many`` lê todos."""
    ws = next((s for s in grid.sheets if _find_blocks(s)), None)
    team = next((s for s in grid.sheets if s.title.casefold() == "equipe"), None)
    return _parse_reference_sheets(ws, team)


# Abas de um projeto no arquivo da equipe: “Acompanhamento”, “Equipe”, “Como funciona” (o
# principal) e “<Nome> - Acompanhamento”, “<Nome> - Equipe”, “<Nome> - Como funciona” (os
# demais). Regra da base: um projeto existe se as TRÊS abas existirem.
ROLE_TRACKING = "acompanhamento"
ROLE_TEAM = "equipe"
ROLE_HOWTO = "como funciona"
_PROJECT_SHEET = re.compile(
    r"^\s*(?:(?P<name>.+?)\s+[-–—]\s+)?(?P<role>acompanhamento|equipe|como funciona)\s*$", re.IGNORECASE
)
_TITLE_PREFIX = re.compile(r"^\s*acompanhamento\s+da\s+montagem\s*[-–—:]\s*", re.IGNORECASE)


@dataclass(frozen=True)
class ReferenceProject:
    """Um projeto encontrado no arquivo: ``key`` vazio = o principal (abas sem prefixo)."""

    key: str
    tracking: str  # título da aba de acompanhamento
    team: str  # título da aba Equipe


def reference_projects(grid: Grid) -> list[ReferenceProject]:
    """Projetos do arquivo pela regra das três abas, na ordem das abas (principal primeiro).
    Função pura sobre os títulos das abas."""
    groups: dict[str, dict[str, str]] = {}
    names: dict[str, str] = {}
    for sheet in grid.sheets:
        match = _PROJECT_SHEET.match(sheet.title or "")
        if not match:
            continue
        name = " ".join((match.group("name") or "").split())
        key = name.casefold()
        names.setdefault(key, name)
        groups.setdefault(key, {}).setdefault(match.group("role").casefold(), sheet.title)
    found = [
        ReferenceProject(names[key], roles[ROLE_TRACKING], roles[ROLE_TEAM])
        for key, roles in groups.items()
        if {ROLE_TRACKING, ROLE_TEAM, ROLE_HOWTO} <= roles.keys()
    ]
    return sorted(found, key=lambda p: p.key != "")


def project_name_from_title(title: str, fallback: str = "") -> str:
    """“Acompanhamento da Montagem – Agro” → “Agro”; sem o prefixo, o título como está."""
    title = _clean(title)
    short = _TITLE_PREFIX.sub("", title).strip()
    return (short if short and short != title else (title or fallback) or "Projeto importado")[:160]


def parse_reference_many(grid: Grid) -> list[tuple[ReferenceProject, ImportResult]]:
    """Todos os projetos do arquivo (regra das três abas), cada um com o seu resultado e os
    seus erros. O nome vem do A1 sem “Acompanhamento da Montagem –” (ou do prefixo das abas).
    Lista vazia = o arquivo não segue o padrão de vários projetos."""
    out = []
    for project in reference_projects(grid):
        ws = grid.sheet(project.tracking)
        result = _parse_reference_sheets(ws if ws is not None and _find_blocks(ws) else None, grid.sheet(project.team))
        result.name = project_name_from_title(_a(ws, 1) if ws is not None else "", project.key)
        out.append((project, result))
    return out


def _parse_reference_sheets(ws: Sheet | None, team: Sheet | None) -> ImportResult:
    result = ImportResult(source=SOURCE_REFERENCE)
    if ws is None:
        result.error(1, "A", "nenhum bloco de etapa encontrado (título “N. Nome” seguido de “Unidades previstas”)")
        return result
    result.name = (_a(ws, 1) or "Projeto importado")[:160]
    meta_row = next((r for r in range(1, min(ws.max_row, 60) + 1) if _a(ws, r).casefold().startswith("meta")), None)
    if meta_row is None:
        result.error(1, "A", "linha “Meta…” (quantidade prevista) não encontrada")
    else:
        try:
            result.quantity = _int(ws.value(meta_row, 2))
            if not 1 <= result.quantity <= MAX_QUANTITY:
                raise ValueError
        except ValueError:
            result.error(meta_row, "B (meta)", f"número inteiro entre 1 e {MAX_QUANTITY}")
    if team is not None:
        for r in range(1, min(team.max_row, 60) + 1):
            title = _a(team, r).casefold()
            value = team.value(r, 2)
            try:
                if title.startswith("pessoas montando"):
                    result.people = _int(value)
                elif title.startswith("horas de trabalho por dia"):
                    result.hours_per_day = _decimal(value).quantize(Decimal("0.01"))
                elif title.startswith("início do projeto"):
                    result.start_date = _date(value)
                elif title.startswith("prazo de entrega"):
                    result.due_date = _date(value)
            except (ValueError, InvalidOperation):
                result.error(r, f"Equipe!B ({_a(team, r)})", "valor inválido")
    for title_row, first, total in _find_blocks(ws):
        stage = NewStage(name=_a(ws, title_row)[:160], activities=[])
        for r in range(first, total):
            name = _a(ws, r)
            if not name:
                continue
            activity = _read_activity(
                result, r, name[:160], ws.value(r, 2), ws.value(r, 4), blank_is_zero=True
            )
            if activity is not None:
                stage.activities.append(activity)
        if len(stage.activities) > MAX_ACTIVITIES_PER_STAGE:
            result.error(title_row, "A", f"mais de {MAX_ACTIVITIES_PER_STAGE} subatividades na etapa")
        result.stages.append(stage)
        if len(result.stages) > MAX_STAGES:
            result.error(title_row, "A", f"mais de {MAX_STAGES} etapas")
            break
    return result


def _find_blocks(ws: Sheet) -> list[tuple[int, int, int]]:
    """(linha do título, primeira linha de atividade, linha “Total da etapa”) de cada bloco.

    Título: qualquer texto na coluna A (a referência usa “N. Nome”; a exportação do site
    escreve o nome da etapa como está) seguido de “Unidades previstas” e “Subatividade”."""
    blocks = []
    r = 1
    max_row = min(ws.max_row, MAX_GRID_ROWS)
    while r <= max_row:
        if (
            _a(ws, r)
            and _a(ws, r + 1).startswith("Unidades previstas")
            and _a(ws, r + 2).startswith("Subatividade")
        ):
            total = r + 3
            while total <= max_row and not _a(ws, total).startswith("Total da etapa"):
                total += 1
            if total > max_row or total - r > MAX_ACTIVITIES_PER_STAGE + 20:
                break
            blocks.append((r, r + 3, total))
            r = total + 1
        else:
            r += 1
    return blocks


# ---------------------------------------------------------------- entrada única


def parse_upload(filename: str, data: bytes, max_bytes: int) -> ImportResult:
    """Confere tamanho e tipo (extensão + conteúdo) e lê o arquivo em memória (só os formatos
    reconhecidos sozinhos; para mapear colunas, ``load_grid`` + ``import_mapping``)."""
    return auto_parse(load_grid(filename, data, max_bytes), strict=False)


# ---------------------------------------------------------------- pré-visualização ↔ gravação


def to_payload(result: ImportResult) -> dict:
    """Dados já validados, em JSON (vão assinados no formulário de confirmação)."""
    data = asdict(result)
    data.pop("errors")
    data.pop("notes")
    data.pop("warnings")
    data.pop("time_unit")
    data["start_date"] = result.start_date.isoformat() if result.start_date else None
    data["due_date"] = result.due_date.isoformat() if result.due_date else None
    data["hours_per_day"] = str(result.hours_per_day)
    for stage in data["stages"]:
        for activity in stage["activities"]:
            activity["ideal_minutes"] = str(activity["ideal_minutes"])
    return data


def from_payload(data: dict) -> ImportResult:
    """Reconstrói o resultado e REVALIDA (não confia só na assinatura)."""
    result = ImportResult(source=str(data.get("source", SOURCE_CSV)))
    result.name = str(data.get("name", ""))[:160]
    result.mode = MODE_SIMPLE if data.get("mode") == MODE_SIMPLE else MODE_DETAILED
    try:
        result.quantity = int(data.get("quantity", 0))
        result.start_date = date.fromisoformat(data["start_date"]) if data.get("start_date") else None
        result.due_date = date.fromisoformat(data["due_date"]) if data.get("due_date") else None
        result.people = int(data.get("people", 1))
        result.hours_per_day = Decimal(str(data.get("hours_per_day", "8")))
        for s in data.get("stages", [])[: MAX_STAGES + 1]:
            stage = NewStage(name=str(s["name"])[:160], activities=[], archived=bool(s.get("archived")))
            for a in s.get("activities", [])[: MAX_ACTIVITIES_PER_STAGE + 1]:
                stage.activities.append(
                    NewActivity(
                        name=str(a["name"])[:160],
                        ideal_minutes=Decimal(str(a["ideal_minutes"])),
                        units_done=int(a.get("units_done", 0)),
                        archived=bool(a.get("archived")),
                    )
                )
            result.stages.append(stage)
    except (KeyError, TypeError, ValueError, InvalidOperation):
        result.error(0, "dados", "pré-visualização inválida; envie o arquivo de novo")
        return result
    validate(result)
    return result


def validate(result: ImportResult) -> None:
    if not result.name:
        result.error(0, COL_PROJECT, "vazio")
    if not 1 <= result.quantity <= MAX_QUANTITY:
        result.error(0, COL_QUANTITY, "fora do limite")
    if not 1 <= result.people <= 1000 or not Decimal("0.5") <= result.hours_per_day <= Decimal("24"):
        result.error(0, "equipe", "pessoas ou horas por dia fora do limite")
    if not result.stages or len(result.stages) > MAX_STAGES:
        result.error(0, COL_STAGE, "nenhuma etapa ou etapas demais")
    for stage in result.stages:
        if not stage.name or len(stage.activities) > MAX_ACTIVITIES_PER_STAGE:
            result.error(0, COL_STAGE, "etapa inválida")
        for activity in stage.activities:
            if (
                not activity.name
                or not Decimal("0") <= activity.ideal_minutes <= MAX_MINUTES
                or not 0 <= activity.units_done <= result.quantity
            ):
                result.error(0, COL_ACTIVITY, f"subatividade “{activity.name}” inválida")


def save(company: Company, result: ImportResult, user_id: uuid.UUID | None, name: str | None = None) -> Project:
    """Grava o projeto inteiro (sem commit: quem chama faz um commit só). Confere o limite
    de projetos do plano como qualquer criação."""
    if not result.ok:
        raise ValueError("importação com erros não pode ser gravada")
    project = create_project(
        company,
        name=(name or result.name)[:160],
        quantity=result.quantity,
        start_date=result.start_date,
        due_date=result.due_date,
        people=result.people,
        hours_per_day=result.hours_per_day,
        stages=result.stages,
        source="import",
        progress_mode=PROGRESS_SIMPLE if result.mode == MODE_SIMPLE else PROGRESS_DETAILED,
    )
    record_initial_progress(project, user_id)
    audit.record(
        audit.PROJECT_IMPORTED,
        company_id=company.id,
        actor_user_id=user_id,
        object_type="project",
        object_id=project.id,
        details={"source": result.source, "mode": result.mode, "stages": len(result.stages), "activities": result.activity_count},
    )
    db.session.flush()
    return project
