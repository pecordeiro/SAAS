# Pagamentos — Asaas atrás de `PaymentProvider` (Fase 8)

Decisão: [ADR-0004](adr/0004-asaas-paymentprovider.md). Código em `app/services/billing/`
(`provider.py` interface, `asaas.py`, `fake.py`, `service.py` regras, `cli.py`, `notify.py`,
`documents.py`), telas em `app/blueprints/billing.py` (`/app/assinatura`) e webhook em
`app/blueprints/webhooks.py` (`POST /webhooks/asaas`).

## 1. Fontes consultadas (2026-10-14)

O acesso direto a `docs.asaas.com` e `api-sandbox.asaas.com` foi **bloqueado pela rede** do
ambiente de desenvolvimento (proxy recusou o túnel). As informações abaixo vieram de busca
na web sobre as páginas oficiais (resumos das próprias páginas) e do que o plano já
descrevia. **Confira no sandbox (roteiro na seção 5) antes de ir para produção.**

| Assunto | URL oficial | O que confirmamos |
|---|---|---|
| Autenticação | https://docs.asaas.com/docs/autenticação | Chave no header `access_token` (não `Authorization: Bearer`); sandbox `https://api-sandbox.asaas.com/v3`, produção `https://api.asaas.com/v3`; chave de sandbox começa com `$aact_hmlg_`, de produção com `$aact_prod_`; `User-Agent` obrigatório para contas novas. |
| Criar assinatura | https://docs.asaas.com/docs/criando-uma-assinatura · https://docs.asaas.com/reference/assinaturas-1 | `POST /v3/subscriptions` com `customer`, `billingType`, `nextDueDate`, `value`, `cycle` (`MONTHLY`…), `description`; o Asaas gera as cobranças sozinho; cobranças da assinatura em `GET /v3/subscriptions/{id}/payments`. |
| Eventos de webhook | https://docs.asaas.com/docs/webhooks-events · https://docs.asaas.com/docs/sobre-os-webhooks | Payload com `id` do evento, `event` e o objeto (`payment`/`subscription`); entrega **pelo menos uma vez** (precisa ser idempotente); resposta fora de 2xx gera reenvio; eventos guardados por até 14 dias. |
| Eventos de cobrança | https://docs.asaas.com/docs/payment-events · https://docs.asaas.com/docs/eventos-para-pagamentos | `PAYMENT_CREATED`, `PAYMENT_CONFIRMED` (pago, saldo ainda indisponível), `PAYMENT_RECEIVED` (recebido), `PAYMENT_OVERDUE`, `PAYMENT_REFUNDED`, `PAYMENT_DELETED`, `PAYMENT_RESTORED`, chargeback etc. |
| Eventos de assinatura | https://docs.asaas.com/docs/subscription-events · https://docs.asaas.com/docs/eventos-para-assinaturas | `SUBSCRIPTION_CREATED`, `SUBSCRIPTION_UPDATED`, `SUBSCRIPTION_INACTIVATED`, `SUBSCRIPTION_DELETED`. |
| Token do webhook | https://docs.asaas.com/changelog/obrigatoriedade-e-auto-geração-de-tokens-para-webhooks · https://docs.asaas.com/docs/receba-eventos-do-asaas-no-seu-endpoint-de-webhook | `authToken` obrigatório ao cadastrar webhook (gerado pelo Asaas se omitido, mostrado uma vez). |

Não confirmado pela busca (seguimos o plano/arquitetura; **verificar no sandbox**):
- nome do header em que o Asaas envia o token: usamos **`asaas-access-token`**;
- `billingType: "UNDEFINED"` aceito em assinatura (cliente escolhe Pix/boleto/cartão na fatura);
- campo `invoiceUrl` na cobrança (página de pagamento);
- política de fila: muitas respostas de erro seguidas **interrompem a fila** de webhooks da
  conta — por isso respondemos 200 mesmo quando o processamento falha (ver 3).

## 2. Mapeamento

| Nosso | Asaas |
|---|---|
| `create_customer` | `POST /customers` (`name`, `cpfCnpj`, `email`, `externalReference` = id da empresa) |
| `update_customer` | `PUT /customers/{id}` |
| `create_subscription` | `POST /subscriptions` (`billingType=UNDEFINED`, `cycle=MONTHLY`, `value` em reais, `nextDueDate`) |
| `change_plan` | `PUT /subscriptions/{id}` (`value`, `description`, `updatePendingPayments=true`) |
| `cancel` | `DELETE /subscriptions/{id}` |
| `get_subscription` | `GET /subscriptions/{id}` (`status` ≠ `ACTIVE` ou `deleted` = inativa) |
| `list_payments` | `GET /subscriptions/{id}/payments` (paginado, `offset`/`limit`/`hasMore`) |

Status de cobrança → local (`payments.status`): `PENDING`/análise de risco → `pending`;
`CONFIRMED` → `confirmed`; `RECEIVED`/`RECEIVED_IN_CASH`/`DUNNING_RECEIVED` → `received`;
`OVERDUE`/`DUNNING_REQUESTED` → `overdue`; `REFUNDED` e chargeback → `refunded`
(tira o acesso daquele mês); `REFUND_REQUESTED`/`REFUND_IN_PROGRESS` seguem como pagos até o
estorno sair; `deleted: true` → `canceled`.

## 3. Regras

- **Planos (ADR-0019)**: Essencial R$ 249,90 (5 projetos, 5 pessoas), Profissional R$ 497,90
  (10 projetos, 25 pessoas), Empresa R$ 997,90 (ilimitado, MFA, API, identidade visual) e
  Implantação sob orçamento (`price_cents` NULL; implantação, 1 mês de acompanhamento e
  treinamento são serviços, só texto). Valores e limites só na tabela `plans`
  (`app/services/plans.py` + migrations `b1e7c9d2a4f6` e `a9d3f5c1b7e2`; `flask seed-plans` sincroniza).
- **Teste grátis**: 14 dias sem cartão, **só no Essencial e no Profissional**
  (`plans.TRIAL_PLAN_CODES`). O cadastro começa no Profissional (`TRIAL_DAYS`,
  `DEFAULT_TRIAL_PLAN`; valor fora dos planos com teste é ignorado e cai no Profissional). A
  assinatura `trialing` é criada no cadastro (Fase 5) ou, na falta, na primeira visita a
  `/app/assinatura` (mesma data: criação da empresa + 14 dias). Assinatura `trialing` num
  plano sem teste vale como o Profissional em `entitlements.access` (recurso pago nunca sai
  de graça no teste).
- **Empresa (sem teste)**: assinar o Empresa durante o teste gera a 1ª cobrança **com
  vencimento no dia** (não espera o fim do teste); como é upgrade, o plano fica pendente e só
  vale com essa fatura paga. Ao passar a valer (pago ou atribuído), grava
  `plan.visual_custom_contracted` em `audit_logs` e `domain_events` (evento interno, não sai em
  webhook de cliente) — gancho da requisição de identidade visual (Etapa C).
- **Implantação (sob consulta)**: não aparece com botão de contratar; `/app/assinatura/planos/
  implantacao` e `/app/assinatura/cobranca?plano=implantacao` respondem 404 e o serviço
  recusa (`BillingError`). Só `flask billing-admin set-plan --company <uuid> --plan
  implantacao --reason "..."` atribui: cancela a recorrência no Asaas (se houver), cancela
  cobranças em aberto, deixa a assinatura `active` sem fim de período e audita
  (`subscription.admin_plan_set`, motivo obrigatório). O recálculo/reconciliação não mexe
  nela; o proprietário não troca nem cancela pela tela (“fale conosco”). `set-plan` para um
  plano com preço só funciona com assinatura viva no provedor (muda o valor lá).
- **Assinar**: plano → dados de cobrança (CPF/CNPJ com dígito verificador no formulário e de
  novo no serviço) → cliente + assinatura no provedor → redireciona (303) para a `invoiceUrl`
  da primeira cobrança, só se for `https` e o host estiver em `BILLING_CHECKOUT_HOSTS`. Em
  teste grátis, num plano com teste, a 1ª cobrança vence no último dia do teste (pagar antes
  não encurta o teste); no Empresa vence no dia.
  Nenhum dado de cartão passa pelo nosso servidor.
- **Estado é recalculado** das cobranças (`service.recompute`), não “empurrado” por evento:
  - paga (`confirmed`/`received`) cobre do vencimento até o mesmo dia do mês seguinte
    (`current_period_end`, 23:59:59 de São Paulo) → `active`;
  - vencida sem cobertura → `past_due`, `grace_until` = vencimento + 7 dias, e-mail aos
    proprietários (uma vez, na entrada em atraso) e faixa no topo do `/app`;
  - passada a carência → `expired` = **modo leitura** (402 em escrita, leitura e exportação
    liberadas, nada apagado);
  - cancelada → `canceled` com acesso até `current_period_end` (ou fim do teste), depois
    `expired`;
  - estorno/chargeback → a cobertura daquele mês some; sem outra cobertura → `expired`.
- **Fora de ordem**: um evento que faz a cobrança “voltar” (ex.: `OVERDUE` depois de
  `RECEIVED`) ou conflita com o status local → consultamos `list_payments` e vale o provedor.
- **Trocar plano** (projeção: valor atual × novo, diferença, próxima fatura e quando vale):
  - **upgrade** (mais caro): o Asaas passa a cobrar o valor novo já na fatura em aberto
    (`updatePendingPayments`); o plano novo fica em `subscriptions.pending_plan_id` e só vira
    o plano da empresa quando uma fatura **no valor novo** for paga depois do pedido — os
    limites sobem na requisição seguinte ao pagamento confirmado (“vale após o pagamento”).
    Pedir upgrade e cancelar não libera nada (a troca pendente é descartada);
  - **mesmo preço** (outro plano com valor igual): tratado como upgrade — só vale depois de
    uma fatura paga após o pedido, nunca de graça na hora; **preço nulo** (sob consulta) de um
    dos lados: recusado (`service.compare_plans` devolve `managed`);
  - **downgrade** (estritamente mais barato): vale no fim do período já pago ou do teste
    (`pending_plan_at`; aplicado pelo recálculo/`billing-reconcile`). O uso atual precisa caber
    no plano menor ao pedir (a mensagem diz quantos projetos arquivar/usuários remover) e de
    novo na hora de aplicar: se não couber mais, a troca NÃO é aplicada — plano e preço atuais
    ficam (o valor no Asaas volta ao do plano atual), o pendente é limpo, a recusa vai para
    `audit_logs` (`subscription.downgrade_canceled`) e os proprietários recebem e-mail;
  - **bloqueado** com pagamento em atraso (`past_due`), cancelada ou encerrada;
  - assinar durante o teste/período pago num plano mais caro segue a mesma regra do upgrade;
  - sem cobrança proporcional.
- **Falha do provedor no meio da assinatura**: todas as chamadas ao Asaas (cliente,
  assinatura, cobranças) acontecem antes de qualquer mudança local; se uma falhar, a
  transação é desfeita e só o `provider_customer_id` recém-criado é gravado numa transação
  separada (para não duplicar o cliente na próxima tentativa). Status e plano não mudam.
- **Webhook** (`POST /webhooks/asaas`): sem CSRF; rate limit `WEBHOOK_RATE_LIMIT`; header
  `asaas-access-token` comparado com `hmac.compare_digest` contra `ASAAS_WEBHOOK_TOKEN`
  (sem token configurado → tudo 401); `webhook_events.external_event_id` (UNIQUE) gravado e
  commitado ANTES de processar — repetido → 200 `duplicate` sem efeito; erro no processamento
  → `status=failed` + `error` (classe e mensagem segura, sem payload) e **200** (não
  travar a fila do Asaas); a correção vem do `flask billing-reconcile`.
- **RLS**: o webhook não sabe a empresa. A política `subscriptions_provider_lookup`
  (migration `d8b2e6f4a1c7`) libera **SELECT** em `subscriptions` só da linha cujo
  `provider_subscription_id` = `app.billing_lookup` (SET LOCAL feito só durante a busca);
  achada a assinatura, o contexto RLS passa a ser a empresa dela. Testado com papel comum em
  `tests/test_billing_rls.py`.
- **Admin da plataforma** (CLI, sem tela): `flask billing-admin extend-trial --company <uuid>
  --days N --reason "..."` e `flask billing-admin discount --company <uuid> --percent P
  --reason "..."` (0–90 %; aplica no Asaas; recusado em plano sob consulta) e `flask
  billing-admin set-plan --company <uuid> --plan <código> --reason "..."` (Etapa B; único
  caminho para a Implantação). `extend-trial` é recusado em plano sem teste. Motivo obrigatório (≥ 5 caracteres) em
  `audit_logs.details.motivo`, `actor_user_id` nulo e `"por": "admin da plataforma"`.
- **Reconciliação**: `flask billing-reconcile` (idempotente; agendar 1x/dia no worker na
  Fase 10) — por empresa: estado da assinatura no provedor, todas as cobranças, recálculo.
- **Log**: só método, caminho, HTTP e códigos de erro do Asaas. Nunca a chave, o corpo
  enviado (CPF/CNPJ) nem o payload recebido.

## 4. Configuração

| Variável | Uso |
|---|---|
| `ASAAS_API_KEY` | chave da conta (sandbox `$aact_hmlg_…`, produção `$aact_prod_…`) |
| `ASAAS_BASE_URL` | padrão `https://api-sandbox.asaas.com/v3`; produção `https://api.asaas.com/v3` |
| `ASAAS_WEBHOOK_TOKEN` | o mesmo `authToken` cadastrado no webhook do Asaas |
| `BILLING_PROVIDER` | `asaas` ou `fake` (vazio = `asaas` com chave, `fake` sem; fake só em dev/test) |
| `WEBHOOK_RATE_LIMIT` | padrão `120 per minute` |
| `APP_BASE_URL` | (Fase 5) link absoluto no e-mail de atraso |

## 5. Roteiro do ciclo real no sandbox (pendente — fazer com a sua chave)

Não executado nesta fase (sem acesso de rede ao Asaas a partir do ambiente de
desenvolvimento). Registre a data, prints e observações em uma seção “Execução” abaixo.

1. **Conta sandbox**: crie em https://sandbox.asaas.com, gere a chave em Integrações → Chave
   de API (começa com `$aact_hmlg_`). Não cole a chave em commit, issue ou chat.
2. **Expor o app**: rode local com um túnel HTTPS (ex.: `cloudflared tunnel --url
   http://localhost:5000`) ou use o staging. Anote a URL pública.
3. **Variáveis** (`.env`): `ASAAS_API_KEY=…`, `ASAAS_BASE_URL=https://api-sandbox.asaas.com/v3`,
   `ASAAS_WEBHOOK_TOKEN=<gere com python -c "import secrets; print(secrets.token_urlsafe(32))">`,
   `APP_BASE_URL=<url pública>`. `flask db upgrade`.
4. **Webhook no Asaas** (Integrações → Webhooks): URL `<url pública>/webhooks/asaas`, token =
   `ASAAS_WEBHOOK_TOKEN`, API v3, fila ativa, eventos de **cobrança** e **assinatura**.
   Confirme no primeiro evento que o header recebido é `asaas-access-token` (se não for,
   ajuste `app/blueprints/webhooks.py` e este documento).
5. **Teste grátis**: cadastre uma empresa nova → `/app/assinatura` mostra “Teste grátis” e a
   faixa “faltam 14 dias”. Print.
6. **Assinar**: Escolher plano → Essencial → CNPJ de teste válido (ex.: `11.222.333/0001-81`)
   → deve abrir a fatura do Asaas (`sandbox.asaas.com/i/...`). Confira no painel: cliente,
   assinatura mensal R$ 249,90 com vencimento no fim do teste. Print das duas telas. Repita
   com o **Empresa** numa empresa nova: R$ 997,90 com vencimento **hoje** (sem teste).
7. **Pagar**: na fatura do sandbox, pague por Pix/cartão de teste (ou “Confirmar pagamento”
   no painel). Espere `PAYMENT_CONFIRMED`/`PAYMENT_RECEIVED` → `/app/assinatura` = **Ativa**,
   “Período pago até” = vencimento + 1 mês; `webhook_events` com `processed`. Print.
8. **Duplicado**: no painel de webhooks, reenvie o mesmo evento → resposta 200 `duplicate` e
   nada muda.
9. **Trocar plano**: Essencial → Profissional mostra +R$ 248,00 e “vale após o pagamento”;
   confirme; no Asaas o valor da assinatura e da fatura em aberto vira R$ 497,90; o 6º projeto
   continua bloqueado até pagar essa fatura e passa a ser permitido logo depois. Rebaixar
   mostra “vale a partir de DD/MM” (fim do período pago).
10. **Atraso**: crie (ou espere) uma cobrança vencida no sandbox / altere o vencimento para
    ontem → `PAYMENT_OVERDUE` → **Pagamento em atraso**, e-mail aos proprietários, faixa com
    a data da carência. Pague → volta a **Ativa** (“pago com atraso”).
11. **Estorno**: estorne uma cobrança paga no painel → `PAYMENT_REFUNDED` → sem outra
    cobertura, **modo leitura**; dados intactos.
12. **Cancelar**: Assinatura → Cancelar → confirme no modal → **Cancelada, acesso completo até
    …**; no Asaas a assinatura some/inativa e cobranças em aberto são removidas.
13. **Reconciliação**: `flask billing-reconcile` duas vezes — a segunda deve dizer
    `corrigidas: 0`.
14. **Implantação**: `flask billing-admin set-plan --company <uuid> --plan implantacao
    --reason "Contrato ..."` → no Asaas a assinatura é inativada; `/app/assinatura` mostra
    “Implantação · sob consulta”, sem trocar/cancelar; `flask billing-reconcile` não muda nada.
15. **Token inválido**: `curl -X POST <url>/webhooks/asaas -H 'asaas-access-token: x' -d '{}'`
    → 401.

Critério da Fase 10 (produção): cobrança real de valor baixo paga e estornada.

## 6. Limitações conhecidas

- Chamada ao provedor e commit local não são atômicos: se o banco falhar depois de criar a
  assinatura no Asaas, ela fica órfã lá (sem `externalReference` duplicado do nosso lado);
  o cliente criado é guardado mesmo se a assinatura falhar.
- Sem cobrança proporcional na troca de plano (a fatura em aberto muda de valor).
- Nota fiscal manual (D6).
- O desconto do admin fica em `subscriptions.discount_percent` e vale também em trocas de
  plano e em nova assinatura; para tirar, `--percent 0`.
- O FakeProvider não tem página de pagamento (a `invoiceUrl` aponta para
  `pagamento.fake.invalid`): em desenvolvimento, simule o pagamento pelos testes ou use o
  sandbox.
- Evento com `status=failed` não é reprocessado a partir do payload (não guardamos payload);
  a reconciliação busca o estado no Asaas.
