"""Botão claro/escuro no cabeçalho do site público (2026-10-29).

O site público abre claro (só vira escuro quando a pessoa escolhe); o botão alterna e grava o mesmo cookie
“tema” do sistema. Sem JS, o formulário usa a rota /tema e volta para a mesma página."""

from __future__ import annotations

import re

from tests.conftest import csrf_token

PAGES = ("/", "/precos", "/como-funciona", "/termos", "/privacidade", "/contato", "/entrar")


def _toggle(html: str):
    form = re.search(r'<form class="theme-toggle".*?</form>', html, re.S)
    assert form, "botão de tema ausente"
    return form.group(0)


def test_botao_de_tema_aparece_nas_paginas_publicas(client):
    for url in PAGES:
        response = client.get(url)
        if response.status_code != 200:
            continue
        html = response.get_data(as_text=True)
        form = _toggle(html)
        assert 'action="/tema"' in form and 'data-theme-toggle' in form, url
        assert 'name="tema" value="dark"' in form  # abre claro: o próximo passo é o escuro
        assert 'aria-pressed="false"' in form


def test_botao_oferece_o_tema_oposto_ao_atual(client):
    client.set_cookie("tema", "dark")
    form = _toggle(client.get("/").get_data(as_text=True))
    assert 'name="tema" value="light"' in form and 'aria-pressed="true"' in form
    client.set_cookie("tema", "light")
    form = _toggle(client.get("/precos").get_data(as_text=True))
    assert 'name="tema" value="dark"' in form and 'aria-pressed="false"' in form


def test_sem_js_a_rota_grava_o_cookie_e_volta_para_a_pagina(client, app):
    response = client.post("/tema", data={"tema": "dark", "next": "/precos", "csrf_token": csrf_token(client, app)})
    assert response.status_code == 303 and response.headers["Location"] == "/precos"
    assert "tema=dark" in response.headers.get("Set-Cookie", "")
    html = client.get("/precos").get_data(as_text=True)
    assert 'data-theme="dark"' in html.split("<body", 1)[0]  # já sai escuro do servidor, sem piscar


def test_tema_invalido_e_recusado_e_next_externo_ignorado(client, app):
    token = csrf_token(client, app)
    assert client.post("/tema", data={"tema": "roxo", "csrf_token": token}).status_code == 400
    response = client.post("/tema", data={"tema": "light", "next": "https://exemplo.invalid/", "csrf_token": token})
    assert response.status_code == 303 and response.headers["Location"] == "/"
