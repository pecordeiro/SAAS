# Runbook do worker (Etapa F)

Processo separado do web que consome o outbox (`domain_events`) e roda as tarefas agendadas.
Decisão de arquitetura: [ADR-0010](adr/0010-worker-laco-por-empresa.md) — laço empresa a
empresa com `rls.set_context`, **sem** papel `BYPASSRLS`; mesmo `DATABASE_URL` do web.

## Como rodar

```bash
flask worker run                     # laço: ciclo a cada WORKER_INTERVAL_SECONDS (30 s)
flask worker run --once              # um ciclo de todas as tarefas e sai (cron, testes)
flask worker run --once --task events --task alerts
flask worker status                  # pendentes e esgotados por empresa
```

No Render: um **Background Worker** com o mesmo build e as mesmas variáveis do web, comando
`flask worker run`. `SIGTERM` (deploy) para no fim do ciclo atual. Sem Background Worker,
um Cron Job a cada 5–15 min com `flask worker run --once` faz o mesmo (as tarefas são
idempotentes e respeitam dia/hora). Rode **um** worker por vez enquanto o banco for SQLite
(dev); no PostgreSQL dois workers não processam o mesmo evento (`FOR UPDATE SKIP LOCKED`) e as
marcas `UNIQUE` (alertas, relatório) impedem duplicar.

## Tarefas

| Tarefa | Intervalo no laço | O que faz | Idempotência |
|---|---|---|---|
| `events` | todo ciclo | consome `domain_events` pendentes, um por transação | `published_at`; handler confere o estado atual |
| `alerts` | 15 min | alertas automáticos (calc.alertas_projeto) + e-mail-resumo a partir das 7h locais | `UNIQUE(company_id, dedupe_key, day)`; e-mail da mesma chave no máx. 1×/7 dias |
| `weekly` | 15 min | relatório semanal (segunda, a partir das 7h locais) com XLSX | `job_runs (company_id, 'weekly_report', 'AAAA-Wss')` |
| `reconcile` | 24 h | `billing.reconcile_all` (Asaas) | já idempotente (Fase 8) |
| `tokens` | 24 h | apaga resets/confirmações/convites usados ou vencidos há mais de `RETENTION_TOKENS_DAYS` | `platform_audit_logs` só quando apaga algo |

Consumidores do outbox (`worker._handlers`):
- `activity.assigned` → e-mail ao responsável (preferência `notify_assignment`; não envia se a
  pessoa se atribuiu, se foi reatribuída depois, se saiu da empresa ou se a atividade foi arquivada).
- `plan.visual_custom_contracted` → e-mail à equipe em `STAFF_NOTIFY_EMAIL` (vazio = só marca).
- Demais tipos (públicos): marcados publicados — **atenção** ao implementar webhooks de saída:
  eles passam a ter consumidor e só então devem esperar as entregas.

## Falhas e retentativas

- Erro no handler (ex.: Resend fora do ar) → `attempts += 1`, `next_attempt_at = agora +
  60 s × 2^(tentativas−1)` (teto 6 h), `last_error` = só o nome da exceção.
- Com `attempts ≥ WORKER_EVENT_MAX_ATTEMPTS` (8) o evento sai da fila: aparece como
  “esgotados” em `flask worker status`. Para tentar de novo depois de corrigir a causa:
  `UPDATE domain_events SET attempts = 0, next_attempt_at = NULL WHERE id = '<id>'` (no
  contexto da empresa se o RLS estiver ligado: `SELECT set_config('app.company_id', '<empresa>', true)` na mesma transação).
- Uma tarefa que lança exceção é registrada no log (`tarefa X falhou`) e não derruba as
  outras; `--once` sai com código 1 se alguma tarefa falhou (o cron acusa).
- E-mail de resumo/relatório que falha para um destinatário: log de aviso (sem endereço) e
  segue para os outros; o resumo de alertas fica pendente se nenhum envio deu certo.

## Variáveis

| Variável | Padrão | Uso |
|---|---|---|
| `WORKER_INTERVAL_SECONDS` | 30 | pausa entre ciclos do laço |
| `WORKER_EVENT_MAX_ATTEMPTS` | 8 | tentativas por evento antes de sair da fila |
| `STAFF_NOTIFY_EMAIL` | vazio | aviso da requisição de identidade visual à equipe |
| `APP_BASE_URL` | — | obrigatório fora de dev/test: base de todos os links dos e-mails |
| `MAIL_BACKEND`, `RESEND_API_KEY`, `MAIL_FROM` | — | envio (o worker envia de forma síncrona) |

## Com RLS ligado

Nada a fazer além do web: o worker usa o mesmo papel comum e informa a empresa em cada
transação. Tabelas novas da Etapa F (`job_runs`, `alerts`) têm a política
`tenant_isolation`; se `flask rls enable` já tinha rodado antes das migrations, elas ligam o
RLS sozinhas na tabela nova (confira com `flask rls status`).

## Verificação rápida

```bash
flask worker status                         # fila vazia = tudo publicado
flask worker run --once --task alerts       # mostra {'companies': n, 'created': n, 'emails': n}
```
