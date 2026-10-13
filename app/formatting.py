"""Formatação pt-BR para os templates (sem dependência de locale do sistema)."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo


def br_number(value, places: int = 1) -> str:
    if value is None:
        return "—"
    text = f"{float(value):,.{places}f}"
    return text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def br_pct(value, places: int = 1) -> str:
    if value is None:
        return "—"
    return br_number(float(value) * 100, places) + "%"


def br_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else "—"


def br_datetime(value: datetime | None, tz: str = "America/Sao_Paulo") -> str:
    if not value:
        return "—"
    if value.tzinfo is None:
        from datetime import timezone

        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(ZoneInfo(tz)).strftime("%d/%m/%Y %H:%M")
