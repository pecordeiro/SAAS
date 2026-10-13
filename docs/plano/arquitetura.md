# Arquitetura

Status: rascunho para aprovação · Atualizado: 2026-10-13

## 1. Ponto de partida e o que muda

O repositório começou vazio (só `README.md`). Não há código a preservar. Os módulos que o
roteiro trata como existentes nascem na **Fase 0** com estes contratos:

| Módulo | Contrato | Por quê |
|---|---|---|
| `app/services/calc.py` | Funções puras: `progresso(atividades)`, `unidades_concluidas`, `horas_restantes`, `dias_uteis_entre(inicio, fim, feriados, dias_semana)`, `prazo_previsto(horas, capacidade_diaria, ...)`. Sem Flask, sem banco, só tipos simples/dataclasses. | Regra de negócio testável à mão e reaproveitável na API |
| `app/tenancy.py` | `load_company()` (before_request: lê `company_id` da sessão, valida vínculo ativo, põe em `g.company`/`g.membership`), `tenant_required(min_role)`, `scoped(Model)` (query já filtrada por `company_id`), `get_or_404(Model, id)` escopado. | Isolamento num único lugar |
| `tests/test_isolation.py` | Fixture com empresas A e B; cada rota com `<uuid>` testada com recurso de B logado em A → 404. | Regra inviolável 1 |

## 2. Componentes

```mermaid
flowchart LR
  U[Navegador<br/>HTML + HTMX] -->|HTTPS| W[Web: Gunicorn + Flask]
  W --> PG[(PostgreSQL 16<br/>RLS por company_id)]
  W --> R[(Redis<br/>rate limit / cache)]
  W -->|e-mail| E[Resend]
  W -->|API REST| A[Asaas]
  A -->|webhook| W
  K[Worker<br/>outbox, reconciliação, e-mails] --> PG
  K --> A
  K -.fase 9.-> X[Sistemas externos<br/>ERP, BI, TV]
  W --> S[Sentry]
```

- **Web**: Flask 3 com app factory e blueprints: `public` (site), `auth`, `app` (área
  logada, prefixo `/app`), `billing`, `webhooks`, `api_v1` (só com flag), `dev` (só em
  development: `/estilo`).
- **Worker**: processo separado (`flask worker`) que roda jobs periódicos: e-mails pendentes,
  reconciliação do Asaas, limpeza de tokens, apagamento LGPD e, na fase 9, entrega do outbox.
  Sem Celery no MVP: loop simples com `SELECT ... FOR UPDATE SKIP LOCKED`.
- **Templates**: Jinja com macros em `app/templates/components/`, tokens em
  `app/static/css/tokens.css`, HTMX e fontes servidos pelo próprio site.

### Estrutura de pastas alvo

```
app/
  __init__.py          # create_app
  config.py            # Config por ambiente, tudo de env
  extensions.py        # db, migrate, login, csrf, limiter
  tenancy.py
  models/              # um arquivo por agregado
  services/            # calc.py, projects.py, templates.py, entitlements.py,
                       # importer.py, exporter.py, events.py, audit.py, billing/
  blueprints/          # public, auth, app, billing, webhooks, api_v1, dev
  templates/           # base_publica.html, base_app.html, components/, páginas
  static/              # css/, js/htmx.min.js, fonts/, img/
migrations/
tests/
docs/plano/, docs/api/
```

## 3. Fluxo de uma requisição (área logada)

1. Gunicorn recebe; middleware gera `request_id` e o põe no log.
2. Flask-Login carrega o usuário pelo `session_token` versionado (revogação imediata).
3. `tenancy.load_company()` lê `company_id` da sessão, confere vínculo ativo e papel;
   abre a transação com `SET LOCAL app.company_id = :id` (RLS).
4. `tenant_required(min_role)` barra papel insuficiente (403) e, para escrita,
   `entitlements` barra modo leitura/limite de plano (402).
5. A view chama um serviço; o serviço usa `scoped()` e grava `domain_events`/`audit_logs`
   na mesma transação.
6. Resposta: página inteira ou fragmento HTMX (`HX-Request`); CSP com nonce.

## 4. Modelo de dados alvo

Todas as chaves primárias são UUID. Tabelas com dado de cliente têm `company_id NOT NULL`
e índices compostos começando por `company_id`.

```mermaid
erDiagram
  companies ||--o{ memberships : tem
  users ||--o{ memberships : tem
  companies ||--o{ invitations : emite
  users ||--o{ password_resets : pede
  users ||--o{ email_confirmations : confirma
  users ||--o{ mfa_recovery_codes : guarda

  companies ||--o{ templates : possui
  templates ||--o{ template_versions : versiona
  template_versions ||--o{ template_stages : contem
  template_stages ||--o{ template_activities : contem

  companies ||--o{ projects : possui
  template_versions |o--o{ projects : origem
  projects ||--o{ stages : contem
  stages ||--o{ activities : contem
  activities ||--o{ progress_entries : registra
  projects ||--o{ project_members : equipe
  companies ||--o{ holidays : define

  plans ||--o{ subscriptions : define
  companies ||--o| subscriptions : assina
  subscriptions ||--o{ payments : cobra
  webhook_events }o--|| companies : "refere (opcional)"

  companies ||--o{ audit_logs : registra
  companies ||--o{ domain_events : publica
  companies ||--o{ api_clients : possui
  api_clients ||--o{ api_tokens : emite

  companies {
    uuid id PK
    string name
    string cnpj
    string timezone
    numeric daily_hours
    int workdays_mask
    bool mfa_required
    timestamptz deletion_requested_at
  }
  users {
    uuid id PK
    citext email UK
    string password_hash
    timestamptz email_confirmed_at
    int session_version
    string totp_secret_enc
    bool active
  }
  memberships {
    uuid id PK
    uuid company_id FK
    uuid user_id FK
    string role "owner|supervisor|operator"
    bool active
  }
  invitations {
    uuid id PK
    uuid company_id FK
    citext email
    string role
    string token_hash UK
    timestamptz expires_at
    timestamptz used_at
  }
  password_resets {
    uuid id PK
    uuid user_id FK
    string token_hash UK
    timestamptz expires_at
    timestamptz used_at
  }
  templates {
    uuid id PK
    uuid company_id FK
    string name
    uuid current_version_id
    timestamptz archived_at
  }
  template_versions {
    uuid id PK
    uuid company_id FK
    uuid template_id FK
    int number
  }
  template_stages {
    uuid id PK
    uuid company_id FK
    uuid template_version_id FK
    string name
    int position
  }
  template_activities {
    uuid id PK
    uuid company_id FK
    uuid template_stage_id FK
    string name
    numeric hours_per_unit
    int position
  }
  projects {
    uuid id PK
    uuid company_id FK
    uuid template_version_id FK
    string name
    int quantity
    date start_date
    date due_date
    string status
    timestamptz archived_at
  }
  stages {
    uuid id PK
    uuid company_id FK
    uuid project_id FK
    string name
    int position
    timestamptz archived_at
  }
  activities {
    uuid id PK
    uuid company_id FK
    uuid stage_id FK
    string name
    numeric hours_per_unit
    int units_done
    int version
    timestamptz archived_at
  }
  progress_entries {
    uuid id PK
    uuid company_id FK
    uuid activity_id FK
    uuid user_id FK
    int delta
    timestamptz at
  }
  plans {
    uuid id PK
    string code UK
    string name
    int price_cents
    int max_projects
    int max_users
    jsonb features
  }
  subscriptions {
    uuid id PK
    uuid company_id FK
    uuid plan_id FK
    string provider
    string provider_customer_id
    string provider_subscription_id
    string status
    timestamptz current_period_end
    timestamptz grace_until
    timestamptz canceled_at
  }
  payments {
    uuid id PK
    uuid subscription_id FK
    string provider_payment_id UK
    string status
    int value_cents
    date due_date
    timestamptz paid_at
  }
  webhook_events {
    uuid id PK
    string provider
    string external_event_id UK
    string type
    timestamptz received_at
    timestamptz processed_at
    string status
    text error
  }
  audit_logs {
    uuid id PK
    uuid company_id FK
    uuid actor_user_id FK
    string action
    string object_type
    uuid object_id
    inet ip
    timestamptz at
  }
  domain_events {
    uuid id PK
    uuid company_id FK
    string type
    jsonb payload
    timestamptz created_at
    timestamptz published_at
  }
  api_clients {
    uuid id PK
    uuid company_id FK
    string name
  }
  api_tokens {
    uuid id PK
    uuid company_id FK
    uuid api_client_id FK
    string token_hash UK
    string[] scopes
    timestamptz expires_at
    timestamptz last_used_at
    timestamptz revoked_at
  }
```

Observações:
- **Snapshot de modelo**: criar projeto copia `template_stages/activities` para
  `stages/activities` e guarda `template_version_id`. Editar o modelo cria nova versão; o
  projeto só muda com confirmação explícita (registrada no histórico).
- **Concorrência**: `activities.version` para controle otimista (409 no conflito).
- **Histórico**: `progress_entries` é append-only; arquivar nunca apaga.
- **Holidays**: feriados nacionais (seed) + feriados da empresa; alimentam `calc.dias_uteis`.

## 5. Estratégia multiempresa

Três barreiras, da mais importante à de reserva:
1. **Aplicação**: `company_id` vem só da sessão (`g.company.id`); toda consulta passa por
   `scoped()`/`get_or_404()` de `tenancy.py`; recurso de outra empresa responde 404.
2. **Testes**: `tests/test_isolation.py` percorre o `url_map` e falha se uma rota com
   `<uuid:...>` não tiver caso A/B (fase 7); cada rota nova ganha caso já na sua fase.
3. **Banco (RLS)**: políticas `USING (company_id = current_setting('app.company_id')::uuid)`
   em todas as tabelas de cliente; o app conecta com um papel sem `BYPASSRLS`. Ligado por
   `RLS_ENABLED` (ADR-0003).

Vínculo com várias empresas: `memberships` N:N; a troca de empresa reescreve
`session['company_id']` após validar o vínculo.

## 6. Autenticação

- Flask-Login + senha com Argon2id (`argon2-cffi`).
- Sessão: cookie `__Host-session`, Secure, HttpOnly, SameSite=Lax; `session_version` no
  usuário invalida todas as sessões (reset de senha, desativação, “sair de todos”).
- Tokens (confirmação, convite, reset, API): 32 bytes aleatórios, só o SHA-256 vai ao banco,
  uso único e expiração.
- MFA TOTP (`pyotp`) opcional; obrigatório para `owner` quando a empresa ativar; códigos de
  recuperação com hash.
- Bloqueio progressivo por conta e por IP + Flask-Limiter (Redis em produção).

## 7. Pagamento

- Interface `PaymentProvider` (`app/services/billing/provider.py`): `create_customer`,
  `create_subscription`, `change_plan`, `cancel`, `get_subscription`, `list_payments`.
  Implementações `AsaasProvider` (header `access_token`, base URL por env) e `FakeProvider`.
- Estados locais: `trialing → active ⇄ past_due → (grace) → expired`; `canceled` vale até
  `current_period_end`. `expired`/sem assinatura = modo leitura (nunca apaga dados).
- Webhook `POST /webhooks/asaas`: `hmac.compare_digest` do header `asaas-access-token`,
  `INSERT` em `webhook_events` com `external_event_id` UNIQUE antes de processar, resposta
  rápida; eventos fora de ordem → consulta o estado atual no Asaas.
- Reconciliação diária no worker (`flask billing-reconcile`).
- Nenhum dado de cartão passa pelo servidor: checkout do Asaas.

## 8. Eventos de domínio (outbox)

- `app/services/events.py::emit(type, payload)` adiciona uma linha em `domain_events` na
  **mesma transação** da mudança. Tipos do MVP: `project.created`,
  `activity.progress_updated`, `stage.completed`, `project.completed`.
- No MVP nada consome além das métricas internas. Na fase 9 o worker lê
  `published_at IS NULL` com `FOR UPDATE SKIP LOCKED` e entrega aos webhooks de saída.

## 9. API de publicação (fase 9, atrás de `FEATURE_PUBLIC_API`)

- Blueprint `/api/v1` registrado só com a flag ligada (desligada → 404).
- Autenticação `Authorization: Bearer <token>`; token por empresa, hash no banco, escopos
  `read:projects` e `write:progress`; rate limit por token; toda chamada em `audit_logs`.
- Contrato em `docs/api/openapi.yaml` (OpenAPI 3.1), erros RFC 9457, paginação por cursor,
  datas ISO 8601 UTC. `GET /projects/{id}/summary` devolve a saída de `calc.py`.
- Webhooks de saída: HMAC-SHA256 + timestamp, retentativas com backoff, bloqueio de IPs
  privados (SSRF).

## 10. Configuração e ambientes

| Variável | Uso |
|---|---|
| `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL` | básicos |
| `RLS_ENABLED`, `FEATURE_PUBLIC_API` | flags |
| `ASAAS_API_KEY`, `ASAAS_BASE_URL`, `ASAAS_WEBHOOK_TOKEN` | pagamento |
| `EMAIL_BACKEND`, `RESEND_API_KEY`, `MAIL_FROM` | e-mail |
| `SENTRY_DSN` | monitoramento |

Ambientes: `development` (SQLite ou Postgres local via docker-compose, e-mail no console),
`test` (Postgres via `TEST_DATABASE_URL`), `staging` e `production` (Render, segredos
distintos).
