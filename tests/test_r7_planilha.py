"""R7 — planilha: importar qualquer planilha com mapeamento de colunas; exportar no layout da
base (com fórmulas, conferidas contra o calc.py); exportar → importar devolve o projeto."""

from __future__ import annotations

import csv
import html
import io
import os
import re
import shutil
import subprocess
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from flask import g
from openpyxl import Workbook, load_workbook

from app.extensions import db
from app.models import Company, Project, User
from app.services import calc, export_layout, exporter, importer
from app.services import import_mapping as im
from app.services import projects as svc
from tests.conftest import login, make_tenant, post, text_of

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "referencia" / "acompanhamento_montagem_v4.xlsx"


@pytest.fixture()
def ctx(app):
    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "203.0.113.7"}):
        tenant = make_tenant("A")
        company = db.session.get(Company, tenant.company_id)
        g.company = company
        owner = db.session.get(User, tenant.owner_id)
        yield company, owner


def _xlsx(sheets: dict[str, list[list]]) -> bytes:
    wb = Workbook()
    for i, (title, rows) in enumerate(sheets.items()):
        ws = wb.active if i == 0 else wb.create_sheet()
        ws.title = title
        for row in rows:
            ws.append(row)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def _csv(rows: list[list], delimiter=";") -> bytes:
    buffer = io.StringIO()
    csv.writer(buffer, delimiter=delimiter).writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _project(company, owner, name="Lote R7", quantity=6):
    stages = [
        svc.NewStage("1. Base", [svc.NewActivity("Corte", Decimal("60")), svc.NewActivity("Furação", Decimal("45.25"))]),
        svc.NewStage("Pintura", [svc.NewActivity("=Lixar", Decimal("12")), svc.NewActivity("Pintar", Decimal("0"))]),
        svc.NewStage("Vazia", []),
        svc.NewStage("+Fim", [svc.NewActivity("Testar", Decimal("30"))]),
    ]
    project = svc.create_project(
        company, name=name, quantity=quantity, start_date=date(2026, 10, 5), due_date=date(2026, 11, 20),
        people=3, hours_per_day=Decimal("7.5"), stages=stages,
    )
    svc.register_progress(project.stages[0].activities[0], 6, None, owner.id)
    svc.register_progress(project.stages[0].activities[1], 4, None, owner.id)
    svc.register_progress(project.stages[1].activities[0], 6, None, owner.id)
    svc.register_progress(project.stages[1].activities[1], 6, None, owner.id)
    svc.register_progress(project.stages[3].activities[0], 1, None, owner.id)
    gone = svc.add_activity(project.stages[3], svc.NewActivity("Arquivada", Decimal("3")))
    svc.archive_activity(gone, owner.id)
    db.session.commit()
    db.session.expire_all()
    return db.session.get(Project, project.id)


# ================================================================ mapeamento: sugestão e inspeção


def test_sugestao_por_nome_sem_acento_e_sem_caixa():
    headers = ["Fase", "TAREFA", "Tempo que falta", "Tempo padrão", "Qtd", "Peças concluídas", "% Concluído", "Data de entrega"]
    s = im.suggest(headers)
    assert s == {
        im.F_STAGE: 0, im.F_ACTIVITY: 1, im.F_MINUTES: 3, im.F_PLANNED: 4, im.F_DONE: 5, im.F_PCT: 6, im.F_DUE: 7,
    }
    assert im.suggest(["Etapa", "%"]) == {**{k: None for k in im.FIELD_KEYS}, im.F_STAGE: 0, im.F_PCT: 1}
    assert im.normalize("  Peças   CONCLUÍDAS ") == "pecas concluidas"


def test_inspecao_mostra_abas_cabecalho_detectado_e_amostras():
    data = _xlsx({
        "Capa": [["Relatório"]],
        "Produção": [
            ["Acompanhamento da linha 3"],
            [],
            ["Etapa", "Atividade", "Minutos", "Feitas"],
            ["Corte", "Serrar", 10, 2],
            [None, "Lixar", 5.5, 1],
            ["Solda", "Soldar", 20, 0],
        ],
    })
    grid = importer.load_grid("linha.xlsx", data, 10**6)
    assert importer.auto_parse(grid) is None  # formato desconhecido → precisa mapear
    first = im.inspect(grid)
    assert first.sheets == ["Capa", "Produção"] and first.sheet == "Capa"
    view = im.inspect(grid, "Produção")
    assert view.header_row == 3 and view.rows == 3
    assert [(c.letter, c.header) for c in view.columns] == [("A", "Etapa"), ("B", "Atividade"), ("C", "Minutos"), ("D", "Feitas")]
    assert view.columns[2].samples == ["10", "5,5", "20"]
    assert view.suggestion[im.F_STAGE] == 0 and view.suggestion[im.F_ACTIVITY] == 1
    assert view.suggestion[im.F_MINUTES] == 2 and view.suggestion[im.F_DONE] == 3
    # cabeçalho escolhido pela pessoa vale mais que o detectado
    assert im.inspect(grid, "Produção", header_row=4).header_row == 4


# ================================================================ mapeamento: resultado


def test_mapeamento_detalhado_com_etapa_herdada_e_meta_digitada(ctx):
    company, owner = ctx
    grid = importer.load_grid("linha.xlsx", _xlsx({"P": [
        ["Etapa", "Atividade", "Minutos", "Feitas", "Prazo"],
        ["Corte", "Serrar", 10, 2, date(2026, 12, 1)],
        [None, "Lixar", "5,5", 1, "15/12/2026"],
        ["Solda", "Soldar", 20, 0, None],
        ["Total", None, 35.5, 3, None],
    ]}), 10**6)
    mapping = {im.F_STAGE: 0, im.F_ACTIVITY: 1, im.F_MINUTES: 2, im.F_DONE: 3, im.F_DUE: 4}
    result = im.parse_mapped(grid, "P", 1, mapping, quantity=4)
    assert result.ok, result.errors
    assert result.mode == importer.MODE_DETAILED and result.name == "linha" and result.quantity == 4
    assert result.due_date == date(2026, 12, 15)
    assert [(s.name, [(a.name, a.ideal_minutes, a.units_done) for a in s.activities]) for s in result.stages] == [
        ("Corte", [("Serrar", Decimal("10.00"), 2), ("Lixar", Decimal("5.50"), 1)]),
        ("Solda", [("Soldar", Decimal("20.00"), 0)]),
    ]
    # mesmo caminho de hoje: prévia assinada (payload) → revalida → grava
    result = importer.from_payload(importer.to_payload(result))
    project = importer.save(company, result, owner.id, name="Linha 3")
    db.session.commit()
    assert project.quantity == 4 and len(project.stages) == 2


def test_mapeamento_modo_simples_etapa_e_percentual(ctx):
    """Só etapa + % → modo simples: uma subatividade com o nome da etapa (TODO R4)."""
    company, owner = ctx
    grid = importer.load_grid("etapas.csv", _csv([
        ["Etapa", "% concluído", "Meta"],
        ["Chassi", "100%", "20"],
        ["Elétrica", "45", ""],
        ["Teste", "0,1", ""],
    ]), 10**6)
    view = im.inspect(grid)
    assert view.suggestion[im.F_STAGE] == 0 and view.suggestion[im.F_PCT] == 1 and view.suggestion[im.F_PLANNED] == 2
    result = im.parse_mapped(grid, view.sheet, view.header_row, view.suggestion)
    assert result.ok, result.errors
    assert result.mode == importer.MODE_SIMPLE and result.quantity == 20
    assert [(s.name, [(a.name, a.units_done) for a in s.activities]) for s in result.stages] == [
        ("Chassi", [("Chassi", 20)]), ("Elétrica", [("Elétrica", 9)]), ("Teste", [("Teste", 2)]),
    ]
    assert any("modo simples" in n for n in result.notes)
    payload = importer.to_payload(result)
    assert payload["mode"] == importer.MODE_SIMPLE and importer.from_payload(payload).mode == importer.MODE_SIMPLE
    project = importer.save(company, result, owner.id)
    db.session.commit()
    pcts = [round(e.progresso, 2) for e in svc.summary(project).etapas]
    assert pcts == [1.0, 0.45, 0.1]


def test_mapeamento_sem_meta_usa_100_para_guardar_o_percentual():
    grid = importer.load_grid("x.csv", _csv([["Fase", "Progresso"], ["A", "0,5"], ["B", "1"]]), 10**6)
    result = im.parse_mapped(grid, None, 1, {im.F_STAGE: 0, im.F_PCT: 1})
    assert result.ok and result.quantity == 100
    assert [s.activities[0].units_done for s in result.stages] == [50, 100]
    assert any("Meta não informada" in n for n in result.notes)


def test_mapeamento_erros_por_linha():
    grid = importer.load_grid("x.csv", _csv([
        ["Etapa", "Sub", "Tempo", "Previstas", "Peças", "%", "Prazo"],
        ["A", "a1", "dez", "5", "1", "", ""],        # linha 2: tempo
        ["A", "a2", "1", "6", "1", "", ""],          # linha 3: meta diferente
        ["", "", "", "", "", "", "32/13/2026"],      # linha 4: etapa vazia + data
        ["B", "b1", "1", "", "9", "", ""],           # linha 5: peças > meta
        ["B", "b2", "1", "", "", "150%", ""],        # linha 6: % inválido
    ]), 10**6)
    mapping = {im.F_STAGE: 0, im.F_ACTIVITY: 1, im.F_MINUTES: 2, im.F_PLANNED: 3, im.F_DONE: 4, im.F_PCT: 5, im.F_DUE: 6}
    result = im.parse_mapped(grid, None, 1, mapping)
    assert not result.ok
    found = {(e.line, e.column) for e in result.errors}
    assert found >= {
        (2, "tempo ideal"), (3, "Previstas (meta)"), (4, "Prazo (data)"), (4, "Etapa"),
        (5, exporter.COL_UNITS), (6, "% concluído"),
    }


def test_mapeamento_invalido_e_simples_com_etapa_repetida():
    grid = importer.load_grid("x.csv", _csv([["Etapa", "%"], ["A", "10%"], ["A", "20%"]]), 10**6)
    assert [e.message for e in im.parse_mapped(grid, None, 1, {im.F_PCT: 1}).errors] == ["Escolha a coluna da etapa."]
    bad = im.parse_mapped(grid, None, 1, {im.F_STAGE: 0, im.F_PCT: 0}).errors
    assert "usam a mesma coluna" in bad[0].message
    assert "inexistente" in im.parse_mapped(grid, None, 1, {im.F_STAGE: 7}).errors[0].message
    repeated = im.parse_mapped(grid, None, 1, {im.F_STAGE: 0, im.F_PCT: 1})
    assert [(e.line, "repetida" in e.message) for e in repeated.errors] == [(3, True)]
    assert im.parse_mapped(grid, "Outra", 1, {im.F_STAGE: 0}).errors[0].column == "aba"
    empty = importer.load_grid("x.csv", _csv([["Etapa"]]), 10**6)
    assert "nenhuma linha" in im.parse_mapped(empty, None, 1, {im.F_STAGE: 0}).errors[0].message


def test_mapeamento_respeita_limites(monkeypatch):
    monkeypatch.setattr(im, "MAX_ROWS", 2)
    grid = importer.load_grid("x.csv", _csv([["Etapa"], ["A"], ["B"], ["C"]]), 10**6)
    assert im.parse_mapped(grid, None, 1, {im.F_STAGE: 0}).errors[0].message == "mais de 2 linhas"
    monkeypatch.setattr(im, "MAX_ROWS", 2000)
    monkeypatch.setattr(im, "MAX_STAGES", 1)
    assert "mais de 1 etapas" in im.parse_mapped(grid, None, 1, {im.F_STAGE: 0}).errors[0].message


def test_grade_vai_e_volta_em_json_com_datas_e_linhas():
    grid = importer.load_grid("x.xlsx", _xlsx({"P": [["Etapa", "Prazo"], ["A", date(2026, 1, 2)]]}), 10**6)
    back = im.grid_from_data(im.grid_to_data(grid))
    assert back.sheets[0].rows == [["Etapa", "Prazo"], ["A", date(2026, 1, 2)]]
    assert back.kind == "xlsx" and back.filename == "x.xlsx"
    with pytest.raises(importer.ImportError_):
        im.grid_from_data({"s": [{"r": 1}]})


def test_formatos_proprios_continuam_reconhecidos_sozinhos(ctx):
    company, owner = ctx
    project = _project(company, owner)
    for name, data in (("p.csv", exporter.to_csv(project)), ("p.xlsx", exporter.to_xlsx(project))):
        result = importer.auto_parse(importer.load_grid(name, data, 10**7))
        assert result is not None and result.ok and result.source in ("csv", "xlsx")
    if REFERENCE.exists():
        result = importer.auto_parse(importer.load_grid("ref.xlsx", REFERENCE.read_bytes(), 10**7))
        assert result.source == importer.SOURCE_REFERENCE and len(result.stages) == 24


# ================================================================ exportação no layout da base


def test_layout_segue_a_referencia(ctx):
    company, owner = ctx
    project = _project(company, owner)
    wb, lay = export_layout.build_workbook(project)
    assert wb.sheetnames == ["Acompanhamento", "Equipe"]
    ws = wb["Acompanhamento"]
    # 3 etapas ativas com atividade + 1 vazia → 4 blocos de 8 linhas (igual à referência)
    assert [b.title for b in lay.blocks] == [12, 27, 42, 57]
    b = lay.blocks[0]
    assert ws["A12"].value == "1. Base" and ws["A13"].value == "Unidades previstas" and ws["A14"].value == "Subatividade"
    assert ws["C15"].value == '=IF(OR(A15="",$B$23=0),"",N(B15)/$B$23)'
    assert ws["E15"].value == '=IF(A15="","",IF($B$13>0,MIN(1,N(D15)/$B$13),0))'
    assert ws["F15"].value == '=IF(A15="","",N(B15)*$B$13)'
    assert ws["G15"].value == '=IF(A15="","",N(B15)*($B$13-MIN($B$13,N(D15))))'
    assert ws["F13"].value == "=IF(COUNT(E15:E22)=0,0,ROUND(MIN(E15:E22)*B13,0))"
    assert ws["E23"].value == (
        "=IF(B23>0,SUMPRODUCT(B15:B22,E15:E22)/B23,IF(COUNT(E15:E22)=0,0,SUM(E15:E22)/COUNT(E15:E22)))"
    )
    assert b.total == 23 and lay.summary == 73 and lay.indicators == 77 and lay.t1_first == 90
    assert ws[f"F{lay.t2_first}"].value == (
        f'=IF(AND(C{lay.t2_first}>0,B{lay.t2_first}>=C{lay.t2_first}),"Concluída",'
        f'IF(OR(B{lay.t2_first}>0,E{lay.t1_first}>0),"Em andamento","Não iniciada"))'
    )
    assert ws[f"E{lay.t1_total}"].value == f"=IF(F{lay.t1_total}=0,0,1-G{lay.t1_total}/F{lay.t1_total})"
    assert wb["Equipe"]["B8"].value == '=IF(B6*B7>0,B4/(B6*B7),"")'
    assert wb["Equipe"]["B4"].value == f"=Acompanhamento!G{lay.t1_total}"
    # entradas em amarelo, painéis congelados, larguras
    assert ws["B4"].fill.fgColor.rgb.endswith("FFF9DB") and ws["A15"].fill.fgColor.rgb.endswith("FFF9DB")
    assert ws.freeze_panes == "B2" and wb["Equipe"].freeze_panes == "A3"
    assert ws.column_dimensions["A"].width == 46
    assert ws["E15"].number_format == "0%" and ws[f"F{lay.t1_first}"].number_format == "#,##0.0"
    # arquivada não sai no layout
    assert "Arquivada" not in [c.value for row in ws.iter_rows() for c in row]


def test_layout_neutraliza_texto_do_usuario(ctx):
    company, owner = ctx
    project = _project(company, owner, name='=HYPERLINK("http://x","y")')
    ws = load_workbook(io.BytesIO(export_layout.to_xlsx_layout(project)))["Acompanhamento"]
    assert ws["A1"].value == "'=HYPERLINK(\"http://x\",\"y\")" and ws["A1"].data_type == "s"
    lay = export_layout.plan_layout([2, 2, 0, 1])
    assert ws[f"A{lay.blocks[3].title}"].value == "'+Fim" and ws[f"A{lay.blocks[1].first}"].value == "'=Lixar"
    user_texts = {"'=HYPERLINK(\"http://x\",\"y\")", "'+Fim", "'=Lixar"}
    for row in ws.iter_rows():
        for cell in row:
            if cell.data_type == "f":
                assert "HYPERLINK" not in str(cell.value) and "Lixar" not in str(cell.value)
            if cell.value in user_texts:
                assert cell.data_type == "s"


def _recalculate(data: bytes) -> bytes | None:
    """Recalcula o .xlsx no LibreOffice (sem LibreOffice: None e o teste pula)."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "in" / "planilha.xlsx"
        out = Path(tmp) / "out"
        src.parent.mkdir()
        src.write_bytes(data)
        env = {**os.environ, "SAL_USE_VCLPLUGIN": "svp", "HOME": tmp}
        cmd = [soffice, f"-env:UserInstallation=file://{tmp}/perfil", "--headless", "--calc",
               "--convert-to", "xlsx:Calc MS Excel 2007 XML", "--outdir", str(out), str(src)]
        try:
            subprocess.run(cmd, env=env, capture_output=True, timeout=120, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return None
        target = out / "planilha.xlsx"
        return target.read_bytes() if target.exists() else None


def test_formulas_recalculadas_batem_com_o_calc(ctx):
    company, owner = ctx
    project = _project(company, owner)
    recalculated = _recalculate(export_layout.to_xlsx_layout(project))
    if recalculated is None:
        pytest.skip("LibreOffice indisponível para recalcular")
    wb = load_workbook(io.BytesIO(recalculated), data_only=True)
    ws, team = wb["Acompanhamento"], wb["Equipe"]
    lay = export_layout.plan_layout([2, 2, 0, 1])
    res = svc.summary(project)
    errors = [c.coordinate for s in wb for row in s.iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith("#")]
    assert errors == []
    approx = lambda v: pytest.approx(v, rel=1e-9, abs=1e-9)  # noqa: E731
    ind = lay.ind
    for j, (block, etapa) in enumerate(zip(lay.blocks, res.etapas)):
        for k, atv in enumerate(etapa.atividades):
            r = block.first + k
            assert ws[f"C{r}"].value == (approx(atv.peso) if etapa.tempo_unidade_min else "")
            assert ws[f"E{r}"].value == approx(atv.pct)
            assert ws[f"F{r}"].value == approx(atv.tempo_total_min)
            assert ws[f"G{r}"].value == approx(atv.tempo_restante_min)
        assert ws[f"B{block.total}"].value == approx(etapa.tempo_unidade_min)
        assert ws[f"E{block.total}"].value == approx(etapa.progresso)
        assert ws[f"F{block.planned}"].value == etapa.unidades
        t1, t2 = lay.t1_first + j, lay.t2_first + j
        assert ws[f"C{t1}"].value == approx(etapa.peso_no_projeto)
        assert ws[f"F{t1}"].value == approx(etapa.tempo_total_min / 60)
        assert ws[f"G{t1}"].value == approx(etapa.tempo_restante_min / 60)
        assert ws[f"F{t2}"].value == etapa.status
    assert ws[f"B{ind['units']}"].value == res.unidades_concluidas
    assert ws[f"B{ind['stages']}"].value == res.etapas_concluidas
    assert (ws[f"B{ind['tasks']}"].value, ws[f"C{ind['tasks']}"].value) == (res.tarefas_concluidas, res.tarefas)
    assert (ws[f"B{ind['units_sum']}"].value, ws[f"C{ind['units_sum']}"].value) == (
        res.unidades_etapas, res.unidades_etapas_previstas)
    assert ws[f"D{ind['worked']}"].value == approx(res.progresso_geral)
    assert ws[f"B{ind['unit_time']}"].value == approx(res.tempo_unidade_min / 60)
    assert ws[f"B{ind['left']}"].value == approx(res.tempo_restante_min / 60)
    assert ws[f"B{ind['days']}"].value == approx(res.dias_uteis_restantes)
    assert ws[f"B{ind['no_time']}"].value == calc.etapas_sem_tempo(res.etapas)
    assert ws["B6"].value == approx(res.progresso_geral)
    assert ws["B5"].value == f"{res.unidades_concluidas} de {res.previstas}"
    assert team["B4"].value == approx(res.tempo_restante_min / 60)
    for pessoas, dias in calc.equipe_x_prazo(res.tempo_restante_min / 60, float(project.hours_per_day)):
        assert team[f"C{12 + pessoas}"].value == approx(dias)


def test_formulas_da_referencia_recalculadas_batem_com_a_exportacao(ctx):
    """A planilha de referência importada e exportada de novo dá os mesmos números."""
    company, owner = ctx
    if not REFERENCE.exists():  # pragma: no cover
        pytest.skip("planilha de referência ausente")
    result = importer.parse_upload("ref.xlsx", REFERENCE.read_bytes(), 10**7)
    project = importer.save(company, result, owner.id)
    db.session.commit()
    recalculated = _recalculate(export_layout.to_xlsx_layout(project))
    if recalculated is None:
        pytest.skip("LibreOffice indisponível para recalcular")
    ours = load_workbook(io.BytesIO(recalculated), data_only=True)
    ref = load_workbook(REFERENCE, data_only=True)
    lay = export_layout.plan_layout([len(s.activities) for s in result.stages])
    ind = lay.ind
    assert ours["Acompanhamento"][f"B{ind['left']}"].value == pytest.approx(ref["Acompanhamento"]["B383"].value)
    assert ours["Acompanhamento"][f"D{ind['worked']}"].value == pytest.approx(ref["Acompanhamento"]["D381"].value)
    assert ours["Acompanhamento"][f"B{ind['units']}"].value == ref["Acompanhamento"]["B377"].value
    assert ours["Equipe"]["B8"].value == pytest.approx(ref["Equipe"]["B8"].value)


# ================================================================ round-trip


def _shape(project: Project) -> tuple:
    from app.services.projects import active_activities, active_stages

    return (
        project.name, project.quantity, project.start_date, project.due_date, project.people,
        Decimal(project.hours_per_day),
        [(s.name, [(a.name, Decimal(a.ideal_minutes), a.units_done) for a in active_activities(s)])
         for s in active_stages(project)],
    )


def test_exportar_layout_e_importar_reproduz_o_projeto(ctx):
    company, owner = ctx
    project = _project(company, owner, name="-Lote @especial")
    data = export_layout.to_xlsx_layout(project)
    result = importer.parse_upload("planilha.xlsx", data, 10**7)
    assert result.ok, result.errors
    assert result.source == importer.SOURCE_REFERENCE
    result = importer.from_payload(importer.to_payload(result))
    assert result.ok
    imported = importer.save(company, result, owner.id)
    db.session.commit()
    db.session.expire_all()
    original = db.session.get(Project, project.id)
    imported = db.session.get(Project, imported.id)
    assert _shape(imported) == _shape(original)
    assert svc.summary(imported) == svc.summary(original)


# ================================================================ rotas


def _upload(client, app, filename, content, extra=None):
    return post(client, app, "/app/importar", {"file": (io.BytesIO(content), filename), **(extra or {})},
                content_type="multipart/form-data")


def _hidden(page: str, name: str) -> str:
    match = re.search(rf'<input[^>]*name="{name}"[^>]*>', page)
    return html.unescape(re.search(r'value="([^"]*)"', match.group(0)).group(1))


def test_importar_qualquer_planilha_pelas_telas(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    data = _xlsx({
        "Capa": [["Nada aqui"]],
        "Linha": [["Fase", "Tarefa", "Minutos", "Feitas", "Qtd"], ["Corte", "Serrar", 10, 2, 4], [None, "Lixar", 5, 4, 4]],
    })
    page = _upload(client, app, "linha.xlsx", data)
    assert page.status_code == 200 and "Escolher colunas" in text_of(page)
    grid = _hidden(page.get_data(as_text=True), "grid")
    # troca de aba: relê e sugere as colunas da aba nova
    page = post(client, app, "/app/importar/colunas", {"grid": grid, "current_sheet": "Capa", "sheet": "Linha", "action": "ver"})
    assert page.status_code == 200 and "Serrar" in text_of(page)
    # tela: um select “Isto é…” por coluna, com a sugestão já marcada (coluna A = Etapa)
    assert re.search(r'<select[^>]*name="col_0"[^>]*>\s*<option value="">Não usar</option>\s*<option value="etapa" selected>',
                     page.get_data(as_text=True))
    form = {"grid": grid, "current_sheet": "Linha", "sheet": "Linha", "header_row": 1, "etapa": "0",
            "subatividade": "1", "tempo": "2", "concluidas": "3", "previstas": "4", "name": "Linha 3"}
    preview = post(client, app, "/app/importar/colunas", form)
    assert preview.status_code == 200 and "Pré-visualização" in text_of(preview)
    payload = _hidden(preview.get_data(as_text=True), "payload")
    response = post(client, app, "/app/importar/confirmar", {"payload": payload, "name": "Linha 3"})
    assert response.status_code == 303
    with app.app_context():
        project = db.session.query(Project).filter_by(company_id=a.company_id, name="Linha 3").one()
        assert project.quantity == 4
        assert [(x.name, x.units_done) for x in project.stages[0].activities] == [("Serrar", 2), ("Lixar", 4)]
    # mapeamento com erro: volta para as colunas com os erros por linha (400), nada gravado
    bad = post(client, app, "/app/importar/colunas", {**form, "tempo": "3", "concluidas": "3"})
    assert bad.status_code == 400 and "mesma coluna" in text_of(bad) and "Escolher colunas" in text_of(bad)
    bad = post(client, app, "/app/importar/colunas", {**form, "previstas": "", "quantity": "1"})
    assert bad.status_code == 400 and "Linha 2" in text_of(bad)
    # grade adulterada ou ausente
    assert post(client, app, "/app/importar/colunas", {**form, "grid": grid + "x"}).status_code == 400
    assert post(client, app, "/app/importar/colunas", {}).status_code == 400
    with app.app_context():
        assert db.session.query(Project).filter_by(company_id=a.company_id, name="Linha 3").count() == 1


def test_formato_reconhecido_pode_ir_para_colunas(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    csv_bytes = client.get(f"/app/projetos/{a.project_id}/exportar.csv").data
    assert "Pré-visualização" in text_of(_upload(client, app, "p.csv", csv_bytes))
    page = _upload(client, app, "p.csv", csv_bytes, {"map_columns": "y"})
    assert page.status_code == 200 and "Escolher colunas" in text_of(page)


def test_exportar_planilha_no_layout_pela_tela_e_importar_de_volta(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    response = client.get(f"/app/projetos/{a.project_id}/exportar-planilha.xlsx")
    assert response.status_code == 200 and response.data[:2] == b"PK"
    assert response.headers["Content-Disposition"] == 'attachment; filename="projeto-a-planilha.xlsx"'
    assert load_workbook(io.BytesIO(response.data)).sheetnames == ["Acompanhamento", "Equipe"]
    preview = _upload(client, app, "volta.xlsx", response.data)
    assert preview.status_code == 200 and "Pré-visualização" in text_of(preview)
    operator = app.test_client()
    login(operator, app, a.operator_email)
    assert operator.get(f"/app/projetos/{a.project_id}/exportar-planilha.xlsx").status_code == 403
