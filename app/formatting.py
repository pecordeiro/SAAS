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


def br_date_short(value: date | None) -> str:
    return value.strftime("%d/%m") if value else "—"


def br_datetime(value: datetime | None, tz: str = "America/Sao_Paulo") -> str:
    if not value:
        return "—"
    if value.tzinfo is None:
        from datetime import timezone

        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(ZoneInfo(tz)).strftime("%d/%m/%Y %H:%M")


DEFAULT_TZ = "America/Sao_Paulo"


def br_hours(value, long: bool = False) -> str:
    """Horas decimais → “100 h 30” (ou “100 h 30 min” com long=True); “—” se vazio."""
    if value is None:
        return "—"
    total_min = int(round(float(value) * 60))
    hours, minutes = divmod(total_min, 60)
    text = f"{br_number(hours, 0)} h"
    if minutes:
        text += f" {minutes:02d}" + (" min" if long else "")
    return text


def local_dt(value: datetime, tz: str = DEFAULT_TZ) -> datetime:
    if value.tzinfo is None:
        from datetime import timezone

        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(ZoneInfo(tz))


def br_time(value: datetime | None, tz: str = DEFAULT_TZ) -> str:
    return local_dt(value, tz).strftime("%H:%M") if value else "—"


def br_day_label(value: date | None, today: date | None = None) -> str:
    """Rótulo de grupo do histórico: “Hoje, 13/10”, “Ontem, 12/10” ou “09/10/2026”."""
    if value is None:
        return "—"
    today = today or datetime.now(ZoneInfo(DEFAULT_TZ)).date()
    if value == today:
        return f"Hoje, {value:%d/%m}"
    if (today - value).days == 1:
        return f"Ontem, {value:%d/%m}"
    return value.strftime("%d/%m/%Y")


WEEKDAY_ABBR = ("seg", "ter", "qua", "qui", "sex", "sáb", "dom")


def br_workdays(days) -> str:
    """Dias de trabalho: “seg–sex” quando seguidos, senão “seg, qua, sex”."""
    ordered = sorted(set(days))
    if not ordered:
        return "nenhum"
    if len(ordered) > 2 and ordered == list(range(ordered[0], ordered[-1] + 1)):
        return f"{WEEKDAY_ABBR[ordered[0]]}–{WEEKDAY_ABBR[ordered[-1]]}"
    return ", ".join(WEEKDAY_ABBR[d] for d in ordered)
