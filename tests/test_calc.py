"""Testes de app/services/calc.py.

1. Casos conferidos à mão (contas no comentário de cada teste).
2. calc.py é puro: não importa flask nem sqlalchemy.
3. Paridade com a planilha de referência: os valores calculados pelo Excel (cache do .xlsx)
   são a fonte de verdade.
"""

from __future__ import annotations

import ast
import re
from datetime import date
from pathlib import Path

import pytest

from app.services import calc
from app.services.calc import Atividade, Etapa

ROOT = Path(__file__).resolve().parents[1]
CALC_PATH = ROOT / "app" / "services" / "calc.py"
XLSX = ROOT / "docs" / "referencia" / "acompanhamento_montagem_v4.xlsx"
TOL = 1e-9


# ---------------------------------------------------------------------------
# 1. Casos conferidos à mão
# ---------------------------------------------------------------------------


def test_peso_atividade_divide_pela_soma_da_etapa():
    # 100 min ÷ 130 min = 0,76923...
    assert calc.peso_atividade(100, 130) == pytest.approx(100 / 130)


def test_peso_atividade_soma_zero_vale_zero():
    assert calc.peso_atividade(10, 0) == 0.0


def test_peso_etapa():
    # 130 min da etapa ÷ 190 min de 1 equipamento = 0,6842...
    assert calc.peso_etapa(130, 190) == pytest.approx(0.6842105263157895)
    assert calc.peso_etapa(130, 0) == 0.0


def test_pct_atividade_parcial():
    # 5 peças ÷ 10 previstas = 50%
    assert calc.pct_atividade(5, 10) == 0.5


def test_pct_atividade_100_por_cento():
    assert calc.pct_atividade(10, 10) == 1.0


def test_pct_atividade_pecas_acima_da_meta_limita_em_100():
    # 15 ÷ 10 = 1,5 → limitado a 1
    assert calc.pct_atividade(15, 10) == 1.0


def test_pct_atividade_quantidade_zero():
    assert calc.pct_atividade(5, 0) == 0.0


def test_tempos_da_atividade():
    # total = 100 × 10 = 1000; falta = 100 × (10 − 3) = 700
    assert calc.tempo_total_min(100, 10) == 1000
    assert calc.tempo_restante_min(100, 10, 3) == 700


def test_tempo_restante_pecas_acima_da_meta_nao_fica_negativo():
    # 100 × (10 − min(10, 12)) = 0
    assert calc.tempo_restante_min(100, 10, 12) == 0


def test_progresso_tarefas_ponderado_pelo_tempo():
    # Etapa da planilha: tempos 10,10,10,100; peças 5,5,5,0 de 10
    # Σ(t × %) = 10×0,5 × 3 = 15; Σt = 130 → 15/130 = 0,11538...
    atividades = [Atividade(10, 5), Atividade(10, 5), Atividade(10, 5), Atividade(100, 0)]
    assert calc.progresso_tarefas(atividades, 10) == pytest.approx(15 / 130)


def test_progresso_tarefas_soma_de_tempos_zero_usa_media_simples():
    # Tempos 0 e 0; peças 8 e 4 de 10 → (0,8 + 0,4) / 2 = 0,6
    atividades = [Atividade(0, 8), Atividade(0, 4)]
    assert calc.progresso_tarefas(atividades, 10) == pytest.approx(0.6)


def test_progresso_tarefas_sem_atividades():
    assert calc.progresso_tarefas([], 10) == 0.0


def test_unidades_etapa_menor_percentual():
    # min(0,8; 0,4) × 10 = 4
    assert calc.unidades_etapa([Atividade(10, 8), Atividade(5, 4)], 10) == 4


def test_unidades_etapa_arredonda_como_excel():
    # previstas 4, peças 2 e 3 → min(0,5; 0,75) × 4 = 2
    assert calc.unidades_etapa([Atividade(1, 2), Atividade(1, 3)], 4) == 2
    # ROUND do Excel arredonda 0,5 para cima (o round() do Python daria 2 para 2,5)
    assert calc.arredondar(2.5) == 3
    assert calc.arredondar(0.5) == 1
    assert calc.arredondar(2.4999) == 2


def test_unidades_etapa_sem_atividades_e_quantidade_zero():
    assert calc.unidades_etapa([], 10) == 0
    assert calc.unidades_etapa([Atividade(10, 5)], 0) == 0


def test_unidades_projeto_e_o_minimo_entre_etapas():
    assert calc.unidades_projeto([10, 4, 7]) == 4
    assert calc.unidades_projeto([]) == 0


def test_status_etapa():
    assert calc.status_etapa(10, 10, 1.0) == "Concluída"
    assert calc.status_etapa(12, 10, 1.0) == "Concluída"  # peças acima da meta
    assert calc.status_etapa(0, 10, 0.115) == "Em andamento"  # só progresso parcial
    assert calc.status_etapa(3, 10, 0.3) == "Em andamento"
    assert calc.status_etapa(0, 10, 0.0) == "Não iniciada"
    assert calc.status_etapa(0, 0, 0.0) == "Não iniciada"  # quantidade zero nunca conclui


def test_progresso_geral():
    # 1 − 29,1666 h ÷ 31,6666 h = 0,078947...
    assert calc.progresso_geral(1750, 1900) == pytest.approx(1 - 1750 / 1900)
    assert calc.progresso_geral(0, 0) == 0.0


def test_dias_uteis_restantes():
    # 29,1666 h ÷ (1 × 8) = 3,6458...; com 2 pessoas, metade
    assert calc.dias_uteis_restantes(29.166666666666668, 1, 8) == pytest.approx(3.6458333333333335)
    assert calc.dias_uteis_restantes(29.166666666666668, 2, 8) == pytest.approx(1.8229166666666667)
    assert calc.dias_uteis_restantes(10, 0, 8) is None


def test_prazo_em_data_pula_fim_de_semana():
    # 2026-10-15 é quinta. 3 dias úteis: qui, sex, seg → 2026-10-19
    assert calc.prazo_em_data(date(2026, 10, 15), 3) == date(2026, 10, 19)


def test_prazo_em_data_pula_feriado_e_arredonda_dia_parcial():
    # Início sexta 2026-10-30; feriado segunda 2026-11-02; 2,1 dias → 3 dias úteis:
    # sex 30, (sáb, dom, seg feriado pulados), ter 03, qua 04
    assert calc.prazo_em_data(date(2026, 10, 30), 2.1, [date(2026, 11, 2)]) == date(2026, 11, 4)


def test_prazo_em_data_inicio_em_fim_de_semana_e_zero_dias():
    # Sábado 2026-10-17, 1 dia útil → segunda 2026-10-19
    assert calc.prazo_em_data(date(2026, 10, 17), 1) == date(2026, 10, 19)
    assert calc.prazo_em_data(date(2026, 10, 17), 0) == date(2026, 10, 17)


def test_prazo_em_data_com_sabado_util():
    # Dias úteis seg–sáb; quinta 2026-10-15 + 3 dias → qui, sex, sáb = 2026-10-17
    assert calc.prazo_em_data(date(2026, 10, 15), 3, dias_semana=range(6)) == date(2026, 10, 17)


def test_resumo_projeto_completo():
    # Etapa 1: tempos 10 e 30, peças 10 e 5 de 10 → progresso (100 + 150)/400 = 0,625; unidades 5
    # Etapa 2: tempo 20, peças 0 → 0; unidades 0
    # total = (40 + 20) × 10 = 600 min; falta = 30×5 + 20×10 = 350 min
    etapas = [
        Etapa([Atividade(10, 10), Atividade(30, 5)], 10),
        Etapa([Atividade(20, 0)], 10),
    ]
    r = calc.resumo_projeto(etapas, quantidade=10, pessoas=1, horas_dia=8)
    assert r.etapas[0].progresso == pytest.approx(0.625)
    assert r.etapas[0].unidades == 5
    assert r.etapas[0].status == "Em andamento"
    assert r.etapas[0].peso_no_projeto == pytest.approx(40 / 60)
    assert r.etapas[1].status == "Não iniciada"
    assert r.unidades_concluidas == 0
    assert r.unidades_etapas == 5
    assert r.tempo_total_min == 600
    assert r.tempo_restante_min == 350
    assert r.progresso_geral == pytest.approx(1 - 350 / 600)
    assert r.dias_uteis_restantes == pytest.approx(350 / 60 / 8)
    assert r.tarefas == 3 and r.tarefas_concluidas == 1


def test_resumo_projeto_quantidade_zero():
    r = calc.resumo_projeto([Etapa([Atividade(10, 0)], 0)], quantidade=0)
    assert r.tempo_total_min == 0
    assert r.progresso_geral == 0.0
    assert r.unidades_concluidas == 0
    assert r.etapas[0].status == "Não iniciada"


# ---------------------------------------------------------------------------
# 2. Pureza
# ---------------------------------------------------------------------------


def test_calc_nao_importa_flask_nem_sqlalchemy():
    tree = ast.parse(CALC_PATH.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    proibidos = {"flask", "flask_sqlalchemy", "sqlalchemy", "app", "werkzeug", "flask_login"}
    assert not imported & proibidos, f"calc.py importa {imported & proibidos}"


# ---------------------------------------------------------------------------
# 3. Paridade com a planilha
# ---------------------------------------------------------------------------

TITULO_ETAPA = re.compile(r"^\s*\d+\.\s")


def _n(value) -> float:
    """N() do Excel: número vira número; vazio/texto vira 0."""
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _ler_planilha():
    openpyxl = pytest.importorskip("openpyxl")
    import warnings

    if not XLSX.exists():
        pytest.skip(f"planilha de referência ausente: {XLSX}")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # extensões de formatação condicional não suportadas
        formulas = openpyxl.load_workbook(XLSX, data_only=False)
        valores = openpyxl.load_workbook(XLSX, data_only=True)
    return formulas["Acompanhamento"], valores["Acompanhamento"], valores["Equipe"]


def _descobrir_etapas(wf, wv):
    """Acha cada bloco de etapa pelos títulos da coluna A.

    Título "N. Nome" → linha "Unidades previstas" (B = previstas) → linha "Subatividade"
    (cabeçalho) → atividades → linha "Total da etapa ...".
    Entradas (tempo ideal, peças) vêm da planilha de fórmulas; resultados, do cache.
    """
    etapas = []
    r = 1
    max_row = wf.max_row
    while r <= max_row:
        titulo = wf.cell(r, 1).value
        if (
            isinstance(titulo, str)
            and TITULO_ETAPA.match(titulo)
            and str(wf.cell(r + 1, 1).value or "").startswith("Unidades previstas")
            and str(wf.cell(r + 2, 1).value or "").startswith("Subatividade")
        ):
            linha_previstas = r + 1
            previstas_cache = wv.cell(linha_previstas, 2).value
            atividades = []
            linha = r + 3
            while not str(wf.cell(linha, 1).value or "").startswith("Total da etapa"):
                nome = wf.cell(linha, 1).value
                if nome not in (None, ""):
                    atividades.append(
                        calc.Atividade(ideal_min=_n(wf.cell(linha, 2).value), pecas=int(_n(wf.cell(linha, 4).value)))
                    )
                linha += 1
                assert linha - r < 100, f"bloco da etapa {titulo!r} sem linha 'Total da etapa'"
            total = linha
            esperado = {
                "previstas": previstas_cache,
                "unidades": wv.cell(linha_previstas, 6).value,  # F13
                "tempo_unidade": wv.cell(total, 2).value,  # B23
                "progresso": wv.cell(total, 5).value,  # E23
                "tempo_total": wv.cell(total, 6).value,  # F23
                "tempo_restante": wv.cell(total, 7).value,  # G23
                "peso_no_robo": wv.cell(r, 6).value,  # F12
                "pesos": [wv.cell(i, 3).value for i in range(r + 3, total) if wf.cell(i, 1).value not in (None, "")],
                "pcts": [wv.cell(i, 5).value for i in range(r + 3, total) if wf.cell(i, 1).value not in (None, "")],
            }
            etapas.append((titulo, atividades, esperado))
            r = total + 1
        else:
            r += 1
    return etapas


def _status_tabela2(wf, wv) -> dict[str, str]:
    """Status por etapa da Tabela 2 (linhas cuja coluna F tem a fórmula de status)."""
    status = {}
    for r in range(1, wf.max_row + 1):
        formula = wf.cell(r, 6).value
        if isinstance(formula, str) and "Concluída" in formula and "Em andamento" in formula:
            status[wv.cell(r, 1).value] = wv.cell(r, 6).value
    return status


def test_paridade_com_planilha_de_referencia():
    wf, wv, equipe = _ler_planilha()
    if wv["B6"].value is None or wv["F414"].value is None:
        pytest.skip("cache de valores do Excel vazio (planilha salva sem recálculo)")

    blocos = _descobrir_etapas(wf, wv)
    assert len(blocos) >= 3, "nenhuma etapa encontrada na planilha"

    quantidade = int(wv["B4"].value)
    etapas = [calc.Etapa(atividades=tuple(atvs), previstas=int(esp["previstas"])) for _, atvs, esp in blocos]
    pessoas = int(_n(equipe["B6"].value))
    horas_dia = _n(equipe["B7"].value)
    resultado = calc.resumo_projeto(etapas, quantidade=quantidade, pessoas=pessoas, horas_dia=horas_dia)
    status_excel = _status_tabela2(wf, wv)

    for (titulo, _, esp), r in zip(blocos, resultado.etapas):
        ctx = f"etapa {titulo!r}"
        assert r.previstas == esp["previstas"], ctx
        assert r.unidades == esp["unidades"], ctx
        assert r.progresso == pytest.approx(esp["progresso"], abs=TOL), ctx
        assert r.tempo_unidade_min == pytest.approx(esp["tempo_unidade"], abs=TOL), ctx
        assert r.tempo_total_min == pytest.approx(esp["tempo_total"], abs=TOL), ctx
        assert r.tempo_restante_min == pytest.approx(esp["tempo_restante"], abs=TOL), ctx
        assert r.peso_no_projeto == pytest.approx(esp["peso_no_robo"], abs=TOL), ctx
        assert r.status == status_excel[titulo], ctx
        for i, (ra, peso, pct) in enumerate(zip(r.atividades, esp["pesos"], esp["pcts"])):
            # Planilha mostra "" (vazio) no peso quando a soma de tempos é 0; calc devolve 0.
            assert ra.peso == pytest.approx(peso if isinstance(peso, (int, float)) else 0.0, abs=TOL), f"{ctx} ativ. {i}"
            assert ra.pct == pytest.approx(pct, abs=TOL), f"{ctx} ativ. {i}"

    # Resumo final (linhas 377–385) e aba Equipe
    assert resultado.unidades_concluidas == wv["B377"].value  # robôs concluídos
    assert resultado.etapas_concluidas == wv["B378"].value
    assert len(resultado.etapas) == wv["C378"].value
    assert resultado.tarefas_concluidas == wv["B379"].value
    assert resultado.tarefas == wv["C379"].value
    assert resultado.unidades_etapas == wv["B380"].value
    assert resultado.unidades_etapas_previstas == wv["C380"].value
    assert resultado.progresso_geral == pytest.approx(wv["D381"].value, abs=TOL)
    assert resultado.progresso_geral == pytest.approx(wv["E414"].value, abs=TOL)
    assert resultado.tempo_unidade_min / 60 == pytest.approx(wv["B382"].value, abs=TOL)
    assert resultado.tempo_total_h == pytest.approx(wv["F414"].value, abs=TOL)
    assert resultado.tempo_restante_h == pytest.approx(wv["B383"].value, abs=TOL)
    assert resultado.dias_uteis_restantes == pytest.approx(wv["B384"].value, abs=TOL)
    assert resultado.dias_uteis_restantes == pytest.approx(equipe["B8"].value, abs=TOL)
    assert calc.dias_uteis_restantes(resultado.tempo_total_h, pessoas, horas_dia) == pytest.approx(
        equipe["B9"].value, abs=TOL
    )


# ---------------------------------------------------------------- dias úteis entre datas (Fase 4)


def test_dias_uteis_entre_conta_intervalo_aberto_no_inicio():
    # Prazo sexta 16/10/2026, término previsto terça 20/10: seg 19 e ter 20 → 2 dias úteis
    assert calc.dias_uteis_entre(date(2026, 10, 16), date(2026, 10, 20)) == 2


def test_dias_uteis_entre_pula_fim_de_semana_e_feriado():
    # Sexta 30/10 → quarta 04/11 com feriado na segunda 02/11: ter 03, qua 04 → 2
    assert calc.dias_uteis_entre(date(2026, 10, 30), date(2026, 11, 4), [date(2026, 11, 2)]) == 2
    # Sexta → domingo: nenhum dia útil
    assert calc.dias_uteis_entre(date(2026, 10, 16), date(2026, 10, 18)) == 0


def test_dias_uteis_entre_fim_antes_ou_igual_ao_inicio():
    assert calc.dias_uteis_entre(date(2026, 10, 20), date(2026, 10, 20)) == 0
    assert calc.dias_uteis_entre(date(2026, 10, 20), date(2026, 10, 1)) == 0


def test_dias_uteis_entre_com_sabado_util():
    # seg–sáb úteis: sexta 16/10 → segunda 19/10 = sáb 17 + seg 19 → 2
    assert calc.dias_uteis_entre(date(2026, 10, 16), date(2026, 10, 19), dias_semana=range(6)) == 2


def test_dias_uteis_entre_e_inverso_de_prazo_em_data():
    # Começando na segunda 12/10, 5 dias úteis terminam na sexta 16/10;
    # do domingo 11/10 (véspera) até a sexta há exatamente 5 dias úteis.
    fim = calc.prazo_em_data(date(2026, 10, 12), 5)
    assert fim == date(2026, 10, 16)
    assert calc.dias_uteis_entre(date(2026, 10, 11), fim) == 5


# ---------------------------------------------------------------- dashboard (Etapa E)


def test_razao_e_contagem_e_equipe_a_mao():
    assert calc.razao(40, 240) == pytest.approx(40 / 240)
    assert calc.razao(5, 0) == 0.0
    # 10 h ÷ (p × 8 h): 1,25; 0,625; ...
    tabela = calc.equipe_x_prazo(10, 8, ate=3)
    assert [p for p, _ in tabela] == [1, 2, 3]
    assert tabela[0][1] == pytest.approx(1.25) and tabela[1][1] == pytest.approx(0.625)
    assert calc.equipe_x_prazo(10, 0, ate=2) == ((1, None), (2, None))
    r = calc.resumo_projeto(
        [Etapa([Atividade(10, 10)], 10), Etapa([Atividade(10, 3)], 10), Etapa([Atividade(10, 0)], 10)], 10
    )
    assert calc.contagem_status(r.etapas) == {"Concluída": 1, "Em andamento": 1, "Não iniciada": 1}
    # trabalhado = total − falta: etapa 2 = 100 − 70 = 30 min
    assert r.etapas[1].tempo_trabalhado_min == pytest.approx(30)
    assert r.tempo_trabalhado_min == pytest.approx(130)


def test_paridade_dashboard_com_planilha_de_referencia():
    """Cada número do dashboard (KPIs, Tabela 1, Tabela 2, status, horas por etapa, equipe × prazo)
    sai de calc.py e bate com o cache de valores do Excel."""
    wf, wv, equipe = _ler_planilha()
    if wv["B6"].value is None or wv["F414"].value is None:
        pytest.skip("cache de valores do Excel vazio (planilha salva sem recálculo)")
    ws = wv  # aba Acompanhamento com valores

    blocos = _descobrir_etapas(wf, wv)
    n = len(blocos)
    etapas = [calc.Etapa(atividades=tuple(atvs), previstas=int(esp["previstas"])) for _, atvs, esp in blocos]
    pessoas = int(_n(equipe["B6"].value))
    horas_dia = _n(equipe["B7"].value)
    r = calc.resumo_projeto(etapas, quantidade=int(ws["B4"].value), pessoas=pessoas, horas_dia=horas_dia)

    # --- Tabela 1 (linhas 390…) e linha Total
    t1, t2 = 390, 419
    for i, e in enumerate(r.etapas):
        ctx = f"etapa {i + 1}"
        assert e.tempo_unidade_min == pytest.approx(ws.cell(t1 + i, 2).value, abs=TOL), ctx  # tempo por robô
        assert e.peso_no_projeto == pytest.approx(ws.cell(t1 + i, 3).value, abs=TOL), ctx  # peso no robô
        assert e.previstas == ws.cell(t1 + i, 4).value, ctx
        assert e.progresso == pytest.approx(ws.cell(t1 + i, 5).value, abs=TOL), ctx
        assert e.tempo_total_min / 60 == pytest.approx(ws.cell(t1 + i, 6).value, abs=TOL), ctx
        assert e.tempo_restante_min / 60 == pytest.approx(ws.cell(t1 + i, 7).value, abs=TOL), ctx
        # Horas por etapa (gráfico trabalhadas × faltam): F − G
        trabalhadas = ws.cell(t1 + i, 6).value - ws.cell(t1 + i, 7).value
        assert e.tempo_trabalhado_min / 60 == pytest.approx(trabalhadas, abs=TOL), ctx
    tot = t1 + n
    assert ws.cell(tot, 1).value == "Total"
    assert r.tempo_unidade_min == pytest.approx(ws.cell(tot, 2).value, abs=TOL)
    assert sum(e.peso_no_projeto for e in r.etapas) == pytest.approx(ws.cell(tot, 3).value, abs=TOL)  # treemap = 100%
    assert r.unidades_etapas_previstas == ws.cell(tot, 4).value
    assert r.progresso_geral == pytest.approx(ws.cell(tot, 5).value, abs=TOL)
    assert r.tempo_total_h == pytest.approx(ws.cell(tot, 6).value, abs=TOL)
    assert r.tempo_restante_h == pytest.approx(ws.cell(tot, 7).value, abs=TOL)

    # --- Tabela 2 (linhas 419…) e Total: unidades, % e status
    for i, e in enumerate(r.etapas):
        ctx = f"etapa {i + 1}"
        assert e.unidades == ws.cell(t2 + i, 2).value, ctx
        assert e.previstas == ws.cell(t2 + i, 3).value, ctx
        assert f"{e.unidades}/{e.previstas}" == ws.cell(t2 + i, 4).value, ctx
        assert calc.razao(e.unidades, e.previstas) == pytest.approx(ws.cell(t2 + i, 5).value, abs=TOL), ctx
        assert e.status == ws.cell(t2 + i, 6).value, ctx
    assert ws.cell(t2 + n, 1).value == "Total"
    assert r.unidades_etapas == ws.cell(t2 + n, 2).value
    assert r.unidades_etapas_previstas == ws.cell(t2 + n, 3).value
    assert calc.razao(r.unidades_etapas, r.unidades_etapas_previstas) == pytest.approx(ws.cell(t2 + n, 5).value, abs=TOL)

    # --- Rosca “status das etapas”: contagem por situação (B378 e F419:F442)
    contagem = calc.contagem_status(r.etapas)
    status_excel = [ws.cell(t2 + i, 6).value for i in range(n)]
    for nome in (calc.STATUS_CONCLUIDA, calc.STATUS_EM_ANDAMENTO, calc.STATUS_NAO_INICIADA):
        assert contagem[nome] == status_excel.count(nome), nome
    assert contagem[calc.STATUS_CONCLUIDA] == ws["B378"].value and sum(contagem.values()) == ws["C378"].value

    assert calc.etapas_sem_tempo(r.etapas) == ws["B385"].value  # etapas sem tempo definido (treemap)

    # --- KPIs (resumo final 377–384)
    assert r.unidades_concluidas == ws["B377"].value and r.previstas == ws["C377"].value
    assert calc.razao(r.unidades_concluidas, r.previstas) == pytest.approx(ws["D377"].value, abs=TOL)
    assert (r.tarefas_concluidas, r.tarefas) == (ws["B379"].value, ws["C379"].value)
    assert calc.razao(r.tarefas_concluidas, r.tarefas) == pytest.approx(ws["D379"].value, abs=TOL)
    assert calc.razao(r.unidades_etapas, r.unidades_etapas_previstas) == pytest.approx(ws["D380"].value, abs=TOL)
    assert r.tempo_trabalhado_h == pytest.approx(ws["B381"].value, abs=TOL)  # “67,8 h trabalhadas de 160,5 h”
    assert r.tempo_total_h == pytest.approx(ws["C381"].value, abs=TOL)
    assert r.progresso_geral == pytest.approx(ws["D381"].value, abs=TOL)
    assert r.tempo_restante_h == pytest.approx(ws["B383"].value, abs=TOL)
    assert r.dias_uteis_restantes == pytest.approx(ws["B384"].value, abs=TOL)

    # --- Equipe × prazo (aba Equipe, linhas 13–18): pessoas 1…6
    tabela = calc.equipe_x_prazo(r.tempo_restante_h, horas_dia)
    assert len(tabela) == 6
    for linha, (p, dias) in zip(range(13, 19), tabela):
        assert p == equipe.cell(linha, 1).value
        assert dias == pytest.approx(equipe.cell(linha, 3).value, abs=TOL)


# ---------------------------------------------------------------- R2: painel (esteira, atraso, operação)


def _etapa_r(tempo_total, status):
    return calc.ResultadoEtapa(
        tempo_unidade_min=0, peso_no_projeto=0, progresso=0, unidades=0, previstas=0, status=status,
        tempo_total_min=tempo_total, tempo_restante_min=0, tarefas=0, tarefas_concluidas=0, atividades=(),
    )


def test_fracao_prazo_decorrida_em_dias_uteis():
    seg, sex = date(2026, 10, 19), date(2026, 10, 23)  # 4 dias úteis depois do início
    assert calc.fracao_prazo_decorrida(None, sex, seg) is None
    assert calc.fracao_prazo_decorrida(seg, None, seg) is None
    assert calc.fracao_prazo_decorrida(seg, sex, seg) == 0.0
    assert calc.fracao_prazo_decorrida(seg, sex, date(2026, 10, 21)) == 0.5
    assert calc.fracao_prazo_decorrida(seg, sex, date(2026, 10, 30)) == 1.0
    # feriado na quarta: 3 dias úteis no prazo; até a quarta passou 1
    assert calc.fracao_prazo_decorrida(seg, sex, date(2026, 10, 21), [date(2026, 10, 21)]) == pytest.approx(1 / 3)


def test_fatias_e_atraso_por_etapa():
    etapas = [_etapa_r(60, calc.STATUS_CONCLUIDA), _etapa_r(60, calc.STATUS_EM_ANDAMENTO), _etapa_r(120, calc.STATUS_NAO_INICIADA)]
    assert calc.fatias_da_esteira(etapas) == ((0.0, 0.25), (0.25, 0.25), (0.5, 0.5))
    assert calc.fatias_da_esteira([_etapa_r(0, calc.STATUS_NAO_INICIADA)] * 2) == ((0.0, 0.5), (0.5, 0.5))
    assert calc.etapas_atrasadas(etapas, None) == (False, False, False)
    assert calc.etapas_atrasadas(etapas, 0.4) == (False, False, False)
    assert calc.etapas_atrasadas(etapas, 0.5) == (False, True, False)  # a 2ª devia ter acabado
    assert calc.etapas_atrasadas(etapas, 1.0) == (False, True, True)


def test_status_visual_prioridade():
    assert calc.status_visual(calc.STATUS_CONCLUIDA, True, True) == "done"
    assert calc.status_visual(calc.STATUS_EM_ANDAMENTO, True, True) == "waiting"
    assert calc.status_visual(calc.STATUS_EM_ANDAMENTO, False, True) == "late"
    assert calc.status_visual(calc.STATUS_EM_ANDAMENTO) == "doing"
    assert calc.status_visual(calc.STATUS_NAO_INICIADA) == "todo"
    assert calc.contagem_visual(["done", "late", "late"]) == {"done": 1, "doing": 0, "waiting": 0, "late": 2, "todo": 0}


def test_resumo_operacao_soma_tempos():
    a = calc.resumo_projeto([calc.Etapa([calc.Atividade(60, 10)], 10)], 10)
    b = calc.resumo_projeto([calc.Etapa([calc.Atividade(30, 0)], 10)], 10)
    r = calc.resumo_operacao([a, b])
    assert r.projetos == 2 and r.previstas == 20 and r.unidades_concluidas == 10
    assert r.tempo_total_min == 900 and r.tempo_restante_min == 300
    assert r.progresso_geral == pytest.approx(1 - 300 / 900)
    assert calc.resumo_operacao([]).progresso_geral == 0
