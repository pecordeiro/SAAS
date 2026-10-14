"""Fluxos de navegador da Fase 6 (Playwright). Rodar: RUN_E2E=1 python -m pytest tests/e2e -q"""

from __future__ import annotations

import re
import uuid

import pytest
from playwright.sync_api import expect

from app.services.email import outbox
from tests.conftest import PASSWORD
from tests.e2e.conftest import ui_login

pytestmark = pytest.mark.e2e

VIEWPORTS = [pytest.param(375, 800, id="375px"), pytest.param(1280, 900, id="1280px")]


def _confirm_link(live, email: str) -> str:
    for message in reversed(outbox(live.app)):
        if message.to == email:
            return re.search(r"Confirmar e-mail: (\S+)", message.text).group(1)
    raise AssertionError("e-mail de confirmação não encontrado no outbox")


def _register(page, activity_name: str, mobile: bool):
    row = page.locator("li.activity", has_text=activity_name).first
    if mobile:
        row.locator("a.activity__open").click()  # toque 1: abre a folha
    row.locator(".register__submit:visible").click()  # toque 2: Registrar +1


@pytest.mark.parametrize("width,height", VIEWPORTS)
def test_fluxo_completo(live, make_page, width, height):
    """cadastro → confirmar e-mail → modelo → projeto → registrar peças → histórico → exportar."""
    page = make_page(width, height)
    base = live.base
    mobile = width < 768
    email = f"dono.{uuid.uuid4().hex[:8]}@exemplo.com"

    # cadastro
    page.goto(f"{base}/cadastro")
    page.fill("#company_name", "Metalúrgica E2E")
    page.fill("#name", "Ana E2E")
    page.fill("#email", email)
    page.fill("#password", PASSWORD)
    page.fill("#password_confirm", PASSWORD)
    page.click("form button.btn--primary")
    expect(page.get_by_role("heading", name=re.compile("Confirme"))).to_be_visible()

    # confirmar e-mail pelo link do outbox
    page.goto(_confirm_link(live, email))
    page.get_by_role("button", name="Confirmar e-mail").click()
    ui_login(page, base, email, PASSWORD)
    expect(page.get_by_role("heading", name="Projetos")).to_be_visible()

    # modelo de etapas: adiciona uma etapa sem recarregar (HTMX)
    page.goto(f"{base}/app/modelos/novo")
    page.evaluate("window.__marcador = 'sem-recarregar'")
    page.fill("#name", "Modelo E2E")
    page.fill("#stages-0-name", "Corte")
    page.fill("#stages-0-activities", "Serra; 30\nFuração; 30")
    page.fill("#stages-1-name", "Solda")
    page.fill("#stages-1-activities", "Ponto; 60")
    page.get_by_role("button", name="Adicionar etapa").click()
    expect(page.get_by_text("Etapa 3", exact=True)).to_be_visible()
    assert page.evaluate("window.__marcador") == "sem-recarregar"
    page.get_by_role("button", name="Remover etapa 3").click()
    expect(page.get_by_text("Etapa 3", exact=True)).to_have_count(0)
    page.get_by_role("button", name="Criar modelo").click()
    expect(page.get_by_role("heading", name="Modelo E2E")).to_be_visible()

    # novo projeto a partir do modelo, com resumo calculado via HTMX
    page.goto(f"{base}/app/projetos/novo")
    page.fill("#name", "Lote E2E")
    page.fill("#product", "Equipamento CX-10")
    page.fill("#quantity", "10")
    page.fill("#people", "2")
    expect(page.locator("#resumo")).to_contain_text("Trabalho total")
    expect(page.locator("#resumo")).to_contain_text("Dias úteis")
    page.get_by_role("button", name="Criar projeto").click()
    expect(page.get_by_role("heading", name="Lote E2E")).to_be_visible()
    expect(page.get_by_text("Equipamento CX-10")).to_be_visible()
    project_url = page.url

    # registrar peças sem recarregar: etapa e indicadores mudam, toast avisa
    page.evaluate("window.__marcador = 'sem-recarregar'")
    expect(page.locator("#indicadores")).to_contain_text("0/10")
    _register(page, "Serra", mobile)
    expect(page.locator("#toast-region")).to_contain_text("+1 em Serra · 1 de 10")
    expect(page.locator("#indicadores")).to_contain_text("Progresso")
    expect(page.locator("li.activity", has_text="Serra").first).to_contain_text("1/10")
    assert page.evaluate("window.__marcador") == "sem-recarregar"
    expect(page).not_to_have_url(re.compile("#registrar-"))  # a folha fechou (hash trocado pelo JS)

    # histórico: "0 → 1 de 10"
    page.goto(project_url + "/historico")
    expect(page.get_by_text("0 → 1 de 10")).to_be_visible()

    # exportar (CSV)
    page.goto(project_url)
    page.locator("summary", has_text="Ações").click()
    with page.expect_download() as download:
        page.get_by_role("link", name="Exportar CSV").click()
    assert download.value.suggested_filename.endswith(".csv")


@pytest.mark.parametrize("width,height", VIEWPORTS)
def test_operador_sem_acoes_de_supervisor(live, make_page, tenant_a, width, height):
    tenant, _ = tenant_a
    page = make_page(width, height)
    ui_login(page, live.base, tenant.operator_email, PASSWORD)
    page.goto(f"{live.base}/app/projetos")
    expect(page.get_by_role("link", name=re.compile("Novo"))).to_have_count(0)
    expect(page.get_by_role("link", name="Exportar")).to_have_count(0)
    page.goto(f"{live.base}/app/projetos/{tenant.project_id}")
    expect(page.get_by_text("Arquivar projeto")).to_have_count(0)
    expect(page.get_by_text("Editar projeto")).to_have_count(0)
    for path in ("/app/projetos/novo", f"/app/projetos/{tenant.project_id}/exportar.csv", "/app/empresa", "/app/modelos"):
        response = page.goto(live.base + path)
        assert response.status == 403, path
    expect(page.get_by_text("Você não tem permissão")).to_be_visible()


def test_conflito_409_pede_confirmacao_no_navegador(live, make_page, tenant_a):
    tenant, _ = tenant_a
    page1 = make_page(1280, 900)
    ui_login(page1, live.base, tenant.supervisor_email, PASSWORD)
    page2 = make_page(1280, 900, context=page1.context)
    for page in (page1, page2):
        page.goto(f"{live.base}/app/projetos/{tenant.project_id}")
    # a outra pessoa registra 4 antes
    page1.fill(f"#registrar-{tenant.activity_id} .stepper__input", "4")
    page1.locator(f"#registrar-{tenant.activity_id} .register__submit").click()
    expect(page1.locator("#toast-region")).to_contain_text("4 de 10")
    # a página 2 está velha: ao enviar +2 recebe o valor atual e pede confirmação
    page2.fill(f"#registrar-{tenant.activity_id} .stepper__input", "2")
    page2.locator(f"#registrar-{tenant.activity_id} .register__submit").click()
    alert = page2.locator(f"#atividade-{tenant.activity_id} [role=alert]")
    expect(alert).to_contain_text("agora está em 4 de 10")
    confirm = page2.locator(f"#registrar-{tenant.activity_id} .register__submit")
    expect(confirm).to_contain_text("Confirmar e somar")
    confirm.click()
    expect(page2.locator("#toast-region")).to_contain_text("6 de 10")


def test_registro_sem_javascript(live, make_page, tenant_a):
    tenant, _ = tenant_a
    page = make_page(375, 800, js=False)
    ui_login(page, live.base, tenant.operator_email, PASSWORD)
    page.goto(f"{live.base}/app/projetos/{tenant.project_id}")
    row = page.locator("li.activity", has_text="Atividade 1").first
    row.locator("a.activity__open").click()  # âncora :target abre a folha
    page.wait_for_timeout(500)  # animação da folha; sem JS o Playwright não confirma "estável"
    row.locator(".register__submit:visible").click(force=True)
    expect(page.locator(".toast__message")).to_contain_text("+1 em Atividade 1 · 1 de 10")


def test_atualizacao_a_cada_30s_so_com_aba_visivel(live, make_page, tenant_a):
    from app.extensions import db
    from app.models import Activity

    tenant, _ = tenant_a
    page = make_page(1280, 900)
    page.clock.install()
    ui_login(page, live.base, tenant.supervisor_email, PASSWORD)
    page.goto(f"{live.base}/app/projetos/{tenant.project_id}")
    hits: list[str] = []
    page.on("request", lambda r: hits.append(r.url) if r.url.endswith("/atualizar") else None)
    with live.app.app_context():  # outra pessoa registra por fora
        activity = db.session.get(Activity, tenant.activity_id)
        activity.units_done = 5
        activity.version += 1
        db.session.commit()
    # aba oculta: nenhuma requisição
    page.evaluate("Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => 'hidden'})")
    page.clock.run_for(65_000)
    assert hits == []
    # aba visível: em até 30 s o painel se atualiza sozinho
    page.evaluate("Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => 'visible'})")
    page.clock.run_for(31_000)
    expect(page.locator(f"#atividade-{tenant.activity_id}").first).to_contain_text("5/10")
    assert len(hits) >= 1
