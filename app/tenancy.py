"""Isolamento multiempresa num único lugar.

- A empresa ativa vem SÓ de ``session["company_id"]`` (nunca de formulário, URL ou header).
- ``load_company`` roda antes de cada requisição e confere se o usuário tem vínculo ativo
  com essa empresa; senão a empresa é descartada.
- Consultas a dado de cliente passam por ``scoped(Model)`` ou ``get_or_404(Model, id)``,
  que filtram por ``g.company.id``. Recurso de outra empresa responde 404 (não 403), para
  não revelar que ele existe.
"""

from __future__ import annotations

import uuid
from functools import wraps
from typing import Any, Callable, TypeVar

from flask import abort, g, request, session
from flask_login import current_user
from sqlalchemy import Select, select

from app import rls
from app.extensions import db, login_manager
from app.models import ROLE_LEVEL, ROLE_OPERATOR, Company, Membership

SESSION_KEY = "company_id"

T = TypeVar("T")


def load_company() -> None:
    """before_request: põe a empresa ativa em ``g.company`` e o vínculo em ``g.membership``."""
    g.company = None
    g.membership = None
    rls.set_context(company_id=None, user_id=None)
    if not current_user.is_authenticated:
        return
    # Antes de validar o vínculo, o RLS só deixa ler os vínculos do próprio usuário.
    rls.set_context(user_id=current_user.id)
    raw = session.get(SESSION_KEY)
    if not raw:
        return
    try:
        company_id = uuid.UUID(str(raw))
    except ValueError:
        session.pop(SESSION_KEY, None)
        return
    membership = db.session.execute(
        select(Membership)
        .join(Company, Company.id == Membership.company_id)
        .where(
            Membership.company_id == company_id,
            Membership.user_id == current_user.id,
            Membership.active.is_(True),
        )
    ).scalar_one_or_none()
    if membership is None:
        session.pop(SESSION_KEY, None)
        return
    g.company = membership.company
    g.membership = membership
    rls.set_context(company_id=membership.company_id)


def set_company(membership: Membership) -> None:
    """Troca a empresa ativa (só depois de validar o vínculo)."""
    session[SESSION_KEY] = str(membership.company_id)
    g.company = membership.company
    g.membership = membership
    rls.set_context(company_id=membership.company_id)


def first_active_membership(user_id: uuid.UUID) -> Membership | None:
    """Primeiro vínculo ativo do usuário (já autenticado por quem chama)."""
    rls.set_context(user_id=user_id)
    return db.session.execute(
        select(Membership)
        .where(Membership.user_id == user_id, Membership.active.is_(True))
        .order_by(Membership.created_at)
        .limit(1)
    ).scalar_one_or_none()


SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def tenant_required(
    min_role: str = ROLE_OPERATOR, *, allow_read_only: bool = False
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Exige login, empresa ativa e papel mínimo (owner > supervisor > operator).

    Sem login → tela de login. Sem empresa válida na sessão → primeiro vínculo ativo do
    usuário (ou 403 se não houver).
    Papel insuficiente → 403.
    Escrita (método que não é GET/HEAD/OPTIONS) com a empresa em modo leitura → 402
    (``entitlements.ReadOnlyError``). ``allow_read_only=True`` libera a rota (ex.: pagar a
    assinatura, sair).
    """
    if min_role not in ROLE_LEVEL:
        raise ValueError(f"Papel desconhecido: {min_role!r}")

    def decorator(view: Callable[..., T]) -> Callable[..., T]:
        @wraps(view)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if getattr(g, "company", None) is None or getattr(g, "membership", None) is None:
                # Sessão sem empresa válida: escolhe um vínculo ativo do próprio usuário.
                membership = first_active_membership(current_user.id)
                if membership is None:
                    abort(403)
                set_company(membership)
            if not g.membership.has_role(min_role):
                abort(403)
            if not allow_read_only and request.method not in SAFE_METHODS:
                from app.services.entitlements import ensure_writable

                ensure_writable(g.company)
            return view(*args, **kwargs)

        return wrapper

    return decorator


def current_company_id() -> uuid.UUID:
    company = getattr(g, "company", None)
    if company is None:
        raise RuntimeError("Nenhuma empresa ativa: use tenant_required antes de consultar dados.")
    return company.id


def scoped(model: type[T]) -> Select:
    """``select(model)`` já filtrado pela empresa da sessão."""
    return select(model).where(model.company_id == current_company_id())  # type: ignore[attr-defined]


def is_archived(obj: Any) -> bool:
    """Arquivado ele mesmo ou por herança (atividade de etapa arquivada, etapa/atividade de
    projeto arquivado)."""
    if getattr(obj, "archived_at", None) is not None:
        return True
    stage = getattr(obj, "stage", None)
    if stage is not None and is_archived(stage):
        return True
    project = getattr(obj, "project", None)
    return project is not None and getattr(project, "archived_at", None) is not None


def get_or_404(model: type[T], obj_id: uuid.UUID | str, *, include_archived: bool = False) -> T:
    """Busca por id DENTRO da empresa da sessão; de outra empresa (ou inexistente) → 404.

    Arquivado (inclusive por herança) também responde 404, salvo ``include_archived=True``
    (histórico e exportação continuam mostrando o que foi arquivado)."""
    try:
        obj_uuid = obj_id if isinstance(obj_id, uuid.UUID) else uuid.UUID(str(obj_id))
    except ValueError:
        abort(404)
    obj = db.session.execute(scoped(model).where(model.id == obj_uuid)).scalar_one_or_none()  # type: ignore[attr-defined]
    if obj is None or (not include_archived and is_archived(obj)):
        abort(404)
    return obj
