"""Fase 7 — LGPD (exportação, exclusão com carência, expurgo, retenção) e acesso de suporte."""

from __future__ import annotations

import io
import zipfile
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.extensions import db
from app.models import (
    AuditLog,
    Company,
    DomainEvent,
    LoginThrottle,
    Membership,
    PasswordReset,
    ProgressEntry,
    Project,
    User,
)
from app.models.base import utcnow
from app.models.privacy import PlatformAuditLog
from app.services import entitlements, lgpd, support
from app.services.email import outbox
from tests.conftest import PASSWORD, login, make_tenant, post, text_of


def _zip(response) -> dict[str, str]:
    with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
        return {name: zf.read(name).decode("utf-8") for name in zf.namelist()}


# ---------------------------------------------------------------- exportação


def test_exportacao_zip_tem_todas_as_tabelas_sem_segredos(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    response = post(client, app, "/app/privacidade/exportar")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Content-Disposition"].startswith('attachment; filename="dados-empresa-')
    files = _zip(response)
    for name in ("empresa.csv", "usuarios.csv", "projects.csv", "stages.csv", "activities.csv", "memberships.csv", "audit_logs.csv", "LEIA-ME.txt"):
        assert name in files
    everything = "".join(files.values())
    assert "password_hash" not in everything and "$argon2" not in everything
    assert "token_hash" not in everything and "totp_secret_enc" not in everything
    with app.app_context():
        actions = db.session.execute(select(AuditLog.action).where(AuditLog.company_id == a.company_id)).scalars().all()
        assert lgpd.DATA_EXPORTED in actions


def test_exportacao_neutraliza_formula(app, tenants):
    a, _ = tenants
    with app.app_context():
        project = db.session.get(Project, a.project_id)
        project.name = "=HYPERLINK(\"http://x\")"
        db.session.commit()
        data, _ = lgpd.export_company(db.session.get(Company, a.company_id))
    files = {n: zipfile.ZipFile(io.BytesIO(data)).read(n).decode() for n in zipfile.ZipFile(io.BytesIO(data)).namelist()}
    assert "'=HYPERLINK" in files["projects.csv"]


def test_exportacao_so_proprietario(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    assert post(client, app, "/app/privacidade/exportar").status_code == 403
    assert post(client, app, "/app/privacidade/excluir", {"company_name": "Empresa A", "password": PASSWORD}).status_code == 403


def test_exportacao_sem_csrf_400(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    assert client.post("/app/privacidade/exportar").status_code == 400


# ---------------------------------------------------------------- exclusão com carência


def test_pedir_exclusao_exige_senha_e_nome_e_avisa_proprietarios(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    assert post(client, app, "/app/privacidade/excluir", {"company_name": "Empresa A", "password": "errada"}).status_code == 400
    assert post(client, app, "/app/privacidade/excluir", {"company_name": "Outra", "password": PASSWORD}).status_code == 400
    with app.app_context():
        assert db.session.get(Company, a.company_id).deletion_requested_at is None
    response = post(client, app, "/app/privacidade/excluir", {"company_name": "empresa a", "password": PASSWORD})
    assert response.status_code == 303
    assert outbox(app)[-1].to == a.owner_email and "Exclusão" in outbox(app)[-1].subject
    page = text_of(client.get("/app/privacidade"))
    assert "Exclusão agendada" in page and "Cancelar a exclusão" in page
    with app.app_context():
        company = db.session.get(Company, a.company_id)
        first = company.deletion_requested_at
        assert lgpd.purge_date(company) - lgpd._aware(first) == timedelta(days=30)
    # pedir de novo não reinicia o prazo; cancelar limpa
    post(client, app, "/app/privacidade/excluir", {"company_name": "Empresa A", "password": PASSWORD})
    with app.app_context():
        assert db.session.get(Company, a.company_id).deletion_requested_at == first
    assert post(client, app, "/app/privacidade/excluir/cancelar").status_code == 303
    with app.app_context():
        assert db.session.get(Company, a.company_id).deletion_requested_at is None
        actions = set(db.session.execute(select(AuditLog.action).where(AuditLog.company_id == a.company_id)).scalars())
        assert {lgpd.DELETION_REQUESTED, lgpd.DELETION_CANCELLED} <= actions


def _request(app, company_id, days_ago: int):
    with app.app_context():
        company = db.session.get(Company, company_id)
        company.deletion_requested_at = utcnow() - timedelta(days=days_ago)
        db.session.commit()


def test_expurgo_respeita_carencia_e_e_idempotente(app, tenants):
    a, b = tenants
    _request(app, a.company_id, days_ago=10)
    with app.app_context():
        assert lgpd.purge_due(operator="teste") == []  # ainda na carência
        with pytest.raises(lgpd.LgpdError):
            lgpd.purge_company(a.company_id, operator="teste")
        with pytest.raises(lgpd.LgpdError):
            lgpd.purge_company(b.company_id, operator="teste")  # sem pedido
    _request(app, a.company_id, days_ago=31)
    with app.app_context():
        dry = lgpd.purge_due(operator="teste", dry_run=True)
        assert len(dry) == 1 and dry[0].rows["projects"] == 1
        assert db.session.get(Company, a.company_id) is not None  # dry-run não apaga
    result = app.test_cli_runner().invoke(args=["lgpd-purge", "--operador", "ops"])
    assert result.exit_code == 0, result.output
    assert "apagada" in result.output
    again = app.test_cli_runner().invoke(args=["lgpd-purge"])
    assert again.exit_code == 0 and "Nenhuma empresa" in again.output
    with app.app_context():
        assert db.session.get(Company, a.company_id) is None
        assert lgpd.purge_company(a.company_id, operator="x") is None  # idempotente
        for model in (Project, Membership, AuditLog, ProgressEntry, DomainEvent):
            assert db.session.execute(select(func.count()).select_from(model).where(model.company_id == a.company_id)).scalar_one() == 0
        assert db.session.execute(select(func.count()).select_from(User).where(User.email.like("%.a@exemplo.com"))).scalar_one() == 0
        # B intacta
        assert db.session.get(Company, b.company_id) is not None
        assert db.session.execute(select(func.count()).select_from(Project).where(Project.company_id == b.company_id)).scalar_one() == 1
        log = db.session.execute(select(PlatformAuditLog).where(PlatformAuditLog.subject_company_id == a.company_id)).scalar_one()
        assert log.action == lgpd.COMPANY_PURGED and log.operator == "ops" and log.details["users_deleted"] == 3
        assert "exemplo.com" not in str(log.details)


def test_expurgo_mantem_usuario_com_outra_empresa(app, tenants):
    a, b = tenants
    with app.app_context():
        operator_a = db.session.get(User, a.operator_id)
        db.session.add(Membership(company_id=b.company_id, user_id=operator_a.id, role="operator"))
        db.session.add(PasswordReset(user_id=a.owner_id, token_hash="h" * 64, expires_at=utcnow()))
        db.session.add(LoginThrottle(scope="account", key_hash=__import__("app.services.lockout", fromlist=["_key"])._key("account", a.owner_email), failures=1))
        db.session.commit()
    _request(app, a.company_id, days_ago=40)
    with app.app_context():
        [result] = lgpd.purge_due(operator="teste")
        assert result.users_deleted == 2
        assert db.session.get(User, a.operator_id) is not None
        assert db.session.get(User, a.owner_id) is None
        assert db.session.execute(select(func.count()).select_from(PasswordReset)).scalar_one() == 0
        assert db.session.execute(select(func.count()).select_from(LoginThrottle)).scalar_one() == 0
    # o operador continua entrando na outra empresa
    client = app.test_client()
    login(client, app, a.operator_email)
    assert "Projeto B" in client.get("/app/projetos").get_data(as_text=True)


# ---------------------------------------------------------------- retenção


def test_retencao_apaga_so_o_vencido(app, tenants):
    from app.services.api_tokens import API_REQUEST

    a, _ = tenants
    old = utcnow() - timedelta(days=400)
    with app.app_context():
        db.session.add(AuditLog(company_id=a.company_id, action=API_REQUEST, at=old))
        db.session.add(AuditLog(company_id=a.company_id, action="project.updated", at=old))
        db.session.add(DomainEvent(company_id=a.company_id, type="x", payload={}, created_at=old, published_at=old))
        db.session.add(DomainEvent(company_id=a.company_id, type="y", payload={}, created_at=old))  # não publicado: fica
        db.session.add(LoginThrottle(scope="ip", key_hash="k" * 64, failures=1, last_failure_at=old))
        db.session.add(PasswordReset(user_id=a.owner_id, token_hash="r" * 64, expires_at=old, created_at=old))
        db.session.commit()
        dry = lgpd.apply_retention(operator="t", dry_run=True)
        assert dry["audit_logs"] == 1 and dry["domain_events"] == 1
        counts = lgpd.apply_retention(operator="t")
        assert counts["audit_logs"] == 1 and counts["domain_events"] == 1
        assert counts["login_throttles"] == 1 and counts["password_resets"] == 1
        remaining = db.session.execute(select(AuditLog.action).where(AuditLog.company_id == a.company_id, AuditLog.at == old)).scalars().all()
        assert remaining == ["project.updated"]
        assert db.session.execute(select(func.count()).select_from(DomainEvent).where(DomainEvent.published_at.is_(None))).scalar_one() >= 1
        assert db.session.execute(select(PlatformAuditLog.action)).scalars().all() == [lgpd.RETENTION_APPLIED]


# ---------------------------------------------------------------- acesso de suporte


@pytest.fixture()
def support_user(app):
    from app.services.passwords import hash_password

    with app.app_context():
        user = User(email="suporte@plataforma.com", name="Suporte Plataforma", password_hash=hash_password(PASSWORD), email_confirmed_at=utcnow(), mfa_enabled=True)
        db.session.add(user)
        db.session.commit()
        return user.id


def _grant(app, company_id, **kw):
    args = dict(email="suporte@plataforma.com", company_id=company_id, reason="Chamado 123: erro ao importar planilha", hours=2, role="operator", operator="gerente")
    args.update(kw)
    with app.app_context():
        return support.grant(**args).id


def test_suporte_exige_motivo_prazo_mfa_e_nunca_owner(app, tenants, support_user):
    a, _ = tenants
    for kw, msg in (
        ({"reason": "curto"}, "Motivo"),
        ({"hours": 0}, "Prazo"),
        ({"hours": 1000}, "Prazo"),
        ({"role": "owner"}, "operator ou supervisor"),
        ({"operator": ""}, "autorizou"),
        ({"email": a.operator_email}, "MFA"),
    ):
        with pytest.raises(support.SupportError, match=msg):
            _grant(app, a.company_id, **kw)
    with app.app_context():
        user = db.session.get(User, support_user)
        user.mfa_enabled = False
        db.session.commit()
    with pytest.raises(support.SupportError, match="MFA"):
        _grant(app, a.company_id)


def test_suporte_concedido_avisa_dono_audita_e_expira_sozinho(app, tenants, support_user):
    a, b = tenants
    member_id = _grant(app, a.company_id)
    mail = outbox(app)[-1]
    assert mail.to == a.owner_email and "Chamado 123" in mail.text and "Suporte Plataforma" in mail.text
    with app.app_context():
        entry = db.session.execute(select(AuditLog).where(AuditLog.action == support.GRANTED)).scalar_one()
        assert entry.company_id == a.company_id and entry.details["reason"].startswith("Chamado 123")
        assert entry.details["authorized_by"] == "gerente"
        before = entitlements.count_users(a.company_id)
        assert before == 3  # suporte não conta no plano
        db.session.get(User, support_user).mfa_enabled = False  # só para o login do teste (sem etapa TOTP)
        db.session.commit()
    client = app.test_client()
    login(client, app, "suporte@plataforma.com")
    assert client.get(f"/app/projetos/{a.project_id}").status_code == 200
    assert client.get(f"/app/projetos/{b.project_id}").status_code == 404
    # vence: na próxima requisição perde o acesso, sem cron
    with app.app_context():
        member = db.session.get(Membership, member_id)
        member.expires_at = utcnow() - timedelta(minutes=1)
        db.session.commit()
    assert client.get(f"/app/projetos/{a.project_id}").status_code == 403
    with app.app_context():
        assert support.expire() == 1
        assert support.expire() == 0
        assert db.session.get(Membership, member_id).active is False
        assert db.session.execute(select(func.count()).select_from(AuditLog).where(AuditLog.action == support.EXPIRED)).scalar_one() == 1


def test_suporte_cli_conceder_listar_revogar(app, tenants, support_user):
    a, _ = tenants
    runner = app.test_cli_runner()
    sem_motivo = runner.invoke(args=["suporte", "conceder", "suporte@plataforma.com", "--empresa", str(a.company_id), "--autorizado-por", "x"])
    assert sem_motivo.exit_code != 0
    ok = runner.invoke(args=[
        "suporte", "conceder", "suporte@plataforma.com", "--empresa", str(a.company_id),
        "--motivo", "Cliente pediu ajuda no chamado 77", "--horas", "3", "--autorizado-por", "gerente",
    ])
    assert ok.exit_code == 0, ok.output
    assert "suporte@plataforma.com" in runner.invoke(args=["suporte", "listar"]).output
    assert "revogado" in runner.invoke(args=["suporte", "revogar", "suporte@plataforma.com", "--empresa", str(a.company_id)]).output
    assert "Nenhum" in runner.invoke(args=["suporte", "listar"]).output
    with app.app_context():
        assert db.session.execute(select(func.count()).select_from(AuditLog).where(AuditLog.action == support.REVOKED)).scalar_one() == 1


def test_suporte_nao_vira_proprietario(client, app, tenants, support_user):
    a, _ = tenants
    member_id = _grant(app, a.company_id)
    login(client, app, a.owner_email)
    post(client, app, f"/app/usuarios/{member_id}/papel", {"role": "owner"})
    with app.app_context():
        assert db.session.get(Membership, member_id).role == "operator"


def test_membro_comum_nao_recebe_acesso_de_suporte(app, tenants, support_user):
    a, _ = tenants
    with app.app_context():
        db.session.add(Membership(company_id=a.company_id, user_id=support_user, role="operator"))
        db.session.commit()
    with pytest.raises(support.SupportError, match="já é membro"):
        _grant(app, a.company_id)


def test_cli_retencao_e_mfa(app, tenants):
    runner = app.test_cli_runner()
    out = runner.invoke(args=["lgpd-retencao", "--dry-run"])
    assert out.exit_code == 0 and "audit_logs" in out.output
    assert runner.invoke(args=["mfa-rotacionar"]).exit_code == 0



def test_expurgo_nao_apaga_conta_de_suporte(app, tenants, support_user):
    a, _ = tenants
    _grant(app, a.company_id)
    _request(app, a.company_id, days_ago=31)
    with app.app_context():
        [result] = lgpd.purge_due(operator="t")
        assert result.users_deleted == 3
        assert db.session.get(User, support_user) is not None


def test_suporte_nao_convida_ninguem(app, tenants, support_user):
    from app.services import accounts

    a, _ = tenants
    member_id = _grant(app, a.company_id, role="supervisor")
    with app.app_context():
        member = db.session.get(Membership, member_id)
        assert accounts.can_manage_invite_role(member, "operator") is False
