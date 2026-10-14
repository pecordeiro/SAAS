"""Fase 6 — front-end: site público, lista/histórico com filtros, registro via HTMX, resumo,
configurações da empresa e assets com hash. Casos A/B para cada rota nova."""

from __future__ import annotations

import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.extensions import db
from app.models import Activity, Company, Holiday, Plan, Project
from app.services import projects as svc
from app.services import templates as tsvc
from tests.conftest import login, post

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------- site público


def test_paginas_publicas_tem_seo(client):
    for path, needle in (("/", "teste grátis"), ("/precos", "Preços"), ("/termos", "RASCUNHO".title()), ("/privacidade", "LGPD"), ("/contato", "@")):
        response = client.get(path)
        assert response.status_code == 200, path
        html = response.get_data(as_text=True)
        assert "<title>" in html and 'name="description"' in html and 'property="og:title"' in html, path
        assert 'rel="canonical"' in html, path
        assert needle.lower() in html.lower(), path


def test_documentos_legais_marcados_como_rascunho(client):
    for path in ("/termos", "/privacidade"):
        assert "Rascunho para revisão jurídica" in client.get(path).get_data(as_text=True)


def test_precos_vem_da_tabela_plans(client, app):
    with app.app_context():
        plan = db.session.query(Plan).filter_by(code="essencial").one()
        plan.price_cents = 12300
        db.session.commit()
    html = client.get("/precos").get_data(as_text=True)
    assert "123" in html and "Essencial" in html and "Profissional" in html and "Empresa" in html
    assert "Mais escolhido" in html


def test_sitemap_e_robots(client):
    xml = client.get("/sitemap.xml")
    assert xml.status_code == 200 and "xml" in xml.mimetype
    body = xml.get_data(as_text=True)
    for path in ("/precos", "/termos", "/privacidade", "/contato"):
        assert path in body
    robots = client.get("/robots.txt").get_data(as_text=True)
    assert "Disallow: /app/" in robots and "Sitemap:" in robots


def test_area_logada_nao_indexa(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    assert 'content="noindex' in client.get("/app/projetos").get_data(as_text=True)


# ---------------------------------------------------------------- assets


def test_manifesto_de_assets_em_dia():
    import subprocess
    import sys

    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_assets.py"), "--check"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_assets_com_hash_e_cache_longo(client):
    html = client.get("/").get_data(as_text=True)
    css = re.search(r'href="(/static/dist/site\.[0-9a-f]{10}\.css)"', html)
    js = re.search(r'src="(/static/dist/app\.[0-9a-f]{10}\.js)"', html)
    assert css and js
    response = client.get(css.group(1))
    assert response.status_code == 200
    assert "max-age=31536000" in response.headers["Cache-Control"]
    manifest = json.loads((ROOT / "app" / "static" / "dist" / "manifest.json").read_text())
    assert manifest["site.css"] in css.group(1)


# ---------------------------------------------------------------- lista de projetos


def test_lista_filtros_busca_e_exportar(client, app, tenants):
    a, _ = tenants
    with app.app_context():
        company = db.session.get(Company, a.company_id)
        svc_project = svc.create_project(
            company, name="Lote Raro", product="Bancada XYZ", quantity=3, start_date=None, due_date=None,
            people=1, hours_per_day=Decimal("8"),
            stages=[svc.NewStage("E", [svc.NewActivity("x", Decimal("5"))])],
        )
        db.session.commit()
    login(client, app, a.supervisor_email)
    html = client.get("/app/projetos?q=xyz").get_data(as_text=True)
    assert "Lote Raro" in html and "Projeto A" not in html
    assert "Lote Raro" not in client.get("/app/projetos?q=nada-aqui").get_data(as_text=True)
    assert "Nenhum projeto encontrado" in client.get("/app/projetos?q=nada-aqui").get_data(as_text=True)
    assert "Lote Raro" not in client.get("/app/projetos?status=concluidos").get_data(as_text=True)
    assert "Lote Raro" in client.get("/app/projetos?prazo=sem").get_data(as_text=True)
    csv = client.get("/app/projetos/exportar.csv?status=todos")
    assert csv.status_code == 200 and "Lote Raro" in csv.get_data(as_text=True)


def test_operador_nao_ve_nem_acessa_acoes_de_supervisor(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    html = client.get("/app/projetos").get_data(as_text=True)
    assert "Novo projeto" not in html and "Exportar" not in html
    detail = client.get(f"/app/projetos/{a.project_id}").get_data(as_text=True)
    assert "Exportar CSV" not in detail and "Arquivar projeto" not in detail and "Editar projeto" not in detail
    for path in ("/app/projetos/novo", "/app/projetos/exportar.csv", f"/app/projetos/{a.project_id}/exportar.csv", "/app/empresa", "/app/modelos"):
        assert client.get(path).status_code == 403, path


# ---------------------------------------------------------------- registro via HTMX


HX = {"HX-Request": "true"}


def _version(app, activity_id):
    with app.app_context():
        return db.session.get(Activity, activity_id).version


def test_registro_htmx_devolve_pedacos_oob(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    response = post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 3, "version": 1}, headers=HX)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "<html" not in html
    assert f'id="atividade-{a.activity_id}"' in html and 'hx-swap-oob="true"' in html
    assert f'id="etapa-resumo-{a.stage_id}"' in html and 'id="indicadores"' in html
    assert "+3 em Atividade 1 · 3 de 10" in html and 'id="toast-region"' in html
    assert _version(app, a.activity_id) == 2


def test_registro_sem_js_redireciona_e_funciona(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    response = post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 2, "version": 1})
    assert response.status_code == 303
    assert "+2 em Atividade 1 · 2 de 10" in client.get(response.headers["Location"]).get_data(as_text=True)


def test_conflito_409_mostra_valor_atual_e_pede_confirmacao(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    assert post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 4, "version": 1}).status_code == 303
    for headers in ({}, HX):
        response = post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 2, "version": 1}, headers=headers)
        assert response.status_code == 409
        html = response.get_data(as_text=True)
        assert "agora está em 4 de 10" in html
        assert "Confirmar e somar" in html and 'name="version" value="2"' in html
        assert 'name="delta"' in html and 'value="2"' in html
    assert _version(app, a.activity_id) == 2  # nada gravado no conflito
    # confirmar = reenviar com a versão atual
    assert post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 2, "version": 2}).status_code == 303
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).units_done == 6


def test_atualizacao_leve_do_detalhe(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    page = client.get(f"/app/projetos/{a.project_id}").get_data(as_text=True)
    assert f'data-refresh-url="/app/projetos/{a.project_id}/atualizar"' in page
    response = client.get(f"/app/projetos/{a.project_id}/atualizar", headers=HX)
    assert response.status_code == 200 and "no-store" in response.headers["Cache-Control"]
    assert 'id="indicadores"' in response.get_data(as_text=True)


def test_detalhe_prazo_em_dias_uteis(client, app, tenants):
    a, _ = tenants
    with app.app_context():
        project = db.session.get(Project, a.project_id)
        project.due_date = date(2099, 1, 30)
        project.start_date = date(2098, 12, 1)
        db.session.commit()
    login(client, app, a.operator_email)
    html = client.get(f"/app/projetos/{a.project_id}").get_data(as_text=True)
    assert "dias úteis" in html and "folga de" in html


# ---------------------------------------------------------------- histórico


def test_historico_paginado_filtros_e_de_para(client, app, tenants):
    a, b = tenants
    login(client, app, a.supervisor_email)
    for _ in range(3):
        ver = _version(app, a.activity_id)
        post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 1, "version": ver})
    html = client.get(f"/app/projetos/{a.project_id}/historico").get_data(as_text=True)
    assert "0 → 1 de 10" in html and "2 → 3 de 10" in html and "3 registros" in html
    only = client.get(f"/app/projetos/{a.project_id}/historico?atividade={a.activity_id}").get_data(as_text=True)
    assert "3 registros" in only
    general = client.get("/app/historico").get_data(as_text=True)
    assert "Projeto A" in general and "Projeto B" not in general


def test_historico_paginacao(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    with app.app_context():
        from app.models import ProgressEntry

        for _ in range(30):
            db.session.add(ProgressEntry(company_id=a.company_id, activity_id=a.activity_id, user_id=a.owner_id, delta=1))
        db.session.commit()
    page1 = client.get(f"/app/projetos/{a.project_id}/historico").get_data(as_text=True)
    assert "Mostrando 1–25 de 30" in page1
    page2 = client.get(f"/app/projetos/{a.project_id}/historico?page=2").get_data(as_text=True)
    assert "Mostrando 26–30 de 30" in page2


def test_historico_filtros_de_outra_empresa_404(client, app, tenants):
    a, b = tenants
    login(client, app, a.owner_email)
    assert client.get(f"/app/projetos/{a.project_id}/historico?atividade={b.activity_id}").status_code == 404
    assert client.get(f"/app/historico?projeto={b.project_id}").status_code == 404
    assert client.get(f"/app/historico?projeto={a.project_id}").status_code == 200


# ---------------------------------------------------------------- novo projeto + resumo


def _template(app, company_id, owner_id, name="Modelo"):
    with app.app_context():
        company = db.session.get(Company, company_id)
        template = tsvc.create_template(
            company, name, [svc.NewStage("Base", [svc.NewActivity("Corte", Decimal("60"))])], owner_id
        )
        db.session.commit()
        return template.id


def test_resumo_calculado_do_novo_projeto(client, app, tenants):
    a, b = tenants
    tid = _template(app, a.company_id, a.owner_id)
    login(client, app, a.supervisor_email)
    response = client.get(f"/app/projetos/novo/resumo?template_id={tid}&quantity=10&people=2&hours_per_day=8&due_date=2099-01-30")
    html = response.get_data(as_text=True)
    assert response.status_code == 200 and "10 h" in html and "Cabe no prazo" in html
    assert "Escolha um modelo" in client.get("/app/projetos/novo/resumo").get_data(as_text=True)
    assert "Informe quantidade" in client.get(f"/app/projetos/novo/resumo?template_id={tid}&quantity=abc").get_data(as_text=True)


def test_resumo_modelo_de_outra_empresa_404(client, app, tenants):
    a, b = tenants
    tid_b = _template(app, b.company_id, b.owner_id, "Segredo B")
    login(client, app, a.owner_email)
    assert client.get(f"/app/projetos/novo/resumo?template_id={tid_b}&quantity=1&people=1").status_code == 404
    login_op = client.get("/app/projetos/novo")
    assert "Segredo B" not in login_op.get_data(as_text=True)


def test_novo_projeto_com_produto(client, app, tenants):
    a, _ = tenants
    tid = _template(app, a.company_id, a.owner_id)
    login(client, app, a.supervisor_email)
    response = post(
        client, app, "/app/projetos/novo",
        {"name": "Lote P", "product": "Painel PC-4", "quantity": 4, "people": 1, "hours_per_day": "8", "template_id": str(tid)},
    )
    assert response.status_code == 303
    assert "Painel PC-4" in client.get(response.headers["Location"]).get_data(as_text=True)


# ---------------------------------------------------------------- empresa


def test_empresa_so_proprietario(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    assert client.get("/app/empresa").status_code == 403
    assert post(client, app, "/app/empresa", {"name": "X"}).status_code == 403


def test_empresa_salva_dados_e_valida_cnpj(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    base = {"name": "Metalúrgica Nova", "cnpj": "11.222.333/0001-81", "daily_hours": "7.5", "workdays": ["0", "1", "2", "3"]}
    assert post(client, app, "/app/empresa", base).status_code == 303
    with app.app_context():
        company = db.session.get(Company, a.company_id)
        assert company.name == "Metalúrgica Nova" and company.daily_hours == Decimal("7.5")
        assert company.workdays() == (0, 1, 2, 3) and company.cnpj == "11.222.333/0001-81"
    assert post(client, app, "/app/empresa", {**base, "cnpj": "11.222.333/0001-82"}).status_code == 400
    assert post(client, app, "/app/empresa", {**base, "workdays": []}).status_code == 400


def test_feriado_da_empresa_incluir_e_remover(client, app, tenants):
    a, b = tenants
    login(client, app, a.owner_email)
    assert post(client, app, "/app/empresa/feriados", {"day": "2099-12-24", "name": "Recesso"}).status_code == 303
    assert post(client, app, "/app/empresa/feriados", {"day": "2099-12-24", "name": "Repetido"}).status_code == 400
    assert "Recesso" in client.get("/app/empresa").get_data(as_text=True)
    with app.app_context():
        holiday = db.session.query(Holiday).filter_by(company_id=a.company_id).one()
        hid = holiday.id
    assert post(client, app, f"/app/empresa/feriados/{hid}/remover").status_code == 303
    with app.app_context():
        assert db.session.query(Holiday).filter_by(company_id=a.company_id).count() == 0


def test_feriado_de_b_e_nacional_nao_removiveis_por_a(client, app, tenants):
    a, b = tenants
    with app.app_context():
        h_b = Holiday(company_id=b.company_id, day=date(2099, 5, 5), name="B")
        h_nat = Holiday(company_id=None, day=date(2099, 9, 7), name="Nacional")
        db.session.add_all([h_b, h_nat])
        db.session.commit()
        ids = (h_b.id, h_nat.id)
    login(client, app, a.owner_email)
    for hid in ids:
        assert post(client, app, f"/app/empresa/feriados/{hid}/remover").status_code == 404
    with app.app_context():
        assert db.session.query(Holiday).count() == 2


# ---------------------------------------------------------------- editor de modelo (linhas)


ROWS_FORM = {
    "name": "Modelo X", "description": "",
    "stages-0-name": "Corte", "stages-0-activities": "Serra; 10",
    "stages-1-name": "Solda", "stages-1-activities": "Ponto; 5",
}


def test_editor_linhas_htmx_adiciona_remove_e_move(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    html = post(client, app, "/app/modelos/linhas", {**ROWS_FORM, "acao": "add"}, headers=HX).get_data(as_text=True)
    assert "<html" not in html and 'id="etapas-lista"' in html and "Etapa 3" in html
    assert 'value="Corte"' in html and "Serra; 10" in html  # campos preservados
    moved = post(client, app, "/app/modelos/linhas", {**ROWS_FORM, "acao": "up-1"}, headers=HX).get_data(as_text=True)
    assert moved.index("Solda") < moved.index("Corte")
    removed = post(client, app, "/app/modelos/linhas", {**ROWS_FORM, "acao": "remove-0"}, headers=HX).get_data(as_text=True)
    assert "Corte" not in removed and "Solda" in removed and "Etapa 2" not in removed


def test_editor_linhas_sem_js_devolve_pagina_inteira_sem_gravar(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    response = post(client, app, "/app/modelos/linhas", {**ROWS_FORM, "acao": "add"})
    assert response.status_code == 200 and "app-sidebar" in response.get_data(as_text=True)
    with app.app_context():
        from app.models import Template

        assert db.session.query(Template).count() == 0


def test_editor_linhas_modelo_de_outra_empresa_404(client, app, tenants):
    a, b = tenants
    tid_b = _template(app, b.company_id, b.owner_id, "Segredo B")
    login(client, app, a.owner_email)
    assert post(client, app, f"/app/modelos/{tid_b}/linhas", {**ROWS_FORM, "acao": "add"}).status_code == 404
    tid_a = _template(app, a.company_id, a.owner_id, "Meu")
    assert post(client, app, f"/app/modelos/{tid_a}/linhas", {**ROWS_FORM, "acao": "add"}, headers=HX).status_code == 200


def test_previa_do_registro_vem_do_servidor(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    url = f"/app/atividades/{a.activity_id}/previa"
    assert client.get(url + "?delta=3").get_data(as_text=True) == "+3 (→ 3 de 10)"
    assert "faltam só 10" in client.get(url + "?delta=11").get_data(as_text=True)
    assert client.get(url + "?delta=abc").get_data(as_text=True) == ""
    html = client.get(f"/app/projetos/{a.project_id}").get_data(as_text=True)
    assert f'hx-get="{url}"' in html
