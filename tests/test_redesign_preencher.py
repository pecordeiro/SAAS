"""Redesign 2026-10-28: “Preencher etapas” separa Registrar produção (padrão) de Configurar etapas.
O modo só muda o que aparece; as rotas continuam checando o papel."""

from tests.conftest import login


def _page(client, app, email, query=""):
    resp = client.get("/app/preencher" + query)
    assert resp.status_code == 200
    return resp.get_data(as_text=True)


def test_registrar_e_o_padrao_e_traz_o_seletor_de_modo(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    html = _page(client, app, a.supervisor_email)
    assert 'data-modo="registrar"' in html
    assert "Registrar produção" in html and "Configurar etapas" in html
    # o total acumulado é o que se lança (não a quantidade a somar)
    assert "Peças prontas (total)" in html
    # tempos, peso e ações de configuração existem, mas marcados como do modo configurar
    assert 'class="num cfg-only">Tempo ideal (min por unidade)' in html
    assert 'class="etab__new cfg-only"' in html


def test_supervisor_abre_configurar(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    html = _page(client, app, a.supervisor_email, "?modo=configurar")
    assert 'data-modo="configurar"' in html
    assert 'id="nome-etapa"' in html  # o nome da etapa vira campo só aqui
    assert 'name="modo" value="configurar"' in html  # formulários voltam ao mesmo modo


def test_operador_nao_entra_em_configurar(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    html = _page(client, app, a.operator_email, "?modo=configurar")
    assert 'data-modo="registrar"' in html
    assert "Configurar etapas" not in html
    assert 'id="nome-etapa"' not in html
