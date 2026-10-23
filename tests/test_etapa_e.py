"""Etapa E — painel completo do projeto: KPIs, gráficos SVG no servidor e tabela de etapas.

Cálculo só em calc.py (paridade com a planilha em tests/test_calc.py); aqui: a tela imprime
o que o servidor calculou, é acessível (título/desc nos SVG, texto ao lado da cor) e segura
(sem script nem estilo inline por causa da CSP, sem CDN)."""

from __future__ import annotations

import json
import re
from datetime import date
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
    """R2: cabeçalho com frase-resumo, faixa de 5 indicadores, esteira, gráficos e Tabelas 1/2."""
    a, _ = tenants
    _projeto_rico(app, a)
    login(client, app, a.operator_email)
    response = _painel(client, a)
    assert response.status_code == 200
    page = text_of(response)
    for texto in (
        "Atualizado às",
        "Preencher etapas",
        "Progresso geral",
        "Unidades prontas",
        "Etapas concluídas",
        "Horas que faltam",
        "Dias úteis até o prazo",
        "Esteira de etapas",
        "Tarefas × unidades por etapa",
        "Situação das etapas",
        "Atrasadas e aguardando peça",
        "Horas por etapa",
        "Equipe × prazo",
        "Tabela 1 · Progresso por etapa pelas tarefas",
    ):
        assert texto in page, texto
    with app.app_context():
        project = db.session.get(Project, a.project_id)
        r = svc.summary(project)
    html = response.get_data(as_text=True)
    # números do servidor (calc): etapas concluídas sobre o total, unidade em cinza ao lado
    assert re.search(rf'{r.etapas_concluidas}<span class="kpi__unit">/ 5</span>', html)
    assert f"tarefas concluídas: {r.tarefas_concluidas} de {r.tarefas}" in page
    # legenda em texto com a contagem por situação (cor nunca sozinha)
    for nome in ("Concluída", "Em andamento", "Aguardando peça", "Atrasada", "Não iniciada"):
        assert nome in page
    assert "1 etapa ainda sem tempo ideal" in page
    assert "Ver dados em tabela" in page
    # dados dos gráficos: JSON gerado pelo servidor, lido pelo painel.js (ECharts local)
    dados = json.loads(re.search(r'<script type="application/json" id="painel-dados">(.*?)</script>', html, re.S).group(1))
    assert [row["label"] for row in dados["rows"]][:2] == ["1. Etapa 1", "2. Pintura"]
    assert dados["rows"][0]["tasks"] == pytest.approx(r.etapas[0].progresso)
    assert sum(s["value"] for s in dados["status"]) == 5
    assert len(dados["team"]["rows"]) == 6
    assert "/static/" in html and re.search(r"echarts(-5\.5\.1/echarts\.min|\.[0-9a-f]{10})\.js", html)


def test_painel_sem_estilo_inline_sem_cdn_e_esteira_acessivel(client, app, tenants):
    a, _ = tenants
    _projeto_rico(app, a)
    login(client, app, a.operator_email)
    html = _painel(client, a).get_data(as_text=True)
    corpo = html.split('<main id="conteudo"')[1]
    assert not re.search(r"\sstyle\s*=", corpo), "estilo inline quebra a CSP"
    # o único <script> no corpo é o bloco de dados JSON (não executa)
    assert re.findall(r"<script\b[^>]*>", corpo.split("</main>")[0]) == ['<script type="application/json" id="painel-dados">']
    assert "http://" not in corpo and "https://cdn" not in corpo
    # esteira: um bloco (link com nome) por etapa, cor só por classe
    blocos = re.findall(r'<a href="([^"]+)" aria-label="([^"]+)"><rect class="esteira__bloco esteira__bloco--(\w+)"', corpo)
    assert len(blocos) == 5
    assert all(" — " in label for _, label, _ in blocos)
    assert not re.search(r'(fill|stroke)="#', corpo) and "rgb(" not in corpo
    # gráficos do ECharts têm nome acessível
    for chart in ("tasks", "status", "hours", "team"):
        assert re.search(rf'data-chart="{chart}" role="img" aria-label="[^"]+"', corpo), chart


def test_painel_etapas_levam_ao_preencher_com_a_etapa_aberta(client, app, tenants):
    """R3: clicar numa etapa do painel abre “Preencher etapas” já nela (a tela de detalhe deixou de ser o destino)."""
    a, _ = tenants
    _projeto_rico(app, a)
    login(client, app, a.operator_email)
    html = _painel(client, a).get_data(as_text=True)
    links = set(re.findall(r'href="(/app/preencher[^"]*etapa=[^"]+)"', html))
    assert len(links) == 5  # um por etapa (barras e tabela repetem o mesmo destino)
    alvo = sorted(links)[0].replace("&amp;", "&")
    resp = client.get(alvo)
    assert resp.status_code == 200
    etapa_id = re.search(r"etapa=([0-9a-f-]{36})", alvo).group(1)
    assert etapa_id in resp.get_data(as_text=True)



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
    assert "Tabela 2 · Unidades concluídas por etapa" in unidades and "Feitas" in unidades
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


# ---------------------------------------------------------------- dashboard.painel_* (puro)


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


def _painel_fake(pessoas=2, horas_dia=8.0, fracao=None, deadline=None, prazo=None, stages=None):
    st, calcs = _etapas_fake()
    stages = stages or st
    r = calc.resumo_projeto(calcs, 10, pessoas=pessoas, horas_dia=horas_dia)
    d = dashboard.painel_projeto(
        stages, r, nome="Lote 10", quantity=10, people=pessoas, hours_per_day=horas_dia,
        prazo=prazo, deadline=deadline or {}, concluido=False, fracao_decorrida=fracao,
        href_etapa=lambda sid: f"/etapa/{sid}",
    )
    return r, d


def test_painel_projeto_usa_so_numeros_do_calc():
    r, d = _painel_fake()
    assert [e["n"] for e in d["etapas"]] == [1, 2, 3, 4, 5]
    assert d["contagem"] == {"done": 1, "doing": 1, "waiting": 0, "late": 0, "todo": 3}
    assert sum(s["value"] for s in d["grafico"]["status"]) == 5
    assert d["sem_tempo"] == 1
    # esteira: largura ∝ tempo total da etapa (calc.fatias_da_esteira), blocos lado a lado
    blocos = d["esteira"]["blocos"]
    total = sum(e["r"].tempo_total_min for e in d["etapas"])
    for b, e in zip(blocos, d["etapas"]):
        assert b["w"] == pytest.approx(e["r"].tempo_total_min / total * 1000, abs=1e-2)
        assert b["href"] == f"/etapa/{e['id']}"
    assert blocos[-1]["w"] == 0 and sum(b["w"] for b in blocos) == pytest.approx(1000, abs=1e-2)
    assert d["esteira"]["hoje"] is None  # sem prazo: sem marca de hoje
    # horas = trabalhadas + faltam de cada etapa
    for row, e in zip(d["grafico"]["rows"], d["etapas"]):
        assert row["worked"] + row["left"] == pytest.approx(e["total_h"], abs=0.02)
        assert row["tasks"] == pytest.approx(e["r"].progresso, abs=1e-4)
    # equipe × prazo: 6 linhas; a equipe atual (2) é a destacada e bate com o resumo
    assert [x["current"] for x in d["equipe"]] == [False, True, False, False, False, False]
    assert d["equipe_atual"]["days"] == pytest.approx(r.dias_uteis_restantes, abs=0.01)
    assert d["unidades_pct"] == pytest.approx(calc.razao(r.unidades_concluidas, 10))
    assert d["frase"] == "Lote 10: sem prazo definido"


def test_painel_projeto_atraso_e_aguardando_peca():
    st, _ = _etapas_fake()
    st[2].waiting_part = True
    # metade do prazo passou: as etapas cuja faixa terminou antes de 50% e não estão prontas atrasam
    r, d = _painel_fake(fracao=0.5, stages=st, prazo=date(2026, 11, 14),
                        deadline={"on_time": True, "forecast": date(2026, 11, 10), "slack": 3, "until_due": 17})
    atrasos = calc.etapas_atrasadas(r.etapas, 0.5)
    for e, atrasada in zip(d["etapas"], atrasos):
        assert e["atrasada"] == atrasada
    assert d["etapas"][0]["visual"] == "done"
    assert d["etapas"][2]["visual"] == "waiting"  # aguardando peça vence "atrasada"
    assert d["esteira"]["hoje"] == pytest.approx(500)
    assert [p["etapa"]["visual"] for p in d["pendencias"]][-1] == "waiting"
    assert d["frase"].startswith("Lote 10: termina 10/11, folga de 3 dias úteis")
    assert "aguardando peça" in d["frase"]
    assert d["grafico"]["team"]["due"] == 17


def test_painel_projeto_equipe_fora_de_1_a_6_nao_destaca():
    _, d = _painel_fake(pessoas=9)
    assert d["equipe_atual"] is None


def test_painel_projeto_horas_por_dia_zero_nao_quebra():
    _, d = _painel_fake(pessoas=1, horas_dia=0.0)
    assert all(x["days"] is None and x["daysText"] == "—" for x in d["equipe"])


def test_rotulo_nao_repete_a_numeracao():
    assert dashboard.rotulo_etapa(1, "1. Preparação da base") == "1. Preparação da base"
    assert dashboard.rotulo_etapa(3, "3) Montagem") == "3) Montagem"
    assert dashboard.rotulo_etapa(2, "Pintura") == "2. Pintura"
    assert dashboard.rotulo_etapa(4, "4x4 Chassi") == "4. 4x4 Chassi"


def test_painel_operacao_soma_os_projetos():
    st, calcs = _etapas_fake()
    itens = []
    for i, pessoas in enumerate((1, 3)):
        r = calc.resumo_projeto(calcs, 10, pessoas=pessoas, horas_dia=8)
        proj = SimpleNamespace(id=f"p{i}", name=f"Lote {i}", quantity=10, due_date=None)
        itens.append({"project": proj, "stages": st, "result": r, "deadline": {}, "concluido": False, "fracao": None})
    d = dashboard.painel_operacao(itens, href_etapa=lambda p, s: f"/{p}/{s}", href_projeto=lambda p: f"/{p}")
    resumo = d["resumo"]
    assert resumo.projetos == 2 and resumo.etapas == 10
    assert resumo.tempo_restante_min == pytest.approx(2 * itens[0]["result"].tempo_restante_min)
    assert resumo.progresso_geral == pytest.approx(itens[0]["result"].progresso_geral)
    assert [row["label"] for row in d["grafico"]["rows"]] == ["Lote 0", "Lote 1"]
    assert d["proximo"] is None
    assert d["frase"].startswith("2 projetos ativos")
    assert d["projetos"][1]["esteira"]["blocos"][0]["href"] == "/p1/1"


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
