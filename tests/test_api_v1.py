"""API pública v1 (Fase 9): flag, autenticação por token, escopos, plano, isolamento, contrato."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from openapi_spec_validator import validate
from sqlalchemy import select, text

from app.extensions import db
from app.models import ApiToken, AuditLog, Company, Project
from app.services import api_tokens as tokens
from app.services import projects as svc
from tests.conftest import login, make_tenant, post

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "api" / "openapi.yaml"
PROBLEM = "application/problem+json"


@pytest.fixture()
def api_app(app_factory):
    """Flag ligada e plano de teste = Empresa (único com a feature ``api``)."""
    return app_factory({"FEATURE_PUBLIC_API": True, "DEFAULT_TRIAL_PLAN": "empresa"})


@pytest.fixture()
def client(request):
    """Client do app com a API ligada quando o teste usa ``api_app``; senão, do app padrão."""
    target = request.getfixturevalue("api_app" if "api_app" in request.fixturenames else "app")
    return target.test_client()


@pytest.fixture()
def api_tenants(api_app):
    with api_app.app_context():
        return make_tenant("A"), make_tenant("B")


def new_token(app, company_id, scopes=("read:projects",), days=30, name="Integração"):
    with app.app_context():
        company = db.session.get(Company, company_id)
        created = tokens.create_token(company, name=name, scopes=list(scopes), expires_in_days=days, user_id=None)
        db.session.commit()
        return created.raw, created.token.id


def get(client, url, raw=None, **kwargs):
    headers = {"Authorization": f"Bearer {raw}"} if raw else {}
    return client.get(url, headers=headers, **kwargs)


def assert_problem(response, status, code):
    assert response.status_code == status, response.get_data(as_text=True)
    assert response.mimetype == PROBLEM
    body = response.get_json()
    assert body["status"] == status and body["code"] == code
    assert {"type", "title"} <= body.keys()
    return body


# ---------------------------------------------------------------- flag desligada


def test_flag_desligada_api_responde_404_e_tela_invisivel(client, app, tenants):
    a, _ = tenants
    assert app.config["FEATURE_PUBLIC_API"] is False
    for url in ("/api/v1/projects", f"/api/v1/projects/{a.project_id}/summary", "/api/v1/qualquer"):
        assert client.get(url, headers={"Authorization": "Bearer cp_x"}).status_code == 404
    assert client.post("/api/v1/activities/x/progress").status_code == 404
    login(client, app, a.owner_email)
    assert client.get("/app/integracoes/api").status_code == 404
    page = client.get("/app/projetos").get_data(as_text=True)
    assert "/app/integracoes" not in page
    assert not [r for r in app.url_map.iter_rules() if r.endpoint.startswith(("api_v1.", "api_tokens_ui."))]


def test_flag_ligada_menu_so_para_proprietario(client, api_app, api_tenants):
    a, _ = api_tenants
    login(client, api_app, a.owner_email)
    assert "/app/integracoes/api" in client.get("/app/projetos").get_data(as_text=True)
    other = api_app.test_client()
    login(other, api_app, a.supervisor_email)
    assert "/app/integracoes" not in other.get("/app/projetos").get_data(as_text=True)
    assert other.get("/app/integracoes/api").status_code == 403


# ---------------------------------------------------------------- autenticação


def test_sem_token_401(client, api_tenants):
    response = client.get("/api/v1/projects")
    assert_problem(response, 401, "missing_token")
    assert response.headers["WWW-Authenticate"].startswith("Bearer")
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize("header", ["Bearer cp_naoexiste", "Bearer lixo", "Basic abc", "Bearer ", "Bearer cp_" + "x" * 500])
def test_token_invalido_401(client, api_tenants, header):
    response = client.get("/api/v1/projects", headers={"Authorization": header})
    assert response.status_code == 401 and response.mimetype == PROBLEM


def test_token_valido_200_e_revogado_expirado_401(client, api_app, api_tenants):
    a, _ = api_tenants
    raw, token_id = new_token(api_app, a.company_id)
    assert get(client, "/api/v1/projects", raw).status_code == 200
    with api_app.app_context():
        token = db.session.get(ApiToken, token_id)
        tokens.revoke(token, None)
        db.session.commit()
    assert_problem(get(client, "/api/v1/projects", raw), 401, "token_revoked")

    raw2, id2 = new_token(api_app, a.company_id, name="Expira")
    with api_app.app_context():
        db.session.get(ApiToken, id2).expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.session.commit()
    assert_problem(get(client, "/api/v1/projects", raw2), 401, "token_expired")


def test_integracao_revogada_derruba_o_token(client, api_app, api_tenants):
    a, _ = api_tenants
    raw, token_id = new_token(api_app, a.company_id)
    with api_app.app_context():
        db.session.get(ApiToken, token_id).client.revoked_at = datetime.now(timezone.utc)
        db.session.commit()
    assert_problem(get(client, "/api/v1/projects", raw), 401, "token_revoked")


def test_sessao_de_navegador_nao_autentica_na_api(client, api_app, api_tenants):
    a, _ = api_tenants
    login(client, api_app, a.owner_email)
    assert client.get("/app/projetos").status_code == 200
    assert_problem(client.get("/api/v1/projects"), 401, "missing_token")
    assert_problem(client.get(f"/api/v1/projects/{a.project_id}/summary"), 401, "missing_token")


def test_sem_escopo_403(client, api_app, api_tenants):
    a, _ = api_tenants
    raw, _ = new_token(api_app, a.company_id, scopes=("write:progress",))
    body = assert_problem(get(client, "/api/v1/projects", raw), 403, "insufficient_scope")
    assert "read:projects" in body["detail"]
    assert_problem(get(client, f"/api/v1/projects/{a.project_id}/summary", raw), 403, "insufficient_scope")


def test_plano_sem_feature_api_403(client, app_factory):
    app = app_factory({"FEATURE_PUBLIC_API": True})  # teste padrão = Profissional (api: false)
    with app.app_context():
        a = make_tenant("A")
    raw, _ = new_token(app, a.company_id)
    assert_problem(get(app.test_client(), "/api/v1/projects", raw), 403, "plan_feature_unavailable")


def test_post_sem_csrf_chega_na_rota(client, api_app, api_tenants):
    """O blueprint é isento de CSRF: sem token CSRF a requisição não vira 400."""
    a, _ = api_tenants
    raw, _ = new_token(api_app, a.company_id, scopes=("write:progress",))
    response = client.post(
        f"/api/v1/activities/{a.activity_id}/progress", headers={"Authorization": f"Bearer {raw}"}, json={"delta": 1}
    )
    assert response.status_code != 400


def test_rota_desconhecida_404_problem(client, api_app, api_tenants):
    a, _ = api_tenants
    raw, _ = new_token(api_app, a.company_id)
    assert_problem(get(client, "/api/v1/nada", raw), 404, "not_found")


# ---------------------------------------------------------------- dados e isolamento


def test_lista_so_da_empresa_do_token(client, api_app, api_tenants):
    a, b = api_tenants
    raw_a, _ = new_token(api_app, a.company_id)
    raw_b, _ = new_token(api_app, b.company_id)
    data_a = get(client, "/api/v1/projects", raw_a).get_json()
    data_b = get(client, "/api/v1/projects", raw_b).get_json()
    assert [p["id"] for p in data_a["data"]] == [str(a.project_id)]
    assert [p["id"] for p in data_b["data"]] == [str(b.project_id)]
    assert data_a["next_cursor"] is None
    item = data_a["data"][0]
    assert item["name"] == "Projeto A" and item["status"] == "active" and item["quantity"] == 10
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z", item["created_at"])


def test_paginacao_por_cursor(client, api_app, api_tenants):
    a, _ = api_tenants
    with api_app.app_context():
        company = db.session.get(Company, a.company_id)
        for n in range(4):
            svc.create_project(
                company, name=f"Extra {n}", quantity=5, start_date=None, due_date=None, people=1,
                hours_per_day=Decimal("8"), stages=[], check_limits=False,
            )
        db.session.commit()
    raw, _ = new_token(api_app, a.company_id)
    seen, cursor = [], None
    for _ in range(10):
        url = "/api/v1/projects?limit=2" + (f"&cursor={cursor}" if cursor else "")
        page = get(client, url, raw).get_json()
        assert len(page["data"]) <= 2
        seen += [p["id"] for p in page["data"]]
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert len(seen) == 5 and len(set(seen)) == 5  # 4 extras + o projeto A, sem repetir


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "limit=abc", "cursor=%25%25", "cursor=aGVsbG8"])
def test_parametros_invalidos_400(client, api_app, api_tenants, query):
    a, _ = api_tenants
    raw, _ = new_token(api_app, a.company_id)
    assert_problem(get(client, f"/api/v1/projects?{query}", raw), 400, "invalid_parameter")


def test_resumo_igual_ao_calc(client, api_app, api_tenants):
    a, _ = api_tenants
    with api_app.app_context():
        from app.models import Activity

        svc.register_progress(db.session.get(Activity, a.activity_id), 4, None, a.owner_id)
        db.session.commit()
        project = db.session.get(Project, a.project_id)
        expected = svc.summary(project)
    raw, _ = new_token(api_app, a.company_id)
    response = get(client, f"/api/v1/projects/{a.project_id}/summary", raw)
    assert response.status_code == 200 and response.mimetype == "application/json"
    body = response.get_json()
    assert body["project_id"] == str(a.project_id)
    assert body["units_planned"] == 10
    assert body["progress"] == expected.progresso_geral
    assert body["remaining_minutes"] == expected.tempo_restante_min
    assert body["total_minutes"] == expected.tempo_total_min
    assert body["units_completed"] == expected.unidades_concluidas
    activity = next(x for x in body["stages"][0]["activities"] if x["id"] == str(a.activity_id))
    assert activity["units_completed"] == 4 and activity["units_remaining"] == 6 and activity["version"] == 2


def test_token_de_a_nao_le_b_404(client, api_app, api_tenants):
    a, b = api_tenants
    raw_a, _ = new_token(api_app, a.company_id)
    assert_problem(get(client, f"/api/v1/projects/{b.project_id}/summary", raw_a), 404, "not_found")
    assert_problem(get(client, "/api/v1/projects/00000000-0000-0000-0000-000000000000/summary", raw_a), 404, "not_found")
    assert_problem(get(client, "/api/v1/projects/nao-e-uuid/summary", raw_a), 404, "not_found")
    assert get(client, f"/api/v1/projects/{a.project_id}/summary", raw_a).status_code == 200


# ---------------------------------------------------------------- auditoria, uso e segredo


def test_chamada_auditada_last_used_e_token_nunca_em_texto_puro(client, api_app, api_tenants, caplog):
    a, _ = api_tenants
    raw, token_id = new_token(api_app, a.company_id)
    with caplog.at_level(logging.DEBUG):
        assert get(client, "/api/v1/projects", raw).status_code == 200
        assert get(client, f"/api/v1/projects/{a.project_id}/summary", raw).status_code == 200
        assert get(client, "/api/v1/projects/00000000-0000-0000-0000-000000000000/summary", raw).status_code == 404
    with api_app.app_context():
        token = db.session.get(ApiToken, token_id)
        assert token.last_used_at is not None
        assert token.token_hash == tokens.hash_token(raw) and token.token_hash != raw
        assert token.token_prefix == raw[:11] and raw.startswith("cp_")
        calls = db.session.execute(select(AuditLog).where(AuditLog.action == "api.request")).scalars().all()
        assert [c.details["status"] for c in calls] == [200, 200, 404] or sorted(c.details["status"] for c in calls) == [200, 200, 404]
        assert all(c.company_id == a.company_id and c.object_id == token_id for c in calls)
        # o token puro não está em NENHUMA coluna de api_tokens, api_clients nem audit_logs
        for table in ("api_tokens", "api_clients", "audit_logs"):
            rows = db.session.execute(text(f"SELECT * FROM {table}")).all()
            assert rows and not any(raw in str(cell) for row in rows for cell in row), table
    assert raw not in caplog.text


def test_token_invalido_nao_vai_para_o_log(client, api_app, api_tenants, caplog):
    secret = "cp_segredo-que-nao-existe"
    with caplog.at_level(logging.DEBUG):
        client.get("/api/v1/projects", headers={"Authorization": f"Bearer {secret}"})
    assert secret not in caplog.text


# ---------------------------------------------------------------- rate limit


def test_rate_limit_por_token(app_factory):
    app = app_factory(
        {"FEATURE_PUBLIC_API": True, "DEFAULT_TRIAL_PLAN": "empresa", "RATELIMIT_ENABLED": True, "API_RATE_LIMIT": "2 per minute"}
    )
    with app.app_context():
        a = make_tenant("A")
    raw1, _ = new_token(app, a.company_id, name="um")
    raw2, _ = new_token(app, a.company_id, name="dois")
    client = app.test_client()
    assert get(client, "/api/v1/projects", raw1).status_code == 200
    assert get(client, "/api/v1/projects", raw1).status_code == 200
    assert_problem(get(client, "/api/v1/projects", raw1), 429, "rate_limited")
    assert get(client, "/api/v1/projects", raw2).status_code == 200  # outro token, outro balde


# ---------------------------------------------------------------- tela de tokens


def test_owner_cria_token_ve_uma_vez_e_ele_funciona(client, api_app, api_tenants):
    a, _ = api_tenants
    login(client, api_app, a.owner_email)
    assert client.get("/app/integracoes/api").status_code == 200
    response = post(client, api_app, "/app/integracoes/api", {"name": "ERP", "scopes": ["read:projects"], "expires": "30"})
    assert response.status_code == 201
    html = response.get_data(as_text=True)
    raw = re.search(r"cp_[A-Za-z0-9_-]{43}", html).group(0)
    assert response.headers["Cache-Control"] == "no-store"
    assert get(api_app.test_client(), "/api/v1/projects", raw).status_code == 200
    # segunda visita: só o prefixo, nunca o token
    again = client.get("/app/integracoes/api").get_data(as_text=True)
    assert raw not in again and raw[:11] in again
    with api_app.app_context():
        token = db.session.execute(select(ApiToken).where(ApiToken.company_id == a.company_id)).scalar_one()
        assert token.scopes == ["read:projects"] and token.expires_at is not None
        created = db.session.execute(select(AuditLog).where(AuditLog.action == "api_token.created")).scalar_one()
        assert raw not in str(created.details)


@pytest.mark.parametrize(
    "data",
    [
        {"name": "", "scopes": ["read:projects"], "expires": "30"},
        {"name": "X", "scopes": [], "expires": "30"},
        {"name": "X", "scopes": ["admin:tudo"], "expires": "30"},
        {"name": "X", "scopes": ["read:projects"], "expires": "7"},
    ],
)
def test_criar_token_invalido_400(client, api_app, api_tenants, data):
    a, _ = api_tenants
    login(client, api_app, a.owner_email)
    assert post(client, api_app, "/app/integracoes/api", data).status_code == 400
    with api_app.app_context():
        assert db.session.execute(select(ApiToken)).first() is None


def test_criar_token_em_plano_sem_api_402(app_factory):
    app = app_factory({"FEATURE_PUBLIC_API": True})
    with app.app_context():
        a = make_tenant("A")
    client = app.test_client()
    login(client, app, a.owner_email)
    page = client.get("/app/integracoes/api").get_data(as_text=True)
    assert "API indisponível" in page
    assert post(client, app, "/app/integracoes/api", {"name": "X", "scopes": ["read:projects"], "expires": "30"}).status_code == 402
    with app.app_context():
        assert db.session.execute(select(ApiToken)).first() is None


def test_revogar_pela_tela(client, api_app, api_tenants):
    a, _ = api_tenants
    raw, token_id = new_token(api_app, a.company_id)
    login(client, api_app, a.owner_email)
    assert post(client, api_app, f"/app/integracoes/api/{token_id}/revogar").status_code == 303
    assert_problem(get(api_app.test_client(), "/api/v1/projects", raw), 401, "token_revoked")


def test_tela_exige_csrf_e_owner(client, api_app, api_tenants):
    a, _ = api_tenants
    _, token_id = new_token(api_app, a.company_id)
    login(client, api_app, a.owner_email)
    assert client.post(f"/app/integracoes/api/{token_id}/revogar").status_code == 400
    sup = api_app.test_client()
    login(sup, api_app, a.supervisor_email)
    assert post(sup, api_app, f"/app/integracoes/api/{token_id}/revogar").status_code == 403
    assert post(sup, api_app, "/app/integracoes/api", {"name": "X", "scopes": ["read:projects"]}).status_code == 403


# ---------------------------------------------------------------- contrato (openapi.yaml)


def load_spec() -> dict:
    return yaml.safe_load(SPEC.read_text(encoding="utf-8"))


def test_openapi_valido():
    spec = load_spec()
    validate(spec)
    assert spec["openapi"].startswith("3.1")
    assert spec["components"]["securitySchemes"]["bearerAuth"]["scheme"] == "bearer"
    scopes = {s for path in spec["paths"].values() for op in path.values() for sec in op.get("security", []) for ss in sec.values() for s in ss}
    assert scopes == {"read:projects", "write:progress"}
    assert "application/problem+json" in spec["components"]["responses"]["Unauthorized"]["content"]


def _normalized_rules(app):
    found = set()
    for rule in app.url_map.iter_rules():
        if not rule.endpoint.startswith("api_v1.") or rule.endpoint == "api_v1.unknown":
            continue
        path = re.sub(r"<(?:[^:>]+:)?[^>]+>", "{}", rule.rule.removeprefix("/api/v1"))
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            found.add((method.lower(), path))
    return found


def test_rotas_do_blueprint_batem_com_o_contrato(api_app):
    spec = load_spec()
    documented = {
        (method, re.sub(r"\{[^}]+\}", "{}", path))
        for path, ops in spec["paths"].items()
        for method in ops
        if method in {"get", "post", "put", "patch", "delete"}
    }
    assert _normalized_rules(api_app) == documented


# ---------------------------------------------------------------- stubs (501) — comportamento futuro


@pytest.mark.xfail(strict=True, reason="pendente: GET /projects/{id} reservado (501)")
def test_pendente_detalhe_do_projeto(client, api_app, api_tenants):
    a, _ = api_tenants
    raw, _ = new_token(api_app, a.company_id)
    assert get(client, f"/api/v1/projects/{a.project_id}", raw).status_code == 200


@pytest.mark.xfail(strict=True, reason="pendente: GET /projects/{id}/events reservado (501)")
def test_pendente_eventos_do_projeto(client, api_app, api_tenants):
    a, _ = api_tenants
    raw, _ = new_token(api_app, a.company_id)
    assert get(client, f"/api/v1/projects/{a.project_id}/events", raw).status_code == 200


@pytest.mark.xfail(strict=True, reason="pendente: POST /activities/{id}/progress reservado (501)")
def test_pendente_registrar_progresso(client, api_app, api_tenants):
    a, _ = api_tenants
    raw, _ = new_token(api_app, a.company_id, scopes=("write:progress",))
    response = client.post(
        f"/api/v1/activities/{a.activity_id}/progress",
        headers={"Authorization": f"Bearer {raw}", "If-Match": '"1"'},
        json={"delta": 1},
    )
    assert response.status_code == 201


def test_stubs_respondem_501_problem(client, api_app, api_tenants):
    a, _ = api_tenants
    raw, _ = new_token(api_app, a.company_id, scopes=("read:projects", "write:progress"))
    auth = {"Authorization": f"Bearer {raw}"}
    assert_problem(client.get(f"/api/v1/projects/{a.project_id}", headers=auth), 501, "not_implemented")
    assert_problem(client.get(f"/api/v1/projects/{a.project_id}/events", headers=auth), 501, "not_implemented")
    assert_problem(client.post(f"/api/v1/activities/{a.activity_id}/progress", headers=auth, json={"delta": 1}), 501, "not_implemented")
