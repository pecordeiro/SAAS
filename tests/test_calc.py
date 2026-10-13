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
