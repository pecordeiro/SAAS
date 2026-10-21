"""R8 — restaurar o projeto para uma data e hora (servidor): serviço e rotas.

Casos A/B das rotas novas ficam em tests/test_isolation.py (bloco R8)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from flask import g
from sqlalchemy import select

from app.extensions import db
from app.models import Activity, AuditLog, Company, DomainEvent, Project, ProgressEntry, User
from app.services import audit, calc, events
from app.services import projects as svc
from app.services import restore as rsvc
from tests.conftest import login, make_tenant, post, text_of

TZ = "America/Sao_Paulo"


def backdate(entry: ProgressEntry, at: datetime) -> None:
    """Muda a hora de um lançamento (só em teste: UPDATE direto, fora do ORM append-only)."""
    db.session.execute(ProgressEntry.__table__.update().where(ProgressEntry.__table__.c.id == entry.id).values(at=at))
    db.session.commit()
    db.session.expire_all()


def _register(activity_id, delta, user_id, at):
    activity = db.session.get(Activity, activity_id)
    entry = svc.register_progress(activity, delta, None, user_id)
    db.session.commit()
    backdate(entry, at)
    return entry


@pytest.fixture()
def ctx(app):
    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "203.0.113.9"}):
        tenant = make_tenant("A")
        g.company = db.session.get(Company, tenant.company_id)
        owner = db.session.get(User, tenant.owner_id)
        yield g.company, owner, tenant


@pytest.fixture()
def scenario(ctx):
    """Projeto A (10 previstas, 2 atividades): +2 (−3h), +3 (−2h), +1 (−1h) na 1; +4 (−90min) na 2."""
    company, owner, tenant = ctx
    project = db.session.get(Project, tenant.project_id)
    a1, a2 = project.stages[0].activities
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    _register(a1.id, 2, owner.id, now - timedelta(hours=3))
    _register(a1.id, 3, owner.id, now - timedelta(hours=2))
    _register(a1.id, 1, owner.id, now - timedelta(hours=1))
    _register(a2.id, 4, owner.id, now - timedelta(minutes=90))
    return company, owner, db.session.get(Project, project.id), now


def _units(project_id):
    db.session.expire_all()
    project = db.session.get(Project, project_id)
    return [a.units_done for a in project.stages[0].activities]


def _entries(company_id):
    return db.session.query(ProgressEntry).filter_by(company_id=company_id).count()


# ---------------------------------------------------------------- calc e fuso


def test_calc_pecas_no_instante():
    assert calc.pecas_no_instante(6, [3, 1], 10) == 2
    assert calc.pecas_no_instante(6, [], 10) == 6
    assert calc.pecas_no_instante(2, [-4], 10) == 6  # desfazer depois do instante conta com o sinal
    assert calc.pecas_no_instante(1, [3], 10) == 0  # nunca abaixo de 0
    assert calc.pecas_no_instante(9, [-5], 10) == 10  # nunca acima das previstas de agora


def test_data_digitada_e_local_sao_paulo():
    at = rsvc.parse_local("2026-10-21T10:30", TZ)
    assert at == datetime(2026, 10, 21, 13, 30, tzinfo=timezone.utc)
    assert rsvc.format_local(at, TZ) == "2026-10-21T10:30"
    assert rsvc.parse_local("21/10/2026 10:30", TZ) is None
    assert rsvc.parse_local("", TZ) is None
    assert rsvc.parse_local("2026-10-21T10:30", "Fuso/Invalido") == at  # cai no padrão


# ---------------------------------------------------------------- prévia e aplicar


def test_restaurar_para_antes_de_n_lancamentos(scenario):
    company, owner, project, now = scenario
    before_entries = _entries(company.id)
    at = now - timedelta(hours=2, minutes=30)  # depois do +2, antes do +3, +1 e +4
    preview = rsvc.restore_preview(project, at)
    diffs = {d.activity.name: (d.current, d.target) for d in preview.stages[0].activities}
    assert diffs == {"Atividade 1": (6, 2), "Atividade 2": (4, 0)}
    assert len(preview.changes) == 2
    # resumo antes/depois via calc.py
    assert preview.before == svc.summary(project)
    assert preview.after.progresso_geral < preview.before.progresso_geral
    assert preview.stages[0].after.progresso < preview.stages[0].before.progresso

    result = rsvc.restore_apply(project, at, owner.id, preview.token, tz_name=TZ)
    db.session.commit()
    assert _units(project.id) == [2, 0]
    # compensatórios: nada apagado, um lançamento por atividade, todos com o vínculo
    assert _entries(company.id) == before_entries + 2
    assert sorted(e.delta for e in result.entries) == [-4, -4]
    assert {e.restore_id for e in result.entries} == {result.restore_id}
    assert all(e.restore_undoes_id is None and e.user_id == owner.id for e in result.entries)
    log = db.session.execute(select(AuditLog).where(AuditLog.action == audit.PROJECT_RESTORED)).scalar_one()
    assert log.actor_user_id == owner.id and log.object_id == project.id and log.ip == "203.0.113.9"
    assert log.details["lancamentos"] == 2 and log.details["restore_id"] == str(result.restore_id)
    assert log.details["ate"] == rsvc.format_local(at, TZ)
    progress_events = [
        e for e in db.session.query(DomainEvent).filter_by(company_id=company.id, type=events.ACTIVITY_PROGRESS_UPDATED)
        if e.payload["delta"] == -4
    ]
    assert len(progress_events) == 2
    # a mesma prévia agora não tem mais nada a mudar
    assert not rsvc.restore_preview(db.session.get(Project, project.id), at).changed


def test_restaurar_para_o_futuro_nao_muda_nada(scenario):
    company, owner, project, now = scenario
    before = _entries(company.id)
    preview = rsvc.restore_preview(project, now + timedelta(days=1))
    assert not preview.changed and preview.after == preview.before
    with pytest.raises(rsvc.NothingToRestore):
        rsvc.restore_apply(project, now + timedelta(days=1), owner.id, preview.token)
    db.session.rollback()
    assert _units(project.id) == [6, 4] and _entries(company.id) == before


def test_restaurar_para_antes_de_tudo_zera(scenario):
    company, owner, project, now = scenario
    preview = rsvc.restore_preview(project, now - timedelta(days=1))
    rsvc.restore_apply(project, now - timedelta(days=1), owner.id, preview.token)
    db.session.commit()
    assert _units(project.id) == [0, 0]


def test_concorrencia_registro_entre_previa_e_confirmacao_da_409(scenario):
    company, owner, project, now = scenario
    at = now - timedelta(hours=2, minutes=30)
    preview = rsvc.restore_preview(project, at)
    svc.register_progress(db.session.get(Activity, project.stages[0].activities[0].id), 1, None, owner.id)
    db.session.commit()
    before = _entries(company.id)
    with pytest.raises(rsvc.RestoreConflict):
        rsvc.restore_apply(db.session.get(Project, project.id), at, owner.id, preview.token)
    db.session.rollback()
    assert _units(project.id) == [7, 4] and _entries(company.id) == before
    # token vazio ou inventado também é conflito
    with pytest.raises(rsvc.RestoreConflict):
        rsvc.restore_apply(db.session.get(Project, project.id), at, owner.id, "")
    db.session.rollback()


def test_concorrencia_versao_mudou_no_banco_depois_da_leitura(scenario):
    """Token confere com o que a sessão leu, mas a linha mudou no banco: o UPDATE condicional recusa."""
    company, owner, project, now = scenario
    at = now - timedelta(hours=2, minutes=30)
    preview = rsvc.restore_preview(project, at)
    activity = project.stages[0].activities[0]
    db.session.execute(
        Activity.__table__.update().where(Activity.__table__.c.id == activity.id).values(version=activity.version + 5)
    )
    before = _entries(company.id)
    with pytest.raises(rsvc.RestoreConflict):
        rsvc.restore_apply(project, at, owner.id, preview.token)
    db.session.rollback()
    assert _entries(company.id) == before
    assert db.session.query(AuditLog).filter_by(action=audit.PROJECT_RESTORED).count() == 0


def test_desfazer_a_restauracao(scenario):
    company, owner, project, now = scenario
    at = now - timedelta(hours=2, minutes=30)
    preview = rsvc.restore_preview(project, at)
    restored = rsvc.restore_apply(project, at, owner.id, preview.token)
    db.session.commit()
    project = db.session.get(Project, project.id)
    # lançamento de restauração não sai sozinho pelo desfazer de registro
    with pytest.raises(svc.ProgressError):
        svc.undo_progress(restored.entries[0], owner.id)
    undo = rsvc.restore_undo(project, restored.restore_id, owner.id)
    db.session.commit()
    assert _units(project.id) == [6, 4]
    assert sorted(e.delta for e in undo.entries) == [4, 4]
    assert all(e.restore_undoes_id == restored.restore_id and e.restore_id == undo.restore_id for e in undo.entries)
    assert rsvc.is_restore_undone(project, restored.restore_id)
    log = db.session.execute(select(AuditLog).where(AuditLog.action == audit.PROJECT_RESTORE_UNDONE)).scalar_one()
    assert log.details["restore_id"] == str(restored.restore_id) and log.details["lancamentos"] == 2
    records = rsvc.restorations(project)
    assert [(r.restore_id, r.undone, r.entries) for r in records] == [(restored.restore_id, True, 2)]
    # uma vez só; e não se desfaz um desfazer
    with pytest.raises(rsvc.RestoreError):
        rsvc.restore_undo(project, restored.restore_id, owner.id)
    with pytest.raises(rsvc.RestoreError):
        rsvc.restore_undo(project, undo.restore_id, owner.id)
    with pytest.raises(rsvc.RestoreNotFound):
        rsvc.restore_undo(project, __import__("uuid").uuid4(), owner.id)
    # histórico inteiro preservado: 4 registros + 2 da restauração + 2 do desfazer
    assert _entries(company.id) == 8


def test_desfazer_restauracao_recusa_se_estouraria_os_limites(scenario):
    company, owner, project, now = scenario
    at = now - timedelta(days=1)
    preview = rsvc.restore_preview(project, at)
    restored = rsvc.restore_apply(project, at, owner.id, preview.token)  # 6→0 e 4→0
    db.session.commit()
    # depois da restauração, alguém registra 9 na atividade 1: desfazer daria 9 + 6 > 10
    svc.register_progress(db.session.get(Activity, project.stages[0].activities[0].id), 9, None, owner.id)
    db.session.commit()
    with pytest.raises(rsvc.RestoreError):
        rsvc.restore_undo(db.session.get(Project, project.id), restored.restore_id, owner.id)
    db.session.rollback()
    assert _units(project.id) == [9, 0]


def test_restauracao_isolada_por_empresa(scenario):
    company, owner, project, now = scenario
    at = now - timedelta(days=1)
    restored = rsvc.restore_apply(project, at, owner.id, rsvc.restore_preview(project, at).token)
    db.session.commit()
    b = make_tenant("B")
    project_b = db.session.get(Project, b.project_id)
    # id da restauração de A não existe no projeto de B
    with pytest.raises(rsvc.RestoreNotFound):
        rsvc.restore_undo(project_b, restored.restore_id, b.owner_id)
    assert not rsvc.restore_exists(project_b, restored.restore_id)
    assert rsvc.restorations(project_b) == []
    # a prévia de B só enxerga o histórico de B
    assert not rsvc.restore_preview(project_b, at).changed


def test_projeto_arquivado_nao_restaura(scenario):
    company, owner, project, now = scenario
    at = now - timedelta(days=1)
    preview = rsvc.restore_preview(project, at)
    svc.archive_project(project, owner.id)
    db.session.commit()
    with pytest.raises(rsvc.RestoreError):
        rsvc.restore_apply(project, at, owner.id, preview.token)
    db.session.rollback()
    assert _units(project.id) == [6, 4]


def test_atividade_arquivada_fica_de_fora(scenario):
    company, owner, project, now = scenario
    a2 = project.stages[0].activities[1]
    svc.archive_activity(a2, owner.id)
    db.session.commit()
    project = db.session.get(Project, project.id)
    preview = rsvc.restore_preview(project, now - timedelta(days=1))
    assert [d.activity.name for d in preview.changes] == ["Atividade 1"]


def test_restauracao_que_conclui_o_projeto_emite_eventos(ctx):
    company, owner, tenant = ctx
    project = svc.create_project(
        company, name="P1", quantity=1, start_date=None, due_date=None, people=1, hours_per_day=Decimal("8"),
        stages=[svc.NewStage("E", [svc.NewActivity("a", Decimal("5"))])],
    )
    db.session.commit()
    activity = project.stages[0].activities[0]
    now = datetime.now(timezone.utc)
    entry = _register(activity.id, 1, owner.id, now - timedelta(hours=2))
    svc.undo_progress(db.session.get(ProgressEntry, entry.id), owner.id)
    db.session.commit()
    project = db.session.get(Project, project.id)
    assert project.status == "active"
    at = now - timedelta(hours=1)  # antes do desfazer: estava concluída
    rsvc.restore_apply(project, at, owner.id, rsvc.restore_preview(project, at).token)
    db.session.commit()
    assert db.session.get(Project, project.id).status == "done"
    kinds = [e.type for e in db.session.query(DomainEvent).filter_by(company_id=company.id)]
    assert kinds.count(events.PROJECT_COMPLETED) == 2  # o do registro original + o da restauração


# ---------------------------------------------------------------- rotas


def _local(at):
    return rsvc.format_local(at, TZ)


@pytest.fixture()
def routed(app):
    with app.app_context():
        a = make_tenant("A")
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        _register(a.activity_id, 3, a.owner_id, now - timedelta(hours=3))
        _register(a.activity_id, 2, a.owner_id, now - timedelta(hours=1))
        return a, now


def test_operador_recebe_403(client, app, routed):
    a, now = routed
    login(client, app, a.operator_email)
    assert client.get(f"/app/projetos/{a.project_id}/restaurar").status_code == 403
    ate = _local(now - timedelta(hours=2))
    assert client.get(f"/app/projetos/{a.project_id}/restaurar?ate={ate}").status_code == 403
    assert post(client, app, f"/app/projetos/{a.project_id}/restaurar", {"ate": ate, "token": "x", "confirm": "y"}).status_code == 403
    import uuid

    url = f"/app/projetos/{a.project_id}/restauracoes/{uuid.uuid4()}/desfazer"
    assert post(client, app, url, {"confirm": "y"}).status_code == 403
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).units_done == 5


def test_fluxo_previa_aplicar_e_desfazer_pela_rota(client, app, routed):
    a, now = routed
    login(client, app, a.supervisor_email)
    ate = _local(now - timedelta(hours=2))
    page = client.get(f"/app/projetos/{a.project_id}/restaurar?ate={ate}")
    assert page.status_code == 200
    html = text_of(page)
    assert "Atividade 1" in html and "(-2)" in html
    with app.app_context():
        token = rsvc.restore_preview(db.session.get(Project, a.project_id), rsvc.parse_local(ate, TZ)).token
    assert f'value="{token}"' in page.get_data(as_text=True)
    # sem confirmação: nada muda
    assert post(client, app, f"/app/projetos/{a.project_id}/restaurar", {"ate": ate, "token": token}).status_code == 303
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).units_done == 5
    response = post(client, app, f"/app/projetos/{a.project_id}/restaurar", {"ate": ate, "token": token, "confirm": "y"})
    assert response.status_code == 303
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).units_done == 3
        restore_id = db.session.query(ProgressEntry).filter(ProgressEntry.restore_id.isnot(None)).one().restore_id
    listing = text_of(client.get(f"/app/projetos/{a.project_id}/restaurar"))
    assert "Desfazer restauração" in listing
    # histórico mostra a ação de auditoria e não oferece desfazer o lançamento da restauração sozinho
    history = client.get(f"/app/projetos/{a.project_id}/historico").get_data(as_text=True)
    assert "Projeto restaurado" in history
    # mesma confirmação de novo: o estado mudou → 409 com a prévia nova
    again = post(client, app, f"/app/projetos/{a.project_id}/restaurar", {"ate": ate, "token": token, "confirm": "y"})
    assert again.status_code == 409 and "mudou depois da prévia" in text_of(again)
    undo_url = f"/app/projetos/{a.project_id}/restauracoes/{restore_id}/desfazer"
    assert post(client, app, undo_url, {}).status_code == 303  # sem confirmação
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).units_done == 3
    assert post(client, app, undo_url, {"confirm": "y"}).status_code == 303
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).units_done == 5
    assert "desfeita" in text_of(client.get(f"/app/projetos/{a.project_id}/restaurar"))
    # desfazer de novo: recusa com aviso, nada muda
    assert post(client, app, undo_url, {"confirm": "y"}).status_code == 303
    with app.app_context():
        assert db.session.query(ProgressEntry).filter_by(activity_id=a.activity_id).count() == 4


def test_data_invalida_responde_400(client, app, routed):
    a, _ = routed
    login(client, app, a.supervisor_email)
    assert client.get(f"/app/projetos/{a.project_id}/restaurar?ate=ontem").status_code == 400
    response = post(client, app, f"/app/projetos/{a.project_id}/restaurar", {"ate": "ontem", "token": "x", "confirm": "y"})
    assert response.status_code == 400


def test_futuro_pela_rota_nao_grava(client, app, routed):
    a, now = routed
    login(client, app, a.supervisor_email)
    ate = _local(now + timedelta(days=2))
    assert "Nada a restaurar" in text_of(client.get(f"/app/projetos/{a.project_id}/restaurar?ate={ate}"))
    with app.app_context():
        token = rsvc.restore_preview(db.session.get(Project, a.project_id), rsvc.parse_local(ate, TZ)).token
    assert post(client, app, f"/app/projetos/{a.project_id}/restaurar", {"ate": ate, "token": token, "confirm": "y"}).status_code == 303
    with app.app_context():
        assert db.session.query(ProgressEntry).filter_by(activity_id=a.activity_id).count() == 2


def test_projeto_arquivado_pela_rota_e_404(client, app, routed):
    a, now = routed
    with app.app_context():
        svc.archive_project(db.session.get(Project, a.project_id), a.owner_id)
        db.session.commit()
    login(client, app, a.owner_email)
    ate = _local(now - timedelta(hours=2))
    assert client.get(f"/app/projetos/{a.project_id}/restaurar?ate={ate}").status_code == 404
    assert post(client, app, f"/app/projetos/{a.project_id}/restaurar", {"ate": ate, "token": "x", "confirm": "y"}).status_code == 404
