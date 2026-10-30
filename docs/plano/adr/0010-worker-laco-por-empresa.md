# ADR-0010 — Worker em processo separado, empresa a empresa no contexto RLS

- Status: proposto (Etapa F) · Data: 2026-10-15 · Decisão a confirmar com o usuário

## Contexto
A Etapa F liga o worker previsto na arquitetura (§2) e no ADR-0005: publicar/consumir os
`domain_events` pendentes (ex.: `activity.assigned` → e-mail ao responsável) e rodar tarefas
agendadas (alertas, relatório semanal, reconciliação do Asaas, limpeza de tokens). O ADR-0003
deixou em aberto como o worker atravessa empresas com o RLS forçado: (a) laço por empresa com
`rls.set_context(company_id=…)`, ou (b) papel de plataforma dedicado (`BYPASSRLS`) só para o
worker.

## Decisão
1. **Laço por empresa, sem papel privilegiado** (opção a). O worker lê `companies` (sem RLS),
   e para cada empresa faz `rls.set_context(company_id=…)`, trabalha só nas linhas dela e dá
   `commit` antes de passar à próxima. Mesmo padrão já usado por `billing.reconcile_all`,
   `lgpd.apply_retention` e `flask suporte`. Nenhuma `DATABASE_URL` especial; o worker usa o
   mesmo papel comum do processo web (`NOSUPERUSER NOBYPASSRLS`).
2. **Processo separado**: `flask worker run` (laço com intervalo; `SIGTERM`/`SIGINT` param no
   fim do ciclo) e `flask worker run --once` (um ciclo e sai — testes e cron).
   `--task` escolhe tarefas (`events`, `alerts`, `weekly`, `reconcile`, `tokens`).
   `flask worker status` mostra pendentes/esgotados por empresa.
3. **Outbox**: um evento por vez, `SELECT … FOR UPDATE SKIP LOCKED` (PostgreSQL) dentro do
   contexto da empresa; handler por tipo (`worker.HANDLERS`); sucesso → `published_at`; erro →
   `attempts += 1`, `next_attempt_at = agora + backoff` (60 s × 2^tentativas, teto 6 h) e
   `last_error` (só o nome da exceção). Com `attempts ≥ WORKER_EVENT_MAX_ATTEMPTS` (8) o evento
   sai da fila (fica para análise em `flask worker status`). Tipo sem consumidor ainda (eventos
   públicos, enquanto não há webhooks de saída) é marcado publicado. Entrega “pelo menos uma
   vez”: o handler confere o estado atual antes de agir (ex.: responsável ainda é o mesmo).
4. **Tarefas agendadas idempotentes**: alertas com dedupe `UNIQUE(company_id, dedupe_key,
   day)`; relatório semanal com marca `job_runs (company_id, job, period_key)` única;
   reconciliação e limpeza de tokens já são idempotentes. Rodar duas vezes não duplica nada.

## Consequências
- (+) Nenhum caminho do app ou do worker escapa do RLS; um erro de consulta no worker não
  vaza dados de outra empresa (a consulta crua sem contexto volta vazia).
- (+) Mesmo papel de banco para web e worker: nada novo para provisionar no Render.
- (−) O worker visita todas as empresas a cada ciclo (consulta barata por índice
  `company_id, created_at`); com milhares de empresas, trocar o intervalo ou paginar.
- (−) Com RLS ligado não dá para contar a fila global numa consulta só; `status` soma por
  empresa.
- (−) Sem `FOR UPDATE SKIP LOCKED` no SQLite (só dev/test): lá rode um worker por vez.

## Alternativas
Papel `controle_platform` com `BYPASSRLS` e `DATABASE_URL` própria do worker — rejeitado:
reintroduz o papel privilegiado que o ADR-0003 (Fase 7) evitou em todos os outros fluxos e
exige segredo extra. Fila externa (Redis/RQ) — rejeitada pelo ADR-0005 (consistência).
