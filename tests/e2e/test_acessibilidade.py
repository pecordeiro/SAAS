"""WCAG 2.1 AA com axe-core nas telas públicas e logadas (claro e escuro, 375 e 1280 px).

Precisa do axe-core local: E2E_AXE_JS=/caminho/axe.min.js (ex.: `npm pack axe-core@4.10.2`).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.conftest import PASSWORD
from tests.e2e.conftest import ui_login

pytestmark = pytest.mark.e2e

AXE = os.environ.get("E2E_AXE_JS", "")
TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"]
PUBLIC = ["/", "/precos", "/termos", "/privacidade", "/contato", "/entrar", "/cadastro"]


def _violations(page) -> list[str]:
    page.add_script_tag(content=Path(AXE).read_text(encoding="utf-8"))
    result = page.evaluate("axe.run(document, {runOnly: {type: 'tag', values: %s}})" % TAGS)
    return [f"{v['id']} ({v['impact']}) {[n['html'][:90] for n in v['nodes']][:2]}" for v in result["violations"]]


@pytest.mark.skipif(not AXE or not Path(AXE).exists(), reason="defina E2E_AXE_JS com o axe.min.js")
@pytest.mark.parametrize("scheme", ["light", "dark"])
@pytest.mark.parametrize("width", [375, 1280])
def test_axe_sem_violacoes(live, browser, make_page, tenant_a, width, scheme):
    tenant, _ = tenant_a
    context = browser.new_context(viewport={"width": width, "height": 900}, color_scheme=scheme, locale="pt-BR", bypass_csp=True)
    page = make_page(context=context)
    problems: dict[str, list[str]] = {}
    for path in PUBLIC:
        page.goto(live.base + path)
        found = _violations(page)
        if found:
            problems[path] = found
    ui_login(page, live.base, tenant.owner_email, PASSWORD)
    logged = [
        "/app/projetos", f"/app/projetos/{tenant.project_id}", f"/app/projetos/{tenant.project_id}/historico",
        "/app/historico", "/app/projetos/novo", "/app/modelos", "/app/modelos/novo", "/app/usuarios", "/app/empresa",
        "/app/importar", "/conta/perfil",
    ]
    for path in logged:
        page.goto(live.base + path)
        found = _violations(page)
        if found:
            problems[path] = found
    context.close()
    assert not problems, problems
