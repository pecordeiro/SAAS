# Controle de Produção (SaaS)

SaaS web multiempresa para acompanhar a produção de indústrias de montagem por etapas e
atividades: progresso, unidades concluídas, horas restantes, prazo em dias úteis, histórico
e exportação. Site renderizado no servidor (Flask + Jinja + HTMX), em português do Brasil.

## Estado

Fase 0 (esqueleto) entregue: app factory, modelos e primeira migration, isolamento por
empresa (`app/tenancy.py`), regras de cálculo puras (`app/services/calc.py`) conferidas
contra a planilha de referência, cadastro/login e testes.
Fase 2 (base visual) entregue: design system “Prumo” no código (tokens, CSS em camadas,
fontes e HTMX locais, macros, layouts, tema claro/escuro, registro de peças em 2 toques).
Fase 3 (banco) entregue: schema completo do MVP em PostgreSQL 16 (modelos de etapas
versionados, convites, tokens de conta, MFA, planos, assinaturas, cobranças, webhooks,
auditoria, outbox, API), CHECK/UNIQUE, feriados nacionais, políticas RLS ligáveis e testes
em PostgreSQL.
Fase 4 (regras de negócio) entregue: modelos de etapas versionados (`/app/modelos`, novo
projeto a partir de modelo, comparar/aplicar versão com confirmação), edição de projeto
(renomear, ↑/↓, arquivar sem perder histórico, duplicar), desfazer registro (supervisor+,
lançamento compensatório), importação CSV/XLSX e da planilha de referência com
pré-visualização (`/app/importar`), exportação CSV/XLSX neutralizada, limites de plano e
modo leitura (HTTP 402, `app/services/entitlements.py`), eventos de domínio
(`services/events.py`) e auditoria (`services/audit.py::record`).
Progresso por fase em [`docs/plano/progresso.md`](docs/plano/progresso.md).

Variáveis da Fase 4 (opcionais): `READ_ONLY_ENFORCED` (padrão 1: sem assinatura ativa a
empresa fica em modo leitura), `TRIAL_DAYS` (14, teste implícito de empresa sem assinatura),
`DEFAULT_TRIAL_PLAN` (`profissional`), `PAST_DUE_GRACE_DAYS` (7).

Fase 5 (contas) entregue: confirmação de e-mail, esqueci a senha, convites, gestão de
membros, perfil, “sair de todos os dispositivos”, MFA TOTP, bloqueio progressivo de login e
troca de empresa (ver “Contas (Fase 5)” abaixo).

Fase 9 (API de publicação, reservada) desenhada e mínima, **desligada por padrão**: contrato
OpenAPI 3.1 em [`docs/api/openapi.yaml`](docs/api/openapi.yaml), desenho de webhooks em
[`docs/api/webhooks.md`](docs/api/webhooks.md). Com `FEATURE_PUBLIC_API=1` o app registra
`/api/v1` (token Bearer `cp_...` por empresa, escopos `read:projects` e `write:progress`, erros
RFC 9457, auditoria de cada chamada) e a tela `/app/integracoes/api` (só proprietário; plano
Empresa) para criar/revogar tokens. Implementados: `GET /projects` e
`GET /projects/{id}/summary`; as demais rotas respondem 501. Sem a flag, `/api/v1/*` é 404 e o
menu não mostra a tela. Variáveis: `FEATURE_PUBLIC_API`, `API_RATE_LIMIT` (`120 per minute`
por token) e `API_RATE_LIMIT_IP` (`600 per minute`). Com RLS ligado, a busca do token antes de
saber a empresa precisa de papel de plataforma (ver progresso.md, Fase 9).

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

### Contas (Fase 5)

- E-mail: `app/services/email.py` (`EmailSender`: console em development/test — guarda em
  memória e grava `.eml` em `instance/emails/` no development — ou Resend com
  `RESEND_API_KEY`/`MAIL_FROM`). Links usam `APP_BASE_URL` (obrigatório fora de dev/test).
  Textos em `app/templates/emails/*.txt|.html`.
- Tokens (confirmação 24 h, reset 1 h, convite 7 dias): 32 bytes aleatórios só no link; no
  banco só o SHA-256; uso único (`app/services/tokens.py`). Páginas de token mandam
  `Referrer-Policy: no-referrer` e só alteram algo via POST com CSRF.
- Cadastro sem enumeração: e-mail novo ou já cadastrado vê a mesma tela “Confirme seu
  e-mail”; o dono da conta existente recebe um aviso. Sem confirmar, o acesso dura 7 dias.
- Sessões: `/sair` encerra só a sessão atual; “Sair de todos os dispositivos” (perfil),
  troca/redefinição de senha e desativação do último vínculo incrementam `session_version`.
- MFA TOTP (`/conta/mfa`): segredo cifrado (Fernet, chave por HKDF de `MFA_ENCRYPTION_KEY`
  ou `SECRET_KEY`), QR em SVG gerado no servidor, 10 códigos de recuperação de uso único.
  Owner de empresa com “Exigir MFA” (plano Empresa) é levado a ativar.
- Bloqueio progressivo (`app/services/lockout.py`, tabela `login_throttles`): 5 falhas na
  conta ou 20 no IP → espera 1, 5, 15, 60 min (`LOCKOUT_*` na config), além do Flask-Limiter.
  Com o IP bloqueado só entra quem já entrou naquele navegador (cookie de dispositivo
  confiável). Atrás de proxy, defina `TRUSTED_PROXY_COUNT` (Render: 1) para o IP real valer.
- Usuários e convites: `/app/usuarios` (supervisor convida supervisor/operador; owner muda
  papel, desativa/reativa; último owner protegido; convites pendentes contam no limite do plano).
- Testes: `tests/test_accounts.py` e os casos A/B no fim de `tests/test_isolation.py`.

### Produção

`APP_ENV=production` exige `SECRET_KEY` e `DATABASE_URL` (o app não sobe sem eles); para
mandar e-mail, também `APP_BASE_URL`, `RESEND_API_KEY` e `MAIL_FROM`.
Servidor: `gunicorn run:app`. Variáveis em [`.env.example`](.env.example) e em
`docs/plano/arquitetura.md` §10.

## Base de referência

- [`docs/referencia/acompanhamento_montagem_v4.xlsx`](docs/referencia/acompanhamento_montagem_v4.xlsx): planilha cujas regras de cálculo o SaaS reproduz.
- Painel antigo (Flask + Excel/COM, só Windows): `pecordeiro/controle-de-atividades`. Só as regras são reaproveitadas.
