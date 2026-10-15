# Lançamento — checklist go/no-go (Etapa H)

Como usar: leia a Parte A (o que já está pronto), execute a Parte B **na ordem** (cada item diz
**quem**, **como** e **o critério de pronto**), faça o smoke test (Parte C) e só então decida
(Parte E). Rollback na Parte D. Detalhes técnicos: [operacao.md](operacao.md).

Legenda: **[C]** = Claude já entregou e verificou no repositório · **[P]** = só o dono (Pedro) pode
fazer, em painel externo, com conta/cartão/documento dele. Nada em [P] pode ser feito por Claude.

> Regra do roadmap: se faltar **isolamento, segredos, backup ou login em rota privada: NÃO lançar.**

---

## Parte A — O que Claude entregou e verificou ([C])

| # | Entrega | Evidência | Como foi verificado | O que NÃO foi verificado |
|---|---|---|---|---|
| A1 | `/saude` (liveness sem banco) e `/health` (prontidão) | `app/blueprints/public.py`, `tests/test_etapa_h_saude.py` | testes: 200 sem consultar o banco, 200 com banco quebrado, `/health` 503 sem vazar motivo | comportamento atrás do balanceador real |
| A2 | `flask config-check` (+`--online`, `--strict`, `--ignorar`) e `scripts/config_check.py` | `app/configcheck.py`, `tests/test_etapa_h_config.py` (56 casos) | tabela de 30+ configurações inseguras → reprova; nunca imprime valor; `--online` contra PostgreSQL 16 real (papel, migrations, RLS, feriados) | Redis/banco do Render |
| A3 | `flask mail-test`, `storage-test`, `sentry-test`, `worker status --check` | `app/ops_cli.py`, `app/services/worker.py` | testes com Resend simulado (chave nunca vaza), armazenamento local/falho, evento Sentry capturado e **filtrado** (sem e-mail/token/IP) | envio real (Resend), R2 real, Sentry real |
| A4 | `Dockerfile` multi-stage, usuário sem privilégios, assets reconstruídos, `.dockerignore`, `gunicorn.conf.py` (sem log de acesso: o caminho leva token) | arquivos na raiz, `tests/test_etapa_h_render.py` | testes estáticos + etapa de assets reproduzida fora do Docker (saída idêntica à commitada); job `docker` no CI constrói, checa uid≠0 e `/saude` | **`docker build` não foi executado** (sem daemon neste ambiente) — o CI faz |
| A5 | `render.yaml` (produção) e `render.staging.yaml` **gerados** por `scripts/gen_render_yaml.py`: web (`/saude`, pre-deploy `config-check → db upgrade → seed-plans`), worker, crons (LGPD 03:00 BRT, monitor 10 min, backup 04:00 BRT), Key Value, Postgres 16, região `virginia`, segredos `sync: false` só no web | `tests/test_etapa_h_render.py` (parse do YAML, comandos existem no CLI, config do Blueprint passa no `config-check`) | testes; CI confere sincronia | **`render blueprints validate` não rodou** (sem Render CLI); nomes de plano e `autoDeploy` precisam de validação (item P-10) |
| A6 | Backup: `backup_dump.sh` (dump → age → **assinatura** → R2, retenção 30 dias, mínimo 3), `backup_photos.sh` (espelho com trava), `backup_restore_check.sh` | `tests/test_etapa_h_backup.py` (24 casos) | PostgreSQL 16 real: dump → criptografa → assina → restaura **como papel sem privilégios** → contagens iguais; adulteração, hash regravado, chave errada, sem assinatura → recusa; RLS forçado → recusa (saída 3); aws simulado para retenção/espelho | R2 real; RPO/RTO reais (medidos em dados de produção) |
| A7 | `scripts/smoke_check.py` (smoke sem login) | `tests/test_etapa_h_smoke.py` | rodado contra servidor local de verdade | execução contra staging/produção |
| A8 | Runbooks: [operacao.md](operacao.md), ADR-0012, este arquivo, `.env.example`, README | — | revisão cruzada com o código | valores/menus dos painéis de terceiros (marcados “confirme no painel”) |
| A9 | Suíte SQLite verde e testes novos também em PostgreSQL 16 local | ver `progresso.md` → Etapa H | — | a suíte **inteira** em PostgreSQL (o CI faz; item P-11) |
| A10 | Já existentes e reaproveitados: CSP estrita, HSTS, cookies `__Host-`, logs JSON sem PII, Sentry com filtro, LGPD (exportar/expurgar/retenção), RLS ligável, isolamento A/B por rota | `seguranca.md`, `lgpd.md`, `tests/test_isolation.py`, `tests/test_rls.py` | suítes das etapas anteriores | isolamento **em produção** (Parte C) |

Itens que Claude **pode fazer depois, quando você trouxer o insumo**: trocar os textos legais
finais (remover o alerta “Rascunho” de `app/templates/public/_legal.html` e as lacunas
`[razão social]`, `[CNPJ]`…), ajustar `CONTACT_EMAIL`/páginas, escrever ADR do papel de banco
(P-13) e mudar `render.yaml` conforme o resultado, corrigir o que o smoke test acusar.

---

## Parte B — Ordem de execução do dono ([P])

Pré-requisito geral: gerenciador de senhas (1Password/Bitwarden) com 2FA, e-mail próprio do dono
para todas as contas, **2FA ligado em todas** (GitHub, Render, Cloudflare, Resend, Sentry, Asaas,
Registro.br).

### Fase 1 — Prazos longos (comece hoje, em paralelo)

**P-01 · Registrar o domínio (D10)** — [P]
- Como: Registro.br → verificar `controleproducao.com.br` (ou alternativa) → registrar com seu CPF/CNPJ
  → ligar 2FA e renovação automática. Decida o **host canônico**: recomendo `www.seudominio.com.br`
  (o apex redireciona para ele); o cookie de sessão é `__Host-` (por host), então **um só host** serve o app.
- Pronto quando: domínio ativo no painel; host canônico definido por escrito (vira `APP_BASE_URL`).

**P-02 · Contador: nota fiscal e enquadramento (D6)** — [P]
- Como: levar `pagamentos.md` §1–2 e os preços (R$ 249,90 / 497,00 / 997,00). Perguntar: quem emite NFS-e
  de cada mensalidade (manual, ou a automação do Asaas), CNAE/regime, retenções, como tratar estorno e
  plano “Implantação” sob consulta. **Antes da primeira cobrança real.**
- Pronto quando: resposta escrita do contador + processo de emissão definido (quem/quando/onde).

**P-03 · Advogado: Termos e Privacidade (LGPD)** — [P]
- Como: enviar `docs/legal/termos.md` e `privacidade.md` (rascunhos), `lgpd.md` (inventário, operadores,
  retenção), `incidentes.md`. Pontos a pedir: nomear o **encarregado (DPO)** e o e-mail; **transferência
  internacional** (Render/EUA, Resend, Sentry, Cloudflare); janela de **backups** (30 dias + janela do
  Render); contrato de operador (somos operadores das empresas clientes); foro, limitação de
  responsabilidade, carência de 7 dias e modo leitura.
- Depois: me passar o texto final → **[C]** atualiza as páginas e remove o aviso de rascunho.
- Pronto quando: texto aprovado por escrito, publicado sem `[colchetes]` e sem “Rascunho para revisão
  jurídica” (o `smoke_check.py --producao` confere isso).

**P-04 · Criar as contas de produção** — [P]
- Render (workspace do negócio, plano pago), Resend, Cloudflare (DNS + R2), Sentry, **Asaas produção**
  (cadastro com documentos/KYC: pode levar dias — peça já), monitor de uptime (UptimeRobot/Better Stack),
  provedor de logs (retenção ≥ 6 meses), uma **caixa de e-mail do domínio** para `CONTACT_EMAIL` e
  `dmarc@` (Google Workspace, Zoho ou do próprio Registro.br).
- Pronto quando: todas logam com 2FA; Asaas produção aprovado para cobrar; caixa `contato@` recebe e envia.

### Fase 2 — Chaves, DNS e serviços de apoio

**P-05 · Gerar e guardar os segredos** — [P]
- Como (no seu computador; **valores distintos para staging e produção**):
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"        # SECRET_KEY
  python -c "import secrets; print(secrets.token_hex(32))"        # MFA_ENCRYPTION_KEY (outra!)
  python -c "import secrets; print(secrets.token_urlsafe(32))"    # ASAAS_WEBHOOK_TOKEN
  age-keygen -o chave-backup.txt                                   # criptografia do backup
  ssh-keygen -t ed25519 -N "" -C controle-backup -f assina-backup  # assinatura do backup
  ```
  Guarde **tudo** no gerenciador de senhas e uma cópia offline da `chave-backup.txt` (privada) e da
  `assina-backup.pub`. A `assina-backup` (privada) só vai para o Render (`BACKUP_SIGN_KEY`).
- Pronto quando: cada segredo existe no cofre; `chave-backup.txt` tem cópia offline; nada foi colado em chat/e-mail/commit.

**P-06 · Cloudflare: DNS e R2** — [P]
- Como: colocar o domínio na Cloudflare (trocar nameservers no Registro.br) **ou** manter o DNS no
  Registro.br. R2: criar buckets **privados** `controle-fotos`, `controle-fotos-staging` e
  `controle-backup`. Tokens R2: (1) app, *Object Read & Write* só no bucket de fotos de cada ambiente;
  (2) backup, *Object Read & Write* em `controle-backup` + *Read* em `controle-fotos`. Regra de ciclo
  de vida: expirar `db/` do `controle-backup` em 35 dias.
- Pronto quando: `flask storage-test` (P-08/P-12) dá “Armazenamento OK”; tokens com o menor escopo possível.

**P-07 · Resend + SPF/DKIM/DMARC** — [P]
- Como: `operacao.md` §6.1 (adicionar domínio de envio, criar os registros no DNS, aguardar *Verified*,
  criar o DMARC com `p=none`). Criar a `RESEND_API_KEY` com permissão de envio no domínio.
- Pronto quando: domínio *Verified*; `dig` mostra os registros; **`flask mail-test seuemail@gmail.com`**
  chega na caixa de entrada com `spf=pass dkim=pass dmarc=pass` (e também em Outlook e e-mail corporativo);
  mail-tester ≥ 9/10.

### Fase 3 — Staging (ensaio geral, com Asaas sandbox)

**P-08 · Subir o staging no Render** — [P] (+ [C] se algo falhar)
- Como: criar o branch `staging` no GitHub; Render → *New → Blueprint* → repositório → arquivo
  `render.staging.yaml`. Preencher as variáveis `sync: false` (valores de **staging**: Asaas sandbox
  `$aact_hmlg_…`, bucket de staging, `APP_BASE_URL=https://staging.seudominio.com.br`). Adicionar o
  domínio `staging.…` no serviço web e o CNAME no DNS.
- Pronto quando: deploy verde (o `preDeployCommand` passou: `config-check`, migrations, planos);
  `https://staging…/saude` = 200; `python scripts/smoke_check.py https://staging…` = 0 falhas.

**P-09 · Homologação do Asaas (sandbox) — `pagamentos.md` §5** — [P]
- Como: seguir os 15 passos do §5 no **staging** (webhook `https://staging…/webhooks/asaas` com o
  `ASAAS_WEBHOOK_TOKEN` de staging; confirmar que o header é `asaas-access-token`). Registrar data,
  prints e observações na seção “Execução” de `pagamentos.md`. Rodar `flask billing-reconcile` 2×.
- Pronto quando: todos os 15 passos com resultado esperado; reconciliação 2ª vez = 0 corrigidas;
  qualquer divergência vira ajuste de código por **[C]**.

**P-10 · Validar o Blueprint** — [P]
- Como: instalar o Render CLI e rodar `render blueprints validate render.staging.yaml` e `render.yaml`.
  Confirmar nomes de plano (`starter`, `basic-256mb`, `basic-1gb`) e custo mensal no painel antes de aprovar.
  Se o CLI recusar algum campo (ex.: `autoDeploy`), me mande a mensagem: **[C]** ajusta o gerador.
- Pronto quando: os dois arquivos validam sem erro e o custo foi aprovado por você.

**P-11 · CI verde e suíte em PostgreSQL** — [P] (abrir o PR/push)
- Como: dar `git push` do branch `claude/etapa-h-deploy` e abrir o PR; o GitHub Actions roda `pip-audit`, a
  suíte inteira em PostgreSQL 16 e SQLite, as migrations e o **build da imagem Docker**.
- Pronto quando: todos os jobs verdes (audit, test, docker). Falha → me mande o log.

**P-12 · Testes de e-mail, fotos e Sentry no staging** — [P]
- Como: no Shell do serviço web do staging: `flask mail-test …`, `flask storage-test`, `flask sentry-test`
  (conferir no Sentry: `token` = `[filtrado]`, e-mail = `[e-mail]`, usuário só com `id`). Subir uma foto
  pela tela de uma atividade e abri-la.
- Pronto quando: os três comandos passam e a foto aparece (`/app/fotos/<uuid>` só logado).

**P-13 · Conferência visual** — [P] ou **[C]** com navegador
- Como: abrir staging em 375, 768 e 1280 px, tema claro e escuro: início, preços, cadastro, painel,
  projeto, evidências, checklist, unidades, assinatura. (Pendência herdada das etapas F e G.)
- Pronto quando: sem quebra de layout/contraste; ajustes pedidos viram tarefas.

### Fase 4 — Produção

**P-14 · Descobrir o papel do banco e decidir o RLS** — [P] + **[C]** (ADR)
- Como: no Shell do web de produção, a consulta de `operacao.md` §4. Se `rolsuper`/`rolbypassrls` = `t`,
  **pare** e me chame: é preciso um papel comum para o app (ADR-0012 §6) **antes** do go-live.
- Pronto quando: papel é comum (`f`/`f`) **ou** a solução com dois papéis está implementada e testada.

**P-15 · Subir produção e ligar o domínio** — [P]
- Como: Render → *New → Blueprint* → `render.yaml` (branch `main`) com os segredos de **produção**
  (Asaas `$aact_prod_…`, `ASAAS_BASE_URL` já fixo em `api.asaas.com`, bucket de produção). Domínio
  customizado no web: host canônico (www) + apex (redireciona); registros no DNS; aguardar o certificado.
  `CONTACT_EMAIL`, `MAIL_FROM`, `STAFF_NOTIFY_EMAIL` reais.
- Pronto quando: deploy verde; `https://www…/saude` = 200; `http://` e apex redirecionam para o canônico.

**P-16 · Calendário de feriados e RLS** — [P] (Shell do web de produção)
- Como (**nesta ordem**; o seed não funciona depois do RLS forçado):
  ```bash
  flask seed-holidays --de 2026 --ate 2035
  RLS_ENABLED=1 flask rls enable
  flask rls status                      # todas as tabelas: ligado=sim forçado=sim
  flask config-check --online --strict  # tem que APROVAR sem aviso
  ```
- Pronto quando: `rls status` sem “não”, `config-check --online --strict` = APROVADO, e o isolamento A/B de
  produção (P-19) passa com o RLS ligado. Reverter em emergência: `flask rls disable`.

**P-17 · Primeira conta de equipe** — [P]
- Como: criar sua conta no site (cadastro normal, confirmar e-mail) e **ativar o MFA** em `/conta`. No Shell:
  `flask staff conceder voce@dominio --motivo "Dono da plataforma" --autorizado-por "Pedro"`;
  `flask staff listar` deve mostrar `mfa=sim`.
- Pronto quando: `/interno` abre para você e dá 404 para qualquer outra conta.

**P-18 · Webhook do Asaas (produção) e teste de cobrança real** — [P]
- Como: Asaas produção → Integrações → Webhooks: URL `https://www…/webhooks/asaas`, token de produção,
  API v3, eventos de cobrança e assinatura. Depois o critério do roadmap: **cobrança real de valor baixo,
  paga e estornada** (use `flask billing-admin discount --help` para reduzir o valor de uma empresa de
  teste ao mínimo aceito pelo Asaas — confirme o mínimo no painel; pague por Pix; confira a assinatura
  “Ativa”; estorne no painel do Asaas; confira o modo leitura; cancele).
- Pronto quando: pagamento → “Ativa”; estorno → leitura; nenhuma cobrança real remanescente;
  decisão D6 (nota) cumprida para este valor.

**P-19 · Isolamento A/B em produção com duas empresas de teste** — [P]
- Como: roteiro da Parte C, passo C9–C10.
- Pronto quando: todos os acessos cruzados dão 404 e nada de B aparece para A.

**P-20 · Backup real e teste de restauração** — [P]
- Como: preencher as variáveis `BACKUP_*` do cron `controle-backup` (inclui `BACKUP_SIGN_KEY`); *Trigger Run*;
  conferir em `controle-backup` o `.dump.age`, `.sha256`, `.sig` e `fotos/atual/`. Num computador seu,
  baixar os três arquivos e rodar o `backup_restore_check.sh` do `operacao.md` §5.4/5.5 com a **chave
  pública de assinatura** e a **chave age**. Anotar o tempo (insumo do RTO ≤ 4 h) e confirmar RPO ≤ 24 h.
  Verificar no painel do Render a janela de backup/PITR do plano e **anotar** (vai para a política).
- Pronto quando: `RESULTADO: OK`; data/arquivo/tempo registrados em `progresso.md`; teste repetido todo mês.

**P-21 · Monitoramento e alertas** — [P]
- Como: `operacao.md` §7: monitores de uptime (`/saude`, `/health`, home, login, certificado) com alerta
  no seu celular; regras de alerta no Sentry; notificação de cron com falha no Render; *log stream*
  com retenção ≥ 6 meses; `flask sentry-test` em produção.
- Pronto quando: você **derrubou de propósito** (ex.: suspendeu o web por 2 min no staging) e o alerta chegou no celular.

**P-22 · Onboarding do piloto e suporte** — [P]
- Como: convidar o 1º cliente piloto; combinar canal de suporte (`CONTACT_EMAIL`); página de status
  pública do monitor; avisar o piloto do que é teste. (F10-6)
- Pronto quando: piloto consegue cadastrar, criar modelo, projeto e registrar peças sem ajuda.

---

## Parte C — Smoke test pós-deploy (passo a passo)

Rode em **staging** e depois em **produção**, após cada deploy relevante. Tempo: ~25 min.

**Automático (2 min).** `python scripts/smoke_check.py https://www.seudominio.com.br --producao --outro-host https://seudominio.com.br`
→ precisa terminar com “0 falha(s)”. Cobre saúde, páginas públicas, cabeçalhos, cookies, rotas privadas
fechadas, 404 de `/interno`, SEO, redirecionamentos, certificado e textos legais finais.

**Manual (navegador anônimo; 2 empresas de teste: A e B, e-mails seus `a+teste@…`, `b+teste@…`):**

| Passo | Ação | Resultado esperado |
|---|---|---|
| C1 | Abrir `/` , `/precos` | preços R$ 249,90 / 497,00 / 997,00; cadeado HTTPS; sem erro no console |
| C2 | Cadastrar a empresa A (`/cadastro`) | e-mail de confirmação **chega** (Resend) em < 1 min |
| C3 | Confirmar e-mail, entrar (`/entrar`) | painel vazio; faixa “Teste grátis · faltam 14 dias” |
| C4 | Criar modelo de etapas e um projeto (qtd 10, prazo) | prazo em dias úteis calculado; feriado nacional respeitado |
| C5 | Registrar peças numa atividade; desfazer (supervisor) | resumo, % e histórico atualizam; sem 500 |
| C6 | Anexar uma foto; abrir `/app/fotos/<uuid>` | imagem aparece; em janela anônima a mesma URL leva ao login |
| C7 | Convidar um operador (e-mail); aceitar em outra janela | convite chega; operador não vê Assinatura/Equipe |
| C8 | Exportar XLSX do projeto; `Privacidade e dados → exportar` | arquivos baixam; ZIP LGPD abre |
| C9 | **Isolamento A/B**: cadastrar empresa B em outra janela anônima; criar projeto B. Com a sessão de A, abrir a URL do projeto B, `/app/atividades/<id de B>/…`, `/app/fotos/<foto de B>`, `/app/unidades/<id de B>` | **404** em todos (nunca 403/200); nada de B na lista de A |
| C10 | Com a sessão de B, repetir com ids de A; testar também `/interno` | 404 em todos |
| C11 | Assinatura (A, owner) → escolher plano → abrir fatura Asaas | fatura abre no Asaas; webhook marca “Ativa” depois de pagar (produção: só no teste de cobrança P-18) |
| C12 | Esqueci a senha (A) | e-mail de redefinição chega; link funciona uma vez |
| C13 | `flask worker status --check` (Shell) e Sentry | `dead=0`; nenhum erro novo no Sentry |
| C14 | Logs do web (Render) | linhas JSON `request` sem e-mail/token no `route`; nenhum 500 |
| C15 | Apagar as empresas de teste A e B (`Excluir a empresa`) e rodar `flask lgpd-purge --dry-run` depois da carência (ou `lgpd-purge` em staging) | expurgo OK, fotos removidas do bucket |

Falhou qualquer passo C9/C10 → **NO-GO imediato** (isolamento).

---

## Parte D — Plano de rollback

| Situação | Ação | Tempo |
|---|---|---|
| Deploy novo quebrou o site | Render → web → deploy anterior → *Rollback*; idem worker e crons | 2–5 min |
| `preDeployCommand` falhou | nada a fazer: a versão antiga segue no ar; corrija (`config-check` diz o quê) e refaça o deploy | — |
| Migration problemática já aplicada | código anterior segue funcionando (migrations retrocompatíveis); `flask db downgrade` só se reversível e sem dado novo; senão restaurar (`operacao.md` §5.4) | 15 min–4 h |
| RLS bloqueou o app (telas vazias/500) | `flask rls disable` (as políticas ficam); investigar com `flask rls status`; religar depois | 1 min |
| Config errada | corrigir a variável no Render e redeploy; `flask config-check --online` | 5 min |
| Banco corrompido/perdido | `operacao.md` §5.4 cenário 1 (Render) ou 2 (dump assinado); **reaplicar exclusões LGPD** | RTO ≤ 4 h |
| Cobrança incorreta | `flask billing-reconcile`; se erro de cobrança em massa, suspender webhooks no Asaas e chamar **[C]** | — |
| Suspeita de vazamento | `incidentes.md` (ANPD em 3 dias úteis); revogar sessões; rotacionar segredos | imediato |
| Lançamento precisa voltar atrás | suspender o web (Render → *Suspend*) mostra a página de indisponibilidade do host; DNS mantido; comunicar clientes | 1 min |

---

## Parte E — Go / No-Go final

**Eliminatórios (qualquer um em aberto = NÃO lançar):**
- [ ] P-19 e C9/C10: isolamento A/B em produção com RLS ligado (P-16).
- [ ] P-05/P-15: segredos fortes, só em variável de ambiente; `config-check --online --strict` APROVADO.
- [ ] P-20: backup diário rodando **e** restauração testada e assinada (RPO ≤ 24 h, RTO ≤ 4 h).
- [ ] Rotas privadas exigem login (smoke automático sem falha).
- [ ] P-03: Termos e Privacidade revisados por advogado e publicados.
- [ ] P-18: cobrança real de valor baixo paga e estornada; P-02: nota fiscal definida.

**Demais critérios do roadmap:**
- [ ] P-11: CI verde (suíte em PostgreSQL 16, migrations, imagem Docker).
- [ ] P-09: homologação Asaas sandbox completa.
- [ ] P-07: e-mail com SPF/DKIM/DMARC `pass`.
- [ ] P-17: conta de equipe com MFA; `/interno` fechado a terceiros.
- [ ] P-21: alertas testados; P-13: telas conferidas; P-22: piloto onboarded.
- [ ] Smoke test (Parte C) verde em staging **e** produção.

### Registro de execução (preencha)

| Item | Data | Quem | Resultado / link / observação |
|---|---|---|---|
| P-01 | | | |
| … | | | |
