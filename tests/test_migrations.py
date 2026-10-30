"""Migrations reversíveis e sem drift: upgrade → check → downgrade base → upgrade → check.

SQLite (arquivo temporário) sempre; PostgreSQL quando TEST_DATABASE_URL aponta para ele
(no próprio banco de teste, que termina de novo em head).
"""

from __future__ import annotations

import warnings

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from app import create_app
from app.extensions import db
from tests.conftest import downgrade_migrations, get_test_database_url, requires_postgres, run_migrations

# SQLite não reflete o índice de expressão lower(email): o SQLAlchemy/Alembic só avisam.
pytestmark = pytest.mark.filterwarnings("ignore:Skipped unsupported reflection of expression-based index")


def _diff(app) -> list:
    with app.app_context(), db.engine.connect() as conn:
        context = MigrationContext.configure(conn, opts={"compare_type": True})
        with warnings.catch_warnings():
            # SQLite não reflete índice de expressão (lower(email)); o Alembic só avisa.
            warnings.simplefilter("ignore")
            return compare_metadata(context, db.metadata)


def _tables(app) -> set[str]:
    with app.app_context(), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return set(inspect(db.engine).get_table_names())


def _roundtrip(app) -> None:
    run_migrations(app)
    assert _diff(app) == []
    expected = {t.name for t in db.metadata.sorted_tables}
    assert expected <= _tables(app)
    downgrade_migrations(app, "base")
    assert _tables(app) <= {"alembic_version"}
    run_migrations(app)
    assert _diff(app) == []
    assert expected <= _tables(app)


def test_migrations_ida_e_volta_sqlite(tmp_path):
    app = create_app("test", {"SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'm.db'}"})
    try:
        _roundtrip(app)
    finally:
        with app.app_context():
            db.engine.dispose()


@requires_postgres
def test_migrations_ida_e_volta_postgres(_postgres_schema):
    app = create_app("test", {"SQLALCHEMY_DATABASE_URI": get_test_database_url()})
    try:
        _roundtrip(app)
    finally:
        with app.app_context():
            db.engine.dispose()
