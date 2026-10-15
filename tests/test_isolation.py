"""Isolamento multiempresa: recurso da empresa B acessado por usuário da empresa A → 404.

Toda rota com <uuid:...> da área logada precisa de caso aqui (regra inviolável 1).
"""

from __future__ import annotations

import pytest

from app.extensions import db
from app.models import Activity, ProgressEntry, Stage
from tests.conftest import login, post

# (método, molde da URL, campo do Tenant, dados do POST)
ROUTES = [
    ("GET", "/app/projetos/{id}", "project_id", None),
    ("GET", "/app/projetos/{id}/historico", "project_id", None),
    ("POST", "/app/projetos/{id}/etapas", "project_id", {"name": "Invasora"}),
    ("GET", "/app/etapas/{id}", "stage_id", None),
    ("POST", "/app/etapas/{id}/atividades", "stage_id", {"name": "Invasora", "ideal_minutes": "5"}),
    ("GET", "/app/atividades/{id}", "activity_id", None),
    ("POST", "/app/atividades/{id}/registrar", "activity_id", {"delta": 1}),
    # Fase 6
    ("GET", "/app/projetos/{id}/atualizar", "project_id", None),
    ("GET", "/app/atividades/{id}/previa", "activity_id", None),
]

# Fase 6: rotas que precisam de ids que o Tenant não traz (feriado) — casos A/B em tests/test_fase6.py.
ROUTES_FASE6_EXTRA = [
    ("POST", "/app/empresa/feriados/{id}/remover", "holiday_id", None),
    ("POST", "/app/modelos/{id}/linhas", "template_id", None),
]


def _call(client, app, method, url, data):
    if method == "GET":
        return client.get(url)
    return post(client, app, url, data)


@pytest.mark.parametrize("method,template,field,data", ROUTES)
def test_recurso_de_outra_empresa_responde_404(client, app, tenants, method, template, field, data):
    a, b = tenants
    login(client, app, a.owner_email)  # owner: papel máximo, só a empresa impede o acesso
    response = _call(client, app, method, template.format(id=getattr(b, field)), data)
    assert response.status_code == 404


@pytest.mark.parametrize("method,template,field,data", ROUTES)
def test_mesma_rota_funciona_na_propria_empresa(client, app, tenants, method, template, field, data):
    a, _ = tenants
    login(client, app, a.owner_email)
    response = _call(client, app, method, template.format(id=getattr(a, field)), data)
    assert response.status_code in (200, 302, 303)


def test_escrita_bloqueada_nao_altera_dados_de_b(client, app, tenants):
    a, b = tenants
    login(client, app, a.owner_email)
    for method, template, field, data in ROUTES:
        if method == "POST":
            _call(client, app, method, template.format(id=getattr(b, field)), data)
    with app.app_context():
        activity = db.session.get(Activity, b.activity_id)
        assert activity.units_done == 0 and activity.version == 1
        assert db.session.query(ProgressEntry).filter_by(company_id=b.company_id).count() == 0
        assert db.session.query(Stage).filter_by(company_id=b.company_id).count() == 1
        assert db.session.query(Activity).filter_by(company_id=b.company_id).count() == 2


def test_lista_de_projetos_so_mostra_a_propria_empresa(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    page = client.get("/app/projetos").get_data(as_text=True)
    assert "Projeto A" in page
    assert "Projeto B" not in page


def test_company_id_forjado_na_sessao_nao_da_acesso(client, app, tenants):
    a, b = tenants
    login(client, app, a.owner_email)
    with client.session_transaction() as sess:
        sess["company_id"] = str(b.company_id)  # usuário de A sem vínculo com B
    assert client.get(f"/app/projetos/{b.project_id}").status_code == 404
    page = client.get("/app/projetos").get_data(as_text=True)
    assert "Projeto B" not in page and "Projeto A" in page


def test_vinculo_desativado_perde_acesso(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    from app.models import Membership

    with app.app_context():
        membership = db.session.query(Membership).filter_by(user_id=a.operator_id).one()
        membership.active = False
        db.session.commit()
    assert client.get(f"/app/projetos/{a.project_id}").status_code == 403


@pytest.mark.parametrize("flags", [{}, {"FEATURE_PUBLIC_API": True}], ids=["padrao", "api_ligada"])
def test_toda_rota_com_uuid_tem_caso_de_isolamento(app_factory, flags):
    """Varre o url_map (com e sem as flags que registram blueprints) e falha se alguma rota
    com <uuid:> não tiver caso A/B. Rota com dois <uuid:> também precisa estar listada."""
    app = app_factory(flags)
    todas = ROUTES + FASE4_ROUTES + ROUTES_CONTAS + ROUTES_FASE6_EXTRA + ROUTES_API + ROUTES_API_UI + ROUTES_ETAPA_D + ROUTES_ETAPA_E + ROUTES_ETAPA_F + ROUTES_ETAPA_G
    cobertas = {template.replace("{id}", "") for _, template, _, _ in todas}
    # Etapa C: /interno é da plataforma (sem empresa na URL); acesso cruzado = não ser equipe → 404,
    # coberto por tests/test_etapa_c_interno.py::test_interno_e_404_para_quem_nao_e_equipe.
    cobertas |= {"/interno/requisicoes/", "/interno/requisicoes//estado"}
    vistas = 0
    for rule in app.url_map.iter_rules():
        if "<uuid:" not in rule.rule:
            continue
        vistas += 1
        import re as _re

        sem_parametro = _re.sub(r"<uuid:[^>]+>", "", rule.rule)
        assert sem_parametro in cobertas, f"rota {rule.rule} sem teste de isolamento A/B"
    assert vistas > 0


def test_registrar_pecas_valida_maximo_e_grava_historico(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    url = f"/app/atividades/{a.activity_id}/registrar"
    assert post(client, app, url, {"delta": 3, "version": 1}).status_code == 303
    assert post(client, app, url, {"delta": 2, "version": 2}).status_code == 303
    with app.app_context():
        activity = db.session.get(Activity, a.activity_id)
        assert activity.units_done == 5 and activity.version == 3
    # +20 numa atividade com 5/10 → "máximo 5"
    response = post(client, app, url, {"delta": 20, "version": 3})
    assert response.status_code == 400
    assert "Máximo 5" in response.get_data(as_text=True)
    # versão antiga → conflito 409
    assert post(client, app, url, {"delta": 1, "version": 1}).status_code == 409
    with app.app_context():
        activity = db.session.get(Activity, a.activity_id)
        assert activity.units_done == 5
        entries = db.session.query(ProgressEntry).filter_by(activity_id=a.activity_id).all()
        assert sorted(e.delta for e in entries) == [2, 3]
    history = client.get(f"/app/projetos/{a.project_id}/historico").get_data(as_text=True)
    assert "+3" in history and "+2" in history


# ================================================================ Fase 4
# Rotas novas (modelos, edição, desfazer, exportar). Mesmo contrato: owner de A pedindo
# recurso de B → 404 e nada muda em B; na própria empresa a rota funciona.

from dataclasses import dataclass  # noqa: E402
from decimal import Decimal  # noqa: E402

from app.models import AuditLog, Company, DomainEvent, Project, Template, TemplateVersion, User  # noqa: E402
from app.services import projects as svc  # noqa: E402
from app.services import templates as tsvc  # noqa: E402
from tests.conftest import make_tenant  # noqa: E402

FASE4_ROUTES = [
    ("GET", "/app/modelos/{id}", "template_id", None),
    ("POST", "/app/modelos/{id}", "template_id", {"name": "Invasor", "stages-0-name": "X", "stages-0-activities": "Y; 1"}),
    ("GET", "/app/modelos/{id}/versoes", "template_id", None),
    ("POST", "/app/modelos/{id}/arquivar", "template_id", {}),
    ("GET", "/app/projetos/{id}/editar", "project_id", None),
    ("POST", "/app/projetos/{id}/editar", "project_id", {"name": "Invasor", "quantity": 10, "people": 1, "hours_per_day": "8"}),
    ("POST", "/app/projetos/{id}/duplicar", "project_id", {}),
    ("POST", "/app/projetos/{id}/arquivar", "project_id", {"confirm": "y"}),
    ("GET", "/app/projetos/{id}/modelo", "tpl_project_id", None),
    ("POST", "/app/projetos/{id}/modelo/aplicar", "tpl_project_id", {"confirm": "y"}),
    ("GET", "/app/projetos/{id}/exportar.csv", "project_id", None),
    ("GET", "/app/projetos/{id}/exportar.xlsx", "project_id", None),
    ("POST", "/app/etapas/{id}/renomear", "stage_id", {"name": "Invasora"}),
    ("POST", "/app/etapas/{id}/mover", "stage_id", {"direction": "down"}),
    ("POST", "/app/etapas/{id}/arquivar", "stage_id", {}),
    ("POST", "/app/atividades/{id}/editar", "activity_id", {"name": "Invasora", "ideal_minutes": "1"}),
    ("POST", "/app/atividades/{id}/mover", "activity_id", {"direction": "down"}),
    ("POST", "/app/atividades/{id}/arquivar", "activity_id", {}),
    ("GET", "/app/registros/{id}/desfazer", "entry_id", None),
    ("POST", "/app/registros/{id}/desfazer", "entry_id", {"confirm": "y"}),
]


@dataclass
class Tenant4:
    company_id: object
    owner_email: str
    project_id: object
    stage_id: object
    activity_id: object
    template_id: object
    version_id: object
    tpl_project_id: object
    entry_id: object


def _make_tenant4(label: str) -> Tenant4:
    base = make_tenant(label)
    company = db.session.get(Company, base.company_id)
    owner = db.session.query(User).filter_by(email=base.owner_email).one()
    template = tsvc.create_template(
        company,
        f"Modelo {label}",
        [svc.NewStage("Etapa M", [svc.NewActivity("Atv M", Decimal("10"))])],
        created_by_user_id=owner.id,
    )
    tpl_project = tsvc.create_project_from_template(
        company, template, name=f"De modelo {label}", quantity=5, start_date=None, due_date=None,
        people=1, hours_per_day=Decimal("8"),
    )
    # Versão nova do modelo: comparar/aplicar têm o que mostrar.
    tsvc.update_template(
        template, name=template.name, description=None, user_id=owner.id,
        stages=[svc.NewStage("Etapa M", [svc.NewActivity("Atv M", Decimal("12"))])],
    )
    entry = svc.register_progress(db.session.get(Activity, base.activity_id), 2, None, owner.id)
    db.session.commit()
    return Tenant4(
        company_id=base.company_id, owner_email=base.owner_email, project_id=base.project_id,
        stage_id=base.stage_id, activity_id=base.activity_id, template_id=template.id,
        version_id=template.current_version_id, tpl_project_id=tpl_project.id, entry_id=entry.id,
    )


@pytest.fixture()
def tenants4(app):
    with app.app_context():
        return _make_tenant4("A"), _make_tenant4("B")


def _snapshot(company_id) -> dict:
    """Estado de uma empresa que nenhuma requisição de outra pode mudar."""
    q = db.session.query
    return {
        "projects": sorted(
            (p.name, p.quantity, p.archived_at is None, str(p.template_version_id))
            for p in q(Project).filter_by(company_id=company_id)
        ),
        "stages": sorted(
            (s.name, s.position, s.archived_at is None, s.waiting_part, s.version)
            for s in q(Stage).filter_by(company_id=company_id)
        ),
        "activities": sorted(
            (a.name, str(a.ideal_minutes), a.position, a.units_done, a.archived_at is None)
            for a in q(Activity).filter_by(company_id=company_id)
        ),
        "entries": q(ProgressEntry).filter_by(company_id=company_id).count(),
        "templates": sorted(
            (t.name, t.archived_at is None, str(t.current_version_id)) for t in q(Template).filter_by(company_id=company_id)
        ),
        "versions": q(TemplateVersion).filter_by(company_id=company_id).count(),
        "events": q(DomainEvent).filter_by(company_id=company_id).count(),
        "audit": q(AuditLog).filter_by(company_id=company_id).count(),
    }


@pytest.mark.parametrize("method,template,field,data", FASE4_ROUTES)
def test_fase4_recurso_de_outra_empresa_responde_404(client, app, tenants4, method, template, field, data):
    a, b = tenants4
    with app.app_context():
        before = _snapshot(b.company_id)
    login(client, app, a.owner_email)
    response = _call(client, app, method, template.format(id=getattr(b, field)), data)
    assert response.status_code == 404
    with app.app_context():
        assert _snapshot(b.company_id) == before


@pytest.mark.parametrize("method,template,field,data", FASE4_ROUTES)
def test_fase4_mesma_rota_funciona_na_propria_empresa(client, app, tenants4, method, template, field, data):
    a, _ = tenants4
    login(client, app, a.owner_email)
    response = _call(client, app, method, template.format(id=getattr(a, field)), data)
    assert response.status_code in (200, 302, 303)


def test_novo_projeto_com_modelo_de_outra_empresa_responde_404_e_nada_grava(client, app, tenants4):
    a, b = tenants4
    with app.app_context():
        before_a, before_b = _snapshot(a.company_id), _snapshot(b.company_id)
    login(client, app, a.owner_email)
    base = {"name": "Roubado", "quantity": 3, "people": 1, "hours_per_day": "8"}
    assert post(client, app, "/app/projetos/novo", {**base, "template_id": str(b.template_id)}).status_code == 404
    # id de VERSÃO de B no lugar do modelo também não serve
    assert post(client, app, "/app/projetos/novo", {**base, "template_id": str(b.version_id)}).status_code == 404
    assert post(client, app, "/app/projetos/novo", {**base, "template_id": "nao-e-uuid"}).status_code == 404
    with app.app_context():
        assert _snapshot(a.company_id) == before_a and _snapshot(b.company_id) == before_b


def test_modelos_da_outra_empresa_nao_aparecem(client, app, tenants4):
    a, _ = tenants4
    login(client, app, a.owner_email)
    page = client.get("/app/modelos").get_data(as_text=True)
    assert "Modelo A" in page and "Modelo B" not in page
    page = client.get("/app/projetos/novo").get_data(as_text=True)
    assert "Modelo A" in page and "Modelo B" not in page


def test_previa_de_importacao_assinada_para_outra_empresa_e_recusada(client, app, tenants4):
    """O payload assinado leva empresa e usuário: não serve em outra sessão."""
    from itsdangerous import URLSafeTimedSerializer

    from app.blueprints.dados import PAYLOAD_SALT

    a, b = tenants4
    payload = URLSafeTimedSerializer(app.secret_key, salt=PAYLOAD_SALT).dumps(
        {"c": str(b.company_id), "u": "x", "d": {"name": "X", "quantity": 1, "stages": [{"name": "E", "activities": []}]}}
    )
    login(client, app, a.owner_email)
    with app.app_context():
        before = db.session.query(Project).count()
    response = post(client, app, "/app/importar/confirmar", {"payload": payload, "name": "X"})
    assert response.status_code == 400
    with app.app_context():
        assert db.session.query(Project).count() == before


def test_historico_e_exportacao_de_outra_empresa_nao_vazam_registros(client, app, tenants4):
    a, b = tenants4
    login(client, app, a.owner_email)
    page = client.get(f"/app/projetos/{a.project_id}/historico").get_data(as_text=True)
    assert f"/app/registros/{a.entry_id}/desfazer" in page
    assert str(b.entry_id) not in page
    csv_text = client.get(f"/app/projetos/{a.project_id}/exportar.csv").get_data(as_text=True)
    assert "Projeto A" in csv_text and "Projeto B" not in csv_text


# --------------------------------------------------------------------------- Fase 5 (contas)
# Rotas com <uuid:> de usuários e convites. O id vem de `_ids_contas` (membro supervisor e
# convite pendente de cada empresa), não do Tenant.

ROUTES_CONTAS = [
    ("POST", "/app/usuarios/convites/{id}/reenviar", "invitation_id", None),
    ("POST", "/app/usuarios/convites/{id}/revogar", "invitation_id", None),
    ("POST", "/app/usuarios/{id}/papel", "membership_id", {"role": "operator"}),
    ("POST", "/app/usuarios/{id}/desativar", "membership_id", None),
    ("POST", "/app/usuarios/{id}/reativar", "membership_id", None),
]


def _ids_contas(app, tenant):
    from datetime import timedelta

    from sqlalchemy import select

    from app.models import Invitation, Membership, User
    from app.services.tokens import new_token, utcnow

    with app.app_context():
        sup = db.session.execute(select(User).where(User.email == tenant.supervisor_email)).scalar_one()
        membership_id = db.session.execute(select(Membership.id).where(Membership.user_id == sup.id)).scalar_one()
        _token, token_hash = new_token()
        inv = Invitation(
            company_id=tenant.company_id, email=f"pendente-{tenant.company_id}@x.com", role="operator",
            token_hash=token_hash, expires_at=utcnow() + timedelta(days=7),
        )
        db.session.add(inv)
        db.session.commit()
        return {"membership_id": membership_id, "invitation_id": inv.id}


@pytest.mark.parametrize("method,template,field,data", ROUTES_CONTAS)
def test_contas_recurso_de_outra_empresa_responde_404(client, app, tenants, method, template, field, data):
    a, b = tenants
    ids_b = _ids_contas(app, b)
    login(client, app, a.owner_email)
    assert _call(client, app, method, template.format(id=ids_b[field]), data).status_code == 404


@pytest.mark.parametrize("method,template,field,data", ROUTES_CONTAS)
def test_contas_mesma_rota_funciona_na_propria_empresa(client, app, tenants, method, template, field, data):
    a, _ = tenants
    ids_a = _ids_contas(app, a)
    login(client, app, a.owner_email)
    assert _call(client, app, method, template.format(id=ids_a[field]), data).status_code in (200, 302, 303)


def test_contas_escrita_bloqueada_nao_altera_b(client, app, tenants):
    from app.models import Invitation, Membership

    a, b = tenants
    ids_b = _ids_contas(app, b)
    login(client, app, a.owner_email)
    for method, template, field, data in ROUTES_CONTAS:
        _call(client, app, method, template.format(id=ids_b[field]), data)
    with app.app_context():
        member = db.session.get(Membership, ids_b["membership_id"])
        assert member.active and member.role == "supervisor"
        inv = db.session.get(Invitation, ids_b["invitation_id"])
        assert inv.revoked_at is None and inv.used_at is None


def test_lista_de_usuarios_so_mostra_a_propria_empresa(client, app, tenants):
    a, b = tenants
    _ids_contas(app, b)
    login(client, app, a.owner_email)
    page = client.get("/app/usuarios").get_data(as_text=True)
    assert a.operator_email in page
    assert b.operator_email not in page and f"pendente-{b.company_id}" not in page


def test_trocar_para_empresa_sem_vinculo_responde_404(client, app, tenants):
    a, b = tenants
    login(client, app, a.owner_email)
    assert post(client, app, "/conta/empresas/trocar", {"company_id": str(b.company_id)}).status_code == 404
    assert post(client, app, "/conta/empresas/trocar", {"company_id": "nao-e-uuid"}).status_code == 404
    page = client.get("/app/projetos").get_data(as_text=True)
    assert "Projeto A" in page and "Projeto B" not in page
    companies = client.get("/conta/empresas").get_data(as_text=True)
    assert "Empresa B" not in companies


def test_convite_aceito_so_vincula_a_empresa_do_convite(client, app, tenants):
    """Aceitar convite da A não dá acesso à B, mesmo forjando company_id na sessão."""
    import re

    from app.services.email import outbox

    a, b = tenants
    login(client, app, a.owner_email)
    post(client, app, "/app/usuarios/convidar", {"email": "nova@x.com", "role": "operator"})
    token = re.search(r"/convite/([A-Za-z0-9_-]+)", outbox(app)[-1].text).group(1)
    guest = app.test_client()
    post(guest, app, f"/convite/{token}", {"name": "Nova", "password": "senha-forte-nova", "password_confirm": "senha-forte-nova"})
    assert "Projeto A" in guest.get("/app/projetos").get_data(as_text=True)
    with guest.session_transaction() as sess:
        sess["company_id"] = str(b.company_id)
    assert guest.get(f"/app/projetos/{b.project_id}").status_code == 404
    assert "Projeto B" not in guest.get("/app/projetos").get_data(as_text=True)

# ---------------------------------------------------------------- Fase 9: API pública (atrás de FEATURE_PUBLIC_API)


def test_fase9_revogar_token_de_outra_empresa_responde_404_e_nada_muda(app_factory):
    from app.models import ApiToken, Company
    from app.services import api_tokens as tokens
    from tests.conftest import make_tenant

    app = app_factory({"FEATURE_PUBLIC_API": True})
    with app.app_context():
        a, b = make_tenant("A", plan="empresa"), make_tenant("B", plan="empresa")
        company_b = db.session.get(Company, b.company_id)
        created = tokens.create_token(company_b, name="ERP B", scopes=["read:projects"], expires_in_days=30, user_id=None)
        db.session.commit()
        token_id, prefix = created.token.id, created.token.token_prefix
    client = app.test_client()
    login(client, app, a.owner_email)
    assert post(client, app, f"/app/integracoes/api/{token_id}/revogar").status_code == 404
    assert post(client, app, "/app/integracoes/api/nao-e-uuid/revogar").status_code == 404
    page = client.get("/app/integracoes/api").get_data(as_text=True)
    assert "ERP B" not in page and prefix not in page
    with app.app_context():
        assert db.session.get(ApiToken, token_id).revoked_at is None


# ---------------------------------------------------------------- Fase 7: API com a flag ligada
# Toda rota <uuid:> da API: token de A pedindo id de B → 404 (problem+json) e B intacto; o
# mesmo id da própria empresa passa do 404 (200 ou 501 dos stubs reservados).

ROUTES_API = [
    ("GET", "/api/v1/projects/{id}", "project_id", None),
    ("GET", "/api/v1/projects/{id}/summary", "project_id", None),
    ("GET", "/api/v1/projects/{id}/events", "project_id", None),
    ("POST", "/api/v1/activities/{id}/progress", "activity_id", {"delta": 1}),
]
# Tela de tokens: coberta por test_fase9_revogar_token_de_outra_empresa_responde_404_e_nada_muda.
ROUTES_API_UI = [("POST", "/app/integracoes/api/{id}/revogar", "token_id", None)]


@pytest.fixture()
def api_ab(app_factory):
    from app.models import Company
    from app.services import api_tokens as tokens
    from tests.conftest import make_tenant

    app = app_factory({"FEATURE_PUBLIC_API": True})
    with app.app_context():
        a, b = make_tenant("A", plan="empresa"), make_tenant("B", plan="empresa")
        created = tokens.create_token(
            db.session.get(Company, a.company_id), name="ERP A", scopes=["read:projects", "write:progress"],
            expires_in_days=30, user_id=None,
        )
        db.session.commit()
    return app, a, b, created.raw


def _api_call(client, method, url, raw, data):
    headers = {"Authorization": f"Bearer {raw}", "If-Match": '"1"'}
    if method == "GET":
        return client.get(url, headers=headers)
    return client.post(url, headers=headers, json=data)


@pytest.mark.parametrize("method,template,field,data", ROUTES_API)
def test_api_recurso_de_outra_empresa_responde_404(api_ab, method, template, field, data):
    app, a, b, raw = api_ab
    response = _api_call(app.test_client(), method, template.format(id=getattr(b, field)), raw, data)
    assert response.status_code == 404
    assert "Projeto B" not in response.get_data(as_text=True)
    with app.app_context():
        activity = db.session.get(Activity, b.activity_id)
        assert activity.units_done == 0 and activity.version == 1


@pytest.mark.parametrize("method,template,field,data", ROUTES_API)
def test_api_mesma_rota_na_propria_empresa_passa_do_404(api_ab, method, template, field, data):
    app, a, _, raw = api_ab
    response = _api_call(app.test_client(), method, template.format(id=getattr(a, field)), raw, data)
    assert response.status_code in (200, 201, 501)


# ---------------------------------------------------------------- Fase 7: LGPD (sem <uuid:>; empresa da sessão)


def test_lgpd_exportacao_so_tem_dados_da_propria_empresa(client, app, tenants):
    import io
    import zipfile

    a, b = tenants
    login(client, app, a.owner_email)
    response = post(client, app, "/app/privacidade/exportar")
    assert response.status_code == 200 and response.mimetype == "application/zip"
    content = ""
    with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
        for name in zf.namelist():
            content += zf.read(name).decode("utf-8")
    assert "Projeto A" in content and str(a.company_id) in content and a.operator_email in content
    assert "Projeto B" not in content and "Empresa B" not in content
    assert str(b.company_id) not in content and str(b.project_id) not in content and b.operator_email not in content


def test_lgpd_pedido_de_exclusao_so_afeta_a_empresa_da_sessao(client, app, tenants):
    from app.models import Company
    from tests.conftest import PASSWORD

    a, b = tenants
    login(client, app, a.owner_email)
    with client.session_transaction() as sess:
        sess["company_id"] = str(b.company_id)  # forjado: sem vínculo com B → volta para A
    response = post(client, app, "/app/privacidade/excluir", {"company_name": "Empresa B", "password": PASSWORD})
    assert response.status_code == 400  # o nome digitado não é o da empresa da sessão (A)
    response = post(client, app, "/app/privacidade/excluir", {"company_name": "Empresa A", "password": PASSWORD})
    assert response.status_code == 303
    with app.app_context():
        assert db.session.get(Company, a.company_id).deletion_requested_at is not None
        assert db.session.get(Company, b.company_id).deletion_requested_at is None

# ---------------------------------------------------------------- Fase 8: assinatura


def _billing_setup(app_factory):
    from tests.conftest import make_tenant
    from tests.test_billing import WEBHOOK_TOKEN

    app = app_factory({"ASAAS_WEBHOOK_TOKEN": WEBHOOK_TOKEN, "BILLING_PROVIDER": "fake"})
    with app.app_context():
        tenants = make_tenant("A"), make_tenant("B")
    return app, tenants


def test_fase8_assinatura_e_faturas_so_da_propria_empresa(app_factory):
    """Rotas de cobrança não levam id: a empresa vem da sessão. A vê só as faturas de A;
    cancelar ou trocar plano numa empresa não toca na outra."""
    from tests.test_billing import fake, pay, sub_state, subscribe

    app, (a, b) = _billing_setup(app_factory)
    client_a, client_b = app.test_client(), app.test_client()
    subscribe(client_b, app, b)
    pay(client_b, app, b)
    subscribe(client_a, app, a, plan="essencial")
    pid_b = fake(app).payments_of(sub_state(app, b.company_id)["provider_subscription_id"])[0]
    pid_a = fake(app).payments_of(sub_state(app, a.company_id)["provider_subscription_id"])[0]
    for url in ("/app/assinatura", "/app/assinatura/faturas"):
        page = client_a.get(url).get_data(as_text=True)
        assert pid_a in page and pid_b not in page, url
        assert "Empresa B" not in page
    before_b = sub_state(app, b.company_id)
    assert post(client_a, app, "/app/assinatura/cancelar").status_code == 303
    assert sub_state(app, a.company_id)["status"] == "canceled"
    assert sub_state(app, b.company_id) == before_b
    before_a = sub_state(app, a.company_id)
    assert post(client_b, app, "/app/assinatura/planos/essencial").status_code == 302
    assert sub_state(app, a.company_id) == before_a and sub_state(app, b.company_id)["pending_plan"] == "essencial"


def test_fase8_webhook_de_b_so_altera_b(app_factory):
    from app.models import WebhookEvent
    from tests.test_billing import fake, hook, sub_state, subscribe

    app, (a, b) = _billing_setup(app_factory)
    client_a, client_b = app.test_client(), app.test_client()
    subscribe(client_a, app, a)
    subscribe(client_b, app, b)
    before_a = sub_state(app, a.company_id)
    provider = fake(app)
    pid_b = provider.payments_of(sub_state(app, b.company_id)["provider_subscription_id"])[0]
    provider.set_payment_status(pid_b, "confirmed")
    assert hook(client_a, provider.webhook("PAYMENT_CONFIRMED", payment_id=pid_b)).status_code == 200
    assert sub_state(app, b.company_id)["status"] == "active"
    assert sub_state(app, a.company_id) == before_a
    with app.app_context():
        assert db.session.query(WebhookEvent).one().company_id == b.company_id


@pytest.mark.parametrize("url", ["/app/assinatura", "/app/assinatura/faturas", "/app/assinatura/planos", "/app/assinatura/cobranca"])
def test_fase8_cobranca_negada_a_supervisor_e_operador(app, tenants, url):
    a, _ = tenants
    for email in (a.supervisor_email, a.operator_email):
        other = app.test_client()
        login(other, app, email)
        assert other.get(url).status_code == 403
        assert post(other, app, "/app/assinatura/cancelar").status_code == 403


# ================================================================ Etapa D — colaboração
# Mesmo contrato: owner de A pedindo recurso de B → 404 e nada muda em B (nem auditoria nem
# eventos); na própria empresa a rota funciona. ``data`` pode ser função do Tenant (ids reais).

ROUTES_ETAPA_D = [
    ("POST", "/app/atividades/{id}/responsavel", "activity_id", lambda t: {"assignee_id": str(t.owner_id)}),
    ("GET", "/app/projetos/{id}/pessoas", "project_id", None),
    ("POST", "/app/projetos/{id}/etapas/ordem", "project_id", lambda t: {"order": [str(t.stage_id)]}),
    (
        "POST", "/app/atividades/{id}/posicionar", "activity_id",
        lambda t: {"stage_id": str(t.stage_id), "position": 1, "version": 1},
    ),
]


# Etapa E — painel do projeto (somente leitura). Dono de A pedindo o painel de B → 404, sem
# vazar nenhum número de B; na própria empresa → 200. Também com ?etapa= de outra empresa.
ROUTES_ETAPA_E = [
    ("GET", "/app/projetos/{id}/painel", "project_id", None),
]


@pytest.mark.parametrize("method,template,field,data", ROUTES_ETAPA_E)
def test_etapa_e_recurso_de_outra_empresa_responde_404(client, app, tenants, method, template, field, data):
    a, b = tenants
    with app.app_context():
        before = _snapshot(b.company_id)
    login(client, app, a.owner_email)
    for suffix in ("", f"?tabela=unidades&etapa={a.stage_id}", f"?etapa={b.stage_id}"):
        assert _call(client, app, method, template.format(id=getattr(b, field)) + suffix, data).status_code == 404
    with app.app_context():
        assert _snapshot(b.company_id) == before


@pytest.mark.parametrize("method,template,field,data", ROUTES_ETAPA_E)
def test_etapa_e_mesma_rota_funciona_na_propria_empresa(client, app, tenants, method, template, field, data):
    a, b = tenants
    login(client, app, a.owner_email)
    response = _call(client, app, method, template.format(id=getattr(a, field)), data)
    assert response.status_code == 200
    # nada da empresa B aparece no painel de A
    assert "Projeto B" not in response.get_data(as_text=True)


def _etapa_d_data(data, tenant):
    return data(tenant) if callable(data) else data


@pytest.mark.parametrize("method,template,field,data", ROUTES_ETAPA_D)
def test_etapa_d_recurso_de_outra_empresa_responde_404(client, app, tenants, method, template, field, data):
    a, b = tenants
    with app.app_context():
        before = _snapshot(b.company_id)
    login(client, app, a.owner_email)
    # Dados com ids da PRÓPRIA empresa de quem ataca, e também com ids de B.
    for payload in (_etapa_d_data(data, a), _etapa_d_data(data, b)):
        response = _call(client, app, method, template.format(id=getattr(b, field)), payload)
        assert response.status_code == 404
    with app.app_context():
        assert _snapshot(b.company_id) == before
        assert db.session.get(Activity, b.activity_id).assignee_id is None


@pytest.mark.parametrize("method,template,field,data", ROUTES_ETAPA_D)
def test_etapa_d_mesma_rota_funciona_na_propria_empresa(client, app, tenants, method, template, field, data):
    a, _ = tenants
    login(client, app, a.owner_email)
    response = _call(client, app, method, template.format(id=getattr(a, field)), _etapa_d_data(data, a))
    assert response.status_code in (200, 302, 303)


def test_etapa_d_responsavel_de_outra_empresa_responde_404_e_nada_grava(client, app, tenants):
    """Atividade de A, pessoa de B: o id do formulário é resolvido na empresa da atividade."""
    a, b = tenants
    with app.app_context():
        before_a, before_b = _snapshot(a.company_id), _snapshot(b.company_id)
    login(client, app, a.owner_email)
    url = f"/app/atividades/{a.activity_id}/responsavel"
    for bad in (str(b.owner_id), str(b.operator_id), "nao-e-uuid", "00000000-0000-0000-0000-000000000000"):
        assert post(client, app, url, {"assignee_id": bad}).status_code == 404
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).assignee_id is None
        assert _snapshot(a.company_id) == before_a and _snapshot(b.company_id) == before_b


def test_etapa_d_arrastar_com_etapa_de_outra_empresa_responde_404_e_nada_grava(client, app, tenants):
    """Atividade/projeto de A com id de etapa de B no corpo: 404, nada muda nas duas empresas."""
    a, b = tenants
    with app.app_context():
        before_a, before_b = _snapshot(a.company_id), _snapshot(b.company_id)
    login(client, app, a.owner_email)
    move = f"/app/atividades/{a.activity_id}/posicionar"
    assert post(client, app, move, {"stage_id": str(b.stage_id), "position": 0, "version": 1}).status_code == 404
    order = f"/app/projetos/{a.project_id}/etapas/ordem"
    assert post(client, app, order, {"order": [str(b.stage_id)]}).status_code == 404
    assert post(client, app, order, {"order": [str(a.stage_id), str(b.stage_id)]}).status_code == 404
    with app.app_context():
        assert _snapshot(a.company_id) == before_a and _snapshot(b.company_id) == before_b


# ================================================================ Etapa F — aguardando peça
# Dono de A marcando etapa de B → 404 e nada muda em B (nem marca, nem versão, nem auditoria).

ROUTES_ETAPA_F = [
    (
        "POST", "/app/etapas/{id}/aguardando-peca", "stage_id",
        {"waiting": "y", "expected_on": "2026-10-20", "note": "Invasora", "version": 1},
    ),
]


@pytest.mark.parametrize("method,template,field,data", ROUTES_ETAPA_F)
def test_etapa_f_recurso_de_outra_empresa_responde_404(client, app, tenants, method, template, field, data):
    a, b = tenants
    with app.app_context():
        before = _snapshot(b.company_id)
    login(client, app, a.owner_email)
    assert _call(client, app, method, template.format(id=getattr(b, field)), data).status_code == 404
    with app.app_context():
        assert _snapshot(b.company_id) == before
        assert db.session.get(Stage, b.stage_id).waiting_part is False


@pytest.mark.parametrize("method,template,field,data", ROUTES_ETAPA_F)
def test_etapa_f_mesma_rota_funciona_na_propria_empresa(client, app, tenants, method, template, field, data):
    a, _ = tenants
    login(client, app, a.owner_email)
    assert _call(client, app, method, template.format(id=getattr(a, field)), data).status_code in (200, 302, 303)
    with app.app_context():
        assert db.session.get(Stage, a.stage_id).waiting_part is True


# Etapa F — rotas sem <uuid:> também ganham caso A/B: a lista de alertas e as preferências de
# e-mail só enxergam/alteram a empresa e o usuário da sessão.


def test_etapa_f_alertas_so_da_propria_empresa(client, app, tenants):
    from datetime import date, datetime, timezone

    from app.models import Alert

    a, b = tenants
    with app.app_context():
        for t in (a, b):
            db.session.add(Alert(company_id=t.company_id, kind="forecast_late", severity="danger",
                                 dedupe_key=f"forecast_late:{t.project_id}", day=date.today(), project_id=t.project_id,
                                 details={"atraso_du": 1, "previsao": "2026-10-20", "prazo": "2026-10-19"},
                                 created_at=datetime.now(timezone.utc)))
        db.session.commit()
    login(client, app, a.owner_email)
    page = client.get("/app/alertas").get_data(as_text=True)
    assert "Projeto A" in page and "Projeto B" not in page and str(b.project_id) not in page
    with client.session_transaction() as sess:
        sess["company_id"] = str(b.company_id)  # forjado: sem vínculo com B
    page = client.get("/app/alertas").get_data(as_text=True)
    assert "Projeto B" not in page


def test_etapa_f_preferencias_so_do_proprio_usuario(client, app, tenants):
    from app.models import User

    a, b = tenants
    login(client, app, a.owner_email)
    # Campos extras (ex.: id de outro usuário) são ignorados: só o usuário da sessão muda.
    assert post(client, app, "/conta/perfil/notificacoes", {"user_id": str(b.owner_id)}).status_code == 303
    with app.app_context():
        assert db.session.query(User).filter_by(email=a.owner_email).one().notify_alerts is False
        other = db.session.query(User).filter_by(email=b.owner_email).one()
        assert (other.notify_assignment, other.notify_alerts, other.notify_weekly) == (True, True, True)


# ================================================================ Etapa G — qualidade
# Bloco 1: evidências por atividade (comentários e fotos). Dono de A pedindo/alterando recurso
# de B → 404 e nada muda em B (linhas, objetos no armazenamento, auditoria); na própria
# empresa a rota funciona. A foto de B nunca é servida a A (nem a miniatura).

import io as _io_g  # noqa: E402

from app.models.quality import ActivityComment, ActivityPhoto  # noqa: E402
from tests import fotos as _fotos  # noqa: E402


class TenantG:
    """Tenant base + ids extras da Etapa G (atributos ausentes caem no Tenant base)."""

    def __init__(self, base, **extra):
        self.base = base
        self.__dict__.update(extra)

    def __getattr__(self, name):
        return getattr(self.base, name)


def _make_tenant_g(label: str) -> TenantG:
    from app.services import comments as comments_svc
    from app.services import photos as photos_svc

    base = make_tenant(label)
    activity = db.session.get(Activity, base.activity_id)
    comment = comments_svc.add_comment(activity, f"Comentário {label}", base.operator_id)
    photo = photos_svc.add_photo(activity, _fotos.jpeg(), base.operator_id, caption=f"Foto {label}")
    db.session.commit()
    return TenantG(base, comment_id=comment.id, photo_id=photo.id, photo_key=photo.object_key)


@pytest.fixture()
def tenants_g(app):
    with app.app_context():
        return _make_tenant_g("A"), _make_tenant_g("B")


def _photo_payload(_t):
    return {"photo": (_io_g.BytesIO(_fotos.jpeg()), "invasora.jpg")}


ROUTES_ETAPA_G = [
    ("GET", "/app/atividades/{id}/evidencias", "activity_id", None),
    ("POST", "/app/atividades/{id}/comentarios", "activity_id", {"body": "Invasor"}),
    ("POST", "/app/comentarios/{id}/apagar", "comment_id", {}),
    ("POST", "/app/atividades/{id}/fotos", "activity_id", _photo_payload),
    ("GET", "/app/fotos/{id}", "photo_id", None),
    ("POST", "/app/fotos/{id}/apagar", "photo_id", {}),
]


def _snapshot_g(app, t) -> dict:
    from app.services import storage as storage_mod

    with app.app_context():
        q = db.session.query
        try:
            stored = storage_mod.get_storage().get(t.photo_key)
        except storage_mod.ObjectNotFound:
            stored = None
        return {
            "base": _snapshot(t.company_id),
            "comments": sorted(c.body for c in q(ActivityComment).filter_by(company_id=t.company_id)),
            "photos": sorted(str(p.id) for p in q(ActivityPhoto).filter_by(company_id=t.company_id)),
            "object": stored,
        }


def _call_g(client, app, method, url, data, tenant):
    payload = data(tenant) if callable(data) else data
    if method == "GET":
        return client.get(url)
    return post(client, app, url, payload)


@pytest.mark.parametrize("method,template,field,data", ROUTES_ETAPA_G)
def test_etapa_g_recurso_de_outra_empresa_responde_404(client, app, tenants_g, method, template, field, data):
    a, b = tenants_g
    before = _snapshot_g(app, b)
    login(client, app, a.owner_email)
    response = _call_g(client, app, method, template.format(id=getattr(b, field)), data, a)
    assert response.status_code == 404
    assert b"Foto B" not in response.data and "Comentário B".encode() not in response.data
    assert _snapshot_g(app, b) == before
    if field == "photo_id":
        assert client.get(f"/app/fotos/{b.photo_id}?tamanho=mini").status_code == 404


@pytest.mark.parametrize("method,template,field,data", ROUTES_ETAPA_G)
def test_etapa_g_mesma_rota_funciona_na_propria_empresa(client, app, tenants_g, method, template, field, data):
    a, b = tenants_g
    before_b = _snapshot_g(app, b)
    login(client, app, a.owner_email)
    response = _call_g(client, app, method, template.format(id=getattr(a, field)), data, a)
    assert response.status_code in (200, 302, 303)
    assert _snapshot_g(app, b) == before_b


def test_etapa_g_evidencias_so_mostram_a_propria_empresa(client, app, tenants_g):
    a, b = tenants_g
    login(client, app, a.operator_email)
    html = client.get(f"/app/atividades/{a.activity_id}/evidencias").get_data(as_text=True)
    assert "Comentário A" in html and "Foto A" in html
    assert "Comentário B" not in html and "Foto B" not in html and str(b.photo_id) not in html
    # sessão com company_id forjado (sem vínculo com B) não dá acesso à foto de B
    with client.session_transaction() as sess:
        sess["company_id"] = str(b.company_id)
    assert client.get(f"/app/fotos/{b.photo_id}").status_code == 404
