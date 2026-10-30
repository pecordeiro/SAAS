# Webhooks de saída — desenho (não implementado)

Status: **somente desenho** (Fase 9). Nada disto existe em código. Implementação futura
sobre o outbox `domain_events` (já gravado na mesma transação da mudança). O worker existe
desde a Etapa F (`docs/plano/worker.md`); hoje ele só MARCA os eventos públicos como
publicados — ao implementar os webhooks, registre o consumidor em `worker._handlers` e decida
o que fazer com os eventos antigos já marcados.

## Fluxo
1. A empresa (owner, plano com feature `api`) cadastra uma URL HTTPS e escolhe os tipos de
   evento (`activity.progress_updated`, `stage.completed`, `project.completed`, ...). O
   segredo de assinatura (32 bytes aleatórios) é mostrado uma vez e guardado cifrado.
2. O worker lê `domain_events` com `published_at IS NULL` (empresa a empresa no contexto RLS, ADR-0010),
   cria uma entrega por endpoint inscrito e faz o POST.
3. Sucesso (2xx em até 10 s) marca a entrega como feita; o evento só recebe `published_at`
   quando todas as entregas terminam (sucesso ou esgotadas).

## Requisição
`POST <url>` com `Content-Type: application/json` e corpo:

```json
{"id": "<uuid do evento>", "type": "activity.progress_updated", "created_at": "2026-10-13T14:30:00.000Z", "company_id": "<uuid>", "data": { ... }}
```

Cabeçalhos:
- `X-Webhook-Id`: id do evento (idempotência no receptor; o mesmo id se repete nas retentativas).
- `X-Webhook-Timestamp`: segundos Unix do envio.
- `X-Webhook-Signature`: `v1=<hex>` com `HMAC-SHA256(segredo, timestamp + "." + corpo_bruto)`.

O receptor deve recalcular o HMAC sobre o corpo bruto, comparar em tempo constante e
recusar se o timestamp tiver mais de 5 minutos de diferença (anti-replay).
Rotação de segredo: dois segredos válidos por 24 h; a assinatura leva um `v1=` por segredo.

## Retentativas
Falha = timeout, erro de conexão, 3xx (não segue redirecionamento) ou status fora de 2xx.
Backoff exponencial com jitter: 1 min, 5 min, 30 min, 2 h, 6 h, 24 h (6 retentativas).
Depois disso a entrega fica `failed` e aparece na tela; 410 Gone desativa o endpoint.
Endpoint com 20 falhas seguidas é pausado e o owner é avisado por e-mail.
`domain_events.attempts` conta as tentativas.

## Bloqueio de SSRF
Antes de cada envio (não só no cadastro, por causa de DNS rebinding):
- Só `https://`, porta 443 (ou lista curta permitida), sem credenciais na URL.
- Resolver o nome e **conectar no IP já validado** (fixar o IP resolvido na conexão).
- Recusar IP privado, loopback, link-local (169.254.0.0/16, incluindo metadados de nuvem),
  CGNAT 100.64.0.0/10, multicast, reservado e os equivalentes IPv6 (`::1`, `fc00::/7`,
  `fe80::/10`, IPv4 mapeado em IPv6). Python: `ipaddress` com `is_global`.
- Não seguir redirecionamentos; limitar o corpo da resposta lido (ex.: 64 KB) e descartá-lo.
- Em produção, o worker sai por proxy de egresso que também bloqueia as faixas internas.

## Dados
Payload só com ids e números do evento (sem e-mail, nome de pessoa ou token). Logs guardam
status, duração e id da entrega, nunca o segredo nem o corpo da resposta.
