"""CPF e CNPJ: normalização e dígitos verificadores (sem Flask nem banco).

Usado no formulário (mensagem no campo) e de novo no serviço (``service.BillingInfo``),
então um caminho que pule o formulário também é recusado.
"""

from __future__ import annotations

import re

_NON_DIGIT = re.compile(r"\D")


def only_digits(value: str | None) -> str:
    return _NON_DIGIT.sub("", value or "")


def _cpf_digit(digits: str, weight_start: int) -> int:
    total = sum(int(d) * w for d, w in zip(digits, range(weight_start, 1, -1)))
    rest = total % 11
    return 0 if rest < 2 else 11 - rest


def is_valid_cpf(value: str | None) -> bool:
    d = only_digits(value)
    if len(d) != 11 or d == d[0] * 11:
        return False
    return _cpf_digit(d[:9], 10) == int(d[9]) and _cpf_digit(d[:10], 11) == int(d[10])


_CNPJ_W1 = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_CNPJ_W2 = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def _cnpj_digit(digits: str, weights: tuple[int, ...]) -> int:
    rest = sum(int(d) * w for d, w in zip(digits, weights)) % 11
    return 0 if rest < 2 else 11 - rest


def is_valid_cnpj(value: str | None) -> bool:
    d = only_digits(value)
    if len(d) != 14 or d == d[0] * 14:
        return False
    return _cnpj_digit(d[:12], _CNPJ_W1) == int(d[12]) and _cnpj_digit(d[:13], _CNPJ_W2) == int(d[13])


def is_valid_document(value: str | None) -> bool:
    """CPF (11 dígitos) ou CNPJ (14 dígitos) com dígitos verificadores corretos."""
    d = only_digits(value)
    if len(d) == 11:
        return is_valid_cpf(d)
    if len(d) == 14:
        return is_valid_cnpj(d)
    return False


def mask_document(value: str | None) -> str:
    """Só os 2 últimos dígitos (para tela/log; CPF é dado pessoal)."""
    d = only_digits(value)
    return ("•" * (len(d) - 2) + d[-2:]) if len(d) > 2 else ""
