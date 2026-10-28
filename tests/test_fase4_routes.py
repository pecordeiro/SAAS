"""Fase 4 — rotas: limite de plano (402 chamando a rota direto), modo leitura, modelos,
novo projeto a partir de modelo, edição, desfazer, importar e exportar."""

from __future__ import annotations

import io
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from app.extensions import db
from app.models import Activity, Company, Project, ProgressEntry, Stage, Subscription, Template, User
from app.services import exporter
from app.services import projects as svc
from app.services import templates as tsvc
from app.services.plans import ESSENCIAL, get_plan
from tests.conftest import login, post, text_of

XLSX = Path(__file__).resolve().parents[1] / "docs" / "referencia" / "acompanhamento_montagem_v4.xlsx"

NEW = {"name": "Lote novo", "quantity": 4, "people": 1, "hours_per_day": "8",
       "stages-0-name": "Etapa", "stages-0-activities": "Corte; 10"}


def _subscribe(app, company_id, status="active", **kw):
    with app.app_context():
        db.session.add(Subscription(company_id=company_id, plan_id=get_plan(ESSENCIAL).id, provider="fake", status=status, **kw))
        db.session.commit()


def _add_projects(app, company_id, n):
    with app.app_context():
        company = db.session.get(Company, company_id)
        for i in range(n):
            svc.create_project(company, name=f"Extra {i}", quantity=1, start_date=None, due_date=None, people=1,
                               hours_per_day=Decimal("8"), stages=[])
        db.session.commit()


def _count(app, model, **filters):
    with app.app_context():
        return db.session.query(model).filter_by(**filters).count()


# ---------------------------------------------------------------- 402


def test_criar_sexto_projeto_no_essencial_responde_402_chamando_a_rota(client, app, tenants):
    a, _ = tenants
    _subscribe(app, a.company_id)
    _add_projects(app, a.company_id, 4)  # 5 ativos
    login(client, app, a.supervisor_email)
    before = _count(app, Project, company_id=a.company_id)
    response = post(client, app, "/app/projetos/novo", NEW)
    assert response.status_code == 402
    page = text_of(response)
    assert "Essencial permite 5 projetos ativos" in page and "Ver planos" in page
    assert _count(app, Project, company_id=a.company_id) == before
    # duplicar também é criação
    assert post(client, app, f"/app/projetos/{a.project_id}/duplicar").status_code == 402
    assert _count(app, Project, company_id=a.company_id) == before


def test_empresa_sem_assinatura_ativa_le_mas_nao_escreve(client, app, tenants):
    a, _ = tenants
    _subscribe(app, a.company_id, status="expired")
    login(client, app, a.operator_email)
    page = client.get(f"/app/projetos/{a.project_id}")
    assert page.status_code == 200 and "modo leitura" in text_of(page)
    response = post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 1, "version": 1})
    assert response.status_code == 402
    assert "modo leitura" in text_of(response)
    assert _count(app, ProgressEntry, company_id=a.company_id) == 0
    client = app.test_client()
    login(client, app, a.supervisor_email)
    assert post(client, app, "/app/projetos/novo", NEW).status_code == 402
    assert post(client, app, f"/app/etapas/{a.stage_id}/renomear", {"name": "X"}).status_code == 402
    assert client.get(f"/app/projetos/{a.project_id}/exportar.csv").status_code == 200  # leitura liberada


# ---------------------------------------------------------------- modelos e novo projeto


def test_fluxo_de_modelos_pelas_telas(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    assert "Nenhum modelo de etapas" in text_of(client.get("/app/modelos"))
    assert client.get("/app/modelos/novo").status_code == 200
    assert post(client, app, "/app/modelos/novo", {"name": ""}).status_code == 400
    response = post(client, app, "/app/modelos/novo", {
        "name": "Compacto", "stages-0-name": "Base", "stages-0-activities": "Corte; 60\nFuração; 45,5",
    })
    assert response.status_code == 303
    with app.app_context():
        template = db.session.query(Template).filter_by(company_id=a.company_id).one()
        template_id = template.id
    # nome repetido
    assert post(client, app, "/app/modelos/novo", {
        "name": "compacto", "stages-0-name": "B", "stages-0-activities": "x; 1"}).status_code == 400
    page = text_of(client.get("/app/modelos"))
    assert "Compacto" in page and "v1" in page
    edit = text_of(client.get(f"/app/modelos/{template_id}"))
    assert "Furação; 45,5" in edit
    # novo projeto a partir do modelo (snapshot)
    response = post(client, app, "/app/projetos/novo", {"template_id": str(template_id), "name": "Do modelo",
                                                       "quantity": 3, "people": 1, "hours_per_day": "8"})
    assert response.status_code == 303
    # salvar igual → sem versão nova; salvar diferente → v2
    same = {"name": "Compacto", "stages-0-name": "Base", "stages-0-activities": "Corte; 60\nFuração; 45,5"}
    assert post(client, app, f"/app/modelos/{template_id}", same).status_code == 303
    changed = {**same, "stages-0-activities": "Corte; 50\nFuração; 45,5"}
    assert post(client, app, f"/app/modelos/{template_id}", changed).status_code == 303
    assert post(client, app, f"/app/modelos/{template_id}", {**changed, "name": ""}).status_code == 400
    assert "v2" in text_of(client.get(f"/app/modelos/{template_id}/versoes"))
    with app.app_context():
        project = db.session.query(Project).filter_by(name="Do modelo").one()
        assert [a.ideal_minutes for a in project.stages[0].activities] == [Decimal("60"), Decimal("45.5")]
        project_id = project.id
    # comparar e aplicar (só com confirmação)
    compare = text_of(client.get(f"/app/projetos/{project_id}/modelo"))
    assert "Tempo ideal de “Corte”" in compare
    assert post(client, app, f"/app/projetos/{project_id}/modelo/aplicar", {}).status_code == 303
    with app.app_context():
        assert db.session.get(Project, project_id).stages[0].activities[0].ideal_minutes == Decimal("60")
        version_id = db.session.get(Template, template_id).current_version_id
    response = post(client, app, f"/app/projetos/{project_id}/modelo/aplicar", {"confirm": "y", "version_id": str(version_id)})
    assert response.status_code == 303
    with app.app_context():
        assert db.session.get(Project, project_id).stages[0].activities[0].ideal_minutes == Decimal("50")
    history = text_of(client.get(f"/app/projetos/{project_id}/historico"))
    assert "Versão do modelo aplicada" in history and "v1 → v2" in history
    assert "Nada a aplicar" in text_of(client.get(f"/app/projetos/{project_id}/modelo"))
    # arquivar o modelo
    assert post(client, app, f"/app/modelos/{template_id}/arquivar").status_code == 303
    assert client.get(f"/app/modelos/{template_id}").status_code == 404


def test_comparar_projeto_sem_modelo_e_404(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    assert client.get(f"/app/projetos/{a.project_id}/modelo").status_code == 404


def test_operador_nao_acessa_telas_de_supervisor(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    for url in ("/app/modelos", "/app/importar", f"/app/projetos/{a.project_id}/exportar.csv",
                f"/app/projetos/{a.project_id}/editar"):
        assert client.get(url).status_code == 403, url
    assert post(client, app, f"/app/projetos/{a.project_id}/duplicar").status_code == 403


# ---------------------------------------------------------------- edição


def test_edicao_do_projeto_pelas_telas(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    page = client.get(f"/app/projetos/{a.project_id}/editar")
    assert page.status_code == 200 and "Etapas e atividades" in text_of(page)
    data = {"name": "Renomeado", "quantity": 12, "people": 2, "hours_per_day": "8"}
    assert post(client, app, f"/app/projetos/{a.project_id}/editar", data).status_code == 303
    assert post(client, app, f"/app/projetos/{a.project_id}/editar", {**data, "quantity": 0}).status_code == 400
    post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 5})
    response = post(client, app, f"/app/projetos/{a.project_id}/editar", {**data, "quantity": 3})
    assert response.status_code == 400 and "não pode ser menor" in text_of(response)
    assert post(client, app, f"/app/etapas/{a.stage_id}/renomear", {"name": ""}).status_code == 303
    assert post(client, app, f"/app/etapas/{a.stage_id}/renomear", {"name": "Nova etapa"}).status_code == 303
    assert post(client, app, f"/app/etapas/{a.stage_id}/mover", {"direction": "sideways"}).status_code == 400
    assert post(client, app, f"/app/atividades/{a.activity_id}/mover", {"direction": "x"}).status_code == 400
    assert post(client, app, f"/app/atividades/{a.activity_id}/mover", {"direction": "down"}).status_code == 303
    assert post(client, app, f"/app/atividades/{a.activity_id}/editar", {"name": "", "ideal_minutes": "x"}).status_code == 303
    assert post(client, app, f"/app/atividades/{a.activity_id}/editar", {"name": "Nova", "ideal_minutes": "7,5"}).status_code in (303, 400)
    assert post(client, app, f"/app/atividades/{a.activity_id}/editar", {"name": "Nova", "ideal_minutes": "7.5"}).status_code == 303
    with app.app_context():
        activity = db.session.get(Activity, a.activity_id)
        assert (activity.name, activity.ideal_minutes, activity.position) == ("Nova", Decimal("7.5"), 1)
        assert db.session.get(Stage, a.stage_id).name == "Nova etapa"
        assert db.session.get(Project, a.project_id).name == "Renomeado"
    assert post(client, app, f"/app/atividades/{a.activity_id}/arquivar").status_code == 303
    # arquivada: some da tela (404 em ações), mas o histórico mantém o registro
    assert post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 1}).status_code == 404
    assert "Nova" in text_of(client.get(f"/app/projetos/{a.project_id}/historico"))
    assert post(client, app, f"/app/etapas/{a.stage_id}/arquivar").status_code == 303
    # duplicar e arquivar projeto
    assert post(client, app, f"/app/projetos/{a.project_id}/duplicar").status_code == 303
    assert post(client, app, f"/app/projetos/{a.project_id}/arquivar", {}).status_code == 303
    assert client.get(f"/app/projetos/{a.project_id}").status_code == 200  # sem confirmação, nada muda
    assert post(client, app, f"/app/projetos/{a.project_id}/arquivar", {"confirm": "y"}).status_code == 303
    assert client.get(f"/app/projetos/{a.project_id}").status_code == 404
    assert client.get(f"/app/projetos/{a.project_id}/historico").status_code == 200  # histórico continua
    assert "Cópia de Renomeado" in text_of(client.get("/app/projetos"))


# ---------------------------------------------------------------- desfazer


def test_desfazer_so_supervisor_e_por_lancamento_compensatorio(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 3})
    with app.app_context():
        entry_id = db.session.query(ProgressEntry).filter_by(activity_id=a.activity_id).one().id
    assert client.get(f"/app/registros/{entry_id}/desfazer").status_code == 403
    assert post(client, app, f"/app/registros/{entry_id}/desfazer", {"confirm": "y"}).status_code == 403
    assert f"/app/registros/{entry_id}/desfazer" not in text_of(client.get(f"/app/projetos/{a.project_id}/historico"))
    client = app.test_client()
    login(client, app, a.supervisor_email)
    page = text_of(client.get(f"/app/registros/{entry_id}/desfazer"))
    assert "O total volta para 0 de 10" in page
    assert post(client, app, f"/app/registros/{entry_id}/desfazer", {}).status_code == 303  # sem confirmação
    assert _count(app, ProgressEntry, activity_id=a.activity_id) == 1
    assert post(client, app, f"/app/registros/{entry_id}/desfazer", {"confirm": "y"}).status_code == 303
    with app.app_context():
        assert db.session.get(Activity, a.activity_id).units_done == 0
        deltas = sorted(e.delta for e in db.session.query(ProgressEntry).filter_by(activity_id=a.activity_id))
        assert deltas == [-3, 3]
        reversal_id = db.session.query(ProgressEntry).filter_by(delta=-3).one().id
    history = text_of(client.get(f"/app/projetos/{a.project_id}/historico"))
    assert "desfeito" in history and "Registro desfeito" in history
    assert "já foi desfeito" in text_of(client.get(f"/app/registros/{entry_id}/desfazer"))
    assert "já é um desfazer" in text_of(client.get(f"/app/registros/{reversal_id}/desfazer"))
    assert post(client, app, f"/app/registros/{entry_id}/desfazer", {"confirm": "y"}).status_code == 303
    assert _count(app, ProgressEntry, activity_id=a.activity_id) == 2


def test_desfazer_registro_de_atividade_arquivada_e_404(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 1})
    with app.app_context():
        entry_id = db.session.query(ProgressEntry).filter_by(activity_id=a.activity_id).one().id
    post(client, app, f"/app/atividades/{a.activity_id}/arquivar")
    assert client.get(f"/app/registros/{entry_id}/desfazer").status_code == 404


# ---------------------------------------------------------------- importar e exportar


def _upload(client, app, filename, content, extra=None, url="/app/importar"):
    return post(client, app, url, {"file": (io.BytesIO(content), filename), **(extra or {})},
                content_type="multipart/form-data")


def _hidden(page: str, name: str) -> str:
    import re

    return re.search(rf'name="{name}" type="hidden" value="([^"]+)"|type="hidden" name="{name}" value="([^"]+)"|id="{name}" name="{name}" type="hidden" value="([^"]+)"', page).group(0).rsplit('value="', 1)[1].rstrip('"')


def test_exportar_importar_pelas_telas(client, app, tenants):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    post(client, app, f"/app/atividades/{a.activity_id}/registrar", {"delta": 4})
    response = client.get(f"/app/projetos/{a.project_id}/exportar.csv")
    assert response.status_code == 200 and response.mimetype == "text/csv"
    assert response.headers["Content-Disposition"] == 'attachment; filename="projeto-a.csv"'
    csv_bytes = response.data
    xlsx = client.get(f"/app/projetos/{a.project_id}/exportar.xlsx")
    assert xlsx.status_code == 200 and xlsx.data[:2] == b"PK"
    assert client.get("/app/importar").status_code == 200
    assert client.get("/app/importar/modelo.csv").data.decode("utf-8-sig").startswith("Projeto;")
    preview = _upload(client, app, "projeto.csv", csv_bytes, {"name": ""})
    page = preview.get_data(as_text=True)
    assert preview.status_code == 200 and "Pré-visualização" in page and "Atividade 1" in page
    payload = _hidden(page, "payload")
    before = _count(app, Project, company_id=a.company_id)
    response = post(client, app, "/app/importar/confirmar", {"payload": payload, "name": "Importado"})
    assert response.status_code == 303
    assert _count(app, Project, company_id=a.company_id) == before + 1
    with app.app_context():
        imported = db.session.query(Project).filter_by(name="Importado").one()
        assert [(x.name, x.units_done) for x in imported.stages[0].activities] == [("Atividade 1", 4), ("Atividade 2", 0)]
    # payload adulterado ou vazio
    assert post(client, app, "/app/importar/confirmar", {"payload": payload + "x"}).status_code == 400
    assert post(client, app, "/app/importar/confirmar", {}).status_code == 400


def test_importar_erros_pelas_telas(client, app, tenants, monkeypatch):
    a, _ = tenants
    login(client, app, a.supervisor_email)
    bad = ("Projeto;Quantidade;Etapa;Atividade;Tempo ideal (min)\r\nL;2;E;A;1\r\n" + "\r\n".join(
        ["L;2;E;B;1"] * 4) + "\r\nL;2;E;C;dez\r\n").encode()
    response = _upload(client, app, "x.csv", bad)
    assert response.status_code == 400
    # R7 (tela): erros por linha numa tabela (Linha · Coluna · Problema)
    assert re.search(r"Linha 7</td>[^<]*<td[^>]*>tempo ideal</td>[^<]*<td[^>]*>número inválido", text_of(response)) and "Nada foi gravado" in text_of(response)
    assert _upload(client, app, "x.txt", b"oi").status_code == 400
    assert post(client, app, "/app/importar", {}, content_type="multipart/form-data").status_code == 400
    big = _upload(client, app, "x.csv", b"x" * (3 * 1024 * 1024))
    assert big.status_code == 413 and "grande demais" in text_of(big)
    app.config["IMPORT_MAX_BYTES"] = 10
    assert _upload(client, app, "x.csv", b"x" * (100 * 1024)).status_code == 413
    assert _upload(client, app, "x.csv", b"x" * 20).status_code == 400  # acima de 10 bytes


def test_importar_planilha_de_referencia_pela_tela(client, app, tenants):
    if not XLSX.exists():  # pragma: no cover
        pytest.skip("planilha de referência ausente")
    a, _ = tenants
    login(client, app, a.supervisor_email)
    response = _upload(client, app, "acompanhamento_montagem_v4.xlsx", XLSX.read_bytes(), {"name": "SoBot"})
    page = text_of(response)
    assert response.status_code == 200
    assert "planilha de acompanhamento reconhecido" in page and "24 etapas" in page and "Montagem do Suporte de Manutenção" in page
    assert _count(app, Project, company_id=a.company_id) == 1  # nada gravado antes de confirmar


def test_previa_avisa_limite_e_confirmacao_respeita_402(client, app, tenants):
    a, _ = tenants
    _subscribe(app, a.company_id)
    _add_projects(app, a.company_id, 4)
    login(client, app, a.supervisor_email)
    with app.app_context():
        project = db.session.get(Project, a.project_id)
        data = exporter.to_csv(project)
    preview = _upload(client, app, "p.csv", data)
    page = preview.get_data(as_text=True)
    assert "Limite do plano" in page
    response = post(client, app, "/app/importar/confirmar", {"payload": _hidden(page, "payload")})
    assert response.status_code == 402


def test_atraso_previsto_mostra_dias_uteis(client, app, tenants):
    a, _ = tenants
    with app.app_context():
        project = db.session.get(Project, a.project_id)
        project.due_date = datetime.now(timezone.utc).date() - timedelta(days=10)
        db.session.commit()
    login(client, app, a.operator_email)
    page = text_of(client.get("/app/projetos"))
    assert re.search(r"Atraso previsto · \d+ (dia útil|dias úteis)", page)  # por extenso, sem “d.u.” (redesign 2026-10-28)
    assert "dias úteis" in text_of(client.get(f"/app/projetos/{a.project_id}"))


def test_menu_mostra_modelos_so_para_supervisor(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    assert "/app/modelos" not in client.get("/app/projetos").get_data(as_text=True)
    client = app.test_client()
    login(client, app, a.supervisor_email)
    assert "/app/modelos" in client.get("/app/projetos").get_data(as_text=True)


def test_isolamento_novo_projeto_usa_so_modelo_da_sessao(client, app, tenants):
    """Complementa test_isolation: o select só oferece modelos da empresa ativa."""
    a, b = tenants
    with app.app_context():
        company_b = db.session.get(Company, b.company_id)
        owner_b = db.session.query(User).filter_by(email=b.owner_email).one()
        tsvc.create_template(company_b, "Segredo B", [svc.NewStage("E", [svc.NewActivity("x", Decimal("1"))])], owner_b.id)
        db.session.commit()
    login(client, app, a.supervisor_email)
    assert "Segredo B" not in client.get("/app/projetos/novo").get_data(as_text=True)
