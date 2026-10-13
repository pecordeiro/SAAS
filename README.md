# Controle de Produção (SaaS)

SaaS web multiempresa para acompanhar a produção de indústrias de montagem por etapas e
atividades: progresso, unidades concluídas, horas restantes, prazo em dias úteis, histórico
e exportação. Site renderizado no servidor (Flask + Jinja + HTMX), em português do Brasil.

## Estado

Fase 0 (esqueleto) entregue: app factory, modelos e primeira migration, isolamento por
empresa (`app/tenancy.py`), regras de cálculo puras (`app/services/calc.py`) conferidas
contra a planilha de referência, cadastro/login, telas provisórias sem design e testes.
Fase 3 (banco) entregue: schema completo do MVP em PostgreSQL 16 (modelos de etapas
versionados, convites, tokens de conta, MFA, planos, assinaturas, cobranças, webhooks,
auditoria, outbox, API), CHECK/UNIQUE, feriados nacionais, políticas RLS ligáveis e testes
em PostgreSQL. Progresso por fase em [`docs/plano/progresso.md`](docs/plano/progresso.md).

- Contexto para o Claude: [`CLAUDE.md`](CLAUDE.md)
- Plano: [`docs/plano/`](docs/plano/) — PRD, arquitetura, ADRs, roadmap, backlog, riscos e progresso
- Guia de segurança: [`.claude/claude-security-guidance.md`](.claude/claude-security-guidance.md)

## Como rodar

Requisitos: Python 3.12+ (o CI usa 3.12) e PostgreSQL 16 (via Docker, recomendado). Sem
`DATABASE_URL`, o ambiente de desenvolvimento cai no SQLite em `instance/dev.db` (atalho).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # APP_ENV=development já vem preenchido
docker compose up -d          # PostgreSQL 16 (bancos controle e controle_test) + Redis 7
# no .env: DATABASE_URL=postgresql+psycopg://controle:controle@localhost:5432/controle

flask db upgrade              # cria o schema pelas migrations (nunca db.create_all); já grava os planos
flask seed-holidays           # feriados nacionais do ano atual + 4 (idempotente)
flask seed-demo               # 2 empresas fictícias com modelo de etapas, 2 projetos e trial
python run.py                 # http://127.0.0.1:5000  (/health responde {"status": "ok"})
```

Outros comandos: `flask seed-plans` (sincroniza Essencial/Profissional/Empresa, idempotente),
`flask seed-holidays --de 2026 --ate 2030`, `flask rls status|enable|disable` (ver abaixo).

O `seed-demo` cria `owner.a@demo.invalid`, `supervisor.a@demo.invalid`,
`operator.a@demo.invalid` (e os mesmos com `.b`). A senha é a de `DEMO_PASSWORD` no `.env`
ou, se vazia, uma senha gerada e exibida no terminal. Só roda em development/test.

### Testes

```bash
TEST_DATABASE_URL=postgresql+psycopg://controle:controle@localhost:5432/controle_test python -m pytest -q
python -m pytest -q                                      # atalho: SQLite em memória
```

No PostgreSQL o schema dos testes vem das **migrations** (o `schema public` do banco de
teste é recriado no início — por isso o nome do banco precisa conter `test`) e cada teste
começa com as tabelas vazias (os planos da migration ficam). Os testes de RLS e de
migrations no PostgreSQL só rodam com `TEST_DATABASE_URL`; no SQLite aparecem como skipped.

- `tests/test_calc.py`: casos conferidos à mão, pureza do `calc.py` e paridade com
  `docs/referencia/acompanhamento_montagem_v4.xlsx` (valores calculados pelo Excel).
- `tests/test_isolation.py`: recurso da empresa B acessado por usuário da A → 404; falha se
  surgir rota com `<uuid:...>` sem caso A/B.
- `tests/test_auth.py`: cadastro, login, papéis (403), CSRF (400), rate limit.
- `tests/test_schema.py`: toda tabela de cliente com `company_id NOT NULL` e índice
  começando por `company_id` (exceções justificadas), CHECK/UNIQUE, planos, feriados,
  snapshot de modelo.
- `tests/test_rls.py`: RLS ligado com um papel comum (não superusuário) criado no teste.
- `tests/test_migrations.py`: upgrade → downgrade base → upgrade sem drift (SQLite e PG).

### Migrations

```bash
flask db migrate -m "descrição"   # gera; revise o arquivo em migrations/versions/ antes do commit
flask db upgrade
flask db check                    # sem drift entre modelos e migrations
flask db downgrade base           # toda migration precisa voltar (o CI faz ida e volta)
```

Tabela nova com dado de cliente: `company_id NOT NULL` (use `TenantMixin`), índice
começando por `company_id`, entrada em `app/rls.py::RLS_TABLES` e política na migration —
`tests/test_schema.py` falha se faltar algum.

### RLS (segunda barreira, ADR-0003)

Pronto e **desligado por padrão**. Para ligar num ambiente: `RLS_ENABLED=1` no app (deploy),
`flask seed-holidays`, depois `RLS_ENABLED=1 flask rls enable` com o papel dono das tabelas
e `flask rls status` para conferir. O app precisa conectar com papel **sem** `SUPERUSER` e
sem `BYPASSRLS` (para esses o RLS não vale); no docker-compose o usuário é superusuário, então
lá o RLS não tem efeito — os testes criam um papel comum para provar o isolamento.

### Produção

`APP_ENV=production` exige `SECRET_KEY` e `DATABASE_URL` (o app não sobe sem eles).
Servidor: `gunicorn run:app`. Variáveis em [`.env.example`](.env.example) e em
`docs/plano/arquitetura.md` §10.

## Base de referência

- [`docs/referencia/acompanhamento_montagem_v4.xlsx`](docs/referencia/acompanhamento_montagem_v4.xlsx): planilha cujas regras de cálculo o SaaS reproduz.
- Painel antigo (Flask + Excel/COM, só Windows): `pecordeiro/controle-de-atividades`. Só as regras são reaproveitadas.
