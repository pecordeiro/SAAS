"""Feriados nacionais (linhas globais com company_id NULL) e feriados da empresa.

Nacionais: Lei 662/1949 (com 6.802/1980 e 14.759/2023) — 1º/1, 21/4, 1º/5, 7/9, 12/10,
2/11, 15/11, 20/11 e 25/12 — mais a Sexta-feira da Paixão (móvel, guardada em todo o país).
Carnaval e Corpus Christi são ponto facultativo: a empresa cadastra como feriado próprio
se parar nesses dias.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import or_, select

from app.extensions import db
from app.models import Holiday

FIXED_NATIONAL: tuple[tuple[int, int, str], ...] = (
    (1, 1, "Confraternização Universal"),
    (4, 21, "Tiradentes"),
    (5, 1, "Dia do Trabalho"),
    (9, 7, "Independência do Brasil"),
    (10, 12, "Nossa Senhora Aparecida"),
    (11, 2, "Finados"),
    (11, 15, "Proclamação da República"),
    (11, 20, "Dia Nacional de Zumbi e da Consciência Negra"),
    (12, 25, "Natal"),
)


def easter(year: int) -> date:
    """Domingo de Páscoa (algoritmo de Meeus/Jones/Butcher, calendário gregoriano)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    m = (32 + 2 * e + 2 * i - h - k) % 7
    n = (a + 11 * h + 22 * m) // 451
    month, day = divmod(h + m - 7 * n + 114, 31)
    return date(year, month, day + 1)


def national_holidays(year: int) -> list[tuple[date, str]]:
    days = [(date(year, m, d), name) for m, d, name in FIXED_NATIONAL]
    if year < 2024:  # 20/11 virou feriado nacional pela Lei 14.759/2023
        days = [(d, n) for d, n in days if (d.month, d.day) != (11, 20)]
    days.append((easter(year) - timedelta(days=2), "Sexta-feira da Paixão"))
    return sorted(days)


def seed_national_holidays(first_year: int, last_year: int) -> int:
    """Grava os feriados nacionais dos anos pedidos (idempotente). Devolve quantos criou."""
    existing = set(
        db.session.execute(
            select(Holiday.day).where(
                Holiday.company_id.is_(None),
                Holiday.day >= date(first_year, 1, 1),
                Holiday.day <= date(last_year, 12, 31),
            )
        ).scalars()
    )
    created = 0
    for year in range(first_year, last_year + 1):
        for day, name in national_holidays(year):
            if day not in existing:
                db.session.add(Holiday(company_id=None, day=day, name=name))
                created += 1
    db.session.flush()
    return created


def holidays_for(company_id) -> list[date]:
    """Dias de feriado que valem para a empresa: os nacionais + os dela."""
    return list(
        db.session.execute(
            select(Holiday.day).where(or_(Holiday.company_id.is_(None), Holiday.company_id == company_id))
        ).scalars()
    )
