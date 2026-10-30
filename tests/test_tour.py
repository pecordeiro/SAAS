"""ADR-0021: tour de primeiro acesso e Como funciona por tópicos."""

from __future__ import annotations

from datetime import date

from app.extensions import db
from app.models import User
from app.services import calc
from tests.conftest import login, post


def _seen(app, email):
    with app.app_context():
        return db.session.query(User).filter_by(email=email).one().tour_seen_at


# ---------------------------------------------------------------- tour


def test_tour_abre_no_primeiro_acesso_e_marca_visto(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    html = client.get("/app/").get_data(as_text=True)
    assert "data-tour-root" in html and "Um giro rápido pela Teroz" in html
    assert 'data-tour="fill"' in html and 'data-tour="settings"' in html
    assert _seen(app, a.owner_email) is None
    assert post(client, app, "/app/tutorial/visto").status_code == 204
    assert _seen(app, a.owner_email) is not None
    assert "data-tour-root" not in client.get("/app/").get_data(as_text=True)
    # “Rever o tour” abre de novo sem apagar a marca.
    assert "data-tour-root" in client.get("/app/?tutorial=1").get_data(as_text=True)
    first = _seen(app, a.owner_email)
    assert post(client, app, "/app/tutorial/visto").status_code == 204
    assert _seen(app, a.owner_email) == first


def test_tour_passos_por_papel(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    html = client.get("/app/").get_data(as_text=True)
    steps = html.split('class="tour__steps"', 1)[1].split("</ol>", 1)[0]
    assert "Preencher etapas" in steps and "Como funciona" in steps
    assert "<strong>Configurações</strong>" not in steps
    assert "quem muda esses números é o supervisor" in steps


def test_tour_so_abre_no_painel(client, app, tenants):
    a, _ = tenants
    login(client, app, a.owner_email)
    assert "data-tour-root" not in client.get(f"/app/como-funciona?projeto={a.project_id}").get_data(as_text=True)


def test_tour_visto_exige_login_e_csrf(client, app, tenants):
    a, _ = tenants
    assert client.post("/app/tutorial/visto").status_code in (302, 303, 400, 401)
    login(client, app, a.owner_email)
    assert client.post("/app/tutorial/visto").status_code == 400  # sem CSRF
    assert _seen(app, a.owner_email) is None


def test_tour_visto_marca_so_a_propria_conta(client, app, tenants):
    a, b = tenants
    login(client, app, a.owner_email)
    post(client, app, "/app/tutorial/visto")
    assert _seen(app, a.owner_email) is not None
    assert _seen(app, a.operator_email) is None
    assert _seen(app, b.owner_email) is None


# ---------------------------------------------------------------- Como funciona por tópicos


def _topicos(**kw):
    etapas = [
        calc.Etapa((calc.Atividade(10, 4), calc.Atividade(30, 2)), 10),
        calc.Etapa((calc.Atividade(20, 0),), 10),
    ]
    return calc.topicos_como_funciona(
        etapas, ["Preparação", "Montagem"], [["Cortar", "Soldar"], ["Montar"]], 10, 2, 8, **kw
    )


def test_topicos_mostram_a_conta_passo_a_passo():
    t = {x.chave: x for x in _topicos()}
    assert list(t) == ["progresso", "unidades", "peso", "horas", "dias", "termino", "situacao", "equipe"]
    # tempo total = (10 + 30 + 20) × 10 = 600 min = 10 h; falta 10×6 + 30×8 + 20×10 = 500 min
    progresso = [linha for p in t["progresso"].passos for linha in p.conta]
    assert "10,0 h" in progresso and "1 − 8,3 h ÷ 10,0 h = 16,7%" in progresso
    unidades = [linha for p in t["unidades"].passos for linha in p.conta]
    assert "Cortar: 4" in unidades and "Preparação: 2 unidades prontas" in unidades
    assert "menor valor = 0 de 10" in unidades
    assert "Cortar: 10 min ÷ 40 min = 25%" in t["peso"].passos[0].conta
    dias = [linha for p in t["dias"].passos for linha in p.conta]
    assert "8,3 h ÷ 16 h = 0,5 dias de trabalho" in dias
    assert t["situacao"].regras[0].startswith("Concluída") and not any("Aguardando" in r for r in t["situacao"].regras)


def test_topico_termino_com_folga_e_atraso():
    sexta = date(2026, 10, 30)
    termino = calc.prazo_em_data(sexta, 0.52)  # 1 dia útil → a própria sexta
    folga = {x.chave: x for x in _topicos(inicio_contagem=sexta, termino=termino, prazo=date(2026, 11, 4))}
    assert folga["termino"].conclusao == "No ritmo de hoje, termina com folga de 3 dias úteis."
    atraso = {x.chave: x for x in _topicos(inicio_contagem=sexta, termino=date(2026, 11, 3), prazo=sexta)}
    assert atraso["termino"].conclusao == "No ritmo de hoje, termina 2 dias úteis depois do prazo."


def test_topicos_sem_dados_explicam_so_a_regra():
    t = {x.chave: x for x in calc.topicos_como_funciona([], [], [], 10, 1, 8)}
    assert all(not x.passos for k, x in t.items() if k != "situacao")
    assert t["progresso"].resposta and t["situacao"].regras


def test_como_funciona_escolhe_o_topico(client, app, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    html = client.get(f"/app/como-funciona?projeto={a.project_id}&topico=termino").get_data(as_text=True)
    assert "Quando o projeto termina? Vai dar no prazo?</h2>" in html
    assert "Rever o tour pelas telas" in html and "tutorial=1" in html
    # tópico desconhecido cai no primeiro, sem erro
    html = client.get(f"/app/como-funciona?projeto={a.project_id}&topico=nada").get_data(as_text=True)
    assert "O que é o progresso pelas tarefas?</h2>" in html
