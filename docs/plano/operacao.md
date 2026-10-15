# Operação — deploy, e-mail, backup, restauração e monitoramento

Etapa H. Este é o runbook do dia a dia; a lista ordenada do que fazer para lançar (e quem faz)
está em [lancamento.md](lancamento.md). Decisões: [ADR-0006](adr/0006-hospedagem-render.md) e
[ADR-0012](adr/0012-deploy-saude-papeis-de-banco.md).

Onde algo depende de painel de terceiros (Render, Resend, Cloudflare, Sentry, Asaas), o texto
diz **“confirme no painel”**: nomes de plano, preços, janelas de retenção e menus mudam, e este
repositório não tem como verificá-los.

## 1. Topologia

```
                    Cloudflare/Registro.br (DNS)
                              │ HTTPS (TLS no Render)
┌───────────────────────── Render, região virginia ─────────────────────────┐
│  controle-web      gunicorn (Docker)  ── /saude (liveness) · /health (com banco)
│  controle-worker   flask worker run   ── outbox, alertas, relatório semanal, reconciliação
│  controle-lgpd     cron 06:00 UTC     ── flask lgpd-retencao && flask lgpd-purge
│  controle-monitor  cron */10 min      ── flask worker status --check (falha = aviso do Render)
│  controle-backup   cron 07:00 UTC     ── dump criptografado → R2 + espelho das fotos
│  controle-redis    Key Value          ── rate limit e bloqueio de login (rede privada)
│  controle-db       PostgreSQL 16      ── rede privada; backups/PITR do Render
└───────────────────────────────────────────────────────────────────────────┘
        │                         │                       │
   Resend (e-mail)      Cloudflare R2 (fotos,      Asaas (cobrança, webhook
                         backups)                  → /webhooks/asaas)        Sentry (erros)
```

Um único `Dockerfile` serve web, worker e crons (muda só o comando). O `render.yaml`
(produção) e o `render.staging.yaml` (homologação) são **gerados** por
`python scripts/gen_render_yaml.py` — não edite à mão; o CI falha se estiverem fora de
sincronia. Antes de criar o Blueprint: `render blueprints validate render.yaml` (Render CLI).

### Região

O Render **não tem região em São Paulo** (regiões atuais: Oregon, Ohio, Virginia, Frankfurt,
Singapore — confirme no painel, a lista muda). A mais próxima do Brasil é **Virginia** (leste
dos EUA), com latência típica na faixa de 110–140 ms a partir de São Paulo, contra ~200 ms de
Frankfurt. Tudo (web, worker, crons, Key Value e banco) precisa estar na **mesma região** para
usar a rede privada. A região fica em `scripts/gen_render_yaml.py::REGION`; trocar exige
recriar o banco e o Redis (não dá para mover). Consequência de LGPD: dados armazenados nos
EUA = **transferência internacional** (art. 33) — já listada em `lgpd.md` e precisa estar na
política de privacidade (item do advogado em `lancamento.md`). Se um cliente exigir dados no
Brasil, a alternativa do ADR-0006 é AWS/GCP em São Paulo.

## 2. Deploy

- **Produção**: `autoDeploy: false`. Depois do go/no-go, o deploy é manual (Render → serviço →
  *Manual Deploy → Deploy latest commit* do branch `main`). **Staging**: `autoDeploy: true`
  no branch `staging`.
- **preDeployCommand** (só no web, antes de trocar a versão):
  `flask config-check --online && flask db upgrade && flask seed-plans`.
  Se qualquer etapa falhar, o Render **cancela o deploy e mantém a versão anterior no ar**.
  O `config-check` reprova segredo fraco, `APP_BASE_URL` sem https, Redis ausente,
  `MFA_ENCRYPTION_KEY` ausente, e-mail em modo console, fotos em disco local, Asaas sandbox em
  produção, `RLS_ENABLED` desligado etc., listando tudo de uma vez (sem imprimir valores).
- **Health check**: `GET /saude` (200 `{"status":"ok"}`), sem banco, sem dado sensível. Uma queda
  do banco **não** reinicia o web em laço; a prontidão com banco é `GET /health` (503 se o
  banco não responde) e é o que o monitor de uptime deve olhar (seção 7).
- **Zero downtime**: o Render sobe a nova instância, espera `/saude` e só então tira a antiga.
  Migrations seguem **expandir → contrair**: a migration do deploy N não pode quebrar o código
  do deploy N−1 (que ainda atende durante a troca).
- **Migrations com RLS forçado**: depois de `flask rls enable`, o papel do app está sujeito às
  políticas também dentro do `flask db upgrade`. Migration que **lê ou grava linhas de tabelas
  de cliente** (data migration) precisa informar a empresa (`SELECT set_config('app.company_id',
  …, true)`) ou desligar o RLS na janela (`flask rls disable` → deploy → `flask rls enable`).
  Migration só de DDL (criar/alterar tabela, índice) não é afetada; tabela nova de cliente
  nasce com a política e liga o RLS sozinha se ele já estiver ativo (ver `worker.md`).

### Rollback

1. **Código**: Render → serviço web → *Events/Deploys* → deploy anterior → *Rollback*. Faça o
   mesmo no worker e nos crons (mesmo commit). Pronto em ~2–5 min.
2. **Banco**: o rollback do Render **não desfaz migration**. Como as migrations são
   retrocompatíveis (expandir → contrair), o código anterior continua funcionando com o schema
   novo. Só use `flask db downgrade` se a migration for reversível e **nenhum dado novo** depender
   dela; senão restaure (seção 5) — e isso é decisão de quem está de plantão com o dono.
3. **Configuração**: variável de ambiente alterada por engano → voltar o valor (o histórico
   fica em Render → Environment → *Audit log*, confirme no painel) e redeploy.
4. **Registrar** o incidente (`incidentes.md`) se houve indisponibilidade ou perda de dado.

## 3. Variáveis de ambiente

Fonte da verdade do formato: `.env.example`. No Render só o **web** recebe os segredos
(`sync: false`, digitados uma vez ao criar o Blueprint); worker e crons os leem do web
(`fromService` + `envVarKey`). `DATABASE_URL` vem de `fromDatabase` e `REDIS_URL` do Key Value.

| Variável | Origem | Como gerar / valor |
|---|---|---|
| `SECRET_KEY` | digitada | `python -c "import secrets; print(secrets.token_hex(32))"` · guarde no gerenciador de senhas |
| `MFA_ENCRYPTION_KEY` | digitada | outro `token_hex(32)`, **independente**. Perder = todo MFA precisa ser reativado |
| `APP_BASE_URL` | digitada | `https://app.seudominio.com.br` (sem barra no fim; https obrigatório) |
| `CONTACT_EMAIL` | digitada | e-mail de atendimento real (aparece em `/contato`) |
| `MAIL_FROM` | digitada | `Controle de Produção <nao-responda@seudominio.com.br>` (domínio verificado no Resend) |
| `RESEND_API_KEY` | digitada | Resend → API Keys → permissão **Sending access** restrita ao domínio |
| `ASAAS_API_KEY` | digitada | produção `$aact_prod_…`; staging sandbox `$aact_hmlg_…` |
| `ASAAS_WEBHOOK_TOKEN` | digitada | `python -c "import secrets; print(secrets.token_urlsafe(32))"` (o mesmo no webhook do Asaas) |
| `STORAGE_S3_ENDPOINT` / `_BUCKET` | digitadas | R2: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` e o nome do bucket **privado** de fotos |
| `STORAGE_S3_ACCESS_KEY_ID` / `_SECRET_ACCESS_KEY` | digitadas | token R2 com *Object Read & Write* **só neste bucket** |
| `SENTRY_DSN` | digitada | Sentry → projeto → Client Keys |
| `STAFF_NOTIFY_EMAIL` | digitada | quem recebe o aviso de requisição de identidade visual |
| `DATABASE_URL` | `fromDatabase` | injetada |
| `REDIS_URL` | `fromService` | injetada |
| `APP_ENV`, `RLS_ENABLED`, `TRUSTED_PROXY_COUNT`, `LOG_*`, `BILLING_PROVIDER`, `ASAAS_BASE_URL`, `MAIL_BACKEND`, `STORAGE_BACKEND`… | valor fixo no `render.yaml` | não são segredo |
| `BACKUP_*` (cron de backup) | digitadas | seção 5 |

`TRUSTED_PROXY_COUNT=1` é valor fixo (não segredo): atrás do proxy do Render há exatamente
um salto; com `0` todo cliente teria o IP do proxy e o rate limit/bloqueio de login valeria para
todos juntos (o `config-check` reprova).

Rotação: ver `incidentes.md` → “Rotação de segredos”.

## 4. Banco: papéis, RLS e calendário

### O papel do banco no Render

O RLS (ADR-0003) **não vale para superusuário nem para papel com `BYPASSRLS`**. O app e o
worker conectam com o usuário do `DATABASE_URL`. Antes de ligar o RLS é preciso saber **o que o
papel do Render é de verdade** (isto não dá para verificar daqui). No Shell do Render:

```bash
psql "$DATABASE_URL" -Atc "SELECT rolname, rolsuper, rolbypassrls, rolcreaterole FROM pg_roles WHERE rolname = current_user"
```

| Resultado | O que fazer |
|---|---|
| `rolsuper = f` e `rolbypassrls = f` | Ótimo: é um papel comum. `flask rls enable` com ele vale (o `FORCE` cobre até o dono das tabelas). |
| `rolsuper = t` ou `rolbypassrls = t` | O RLS **não protegeria nada**. Criar um papel comum para o app/worker/crons (`CREATE ROLE controle_app LOGIN PASSWORD '…' NOSUPERUSER NOBYPASSRLS`; `GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public`, `GRANT USAGE, SELECT ON ALL SEQUENCES`, `ALTER DEFAULT PRIVILEGES …`) e usar o papel dono só para migrations (pre-deploy) e backup. Isso exige uma variável de banco separada — **pedir aprovação (ADR)** antes, pois muda o `render.yaml`. |

`flask config-check --online` já reprova (`DB_ROLE`) quando `RLS_ENABLED=1` e o papel ignora o RLS.

### Backup e RLS forçado

Com `FORCE ROW LEVEL SECURITY`, o `pg_dump` de um papel comum **falha** ("query would be
affected by row-level security policy") — e o remédio errado (`--enable-row-security`) gravaria
um dump **vazio**. Por isso `scripts/backup_dump.sh` e `backup_restore_check.sh` **recusam**
(saída 3) quando o papel não é superusuário/`BYPASSRLS` e há RLS forçado. O papel que faz o dump
precisa enxergar tudo: confirme com o suporte do Render qual papel pode fazer `pg_dump` completo
no seu plano (ou use o papel de backup do item acima). Os backups gerenciados do Render (seção
5.1) são feitos pela plataforma e não dependem disto.

### Calendário de feriados e RLS

`flask seed-holidays` grava linhas com `company_id` nulo, que o RLS forçado **recusa**. Ordem
segura: `flask seed-holidays --de 2026 --ate 2035` (10 anos) **antes** de `flask rls enable`.
Para estender depois (o `config-check --online` avisa quando o calendário acaba no ano que
vem): `flask rls disable` → `flask seed-holidays --ate AAAA` → `flask rls enable`
(~segundos; faça em horário calmo).

## 5. Backup e restauração

Metas (roadmap, Fase 10): **RPO ≤ 24 h** e **RTO ≤ 4 h**.

### 5.1 Camadas

| Camada | O que cobre | Frequência | Retenção | Quem opera |
|---|---|---|---|---|
| **A. Backups gerenciados do Render** (banco) | queda/corrupção do banco, erro humano recente | contínuo (PITR) e/ou diário — **confirme no painel o que o seu plano inclui** | janela do plano (tipicamente poucos dias; **confirme**) | Render |
| **B. Dump lógico criptografado** (`controle-backup`) | perda da conta/serviço no Render, erro descoberto tarde, exigência de 30 dias | diário 07:00 UTC | **30 dias** (`BACKUP_RETENTION_DAYS`, alinhado a `lgpd.md`); mínimo de 3 sempre preservados | cron + dono |
| **C. Espelho do bucket de fotos** | perda/corrupção do bucket de fotos | diário (junto da B) | espelho: o que é apagado na origem some na próxima execução | cron |
| **D. Teste de restauração** | prova que A/B funcionam | mensal e antes do go-live | — | dono |

A camada A **sozinha não cumpre os 30 dias** do `lgpd.md`; é a B que garante a janela
documentada. Se o plano do Render tiver janela maior, melhor — a política de privacidade deve
citar **a janela real mais longa** em que um dado apagado ainda existe em backup.

### 5.2 Dump diário (camada B)

`scripts/backup_dump.sh` (roda no cron `controle-backup`, imagem `docker/backup/Dockerfile`):
`pg_dump -Fc --no-owner --no-privileges` → confere que lê (`pg_restore --list`) → **criptografa
com `age`** (chave pública `BACKUP_AGE_RECIPIENT`) → envia `db/controle-AAAAMMDDTHHMMSSZ.dump.age`
+ `.sha256` ao bucket de backup → apaga o que passou da retenção.

Preparação (uma vez, dono):
1. `age-keygen -o chave-backup.txt` (num computador seu). Guarde o **arquivo inteiro** no
   gerenciador de senhas **e** uma cópia impressa/offline. A linha `# public key: age1…` vai em
   `BACKUP_AGE_RECIPIENT` (Render). **Sem a chave privada o backup é inútil; quem a tem lê tudo.**
2. Cloudflare R2: crie o bucket **`controle-backup`** (privado, separado do de fotos) e um token
   com *Object Read & Write* nele **+ leitura no bucket de fotos** (para o espelho).
   `BACKUP_S3_ENDPOINT/_BUCKET/_ACCESS_KEY_ID/_SECRET_ACCESS_KEY` no cron.
3. Regra de ciclo de vida no R2 (defesa em profundidade): expirar `db/` após **35 dias**.
4. Rode uma vez à mão (Render → cron → *Trigger Run*) e confira o objeto no bucket.

Falhou (saída ≠ 0) → o Render avisa por e-mail de cron com falha. Códigos: 2 configuração, 3 papel
sem acesso a todas as linhas (RLS), 4 dump inválido, 5 envio/limpeza, 6 trava das fotos.
Teste local sem enviar: `BACKUP_DRY_RUN=1 BACKUP_OUT_DIR=/tmp/x DATABASE_URL=… scripts/backup_dump.sh`.

### 5.3 Fotos (camada C)

`scripts/backup_photos.sh`: `aws s3 sync --delete` do bucket de fotos para
`s3://<backup>/fotos/atual/`. Premissas: mesma conta R2, chave de backup com leitura no bucket de
fotos. É **espelho com apagamento** de propósito: foto removida no app (inclusive expurgo LGPD)
some do backup na execução seguinte. Trava (saída 6): origem vazia com backup não vazio → não
apaga nada (credencial/bucket errados). **Limite conhecido**: está na mesma conta; não protege
contra comprometimento da conta Cloudflare nem contra apagar fotos por engano e esperar o
espelho rodar. Evolução sugerida: segundo provedor (Backblaze B2/AWS) com `rclone` e versionamento.

### 5.4 Restaurar

**Cenário 1 — erro recente / banco corrompido (usa a camada A, mais rápido).**
1. Render → banco → *Recovery* (PITR ou backup lógico; **confirme no painel** as opções do plano).
   Restaure para um **novo banco** (nunca por cima do atual).
2. No web/worker/crons, aponte `DATABASE_URL` para o novo banco (ou crie o novo no Blueprint e
   redeploy) com **todos pausados** durante a troca (suspenda worker e crons primeiro).
3. `flask config-check --online`, `flask rls status`, smoke test (`lancamento.md`, seção 6).

**Cenário 2 — perda do banco/conta (usa a camada B).**
1. Baixe o último `…dump.age` e o `.sha256` do bucket `controle-backup` (painel R2 ou `aws s3 cp`).
2. Num computador seu (tem a chave privada), com Docker/Postgres 16 local:
   ```bash
   sha256sum -c controle-AAAAMMDDTHHMMSSZ.dump.age.sha256
   AGE_IDENTITY_FILE=chave-backup.txt RESTORE_ADMIN_URL=postgresql://postgres@localhost:5432/postgres \
     scripts/backup_restore_check.sh --dump controle-AAAAMMDDTHHMMSSZ.dump.age --sem-fonte
   ```
   Isso restaura num banco temporário e confere (tabelas, `alembic_version`, planos, RLS). Para
   **subir em produção**: crie o banco novo no Render, e restaure nele com
   `age -d -i chave-backup.txt arquivo.dump.age | pg_restore --no-owner --no-privileges -d "<URL EXTERNA do banco novo>"`
   (libere seu IP no `ipAllowList` do banco só durante a restauração; depois, remova).
3. Aponte os serviços para o banco novo, `flask db upgrade` (se o dump é de uma versão anterior),
   `flask rls status` (o dump traz as políticas e o `FORCE`), smoke test.
4. **LGPD — reaplicar exclusões.** Restaurar um estado antigo **ressuscita** empresas que já
   foram expurgadas e dados que o titular mandou apagar depois do backup. Antes de reabrir o
   acesso: levante os expurgos feitos desde a data do backup (logs do cron `controle-lgpd` —
   linha `Empresa <id> apagada` — e `platform_audit_logs` do banco antigo, se legível) e rode de
   novo o expurgo/solicitações. Registre em `incidentes.md`.
5. Atualize a data do próximo teste.

**Cenário 3 — fotos.** Copie de volta `fotos/atual/` do bucket de backup para o bucket de fotos
(`aws s3 sync s3://controle-backup/fotos/atual/ s3://<fotos>/ --endpoint-url …`) e rode
`flask storage-test`.

### 5.5 Teste de restauração (dono, mensal)

`scripts/backup_restore_check.sh` faz **dump → restore em banco temporário → compara contagens
tabela a tabela** com a fonte, confere `alembic_version` e o resumo do RLS, mede o tempo (insumo
do RTO) e **apaga o banco temporário**. Em desenvolvimento:

```bash
docker compose up -d
SOURCE_DATABASE_URL=postgresql://controle:controle@localhost:5432/controle \
RESTORE_ADMIN_URL=postgresql://controle:controle@localhost:5432/postgres \
  scripts/backup_restore_check.sh
```

Saídas: 0 ok · 1 divergência · 2 configuração · 3 papel sem acesso a todas as linhas · 4 falha
de dump/restore (ou arquivo adulterado: o `.sha256` é conferido antes de descriptografar).
Com fonte viva use `--tolerar-crescimento` (aceita linhas novas depois do dump; nunca aceita
linhas a menos). **Nunca aponte `RESTORE_ADMIN_URL` para o banco de produção.**
Registre cada teste (data, arquivo, tempo, resultado) em `progresso.md` → “Operação”.

### 5.6 Retenção e LGPD

| Dado | Retenção | Coerência com `lgpd.md` |
|---|---|---|
| Dump criptografado (B) | 30 dias (apagado pelo script; lifecycle 35 dias como rede) | “Backups do banco: 30 dias” |
| Backups do Render (A) | janela do plano (**confirme**) | informar a janela real na política |
| Espelho de fotos (C) | segue a origem (apagou → some na próxima execução) | expurgo LGPD propaga em ≤ 24 h |
| Logs de aplicação | 6 meses (provedor de logs, seção 7) | Marco Civil |

Dado apagado por pedido do titular some do banco na hora e dos backups em até 30 dias — é isso
que a política de privacidade deve dizer.

## 6. E-mail transacional (Resend)

O app usa **Resend** (`MAIL_BACKEND=resend`, `RESEND_API_KEY`); não há backend SMTP. Sem a chave
o app cai no modo *console* (nada é entregue) e o `config-check` reprova em produção.

### 6.1 Domínio e DNS

Use um **subdomínio de envio** (ex.: `mail.seudominio.com.br`) para isolar a reputação do domínio
principal, e `MAIL_FROM="Controle de Produção <nao-responda@mail.seudominio.com.br>"`.

1. Resend → *Domains → Add Domain* → `mail.seudominio.com.br` (região: a mais próxima disponível).
2. O Resend mostra os registros **exatos** (confirme no painel; abaixo, o formato):

| Tipo | Nome | Finalidade |
|---|---|---|
| `TXT` | `resend._domainkey.mail` | **DKIM** — chave pública que assina cada mensagem |
| `MX` | `send.mail` | caminho de retorno (*Return-Path*/bounces) |
| `TXT` | `send.mail` | **SPF** do envio: `v=spf1 include:amazonses.com ~all` (o Resend envia via infraestrutura própria; use o valor mostrado) |

3. **DMARC** (`TXT` em `_dmarc.seudominio.com.br`; o Resend não cria este). Comece só
   observando:
   `v=DMARC1; p=none; rua=mailto:dmarc@seudominio.com.br; fo=1; adkim=r; aspf=r`
   Depois de 2–4 semanas sem falhas legítimas nos relatórios: `p=quarantine; pct=25` →
   `p=quarantine` → `p=reject`. O `rua` precisa ser uma caixa que você lê (ou um serviço
   gratuito de relatórios DMARC).
4. Aguarde o status **Verified** no Resend. Se já existir um SPF no domínio raiz para outro
   serviço, **não** crie um segundo `TXT v=spf1` na mesma entrada (só vale um por nome):
   mescle com `include:`.

Conferir de fora:
```bash
dig +short TXT resend._domainkey.mail.seudominio.com.br
dig +short TXT send.mail.seudominio.com.br
dig +short MX  send.mail.seudominio.com.br
dig +short TXT _dmarc.seudominio.com.br
```

### 6.2 Teste de envio

```bash
flask mail-test voce@gmail.com      # no Shell do Render, com as variáveis de produção
```

Mostra o backend, o domínio do remetente, o destino **mascarado** e o tempo; **não imprime a
chave**. Falha → mensagem com as causas comuns (domínio não verificado, chave inválida,
`MAIL_FROM` fora do domínio). Sucesso → abra a mensagem **na caixa de entrada** (não no spam),
*Mostrar original/cabeçalhos* e procure `Authentication-Results`: precisa de `spf=pass`,
`dkim=pass`, `dmarc=pass`. Repita para um Gmail, um Outlook/Hotmail e um e-mail corporativo.
Teste extra de pontuação de spam: enviar o `mail-test` para o endereço único de
https://www.mail-tester.com (nota ≥ 9/10).

Depois do go-live, acompanhe no painel do Resend: taxa de *bounce* (< 2 %) e *complaint*
(< 0,1 %); alta → pausar envio em massa e investigar.

## 7. Monitoramento

### 7.1 Erros (Sentry) — já implementado, validado

`app/logging_config.py`: só liga com `SENTRY_DSN`; `send_default_pii=False`, sem corpo de
requisição, sem variáveis locais; `before_send` remove cookies, `Authorization`, senhas, tokens,
e-mails e IP, e mantém só o id do usuário (testes em `tests/test_fase7_security.py`).
**Validação ponta a ponta** (Etapa H): `flask sentry-test` envia um evento com e-mail, token e IP
falsos; `tests/test_etapa_h_config.py::test_sentry_test_evento_sai_filtrado` prova que nada disso
sai do processo. Em produção, depois de configurar o DSN, rode `flask sentry-test` e abra o
evento no Sentry: `token` = `[filtrado]`, e-mail = `[e-mail]`, usuário só com `id`.
Configurar no projeto: retenção 90 dias (`lgpd.md`), *Data Scrubbing* ligado, *Prevent storing of
IP addresses* ligado, alerta “novo issue” e “issue regrediu” por e-mail, e `SENTRY_TRACES_SAMPLE_RATE=0`
(sem performance por padrão).

### 7.2 Disponibilidade (uptime)

Monitor externo gratuito (UptimeRobot, Better Stack ou similar), intervalo 1–5 min, alerta por
e-mail **e** mensagem (WhatsApp/Telegram) para o dono:

| Monitor | URL | Espera | Observação |
|---|---|---|---|
| Liveness | `https://app.…/saude` | 200 `"status":"ok"` | processo de pé |
| Prontidão | `https://app.…/health` | 200 `"status":"ok"` | banco respondendo (503 = banco fora) |
| Página pública | `https://seudominio.com.br/` | 200 + palavra-chave | TLS e roteamento |
| Login | `https://app.…/entrar` | 200 | rota pública crítica |
| Certificado | mesmos hosts | validade > 14 dias | alerta de expiração |

Página de status (F10-6): a do próprio monitor (Better Stack/UptimeRobot) basta no início.

### 7.3 Worker, filas e crons

- **`flask worker status`**: fila por empresa (pendentes/esgotados).
- **`flask worker status --check`** (Etapa H): imprime `worker_queue pending=… dead=…
  oldest_pending_seconds=…` e **sai com 1** se há evento esgotado ou pendente há mais de 15 min
  (`--max-idade-min`). O cron `controle-monitor` roda isso a cada 10 min: **falhou → o Render
  avisa por e-mail** (confirme em *Account/Workspace → Notifications* que “cron job failed” está
  ligado).
- **Heartbeat do worker**: o laço escreve `worker: ativo (ciclos=N)` a cada 5 min (INFO). Alerta
  de log: ausência dessa linha por > 15 min = worker parado (Render também reinicia o worker que
  morre).
- **Cron com falha** (lgpd, backup, monitor): e-mail do Render.
- **Webhook do Asaas falhando**: Asaas → Integrações → Webhooks → fila de eventos *pausada* ou com
  erros → e-mail do Asaas; no banco, `SELECT status, count(*) FROM webhook_events GROUP BY 1` com
  `failed` > 0. Rodar `flask billing-reconcile` corrige divergências.

### 7.4 Logs (retenção de 6 meses)

O app escreve **uma linha JSON por requisição** (`route` molde, `status`, `duration_ms`,
`request_id`, `user_id`, `company_id`) sem caminho real, query, e-mail ou IP completo. O Render
guarda pouco tempo: configure **Log Streams** (Render → *Workspace → Log Streams*) para um
provedor com retenção ≥ 6 meses (Better Stack, Papertrail, Datadog… **confirme** o custo) —
exigência de `lgpd.md` (“Logs de aplicação: 6 meses”). Alertas de log úteis:
`status>=500` com taxa > 1 % em 5 min; `duration_ms` p95 > 2 s; `"msg":"Resend:"` com HTTP ≥ 400
(e-mail falhando); `photos.orphan_object`; `tarefa .* falhou`.

### 7.5 Checklist de dashboards (conferir semanalmente nos primeiros 30 dias)

| Painel | Olhar | Limite de atenção |
|---|---|---|
| Render → web | CPU, memória, latência, 5xx, reinícios | memória > 80 %, qualquer reinício inesperado |
| Render → worker | memória, reinícios, logs `worker: ativo` | sem heartbeat > 15 min |
| Render → banco | conexões, CPU, disco, I/O, último backup | disco > 70 %, conexões > 80 % do limite |
| Render → Key Value | memória, evictions | evictions constantes |
| Sentry | issues novos, regressões, taxa de erro | qualquer issue novo em rota de pagamento/login |
| Resend | entregas, bounces, complaints | bounce > 2 %, complaint > 0,1 % |
| Cloudflare R2 | armazenamento, operações, erros 4xx/5xx | crescimento anormal |
| Asaas | cobranças do dia, webhooks, chargebacks | webhook pausado |
| Monitor de uptime | disponibilidade 30 dias | < 99,5 % |
| `/interno` | métricas do PRD (empresas, trial→pago) | — |

## 8. Plantão mínimo

Dono = plantão. Sinal → ação: **site fora** (monitor) → Render events + Sentry; se o último
deploy, rollback (seção 2). **Banco fora** (`/health` 503) → status do Render; se perda de dados,
seção 5.4. **E-mail não chega** → `flask mail-test`, painel Resend, DNS. **Cobrança não
atualiza** → webhook Asaas + `flask billing-reconcile`. **Suspeita de vazamento** →
`incidentes.md` (prazo ANPD: 3 dias úteis).
