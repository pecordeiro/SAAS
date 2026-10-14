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


def test_toda_rota_com_uuid_tem_caso_de_isolamento(app):
    cobertas = {template.replace("{id}", "") for _, template, _, _ in ROUTES + FASE4_ROUTES + ROUTES_CONTAS + ROUTES_FASE6_EXTRA}
    for rule in app.url_map.iter_rules():
        if "<uuid:" not in rule.rule:
            continue
        sem_parametro = rule.rule.split("<")[0] + rule.rule.split(">", 1)[1]
        assert sem_parametro in cobertas, f"rota {rule.rule} sem teste de isolamento A/B"


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
        "stages": sorted((s.name, s.position, s.archived_at is None) for s in q(Stage).filter_by(company_id=company_id)),
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

    app = app_factory({"FEATURE_PUBLIC_API": True, "DEFAULT_TRIAL_PLAN": "empresa"})
    with app.app_context():
        a, b = make_tenant("A"), make_tenant("B")
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
