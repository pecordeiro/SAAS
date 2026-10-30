"""Etapa H — /saude (liveness do host) e /health (prontidão com banco)."""

from __future__ import annotations

from sqlalchemy import event

from app.extensions import db


def _contar_consultas(app, fn):
    consultas: list[str] = []

    def antes(conn, cursor, statement, parameters, context, executemany):  # noqa: ARG001
        consultas.append(statement)

    with app.app_context():
        engine = db.engine
        event.listen(engine, "before_cursor_execute", antes)
        try:
            resposta = fn()
        finally:
            event.remove(engine, "before_cursor_execute", antes)
    return resposta, consultas


def test_saude_responde_ok_sem_dado_interno(client):
    response = client.get("/saude")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    assert response.headers["Cache-Control"] == "no-store"


def test_saude_nao_toca_no_banco(app, client):
    response, consultas = _contar_consultas(app, lambda: client.get("/saude"))
    assert response.status_code == 200
    assert consultas == []


def test_saude_segue_de_pe_com_banco_fora_do_ar(client, monkeypatch):
    def quebrado(*args, **kwargs):
        raise RuntimeError("banco fora do ar")

    monkeypatch.setattr(db.session, "execute", quebrado)
    assert client.get("/saude").status_code == 200
    # A prontidão, ao contrário, acusa o problema sem vazar o motivo.
    pronta = client.get("/health")
    assert pronta.status_code == 503
    assert "banco fora do ar" not in pronta.get_data(as_text=True)


def test_saude_nao_tem_rate_limit_e_aceita_so_get(client):
    for _ in range(30):
        assert client.get("/saude").status_code == 200
    assert client.post("/saude").status_code in {400, 405}


def test_saude_traz_cabecalhos_de_seguranca_e_request_id(client):
    response = client.get("/saude", headers={"X-Request-ID": "monitor-uptime-01"})
    assert response.headers["X-Request-ID"] == "monitor-uptime-01"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "Content-Security-Policy" in response.headers


def test_saude_nao_exige_login_nem_empresa(client):
    response = client.get("/saude", follow_redirects=False)
    assert response.status_code == 200
