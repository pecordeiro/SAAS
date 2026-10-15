"""Etapa C — painel interno da equipe e requisição de identidade visual.

- /interno responde 404 para quem não é equipe (anônimo, dono de empresa, equipe sem MFA).
- A requisição abre sozinha ao passar a ter ``visual_custom`` (uma vez), com o contato do dono.
- Mudança de estado: servidor valida, audita em platform_audit_logs; a empresa não tem rota.
- ``flask staff conceder|revogar`` exige MFA, motivo e deixa trilha.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models import (
    Company,
    PlatformAuditLog,
    Subscription,
    User,
    VisualRequest,
)
from app.models.base import utcnow
from app.services import plans as catalog
from app.services import staff
from app.services.billing import service as billing
from tests.conftest import login, make_tenant, post


def _staff_user(app, *, mfa=True, is_staff=True, email="equipe@exemplo.com"):
    from app.services.passwords import hash_password
    from tests.conftest import PASSWORD

    with app.app_context():
        user = User(
            email=email,
            name="Equipe",
            password_hash=hash_password(PASSWORD),
            email_confirmed_at=utcnow(),
            mfa_enabled=mfa,
            is_staff=is_staff,
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def _session_as(client, app, user_id):
    with app.app_context():
        user = db.session.get(User, user_id)
        ident = user.get_id()
    with client.session_transaction() as sess:
        sess["_user_id"] = ident
        sess["_fresh"] = True


def _contract_visual(app, company_id, code="empresa"):
    with app.app_context():
        company = db.session.get(Company, company_id)
        sub = db.session.execute(select(Subscription).where(Subscription.company_id == company_id)).scalar_one_or_none()
        if sub is None:
            sub = Subscription(company_id=company_id, plan_id=catalog.get_plan("essencial").id, provider="fake", status="active")
            db.session.add(sub)
            db.session.flush()
        billing._apply_plan(sub, catalog.get_plan(code))
        db.session.commit()
        return company.name


def _requests(app):
    with app.app_context():
        return list(db.session.execute(select(VisualRequest)).scalars())


def test_contratar_empresa_abre_uma_requisicao_com_contato_do_dono(app, tenants):
    a, _ = tenants
    _contract_visual(app, a.company_id)
    [req] = _requests(app)
    assert req.company_id == a.company_id and req.status == "new" and req.plan_code == "empresa"
    assert req.contact_email == a.owner_email and req.company_name == "Empresa A"
    # idempotente: reaplicar o mesmo plano ou subir para Implantação não duplica a aberta
    _contract_visual(app, a.company_id, "implantacao")
    assert len(_requests(app)) == 1
    with app.app_context():
        assert db.session.query(PlatformAuditLog).filter_by(action=staff.VISUAL_REQUEST_OPENED).count() == 1


def test_plano_sem_identidade_visual_nao_abre_requisicao(app, tenants):
    a, _ = tenants
    _contract_visual(app, a.company_id, "profissional")
    assert _requests(app) == []


@pytest.mark.parametrize("who", ["anonimo", "dono", "equipe_sem_mfa", "nao_equipe"])
def test_interno_e_404_para_quem_nao_e_equipe(client, app, tenants, who):
    a, _ = tenants
    _contract_visual(app, a.company_id)
    [req] = _requests(app)
    if who == "dono":
        login(client, app, a.owner_email)
    elif who == "equipe_sem_mfa":
        _session_as(client, app, _staff_user(app, mfa=False))
    elif who == "nao_equipe":
        _session_as(client, app, _staff_user(app, is_staff=False))
    urls = ["/interno", f"/interno/requisicoes/{req.id}"]
    for url in urls:
        assert client.get(url).status_code == 404
    assert post(client, app, f"/interno/requisicoes/{req.id}/estado", {"status": "delivered"}).status_code == 404
    assert _requests(app)[0].status == "new"


def test_equipe_ve_lista_detalhe_e_muda_estado(client, app, tenants):
    a, b = tenants
    _contract_visual(app, a.company_id)
    _contract_visual(app, b.company_id)
    _session_as(client, app, _staff_user(app))
    page = client.get("/interno").get_data(as_text=True)
    assert "Empresa A" in page and "Empresa B" in page
    only_new = client.get("/interno?estado=delivered").get_data(as_text=True)
    assert "Empresa A" not in only_new
    req = next(r for r in _requests(app) if r.company_name == "Empresa A")
    detail = client.get(f"/interno/requisicoes/{req.id}").get_data(as_text=True)
    assert a.owner_email in detail
    ok = post(client, app, f"/interno/requisicoes/{req.id}/estado", {"status": "in_progress", "notes": "Logo recebido"})
    assert ok.status_code == 303
    inv = post(client, app, f"/interno/requisicoes/{req.id}/estado", {"status": "invalido", "notes": ""})
    assert inv.status_code == 400
    with app.app_context():
        got = db.session.get(VisualRequest, req.id)
        assert got.status == "in_progress" and got.notes == "Logo recebido" and got.updated_by == "equipe@exemplo.com"
        log = db.session.query(PlatformAuditLog).filter_by(action=staff.VISUAL_STATUS_CHANGED).one()
        assert log.details["para"] == "in_progress" and "Logo" not in str(log.details)
    assert client.get(f"/interno/requisicoes/{uuid.uuid4()}").status_code == 404


def test_cli_conceder_exige_mfa_e_motivo_e_revogar_derruba_sessao(app):
    runner = app.test_cli_runner()
    uid = _staff_user(app, mfa=False, is_staff=False, email="novo@exemplo.com")
    fail = runner.invoke(args=["staff", "conceder", "novo@exemplo.com", "--motivo", "Atende o plano Empresa", "--autorizado-por", "Pedro"])
    assert fail.exit_code != 0 and "MFA" in fail.output
    with app.app_context():
        user = db.session.get(User, uid)
        user.mfa_enabled = True
        db.session.commit()
    short = runner.invoke(args=["staff", "conceder", "novo@exemplo.com", "--motivo", "curto", "--autorizado-por", "Pedro"])
    assert short.exit_code != 0
    ok = runner.invoke(args=["staff", "conceder", "novo@exemplo.com", "--motivo", "Atende o plano Empresa", "--autorizado-por", "Pedro"])
    assert ok.exit_code == 0, ok.output
    with app.app_context():
        assert db.session.get(User, uid).is_staff
        version = db.session.get(User, uid).session_version
    assert "novo@exemplo.com" in runner.invoke(args=["staff", "listar"]).output
    rev = runner.invoke(args=["staff", "revogar", "novo@exemplo.com", "--motivo", "Saiu da equipe da plataforma", "--autorizado-por", "Pedro"])
    assert rev.exit_code == 0, rev.output
    with app.app_context():
        user = db.session.get(User, uid)
        assert not user.is_staff and user.session_version == version + 1
        assert db.session.query(PlatformAuditLog).filter(PlatformAuditLog.action.in_([staff.STAFF_GRANTED, staff.STAFF_REVOKED])).count() == 2


def test_expurgo_lgpd_apaga_a_requisicao_da_empresa(app, tenants):
    a, _ = tenants
    _contract_visual(app, a.company_id)
    from app.services import lgpd

    with app.app_context():
        assert "visual_requests" in {t.name for t in lgpd.company_tables()}


def test_exportacao_lgpd_nao_leva_anotacao_nem_email_da_equipe(client, app, tenants):
    import io
    import zipfile

    a, _ = tenants
    _contract_visual(app, a.company_id)
    with app.app_context():
        req = db.session.execute(select(VisualRequest)).scalars().first()
        req.notes, req.updated_by = "ANOTACAO-INTERNA-SECRETA", "equipe-interna@exemplo.com"
        db.session.commit()
        from app.services import lgpd

        data, _counts = lgpd.export_company(db.session.get(Company, a.company_id))
    zf = zipfile.ZipFile(io.BytesIO(data))
    blob = b"".join(zf.read(n) for n in zf.namelist())
    assert b"ANOTACAO-INTERNA-SECRETA" not in blob and b"equipe-interna@exemplo.com" not in blob
    assert not any("visual_requests" in n for n in zf.namelist())
