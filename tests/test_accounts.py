"""Fase 5 — contas: e-mail, confirmação, reset de senha, convites, membros, perfil, sessões,
MFA, bloqueio progressivo, troca de empresa e ausência de token em claro no banco/logs."""

from __future__ import annotations

import logging
import re
import time
from datetime import timedelta

import pyotp
import pytest
from sqlalchemy import select, text

from app.extensions import db
from app.models import (
    Company,
    EmailConfirmation,
    Invitation,
    LoginThrottle,
    Membership,
    MfaRecoveryCode,
    PasswordReset,
    Subscription,
    User,
)
from app.services import accounts, lockout, mfa
from app.services.email import ConsoleEmailSender, EmailError, EmailMessage, ResendEmailSender, outbox
from app.services.plans import get_plan
from app.services.tokens import hash_token, utcnow
from tests.conftest import PASSWORD, login, post, text_of

TOKEN_RE = re.compile(r"/(conta/confirmar|senha/redefinir|convite)/([A-Za-z0-9_-]{20,})")
NEW_PASSWORD = "nova-senha-forte-456"
SIGNUP = {
    "company_name": "Indústria Nova",
    "name": "Rita Nova",
    "email": "rita@nova.com",
    "password": "senha-forte-123",
    "password_confirm": "senha-forte-123",
}


def mails(app, to=None):
    return [m for m in outbox(app) if to is None or m.to == to]


def last_token(app, to=None, kind=None) -> str:
    for message in reversed(mails(app, to)):
        for match in TOKEN_RE.finditer(message.text):
            if kind is None or match.group(1) == kind:
                return match.group(2)
    raise AssertionError("nenhum token nos e-mails")


def no_csrf(html: str) -> str:
    return re.sub(r'name="csrf_token"[^>]*value="[^"]*"|value="[^"]*"\s+name="csrf_token"', "", html)


def _set_plan(app, company_id, code):
    with app.app_context():
        db.session.add(Subscription(company_id=company_id, plan_id=get_plan(code).id, provider="fake", status="active"))
        db.session.commit()


# --------------------------------------------------------------------------- e-mail


def test_console_guarda_em_memoria_e_nao_loga_corpo(app, caplog):
    caplog.set_level(logging.DEBUG)
    with app.test_request_context():
        from app.services.email import send_template

        send_template("x@exemplo.com", "Redefinir a senha", "reset_password", name="X", url="https://h/senha/redefinir/SEGREDO123")
    assert len(outbox(app)) == 1
    msg = outbox(app)[0]
    assert "SEGREDO123" in msg.text and "SEGREDO123" in msg.html
    assert "Controle de Produção" in msg.html and "Controle de Produção" in msg.text
    assert "SEGREDO123" not in caplog.text and "x@exemplo.com" not in caplog.text


def test_resend_envia_com_timeout_e_falha_sem_vazar(monkeypatch, caplog):
    import requests

    calls = []

    class Resp:
        status_code = 200

    def fake_post(url, headers, json, timeout):
        calls.append((url, headers, json, timeout))
        return Resp()

    monkeypatch.setattr(requests, "post", fake_post)
    sender = ResendEmailSender("re_chave_secreta", "Controle <a@b.com>", 7)
    sender.send(EmailMessage("y@exemplo.com", "Assunto", "texto TOKEN-XYZ", "<p>html</p>"))
    url, headers, payload, timeout = calls[0]
    assert url == "https://api.resend.com/emails" and timeout == 7
    assert headers["Authorization"] == "Bearer re_chave_secreta"
    assert payload["to"] == ["y@exemplo.com"] and payload["from"] == "Controle <a@b.com>"
    Resp.status_code = 500
    caplog.set_level(logging.DEBUG)
    with pytest.raises(EmailError):
        sender.send(EmailMessage("y@exemplo.com", "Assunto", "texto TOKEN-XYZ", "<p>html</p>"))
    assert "TOKEN-XYZ" not in caplog.text and "re_chave_secreta" not in caplog.text


def test_backend_de_teste_e_console(app):
    from app.services.email import get_sender

    assert isinstance(get_sender(app), ConsoleEmailSender)


def test_link_de_email_fora_de_dev_exige_app_base_url(app_factory):
    from app.services.email import external_url

    app = app_factory({"APP_BASE_URL": None})
    app.config["ENV_NAME"] = "production"
    with app.test_request_context(), pytest.raises(RuntimeError, match="APP_BASE_URL"):
        external_url("auth.login")
    app2 = app_factory({"APP_BASE_URL": "https://app.exemplo.com.br/"})
    with app2.test_request_context("/", base_url="http://evil.example"):
        assert external_url("auth.login") == "https://app.exemplo.com.br/entrar"


# --------------------------------------------------------------------------- confirmação


def test_confirmacao_valida_reutilizada_e_expirada(client, app):
    post(client, app, "/cadastro", SIGNUP)
    token = last_token(app, "rita@nova.com", "conta/confirmar")
    # GET não confirma (pré-carregamento de link por antivírus/e-mail não consome o token).
    assert client.get(f"/conta/confirmar/{token}").status_code == 200
    with app.app_context():
        assert accounts.find_user_by_email("rita@nova.com").email_confirmed_at is None
    response = post(client, app, f"/conta/confirmar/{token}")
    assert response.status_code == 303
    with app.app_context():
        assert accounts.find_user_by_email("rita@nova.com").email_confirmed_at is not None
    reused = post(client, app, f"/conta/confirmar/{token}")
    assert reused.status_code == 400 and "não vale mais" in text_of(reused)
    # expirado
    with app.app_context():
        user = accounts.find_user_by_email("rita@nova.com")
        user.email_confirmed_at = None
        db.session.commit()
    login(client, app, "rita@nova.com", SIGNUP["password"])
    post(client, app, "/conta/confirmar-email/reenviar")
    token2 = last_token(app, "rita@nova.com", "conta/confirmar")
    assert token2 != token
    with app.app_context():
        row = db.session.execute(select(EmailConfirmation).where(EmailConfirmation.token_hash == hash_token(token2))).scalar_one()
        row.expires_at = utcnow() - timedelta(minutes=1)
        db.session.commit()
    expired = post(client, app, f"/conta/confirmar/{token2}")
    assert expired.status_code == 400 and "venceu" in text_of(expired)
    assert client.get("/conta/confirmar/nao-e-token").status_code == 400


def test_token_de_confirmacao_de_outro_usuario_so_confirma_o_dono(client, app, tenants):
    a, _ = tenants
    post(client, app, "/cadastro", SIGNUP)
    token = last_token(app, "rita@nova.com", "conta/confirmar")
    login(client, app, a.owner_email)  # logado como outra pessoa (empresa A)
    assert post(client, app, f"/conta/confirmar/{token}").status_code == 303
    with app.app_context():
        assert accounts.find_user_by_email("rita@nova.com").email_confirmed_at is not None
        assert db.session.get(User, a.owner_id).email_confirmed_at is None


def test_sem_confirmacao_apos_7_dias_pede_confirmacao(client, app, tenants):
    a, _ = tenants
    with app.app_context():
        user = db.session.get(User, a.operator_id)
        user.created_at = utcnow() - timedelta(days=8)
        db.session.commit()
    login(client, app, a.operator_email)
    response = client.get("/app/projetos")
    assert response.status_code == 302 and response.headers["Location"].endswith("/conta/confirmar-email")
    assert "acesso está pausado" in text_of(client.get("/conta/confirmar-email"))
    post(client, app, "/conta/confirmar-email/reenviar")
    token = last_token(app, a.operator_email, "conta/confirmar")
    post(client, app, f"/conta/confirmar/{token}")
    assert client.get("/app/projetos").status_code == 200


def test_cadastro_com_email_existente_avisa_o_dono(client, app, tenants):
    a, _ = tenants
    new = post(client, app, "/cadastro", {**SIGNUP, "email": "nao-existe@x.com"})
    existing = post(client, app, "/cadastro", {**SIGNUP, "email": a.owner_email})
    assert new.status_code == existing.status_code == 303
    assert new.headers["Location"] == existing.headers["Location"]
    warning = mails(app, a.owner_email)
    assert len(warning) == 1 and "Tentativa de cadastro" in warning[0].subject
    assert TOKEN_RE.search(warning[0].text) is None  # aviso não leva token
    with app.app_context():
        assert db.session.query(Company).filter_by(name="Indústria Nova").count() == 1


# --------------------------------------------------------------------------- reset de senha


def test_reset_resposta_igual_para_email_existente_e_inexistente(client, app, tenants):
    a, _ = tenants
    r1 = post(client, app, "/senha/esqueci", {"email": a.owner_email})
    r2 = post(client, app, "/senha/esqueci", {"email": "ninguem@exemplo.com"})
    assert r1.status_code == r2.status_code == 200
    assert no_csrf(r1.get_data(as_text=True)).replace(a.owner_email, "") == no_csrf(r2.get_data(as_text=True)).replace(
        "ninguem@exemplo.com", ""
    )
    assert "Se houver conta com esse e-mail" in text_of(r1)
    assert len(mails(app, a.owner_email)) == 1 and not mails(app, "ninguem@exemplo.com")


def test_reset_valido_derruba_sessoes_e_nao_reutiliza(client, app, tenants):
    a, _ = tenants
    other = app.test_client()
    login(other, app, a.owner_email)
    assert other.get("/app/projetos").status_code == 200
    post(client, app, "/senha/esqueci", {"email": a.owner_email})
    token = last_token(app, a.owner_email, "senha/redefinir")
    page = client.get(f"/senha/redefinir/{token}")
    assert page.status_code == 200 and page.headers["Referrer-Policy"] == "no-referrer"
    response = post(client, app, f"/senha/redefinir/{token}", {"password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD})
    assert response.status_code == 303
    assert other.get("/app/projetos").status_code == 302  # outra sessão caiu
    assert login(client, app, a.owner_email).status_code == 400  # senha antiga não vale
    assert login(client, app, a.owner_email, NEW_PASSWORD).status_code == 302
    post(client, app, "/sair")
    reused = post(client, app, f"/senha/redefinir/{token}", {"password": "outra-senha-999x", "password_confirm": "outra-senha-999x"})
    assert reused.status_code == 400 and "não vale mais" in text_of(reused)
    assert login(client, app, a.owner_email, NEW_PASSWORD).status_code == 302


def test_reset_expirado_e_invalido(client, app, tenants):
    a, _ = tenants
    post(client, app, "/senha/esqueci", {"email": a.owner_email})
    token = last_token(app, a.owner_email, "senha/redefinir")
    with app.app_context():
        row = db.session.execute(select(PasswordReset)).scalar_one()
        assert row.token_hash == hash_token(token)
        row.expires_at = utcnow() - timedelta(seconds=1)
        db.session.commit()
    response = post(client, app, f"/senha/redefinir/{token}", {"password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD})
    assert response.status_code == 400 and "venceu" in text_of(response)
    assert client.get("/senha/redefinir/" + "x" * 43).status_code == 400
    assert login(client, app, a.owner_email).status_code == 302  # senha não mudou


def test_reset_de_usuario_de_outra_empresa_nao_mexe_na_minha_conta(client, app, tenants):
    a, b = tenants
    post(client, app, "/senha/esqueci", {"email": b.owner_email})
    token = last_token(app, b.owner_email, "senha/redefinir")
    login(client, app, a.owner_email)
    post(client, app, f"/senha/redefinir/{token}", {"password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD})
    fresh = app.test_client()
    assert login(fresh, app, a.owner_email).status_code == 302  # A continua com a senha dela
    assert login(app.test_client(), app, b.owner_email, NEW_PASSWORD).status_code == 302


# --------------------------------------------------------------------------- convites


def test_convite_cria_conta_e_vinculo(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    assert post(client, app, "/app/usuarios/convidar", {"email": "Ana@X.com", "role": "operator"}).status_code == 303
    token = last_token(app, "ana@x.com", "convite")
    guest = app.test_client()
    page = guest.get(f"/convite/{token}")
    assert page.status_code == 200 and "Empresa A" in text_of(page)
    response = post(guest, app, f"/convite/{token}", {"name": "Ana", "password": "senha-forte-ana1", "password_confirm": "senha-forte-ana1"})
    assert response.status_code == 303
    assert "Projeto A" in text_of(guest.get("/app/projetos"))
    with app.app_context():
        user = accounts.find_user_by_email("ana@x.com")
        member = db.session.execute(select(Membership).where(Membership.user_id == user.id)).scalar_one()
        assert member.company_id == a.company_id and member.role == "operator"
        assert user.email_confirmed_at is not None
    # reutilizado
    again = app.test_client().get(f"/convite/{token}")
    assert again.status_code == 400 and "não vale mais" in text_of(again)


def test_convite_expirado_revogado_e_reenviado(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    post(client, app, "/app/usuarios/convidar", {"email": "bia@x.com", "role": "operator"})
    token = last_token(app, "bia@x.com", "convite")
    with app.app_context():
        inv = db.session.execute(select(Invitation).where(Invitation.email == "bia@x.com")).scalar_one()
        inv_id = inv.id
        inv.expires_at = utcnow() - timedelta(minutes=1)
        db.session.commit()
    expired = app.test_client().get(f"/convite/{token}")
    assert expired.status_code == 400 and "venceu" in text_of(expired)
    # reenviar: token novo, o antigo para de valer
    assert post(client, app, f"/app/usuarios/convites/{inv_id}/reenviar").status_code == 303
    token2 = last_token(app, "bia@x.com", "convite")
    assert token2 != token
    assert app.test_client().get(f"/convite/{token}").status_code == 400
    assert app.test_client().get(f"/convite/{token2}").status_code == 200
    # revogar
    assert post(client, app, f"/app/usuarios/convites/{inv_id}/revogar").status_code == 303
    assert app.test_client().get(f"/convite/{token2}").status_code == 400


def test_convite_vincula_conta_existente_e_troca_de_empresa(client, app, tenants):
    a, b = tenants
    login(client, app, a.owner_email)
    post(client, app, "/app/usuarios/convidar", {"email": b.owner_email, "role": "supervisor"})
    token = last_token(app, b.owner_email, "convite")
    other = app.test_client()
    page = other.get(f"/convite/{token}")
    assert "Entrar e aceitar" in text_of(page)
    login(other, app, b.owner_email)
    assert post(other, app, f"/convite/{token}").status_code == 303
    assert "Projeto A" in text_of(other.get("/app/projetos"))  # já na empresa A
    page = text_of(other.get("/conta/empresas"))
    assert "Empresa A" in page and "Empresa B" in page
    assert post(other, app, "/conta/empresas/trocar", {"company_id": str(b.company_id)}).status_code == 303
    projects = text_of(other.get("/app/projetos"))
    assert "Projeto B" in projects and "Projeto A" not in projects


def test_convite_para_outro_email_nao_vincula_usuario_logado(client, app, tenants):
    """Token de convite da empresa B para outra pessoa, usado por alguém logado da A."""
    a, b = tenants
    login(client, app, b.owner_email)
    post(client, app, "/app/usuarios/convidar", {"email": "carla@x.com", "role": "owner"})
    token = last_token(app, "carla@x.com", "convite")
    intruder = app.test_client()
    login(intruder, app, a.owner_email)
    assert "outra conta" in text_of(intruder.get(f"/convite/{token}"))
    assert post(intruder, app, f"/convite/{token}").status_code == 400
    with app.app_context():
        assert db.session.query(Membership).filter_by(user_id=a.owner_id).count() == 1
        assert db.session.execute(select(Invitation.used_at)).scalar_one() is None


def test_supervisor_nao_convida_owner_e_operador_nao_ve_usuarios(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    response = post(client, app, "/app/usuarios/convidar", {"email": "dono@x.com", "role": "owner"})
    assert response.status_code == 400
    assert post(client, app, "/app/usuarios/convidar", {"email": "op@x.com", "role": "operator"}).status_code == 303
    with app.app_context():
        assert {i.email for i in db.session.query(Invitation)} == {"op@x.com"}
    post(client, app, "/sair")
    login(client, app, a.operator_email)
    assert client.get("/app/usuarios").status_code == 403
    assert post(client, app, "/app/usuarios/convidar", {"email": "z@x.com", "role": "operator"}).status_code == 403


def test_convites_pendentes_contam_no_limite_de_usuarios(client, app, tenants):
    a, _ = tenants
    _set_plan(app, a.company_id, "essencial")  # 5 usuários; A já tem 3
    login(client, app, a.owner_email)
    assert post(client, app, "/app/usuarios/convidar", {"email": "u1@x.com", "role": "operator"}).status_code == 303
    assert post(client, app, "/app/usuarios/convidar", {"email": "u2@x.com", "role": "operator"}).status_code == 303
    blocked = post(client, app, "/app/usuarios/convidar", {"email": "u3@x.com", "role": "operator"})
    assert blocked.status_code == 400 and "Limite do plano" in text_of(blocked)
    assert "5 de 5 usuários" in text_of(client.get("/app/usuarios"))
    with app.app_context():
        u1 = db.session.execute(select(Invitation.id).where(Invitation.email == "u1@x.com")).scalar_one()
    post(client, app, f"/app/usuarios/convites/{u1}/revogar")
    assert post(client, app, "/app/usuarios/convidar", {"email": "u3@x.com", "role": "operator"}).status_code == 303


# --------------------------------------------------------------------------- membros


def _membership_id(app, user_id):
    with app.app_context():
        return db.session.execute(select(Membership.id).where(Membership.user_id == user_id)).scalar_one()


def test_usuario_desativado_perde_acesso_na_proxima_requisicao(client, app, tenants):
    a, _ = tenants
    operator = app.test_client()
    login(operator, app, a.operator_email)
    assert operator.get("/app/projetos").status_code == 200
    login(client, app, a.owner_email)
    assert post(client, app, f"/app/usuarios/{_membership_id(app, a.operator_id)}/desativar").status_code == 303
    response = operator.get("/app/projetos")
    assert response.status_code == 302 and "/entrar" in response.headers["Location"]
    assert login(operator, app, a.operator_email).status_code == 302  # entra, mas sem empresa
    assert operator.get("/app/projetos").status_code == 403
    assert post(client, app, f"/app/usuarios/{_membership_id(app, a.operator_id)}/reativar").status_code == 303
    assert operator.get("/app/projetos").status_code == 200


def test_ultimo_owner_nao_pode_ser_rebaixado_nem_desativado(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    owner_m = _membership_id(app, a.owner_id)
    response = post(client, app, f"/app/usuarios/{owner_m}/papel", {"role": "operator"})
    assert response.status_code == 400 and "pelo menos um proprietário" in text_of(response)
    assert post(client, app, f"/app/usuarios/{owner_m}/desativar").status_code == 400
    with app.app_context():
        assert db.session.get(Membership, owner_m).role == "owner"
        assert db.session.get(Membership, owner_m).active
    # Com um segundo owner, rebaixar o primeiro passa.
    sup = db_supervisor_membership(app, a)
    assert post(client, app, f"/app/usuarios/{sup}/papel", {"role": "owner"}).status_code == 303
    assert post(client, app, f"/app/usuarios/{owner_m}/papel", {"role": "supervisor"}).status_code == 303


def db_supervisor_membership(app, tenant):
    with app.app_context():
        user = accounts.find_user_by_email(tenant.supervisor_email)
        return db.session.execute(select(Membership.id).where(Membership.user_id == user.id)).scalar_one()


def test_supervisor_nao_muda_papel_nem_desativa(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    assert client.get("/app/usuarios").status_code == 200
    target = _membership_id(app, a.operator_id)
    assert post(client, app, f"/app/usuarios/{target}/papel", {"role": "supervisor"}).status_code == 403
    assert post(client, app, f"/app/usuarios/{target}/desativar").status_code == 403


# --------------------------------------------------------------------------- perfil e sessões


def test_perfil_nome_senha_e_sair_de_todos(client, app, tenants):
    a, _ = tenants
    other = app.test_client()
    login(other, app, a.owner_email)
    login(client, app, a.owner_email)
    assert post(client, app, "/conta/perfil/nome", {"name": "Dona A"}).status_code == 303
    wrong = post(client, app, "/conta/perfil/senha", {"current_password": "errada-000000", "password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD})
    assert wrong.status_code == 400 and "Senha atual incorreta" in text_of(wrong)
    ok = post(client, app, "/conta/perfil/senha", {"current_password": PASSWORD, "password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD})
    assert ok.status_code == 303
    assert client.get("/app/projetos").status_code == 200  # esta sessão segue
    assert other.get("/app/projetos").status_code == 302  # a outra caiu
    login(other, app, a.owner_email, NEW_PASSWORD)
    assert post(client, app, "/conta/sair-de-todos").status_code == 303
    assert client.get("/app/projetos").status_code == 302
    assert other.get("/app/projetos").status_code == 302


def test_logout_so_encerra_a_sessao_atual(client, app, tenants):
    a, _ = tenants
    other = app.test_client()
    login(other, app, a.owner_email)
    login(client, app, a.owner_email)
    post(client, app, "/sair")
    assert client.get("/app/projetos").status_code == 302
    assert other.get("/app/projetos").status_code == 200


def test_troca_de_email_com_reconfirmacao(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    _confirm_logged_user(client, app)
    wrong = post(client, app, "/conta/perfil/email", {"email": "novo@a.com", "current_password": "errada-00000"})
    assert wrong.status_code == 400
    assert post(client, app, "/conta/perfil/email", {"email": "novo@a.com", "current_password": PASSWORD}).status_code == 303
    with app.app_context():
        assert db.session.get(User, a.owner_id).email == a.owner_email  # ainda não mudou
    token = last_token(app, "novo@a.com", "conta/confirmar")
    assert post(client, app, f"/conta/confirmar/{token}").status_code == 303
    with app.app_context():
        assert db.session.get(User, a.owner_id).email == "novo@a.com"
    assert any("trocado" in m.subject for m in mails(app, a.owner_email))
    # e-mail que já tem conta: mesma resposta, nada muda, aviso vai para o dono do endereço
    response = post(client, app, "/conta/perfil/email", {"email": a.operator_email, "current_password": PASSWORD})
    assert response.status_code == 303
    assert any("Tentativa" in m.subject for m in mails(app, a.operator_email))


# --------------------------------------------------------------------------- MFA


def _confirm_logged_user(client, app) -> None:
    """MFA e troca de e-mail exigem e-mail confirmado (os usuários do fixture não são)."""
    import uuid as _uuid

    with client.session_transaction() as sess:
        user_id = _uuid.UUID(sess["_user_id"].split(":")[0])
    with app.app_context():
        db.session.get(User, user_id).email_confirmed_at = utcnow()
        db.session.commit()


def _enable_mfa(client, app) -> tuple[str, list[str]]:
    _confirm_logged_user(client, app)
    assert client.get("/conta/mfa").status_code == 200
    qr = client.get("/conta/mfa/qr.svg")
    assert qr.status_code == 200 and qr.headers["Content-Type"] == "image/svg+xml" and b"<svg" in qr.data
    with client.session_transaction() as sess:
        enc = sess["mfa_setup"]
    with app.app_context():
        secret = mfa.decrypt_secret(enc)
    assert post(client, app, "/conta/mfa/ativar", {"code": "000000" if pyotp.TOTP(secret).now() != "000000" else "111111"}).status_code == 400
    response = post(client, app, "/conta/mfa/ativar", {"code": pyotp.TOTP(secret).now()})
    assert response.status_code == 200
    codes = re.findall(r'<code class="num">([a-z2-9]{5}-[a-z2-9]{5})</code>', response.get_data(as_text=True))
    assert len(codes) == 10
    return secret, codes


def test_mfa_ativar_e_entrar_com_codigo_e_recuperacao(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    secret, codes = _enable_mfa(client, app)
    with app.app_context():
        user = db.session.get(User, a.owner_id)
        assert user.mfa_enabled and secret not in user.totp_secret_enc
        assert all(c.replace("-", "") not in r.code_hash for c in codes for r in db.session.query(MfaRecoveryCode))
    post(client, app, "/sair")
    response = login(client, app, a.owner_email)
    assert response.status_code == 303 and response.headers["Location"].endswith("/entrar/mfa")
    assert client.get("/app/projetos").status_code == 302  # ainda não entrou
    assert post(client, app, "/entrar/mfa", {"code": "123456" if pyotp.TOTP(secret).now() != "123456" else "654321"}).status_code == 400
    # o código da ativação (passo atual) já foi usado: vale o do próximo passo (janela ±1)
    used = pyotp.TOTP(secret).at(time.time() + 30)
    assert post(client, app, "/entrar/mfa", {"code": used}).status_code == 302
    assert client.get("/app/projetos").status_code == 200
    post(client, app, "/sair")
    # mesmo código TOTP não vale de novo (replay) — o recovery code vale uma vez
    login(client, app, a.owner_email)
    assert post(client, app, "/entrar/mfa", {"code": used}).status_code == 400
    assert post(client, app, "/entrar/mfa", {"code": codes[0]}).status_code == 302
    post(client, app, "/sair")
    login(client, app, a.owner_email)
    assert post(client, app, "/entrar/mfa", {"code": codes[0]}).status_code == 400
    assert post(client, app, "/entrar/mfa", {"code": codes[1].upper()}).status_code == 302


def test_mfa_obrigatorio_para_owner_quando_empresa_exige(client, app, tenants):
    a, _ = tenants
    _set_plan(app, a.company_id, "empresa")
    login(client, app, a.owner_email)
    blocked = post(client, app, "/app/usuarios/seguranca/mfa", {"exigir": "1"})
    assert blocked.status_code == 400  # o próprio owner precisa ter MFA antes
    _enable_mfa(client, app)
    assert post(client, app, "/app/usuarios/seguranca/mfa", {"exigir": "1"}).status_code == 303
    # promove o supervisor a owner: ele, sem MFA, é levado a ativar
    sup = db_supervisor_membership(app, a)
    post(client, app, f"/app/usuarios/{sup}/papel", {"role": "owner"})
    other = app.test_client()
    login(other, app, a.supervisor_email)
    response = other.get("/app/projetos")
    assert response.status_code == 302 and response.headers["Location"].endswith("/conta/mfa")
    # operador não é afetado
    op = app.test_client()
    login(op, app, a.operator_email)
    assert op.get("/app/projetos").status_code == 200


def test_exigir_mfa_so_no_plano_empresa(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    assert post(client, app, "/app/usuarios/seguranca/mfa", {"exigir": "1"}).status_code == 403


def test_segredo_mfa_cifrado_com_chave_derivada(app_factory):
    app = app_factory({"MFA_ENCRYPTION_KEY": "chave-mfa-de-teste"})
    with app.app_context():
        enc = mfa.encrypt_secret("JBSWY3DPEHPK3PXP")
        assert "JBSWY3DPEHPK3PXP" not in enc and mfa.decrypt_secret(enc) == "JBSWY3DPEHPK3PXP"
    other = app_factory({"MFA_ENCRYPTION_KEY": "outra-chave"})
    with other.app_context():
        assert mfa.decrypt_secret(enc) is None


# --------------------------------------------------------------------------- bloqueio


def test_bloqueio_progressivo_por_conta(client, app, tenants):
    a, _ = tenants
    codes = [login(client, app, a.owner_email, "errada-000000").status_code for _ in range(5)]
    assert codes == [400, 400, 400, 400, 429]
    locked = login(client, app, a.owner_email)  # senha certa, mas bloqueado
    assert locked.status_code == 429 and "Muitas tentativas" in text_of(locked)
    # e-mail inexistente se comporta igual (não revela cadastro)
    ghost = [login(client, app, "fantasma@x.com", "errada-000000").status_code for _ in range(5)]
    assert ghost == codes
    with app.app_context():
        for row in db.session.query(LoginThrottle):
            row.locked_until = utcnow() - timedelta(seconds=1)
        db.session.commit()
    assert login(client, app, a.owner_email).status_code == 302
    with app.app_context():  # login certo zera a conta
        assert lockout.status(a.owner_email, None).locked is False


def test_bloqueio_escalona_1_5_15_60(app):
    with app.test_request_context():
        now = utcnow()
        waits = []
        for i in range(9):
            st = lockout.register_failure("x@y.com", None, now=now)
            waits.append(round(st.retry_after_seconds / 60))
        assert waits == [0, 0, 0, 0, 1, 5, 15, 60, 60]
        rows = db.session.query(LoginThrottle).all()
        assert len(rows) == 1 and "x@y.com" not in rows[0].key_hash


def test_bloqueio_por_ip(app_factory):
    app = app_factory({"LOCKOUT_IP_THRESHOLD": 3})
    client = app.test_client()
    statuses = [login(client, app, f"pessoa{i}@x.com", "errada-000000").status_code for i in range(4)]
    assert statuses == [400, 400, 429, 429]


def test_mfa_errado_conta_no_bloqueio(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    _enable_mfa(client, app)
    post(client, app, "/sair")
    login(client, app, a.owner_email)
    results = [post(client, app, "/entrar/mfa", {"code": "000001"}).status_code for _ in range(5)]
    assert results[-1] == 429


# --------------------------------------------------------------------------- tokens em claro


def test_nenhum_token_em_claro_no_banco_nem_nos_logs(client, app, tenants, caplog):
    caplog.set_level(logging.DEBUG)
    a, _ = tenants
    post(client, app, "/cadastro", SIGNUP)
    post(client, app, "/senha/esqueci", {"email": a.owner_email})
    login(client, app, a.owner_email)
    post(client, app, "/app/usuarios/convidar", {"email": "tok@x.com", "role": "operator"})
    tokens = {m.group(2) for msg in outbox(app) for m in TOKEN_RE.finditer(msg.text)}
    assert len(tokens) >= 3
    # usa os tokens (a página e o aceite também passam pelos logs)
    for token in tokens:
        client.get(f"/convite/{token}")
        client.get(f"/senha/redefinir/{token}")
    with app.app_context():
        dump = []
        for table in db.metadata.sorted_tables:
            for row in db.session.execute(text(f'SELECT * FROM "{table.name}"')):
                dump.append(" ".join(str(v) for v in row))
        everything = "\n".join(dump)
    for token in tokens:
        assert token not in everything
        assert token not in caplog.text
        assert hash_token(token) in everything  # o hash está lá


# --------------------------------------------------------------------------- com RLS ligado

from tests.conftest import requires_postgres  # noqa: E402
from tests.test_rls import rls_app, rls_url  # noqa: E402,F401  (fixtures)


@requires_postgres
def test_fluxos_de_conta_com_rls_ligado(app, rls_app, tenants):  # noqa: F811
    """Convite (lido pelo hash do token, política invitations_by_token), reset de senha e
    lista de usuários rodando como papel comum com RLS forçado."""
    a, b = tenants
    owner = rls_app.test_client()
    assert login(owner, rls_app, a.owner_email).status_code == 302
    page = text_of(owner.get("/app/usuarios"))
    assert a.operator_email in page and b.operator_email not in page
    assert post(owner, rls_app, "/app/usuarios/convidar", {"email": "rls@x.com", "role": "operator"}).status_code == 303
    token = last_token(rls_app, "rls@x.com", "convite")
    guest = rls_app.test_client()
    assert guest.get(f"/convite/{token}").status_code == 200
    response = post(guest, rls_app, f"/convite/{token}", {"name": "R", "password": "senha-forte-rls1", "password_confirm": "senha-forte-rls1"})
    assert response.status_code == 303
    assert "Projeto A" in text_of(guest.get("/app/projetos"))
    with app.app_context():
        user = accounts.find_user_by_email("rls@x.com")
        assert db.session.execute(select(Membership.company_id).where(Membership.user_id == user.id)).scalar_one() == a.company_id
    # reset de senha (tabelas globais) também funciona
    anon = rls_app.test_client()
    post(anon, rls_app, "/senha/esqueci", {"email": b.owner_email})
    reset = last_token(rls_app, b.owner_email, "senha/redefinir")
    assert post(anon, rls_app, f"/senha/redefinir/{reset}", {"password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD}).status_code == 303
    assert login(anon, rls_app, b.owner_email, NEW_PASSWORD).status_code == 302
    # membro de B continua 404 para o owner de A
    with app.app_context():
        b_member = db.session.execute(select(Membership.id).where(Membership.user_id == b.operator_id)).scalar_one()
    assert post(owner, rls_app, f"/app/usuarios/{b_member}/desativar").status_code == 404


@requires_postgres
def test_sem_token_o_rls_nao_mostra_convite(rls_app, app, tenants):  # noqa: F811
    from sqlalchemy import create_engine

    from app.services.tokens import new_token

    a, _ = tenants
    _tok, token_hash = new_token()
    with app.app_context():
        db.session.add(
            Invitation(company_id=a.company_id, email="z@x.com", role="operator", token_hash=token_hash, expires_at=utcnow() + timedelta(days=1))
        )
        db.session.commit()
    engine = create_engine(rls_app.config["SQLALCHEMY_DATABASE_URI"])
    try:
        with engine.begin() as conn:
            assert conn.execute(text("SELECT count(*) FROM invitations")).scalar_one() == 0
            conn.execute(text("SELECT set_config('app.token_hash', :h, true)"), {"h": "0" * 64})
            assert conn.execute(text("SELECT count(*) FROM invitations")).scalar_one() == 0
            conn.execute(text("SELECT set_config('app.token_hash', :h, true)"), {"h": token_hash})
            assert conn.execute(text("SELECT count(*) FROM invitations")).scalar_one() == 1
            # o hash só autoriza ler, não gravar
            assert conn.execute(text("UPDATE invitations SET role = 'owner'")).rowcount == 0
    finally:
        engine.dispose()


def test_paginas_de_conta_renderizam(client, app, tenants):
    a, _ = tenants
    for url in ("/entrar", "/senha/esqueci", "/cadastro"):
        assert client.get(url).status_code == 200, url
    assert "Esqueci a senha" in text_of(client.get("/entrar"))
    login(client, app, a.owner_email)
    for url in ("/conta/perfil", "/conta/empresas", "/conta/confirmar-email", "/app/usuarios"):
        response = client.get(url)
        assert response.status_code == 200, url
        assert "app-sidebar" in response.get_data(as_text=True)
    nav = text_of(client.get("/app/projetos"))
    assert "Usuários" in nav and "Perfil" in nav and "Confirme seu e-mail" in nav
    _confirm_logged_user(client, app)
    assert client.get("/conta/mfa").status_code == 200


# --------------------------------------------------------------------------- correções da revisão


def test_bloqueio_por_ip_nao_barra_senha_certa(app_factory):
    """Atrás de NAT/proxy, um atacante não tranca os demais: a senha certa entra mesmo com o
    IP bloqueado; senha errada desse IP responde 429."""
    from tests.conftest import make_tenant

    app = app_factory({"LOCKOUT_IP_THRESHOLD": 3})
    with app.app_context():
        a = make_tenant("A")
    attacker = app.test_client()
    statuses = [login(attacker, app, f"alvo{i}@x.com", "errada-000000").status_code for i in range(3)]
    assert statuses == [400, 400, 429]
    victim = app.test_client()  # mesmo IP (127.0.0.1)
    assert login(victim, app, a.owner_email).status_code == 302
    assert victim.get("/app/projetos").status_code == 200
    assert login(app.test_client(), app, a.operator_email, "errada-000000").status_code == 429


def test_ip_do_proxy_so_com_trusted_proxy_count(app_factory):
    def wrong(client, app, ip):
        return post(client, app, "/entrar", {"email": "x@x.com", "password": "errada-000000"},
                    headers={"X-Forwarded-For": ip}).status_code

    trusted = app_factory({"TRUSTED_PROXY_COUNT": 1, "LOCKOUT_IP_THRESHOLD": 2, "LOCKOUT_ACCOUNT_THRESHOLD": 99})
    c = trusted.test_client()
    assert [wrong(c, trusted, "1.1.1.1"), wrong(c, trusted, "1.1.1.1")] == [400, 429]
    assert wrong(c, trusted, "2.2.2.2") == 400  # outro IP real, outro contador
    with trusted.app_context():
        assert lockout.status(None, "1.1.1.1").locked and not lockout.status(None, "2.2.2.2").locked
    # Sem proxy confiável o header é ignorado (forjável): conta tudo no IP da conexão.
    plain = app_factory({"LOCKOUT_IP_THRESHOLD": 2, "LOCKOUT_ACCOUNT_THRESHOLD": 99})
    c2 = plain.test_client()
    assert [wrong(c2, plain, "1.1.1.1"), wrong(c2, plain, "9.9.9.9")] == [400, 429]


def test_supervisor_nao_reativa_membro_desativado_por_convite(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    op_member = _membership_id(app, a.operator_id)
    post(client, app, f"/app/usuarios/{op_member}/desativar")
    post(client, app, "/sair")
    sup = app.test_client()
    login(sup, app, a.supervisor_email)
    response = post(sup, app, "/app/usuarios/convidar", {"email": a.operator_email, "role": "operator"})
    assert response.status_code == 400 and "Só o proprietário" in text_of(response)
    with app.app_context():
        assert db.session.query(Invitation).count() == 0
    # Defesa no aceite: convite criado por não-owner (gravado direto) não reativa.
    from app.services.tokens import new_token

    token, token_hash = new_token()
    with app.app_context():
        sup_user = accounts.find_user_by_email(a.supervisor_email)
        db.session.add(Invitation(company_id=a.company_id, email=a.operator_email, role="operator", token_hash=token_hash,
                                  invited_by_user_id=sup_user.id, expires_at=utcnow() + timedelta(days=1)))
        db.session.commit()
    op = app.test_client()
    login(op, app, a.operator_email)
    assert post(op, app, f"/convite/{token}").status_code == 400
    with app.app_context():
        assert db.session.get(Membership, op_member).active is False
    # Convite do owner reativa.
    login(client, app, a.owner_email)
    assert post(client, app, "/app/usuarios/convidar", {"email": a.operator_email, "role": "operator"}).status_code == 303
    owner_token = last_token(app, a.operator_email, "convite")
    assert post(op, app, f"/convite/{owner_token}").status_code == 303
    with app.app_context():
        assert db.session.get(Membership, op_member).active is True


def test_reset_com_provedor_lento_ou_com_erro_responde_igual_e_rapido(client, app, tenants, monkeypatch):
    import threading

    import requests

    a, _ = tenants
    calls = []
    done = threading.Event()

    def slow_failing_post(*args, **kwargs):
        time.sleep(1.0)
        calls.append(kwargs["json"]["to"])
        done.set()
        raise requests.ConnectionError("fora do ar")

    monkeypatch.setattr(requests, "post", slow_failing_post)
    app.extensions["email_sender"] = ResendEmailSender("re_teste", "a@b.com", 5)
    started = time.monotonic()
    r1 = post(client, app, "/senha/esqueci", {"email": a.owner_email})
    r2 = post(client, app, "/senha/esqueci", {"email": "ninguem@exemplo.com"})
    elapsed = time.monotonic() - started
    assert r1.status_code == r2.status_code == 200
    assert no_csrf(r1.get_data(as_text=True)).replace(a.owner_email, "") == no_csrf(r2.get_data(as_text=True)).replace(
        "ninguem@exemplo.com", ""
    )
    assert elapsed < 0.9  # o envio (1 s e com erro) não entrou no tempo da resposta
    assert done.wait(5) and calls == [[a.owner_email]]  # só a conta existente gerou envio
    with app.app_context():
        assert db.session.query(PasswordReset).count() == 1


def test_pre_account_takeover_mfa_e_email_so_depois_de_confirmar(client, app, tenants):
    a, _ = tenants
    # Atacante cadastra o e-mail da vítima (não confirmado) e entra.
    post(client, app, "/cadastro", {**SIGNUP, "email": "vitima@x.com", "password": "senha-atacante1", "password_confirm": "senha-atacante1"})
    login(client, app, "vitima@x.com", "senha-atacante1")
    response = client.get("/conta/mfa")
    assert response.status_code == 303 and response.headers["Location"].endswith("/conta/confirmar-email")
    assert post(client, app, "/conta/mfa/ativar", {"code": "123456"}).status_code == 303
    assert client.get("/conta/mfa/qr.svg").status_code == 404
    changed = post(client, app, "/conta/perfil/email", {"email": "atacante@x.com", "current_password": "senha-atacante1"})
    assert changed.status_code == 400 and "Confirme o seu e-mail atual" in text_of(changed)
    with app.app_context():
        user = accounts.find_user_by_email("vitima@x.com")
        assert not user.mfa_enabled and user.email == "vitima@x.com"
        # Mesmo que um MFA tenha sido ativado antes da correção, o reset da vítima o apaga.
        mfa.enable(user, mfa.new_secret())
        db.session.commit()
    victim = app.test_client()
    post(victim, app, "/senha/esqueci", {"email": "vitima@x.com"})
    token = last_token(app, "vitima@x.com", "senha/redefinir")
    assert post(victim, app, f"/senha/redefinir/{token}", {"password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD}).status_code == 303
    with app.app_context():
        user = accounts.find_user_by_email("vitima@x.com")
        assert not user.mfa_enabled and user.totp_secret_enc is None
        assert user.email_confirmed_at is not None
        assert db.session.query(MfaRecoveryCode).filter_by(user_id=user.id).count() == 0
    assert client.get("/app/projetos").status_code == 302  # sessão do atacante caiu
    assert login(victim, app, "vitima@x.com", NEW_PASSWORD).status_code == 302  # sem pedir MFA


def test_reset_em_conta_confirmada_mantem_mfa(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    _enable_mfa(client, app)
    post(client, app, "/sair")
    post(client, app, "/senha/esqueci", {"email": a.owner_email})
    token = last_token(app, a.owner_email, "senha/redefinir")
    post(client, app, f"/senha/redefinir/{token}", {"password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD})
    with app.app_context():
        assert db.session.get(User, a.owner_id).mfa_enabled
    assert login(client, app, a.owner_email, NEW_PASSWORD).headers["Location"].endswith("/entrar/mfa")
