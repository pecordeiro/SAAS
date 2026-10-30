"""Importação com mapeamento: ajuda por campo e unidade do tempo (ADR-0019 §5).

O servidor converte horas em minutos (mesmos limites de sempre) e avisa quando a unidade
parece errada; o navegador só escolhe entre "minutos" e "horas"."""

from __future__ import annotations

import html
import io
import re
from decimal import Decimal

import pytest
from openpyxl import Workbook

from app.extensions import db
from app.models import Project
from app.services import import_mapping as im
from app.services import importer
from tests.conftest import login, post, text_of

MAPPING = {im.F_STAGE: 0, im.F_ACTIVITY: 1, im.F_MINUTES: 2, im.F_PLANNED: 3}


def _grid(rows):
    return importer.Grid("xlsx", "t.xlsx", [importer.Sheet("Aba", [["Etapa", "Tarefa", "Tempo", "Qtd"], *rows])])


def _parse(rows, unit=im.UNIT_MINUTES, mapping=MAPPING):
    return im.parse_mapped(_grid(rows), "Aba", 1, mapping, time_unit=unit)


def _minutes(result):
    return [a.ideal_minutes for s in result.stages for a in s.activities]


# ---------------------------------------------------------------- serviço


def test_horas_viram_minutos_no_servidor():
    result = _parse([["Solda", "Soldar", 1.5, 4], ["Solda", "Lixar", "0,25", 4], ["Pintura", "Pintar", "2", 4]], im.UNIT_HOURS)
    assert result.ok and result.time_unit == im.UNIT_HOURS
    assert _minutes(result) == [Decimal("90.00"), Decimal("15.00"), Decimal("120.00")]
    assert result.total_minutes == Decimal("225.00")


def test_horas_com_virgula_decimal():
    result = _parse([["A", "x", "1,5", 2], ["A", "y", "0,333", 2]], im.UNIT_HOURS)
    assert _minutes(result) == [Decimal("90.00"), Decimal("19.98")]


def test_minutos_continuam_iguais():
    result = _parse([["A", "x", "12,5", 2]])
    assert _minutes(result) == [Decimal("12.50")] and result.time_unit == im.UNIT_MINUTES


def test_unidade_invalida_e_recusada_sem_padrao_silencioso():
    for bad in ("", "dias", "HORAS", None):
        result = _parse([["A", "x", 1, 2]], bad)
        assert not result.ok and result.errors[0].column == "unidade" and not result.stages


def test_limites_valem_depois_da_conversao():
    # 2000 h = 120000 min > MAX_MINUTES (100000); 1666 h = 99960 min ainda cabe
    assert not _parse([["A", "x", 2000, 2]], im.UNIT_HOURS).ok
    assert _parse([["A", "x", 1666, 2]], im.UNIT_HOURS).ok
    assert not _parse([["A", "x", -1, 2]], im.UNIT_HOURS).ok
    assert not _parse([["A", "x", "abc", 2]], im.UNIT_HOURS).ok
    assert not _parse([["A", "x", 100001, 2]], im.UNIT_MINUTES).ok


def test_modo_simples_sem_tempo_usa_padrao_em_minutos_mesmo_em_horas():
    mapping = {im.F_STAGE: 0, im.F_PLANNED: 3}
    result = _parse([["A", "", "", 2]], im.UNIT_HOURS, mapping)
    assert result.ok and result.time_unit is None
    assert _minutes(result) == [Decimal(str(im.SIMPLE_DEFAULT_MINUTES)).quantize(Decimal("0.01"))]


def test_aviso_de_provavel_unidade_errada():
    small = _parse([["A", "x", "0,5", 2], ["A", "y", "0,25", 2]], im.UNIT_MINUTES)
    assert small.ok and len(small.warnings) == 1 and "Horas" in small.warnings[0]
    big = _parse([["A", "x", 60, 2], ["A", "y", 90, 2]], im.UNIT_HOURS)
    assert big.ok and len(big.warnings) == 1 and "Minutos" in big.warnings[0]
    assert not _parse([["A", "x", 12, 2]], im.UNIT_MINUTES).warnings
    assert not _parse([["A", "x", "0,2", 2]], im.UNIT_HOURS).warnings
    assert not _parse([["A", "x", 0, 2]], im.UNIT_MINUTES).warnings  # zero não conta


def test_payload_nao_leva_aviso_nem_unidade():
    payload = importer.to_payload(_parse([["A", "x", "0,5", 2]]))
    assert "warnings" not in payload and "time_unit" not in payload
    assert importer.from_payload(payload).ok


def test_ajuda_cobre_todos_os_campos():
    assert set(im.FIELD_HELP) == set(im.FIELD_KEYS)
    assert "Soldagem" in im.FIELD_HELP[im.F_STAGE]
    assert "modo simples" in im.FIELD_HELP[im.F_ACTIVITY] and "Soldar suporte" in im.FIELD_HELP[im.F_ACTIVITY]


# ---------------------------------------------------------------- rotas


def _xlsx(rows) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Linha"
    for row in rows:
        ws.append(row)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def _hidden(page: str, name: str) -> str:
    match = re.search(rf'<input[^>]*name="{name}"[^>]*>', page)
    return html.unescape(re.search(r'value="([^"]*)"', match.group(0)).group(1))


@pytest.fixture()
def tela(client, app, tenants):
    a, b = tenants
    login(client, app, a.supervisor_email)
    data = _xlsx([["Fase", "Tarefa", "Tempo", "Qtd"], ["Corte", "Serrar", "1,5", 4], [None, "Lixar", "0,25", 4]])
    page = post(client, app, "/app/importar", {"file": (io.BytesIO(data), "x.xlsx"), "map_columns": "y"},
                content_type="multipart/form-data")
    assert page.status_code == 200
    form = {"grid": _hidden(page.get_data(as_text=True), "grid"), "current_sheet": "Linha", "sheet": "Linha",
            "header_row": 1, "etapa": "0", "subatividade": "1", "tempo": "2", "previstas": "3", "name": "Horas"}
    return page, form, a


def test_tela_tem_ajuda_e_seletor_de_unidade(tela):
    page, _, _ = tela
    text = text_of(page)
    assert "O grupo de trabalho, ex.: Soldagem" in text
    assert "Soldar suporte" in text and "modo simples" in text
    assert "ex.: 45%" in text and "31/12/2026" in text and "ex.: 200" in text
    body = page.get_data(as_text=True)
    assert re.search(r'<select[^>]*name="time_unit"', body)
    assert re.search(r'<option[^>]*(selected[^>]*value="minutos"|value="minutos"[^>]*selected)', body)
    assert 'value="horas"' in body


def test_fluxo_horas_previa_convertida_e_confirmacao(client, app, tela):
    _, form, a = tela
    prev = post(client, app, "/app/importar/colunas", {**form, "time_unit": "horas"})
    text = text_of(prev)
    assert prev.status_code == 200 and "Prévia" in text
    assert "105,00 min" in text and "horas (convertidas para minutos)" in text
    assert "Confira a unidade do tempo" not in text
    # voltar às colunas devolve a unidade escolhida
    assert re.search(r'name="time_unit" value="horas"', prev.get_data(as_text=True))
    payload = _hidden(prev.get_data(as_text=True), "payload")
    assert post(client, app, "/app/importar/confirmar", {"payload": payload, "name": "Horas"}).status_code == 303
    with app.app_context():
        project = db.session.query(Project).filter_by(company_id=a.company_id, name="Horas").one()
        assert [x.ideal_minutes for x in project.stages[0].activities] == [Decimal("90.00"), Decimal("15.00")]


def test_fluxo_aviso_na_previa_nao_bloqueia(client, app, tela):
    _, form, _ = tela
    prev = post(client, app, "/app/importar/colunas", {**form, "time_unit": "minutos"})  # 1,5 e 0,25 min
    text = text_of(prev)
    assert prev.status_code == 200 and "Prévia" in text
    assert "Confira a unidade do tempo" in text and "escolha “Horas”" in text
    assert "Importar projeto" in text


def test_fluxo_unidade_ausente_vale_minutos_e_invalida_e_erro(client, app, tela):
    _, form, a = tela
    assert "minutos" in text_of(post(client, app, "/app/importar/colunas", form))
    bad = post(client, app, "/app/importar/colunas", {**form, "time_unit": "dias"})
    assert bad.status_code == 400 and "Unidade do tempo inválida" in text_of(bad) and "Escolher colunas" in text_of(bad)
    with app.app_context():
        assert db.session.query(Project).filter_by(company_id=a.company_id, name="Horas").count() == 0


def test_fluxo_sem_csrf_recusado(client, app, tela):
    _, form, _ = tela
    assert client.post("/app/importar/colunas", data={**form, "time_unit": "horas"}).status_code == 400
