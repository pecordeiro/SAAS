"""Schema da Fase 3: regra multiempresa no metadata, constraints, UNIQUE, CHECK e seeds."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app import rls
from app.extensions import db
from app.models import (
    Activity,
    Company,
    Holiday,
    Membership,
    Payment,
    Plan,
    Project,
    Stage,
    Subscription,
    User,
    WebhookEvent,
)
from app.services import projects as svc
from app.services import templates as templates_svc
from app.services.holidays import easter, holidays_for, national_holidays
from app.services.plans import PLAN_CATALOG, get_plan, seed_plans
from tests.conftest import requires_postgres

# Tabelas SEM company_id NOT NULL, cada uma com o motivo. Tabela nova sem company_id que não
# estiver aqui faz o teste falhar: ou ganha company_id, ou entra aqui com justificativa.
EXCEPTIONS = {
    "companies": "raiz do tenant: o próprio id é o company_id",
    "users": "identidade global; vínculo com empresas via memberships (N:N)",
    "password_resets": "token da conta do usuário (global), não da empresa",
    "email_confirmations": "token da conta do usuário (global), não da empresa",
    "mfa_recovery_codes": "segredo da conta do usuário (global), não da empresa",
    "plans": "catálogo de planos, igual para todos",
    "webhook_events": "caixa de entrada da plataforma: chega antes de saber a empresa",
    "holidays": "company_id NULL = feriado nacional compartilhado (tem índice por company_id)",
    "login_throttles": "bloqueio de login por conta/IP: chega antes de saber a empresa (Fase 5)",
    "platform_audit_logs": "auditoria da plataforma: sobrevive ao expurgo LGPD da empresa (Fase 7)",
}


def _tables():
    return db.metadata.sorted_tables


def _leading_columns(table) -> set[str]:
    """Primeira coluna de cada índice, UNIQUE e da PK."""
    firsts = set()
    for index in table.indexes:
        cols = list(index.columns)
        if cols:
            firsts.add(cols[0].name)
    for constraint in table.constraints:
        cols = list(getattr(constraint, "columns", []))
        if cols and constraint.__class__.__name__ in {"UniqueConstraint", "PrimaryKeyConstraint"}:
            firsts.add(cols[0].name)
    return firsts


def test_toda_tabela_de_cliente_tem_company_id_not_null_e_indice(app):
    with app.app_context():
        problems = []
        for table in _tables():
            if table.name in EXCEPTIONS:
                continue
            column = table.c.get("company_id")
            if column is None or column.nullable:
                problems.append(f"{table.name}: sem company_id NOT NULL")
                continue
            if "company_id" not in _leading_columns(table):
                problems.append(f"{table.name}: nenhum índice começa por company_id")
        assert problems == []


def test_excecoes_existem_e_continuam_sem_company_id_obrigatorio(app):
    with app.app_context():
        names = {t.name for t in _tables()}
        assert set(EXCEPTIONS) <= names, "exceção para tabela que não existe mais"
        for name in EXCEPTIONS:
            column = db.metadata.tables[name].c.get("company_id")
            assert column is None or column.nullable, f"{name} já tem company_id NOT NULL: tire das exceções"
        assert "company_id" in _leading_columns(db.metadata.tables["holidays"])


def test_lista_de_tabelas_com_rls_cobre_todo_dado_de_cliente(app):
    with app.app_context():
        tenant_tables = {
            t.name for t in _tables() if t.c.get("company_id") is not None and not t.c.company_id.nullable
        }
        assert set(rls.RLS_TABLES) == tenant_tables | {"holidays"}


@requires_postgres
def test_migration_criou_politica_em_toda_tabela_de_cliente(app):
    with app.app_context():
        info = rls.status(db.session.connection())
        for table in rls.RLS_TABLES:
            assert "tenant_isolation" in info[table]["policies"], table
        assert "memberships_own_user" in info["memberships"]["policies"]
        assert "holidays_national_read" in info["holidays"]["policies"]
        # Desligado por padrão (ADR-0003): só `flask rls enable` liga a cobrança.
        assert not any(info[t]["enabled"] for t in rls.RLS_TABLES)


# --- UNIQUE --------------------------------------------------------------------------


def _subscription(company: Company) -> Subscription:
    sub = Subscription(company_id=company.id, plan_id=get_plan("essencial").id, provider="fake", status="active")
    db.session.add(sub)
    db.session.flush()
    return sub


def _company(name: str = "Empresa X") -> Company:
    company = Company(name=name)
    db.session.add(company)
    db.session.flush()
    return company


def test_provider_payment_id_unico(app):
    with app.app_context():
        company = _company()
        sub = _subscription(company)
        payment = dict(company_id=company.id, subscription_id=sub.id, status="pending", value_cents=14900, due_date=date(2026, 11, 1))
        db.session.add(Payment(provider_payment_id="pay_123", **payment))
        db.session.commit()
        db.session.add(Payment(provider_payment_id="pay_123", **payment))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        assert db.session.query(Payment).count() == 1


def test_external_event_id_unico_impede_processar_duas_vezes(app):
    with app.app_context():
        db.session.add(WebhookEvent(provider="asaas", external_event_id="evt_1", type="PAYMENT_RECEIVED"))
        db.session.commit()
        db.session.add(WebhookEvent(provider="asaas", external_event_id="evt_1", type="PAYMENT_RECEIVED"))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        assert db.session.query(WebhookEvent).count() == 1


def test_uma_assinatura_por_empresa(app):
    with app.app_context():
        company = _company()
        _subscription(company)
        db.session.commit()
        db.session.add(Subscription(company_id=company.id, plan_id=get_plan("empresa").id, provider="fake", status="trialing"))
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_email_unico_sem_diferenciar_maiusculas(app):
    with app.app_context():
        db.session.add(User(email="maria@exemplo.com", name="Maria", password_hash="x"))
        db.session.commit()
        db.session.add(User(email="Maria@Exemplo.com", name="Outra", password_hash="x"))
        with pytest.raises(IntegrityError):
            db.session.commit()


# --- CHECK ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(lambda c, u: Membership(company_id=c.id, user_id=u.id, role="admin"), id="papel-invalido"),
        pytest.param(lambda c, u: Project(company_id=c.id, name="P", quantity=-1), id="quantidade-negativa"),
        pytest.param(lambda c, u: Project(company_id=c.id, name="P", quantity=1, status="perdido"), id="status-projeto"),
        pytest.param(
            lambda c, u: Subscription(company_id=c.id, plan_id=get_plan("essencial").id, provider="fake", status="pago"),
            id="status-assinatura",
        ),
        pytest.param(
            lambda c, u: Subscription(company_id=c.id, plan_id=get_plan("essencial").id, provider="pix", status="active"),
            id="provedor",
        ),
        pytest.param(lambda c, u: WebhookEvent(provider="asaas", external_event_id="e", type="t", status="?"), id="status-webhook"),
        pytest.param(lambda c, u: Plan(code="x", name="X", price_cents=-1, features={}), id="preco-negativo"),
    ],
)
def test_check_constraints_barram_valores_invalidos(app, build):
    with app.app_context():
        company = _company()
        user = User(email="check@exemplo.com", name="C", password_hash="x")
        db.session.add(user)
        db.session.flush()
        db.session.add(build(company, user))
        with pytest.raises(IntegrityError):
            db.session.flush()


def test_check_pecas_concluidas_nao_negativas(app, tenants):
    a, _ = tenants
    with app.app_context():
        activity = db.session.get(Activity, a.activity_id)
        activity.units_done = -1
        with pytest.raises(IntegrityError):
            db.session.commit()


# --- Seeds ---------------------------------------------------------------------------


def test_planos_do_catalogo(app):
    with app.app_context():
        plans = {p.code: p for p in db.session.execute(select(Plan)).scalars()}
        assert set(plans) == {"essencial", "profissional", "empresa", "implantacao"}
        assert (plans["essencial"].price_cents, plans["essencial"].max_projects, plans["essencial"].max_users) == (24990, 3, 3)
        assert (plans["profissional"].price_cents, plans["profissional"].max_projects, plans["profissional"].max_users) == (49700, 10, 20)
        assert (plans["empresa"].price_cents, plans["empresa"].max_projects, plans["empresa"].max_users) == (99700, None, None)
        assert (plans["implantacao"].price_cents, plans["implantacao"].max_projects, plans["implantacao"].max_users) == (None, None, None)
        assert plans["empresa"].features == {"mfa_required": True, "api": True, "visual_custom": True, "implantacao": False}
        assert plans["implantacao"].features == {"mfa_required": True, "api": True, "visual_custom": True, "implantacao": True}
        assert plans["essencial"].features["api"] is False and plans["profissional"].features["visual_custom"] is False
        # Mesmos ids em todo ambiente (migration e seed-plans usam uuid5 do código).
        assert {p.code: p.id for p in plans.values()} == {s.code: s.id for s in PLAN_CATALOG}


def test_seed_plans_idempotente_e_corrige_valores(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["seed-plans"])
    assert result.exit_code == 0 and "0 criado(s), 0 atualizado(s)" in result.output
    with app.app_context():
        get_plan("essencial").price_cents = 1
        db.session.commit()
    result = runner.invoke(args=["seed-plans"])
    assert "1 atualizado(s)" in result.output
    with app.app_context():
        assert get_plan("essencial").price_cents == 24990
        assert db.session.query(Plan).count() == 4
        assert seed_plans() == (0, 0)


# --- Feriados ------------------------------------------------------------------------


def test_feriados_nacionais_calculados():
    assert easter(2026) == date(2026, 4, 5)
    assert easter(2027) == date(2027, 3, 28)
    dias = dict(national_holidays(2026))
    assert dias[date(2026, 4, 3)] == "Sexta-feira da Paixão"
    assert date(2026, 11, 20) in dias and date(2026, 12, 25) in dias
    assert len(dias) == 10
    assert date(2023, 11, 20) not in dict(national_holidays(2023))


def test_feriado_nacional_vale_para_todas_e_o_da_empresa_so_para_ela(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["seed-holidays", "--de", "2026", "--ate", "2027"])
    assert result.exit_code == 0 and "20 criado(s)" in result.output
    again = runner.invoke(args=["seed-holidays", "--de", "2026", "--ate", "2027"])
    assert "0 criado(s)" in again.output  # idempotente
    with app.app_context():
        a, b = _company("A"), _company("B")
        db.session.add(Holiday(company_id=a.id, day=date(2026, 12, 24), name="Recesso A"))
        db.session.commit()
        dias_a, dias_b = set(holidays_for(a.id)), set(holidays_for(b.id))
        assert date(2026, 12, 25) in dias_a and date(2026, 12, 25) in dias_b
        assert date(2026, 12, 24) in dias_a and date(2026, 12, 24) not in dias_b
        # Nacional duplicado é barrado pelo índice único parcial.
        db.session.add(Holiday(company_id=None, day=date(2026, 12, 25), name="Natal de novo"))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        # A empresa pode marcar o mesmo dia como feriado próprio (não colide com o nacional).
        db.session.add(Holiday(company_id=a.id, day=date(2026, 12, 25), name="Natal (empresa)"))
        db.session.commit()


# --- Modelos de etapas (snapshot) ------------------------------------------------------


def test_projeto_copia_etapas_da_versao_do_modelo(app):
    with app.app_context():
        company = _company()
        template = templates_svc.create_template(
            company,
            "Modelo",
            [svc.NewStage(name="Etapa 1", activities=[svc.NewActivity(name="A1", ideal_minutes=Decimal("10"))])],
        )
        v1 = template.current_version
        assert v1.number == 1
        project = svc.create_project(
            company,
            name="Projeto",
            quantity=5,
            start_date=None,
            due_date=None,
            people=1,
            hours_per_day=Decimal("8"),
            stages=templates_svc.stages_from_version(v1),
            template_version_id=v1.id,
        )
        db.session.commit()
        v2 = templates_svc.add_version(
            template, [svc.NewStage(name="Etapa nova", activities=[svc.NewActivity(name="B", ideal_minutes=Decimal("5"))])]
        )
        template.current_version_id = v2.id
        db.session.commit()
        assert v2.number == 2
        db.session.expire_all()
        project = db.session.get(Project, project.id)
        assert project.template_version_id == v1.id
        assert [s.name for s in db.session.query(Stage).filter_by(project_id=project.id)] == ["Etapa 1"]
        # Versões duplicadas do mesmo modelo são barradas.
        from app.models import TemplateVersion

        db.session.add(TemplateVersion(company_id=company.id, template_id=template.id, number=2))
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_seed_demo_cria_modelo_projeto_do_modelo_e_trial(app, monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "senha-demo-teste")
    result = app.test_cli_runner().invoke(args=["seed-demo"])
    assert result.exit_code == 0, result.output
    with app.app_context():
        for company in db.session.query(Company).all():
            projects = db.session.execute(select(Project).where(Project.company_id == company.id)).scalars().all()
            assert len(projects) == 2
            assert all(p.template_version_id is not None for p in projects)
            sub = db.session.execute(select(Subscription).where(Subscription.company_id == company.id)).scalar_one()
            assert sub.status == "trialing" and sub.plan.code == "profissional"
            trial_end = sub.trial_ends_at if sub.trial_ends_at.tzinfo else sub.trial_ends_at.replace(tzinfo=timezone.utc)
            assert trial_end > datetime.now(timezone.utc) + timedelta(days=13)
        assert db.session.execute(select(Holiday).where(Holiday.company_id.is_(None))).first() is not None


@requires_postgres
def test_set_local_nao_vaza_para_a_proxima_transacao(app):
    with app.app_context():
        conn = db.session.connection()
        conn.execute(text("SELECT set_config('app.company_id', 'x', true)"))
        db.session.commit()
        value = db.session.execute(text("SELECT current_setting('app.company_id', true)")).scalar()
        assert value in ("", None)


def test_cli_rls(app):
    runner = app.test_cli_runner()
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        result = runner.invoke(args=["rls", "status"])
        assert result.exit_code != 0 and "só existe no PostgreSQL" in result.output
        return
    # Sem RLS_ENABLED o comando se recusa a ligar (o app ficaria sem empresa no banco).
    result = runner.invoke(args=["rls", "enable"])
    assert result.exit_code != 0 and "RLS_ENABLED=1" in result.output
    result = runner.invoke(args=["rls", "status"])
    assert result.exit_code == 0 and "projects" in result.output and "tenant_isolation" in result.output
    app.config["RLS_ENABLED"] = True
    try:
        assert runner.invoke(args=["rls", "enable"]).exit_code == 0
        with app.app_context():
            assert rls.status(db.session.connection())["projects"]["forced"] is True
    finally:
        assert runner.invoke(args=["rls", "disable"]).exit_code == 0
    with app.app_context():
        assert rls.status(db.session.connection())["projects"]["enabled"] is False
