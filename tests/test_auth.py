"""Cadastro, login, papéis e CSRF."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app import create_app
from app.blueprints.auth import safe_next
from app.extensions import db
from app.models import Company, Membership, User
from tests.conftest import PASSWORD, csrf_token, login, post, text_of

SIGNUP = {
    "company_name": "Indústria Teste",
    "name": "Maria",
    "email": "Maria@Exemplo.com",
    "password": "senha-forte-123",
    "password_confirm": "senha-forte-123",
}


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_cadastro_cria_empresa_e_owner_e_pede_confirmacao(client, app):
    response = post(client, app, "/cadastro", SIGNUP)
    assert response.status_code == 303
    assert response.headers["Location"].endswith("/cadastro/confirme")
    assert "maria@exemplo.com" in text_of(client.get("/cadastro/confirme"))
    with app.app_context():
        user = db.session.execute(select(User).where(User.email == "maria@exemplo.com")).scalar_one()
        assert user.password_hash.startswith("$argon2id$")
        assert user.email_confirmed_at is None
        membership = db.session.execute(select(Membership).where(Membership.user_id == user.id)).scalar_one()
        assert membership.role == "owner"
        assert db.session.get(Company, membership.company_id).name == "Indústria Teste"
    # Sem confirmar ainda entra (carência de 7 dias).
    assert login(client, app, "maria@exemplo.com", SIGNUP["password"]).status_code == 302
    assert client.get("/app/projetos").status_code == 200


def test_cadastro_email_repetido_mesma_resposta_sem_enumerar(client, app):
    first = post(client, app, "/cadastro", SIGNUP)
    second = post(client, app, "/cadastro", {**SIGNUP, "company_name": "Outra"})
    assert first.status_code == second.status_code == 303
    assert first.headers["Location"] == second.headers["Location"]
    page = text_of(client.get("/cadastro/confirme"))
    assert "Indústria Teste" not in page
    with app.app_context():
        assert db.session.query(Company).count() == 1


def test_login_e_logout(client, app, tenants):
    a, _ = tenants
    response = login(client, app, a.owner_email)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/app/projetos")
    assert "Projeto A" in text_of(client.get("/app/projetos"))
    response = post(client, app, "/sair")
    assert response.status_code == 302
    assert client.get("/app/projetos").status_code == 302  # volta para o login


def test_login_senha_errada_mensagem_generica(client, app, tenants):
    a, _ = tenants
    wrong = login(client, app, a.owner_email, "senha-errada-000")
    unknown = login(client, app, "ninguem@exemplo.com", "senha-errada-000")
    assert wrong.status_code == unknown.status_code == 400
    assert "E-mail ou senha incorretos." in text_of(wrong)
    assert "E-mail ou senha incorretos." in text_of(unknown)
    assert client.get("/app/projetos").status_code == 302


def test_area_logada_exige_login(client):
    response = client.get("/app/projetos")
    assert response.status_code == 302
    assert "/entrar" in response.headers["Location"]


def test_login_next_so_aceita_caminho_interno(client, app, tenants):
    a, _ = tenants
    response = post(client, app, "/entrar", {"email": a.owner_email, "password": PASSWORD, "next": "https://evil.example/x"})
    assert response.headers["Location"].endswith("/app/projetos")
    post(client, app, "/sair")
    response = post(client, app, "/entrar", {"email": a.owner_email, "password": PASSWORD, "next": f"/app/projetos/{a.project_id}"})
    assert response.headers["Location"].endswith(f"/app/projetos/{a.project_id}")


def test_safe_next():
    assert safe_next("/app/projetos") == "/app/projetos"
    for bad in ["https://evil.com", "//evil.com", "/\\evil.com", "\\\\evil.com", "javascript:alert(1)", "", None, "/a\r\nb"]:
        assert safe_next(bad) is None, bad


def test_operador_recebe_403_ao_criar_projeto(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    assert client.get("/app/projetos/novo").status_code == 403
    response = post(client, app, "/app/projetos/novo", {"name": "X", "quantity": 1})
    assert response.status_code == 403
    assert post(client, app, f"/app/projetos/{a.project_id}/etapas", {"name": "Nova"}).status_code == 403
    assert (
        post(client, app, f"/app/etapas/{a.stage_id}/atividades", {"name": "Nova", "ideal_minutes": "5"}).status_code
        == 403
    )


def test_operador_pode_registrar_pecas(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    response = post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 2})
    assert response.status_code == 303


def test_supervisor_cria_projeto(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    data = {
        "name": "Lote 10 equipamentos",
        "quantity": 10,
        "people": 1,
        "hours_per_day": "8",
        "stages-0-name": "Preparação",
        "stages-0-activities": "Separar peças; 10\nConferir; 5,5",
        "stages-1-name": "Montagem",
        "stages-1-activities": "Montar; 30",
    }
    response = post(client, app, "/app/projetos/novo", data)
    assert response.status_code == 303, text_of(response)
    page = text_of(client.get(response.headers["Location"]))
    assert "Lote 10 equipamentos" in page
    assert "Preparação" in page and "Conferir" in page
    assert "0 de 10" in page
    assert "0,0%" in page  # progresso 0%
    assert "Lote 10 equipamentos" in text_of(client.get("/app/projetos"))


def test_novo_projeto_valida_linhas_de_atividade(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    data = {"name": "P", "quantity": 5, "people": 1, "hours_per_day": "8", "stages-0-name": "E", "stages-0-activities": "sem tempo"}
    response = post(client, app, "/app/projetos/novo", data)
    assert response.status_code == 400
    assert "Nome; minutos" in text_of(response)


def test_post_sem_csrf_recebe_400(client, app, tenants):
    a, _ = tenants
    assert client.post("/entrar", data={"email": a.owner_email, "password": PASSWORD}).status_code == 400
    assert client.post("/cadastro", data=SIGNUP).status_code == 400
    login(client, app, a.owner_email)
    assert client.post("/app/projetos/novo", data={"name": "X", "quantity": 1}).status_code == 400
    assert client.post(f"/app/atividades/{a.activity_id}/registrar", data={"delta": 1}).status_code == 400
    assert client.post("/sair").status_code == 400
    bad = client.post(f"/app/atividades/{a.activity_id}/registrar", data={"delta": 1, "csrf_token": "forjado"})
    assert bad.status_code == 400


def test_sessao_invalidada_ao_trocar_session_version(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    assert client.get("/app/projetos").status_code == 200
    with app.app_context():
        db.session.get(User, a.owner_id).session_version += 1
        db.session.commit()
    assert client.get("/app/projetos").status_code == 302


def test_usuario_inativo_nao_entra(client, app, tenants):
    a, _ = tenants
    with app.app_context():
        db.session.get(User, a.owner_id).active = False
        db.session.commit()
    assert login(client, app, a.owner_email).status_code == 400


def test_rate_limit_no_login(app_factory):
    app = app_factory({"RATELIMIT_ENABLED": True, "LOGIN_RATE_LIMIT": "3 per minute"})
    client = app.test_client()
    codes = [
        client.post("/entrar", data={"email": "x@exemplo.com", "password": "y", "csrf_token": csrf_token(client, app)}).status_code
        for _ in range(4)
    ]
    assert codes[:3] == [400, 400, 400]
    assert codes[3] == 429


def test_config_producao_exige_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app("production")
