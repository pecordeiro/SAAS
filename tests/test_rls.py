"""RLS (ADR-0003): a segunda barreira, conferida com um papel NÃO superusuário.

Só roda com TEST_DATABASE_URL em PostgreSQL. O teste cria um papel de login comum
(sem SUPERUSER e sem BYPASSRLS — para esses o RLS não vale), dá a ele só DML nas tabelas,
liga ENABLE + FORCE ROW LEVEL SECURITY (`app.rls.enable`, o mesmo de `flask rls enable`)
e conecta por ele. Os dados são criados antes, pelo papel dono (fixture `tenants`).
"""

from __future__ import annotations

import secrets
import uuid
from datetime import date

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from app import create_app, rls
from app.extensions import db
from app.models import Activity, Holiday, Membership, ProgressEntry, Project
from tests.conftest import login, post, requires_postgres, get_test_database_url
from tests.test_isolation import ROUTES

pytestmark = requires_postgres

ROLE = "controle_app_rls_test"


def _drop_role(conn) -> None:
    exists = conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname = :r"), {"r": ROLE}).first()
    if exists:
        conn.execute(text(f"DROP OWNED BY {ROLE}"))
        conn.execute(text(f"DROP ROLE {ROLE}"))


@pytest.fixture()
def rls_url(app):
    """Papel comum com DML nas tabelas + RLS ligado e forçado. Devolve a URL desse papel."""
    password = secrets.token_hex(16)
    with app.app_context():
        with db.engine.begin() as conn:
            _drop_role(conn)
            conn.execute(text(f"CREATE ROLE {ROLE} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD '{password}'"))
            conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {ROLE}"))
            conn.execute(text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {ROLE}"))
            rls.enable(conn)
    url = make_url(get_test_database_url()).set(username=ROLE, password=password)
    yield url.render_as_string(hide_password=False)
    with app.app_context():
        with db.engine.begin() as conn:
            rls.disable(conn)
            _drop_role(conn)


@pytest.fixture()
def raw(rls_url):
    engine = create_engine(rls_url)
    yield engine
    engine.dispose()


@pytest.fixture()
def rls_app(rls_url):
    """O app inteiro rodando como o papel comum, com RLS_ENABLED=1."""
    app = create_app("test", {"SQLALCHEMY_DATABASE_URI": rls_url, "RLS_ENABLED": True})
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


def _set(conn, company=None, user=None):
    conn.execute(
        text("SELECT set_config('app.company_id', :c, true), set_config('app.user_id', :u, true)"),
        {"c": str(company or ""), "u": str(user or "")},
    )


def test_papel_do_teste_nao_e_superusuario(raw):
    with raw.connect() as conn:
        superuser, bypass = conn.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
        ).one()
    assert (superuser, bypass) == (False, False)


@pytest.mark.parametrize("table", rls.RLS_TABLES)
def test_consulta_crua_sem_empresa_retorna_zero_linhas(raw, tenants, table):
    with raw.connect() as conn:
        assert conn.execute(text(f'SELECT count(*) FROM "{table}" WHERE company_id IS NOT NULL')).scalar() == 0


def test_com_empresa_a_so_ve_linhas_de_a(raw, tenants):
    a, b = tenants
    with raw.begin() as conn:
        _set(conn, company=a.company_id)
        for table in ("projects", "stages", "activities", "memberships"):
            ids = set(conn.execute(text(f'SELECT DISTINCT company_id FROM "{table}"')).scalars())
            assert ids == {a.company_id}, table
        # Nem pedindo explicitamente pelo id de B.
        assert conn.execute(text("SELECT count(*) FROM projects WHERE id = :id"), {"id": b.project_id}).scalar() == 0
    with raw.begin() as conn:
        _set(conn, company=b.company_id)
        assert set(conn.execute(text("SELECT company_id FROM projects")).scalars()) == {b.company_id}


def test_set_local_some_no_fim_da_transacao(raw, tenants):
    a, _ = tenants
    with raw.connect() as conn:
        with conn.begin():
            _set(conn, company=a.company_id)
            assert conn.execute(text("SELECT count(*) FROM projects")).scalar() == 1
        # Mesma conexão, transação nova: sem empresa de novo (o pool não herda contexto).
        with conn.begin():
            assert conn.execute(text("SELECT count(*) FROM projects")).scalar() == 0


def test_nao_grava_nem_altera_linha_de_outra_empresa(raw, tenants):
    a, b = tenants
    with raw.connect() as conn:
        trans = conn.begin()
        _set(conn, company=a.company_id)
        with pytest.raises(DBAPIError, match="row-level security"):
            conn.execute(
                text("INSERT INTO projects (id, company_id, name, quantity, people, hours_per_day, status, created_at) "
                     "VALUES (:id, :c, 'Invasor', 1, 1, 8, 'active', now())"),
                {"id": uuid.uuid4(), "c": b.company_id},
            )
        trans.rollback()
    with raw.begin() as conn:
        _set(conn, company=a.company_id)
        changed = conn.execute(text("UPDATE activities SET units_done = 5 WHERE id = :id"), {"id": b.activity_id})
        assert changed.rowcount == 0
        deleted = conn.execute(text("DELETE FROM progress_entries WHERE company_id = :c"), {"c": b.company_id})
        assert deleted.rowcount == 0


def test_usuario_le_os_proprios_vinculos_sem_empresa(raw, tenants):
    a, _ = tenants
    with raw.begin() as conn:
        _set(conn, user=a.owner_id)
        rows = conn.execute(text("SELECT user_id, company_id FROM memberships")).all()
        assert rows == [(a.owner_id, a.company_id)]


def test_feriado_nacional_visivel_e_feriado_de_outra_empresa_nao(app, raw, tenants):
    a, b = tenants
    with app.app_context():
        db.session.add_all(
            [
                Holiday(company_id=None, day=date(2026, 12, 25), name="Natal"),
                Holiday(company_id=b.company_id, day=date(2026, 12, 24), name="Recesso B"),
            ]
        )
        db.session.commit()
    with raw.begin() as conn:
        _set(conn, company=a.company_id)
        names = set(conn.execute(text("SELECT name FROM holidays")).scalars())
        assert names == {"Natal"}
        # Empresa não grava feriado "nacional" (company_id NULL) nem altera o nacional.
        assert conn.execute(text("UPDATE holidays SET name = 'x' WHERE company_id IS NULL")).rowcount == 0


def test_orm_sem_filtro_ainda_fica_na_empresa_do_contexto(rls_app, tenants):
    """Simula o esquecimento do `scoped()`: a consulta sem filtro só enxerga a empresa A."""
    a, _ = tenants
    with rls_app.app_context():
        rls.set_context(company_id=a.company_id)
        projects = db.session.execute(select(Project)).scalars().all()
        assert [p.company_id for p in projects] == [a.company_id]
        db.session.commit()  # transação nova: o hook after_begin reaplica a empresa
        assert db.session.query(Activity).count() == 2


def test_orm_sem_contexto_nao_ve_nada(rls_app, tenants):
    with rls_app.app_context():
        assert db.session.query(Project).count() == 0
        assert db.session.query(Membership).count() == 0


@pytest.mark.parametrize("method,template,field,data", ROUTES)
def test_isolamento_ab_com_rls_ligado(rls_app, tenants, method, template, field, data):
    a, b = tenants
    client = rls_app.test_client()
    assert login(client, rls_app, a.owner_email).status_code == 302
    call = (lambda url: client.get(url)) if method == "GET" else (lambda url: post(client, rls_app, url, data))
    assert call(template.format(id=getattr(b, field))).status_code == 404
    assert call(template.format(id=getattr(a, field))).status_code in (200, 302, 303)


def test_fluxo_completo_com_rls_ligado(app, rls_app, tenants):
    a, b = tenants
    client = rls_app.test_client()
    login(client, rls_app, a.operator_email)
    page = client.get("/app/projetos").get_data(as_text=True)
    assert "Projeto A" in page and "Projeto B" not in page
    url = f"/app/atividades/{a.activity_id}/registrar"
    assert post(client, rls_app, url, {"delta": 2, "version": 1}).status_code == 303
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).units_done == 2
        assert db.session.query(ProgressEntry).filter_by(company_id=a.company_id).count() == 1
        assert db.session.query(ProgressEntry).filter_by(company_id=b.company_id).count() == 0


def test_cadastro_com_rls_ligado(app, rls_app):
    client = rls_app.test_client()
    response = post(
        client,
        rls_app,
        "/cadastro",
        {
            "company_name": "Nova",
            "name": "Ana",
            "email": "ana@exemplo.com",
            "password": "senha-forte-123",
            "password_confirm": "senha-forte-123",
        },
    )
    assert response.status_code == 302
    assert client.get("/app/projetos").status_code == 200
    with app.app_context():
        assert db.session.query(Membership).count() == 1
