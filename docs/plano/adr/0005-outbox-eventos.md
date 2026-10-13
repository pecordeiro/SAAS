# ADR-0005 — Outbox para eventos de domínio

- Status: proposto · Data: 2026-10-13

## Contexto
A API de publicação (fase 9) vai avisar sistemas externos quando algo muda. Publicar
direto na requisição perde eventos quando a transação falha ou a rede cai.

## Decisão
Tabela `domain_events` (outbox). Serviços gravam o evento na mesma transação da mudança.
Um worker lê `published_at IS NULL` com `FOR UPDATE SKIP LOCKED`, entrega e marca. No MVP
só gravamos (e usamos para métricas); a entrega começa na fase 9.

## Consequências
- (+) Consistência: evento existe se, e só se, a mudança existe.
- (+) Base para métricas do PRD, auditoria de produção e webhooks de saída.
- (−) Entrega “pelo menos uma vez”: consumidores precisam de idempotência (id do evento).
- (−) Tabela cresce; política de retenção (ex.: 180 dias após publicado).

## Alternativas
Fila externa (Redis/RabbitMQ) sem outbox: risco de inconsistência. CDC/Debezium: pesado
demais para o porte.
