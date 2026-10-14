"""Configurações da empresa (/app/empresa): dados, jornada, dias de trabalho e feriados.

Só o proprietário muda (a rota exige). Toda alteração entra em ``audit_logs`` na mesma
transação. Feriados nacionais são globais (``company_id`` NULL) e não aparecem aqui como
editáveis: a empresa só cria e remove os dela.
"""

from __future__ import annotations

import re
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.extensions import db
from app.models import Company, Holiday
from app.services import audit
from app.tenancy import scoped

WEEKDAYS = (
    (0, "Seg", "Segunda"),
    (1, "Ter", "Terça"),
    (2, "Qua", "Quarta"),
    (3, "Qui", "Quinta"),
    (4, "Sex", "Sexta"),
    (5, "Sáb", "Sábado"),
    (6, "Dom", "Domingo"),
)
MAX_COMPANY_HOLIDAYS = 200


class CompanyError(Exception):
    """Dado inválido (mensagem pronta para a tela)."""


def format_cnpj(digits: str) -> str:
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def valid_cnpj(raw: str) -> bool:
    """Confere os dois dígitos verificadores (módulo 11)."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) != 14 or len(set(digits)) == 1:
        return False
    for size in (12, 13):
        weights = list(range(size - 7, 1, -1)) + list(range(9, 1, -1))
        total = sum(int(d) * w for d, w in zip(digits[:size], weights))
        check = (total * 10) % 11 % 10
        if check != int(digits[size]):
            return False
    return True


def mask_from_days(days) -> int:
    mask = 0
    for day in days:
        if day in range(7):
            mask |= 1 << day
    return mask


def update_company(
    company: Company,
    *,
    name: str,
    cnpj: str | None,
    daily_hours: Decimal,
    workdays: list[int],
    user_id: uuid.UUID | None,
) -> None:
    name = (name or "").strip()
    if not name or len(name) > 120:
        raise CompanyError("Informe o nome da empresa (até 120 caracteres).")
    digits = re.sub(r"\D", "", cnpj or "")
    if digits and not valid_cnpj(digits):
        raise CompanyError("CNPJ inválido. Confira os 14 dígitos.")
    mask = mask_from_days(workdays)
    if mask == 0:
        raise CompanyError("Marque pelo menos um dia de trabalho na semana.")
    if not Decimal("0.5") <= daily_hours <= Decimal("24"):
        raise CompanyError("A jornada deve ficar entre 0,5 e 24 horas por dia.")
    before = {"name": company.name, "daily_hours": str(company.daily_hours), "workdays_mask": company.workdays_mask}
    company.name = name
    company.cnpj = format_cnpj(digits) if digits else None
    company.daily_hours = daily_hours
    company.workdays_mask = mask
    db.session.flush()
    audit.record(
        audit.COMPANY_UPDATED,
        company_id=company.id,
        actor_user_id=user_id,
        object_type="company",
        object_id=company.id,
        details={"antes": before, "depois": {"name": name, "daily_hours": str(daily_hours), "workdays_mask": mask}},
    )


def list_company_holidays() -> list[Holiday]:
    """Feriados próprios da empresa da sessão, do mais próximo ao mais distante."""
    return list(db.session.execute(scoped(Holiday).order_by(Holiday.day)).scalars())


def add_holiday(company: Company, day: date, name: str, user_id: uuid.UUID | None) -> Holiday:
    name = (name or "").strip()
    if not name or len(name) > 120:
        raise CompanyError("Dê um nome ao feriado (até 120 caracteres).")
    if day.year < 2000 or day.year > 2100:
        raise CompanyError("Data fora do intervalo aceito.")
    existing = db.session.execute(scoped(Holiday).where(Holiday.day == day)).scalars().first()
    if existing is not None:
        raise CompanyError("Já existe um feriado da empresa nesta data.")
    count = len(list_company_holidays())
    if count >= MAX_COMPANY_HOLIDAYS:
        raise CompanyError(f"Limite de {MAX_COMPANY_HOLIDAYS} feriados da empresa atingido.")
    holiday = Holiday(company_id=company.id, day=day, name=name)
    db.session.add(holiday)
    db.session.flush()
    audit.record(
        audit.HOLIDAY_ADDED,
        company_id=company.id,
        actor_user_id=user_id,
        object_type="holiday",
        object_id=holiday.id,
        details={"day": day.isoformat(), "name": name},
    )
    return holiday


def remove_holiday(holiday: Holiday, user_id: uuid.UUID | None) -> None:
    """Remove um feriado DA EMPRESA (o chamador já resolveu o id na empresa da sessão)."""
    if holiday.company_id is None:
        raise CompanyError("Feriados nacionais não podem ser removidos.")
    audit.record(
        audit.HOLIDAY_REMOVED,
        company_id=holiday.company_id,
        actor_user_id=user_id,
        object_type="holiday",
        object_id=holiday.id,
        details={"day": holiday.day.isoformat(), "name": holiday.name},
    )
    db.session.delete(holiday)
    db.session.flush()


def upcoming_national_holidays(limit: int = 6, today: date | None = None) -> list[Holiday]:
    """Próximos feriados nacionais (informativo na tela)."""
    today = today or date.today()
    return list(
        db.session.execute(
            select(Holiday).where(Holiday.company_id.is_(None), Holiday.day >= today).order_by(Holiday.day).limit(limit)
        ).scalars()
    )
