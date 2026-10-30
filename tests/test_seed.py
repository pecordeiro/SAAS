"""flask seed-demo: 2 empresas fictícias, 2 projetos (10 e 4 equipamentos) cada, com 3–6
etapas genéricas vindas de um modelo e histórico."""

from __future__ import annotations

from app.extensions import db
from app.models import Activity, Company, ProgressEntry, Project, Stage


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
        assert len(projects) == 4
        assert sorted(p.quantity for p in projects) == [4, 4, 10, 10]
        for project in projects:
            stages = db.session.query(Stage).filter_by(project_id=project.id).count()
            assert 3 <= stages <= 6
        for activity in db.session.query(Activity).all():
            soma = sum(e.delta for e in db.session.query(ProgressEntry).filter_by(activity_id=activity.id))
            assert soma == activity.units_done <= activity.stage.project.quantity
        assert db.session.query(ProgressEntry).count() > 20
        nomes = " ".join(s.name for s in db.session.query(Stage).all()).lower()
        assert "sobot" not in nomes and "robô" not in nomes  # D15: só etapas genéricas
