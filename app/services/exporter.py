"""Exportação de projeto em CSV e XLSX (mesmas colunas da tela + o que a importação lê).

Uma linha por atividade (etapa sem atividade sai numa linha só com a etapa). Inclui o que
foi ARQUIVADO (coluna “Situação”), para o histórico não se perder e para que exportar →
importar devolva o mesmo projeto.

Segurança: toda célula de texto que começa com ``= + - @`` (ou TAB/CR) sai com um apóstrofo
na frente, para o Excel/LibreOffice não interpretar como fórmula (CSV/formula injection).
A importação remove esse apóstrofo de volta.
"""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from datetime import date
from decimal import Decimal

from app.models import Project
from app.services import calc
from app.services.projects import active_activities, active_stages

COL_PROJECT = "Projeto"
COL_QUANTITY = "Quantidade"
COL_START = "Início"
COL_DUE = "Prazo"
COL_PEOPLE = "Pessoas"
COL_HOURS = "Horas por dia"
COL_STAGE = "Etapa"
COL_ACTIVITY = "Atividade"
COL_MINUTES = "Tempo ideal (min)"
COL_UNITS = "Peças concluídas"
COL_STATUS = "Situação"
COL_PCT = "% concluído"
COL_LEFT = "Tempo que falta (h)"

COLUMNS = (
    COL_PROJECT, COL_QUANTITY, COL_START, COL_DUE, COL_PEOPLE, COL_HOURS,
    COL_STAGE, COL_ACTIVITY, COL_MINUTES, COL_UNITS, COL_STATUS, COL_PCT, COL_LEFT,
)

STATUS_ACTIVE = "ativa"
STATUS_ARCHIVED = "arquivada"
STATUS_STAGE_ARCHIVED = "etapa arquivada"

DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def neutralize(value):
    """Texto perigoso para planilha ganha um apóstrofo na frente (números ficam como estão)."""
    if isinstance(value, str) and value.startswith(DANGEROUS_PREFIXES):
        return "'" + value
    return value


def br_decimal(value) -> str:
    """Número no formato brasileiro, sem zeros inúteis: 10 → "10", 7.5 → "7,5"."""
    if value is None:
        return ""
    d = Decimal(str(value)).normalize()
    text = format(d, "f")
    return text.replace(".", ",")


def br_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else ""


def rows(project: Project) -> list[dict]:
    """Linhas da exportação (valores Python; o formato de cada arquivo cuida do resto)."""
    result = calc.resumo_projeto(_calc_etapas(project), project.quantity, project.people, float(project.hours_per_day))
    live_results = {}
    for stage, stage_result in zip(active_stages(project), result.etapas):
        for activity, act_result in zip(active_activities(stage), stage_result.atividades):
            live_results[activity.id] = act_result
    base = {
        COL_PROJECT: project.name,
        COL_QUANTITY: project.quantity,
        COL_START: project.start_date,
        COL_DUE: project.due_date,
        COL_PEOPLE: project.people,
        COL_HOURS: project.hours_per_day,
    }
    out = []
    for stage in sorted(project.stages, key=lambda s: (s.archived_at is not None, s.position)):
        acts = sorted(stage.activities, key=lambda a: (a.archived_at is not None, a.position))
        if not acts:
            out.append({**base, COL_STAGE: stage.name, COL_STATUS: STATUS_STAGE_ARCHIVED if stage.archived_at else STATUS_ACTIVE})
            continue
        for activity in acts:
            if stage.archived_at is not None:
                status = STATUS_STAGE_ARCHIVED
            elif activity.archived_at is not None:
                status = STATUS_ARCHIVED
            else:
                status = STATUS_ACTIVE
            r = live_results.get(activity.id)
            out.append(
                {
                    **base,
                    COL_STAGE: stage.name,
                    COL_ACTIVITY: activity.name,
                    COL_MINUTES: activity.ideal_minutes,
                    COL_UNITS: activity.units_done,
                    COL_STATUS: status,
                    COL_PCT: r.pct if r else None,
                    COL_LEFT: (r.tempo_restante_min / 60) if r else None,
                }
            )
    return out


def _calc_etapas(project: Project) -> list[calc.Etapa]:
    from app.services.projects import to_calc

    return to_calc(project)


def _csv_cell(column: str, value) -> str:
    if value is None:
        return ""
    if isinstance(value, date):
        return br_date(value)
    if column == COL_PCT:
        return br_decimal(round(Decimal(str(value)) * 100, 1)) + "%"
    if column == COL_LEFT:
        return br_decimal(round(Decimal(str(value)), 2))
    if isinstance(value, (int, float, Decimal)):
        return br_decimal(value)
    return neutralize(str(value))


def to_csv(project: Project) -> bytes:
    """CSV no padrão do Excel brasileiro: ``;`` como separador, vírgula decimal, UTF-8 com BOM."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(COLUMNS)
    for row in rows(project):
        writer.writerow([_csv_cell(c, row.get(c)) for c in COLUMNS])
    return ("﻿" + buffer.getvalue()).encode("utf-8")


def template_csv() -> bytes:
    """Modelo para baixar no site: cabeçalho + 2 linhas de exemplo."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(COLUMNS[:11])
    writer.writerow(["Lote 2026-001", "10", "05/10/2026", "30/10/2026", "3", "8", "1. Preparação", "Separar componentes", "10", "0", STATUS_ACTIVE])
    writer.writerow(["", "", "", "", "", "", "1. Preparação", "Conferir a base", "5,5", "0", STATUS_ACTIVE])
    return ("﻿" + buffer.getvalue()).encode("utf-8")


def to_xlsx(project: Project) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Projeto"
    ws.append(list(COLUMNS))
    for row in rows(project):
        values = []
        for column in COLUMNS:
            value = row.get(column)
            if isinstance(value, Decimal):
                value = float(value)
            if column == COL_PCT and value is not None:
                value = round(float(value), 4)
            if column == COL_LEFT and value is not None:
                value = round(float(value), 2)
            values.append(neutralize(value))
        ws.append(values)
    for cells in ws.iter_rows(min_row=2):
        for cell in cells:
            if isinstance(cell.value, str):
                cell.data_type = "s"  # nunca fórmula, mesmo que o texto pareça uma
            elif isinstance(cell.value, date):
                cell.number_format = "DD/MM/YYYY"
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def filename(project: Project, ext: str) -> str:
    """Nome de arquivo só com ASCII seguro (vai no Content-Disposition)."""
    ascii_name = unicodedata.normalize("NFKD", project.name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^A-Za-z0-9]+", "-", ascii_name).strip("-").lower()[:60] or "projeto"
    return f"{slug}.{ext}"
