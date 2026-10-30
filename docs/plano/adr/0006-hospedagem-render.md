# ADR-0006 — Hospedagem no Render com PostgreSQL gerenciado

- Status: proposto · Data: 2026-10-13

## Contexto
Equipe pequena, sem time de infra. Precisamos de web, worker, Redis e Postgres, dois
ambientes (staging e produção), HTTPS, deploy por Git e backups.

## Decisão
Render: serviço web (`gunicorn run:app`), background worker, Key Value (Redis) e Postgres
gerenciado, descritos em `render.yaml` (IaC). Pre-deploy roda `flask db upgrade`;
healthcheck em `/health`. Região mais próxima do Brasil oferecida pelo Render no momento do
deploy (confirmar latência e transferência internacional de dados na LGPD).
Backup extra diário criptografado fora do Render (fase 10).

## Consequências
- (+) Pouca operação; preview e rollback simples.
- (−) Dados possivelmente fora do Brasil: registrar na política de privacidade
  (transferência internacional, art. 33 LGPD).
- (−) Custo cresce com recursos; reavaliar acima de ~100 clientes.

## Alternativas
Fly.io, Railway (semelhantes); AWS/GCP com região em São Paulo (mais controle, mais
operação) — candidata se clientes exigirem dados no Brasil.
