"""Etapa F — relatório semanal por e-mail (dono/supervisores) com XLSX, uma vez por semana."""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

from openpyxl import load_workbook

from app.extensions import db
from app.models import Activity, JobRun, ProgressEntry, User
from app.services import email, worker
from app.services.notifications import WEEKLY_SUBJECT, week_key
from tests.conftest import make_tenant

MONDAY = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)  # segunda, 9h em São Paulo


def _reports(app, to=None):
    return [m for m in email.outbox(app) if m.subject.startswith(WEEKLY_SUBJECT) and (to is None or m.to == to)]


def _with_entries(tenant):
    activity = db.session.get(Activity, tenant.activity_id)
    activity.units_done = 5
    db.session.add_all(
        [
            ProgressEntry(company_id=tenant.company_id, activity_id=activity.id, user_id=tenant.operator_id, delta=3,
                          at=MONDAY - timedelta(days=3)),
            ProgressEntry(company_id=tenant.company_id, activity_id=activity.id, user_id=tenant.operator_id, delta=2,
                          at=MONDAY - timedelta(days=2)),
            # fora da semana (há 20 dias): não conta
            ProgressEntry(company_id=tenant.company_id, activity_id=activity.id, user_id=tenant.owner_id, delta=7,
                          at=MONDAY - timedelta(days=20)),
        ]
    )
    db.session.commit()


def test_relatorio_sai_na_segunda_uma_vez_com_xlsx(app_factory):
    app = app_factory({"APP_BASE_URL": "https://app.exemplo.com.br"})
    with app.app_context():
        a, b = make_tenant("A"), make_tenant("B")
        _with_entries(a)
        result = worker.run_task(worker.TASK_WEEKLY, MONDAY)
        assert result["companies"] == 2
        sent = _reports(app)
        to_a = sorted(m.to for m in sent if "Empresa A" in m.subject)
        assert to_a == ["owner.a@exemplo.com", "supervisor.a@exemplo.com"]  # operador não recebe
        msg = next(m for m in sent if m.to == a.owner_email)
        assert "Projeto A" in msg.text and "Projeto B" not in msg.text
        assert "operator A: 5 peças em 2 registros" in msg.text
        assert "https://app.exemplo.com.br/app/projetos" in msg.text
        assert len(msg.attachments) == 1
        attachment = msg.attachments[0]
        assert attachment.filename == f"relatorio-semanal-{week_key(MONDAY.date())}.xlsx"
        wb = load_workbook(io.BytesIO(attachment.content))
        assert wb.sheetnames == ["Projetos", "Pessoas"]
        projetos = list(wb["Projetos"].iter_rows(min_row=3, values_only=True))
        assert projetos[0][0] == "Projeto A" and projetos[0][6] == 5  # peças na semana
        pessoas = list(wb["Pessoas"].iter_rows(min_row=3, values_only=True))
        assert pessoas == [("operator A", 5, 2, 0, 0.83, 2)]
        # Idempotente: mesma semana de novo não reenvia; marca em job_runs por empresa.
        count = len(_reports(app))
        assert worker.run_task(worker.TASK_WEEKLY, MONDAY + timedelta(hours=3))["companies"] == 0
        assert len(_reports(app)) == count
        assert db.session.query(JobRun).filter_by(company_id=a.company_id, job="weekly_report").count() == 1
        assert db.session.query(JobRun).filter_by(company_id=b.company_id, job="weekly_report").count() == 1


def test_fora_da_segunda_ou_antes_das_7h_nao_envia(app):
    with app.app_context():
        make_tenant("A")
        assert worker.run_task(worker.TASK_WEEKLY, MONDAY - timedelta(days=1))["companies"] == 0  # domingo
        assert worker.run_task(worker.TASK_WEEKLY, MONDAY.replace(hour=9))["companies"] == 0  # 6h local
        assert _reports(app) == [] and db.session.query(JobRun).count() == 0


def test_preferencia_desligada_nao_recebe(app):
    with app.app_context():
        a = make_tenant("A")
        db.session.query(User).filter_by(email=a.supervisor_email).one().notify_weekly = False
        db.session.commit()
        worker.run_task(worker.TASK_WEEKLY, MONDAY)
        assert [m.to for m in _reports(app)] == [a.owner_email]


def test_planilha_neutraliza_formula_em_nome_de_projeto(app):
    from app.models import Project

    with app.app_context():
        a = make_tenant("A")
        db.session.get(Project, a.project_id).name = "=HYPERLINK(\"http://x\")"
        db.session.commit()
        worker.run_task(worker.TASK_WEEKLY, MONDAY)
        content = _reports(app)[0].attachments[0].content
        wb = load_workbook(io.BytesIO(content))
        assert wb["Projetos"].cell(row=3, column=1).value.startswith("'=")
