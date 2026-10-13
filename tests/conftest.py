"""Fixtures comuns.

Banco: SQLite em memória por padrão; defina TEST_DATABASE_URL para rodar no PostgreSQL.
db.create_all() é usado SÓ aqui (testes); em qualquer outro ambiente o schema vem das
migrations Alembic.
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from decimal import Decimal

import pytest
from itsdangerous import URLSafeTimedSerializer

from app import create_app
from app.extensions import db as _db
from app.models import ROLE_OPERATOR, ROLE_OWNER, ROLE_SUPERVISOR, Company, Membership, User
from app.services import projects as svc
from app.services.passwords import hash_password

PASSWORD = "senha-de-teste-123"


@pytest.fixture()
def app():
    """App de teste. O contexto NÃO fica ativo durante o teste: cada requisição do client
    abre o seu (como em produção), então `g` e o usuário em cache não vazam entre requisições.
    Para mexer no banco dentro do teste, use `with app.app_context():`.
    """
    app = create_app("test")
    with app.app_context():
        _db.drop_all()
        _db.create_all()
    yield app
    with app.app_context():
        _db.session.remove()
        _db.drop_all()
        _db.engine.dispose()


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


def make_tenant(label: str, quantity: int = 10) -> Tenant:
    company = Company(name=f"Empresa {label}")
    _db.session.add(company)
    _db.session.flush()
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
