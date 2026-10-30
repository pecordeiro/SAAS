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
Reestruturação R9 (limpeza): saíram os gráficos SVG antigos que o Painel com ECharts substituiu
(macros de `components/chart.html`, geometria de `services/charts.py`), CSS sem uso, a rota
`/app/etapas/<id>` e funções de serviço sem chamada; o que ficou em dúvida está em
`docs/plano/limpeza-pendente.md`.
ADR-0019 (briefing e ligação): no plano Empresa ou Implantação, o proprietário preenche o briefing de
identidade visual em `/app/identidade-visual` (textos, logo e fotos de produto) e marca a ligação com a
equipe em `/app/identidade-visual/ligacao` (horários de Brasília, reserva atômica). A equipe cria os
horários e decide pedidos de cancelar/remarcar em `/interno/horarios`, sem ler o briefing.
Reestruturação R7–R8 (telas): importar planilha em 3 passos (`/app/importar`: enviar →
escolher colunas com “Isto é…” por coluna, ou escolher projetos quando o arquivo da equipe traz
vários (abas “<Nome> - Acompanhamento/Equipe/Como funciona”) → prévia com erros por linha e
confirmar; a tela de colunas traz ajuda por campo e a unidade do tempo, minutos ou horas, convertida no servidor e mostrada na prévia), menu “Exportar” no projeto (planilha no formato da equipe com fórmulas ou lista
simples) e “Restaurar para uma data” no histórico (prévia antes → depois, confirmar, desfazer).
Reestruturação R6 (opcionais, ADR-0017): o núcleo é acompanhar etapas; responsáveis e progresso
por pessoa, alertas e relatório semanal, aguardando peça, fotos e comentários, checklist de
inspeção, número de série e API viram **módulos opcionais**, desligados por padrão e ligados pelo
proprietário em Configurações › Módulos (`/app/empresa/modulos`). Desligado, o módulo some do menu
e das telas e as rotas dele respondem 404.
Fase 8 (assinaturas e pagamento) entregue: `PaymentProvider` com Asaas e Fake
(`app/services/billing/`), teste grátis de 14 dias sem cartão, assinar com CPF/CNPJ validado e
checkout no Asaas (Pix, boleto ou cartão), webhook idempotente (`POST /webhooks/asaas`),
carência de 7 dias com e-mail e faixa, modo leitura depois, troca de plano com projeção,
faturas, cancelamento até o fim do período, `flask billing-reconcile` e
`flask billing-admin` (ver [`docs/plano/pagamentos.md`](docs/plano/pagamentos.md)).
Planos (ADR-0019): Essencial R$ 249,90 (5 projetos, 5 pessoas), Profissional R$ 497,90
(10 projetos, 25 pessoas), Empresa R$ 997,90 (ilimitado, sem teste grátis) e Implantação sob
orçamento, online ou presencial, com 1 mês de acompanhamento e treinamento (só `flask billing-admin set-plan --company <uuid> --plan implantacao --reason "..."`).
Teste grátis de 14 dias só no Essencial e no Profissional. Em produção `APP_BASE_URL` (https)
é obrigatório: sem ele o app não sobe.
Etapa D (colaboração): autoria de cada lançamento no detalhe e no histórico (inclusive quem
desfez), edição de etapa/atividade com `version` e 409 com o valor atual, responsável por
atividade (supervisor+, só membro ativo da empresa; evento interno `activity.assigned`),
progresso por pessoa (`calc.progresso_por_pessoa`, tela `/app/projetos/<id>/pessoas`) e
arrastar etapas/atividades na edição (`static/js/arrastar.js`, sem biblioteca; Subir/Descer e
“Mover” continuam sem JS). Migration `d4a8c2e6f1b3`.
Etapa F (worker e alertas): processo separado `flask worker run` (ou `--once` no cron) que
consome o outbox com tentativas e backoff e roda tarefas idempotentes empresa a empresa no
contexto RLS (ADR-0010): alertas automáticos (prazo em risco, atraso previsto, etapa parada há
X dias úteis — X por empresa em `/app/empresa` —, peça atrasada) em `/app/alertas` e por e-mail,
e-mail ao responsável quando uma atividade é atribuída, relatório semanal com XLSX,
reconciliação do Asaas e limpeza de tokens. Etapa “aguardando peça” (supervisor+, só sinaliza)
com selo na lista, no detalhe e no painel. Preferências de e-mail em `/conta/perfil`.
Migrations `e2b7f1c3a9d0`, `f3c8a2d4b1e5`, `a5d9e3f7c2b8`. Runbook:
[`docs/plano/worker.md`](docs/plano/worker.md).
Etapa G (qualidade, ADR-0011): fotos e comentários por atividade
(`/app/atividades/<id>/evidencias`; fotos validadas pelo conteúdo, reencodadas sem EXIF/GPS,
servidas só por `/app/fotos/<uuid>` com login; armazenamento local em dev/test e S3/R2 em
produção — `STORAGE_*`), checklist de inspeção por etapa (itens no modelo, assinatura =
usuário + hora do servidor, correção registrada; “exigir checklist” só sinaliza) e número de
série por unidade (`/app/projetos/<id>/unidades`, `/app/unidades/<id>`, busca em
`/app/unidades`; rastreabilidade, o cálculo não muda). Migrations `b6e1f4a2c9d3`,
`c8f2a5d1e7b4`, `d9a3b6e2f8c5`.
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

Fase 7 (segurança e LGPD) entregue: CSP estrita com nonce, HSTS e cabeçalhos
(`app/security.py`), cookies `__Host-`, rate limit em Redis obrigatório em produção, uploads
em memória com proteção a zip bomb/XXE, logs JSON com `request_id` e Sentry opcional com filtro
(`app/logging_config.py`), exportação ZIP e exclusão da empresa com carência de 30 dias em
`/app/privacidade` (proprietário), `flask lgpd-purge`, `flask lgpd-retencao`, acesso de
suporte auditado (`flask suporte ...`), rotação de chaves (`SECRET_KEY_FALLBACKS`,
`MFA_ENCRYPTION_KEY` com MultiFernet + `flask mfa-rotacionar`), `pip-audit` no CI e Dependabot.
Docs: [`seguranca.md`](docs/plano/seguranca.md) (STRIDE), [`lgpd.md`](docs/plano/lgpd.md),
[`incidentes.md`](docs/plano/incidentes.md); textos-rascunho em `docs/legal/`.

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

### Painel e moldura (reestruturação R1–R2)

- Visual da base “Controle de Atividades” (ADR-0015): IBM Plex Sans 400/600 local, paleta do painel
  antigo, cores de status e de série em `tokens.css`, nada acima de 32 px, cards sem sombra.
- Menu: Painel, Preencher etapas, Meta e equipe, Como funciona; depois Projetos e Histórico;
  Configurações no rodapé. Celular: as 4 telas + “Mais”.
- `/app` abre o **Painel da operação** (todos os projetos ativos); `/app/projetos/<id>/painel` é o
  painel de um projeto. Frase-resumo, 5 indicadores, gráficos (tarefas × unidades, situação, quanto cada etapa representa,
  horas e equipe × prazo) e Tabelas 1/2.
- Ícones de linha do Lucide 0.460.0 no sprite `app/templates/components/_icons.html` (ISC, licença em
  `app/static/vendor/lucide-0.460.0/LICENSE`), todos com traço de 2 px.
- Gráficos com ECharts 5.5.1 vendorizado (`app/static/vendor/echarts-5.5.1/`, Apache-2.0), desenhados
  por `app/static/js/painel.js` a partir do JSON que o servidor gera (`app/services/dashboard.py` →
  `calc.py`). Nenhuma conta no navegador.
- `/app/preencher`, `/app/meta-e-equipe` e `/app/como-funciona` ainda redirecionam para as telas
  existentes mais próximas (telas próprias na R3/R5).

### Módulos opcionais (reestruturação R6)

- Catálogo e regra em `app/services/modules.py` (ADR-0017); estado por empresa em `company_modules`
  (migration `f1a7c3e9b2d4`, com RLS). Sem linha = desligado: empresa nova vê só o núcleo.
- Módulos: `atribuicao` (responsáveis e progresso por pessoa), `alertas` (alertas e relatório
  semanal), `aguardando_peca`, `fotos` (fotos e comentários), `checklist`, `unidades` (número de
  série) e `api` (só com `FEATURE_PUBLIC_API`; o plano continua exigindo a feature `api`).
- A recusa é do servidor: `tenancy.tenant_required` chama `modules.guard_endpoint` e devolve 404
  para qualquer rota de módulo desligado (antes do papel); a API faz o mesmo no token. Templates só
  leem `modules` para esconder menu e fragmentos, e mostram o selo “Opcional”
  (`components/optional.html`) no que é de módulo.
- O worker pula alertas e relatório de empresa sem `alertas`; sem `aguardando_peca` a marca é
  ignorada (painel, alertas, relatório); sem `atribuicao` o e-mail de atribuição não sai.
- Só o proprietário liga/desliga; cada mudança vai para `audit_logs` (`module.enabled` /
  `module.disabled`). Desligar não apaga dado. Empresas que já existiam ganharam ligados os módulos
  em que já tinham dados (migration).

### Interface (Fase 2)

- Tokens: `app/static/css/tokens.css` é cópia de `docs/design/tokens.css` (o handoff do
  design, ADR-0008). Mudou a marca? Troque os valores lá e copie; nomes não mudam.
- CSS: `app/static/css/{base,layout,components,pages,utilities}.css` em `@layer`. Só
  `var(--…)`: cor hex, `rgb(`/`hsl(` ou `px` fora de `tokens.css` quebram
  `tests/test_visual.py`.
- Componentes: macros em `app/templates/components/` (`{% from "components/button.html"
  import button %}` etc.). Páginas estendem `base_publica.html` ou `base_app.html`.
- Vitrine: `http://127.0.0.1:5000/estilo` (só com `APP_ENV=development`; 404 nos demais).
- Sem CDN e sem script/estilo inline (CSP `default-src 'self'`; o único `<script>` sem `src` é o bloco
  de dados `application/json` do painel): fontes woff2 (OFL) em
  `app/static/fonts`, HTMX 2.0.4 em `app/static/js/htmx.min.js` (`allowEval:false`),
  melhorias em `app/static/js/app.js`. Tudo funciona sem JS.
- Tema: Sistema/Claro/Escuro no menu (cookie `tema`).
- Capturas de referência: `docs/design/capturas/fase2/` (375/768/1280, claro e escuro).

### Front-end completo (Fase 6)

- Site público: `/`, `/precos` (planos lidos da tabela `plans`), `/termos` e `/privacidade`
  (RASCUNHO para revisão jurídica), `/contato` (e-mail de `CONTACT_EMAIL`, só texto),
  `/sitemap.xml`, `/robots.txt`.
- Área logada: lista com abas/busca/prazo/exportar, detalhe com registro por HTMX
  (`hx-swap-oob`, sem recarregar), conflito 409 com confirmação, atualização a cada 30 s
  (só aba visível), histórico paginado e geral (`/app/historico`), novo projeto com resumo via
  HTMX, editor de modelo com ↑/↓/remover/adicionar etapa, `/app/empresa` (dados, jornada, dias,
  feriados). Tudo funciona sem JavaScript (fallback por formulário). O navegador não calcula
  nada: textos como “+2 (→ 5 de 10)” vêm do servidor.
- Assets minificados com hash: `python scripts/build_assets.py` (gera `app/static/dist/`;
  `--check` confere). Rode depois de mexer em CSS/JS e commite o resultado.
- Testes de navegador (opcionais): `pip install playwright==1.55.0`; `RUN_E2E=1 python -m pytest tests/e2e -q`
  (axe: `E2E_AXE_JS=/caminho/axe.min.js`). Capturas: `python scripts/capturar_telas.py docs/design/capturas/fase6`.

### Identidade oliva em todo o sistema (ADR-0018)

- Os tokens semânticos de `app/static/css/tokens.css` valem a marca oliva (off-white, tinta, oliva escuro; tema
  escuro equivalente) em toda a área logada, no login e nas páginas de erro; DM Sans no texto, Newsreader em
  títulos e números grandes (IBM Plex saiu). Botão principal com raio 8 px, foco de 3 px, menu com item ativo
  oliva suave. O oliva nunca colore dado: barras, rosca, esteira e selos de situação seguem verde/azul/cinza/
  amarelo/vermelho. Animação reduzida à transição curta, realce da linha salva, menus/diálogos, gráfico uma vez
  e spinner. E-mails com a mesma paleta via atributos HTML. Capturas: `python scripts/capturar_telas.py <pasta>`.

### Redesign das telas e auditoria do sistema (2026-10-28)

- Preencher etapas separa **Registrar produção** (padrão, para quem lança peças) de **Configurar etapas** (supervisor+,
  `?modo=configurar`, decidido no servidor). O Painel da operação mostra 4 indicadores, "Precisa de atenção" e a
  lista de projetos, sem gráficos que repetiam a lista; Meta e equipe põe a previsão ao lado do formulário.
- Auditoria do sistema em [`docs/plano/system-audit.md`](docs/plano/system-audit.md) e achados com gravidade em
  [`docs/plano/system-findings.md`](docs/plano/system-findings.md): pedido do HTMX com a sessão encerrada vira 401 +
  `HX-Redirect` (nada de "salvo" falso), Pillow 13.0.0, Painel da operação com número fixo de consultas, mensagens de
  falha ao salvar e trava contra clique duplo.
- Telas, fluxo e decisão de cada gráfico: [`docs/design/redesign-2026-10-28.md`](docs/design/redesign-2026-10-28.md).

### Textos da Teroz (auditoria de copy, 2026-10-29)

- Vocabulário único em [`docs/teroz-terminologia.md`](docs/teroz-terminologia.md) (Teroz, subatividade, peças e
  unidades prontas, meta, situação…) e voz em [`docs/teroz-voice-and-tone.md`](docs/teroz-voice-and-tone.md).
- Inventário de todos os textos (arquivo:linha, antes → depois, status) em
  [`docs/ux-copy-inventory.md`](docs/ux-copy-inventory.md). Endereços, IDs, API e o formato da planilha exportada não
  mudaram; o importador continua reconhecendo os nomes antigos das colunas.

### Site público na identidade oliva (R10, ADR-0016)

- Páginas: `/`, `/precos`, `/como-funciona` (como funciona com a sua planilha), `/termos`, `/privacidade`,
  `/contato`; os planos (preço e limites) vêm sempre da tabela `plans`.
- Visual verde-oliva + off-white só nelas (tokens `--color-brand-*`, escopo `.site--marca` em
  `app/static/css/publico.css`); a área logada segue na ADR-0015. Dado (anel, esteira, etiquetas) usa só cores de status.
- Fontes Newsreader e DM Sans (OFL) em `app/static/fonts/`; animações em `app/static/js/publico.js`
  (respeitam `prefers-reduced-motion`). Depois de mexer em CSS/JS: `python scripts/build_assets.py`.
- Para a página de uma empresa nova declarar a marca, basta `{% set marca = true %}` no template.

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

### Pagamento (Fase 8)

Sem `ASAAS_API_KEY`, development/test usam o `FakeProvider` (em memória). Com a chave, o app
fala com o Asaas em `ASAAS_BASE_URL` (padrão sandbox). Cadastre o webhook do Asaas para
`<site>/webhooks/asaas` com o token de `ASAAS_WEBHOOK_TOKEN`. Comandos:

```bash
flask billing-reconcile                      # corrige divergências com o Asaas (idempotente; 1x/dia)
flask billing-admin extend-trial --company <uuid> --days 7 --reason "motivo"
flask billing-admin discount --company <uuid> --percent 20 --reason "motivo"
```

Telas em `/app/assinatura` (só proprietário). Roteiro do ciclo real no sandbox em
[`docs/plano/pagamentos.md`](docs/plano/pagamentos.md).

### Worker (Etapa F)

```bash
flask worker run                 # laço (Background Worker no Render)
flask worker run --once          # um ciclo de tudo e sai (cron); --task events|alerts|weekly|reconcile|tokens
flask worker status              # eventos pendentes/esgotados por empresa
```

Sem o worker rodando, nada de e-mail de atribuição, alertas ou relatório semanal sai (os
eventos ficam na fila). Detalhes, retentativas e variáveis em
[`docs/plano/worker.md`](docs/plano/worker.md).

### Fotos de evidência (Etapa G)

Em development/test as fotos vão para `instance/uploads/` (fora de `static`, nunca servidas
direto). Em produção o padrão é **fotos desligadas** (`STORAGE_BACKEND` vazio = `none`); para
ligar, crie um bucket **privado** (Cloudflare R2 recomendado; AWS S3/MinIO também servem) e uma
chave com permissão só de Put/Get/DeleteObject nele, e defina `STORAGE_BACKEND=s3`,
`STORAGE_S3_ENDPOINT` (https), `STORAGE_S3_BUCKET`, `STORAGE_S3_REGION` (`auto` no R2),
`STORAGE_S3_ADDRESSING` (`path` no R2, `virtual` na AWS), `STORAGE_S3_ACCESS_KEY_ID` e
`STORAGE_S3_SECRET_ACCESS_KEY`. `STORAGE_BACKEND=local` em produção derruba o boot. Limites:
5 MB por foto, `PHOTOS_MAX_PER_ACTIVITY` (20), `PHOTOS_MAX_PER_COMPANY` (5000),
`PHOTO_UPLOAD_RATE_LIMIT`. O expurgo LGPD apaga os arquivos antes das linhas.

### Produção

`APP_ENV=production` exige `SECRET_KEY`, `DATABASE_URL` e `REDIS_URL` (ou
`RATELIMIT_STORAGE_URI=redis://...`) — o app não sobe sem eles nem com cookie inseguro; para
mandar e-mail, também `APP_BASE_URL`, `RESEND_API_KEY` e `MAIL_FROM`. Atrás do proxy do
Render, `TRUSTED_PROXY_COUNT=1`. Opcionais: `SENTRY_DSN`, `LOG_LEVEL`, `SECRET_KEY_FALLBACKS`.
Não ligue o access log do Gunicorn (ele grava o caminho, que pode ter token): o app já
registra cada requisição em JSON com o molde da rota.

Rotinas agendadas (cron): `flask lgpd-purge --operador cron` e `flask lgpd-retencao
--operador cron` (diárias), `flask suporte expirar` (de hora em hora). O worker
(`flask worker run`, processo separado) já cobre `billing-reconcile` e a limpeza de tokens. Acesso de suporte:
`flask suporte conceder EMAIL --empresa UUID --motivo "..." --horas 4 --autorizado-por "..."`.
Auditoria de dependências: `pip-audit -r requirements-dev.txt`.
Servidor: `gunicorn run:app`. Variáveis em [`.env.example`](.env.example) e em
`docs/plano/arquitetura.md` §10.

### Deploy e lançamento (Etapa H)

Guia completo: [`docs/plano/lancamento.md`](docs/plano/lancamento.md) (checklist go/no-go: o que
já está pronto e o que só o dono faz) e [`docs/plano/operacao.md`](docs/plano/operacao.md)
(runbook de deploy, e-mail SPF/DKIM/DMARC, backup/restauração, monitoramento).

- `Dockerfile` (multi-stage, sem root, assets construídos) + `gunicorn.conf.py`; um build serve
  web, worker e crons. `render.yaml` (produção) e `render.staging.yaml` são **gerados** por
  `python scripts/gen_render_yaml.py` (não edite à mão). Segredos: `sync: false`, só no web.
- Saúde: `GET /saude` (liveness, sem banco; health check do Render) e `GET /health` (prontidão
  com banco; monitor de uptime).
- `flask config-check [--online] [--strict]` lista tudo que falta/está inseguro em produção (exit 1)
  e roda no `preDeployCommand`; `python scripts/config_check.py` faz o mesmo sem subir o app.
- `flask mail-test DESTINO`, `flask storage-test`, `flask sentry-test`, `flask worker status --check`.
- Backup: `scripts/backup_dump.sh` (pg_dump → age → assinatura → R2, 30 dias),
  `scripts/backup_photos.sh`, `scripts/backup_restore_check.sh` (restaura num banco temporário, como
  papel sem privilégios, e confere contagens). Crons de LGPD (`suporte expirar`, `lgpd-retencao`,
  `lgpd-purge`), monitor e backup estão no `render.yaml`.
- `python scripts/smoke_check.py https://seu-host --producao` — smoke test sem login.

## Base de referência

- [`docs/referencia/acompanhamento_montagem_v4.xlsx`](docs/referencia/acompanhamento_montagem_v4.xlsx): planilha cujas regras de cálculo o SaaS reproduz.
- Painel antigo (Flask + Excel/COM, só Windows): `pecordeiro/controle-de-atividades`. Só as regras são reaproveitadas.
