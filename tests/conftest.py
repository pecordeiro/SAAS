"""Fixtures comuns.

Banco:
- PostgreSQL (recomendado, igual à produção): defina TEST_DATABASE_URL. O schema vem das
  MIGRATIONS (upgrade uma vez por sessão de testes, num schema public recriado do zero) e
  cada teste começa com as tabelas esvaziadas (TRUNCATE), mantendo o seed de planos da
  migration. Por segurança, o nome do banco precisa conter "test".
- SQLite em memória (atalho rápido, sem TEST_DATABASE_URL): db.create_all() por teste +
  `seed_plans()`. create_all é usado SÓ aqui; fora dos testes o schema vem das migrations.
"""

from __future__ import annotations

import os
import re
import secrets
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import pytest
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app import create_app
from app.config import _database_url_raw
from app.extensions import db as _db
from app.models import ROLE_OPERATOR, ROLE_OWNER, ROLE_SUPERVISOR, Company, Membership, User
from app.services import projects as svc
from app.services.passwords import hash_password
from app.services.plans import seed_plans

PASSWORD = "senha-de-teste-123"
MIGRATIONS_DIR = str(Path(__file__).resolve().parent.parent / "migrations")
# Tabelas que o TRUNCATE entre testes preserva (seed da migration).
KEEP_TABLES = {"alembic_version", "plans"}


def get_test_database_url() -> str | None:
    return _database_url_raw(os.environ.get("TEST_DATABASE_URL") or None)


def using_postgres() -> bool:
    url = get_test_database_url()
    return bool(url) and make_url(url).get_backend_name() == "postgresql"


requires_postgres = pytest.mark.skipif(not using_postgres(), reason="precisa de TEST_DATABASE_URL (PostgreSQL)")


def run_migrations(app, revision: str = "head") -> None:
    from flask_migrate import upgrade

    with app.app_context():
        upgrade(directory=MIGRATIONS_DIR, revision=revision)


def downgrade_migrations(app, revision: str = "base") -> None:
    from flask_migrate import downgrade

    with app.app_context():
        downgrade(directory=MIGRATIONS_DIR, revision=revision)


@pytest.fixture(scope="session")
def _postgres_schema():
    """Recria o schema public do banco de TESTE e aplica as migrations (uma vez)."""
    if not using_postgres():
        yield None
        return
    database = make_url(get_test_database_url()).database or ""
    if "test" not in database:
        pytest.exit(f"TEST_DATABASE_URL deve apontar para um banco de teste (nome com 'test'), não {database!r}.")
    app = create_app("test")
    with app.app_context():
        with _db.engine.begin() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
        _db.engine.dispose()
    run_migrations(app)
    yield app
    with app.app_context():
        _db.engine.dispose()


def truncate_all() -> None:
    tables = _db.session.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = current_schema()")
    ).scalars()
    names = ", ".join(f'"{t}"' for t in tables if t not in KEEP_TABLES)
    if names:
        _db.session.execute(text(f"TRUNCATE {names} CASCADE"))
    _db.session.commit()


def _resync_plans() -> None:
    """``plans`` sobrevive ao TRUNCATE (semeada pela migration): volta ao catálogo antes de
    cada teste — um teste que mexe em preço/limite/feature de plano (ou cria um plano extra)
    não vaza para o próximo. Assinaturas já foram truncadas, então nada referencia os extras."""
    from app.models import Plan
    from app.services.plans import PLAN_CATALOG

    _db.session.execute(Plan.__table__.delete().where(Plan.code.notin_([spec.code for spec in PLAN_CATALOG])))
    seed_plans()
    _db.session.commit()


def _prepare_db(app) -> None:
    with app.app_context():
        if using_postgres():
            truncate_all()
            _resync_plans()
        else:
            _db.drop_all()
            _db.create_all()
            seed_plans()
            _db.session.commit()


def _cleanup_db(app) -> None:
    with app.app_context():
        _db.session.remove()
        if not using_postgres():
            _db.drop_all()
        _db.engine.dispose()


@pytest.fixture()
def app_factory(_postgres_schema, tmp_path_factory):
    """Cria apps de teste com overrides de config, banco limpo e limpeza no fim.

    Etapa G: cada app grava fotos (backend ``local``) numa pasta temporária própria — nunca em
    ``instance/`` do repositório."""
    created = []

    def factory(overrides: dict | None = None):
        overrides = {"STORAGE_LOCAL_DIR": str(tmp_path_factory.mktemp("storage")), **(overrides or {})}
        new_app = create_app("test", overrides)
        _prepare_db(new_app)
        created.append(new_app)
        return new_app

    yield factory
    for created_app in created:
        _cleanup_db(created_app)


@pytest.fixture()
def app(app_factory):
    """App de teste. O contexto NÃO fica ativo durante o teste: cada requisição do client
    abre o seu (como em produção), então `g` e o usuário em cache não vazam entre requisições.
    Para mexer no banco dentro do teste, use `with app.app_context():`.
    """
    return app_factory()


@pytest.fixture()
def client(app):
    return app.test_client()


def csrf_token(client, app) -> str:
    """Token CSRF válido para a sessão do client (mesmo esquema do Flask-WTF)."""
    with client.session_transaction() as sess:
        raw = sess.get("csrf_token")
        if not raw:
            raw = secrets.token_hex(20)
            sess["csrf_token"] = raw
    return URLSafeTimedSerializer(app.secret_key, salt="wtf-csrf-token").dumps(raw)


def post(client, app, url, data=None, **kwargs):
    payload = dict(data or {})
    payload["csrf_token"] = csrf_token(client, app)
    return client.post(url, data=payload, **kwargs)


def login(client, app, email, password=PASSWORD):
    return post(client, app, "/entrar", {"email": email, "password": password})


@dataclass
class Tenant:
    company_id: object
    owner_id: object
    owner_email: str
    supervisor_email: str
    operator_id: object
    operator_email: str
    project_id: object
    stage_id: object
    activity_id: object


ALL_MODULES = object()  # marcador: liga todos os módulos opcionais (padrão de make_tenant)


def set_tenant_modules(company_id, modules) -> None:
    """Grava direto o estado dos módulos opcionais (R6) da empresa, sem auditoria: ``modules`` é a
    lista de chaves ligadas (as demais ficam desligadas). Para testar a TELA de módulos use a rota."""
    from app.models import CompanyModule
    from app.services.modules import KEYS

    wanted = set(KEYS if modules is ALL_MODULES else modules)
    _db.session.execute(CompanyModule.__table__.delete().where(CompanyModule.company_id == company_id))
    for key in KEYS:
        if key in wanted:
            _db.session.add(CompanyModule(company_id=company_id, module=key, enabled=True))
    _db.session.flush()


def make_tenant(label: str, quantity: int = 10, plan: str | None = None, modules=ALL_MODULES) -> Tenant:
    """Empresa com 3 pessoas (owner, supervisor, operador) e 1 projeto. Sem ``plan``: sem
    assinatura (teste grátis implícito no plano de teste). Com ``plan``: assinatura ativa
    (paga) nesse plano — ex.: ``plan="empresa"`` para ter a feature ``api``.

    R6: por padrão TODOS os módulos opcionais vêm ligados (empresa “existente”, que já usa os
    recursos — os testes antigos de cada módulo continuam valendo). ``modules=()`` = empresa só
    com o núcleo; ``modules=("fotos",)`` = só esse ligado."""
    company = Company(name=f"Empresa {label}")
    _db.session.add(company)
    _db.session.flush()
    set_tenant_modules(company.id, modules)
    users = {}
    for role in (ROLE_OWNER, ROLE_SUPERVISOR, ROLE_OPERATOR):
        user = User(email=f"{role}.{label.lower()}@exemplo.com", name=f"{role} {label}", password_hash=hash_password(PASSWORD))
        _db.session.add(user)
        _db.session.flush()
        _db.session.add(Membership(company_id=company.id, user_id=user.id, role=role))
        users[role] = user
    project = svc.create_project(
        company,
        name=f"Projeto {label}",
        quantity=quantity,
        start_date=None,
        due_date=None,
        people=1,
        hours_per_day=Decimal("8"),
        stages=[
            svc.NewStage(
                name="Etapa 1",
                activities=[
                    svc.NewActivity(name="Atividade 1", ideal_minutes=Decimal("10")),
                    svc.NewActivity(name="Atividade 2", ideal_minutes=Decimal("30")),
                ],
            )
        ],
    )
    if plan is not None:
        from app.models import Subscription
        from app.services.plans import get_plan

        _db.session.add(Subscription(company_id=company.id, plan_id=get_plan(plan).id, provider="fake", status="active"))
    _db.session.commit()
    stage = project.stages[0]
    activity = stage.activities[0]
    return Tenant(
        company_id=company.id,
        owner_id=users[ROLE_OWNER].id,
        owner_email=users[ROLE_OWNER].email,
        supervisor_email=users[ROLE_SUPERVISOR].email,
        operator_id=users[ROLE_OPERATOR].id,
        operator_email=users[ROLE_OPERATOR].email,
        project_id=project.id,
        stage_id=stage.id,
        activity_id=activity.id,
    )


@pytest.fixture()
def tenants(app):
    with app.app_context():
        return make_tenant("A"), make_tenant("B")


def text_of(response) -> str:
    return re.sub(r"\s+", " ", response.get_data(as_text=True))
