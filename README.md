# Controle de Produção (SaaS)

SaaS web multiempresa para acompanhar a produção de indústrias de montagem por etapas e
atividades: progresso, unidades concluídas, horas restantes, prazo em dias úteis, histórico
e exportação. Site renderizado no servidor (Flask + Jinja + HTMX), em português do Brasil.

## Estado

Fase 0 (esqueleto) entregue: app factory, modelos e primeira migration, isolamento por
empresa (`app/tenancy.py`), regras de cálculo puras (`app/services/calc.py`) conferidas
contra a planilha de referência, cadastro/login e testes.
Fase 2 (base visual) entregue: design system “Prumo” no código (tokens, CSS em camadas,
fontes e HTMX locais, macros, layouts público e logado, tema claro/escuro, registro de peças
em 2 toques no celular). Progresso por fase em [`docs/plano/progresso.md`](docs/plano/progresso.md).

- Contexto para o Claude: [`CLAUDE.md`](CLAUDE.md)
- Plano: [`docs/plano/`](docs/plano/) — PRD, arquitetura, ADRs, roadmap, backlog, riscos e progresso
- Guia de segurança: [`.claude/claude-security-guidance.md`](.claude/claude-security-guidance.md)

## Como rodar

Requisitos: Python 3.12+ (o CI usa 3.12). PostgreSQL 16 é opcional nesta fase; sem
`DATABASE_URL`, o ambiente de desenvolvimento usa SQLite em `instance/dev.db`.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # APP_ENV=development já vem preenchido

flask db upgrade              # cria o schema pelas migrations (nunca db.create_all)
flask seed-demo               # 2 empresas fictícias, 1 projeto de 10 equipamentos cada
python run.py                 # http://127.0.0.1:5000  (/health responde {"status": "ok"})
```

O `seed-demo` cria `owner.a@demo.invalid`, `supervisor.a@demo.invalid`,
`operator.a@demo.invalid` (e os mesmos com `.b`). A senha é a de `DEMO_PASSWORD` no `.env`
ou, se vazia, uma senha gerada e exibida no terminal. Só roda em development/test.

### Testes

```bash
python -m pytest -q                                      # SQLite em memória
TEST_DATABASE_URL=postgresql+psycopg://usuario@localhost/controle_test python -m pytest -q
```

- `tests/test_calc.py`: casos conferidos à mão, pureza do `calc.py` e paridade com
  `docs/referencia/acompanhamento_montagem_v4.xlsx` (valores calculados pelo Excel).
- `tests/test_isolation.py`: recurso da empresa B acessado por usuário da A → 404; falha se
  surgir rota com `<uuid:...>` sem caso A/B.
- `tests/test_auth.py`: cadastro, login, papéis (403), CSRF (400), rate limit.

### Interface (Fase 2)

- Tokens: `app/static/css/tokens.css` é cópia de `docs/design/tokens.css` (o handoff do
  design, ADR-0008). Mudou a marca? Troque os valores lá e copie; nomes não mudam.
- CSS: `app/static/css/{base,layout,components,pages,utilities}.css` em `@layer`. Só
  `var(--…)`: cor hex, `rgb(`/`hsl(` ou `px` fora de `tokens.css` quebram
  `tests/test_visual.py`.
- Componentes: macros em `app/templates/components/` (`{% from "components/button.html"
  import button %}` etc.). Páginas estendem `base_publica.html` ou `base_app.html`.
- Vitrine: `http://127.0.0.1:5000/estilo` (só com `APP_ENV=development`; 404 nos demais).
- Sem CDN e sem script/estilo inline (CSP `default-src 'self'`): fontes woff2 (OFL) em
  `app/static/fonts`, HTMX 2.0.4 em `app/static/js/htmx.min.js` (`allowEval:false`),
  melhorias em `app/static/js/app.js`. Tudo funciona sem JS.
- Tema: Sistema/Claro/Escuro no menu (cookie `tema`).
- Capturas de referência: `docs/design/capturas/fase2/` (375/768/1280, claro e escuro).

### Migrations

```bash
flask db migrate -m "descrição"   # gera; revise o arquivo em migrations/versions/ antes do commit
flask db upgrade
```

### Produção

`APP_ENV=production` exige `SECRET_KEY` e `DATABASE_URL` (o app não sobe sem eles).
Servidor: `gunicorn run:app`. Variáveis em [`.env.example`](.env.example) e em
`docs/plano/arquitetura.md` §10.

## Base de referência

- [`docs/referencia/acompanhamento_montagem_v4.xlsx`](docs/referencia/acompanhamento_montagem_v4.xlsx): planilha cujas regras de cálculo o SaaS reproduz.
- Painel antigo (Flask + Excel/COM, só Windows): `pecordeiro/controle-de-atividades`. Só as regras são reaproveitadas.
