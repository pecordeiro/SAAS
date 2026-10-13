# Progresso

Cada fase preenche um bloco abaixo ao terminar. A próxima só começa quando todos os
critérios de pronto da anterior estiverem marcados.

## Formato do bloco

```
### Fase N — Nome
- Status: não iniciada | em andamento | concluída
- Datas: início AAAA-MM-DD · fim AAAA-MM-DD
- Entregas: lista curta do que foi feito
- Critérios de pronto: [x] / [ ] um por linha, copiados do roadmap
- Testes: resultado de `python -m pytest -q` (n passaram, n falharam, cobertura se aplicável)
- /security-review: sem achados | achados abertos (listar)
- Telas conferidas (375/768/1280, claro/escuro): sim | não | n/a
- Commit: hash e mensagem
- ADRs criados: lista
- Pendências e dívidas: lista
```

## Fases

### Fase 0 — Esqueleto do projeto
- Status: concluída (aguarda /security-review e commit do orquestrador)
- Datas: início 2026-10-13 · fim 2026-10-13
- Entregas:
  - `requirements.txt` / `requirements-dev.txt` fixados; `.gitignore`; `.env.example`; `run.py`.
  - `app/__init__.py` (create_app), `app/config.py` (por ambiente, lido do env na criação do
    app; `SECRET_KEY` e `DATABASE_URL` obrigatórios fora de development/test),
    `app/extensions.py`; blueprints `public` (`/`, `/health`), `auth` (`/cadastro`,
    `/entrar`, `/sair`) e `app` (`/app/...`); cabeçalhos de segurança (CSP `default-src 'self'`).
  - Modelos (UUID, `company_id NOT NULL`, índices começando por `company_id`): companies,
    users, memberships, projects, stages, activities, progress_entries (append-only, guarda
    no ORM), holidays. Migration `e972bfba83c7` revisada; `flask db upgrade`/`downgrade` e
    `flask db check` conferidos em SQLite e PostgreSQL 16.
  - `app/tenancy.py`: `load_company`, `tenant_required(min_role)`, `scoped`, `get_or_404`.
  - `app/services/calc.py` puro (pesos, %, progresso por tarefas com fallback, unidades,
    status, tempos, dias úteis, progresso geral, `prazo_em_data`, resumos em dataclasses).
  - `app/services/projects.py` (criar projeto, incluir etapa/atividade, registrar peças com
    UPDATE condicional por `version` → 409 em conflito; histórico).
  - Cadastro de empresa + login/logout (Argon2id, CSRF em todo POST, Flask-Limiter
    `memory://`, `next` só interno, sessão versionada por `session_version`).
  - Telas provisórias sem CSS: início, login, cadastro, projetos, novo projeto, detalhe
    (indicadores + registrar peças), histórico, erros 400/403/404/429/500.
  - `flask seed-demo` (2 empresas, 1 projeto de 10 equipamentos com 6 etapas genéricas cada).
  - `.github/workflows/ci.yml` (Python 3.12: `flask db upgrade` + `flask db check` + pytest com cobertura).
- Critérios de pronto:
  - [x] `python -m pytest -q` verde localmente (CI configurado; ainda não executado no GitHub).
  - [x] `test_calc.py` com ≥ 15 casos conferidos à mão (26 testes, incluindo quantidade zero,
        soma de tempos zero, atividade 100%, peças acima da meta) **e** teste de paridade com
        `acompanhamento_montagem_v4.xlsx` (24 etapas + resumo + aba Equipe, tolerância 1e-9).
  - [x] `calc.py` não importa `flask` nem `sqlalchemy` (teste por AST).
  - [x] Usuário da empresa A recebe 404 em GET/POST de projeto, etapa e atividade da empresa B.
  - [x] Operador recebe 403 ao criar projeto; POST sem CSRF recebe 400.
  - [x] `flask db upgrade` em banco vazio cria tudo; `/health` responde 200 (servidor real).
- Testes: `65 passed` (SQLite em memória, ~21 s); mesmos 64 da suíte principal também
  verdes com `TEST_DATABASE_URL` em PostgreSQL 16 local. Cobertura 90% de `app/`.
- /security-review: não executado nesta sessão (pendente para o orquestrador).
- Telas conferidas (375/768/1280, claro/escuro): n/a (telas provisórias sem design; migram na Fase 2).
- Commit: (preenchido pelo orquestrador)
- ADRs criados: nenhum (ADR-0007 já cobria a fase).
- Pendências e dívidas:
  - Feriados: `holidays.company_id` é NOT NULL (só feriados da empresa); feriados nacionais
    compartilhados ficam para a Fase 3 (decidir entre linha global ou seed por empresa).
  - `users.email` é `String` em minúsculas; `citext` no PostgreSQL fica para a Fase 3.
  - Rate limit em memória e sem bloqueio progressivo por conta (Fase 5/7, Redis).
  - CSP sem nonce (não há script ainda); RLS não ligado (`RLS_ENABLED`, Fase 3).
  - Cadastro informa “não foi possível cadastrar com este e-mail” em e-mail repetido:
    não revela dados da outra conta, mas permite enumerar e-mails; resolver com confirmação
    por e-mail na Fase 5.
  - Novo projeto usa 6 blocos fixos de etapa com atividades em texto (“Nome; minutos”);
    a tela definitiva (HTMX) vem na Fase 2/6.
  - Desfazer registro de peças (D13, supervisor+) não existe ainda (Fase 4).
