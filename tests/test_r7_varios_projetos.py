"""R7 — arquivo da equipe com VÁRIOS projetos (abas “Acompanhamento/Equipe/Como funciona” do
principal e “<Nome> - Acompanhamento/Equipe/Como funciona” dos demais; regra da base: um projeto
existe se as três abas existirem).

A planilha de teste é SINTÉTICA: copia as abas da referência pública
(docs/referencia/acompanhamento_montagem_v4.xlsx) com outros títulos e nomes fictícios.
"""

from __future__ import annotations

import html
import io
import re
from pathlib import Path

import pytest
from openpyxl import load_workbook
from sqlalchemy import select

from app.extensions import db
from app.models import Project, Subscription
from app.services import importer
from app.services import plans as catalog
from app.services import projects as svc
from tests.conftest import login, post, text_of

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "referencia" / "acompanhamento_montagem_v4.xlsx"


def _grid(titles: list[str]) -> importer.Grid:
    return importer.Grid("xlsx", "x.xlsx", [importer.Sheet(t, [["x"]]) for t in titles])


def _many_xlsx(extra: dict[str, str], *, incomplete: str | None = None) -> bytes:
    """Referência + um projeto por item de ``extra`` (nome → título do A1). ``incomplete`` =
    nome de um projeto só com Acompanhamento e Equipe (sem “Como funciona”: não conta)."""
    wb = load_workbook(REFERENCE)
    base = {title: wb[title] for title in ("Acompanhamento", "Equipe", "Como funciona")}
    for name, a1 in [*extra.items(), *([(incomplete, f"Acompanhamento da Montagem – {incomplete}")] if incomplete else [])]:
        roles = ("Acompanhamento", "Equipe") if name == incomplete else ("Acompanhamento", "Equipe", "Como funciona")
        for role in roles:
            copy = wb.copy_worksheet(base[role])
            copy.title = f"{name} - {role}"
            if role == "Acompanhamento":
                copy["A1"] = a1
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


@pytest.fixture(scope="module")
def many_bytes() -> bytes:
    return _many_xlsx({"Agro": "Acompanhamento da Montagem – Agro", "Linha Leve": "Acompanhamento da Montagem – Linha Leve"},
                      incomplete="Rascunho")


# ---------------------------------------------------------------- funções puras


def test_regra_das_tres_abas():
    grid = _grid([
        "Acompanhamento", "Equipe", "Como funciona",
        "Agro - Acompanhamento", "Agro - Equipe", "Agro - Como funciona",
        "Fase 2 – Norte - Acompanhamento", "Fase 2 – Norte - Equipe", "Fase 2 – Norte - Como funciona",
        "Sem ajuda - Acompanhamento", "Sem ajuda - Equipe",  # falta “Como funciona”: não é projeto
        "Resumo",
    ])
    found = importer.reference_projects(grid)
    assert [(p.key, p.tracking, p.team) for p in found] == [
        ("", "Acompanhamento", "Equipe"),
        ("Agro", "Agro - Acompanhamento", "Agro - Equipe"),
        ("Fase 2 – Norte", "Fase 2 – Norte - Acompanhamento", "Fase 2 – Norte - Equipe"),
    ]
    # caixa e travessão não importam; o principal vem primeiro mesmo se as abas dele vêm depois
    grid = _grid(["agro – acompanhamento", "AGRO - EQUIPE", "Agro - como funciona", "Acompanhamento", "Equipe", "Como funciona"])
    assert [p.key for p in importer.reference_projects(grid)] == ["", "agro"]
    assert importer.reference_projects(_grid(["Planilha1", "Dados"])) == []


def test_nome_do_projeto_pelo_titulo():
    assert importer.project_name_from_title("Acompanhamento da Montagem – Agro") == "Agro"
    assert importer.project_name_from_title("Acompanhamento da montagem - Linha Leve") == "Linha Leve"
    assert importer.project_name_from_title("Lote 7", "X") == "Lote 7"
    assert importer.project_name_from_title("", "Agro") == "Agro"


def test_varios_projetos_um_resultado_por_projeto(many_bytes):
    grid = importer.load_grid("equipe.xlsx", many_bytes, 10 * 1024 * 1024)
    found = importer.parse_reference_many(grid)
    assert [r.name for _, r in found] == ["SoBot", "Agro", "Linha Leve"]  # “Rascunho” não tem as 3 abas
    single = importer.parse_reference(importer.load_grid("ref.xlsx", REFERENCE.read_bytes(), 10 * 1024 * 1024))
    for _, result in found:
        assert result.ok and result.source == importer.SOURCE_REFERENCE
        assert len(result.stages) == len(single.stages) == 24
        assert result.quantity == single.quantity and result.people == single.people
        assert [s.name for s in result.stages] == [s.name for s in single.stages]


def test_planilha_de_um_projeto_continua_igual():
    data = REFERENCE.read_bytes()
    grid = importer.load_grid("ref.xlsx", data, 10 * 1024 * 1024)
    assert len(importer.parse_reference_many(grid)) == 1  # um só → fluxo de sempre
    result = importer.auto_parse(grid)
    assert result.ok and result.name == "Acompanhamento da Montagem – SoBot" and len(result.stages) == 24


def test_projeto_com_erro_fica_de_fora_com_os_erros():
    wb = load_workbook(io.BytesIO(_many_xlsx({"Agro": "Acompanhamento da Montagem – Agro"})))
    ws = wb["Agro - Acompanhamento"]
    meta_row = next(r for r in range(1, 60) if str(ws.cell(r, 1).value or "").casefold().startswith("meta"))
    ws.cell(meta_row, 2).value = "muitas"
    buffer = io.BytesIO()
    wb.save(buffer)
    found = importer.parse_reference_many(importer.load_grid("x.xlsx", buffer.getvalue(), 10 * 1024 * 1024))
    assert [r.ok for _, r in found] == [True, False]
    assert any("meta" in e.column for e in found[1][1].errors)


# ---------------------------------------------------------------- rotas


def _upload(client, app, content, extra=None):
    return post(client, app, "/app/importar", {"file": (io.BytesIO(content), "equipe.xlsx"), **(extra or {})},
                content_type="multipart/form-data")


def _hidden(page: str, name: str) -> str:
    match = re.search(rf'<input[^>]*name="{name}"[^>]*>', page)
    return html.unescape(re.search(r'value="([^"]*)"', match.group(0)).group(1))


def _names(app, company_id) -> set[str]:
    with app.app_context():
        return set(db.session.execute(select(Project.name).where(Project.company_id == company_id)).scalars())


def test_escolher_e_importar_varios_projetos(client, app, tenants, many_bytes):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    page = _upload(client, app, many_bytes)
    body = page.get_data(as_text=True)
    assert page.status_code == 200 and "Escolher projetos" in body
    assert all(n in body for n in ("SoBot", "Agro", "Linha Leve")) and "Rascunho" not in body
    assert body.count('name="pick"') == 3 and body.count("checked") >= 3  # todos marcados
    payload = _hidden(body, "payload")
    # nenhum marcado → fica no passo 2 com aviso
    none = post(client, app, "/app/importar/projetos", {"payload": payload})
    assert none.status_code == 400 and "Marque ao menos um projeto" in text_of(none)
    # escolhe Agro e Linha Leve → prévia só com eles
    preview = post(client, app, "/app/importar/projetos", {"payload": payload, "pick": ["1", "2", "9", "x"]})
    text = text_of(preview)
    assert preview.status_code == 200 and "2 projetos para importar" in text and "__name\">SoBot<" not in text
    before = _names(app, a.company_id)
    done = post(client, app, "/app/importar/confirmar-varios", {"payload": _hidden(preview.get_data(as_text=True), "payload")})
    assert done.status_code == 303
    assert _names(app, a.company_id) - before == {"Agro", "Linha Leve"}
    with app.app_context():
        agro = db.session.execute(select(Project).where(Project.company_id == a.company_id, Project.name == "Agro")).scalar_one()
        assert len(svc.active_stages(agro)) == 24


def test_limite_do_plano_vale_para_o_lote(client, app, tenants, many_bytes):
    a, _ = tenants
    with app.app_context():
        sub = db.session.execute(select(Subscription).where(Subscription.company_id == a.company_id)).scalar_one_or_none()
        plan_id = catalog.get_plan("essencial").id  # 3 projetos ativos
        if sub is None:
            db.session.add(Subscription(company_id=a.company_id, provider="fake", plan_id=plan_id, status="active"))
        else:
            sub.plan_id, sub.status = plan_id, "active"
        db.session.commit()
    login(client, app, a.supervisor_email)
    body = _upload(client, app, many_bytes).get_data(as_text=True)
    assert "Passa do limite do plano" in body  # 1 ativo + 3 escolhidos > 3
    payload = _hidden(body, "payload")
    preview = post(client, app, "/app/importar/projetos", {"payload": payload, "pick": ["0", "1", "2"]})
    before = _names(app, a.company_id)
    blocked = post(client, app, "/app/importar/confirmar-varios", {"payload": _hidden(preview.get_data(as_text=True), "payload")})
    assert blocked.status_code == 402 and "desmarque 1" in text_of(blocked)
    assert _names(app, a.company_id) == before  # nada gravado
    preview = post(client, app, "/app/importar/projetos", {"payload": payload, "pick": ["0", "1"]})
    ok = post(client, app, "/app/importar/confirmar-varios", {"payload": _hidden(preview.get_data(as_text=True), "payload")})
    assert ok.status_code == 303 and len(_names(app, a.company_id) - before) == 2


def test_operador_nao_importa_varios(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    assert post(client, app, "/app/importar/projetos", {"payload": "x"}).status_code == 403
    assert post(client, app, "/app/importar/confirmar-varios", {"payload": "x"}).status_code == 403


def test_quero_escolher_as_colunas_ignora_os_varios_projetos(client, app, tenants, many_bytes):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    page = _upload(client, app, many_bytes, {"map_columns": "y"})
    assert page.status_code == 200 and "Escolher colunas" in text_of(page)
