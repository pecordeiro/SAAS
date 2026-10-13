"""flask seed-demo: 2 empresas fictícias, projeto de 10 equipamentos com 3–6 etapas genéricas."""

from __future__ import annotations

from app.extensions import db
from app.models import Company, Project, Stage


def test_seed_demo(app, monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "senha-demo-teste")
    runner = app.test_cli_runner()
    result = runner.invoke(args=["seed-demo"])
    assert result.exit_code == 0, result.output
    assert "senha-demo-teste" not in result.output  # senha não aparece no terminal
    again = runner.invoke(args=["seed-demo"])
    assert again.exit_code == 0 and "Já existe" in again.output
    with app.app_context():
        assert db.session.query(Company).count() == 2
        projects = db.session.query(Project).all()
        assert len(projects) == 2
        for project in projects:
            assert project.quantity == 10
            stages = db.session.query(Stage).filter_by(project_id=project.id).count()
            assert 3 <= stages <= 6
        nomes = " ".join(s.name for s in db.session.query(Stage).all()).lower()
        assert "sobot" not in nomes and "robô" not in nomes  # D15: só etapas genéricas
