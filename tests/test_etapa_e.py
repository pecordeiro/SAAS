"""Etapa E — painel completo do projeto: KPIs, gráficos SVG no servidor e tabela de etapas.

Cálculo só em calc.py (paridade com a planilha em tests/test_calc.py); aqui: a tela imprime
o que o servidor calculou, é acessível (título/desc nos SVG, texto ao lado da cor) e segura
(sem script nem estilo inline por causa da CSP, sem CDN)."""

from __future__ import annotations

import re
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.extensions import db
from app.models import Activity, Project
from app.services import calc, dashboard
from app.services import projects as svc
from tests.conftest import login, text_of

TEMPOS = [Decimal("10"), Decimal("30")]


def _projeto_rico(app, tenant):
    """Projeto de A com 5 etapas de pesos diferentes e progresso variado (qtd 10)."""
    with app.app_context():
        project = db.session.get(Project, tenant.project_id)
        stages = svc.active_stages(project)
        # etapa 1 (já existe: 10 + 30 min): 10/10 e 10/10 → concluída
        for a in svc.active_activities(stages[0]):
            a.units_done = 10
        novas = [
            ("Pintura", [Decimal("60")], 4),
            ("Acabamento", [Decimal("20"), Decimal("20")], 0),
            ("Embalagem", [Decimal("5")], 0),
            ("Sem tempo", [Decimal("0")], 0),
        ]
        for nome, tempos, feitas in novas:
            st = svc.add_stage(project, nome, [svc.NewActivity(name=f"{nome} {i}", ideal_minutes=t) for i, t in enumerate(tempos)])
            for a in svc.active_activities(st):
                a.units_done = feitas
        db.session.commit()
        return project.id


def _painel(client, tenant, query=""):
    return client.get(f"/app/projetos/{tenant.project_id}/painel{query}")


# ---------------------------------------------------------------- tela


def test_painel_mostra_kpis_graficos_e_tabela(client, app, tenants):
    a, _ = tenants
    _projeto_rico(app, a)
    login(client, app, a.operator_email)
    response = _painel(client, a)
    assert response.status_code == 200
    page = text_of(response)
    for texto in (
        "Painel do projeto",
        "Progresso geral",
        "Unidades prontas",
        "Unidades concluídas",
        "Tarefas concluídas",
        "Tempo que falta",
        "Dias úteis até o prazo",
        "Tarefas × unidades por etapa",
        "Status das etapas",
        "Quanto cada etapa representa",
        "Horas por etapa",
        "Equipe × prazo",
        "Progresso por etapa pelas tarefas",
    ):
        assert texto in page, texto
    # números do servidor: 1 de 5 etapas concluídas; etapa "Pintura" 4/10 em andamento
    with app.app_context():
        project = db.session.get(Project, a.project_id)
        r = svc.summary(project)
    html = response.get_data(as_text=True)
    assert re.search(rf'{r.tarefas_concluidas}\s*<span class="kpi__unit">/ {r.tarefas}</span>', html)
    assert "1/5" in page and "concluídas" in page  # centro da rosca
    assert "Concluída" in page and "Em andamento" in page and "Não iniciada" in page
    # etapa sem tempo definido não ocupa o treemap, mas é avisada
    assert "1 etapa sem tempo definido" in page
    # cor nunca sozinha: legenda em texto, “hoje” na equipe atual, tabela de dados
    assert "hoje" in page and "Ver dados em tabela" in page


def test_painel_svgs_acessiveis_sem_script_nem_estilo_inline(client, app, tenants):
    a, _ = tenants
    _projeto_rico(app, a)
    login(client, app, a.operator_email)
    html = _painel(client, a).get_data(as_text=True)
    corpo = html.split('<h1>Painel do projeto</h1>')[1]
    assert not re.search(r"\sstyle\s*=", corpo), "estilo inline quebra a CSP"
    assert not re.search(r"<script", corpo.split("</main>")[0], re.I)
    assert "http://" not in corpo and "https://cdn" not in corpo
    # todo SVG com papel de imagem tem <title> e aria-labelledby; os decorativos ficam aria-hidden
    svgs = re.findall(r"<svg\b[^>]*>", corpo)
    assert len(svgs) >= 6
    for tag in svgs:
        assert 'aria-hidden="true"' in tag or ('role="img"' in tag and "aria-labelledby" in tag), tag
    assert corpo.count("<title") >= 4
    # sem cor solta nos SVG: só classes (tokens no CSS)
    assert not re.search(r'(fill|stroke)="#', corpo) and "rgb(" not in corpo


def test_painel_etapas_levam_ao_detalhe_com_a_etapa_aberta(client, app, tenants):
    a, _ = tenants
    _projeto_rico(app, a)
    login(client, app, a.operator_email)
    html = _painel(client, a).get_data(as_text=True)
    links = set(re.findall(r'href="(/app/projetos/[^"]+\?etapa=[^"]+)"', html))
    assert len(links) == 5  # um por etapa (barras e tabela repetem o mesmo destino)
    alvo = sorted(links)[0].replace("&amp;", "&")
    page = client.get(alvo).get_data(as_text=True)
    etapa_id = re.search(r"etapa=([0-9a-f-]{36})", alvo).group(1)
    assert re.search(rf'<details class="stage[^"]*" id="etapa-{etapa_id}" open', page)
    # as outras etapas (exceto a que abriria sozinha) seguem recolhidas
    abertas = re.findall(r'<details class="stage[^"]*" id="etapa-[0-9a-f-]+"( open)?', page)
    assert abertas.count(" open") == 1


def test_detalhe_ignora_etapa_de_outro_projeto_ou_invalida(client, app, tenants):
    a, b = tenants
    login(client, app, a.operator_email)
    padrao = client.get(f"/app/projetos/{a.project_id}")
    for lixo in (str(b.stage_id), "nao-e-uuid", "00000000-0000-0000-0000-000000000000"):
        response = client.get(f"/app/projetos/{a.project_id}?etapa={lixo}")
        assert response.status_code == 200
        assert f"etapa-{b.stage_id}" not in response.get_data(as_text=True)
        assert re.findall(r"<details class=\"stage[^>]*>", response.get_data(as_text=True)) == re.findall(
            r"<details class=\"stage[^>]*>", padrao.get_data(as_text=True)
        )


def test_painel_tabela_de_unidades_e_aba_invalida(client, app, tenants):
    a, _ = tenants
    _projeto_rico(app, a)
    login(client, app, a.operator_email)
    unidades = text_of(_painel(client, a, "?tabela=unidades"))
    assert "Unidades concluídas por etapa" in unidades and "Feitas" in unidades
    padrao = text_of(_painel(client, a, "?tabela=qualquer-coisa"))
    assert "Progresso por etapa pelas tarefas" in padrao and "Tempo por unidade (min)" in padrao


def test_painel_sem_etapas_mostra_estado_vazio(client, app, tenants):
    a, _ = tenants
    with app.app_context():
        project = db.session.get(Project, a.project_id)
        for stage in svc.active_stages(project):
            svc.archive_stage(stage, None)
        db.session.commit()
    login(client, app, a.operator_email)
    page = text_of(_painel(client, a))
    assert "Nenhuma etapa" in page


def test_painel_exige_login_e_aparece_link_no_detalhe(client, app, tenants):
    a, _ = tenants
    assert _painel(client, a).status_code in (302, 401)
    login(client, app, a.operator_email)
    assert f"/app/projetos/{a.project_id}/painel" in client.get(f"/app/projetos/{a.project_id}").get_data(as_text=True)


# ---------------------------------------------------------------- dashboard.build (puro)


def _etapas_fake():
    stages = [SimpleNamespace(id=i, name=f"Etapa {i}") for i in range(1, 6)]
    calcs = [
        calc.Etapa([calc.Atividade(60, 10)], 10),  # concluída
        calc.Etapa([calc.Atividade(30, 5), calc.Atividade(30, 2)], 10),  # andamento
        calc.Etapa([calc.Atividade(20, 0)], 10),  # não iniciada
        calc.Etapa([calc.Atividade(10, 0)], 10),
        calc.Etapa([calc.Atividade(0, 0)], 10),  # sem tempo
    ]
    return stages, calcs


def test_build_usa_so_numeros_do_calc():
    stages, calcs = _etapas_fake()
    r = calc.resumo_projeto(calcs, 10, pessoas=2, horas_dia=8)
    d = dashboard.build(stages, r, quantity=10, people=2, hours_per_day=8.0)
    assert [e["n"] for e in d["etapas"]] == [1, 2, 3, 4, 5]
    assert d["contagem"] == calc.contagem_status(r.etapas) == {"Concluída": 1, "Em andamento": 1, "Não iniciada": 3}
    assert d["rosca"]["total"] == 5
    assert d["sem_tempo"] == 1 and len(d["treemap"]) == 4
    # área do treemap proporcional ao peso (calc.peso_etapa)
    total = d["treemap_w"] * d["treemap_h"]
    for c in d["treemap"]:
        assert c["w"] * c["h"] == pytest.approx(c["etapa"]["r"].peso_no_projeto * total, rel=1e-2)
    # horas empilhadas = trabalhadas + faltam de cada etapa
    for col, e in zip(d["horas"]["cols"], d["etapas"]):
        assert col["total"] == pytest.approx(e["total_h"])
    # equipe × prazo: 6 linhas; a equipe atual (2) é a destacada e bate com o resumo
    assert [c["destaque"] for c in d["equipe"]["cols"]] == [False, True, False, False, False, False]
    assert d["equipe_atual"]["dias"] == pytest.approx(r.dias_uteis_restantes)
    assert d["unidades_pct"] == pytest.approx(calc.razao(r.unidades_concluidas, 10))


def test_build_equipe_fora_de_1_a_6_nao_destaca_coluna():
    stages, calcs = _etapas_fake()
    r = calc.resumo_projeto(calcs, 10, pessoas=9, horas_dia=8)
    d = dashboard.build(stages, r, quantity=10, people=9, hours_per_day=8.0)
    assert d["equipe_atual"] is None


def test_build_horas_por_dia_zero_nao_quebra():
    stages, calcs = _etapas_fake()
    r = calc.resumo_projeto(calcs, 10, pessoas=1, horas_dia=0)
    d = dashboard.build(stages, r, quantity=10, people=1, hours_per_day=0.0)
    assert all(c["dias"] is None for c in d["equipe"]["cols"])


def test_dashboard_e_puro():
    import ast
    from pathlib import Path

    tree = ast.parse((Path(dashboard.__file__)).read_text(encoding="utf-8"))
    importados = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            importados.add(node.module.split(".")[0] + ("." + node.module.split(".")[1] if node.module.startswith("app.") else ""))
        elif isinstance(node, ast.Import):
            importados.update(a.name for a in node.names)
    assert not importados & {"flask", "sqlalchemy", "flask_login", "app.models", "app.extensions"}
