# Progresso

Cada fase preenche um bloco abaixo ao terminar. A próxima só começa quando todos os
critérios de pronto da anterior estiverem marcados.

## Formato do bloco

```
### Fase N — Nome
- Status: não iniciada | em andamento | concluída
- Datas: início AAAA-MM-DD · fim AAAA-MM-DD
- Entregas: lista curta do que foi feito
- Critérios de pronto: [x] / [ ] um por linha, copiados do roadmap
- Testes: resultado de `python -m pytest -q` (n passaram, n falharam, cobertura se aplicável)
- /security-review: sem achados | achados abertos (listar)
- Telas conferidas (375/768/1280, claro/escuro): sim | não | n/a
- Commit: hash e mensagem
- ADRs criados: lista
- Pendências e dívidas: lista
```

## Fases

### Fase 0 — Esqueleto do projeto
- Status: concluída
- Datas: início 2026-10-13 · fim 2026-10-13
- Entregas:
  - `requirements.txt` / `requirements-dev.txt` fixados; `.gitignore`; `.env.example`; `run.py`.
  - `app/__init__.py` (create_app), `app/config.py` (por ambiente, lido do env na criação do
    app; `SECRET_KEY` e `DATABASE_URL` obrigatórios fora de development/test),
    `app/extensions.py`; blueprints `public` (`/`, `/health`), `auth` (`/cadastro`,
    `/entrar`, `/sair`) e `app` (`/app/...`); cabeçalhos de segurança (CSP `default-src 'self'`).
  - Modelos (UUID, `company_id NOT NULL`, índices começando por `company_id`): companies,
    users, memberships, projects, stages, activities, progress_entries (append-only, guarda
    no ORM), holidays. Migration `e972bfba83c7` revisada; `flask db upgrade`/`downgrade` e
    `flask db check` conferidos em SQLite e PostgreSQL 16.
  - `app/tenancy.py`: `load_company`, `tenant_required(min_role)`, `scoped`, `get_or_404`.
  - `app/services/calc.py` puro (pesos, %, progresso por tarefas com fallback, unidades,
    status, tempos, dias úteis, progresso geral, `prazo_em_data`, resumos em dataclasses).
  - `app/services/projects.py` (criar projeto, incluir etapa/atividade, registrar peças com
    UPDATE condicional por `version` → 409 em conflito; histórico).
  - Cadastro de empresa + login/logout (Argon2id, CSRF em todo POST, Flask-Limiter
    `memory://`, `next` só interno, sessão versionada por `session_version`).
  - Telas provisórias sem CSS: início, login, cadastro, projetos, novo projeto, detalhe
    (indicadores + registrar peças), histórico, erros 400/403/404/429/500.
  - `flask seed-demo` (2 empresas, 1 projeto de 10 equipamentos com 6 etapas genéricas cada).
  - `.github/workflows/ci.yml` (Python 3.12: `flask db upgrade` + `flask db check` + pytest com cobertura).
- Critérios de pronto:
  - [x] `python -m pytest -q` verde localmente (CI configurado; ainda não executado no GitHub).
  - [x] `test_calc.py` com ≥ 15 casos conferidos à mão (26 testes, incluindo quantidade zero,
        soma de tempos zero, atividade 100%, peças acima da meta) **e** teste de paridade com
        `acompanhamento_montagem_v4.xlsx` (24 etapas + resumo + aba Equipe, tolerância 1e-9).
  - [x] `calc.py` não importa `flask` nem `sqlalchemy` (teste por AST).
  - [x] Usuário da empresa A recebe 404 em GET/POST de projeto, etapa e atividade da empresa B.
  - [x] Operador recebe 403 ao criar projeto; POST sem CSRF recebe 400.
  - [x] `flask db upgrade` em banco vazio cria tudo; `/health` responde 200 (servidor real).
- Testes: `65 passed` (SQLite em memória, ~21 s); mesmos 64 da suíte principal também
  verdes com `TEST_DATABASE_URL` em PostgreSQL 16 local. Cobertura 90% de `app/`.
- /security-review: sem achados (confiança ≥ 8). Abaixo do limiar, viram dívida: logout não incrementa `session_version` (Fase 5); busca por id não exclui arquivados (Fase 4).
- Telas conferidas (375/768/1280, claro/escuro): n/a (telas provisórias sem design; migram na Fase 2).
- Commit: 8f29a49 feat: fase 0 — esqueleto Flask, tenancy, calc com paridade da planilha
- ADRs criados: nenhum (ADR-0007 já cobria a fase).
- Pendências e dívidas:
  - ~~Feriados nacionais compartilhados~~ — resolvido na Fase 3 (linha global com
    `company_id` NULL).
  - ~~`citext` para e-mail~~ — resolvido na Fase 3 (índice único em `lower(email)`).
  - Rate limit em memória e sem bloqueio progressivo por conta (Fase 5/7, Redis).
  - CSP sem nonce (não há script ainda); RLS pronto na Fase 3 (desligado por padrão).
  - Cadastro informa “não foi possível cadastrar com este e-mail” em e-mail repetido:
    não revela dados da outra conta, mas permite enumerar e-mails; resolver com confirmação
    por e-mail na Fase 5.
  - Novo projeto usa 6 blocos fixos de etapa com atividades em texto (“Nome; minutos”);
    a tela definitiva (HTMX) vem na Fase 2/6.
  - Desfazer registro de peças (D13, supervisor+) não existe ainda (Fase 4).

### Fase 1 — Identidade visual e telas
- Status: concluída (aguarda aprovação da direção de marca pelo usuário)
- Entregas: docs/design/ (marca “Prumo”, logo/favicon/OG SVG, tokens.css, contraste, design system, telas) e ADR-0008.
- Commit: c873665 docs(design): fase 1 — marca Prumo, tokens e design system
- Pendências: aprovar direção de marca; demonstrar “≤ 2 toques” na tela real (Fase 2).

### Fase 2 — Base visual no código
- Status: concluída (lista de diferenças com o handoff abaixo, todas justificadas)
- Datas: início 2026-10-13 · fim 2026-10-13
- Entregas:
  - `app/static/css/tokens.css` = cópia byte a byte de `docs/design/tokens.css` (claro padrão;
    escuro por `prefers-color-scheme` e por `data-theme` no `<html>`).
  - CSS próprio em camadas `@layer base, layout, components, utilities` (`base.css`,
    `layout.css`, `components.css`, `pages.css`, `utilities.css`; `estilo.css` só na vitrine),
    sem Bootstrap, só `var(--…)`; breakpoints em `em` (30/48/64em).
  - Fontes woff2 servidas pelo site (`app/static/fonts`, subset latin do pacote
    `@fontsource` 5.1.0, com `OFL-*.txt`): IBM Plex Sans 400/600/700 (algarismos já de
    largura fixa) e Barlow Semi Condensed 600/700 (tem `tnum`; conferido com fontTools, então
    `font-variant-numeric: tabular-nums` funciona nos números grandes).
  - HTMX 2.0.4 local (`app/static/js/htmx.min.js`, de `npm pack htmx.org@2.0.4`, licença
    junto), configurado por `<meta name="htmx-config">`: `allowEval:false`,
    `allowScriptTags:false`, `includeIndicatorStyles:false`, `selfRequestsOnly:true`,
    `attributesToSettle` sem `style`. Nenhum CDN; CSP continua `default-src 'self'` sem nonce
    (não há script nem estilo inline; `app/static/js/app.js` faz as melhorias progressivas).
  - Macros em `app/templates/components/`: `button`, `field`/`checkbox`/`form_errors`,
    `stepper`/`piece_stepper`, `data_table`, `kpi`, `progress` (`<progress>` nativo, sem
    estilo inline), `status_badge`/`badge`, `alert`, `toast`/`toast_region`,
    `confirm_dialog`, `empty_state`, `pagination`, `bar_chart` (SVG no servidor, horizontal e
    vertical, com tabela equivalente), `sidebar_nav`/`bottom_nav`/`theme_switch`, `icon`
    (sprite SVG próprio).
  - Layouts `_base.html` → `base_publica.html` (cabeçalho, ☰ em folha no celular, rodapé) e
    `base_app.html` (menu lateral ≥ 768 px com empresa e papel; barra superior + navegação
    inferior no celular; folha “Mais” com tema e Sair). Tema Sistema/Claro/Escuro persistido em
    cookie `tema` (lido no servidor → sem piscar); com JS aplica na hora, sem JS faz
    `POST /tema` (CSRF, `next` só interno).
  - Telas migradas: início, entrar, cadastro, projetos, detalhe, histórico (agrupado por dia
    + gráfico de peças por dia), novo projeto, erros 400/403/404/429/500 (logado mantém o
    menu). Mensagens do WTForms em português (`Meta.locales`, `WTF_I18N_ENABLED=False`).
  - **Registro em 2 toques no celular**: toque na atividade abre a folha inferior por âncora
    (`#registrar-<id>`, funciona sem JS) já com +1 → toque em “Registrar +1 (→ 8 de 10)”.
    Com JS o formulário vai por HTMX (`hx-boost`, sem recarregar a página), a folha fecha, a
    linha pisca e o toast confirma; erro (400/409) reabre a folha com o alerta. Conferido com
    Playwright a 375 px com e sem JS (`docs/design/capturas/fase2/fluxo-*.png`). No desktop
    (≥ 1024 px) o stepper fica na linha da atividade.
  - `/estilo` (só development; 404 em qualquer outro ambiente): tokens (cores, tipos,
    espaços, raios, sombras) e todos os componentes com variantes e estados.
  - Logo e favicon SVG, `favicon-32.png`, `apple-touch-icon.png` (180) e `og-image.png`
    (1200×630) gerados dos SVGs de `docs/design` com Chromium headless e as fontes locais.
- Critérios de pronto:
  - [x] Teste que varre `app/templates/` (e o CSS fora de `tokens.css`) e falha com cor hex,
        `rgb(`/`hsl(` ou valor em `px` (`tests/test_visual.py`).
  - [x] Nenhuma referência a CDN (regex `https?://` em `<link>`/`<script>`), nem script/estilo
        inline nos templates.
  - [x] `/estilo` responde 404 em production, staging e test; 200 em development.
  - [x] Capturas de cada tela em 375/768/1280, claro e escuro (`docs/design/capturas/fase2/`,
        82 PNGs, 3,6 MB); diferenças com o handoff listadas abaixo (corrigidas ou justificadas).
  - [x] Testes antigos verdes.
- Testes: `90 passed` (65 antigos + 25 de `tests/test_visual.py`).
- Contraste: script de `docs/design/contraste.md` rodado de novo (todos os pares passam) +
  pares novos usados nas telas: sucesso/aviso/perigo sobre `--color-bg` e `--color-surface-2`,
  texto secundário sobre `--color-primary-subtle` (pior: 5,07:1 claro, 5,88:1 escuro).
- /security-review: revisão manual — sem `|safe`/`Markup`; `/tema` exige CSRF, valida o valor
  e só redireciona para caminho interno; cookie de tema inválido é ignorado; nenhuma rota
  nova com `<uuid>`.
- Telas conferidas (375/768/1280, claro/escuro): sim (Playwright; sem rolagem horizontal).
- Commit: ver `git log` (feat: fase 2 — base visual no código)
- ADRs criados: nenhum.
- Diferenças com `docs/design/telas.md` (justificadas):
  - Menu: só Projetos (+ Histórico do projeto aberto). Modelos, Usuários, Empresa,
    Assinatura e o histórico geral não têm rota ainda (Fases 4–6); entram nos itens de
    `base_app.html` quando existirem. Faixa de teste grátis/carência fica para a Fase 5.
  - Tablet (768 px): com o menu lateral, o conteúdo tem ~460 px; por isso tabelas viram cards
    e o detalhe usa a folha de registro até 1023 px (o handoff só desenha 375 e 1280). O menu
    lateral não recolhe para ícones.
  - Lista de projetos: sem filtros/abas/busca e sem Exportar; “Atraso previsto” sem o número
    de dias (falta função de dias úteis entre datas em `calc.py` — Fase 4).
  - Detalhe: sem subtítulo de produto (não há campo), sem “prazo em N dias úteis/folga”
    (mesma função de calc), sem Exportar/Editar/Arquivar e sem atualização a cada 30 s;
    indicadores atualizam trocando o corpo da página via `hx-boost` (não `hx-swap-oob`);
    sem coluna “#” (os nomes de etapa do seed já trazem o número). Formulários “Nova
    atividade”/“Incluir etapa” da Fase 0 mantidos (supervisor+).
  - Histórico: sem filtros, exportação, “6 → 7 de 10” e desfazer (Fase 4); mostra os 200
    mais recentes sem paginação.
  - Novo projeto: sem seletor de modelo, resumo calculado por HTMX e dias da semana; etapas
    ainda digitadas em 6 blocos “Nome; minutos” (Fase 4/6). Quantidade usa o stepper.
  - Entrar/cadastro: sem “Manter conectado”, “Esqueci a senha”, MFA, aceite de termos e tela
    “Confirme seu e-mail” (Fase 5); cadastro mantém “Repita a senha”.
  - Site público: “Preços” aponta para `/#precos` (não há `/precos`); rodapé sem Termos,
    Privacidade e contato (páginas ainda não existem). 500 sem código de erro para suporte.
- Pendências e dívidas:
  - `favicon.ico` não gerado (navegadores usam o SVG e o PNG 32).
  - `og:image` usa URL absoluta do host da requisição; em produção conferir `SERVER_NAME`/proxy.
  - Só o último flash vira toast (design: 1 por vez).
  - Campos de data mostram o formato do navegador (`input type=date`).
  - Atualizar HTMX/fontes é manual (versões fixadas acima).

### Fase 3 — Banco de dados
- Status: concluída
- Datas: início 2026-10-13 · fim 2026-10-13
- Entregas:
  - `docker-compose.yml` (PostgreSQL 16 com bancos `controle` e `controle_test`, Redis 7).
  - Modelos novos: `templates`, `template_versions`, `template_stages`,
    `template_activities` (projeto guarda `template_version_id` e copia as etapas —
    `services/templates.py`); `invitations`, `password_resets`, `email_confirmations`,
    `mfa_recovery_codes`; `plans`, `subscriptions` (1 por empresa), `payments`
    (`company_id` redundante para isolamento/RLS), `webhook_events`; `audit_logs`
    (append-only), `domain_events` (outbox, índice parcial dos não publicados),
    `api_clients`, `api_tokens`. Campos novos: `users.totp_secret_enc`, `users.mfa_enabled`;
    `companies.mfa_required`, `companies.deletion_requested_at`.
  - CHECK (papéis, status de projeto/assinatura/cobrança/webhook, provedor, quantidades,
    preços, posições, `version ≥ 1`, horas/dia, máscara de dias) e UNIQUE onde a regra existe
    (`token_hash`, `provider_payment_id`, `external_event_id`, `plans.code`, número de versão
    por modelo, nome de modelo por empresa, assinatura por empresa, feriado nacional por dia).
  - E-mail case-insensitive: índice único em `lower(email)` (SQLite e PostgreSQL) em vez de
    `citext` — mesma garantia nos dois bancos, sem extensão.
  - Feriados nacionais: `holidays.company_id` NULL = nacional (índice único parcial por dia),
    `services/holidays.py` (fixos + Sexta-feira da Paixão pela Páscoa) e `flask seed-holidays`
    idempotente; o prazo usa nacionais + os da empresa.
  - RLS (ADR-0003 aceito): migration `b3e9f1a2c4d5` com políticas em 17 tabelas;
    `app/rls.py` (hook `after_begin` com `set_config(..., true)` = `SET LOCAL` por transação;
    `flask rls enable|disable|status`); `tenancy.py` passa empresa/usuário já validados.
    Pronto e desligado por padrão.
  - Planos: migration de dados `a7c2d4e8f901` (Essencial R$ 149 / 3 projetos / 5 usuários;
    Profissional R$ 349 / 15 / 25; Empresa R$ 799 / ilimitado / 100 com `mfa_required` e
    `api`), ids estáveis (uuid5 do código) e `flask seed-plans` idempotente.
  - `flask seed-demo`: modelo de etapas versionado, 2 projetos por empresa criados a partir
    dele (snapshot), histórico espalhado em dias, assinatura `trialing` de 14 dias no
    Profissional, feriado próprio da empresa + nacionais.
  - Testes no PostgreSQL pelas migrations (schema recriado, TRUNCATE entre testes; o nome do
    banco precisa conter “test”); SQLite continua como atalho.
  - CI: serviço `postgres:16`; ciclo `upgrade → check → downgrade base → upgrade → check` no
    PostgreSQL e no SQLite; pytest com `TEST_DATABASE_URL` (com cobertura) e no SQLite.
  - ER e §5 de `arquitetura.md` atualizados; README e `.env.example`.
- Critérios de pronto:
  - [x] `flask db upgrade` do zero → `flask db downgrade base` → `flask db upgrade` sem erro em
        PostgreSQL 16 (local, 16.15) e no SQLite; `flask db check` sem drift nos dois.
        No CI está configurado (ainda não executado no GitHub).
  - [x] Teste confirma que toda tabela com dado de cliente tem `company_id NOT NULL` e índice
        começando por `company_id` (`tests/test_schema.py`, exceções explícitas e justificadas).
  - [x] Com RLS ligado e papel `NOSUPERUSER NOBYPASSRLS` criado no teste, consulta crua sem
        `app.company_id` retorna 0 linhas nas 17 tabelas; com o id de A, só linhas de A.
  - [x] Testes, inclusive isolamento A/B, verdes em PostgreSQL — e os casos A/B também com o
        app inteiro rodando como o papel comum e `RLS_ENABLED=1`.
  - [x] `UNIQUE` em `payments.provider_payment_id` e `webhook_events.external_event_id` testados.
- Testes: PostgreSQL 16 (`TEST_DATABASE_URL`): `125 passed` (~78 s), cobertura 95% de `app/`;
  SQLite: `88 passed, 37 skipped` (RLS e migração no PG só rodam no PostgreSQL).
- /security-review: revisão manual das mudanças (tokens só como hash; contexto RLS só com
  vínculo validado e por bind parameter; SQL dinâmico só com nomes de tabela constantes;
  nenhum segredo em log); sem achados abertos.
- Telas conferidas (375/768/1280, claro/escuro): n/a (fase sem tela).
- Commit: “feat: fase 3 — banco de dados” (hash no histórico do branch).
- ADRs criados: nenhum novo; ADR-0003 passou a “aceito” com a decisão final.
- Pendências e dívidas:
  - RLS desligado por padrão. Antes de ligar em produção, os fluxos entre empresas precisam
    de papel de plataforma (`BYPASSRLS`) ou função `SECURITY DEFINER`: webhook/reconciliação
    do Asaas (Fase 8), aceitar convite e autenticar token de API (busca por `token_hash`
    antes de saber a empresa; Fases 5/9), worker do outbox, LGPD e `flask seed-holidays`
    (gravar nacionais com RLS forçado). Verificar se o Render permite papel com `BYPASSRLS`.
  - O modo batch do SQLite não recria índice de expressão: migration futura que altere
    `users` em batch precisa tirar e recriar `uq_users_email_lower` fora do batch.
  - Sem FK composta `(company_id, id)` entre pai e filho (a garantia de mesma empresa é do
    serviço + RLS); `project_members` fica para quando a tela de equipe existir.
  - Tabelas de convite/reset/confirmação/MFA/API ainda sem serviço (Fases 5 e 9).

### Fase 4 — Backend e regras de negócio
- Status: concluída (telas mínimas; capturas 375/768/1280 pendentes)
- Datas: início 2026-10-13 · fim 2026-10-13
- Entregas:
  - `services/templates.py`: criar/editar modelo (etapas diferentes → nova versão imutável e
    atual; nome repetido recusado sem diferenciar maiúsculas), arquivar, listar, uso por
    projetos, projeto a partir de modelo (snapshot da versão atual), `compare` (etapa/atividade
    entra ou sai, tempo muda, ordem muda — pareando por nome) e `apply_current_version` (só com
    a versão confirmada; o que sai do modelo é ARQUIVADO, nunca apagado; auditoria com v1 → v2).
  - `services/projects.py`: editar dados (quantidade não fica abaixo das peças registradas),
    renomear, ↑/↓ (normaliza posições, pula arquivados), reordenar etapas, arquivar etapa,
    atividade e projeto, duplicar (progresso zero), desfazer registro (D13) por lançamento
    compensatório: `progress_entries.reverts_entry_id` (UNIQUE, CHECK delta < 0; migration
    `c4f8a1d2e3b6`), status `done`/`active` sincronizado, “atraso previsto em N dias úteis”.
  - `tenancy.get_or_404` agora devolve 404 para arquivado, inclusive por herança (atividade de
    etapa arquivada, etapa de projeto arquivado) — pendência da Fase 0. Histórico e exportação
    usam `include_archived=True`.
  - `calc.dias_uteis_entre(inicio, fim, feriados, dias_semana)` (intervalo (inicio, fim]) com
    5 testes conferidos à mão.
  - `services/entitlements.py`: plano efetivo (assinatura ou teste implícito de `TRIAL_DAYS`
    contado da criação da empresa no `DEFAULT_TRIAL_PLAN`), `max_projects` (ativos = não
    arquivados e não concluídos), `max_users` (vínculos ativos + convites pendentes),
    `has_feature`/`require_feature`, `usage`. Modo leitura: `tenant_required` barra todo método
    não seguro com `ReadOnlyError` (402) — `allow_read_only=True` libera (ex.: pagar). Regra
    ligável por `READ_ONLY_ENFORCED`. Erros viram página 402 amigável com “Ver planos”; aviso
    “Assinatura em modo leitura — registros pausados” no layout.
  - `services/events.py::emit` (`project.created`, `activity.progress_updated`,
    `stage.completed`, `project.completed` na virada) e `services/audit.py::record` (ator, IP,
    objeto, detalhes; constantes de ação para a Fase 5: papel, convite, plano, exclusão).
  - `services/importer.py`: CSV (`;`/`,`/TAB, UTF-8 ou cp1252, vírgula decimal, dd/mm/aaaa),
    XLSX exportado pelo site e a planilha de referência (layout pelos títulos da coluna A + aba
    Equipe). Erros por linha (“Linha 7, tempo ideal: número inválido”); limites de linhas,
    etapas e atividades; tipo por extensão + conteúdo; zip bomb barrado antes de abrir; fórmula
    nunca avaliada. Pré-visualização → dados assinados (itsdangerous, empresa + usuário, 1 h)
    → confirmação revalida e grava tudo num commit. Peças importadas viram 1 registro por
    atividade no histórico.
  - `services/exporter.py`: CSV (Excel BR, BOM) e XLSX com as colunas da tela + situação
    (inclui arquivados); `= + - @ TAB CR` neutralizados com apóstrofo (a importação desfaz).
  - Blueprints novos (sem inflar `app.py`): `modelos` (lista, novo, editar → versão, versões,
    arquivar), `edicao` (editar projeto e estrutura, duplicar, arquivar, comparar/aplicar
    modelo, desfazer registro; handler 402 e aviso de modo leitura), `dados` (exportar CSV/XLSX,
    importar com pré-visualização, modelo CSV). `app.py`: novo projeto com seletor de modelo
    (id resolvido por `get_or_404` na empresa da sessão), histórico com Desfazer/“desfeito” e
    “Alterações do projeto” (auditoria), atraso em dias úteis. Menu “Modelos” (supervisor+).
  - `MAX_CONTENT_LENGTH` = limite de importação + 256 KB (413 antes de ler o corpo).
- Critérios de pronto:
  - [x] Cobertura `pytest-cov` ≥ 90% em `app/services/` (98% no SQLite e no PostgreSQL).
  - [x] Rota de criação chamada direto recebe 402 ao estourar `max_projects` (novo, duplicar,
        importar); `max_users` testado no serviço (`check_can_add_user`, para a Fase 5 chamar
        em convidar/aceitar); empresa sem assinatura ativa recebe 402 em escrita e lê normal.
  - [x] Exportar → importar devolve os mesmos dados (CSV e XLSX, incluindo arquivados, datas,
        equipe, peças e o resumo do calc).
  - [x] CSV com 1 linha inválida não grava nada e devolve linha, coluna e motivo.
  - [x] Célula exportada começando com `= + - @` (e TAB/CR) sai neutralizada (CSV e XLSX).
  - [x] Cada mudança relevante gera exatamente 1 `domain_events` na mesma transação (teste com
        rollback).
  - [x] Editar modelo não altera projeto existente até a confirmação.
  - [x] Isolamento A/B para cada rota nova (20 casos em `tests/test_isolation.py`, B intacto
        conferido por snapshot) + modelo/versão de B no novo projeto → 404 e nada gravado +
        prévia de importação assinada para outra empresa recusada.
- Testes: SQLite `236 passed, 37 skipped (~2 min); cobertura de app/services 98%`; PostgreSQL 16 (`TEST_DATABASE_URL`) `273 passed (~4 min); cobertura de app/services 98%`.
  `flask db upgrade`/`downgrade` da migration nova e `flask db check` sem drift no SQLite e no
  PostgreSQL; `test_migrations` (ida e volta) verde nos dois.
- /security-review: revisão manual — ids do formulário (modelo) sempre resolvidos na empresa
  da sessão; toda rota nova com `tenant_required` no papel certo e POST com CSRF; upload
  limitado e conferido por conteúdo; payload da prévia assinado e amarrado a empresa/usuário;
  `Content-Disposition` só ASCII; sem `|safe`. Sem achados abertos.
- Telas conferidas (375/768/1280, claro/escuro): não (só macros/tokens existentes;
  `test_visual` verde). Fica para a Fase 6 junto com o editor HTMX.
- Commit: “feat: fase 4 — backend e regras de negócio” (hash no histórico do branch).
- ADRs criados: nenhum. Decisões registradas aqui: teste implícito sem assinatura (o cadastro
  ainda não cria assinatura); projetos ativos = não arquivados e não concluídos; desfazer por
  `reverts_entry_id`; importação cria PROJETO (não modelo).
- Pendências e dívidas:
  - Fase 5: chamar `entitlements.check_can_add_user` ao convidar/aceitar e `audit.record` em
    papel/convite; criar assinatura `trialing` no cadastro (aí o teste implícito vira só
    fallback).
  - Migration `c4f8a1d2e3b6` sai de `a7c2d4e8f901`: se a Fase 5 criar migration em paralelo,
    ajustar `down_revision` (ou `flask db merge`) no merge.
  - Editor de modelo é de blocos “Nome; minutos” (sem ↑/↓ por etapa) e a edição do projeto usa
    formulários pequenos sem HTMX; resumo calculado no novo projeto, filtros/paginação do
    histórico e histórico geral (`/app/historico`) ficam para a Fase 6.
  - Importar CSV como MODELO (tela de modelos) não existe; importação cria projeto.
  - Desarquivar projeto não existe (precisará checar `max_projects`).
  - `audit.client_ip` usa `request.remote_addr`: em produção atrás de proxy configurar ProxyFix.
  - Werkzeug guarda upload > 500 KB em arquivo temporário anônimo durante a requisição (o
    serviço lê em memória e não grava nada).

### Fase 5 — Login, convites e contas
- Status: concluída (telas não conferidas por captura; ver pendências)
- Datas: início 2026-10-13 · fim 2026-10-13
- Entregas:
  - `app/services/email.py`: `EmailSender` com `ConsoleEmailSender` (memória para testes;
    `.eml` em `instance/emails/` no development; loga só assunto e domínio) e
    `ResendEmailSender` (`requests`, timeout `MAIL_TIMEOUT_SECONDS`, loga só status).
    Links por `APP_BASE_URL` (obrigatório fora de dev/test — evita envenenar link pelo
    header Host). Templates `emails/*.txt|.html` com a marca, sem CSS (regra de tokens).
  - `app/services/tokens.py`: 32 bytes `token_urlsafe` no link, SHA-256 no banco, uso único,
    expiração (confirmação 24 h, reset 1 h, convite 7 dias). Links abrem página (GET não
    altera nada) e a ação é POST com CSRF; páginas de token com `Referrer-Policy: no-referrer`.
  - Confirmação de e-mail no cadastro + reenviar; sem confirmar, acesso por 7 dias desde o
    cadastro e depois só `/conta/confirmar-email` (guarda `register_guards` após `load_company`).
  - Cadastro sem enumeração (resolve a pendência da Fase 0): e-mail novo ou existente →
    mesmo 303 para “Confirme seu e-mail”; o dono da conta existente recebe aviso; o hash
    Argon2 é calculado nos dois caminhos. O cadastro não loga mais automaticamente.
  - Esqueci a senha: resposta e status iguais para e-mail existente e inexistente; trocar a
    senha incrementa `session_version`, consome todos os resets pendentes e zera o bloqueio.
  - Convites (`/app/usuarios`): owner convida qualquer papel, supervisor só
    supervisor/operador (e só mexe nesses convites); reenviar (token e prazo novos),
    revogar; reconvidar o mesmo e-mail substitui o pendente; vagas = vínculos ativos +
    convites pendentes contra o plano via `entitlements.check_can_add_user` (ao convidar,
    reenviar convite vencido, reativar e ao aceitar) → HTTP 402. Em modo leitura convidar,
    reenviar e reativar dão 402; revogar, mudar papel, desativar e exigir MFA continuam
    (`allow_read_only`); aceitar convite de empresa em modo leitura também dá 402.
    Aceite cria conta (e-mail já confirmado) ou vincula a existente (logada com o mesmo
    e-mail); e-mail diferente é recusado. Vínculo desativado só é reativado por convite
    criado por proprietário ativo (supervisor recebe erro ao convidar).
  - Cadastro cria assinatura `trialing` de `TRIAL_DAYS` no `DEFAULT_TRIAL_PLAN` (Fase 4).
  - Membros: mudar papel, desativar/reativar (owner). Último owner ativo não pode ser
    rebaixado nem desativado (`FOR UPDATE` nos owners no PostgreSQL). Desativado perde a
    empresa na requisição seguinte; sem outro vínculo ativo, `session_version` sobe.
  - Perfil (`/conta/perfil`): nome; e-mail com reconfirmação no novo endereço (pede senha;
    aviso ao endereço antigo; endereço já usado → mesma resposta, sem enumerar); senha
    (pede a atual; derruba as outras sessões e mantém a atual).
  - Sessões: `/sair` limpa só a sessão atual (decisão: logout NÃO incrementa
    `session_version`); “Sair de todos os dispositivos” incrementa. Como a sessão do Flask
    é cookie assinado, uma cópia roubada do cookie continua válida até expirar (12 h) se o
    usuário só clicar em “Sair” — por isso o botão “Sair de todos” e o reset derrubam tudo.
  - MFA TOTP (`pyotp==2.9.0`): segredo cifrado com Fernet (chave HKDF-SHA256 de
    `MFA_ENCRYPTION_KEY` ou `SECRET_KEY`); segredo pendente só cifrado na sessão; QR em SVG
    gerado no servidor (`segno==1.6.6`, rota `/conta/mfa/qr.svg`, `no-store`); 10 códigos
    de recuperação (SHA-256, uso único); código TOTP não reutilizável
    (`users.totp_last_step`); etapa `/entrar/mfa` com validade de 5 min. “Exigir MFA dos
    proprietários” (plano Empresa) em `/app/usuarios`; owner sem MFA é levado a ativar.
  - Bloqueio progressivo (`app/services/lockout.py`, tabela `login_throttles`, chaves só
    em SHA-256): 5 falhas por conta / 20 por IP → 1, 5, 15, 60 min; e-mail inexistente se
    comporta igual; código MFA errado conta; além do Flask-Limiter (novos limites para
    reset, MFA, convite e reenvio). Conta bloqueada: nunca verifica a senha. IP bloqueado:
    não verifica credenciais (barra password spraying), EXCETO para conta que já entrou
    neste navegador — cookie de dispositivo confiável (`app/services/trusted_device.py`:
    assinado, HttpOnly, Secure, SameSite=Lax, 90 dias, só hashes do user_id), para um
    atacante atrás do mesmo NAT não trancar quem já usa o sistema. IP real por `ProxyFix`
    só com `TRUSTED_PROXY_COUNT` > 0 (padrão 0 ignora X-Forwarded-For), antes do bloqueio
    e do Flask-Limiter.
  - E-mail por backend de rede (Resend) sai em thread de fundo e erros de entrega viram só
    log: o tempo e a resposta de “esqueci a senha”/cadastro não dependem de a conta existir.
  - Pre-account takeover: MFA e troca de e-mail só com e-mail confirmado; reset de senha numa
    conta nunca confirmada apaga MFA e códigos de recuperação e marca o e-mail confirmado.
  - Troca de empresa (`/conta/empresas`): só para vínculo ativo; senão 404.
  - Auditoria por `app/services/audit.py` (`record` + constantes novas
    `INVITATION_RESENT/ACCEPTED`, `MEMBER_DEACTIVATED/REACTIVATED`, `MFA_REQUIREMENT_CHANGED`),
    sem token nos detalhes.
  - Migration `4d8a644d753b` (reversível, depois de `c4f8a1d2e3b6` da Fase 4 — cadeia linear): `login_throttles`, `users.totp_last_step`,
    `users.last_login_at` (ADD COLUMN sem batch; downgrade no SQLite tira e recria
    `uq_users_email_lower`) e a política RLS `invitations_by_token`.
  - RLS: reset/confirmação usam só tabelas globais (sem RLS). O convite é lido antes de
    saber a empresa pela política `invitations_by_token` (SELECT onde `token_hash =
    app.token_hash`; o app faz `SET LOCAL` do hash do token apresentado — ter o token é a
    autorização; não autoriza gravar); depois o vínculo é gravado com a empresa do convite
    no contexto. Testado com RLS forçado e papel comum.
- Critérios de pronto:
  - [x] Testes de cada fluxo com token válido, expirado, reutilizado e de outra empresa/
        usuário (confirmação, reset, convite; `tests/test_accounts.py`).
  - [x] Pedido de reset devolve a mesma resposta e mesmo status para e-mail existente e
        inexistente (HTML comparado sem o CSRF).
  - [x] Usuário desativado é deslogado na requisição seguinte.
  - [x] Último proprietário não pode ser removido nem rebaixado.
  - [x] Busca no banco (todas as tabelas) e nos logs (caplog DEBUG) não encontra token em
        texto puro; o hash está no banco.
  - [x] Após N tentativas erradas, login bloqueado por conta e por IP.
  - [x] Isolamento A/B para cada rota nova (`ROUTES_CONTAS` no fim de
        `tests/test_isolation.py`; o teste de cobertura de `<uuid:>` inclui essas rotas).
  - [x] `flask db upgrade`/`check`/`downgrade` sem drift em PostgreSQL 16 e SQLite.
- Testes (já integrados com a Fase 4): SQLite `294 passed, 39 skipped`; PostgreSQL 16
  (`TEST_DATABASE_URL`) `333 passed`. `tests/test_rls.py` agora cria o papel de teste com o
  nome do banco no sufixo (papel é global no cluster; duas suítes em paralelo colidiam).
- /security-review: revisão manual (tokens só hash; GET sem efeito; CSRF em todo POST;
  `next` só interno; sem `|safe`/`Markup` — QR servido como imagem; segredos fora do log).
  Sem achado aberto acima do limiar; riscos aceitos listados abaixo.
- Telas conferidas (375/768/1280, claro/escuro): não (só macros e classes existentes;
  `tests/test_visual.py` verde). Conferir com Playwright na Fase 6.
- Commit: “feat: fase 5 — login, convites e contas” (hash no histórico do branch).
- ADRs criados: nenhum.
- Pendências e dívidas:
  - Produção atrás do proxy do Render: definir `TRUSTED_PROXY_COUNT=1`.
  - Bloqueio por conta permite a terceiros atrasar o login de uma conta conhecida (risco
    aceito; mitigado pelo teto de 60 min e pelo reset de senha que zera o bloqueio).
  - E-mail em thread de fundo se perde se o processo cair antes de enviar; trocar pelo
    outbox com worker (Fase 8).
  - Cadastro sem enumeração na tela, mas cadastrar com a senha X e tentar entrar com X ainda
    distingue e-mail novo de existente (custo alto, sujeito a bloqueio) — risco aceito.
  - E-mails sem CSS (regra de tokens nos templates); estilizar com inliner a partir dos tokens.
  - Sessão em cookie assinado: logout não revoga cópias do cookie (ver acima); sessões no
    servidor (Redis) na Fase 7. “Último acesso” é o último login, não a última requisição.
  - Rotação de `MFA_ENCRYPTION_KEY` exige reativar o MFA (sem MultiFernet ainda).
  - Telas desta fase não foram capturadas em 375/768/1280 (Playwright na Fase 6).

### Fase 9 — API de publicação (reservada)
- Status: concluída no escopo mínimo (atrás de `FEATURE_PUBLIC_API`, desligada por padrão)
- Datas: início 2026-10-13 · fim 2026-10-13
- Entregas:
  - `docs/api/openapi.yaml` (OpenAPI 3.1, validado com `openapi-spec-validator==0.9.0` em
    `requirements-dev.txt`): `GET /projects`, `GET /projects/{id}`, `GET /projects/{id}/summary`,
    `GET /projects/{id}/events`, `POST /activities/{id}/progress` (`If-Match` = versão da
    atividade); cursor opaco, erros `application/problem+json` (RFC 9457, extensão `code`),
    datas ISO 8601 UTC, `bearerAuth`, escopos `read:projects` e `write:progress`.
  - `docs/api/webhooks.md`: desenho (HMAC-SHA256 + timestamp, retentativas com backoff,
    bloqueio de SSRF). Não implementado.
  - `app/services/api_tokens.py`: token `cp_` + 43 caracteres; no banco só SHA-256 e prefixo;
    escopos, expiração, revogação (token e integração), `last_used_at`.
  - `app/blueprints/api_v1.py`: `/api/v1` (registrado só com a flag; isento de CSRF; sessão de
    navegador NÃO autentica) e tela `/app/integracoes/api` (owner; token mostrado uma vez com
    `Cache-Control: no-store`; revogar). Ordem das recusas: 401 → 403 plano sem `api` → 403
    escopo → 404. Rate limit por token (hash do token como chave) e teto por IP. Toda chamada
    de token conhecido vai para `audit_logs` (`api.request`, sem o token). `GET /projects` e
    `GET /projects/{id}/summary` (saída de `calc.py`) implementados; os outros três contratos
    respondem 501 problem+json (testes `xfail(strict=True)` com o comportamento futuro).
  - Menu “API” só para proprietário e só com a flag. Arquivos compartilhados tocados:
    `app/__init__.py` (registro condicional), `app/config.py` (limites), `base_app.html` (menu).
- Critérios de pronto:
  - [x] Flag desligada: `/api/v1/*` → 404 e tela/menu invisíveis (teste).
  - [x] Flag ligada: token de A não lê B (404), sem escopo → 403, revogado → 401, expirado → 401,
        sem token → 401, plano sem feature `api` → 403 (testes).
  - [x] Token nunca em texto puro no banco (varredura de `api_tokens`, `api_clients`, `audit_logs`)
        nem nos logs (`caplog`).
  - [x] `openapi.yaml` válido e rotas do blueprint = paths do contrato (teste bate método + path).
  - [x] Caso A/B no fim de `tests/test_isolation.py` (revogar token de B → 404, B intacto).
- Telas conferidas (375/768/1280, claro/escuro): não (só macros/tokens existentes; `test_visual` verde).
- Pendências e dívidas:
  - **RLS**: `tokens.find_by_raw` consulta `api_tokens` por hash ANTES de saber a empresa; com
    `RLS_ENABLED` + `flask rls enable` isso volta 0 linhas. Decidir na ativação: papel de plataforma
    (BYPASSRLS) só para essa consulta ou função `SECURITY DEFINER` estreita (ADR-0003).
  - Stubs 501: detalhe do projeto, eventos (cursor sobre `domain_events`) e registrar progresso
    (`If-Match` → `register_progress`, 412/422/428, 402 em modo leitura, evento + auditoria).
  - Método errado em rota existente da API responde 404 (catch-all), não 405.
  - Rate limit em memória (`memory://`): em produção usar Redis (`RATELIMIT_STORAGE_URI`).
  - Atrás de proxy, `request.remote_addr` (teto por IP e auditoria) exige ProxyFix.
  - Tela: sem rotação de token nem edição de escopos (revoga e cria outro); fase 6 confere as
    capturas responsivas.

### Fase 8 — Assinaturas e pagamento (Asaas)
- Status: concluída (ciclo real no sandbox pendente — depende da chave do usuário)
- Datas: início 2026-10-14 · fim 2026-10-14
- Entregas:
  - `app/services/billing/`: `provider.py` (interface `PaymentProvider`: create_customer,
    update_customer, create_subscription, change_plan, cancel, get_subscription,
    list_payments), `asaas.py` (requests com timeout, `access_token`, `ASAAS_BASE_URL` padrão
    sandbox, `billingType=UNDEFINED`, log sem chave/payload), `fake.py` (determinístico, ids
    `*_fake_0001`, helpers de teste), `service.py` (regras), `documents.py` (CPF/CNPJ com
    dígito verificador), `notify.py` (e-mail de atraso via `app.services.email` da Fase 5), `cli.py`.
  - Estado recalculado das cobranças (`recompute`): pago cobre até o mesmo dia do mês seguinte;
    vencida → `past_due` + `grace_until` (vencimento + 7 dias) + e-mail; depois `expired`
    (modo leitura, nada apagado); cancelada vale até `current_period_end`; estorno/chargeback
    tira a cobertura. Evento que faz a cobrança regredir → consulta o provedor.
  - `POST /webhooks/asaas` (`app/blueprints/webhooks.py`): sem CSRF, rate limit,
    `hmac.compare_digest` do `asaas-access-token` (401), `webhook_events` UNIQUE commitado antes
    de processar (duplicado → 200 sem efeito), falha → `status=failed` + `error` e 200.
  - Troca de plano sem “upgrade grátis”: `subscriptions.pending_plan_id/pending_plan_at`;
    upgrade vale após pagar a fatura no valor novo, downgrade no fim do período pago (recusado
    se o uso não couber, ao pedir e ao aplicar — aí mantém plano/preço, audita e avisa por
    e-mail), troca bloqueada em `past_due`. Assinar: todas as chamadas ao provedor antes de mudar o estado
    local; em falha, rollback e só o `provider_customer_id` criado é gravado à parte.
  - Telas `/app/assinatura` (owner; `allow_read_only`): assinatura atual com uso × limites e
    fatura em aberto, planos, troca com projeção, dados de cobrança (→ redireciona 303 para a
    `invoiceUrl`, só https e host em `BILLING_CHECKOUT_HOSTS`), faturas, cancelar com modal.
    Faixa de teste/atraso/cancelamento no topo do `/app` (`app/assinatura_faixa.html`) e item
    “Assinatura” no menu (owner).
  - `flask billing-reconcile` (idempotente) e `flask billing-admin extend-trial|discount
    --company --reason` (motivo obrigatório em `audit_logs`).
  - Migration `d8b2e6f4a1c7` (de `4d8a644d753b`, cadeia linear): `payments.invoice_url`,
    `subscriptions.discount_percent` (CHECK 0–90), `pending_plan_id`/`pending_plan_at` e política RLS
    `subscriptions_provider_lookup` (SELECT só da linha cujo `provider_subscription_id` =
    `app.billing_lookup`), para o webhook achar a assinatura antes de saber a empresa.
  - `docs/plano/pagamentos.md`: fontes consultadas, mapeamento, regras e roteiro do sandbox.
- Critérios de pronto:
  - [x] Testes com FakeProvider: aprovado, recusado, vencido, pago com atraso, cancelado,
        reembolso, webhook com token inválido (401), duplicado (200 sem efeito), fora de ordem.
  - [x] CPF/CNPJ inválido recusado no formulário e no serviço.
  - [x] Troca de plano muda limites na requisição seguinte (teste) — ajustado pela revisão de
        segurança: upgrade muda na requisição seguinte ao pagamento confirmado da fatura no
        valor novo; downgrade no fim do período pago (testes dos dois e do bloqueio em atraso).
  - [ ] Ciclo real no sandbox, do teste grátis ao cancelamento, documentado com prints —
        roteiro em `pagamentos.md` §5; a rede do ambiente bloqueia `*.asaas.com`.
- Testes: SQLite `410 passed, 41 skipped, 3 xfailed`; PostgreSQL 16 (`TEST_DATABASE_URL`, RLS incluso) `451 passed, 3 xfailed` (após a correção do downgrade).
  `flask db upgrade`/`downgrade 4d8a644d753b`/`upgrade` + `flask db check` sem drift no SQLite;
  `test_migrations` (ida e volta + compare_metadata) verde no SQLite e no PostgreSQL.
- /security-review: revisão manual — token do webhook em tempo constante e sem token
  configurado = 401; idempotência por UNIQUE antes de processar; payload e chave fora de log e
  banco; CPF/CNPJ só no provedor (no banco/auditoria só o tipo); redirecionamento externo só
  para host de checkout conhecido; `invoice_url` só https; rotas de cobrança só owner (403
  para supervisor/operador), POST com CSRF; empresa só da sessão; RLS da busca do webhook é
  só SELECT e exige o id do provedor. Sem achados abertos.
- Telas conferidas (375/768/1280, claro/escuro): não (sem navegador no ambiente; só macros e
  tokens existentes, `test_visual` verde).
- Commit: “feat: fase 8 — assinaturas e pagamento (Asaas)”.
- ADRs criados: nenhum (segue ADR-0004). Decisões registradas em `pagamentos.md`: webhook
  responde 200 mesmo com falha de processamento (não travar a fila do Asaas; reconciliação
  corrige); 1ª cobrança vence no fim do teste grátis; sem cobrança proporcional na troca;
  política RLS de busca por id do provedor.
- Pendências e dívidas:
  - Ciclo real no sandbox (roteiro em `pagamentos.md` §5) e confirmar header
    `asaas-access-token`, `billingType=UNDEFINED` em assinatura e `invoiceUrl`.
  - O cadastro da Fase 5 cria a assinatura `trialing` com `provider="fake"`; ao assinar, o
    provedor real é gravado (`billing.ensure_subscription` é só rede de segurança).
  - Upgrade sem fatura em aberto (o Asaas gera a próxima ~40 dias antes) fica pendente até a
    próxima fatura ser gerada e paga; cobrança proporcional avulsa ficou para depois.
  - Agendar `flask billing-reconcile` diário no worker (Fase 10).
  - Telas conferidas em 375/768/1280 claro/escuro.


### Fase 6 — Front-end completo do site
- Status: concluída
- Datas: início 2026-10-14 · fim 2026-10-14
- Entregas:
  - Site público (início com planos de `plans`, `/precos` com tabela e FAQ, `/termos` e `/privacidade` marcados
    RASCUNHO, `/contato`, `sitemap.xml`, `robots.txt`, canonical/Open Graph, rodapé com links); área logada com
    `noindex`.
  - Lista de projetos: abas (ativos/concluídos/todos com contagem), busca (nome/produto), prazo (atraso, 7 dias, sem
    prazo), paginação, exportar CSV da lista (supervisor+). Campo opcional **produto** (migration `f6a1b2c3d4e5`,
    só ADD COLUMN; parte de c90a35f e precisa ser reencadeada no merge).
  - Detalhe: produto, prazo em N dias úteis, folga/atraso (`calc.dias_uteis_entre`), menu Ações (exportar, editar,
    arquivar), gráficos SVG (progresso e horas por etapa). Registro via HTMX com `hx-swap="none"` + `hx-swap-oob`
    (atividade, resumo da etapa, indicadores, selos, lateral, gráficos, toast); 409 mostra o valor atual e pede
    “Confirmar e somar”; `/atualizar` a cada 30 s só com aba visível (`data-refresh-url` em `app.js`, sem inline).
  - Histórico paginado (25/pág.) com filtros (atividade, pessoa; projeto no geral), “6 → 7 de 10” (soma acumulada),
    gráfico por dia; `/app/historico` geral.
  - Novo projeto: cartões de modelo, produto, resumo calculado via HTMX (`/app/projetos/novo/resumo`,
    `services.projects.plan_summary` usando só `calc.py`). Editor de modelo: ↑/↓/remover/adicionar etapa
    (`/app/modelos/linhas`, `/<id>/linhas`) com fallback sem JS. `/app/empresa` (proprietário): nome, CNPJ validado,
    jornada, dias de trabalho, feriados da empresa (auditados).
  - Regra “front é só painel”: o rótulo “+N (→ X de Y)” vem do servidor (`/app/atividades/<id>/previa`); `app.js` não
    calcula nem decide limites (min/max só como dica).
  - Assets: `scripts/build_assets.py` (rcssmin/rjsmin fixados) → `static/dist/*.<hash>` + manifesto, cache de 1 ano
    para `dist/` e fontes, fallback para os fontes sem build; teste `--check`.
  - A11y: `aria-label` nos campos de quantidade, sem `role` indevido no formulário de registro, ordem de títulos em
    `/precos`; toasts em região `role=status aria-live`.
- Critérios de pronto:
  - [x] Playwright (`tests/e2e`, marker `e2e`): cadastro → confirmar e-mail (outbox) → modelo → projeto → registrar →
        histórico → exportar em 375 e 1280 px; operador sem botões e com 403; conflito 409; registro sem JS;
        atualização de 30 s (aba oculta não requisita); **7 passed** (+ axe 4 passed com `E2E_AXE_JS`).
  - [x] Nenhuma requisição a outro domínio (monitor de rede em toda página do e2e).
  - [x] Lighthouse 12.3.0 nas páginas públicas (/, /precos, /termos, /privacidade, /contato, /entrar, /cadastro):
        acessibilidade 100, boas práticas 100, SEO 100, desempenho 97–100. axe-core 4.10.2 (wcag2a/aa, 21a/aa,
        best-practice) sem violações nas telas públicas e logadas, claro/escuro, 375/1280.
  - [x] Capturas em `docs/design/capturas/fase6/` (21 telas × 3 larguras × 2 temas = 126 PNGs, 6,1 MB).
  - [x] Isolamento A/B para cada rota nova (`atualizar`, `previa`, `feriados/<id>/remover`, `modelos/<id>/linhas`,
        resumo com modelo de B, filtros de histórico com ids de B → 404).
  - [x] Suíte: SQLite e PostgreSQL 16 verdes (números no relatório do commit final).
- Diferenças com `telas.md` (justificadas): histórico sem filtro de período nem “Carregar mais” (paginação numerada);
  novo projeto sem checkboxes de dias da semana por projeto (dias vêm da empresa; não há campo no projeto);
  empresa só com Dados/Calendário/Feriados (segurança e LGPD ficam para as Fases 7/8); sem “Assinatura” no menu
  (Fase 8); lista sem faixa de assinatura (Fase 8); menu lateral não recolhe em ícones.
- Pendências:
  - Termos/privacidade são rascunho; razão social/CNPJ do operador e `CONTACT_EMAIL` reais antes do lançamento.
  - Migration `f6a1b2c3d4e5` a reencadear após a Fase 7. Rebuild de `dist/` ao mesclar CSS/JS de outras fases.
  - `/estilo` não mostra os componentes novos (radio card, abas, menu de ações, plan_card).
  - Sem Playwright o teste e2e é pulado; CI precisa instalar `playwright==1.55.0` e o Chromium.
### Fase 7 — Segurança e LGPD
- Status: concluída (telas não capturadas em 375/768/1280 — só a página nova de Privacidade, com macros existentes; Fase 6)
- Datas: início 2026-10-14 · fim 2026-10-14
- Entregas:
  - `app/security.py`: CSP com nonce por requisição (`script-src 'self' 'nonce-…'`,
    `style-src 'self'`, `object-src 'none'`, `base-uri 'none'`, `form-action 'self'`,
    `frame-ancestors 'none'`, sem `unsafe-inline`), `csp_nonce()` no Jinja, HSTS fora de
    dev/test, Permissions-Policy, COOP/CORP, `no-store` em página logada; produção recusa
    subir com cookie inseguro; multipart lido em `BytesIO` (nada em disco); rate limit
    automático para blueprint com “webhook” no nome (`WEBHOOK_RATE_LIMIT`, Fase 8 só registra);
    `signing_keys()` para rotação (`SECRET_KEY_FALLBACKS`).
  - Cookies: `__Host-session`, `__Host-remember` (novo), `__Host-dispositivo`, Secure, HttpOnly,
    SameSite=Lax; tema continua sem HttpOnly.
  - Rate limit: `REDIS_URL` → `RATELIMIT_STORAGE_URI`; produção sem Redis falha no boot com
    mensagem clara; limites novos em importar (upload e confirmação) e LGPD. API: chave por
    token só para token EXISTENTE (inválido cai no IP — nota da revisão).
  - Uploads: zip conferido pelo tamanho REAL descompactado em streaming (não só o declarado),
    zip cifrado recusado, XML com DOCTYPE/ENTITY recusado; `defusedxml==0.7.1` (o openpyxl
    passa a usá-lo — conferido: `openpyxl.xml.DEFUSEDXML is True`).
  - `app/logging_config.py`: logs JSON em stdout, `request_id` (aceita `X-Request-ID` só
    `[A-Za-z0-9._-]{8,64}`, devolve no header), log de acesso com o MOLDE da rota (nunca o
    caminho com token), filtro de e-mail/token/chaves sensíveis; Sentry opcional
    (`sentry-sdk==2.72.0`, `send_default_pii=False`, sem corpo, sem variáveis locais,
    `before_send` remove cookies/Authorization/senhas/tokens/e-mails/IP).
  - LGPD (`app/services/lgpd.py`, `app/blueprints/lgpd.py`, `/app/privacidade`, só owner,
    vale em modo leitura): exportação ZIP de CSVs (todas as tabelas com `company_id` + empresa
    + usuários vinculados; sem hashes/segredo TOTP; células neutralizadas; auditada);
    exclusão com senha + nome da empresa, carência de 30 dias, cancelável, e-mail aos
    proprietários; `flask lgpd-purge [--dry-run]` (idempotente, só empresa com carência
    vencida, apaga usuários sem outro vínculo e nunca a conta de suporte; registro em
    `platform_audit_logs`); `flask lgpd-retencao` (tokens 30 d, throttles 30 d, eventos
    publicados 90 d, `api.request` 6 meses, auditoria 5 anos). Menu “Privacidade” (owner).
  - Suporte (`app/services/support.py`, `flask suporte conceder|revogar|listar|expirar`):
    motivo ≥ 15, “autorizado por”, ≤ 72 h, papel ≤ supervisor, conta com e-mail confirmado e
    MFA; vínculo `memberships.is_support` + `expires_at` — `tenancy` ignora vencido na hora
    (expira sozinho); não conta no plano; não vira owner; não convida ninguém; e-mail aos
    proprietários; tudo em `audit_logs`.
  - Pre-account takeover (nota da revisão): reset que confirma conta nunca confirmada também
    revoga tokens da API e convites pendentes das empresas em que ela é owner
    (`account.claimed_by_reset`); sessões já caíam pelo `session_version`. Risco residual
    (convidados que já aceitaram) documentado em `seguranca.md`.
  - MFA: `MFA_ENCRYPTION_KEY` aceita “nova,antiga” (MultiFernet) + `flask mfa-rotacionar`
    (resolve a pendência da Fase 5).
  - RLS (ADR-0003 atualizado): política `api_tokens_by_token` (resolve a pendência da Fase 9);
    LGPD/retenção/suporte rodam empresa a empresa no próprio contexto; decisão de não usar
    `SECURITY DEFINER` (com FORCE o dono também passa pelo RLS) nem BYPASSRLS no web.
  - Stubs 501 da API resolvem o id na empresa antes (B → 404).
  - Migration `228fffa5a2d8` (cadeia linear depois de `d8b2e6f4a1c7` da Fase 8, após o merge com
    `c5d1ecc`; `flask db heads` = um único head): `platform_audit_logs`,
    `memberships.is_support/expires_at`, política `api_tokens_by_token`.
  - Dependências: `redis==8.0.1`, `sentry-sdk==2.72.0`, `defusedxml==0.7.1`,
    `pip-audit==2.10.1` (dev); job `audit` no CI; `.github/dependabot.yml` (pip semanal,
    actions mensal).
  - Docs: `seguranca.md` (STRIDE com código/teste), `lgpd.md`, `incidentes.md` (ANPD em 3 dias
    úteis, rotação de segredos), `docs/legal/termos.md` e `privacidade.md` (RASCUNHO — as
    rotas `/termos` e `/privacidade` não existiam; layout na Fase 6), README, `.env.example`.
- Critérios de pronto:
  - [x] Testes: CSP com nonce e sem `unsafe-inline`, HSTS, cookies Secure/HttpOnly/SameSite/
        `__Host-` em produção, upload acima do limite → 413, zip bomb (real e com tamanho
        declarado falso) e XXE recusados, rate limit 429 (importar, LGPD, webhook, API)
        (`tests/test_fase7_security.py`, `tests/test_lgpd.py`).
  - [x] Teste do `url_map` agora roda com e sem `FEATURE_PUBLIC_API` e exige caso A/B para toda
        rota `<uuid:>` (inclui as 4 da API, com casos A/B novos no fim de `test_isolation.py`).
        Rotas novas da Fase 7 não têm `<uuid:>` (empresa da sessão) e têm teste A/B próprio
        (exportação só com dados de A; exclusão só da empresa da sessão).
  - [x] `pip-audit -r requirements-dev.txt`: “No known vulnerabilities found” (sem exceções).
  - [x] Exportação LGPD gera ZIP só com dados da empresa (teste A/B, também com RLS forçado).
  - [x] Migration reversível a partir de `d8b2e6f4a1c7` (upgrade → downgrade → upgrade →
        `flask db check` sem drift no PostgreSQL 16 e no SQLite; `downgrade base` ida e volta).
  - [x] Revisão de segurança do próprio diff (abaixo).
- Testes (depois do merge com a Fase 8, `c5d1ecc`): SQLite `463 passed, 44 skipped, 3 xfailed`
  + PostgreSQL 16 (`controle_test_f7`) `507 passed, 3 xfailed`; a única falha nas duas
  (`test_billing_asaas::test_provedor_em_producao_exige_chave`, app de produção sem Redis — regra
  nova da Fase 7) foi corrigida no teste e o arquivo reroda verde. Antes do merge: SQLite
  `389 passed, 42 skipped, 3 xfailed`, PostgreSQL `431 passed, 3 xfailed`, cobertura de `app/`
  94% (lgpd 90%, support 92%, security 96%, logging_config 91%).
- /security-review (revisão manual do diff, achados ≥ 8 corrigidos):
  - Suporte supervisor podia convidar alguém e transformar acesso temporário em permanente →
    `can_manage_invite_role` recusa vínculo de suporte (teste).
  - Expurgo apagaria a conta da equipe de suporte junto com a empresa → vínculos de suporte
    excluídos da lista de usuários a apagar (teste).
  - Expurgo com RLS poderia apagar usuário que tem vínculo em outra empresa (vínculos de outras
    empresas invisíveis no contexto da empresa) → checagem pelo contexto de usuário
    (`memberships_own_user`) (teste com RLS forçado).
  - Retenção/expiração com RLS: `flush` dentro do contexto de cada empresa (senão o UPDATE
    sairia sem contexto e afetaria 0 linhas).
  - Log de acesso gravaria `/convite/<token real>` → só o molde da rota; log do Werkzeug em
    WARNING; README pede para não ligar o access log do Gunicorn.
  - Abaixo do limiar / aceitos: exportação em memória (empresa muito grande); `usuarios.csv`
    inclui o nome/e-mail da pessoa de suporte que teve acesso (transparência); o dono pode
    reativar um vínculo de suporte vencido, mas a validade continua valendo.
- Telas conferidas (375/768/1280, claro/escuro): não (página nova só com macros/tokens;
  `test_visual` verde). Fase 6.
- Commit: “feat: fase 7 — segurança e LGPD” (hash no histórico do branch).
- ADRs criados: ADR-0009 (backend é a única fonte de regras; front é só painel — regra 9 em
  `CLAUDE.md`); ADR-0003 atualizado (fluxos entre empresas sem papel de plataforma, incluindo a
  política da Fase 8).
- Pendências e dívidas:
  - Sessão ainda em cookie assinado (logout não revoga cópia do cookie); sessões no Redis
    ficam para depois do go-live se o risco justificar.
  - Fase 8: webhook do Asaas e worker do outbox decidem entre política estreita por id externo
    ou papel de plataforma só no worker (ADR-0003); usar `ASAAS_*` como em `incidentes.md`.
  - Fase 6: rotas `/termos` e `/privacidade` com o texto de `docs/legal/` (RASCUNHO) e link no
    rodapé; página 500 mostrar o `X-Request-ID`; captura da página de Privacidade.
  - Revisão jurídica (termos, privacidade, `lgpd.md`), DPAs e região do Render (go/no-go).
  - Cron no Render: `flask lgpd-purge`, `flask lgpd-retencao` (diários), `flask suporte expirar`.
  - Produção: definir `REDIS_URL`, `TRUSTED_PROXY_COUNT=1`, `MFA_ENCRYPTION_KEY` própria.

### Etapa B — Planos novos e cobrança
- Status: concluída
- Datas: início 2026-10-14 · fim 2026-10-14
- Entregas:
  - `app/services/plans.py`: 4 planos (ids uuid5 mantidos) — Essencial R$ 249,90 (3 projetos,
    3 pessoas), Profissional R$ 497,00 (10, 20), Empresa R$ 997,00 (ilimitado; MFA, API,
    identidade visual), Implantação sob consulta (`price_cents` NULL; tudo do Empresa +
    `implantacao`). `features`: `mfa_required`, `api`, `visual_custom`, `implantacao`.
    `TRIAL_PLAN_CODES`, `has_trial`, `is_self_service`, `is_managed`, `active_plans`.
  - Migration `b1e7c9d2a4f6` (depois de `f6a1b2c3d4e5`): `plans.price_cents` anulável, CHECK
    `price_cents IS NULL OR price_cents >= 0`, atualiza os 3 planos e insere `implantacao`;
    downgrade volta os valores da Fase 3 (recusa se houver assinatura em plano sob consulta).
    `flask seed-plans` continua idempotente (sincroniza também `active`).
  - Teste grátis só no Essencial/Profissional: `entitlements.trial_plan()` (config fora dos
    planos com teste cai no Profissional), `trialing` em plano sem teste vale como o plano de
    teste; cadastro e `ensure_subscription` usam o mesmo plano.
  - Cobrança: Empresa sem teste (1ª fatura vence no dia; upgrade pendente até pagar);
    `compare_plans` explícito (upgrade, mesmo preço = só após pagamento, downgrade só se
    estritamente mais barato, preço nulo = recusado); `price_for` devolve None e `charge_for`
    levanta `BillingError` para sob consulta (nunca conta com None); autosserviço recusa
    Implantação (404 nas rotas, `BillingError` no serviço) e troca/cancelamento de quem está
    nela; `recompute` não mexe em plano sob consulta sem assinatura no provedor.
  - `flask billing-admin set-plan --company --plan --reason` (motivo obrigatório,
    `subscription.admin_plan_set` em audit_logs); `extend-trial` recusado em plano sem teste;
    `discount` recusado em sob consulta.
  - Gancho da Etapa C: `plan.visual_custom_contracted` em `audit_logs` e `domain_events`
    (evento interno, `events.INTERNAL_EVENT_TYPES`) quando o plano com `visual_custom` passa a
    valer (pago ou atribuído).
  - Telas: `/` e `/precos` com os 4 planos do banco (Implantação “Sob consulta — fale
    conosco” com CTA para `/contato`; linha de teste grátis por plano; comparação com
    identidade visual e implantação); `/app/assinatura/planos` com os 4 planos, sem botão de
    contratar no 4; assinatura/troca/cobrança tratam preço e pessoas ilimitadas. Só macros e
    tokens existentes (CSS/JS não mudaram; sem `build_assets`).
  - `APP_BASE_URL` (https) obrigatório fora de development/test em `finalize_config`.
- Critérios de pronto:
  - [x] Testes novos e antigos verdes em SQLite
  - [x] Suíte em PostgreSQL 16 (`controle_test_b`)
  - [x] `flask db heads` com um head; upgrade → downgrade → upgrade e `flask db check` sem
    drift em SQLite e PostgreSQL
  - [x] Revisão de segurança do diff
  - [ ] Telas conferidas em 375/768/1280 claro/escuro (só macros/tokens; `test_visual` verde)
  - [x] README, prd.md (D2–D5 + tabela de planos), pagamentos.md, backlog.md (F8-5)
- Testes: SQLite `528 passed, 57 skipped, 3 xfailed`; PostgreSQL `574 passed, 11 skipped,
  3 xfailed`. Correção de isolamento no PG: `plans` sobrevive ao TRUNCATE entre testes e
  testes que mexem em preço/limite (ex.: `test_preco_e_limite_vem_do_banco`,
  `test_precos_vem_da_tabela_plans`) vazavam para os seguintes; `tests/conftest.py`
  (`_resync_plans`) agora volta `plans` ao catálogo (e remove planos extras) antes de cada teste. novos em `tests/test_etapa_b_planos.py`
  (31 casos: limites dos 4 planos pelas rotas, trial só 1/2, Empresa sem trial, Implantação
  fora do autosserviço e só por `set-plan` com motivo, preço/limite do banco, telas 200,
  preço igual/nulo, `APP_BASE_URL`). Testes de API passam a assinar o Empresa
  (`make_tenant(..., plan="empresa")`) em vez de `DEFAULT_TRIAL_PLAN=empresa`.
- /security-review (revisão manual do diff): sem achado aberto. Conferido: limite não fura
  por teste em plano pago (guarda em `access`), teste não é reaproveitado em plano sem teste
  (`extend-trial` recusa), Implantação não entra por rota, formulário, troca pendente ou
  webhook, preço sempre lido do banco (o formulário só manda o código do plano), sem
  aritmética com preço nulo.
- Telas conferidas (375/768/1280, claro/escuro): não (sem navegador nesta sessão).
- Commit: “feat: etapa B — planos novos e cobrança” (hash no histórico do branch).
- ADRs criados: nenhum (decisões do usuário registradas no PRD D2–D5).
- Pendências e dívidas:
  - Etapa C: consumir `plan.visual_custom_contracted` (requisição de identidade visual) e
    painel interno; sair da Implantação hoje só por `set-plan` para plano com preço quando
    houver assinatura no provedor (senão o cliente assina pela tela depois de a equipe
    cancelar o contrato).
  - Homologação no sandbox do Asaas com os valores novos (`pagamentos.md` §5).

## Etapa C — painel interno e requisição de identidade visual
- [x] `users.is_staff` + `flask staff conceder|revogar|listar` (motivo ≥ 15 caracteres, quem autorizou, e-mail confirmado e MFA ativo; revogar derruba as sessões; tudo em `platform_audit_logs`).
- [x] `visual_requests` (dado da plataforma, sem RLS por empresa; `company_id` nullable, sem FK; o expurgo LGPD apaga as linhas via `lgpd.company_tables`). Migration `c7d3e9a1b5f2`.
- [x] `billing.service._apply_plan` abre a requisição na mesma transação ao passar a ter `visual_custom` (uma aberta por empresa), copiando o contato do proprietário.
- [x] `/interno` (lista com filtro por estado, detalhe, mudar estado + anotação): só `staff.is_staff` (equipe ativa, MFA, e-mail confirmado); qualquer outra pessoa, logada ou não, recebe 404; `Cache-Control: no-store`; CSRF; estado validado no servidor; auditoria sem o texto da anotação. Decisão: acesso pelo login normal do sistema, com MFA obrigatório para a conta de equipe.
- Testes: `tests/test_etapa_c_interno.py` (abertura única, 404 para anônimo/dono/não-equipe/sem MFA, fluxo da equipe, CLI, LGPD).
- Pendências: telas do `/interno` ainda sem conferência visual (375/768/1280, claro/escuro); aviso por e-mail à equipe ao abrir a requisição entra com o worker (Etapa F).

## Etapa D — colaboração
- Status: concluída (pendências abaixo) · 2026-10-15
- Entregas:
  - [x] Schema: migration `d4a8c2e6f1b3` (down `c7d3e9a1b5f2`): `stages.version` (padrão 1,
    CHECK ≥ 1) e `activities.assignee_id` (FK `users` ON DELETE SET NULL, índice
    `company_id, assignee_id`). Upgrade → downgrade → upgrade sem drift em SQLite.
  - [x] Autoria: cada atividade do detalhe mostra o responsável e o último lançamento (quem,
    quanto, quando — `projects.last_entries`, uma consulta); o histórico já mostrava o autor e
    agora mostra quem desfez cada registro desfeito (`projects.undo_entries`).
  - [x] Edição com concorrência: renomear etapa e editar nome/tempo da atividade levam a
    `version` lida pela tela; UPDATE condicional (`_guarded_update`) → `EditConflict` → 409 na
    tela de edição com o valor atual e o que a pessoa digitou, já com a versão atual (salvar de
    novo = confirmação). A versão da atividade é a mesma do registro de peças: registrar, editar
    ou mover invalidam telas abertas (de propósito). Sem `version` no POST continua aceito
    (como no registro). Auditoria `stage.renamed` e `activity.updated`.
  - [x] Atribuição: `POST /app/atividades/<id>/responsavel` (supervisor+). `assign_activity`
    só aceita membro ATIVO da mesma empresa (vínculo `usable()`, sem acesso de suporte, usuário
    ativo); outro id (outra empresa, desativado, inexistente, inválido) → 404. Auditoria
    `activity.assigned`; ao atribuir, evento INTERNO `activity.assigned` só com ids (projeto,
    etapa, atividade, responsável) — gancho da notificação por e-mail da Etapa F; não sai em
    webhook de cliente (`INTERNAL_EVENT_TYPES`). Desativar a pessoa limpa as atribuições dela na
    empresa (`clear_assignments`, contado na auditoria).
  - [x] Progresso por pessoa: `calc.progresso_por_pessoa` (puro) agrega lançamentos por pessoa
    no período (saldo de peças, registros, desfazeres, horas-padrão = Σ delta × tempo ideal,
    dias ativos, saldo por atividade) e as atividades atribuídas por responsável (concluídas,
    peças/previstas, progresso ponderado por tempo como `progresso_tarefas`).
    `GET /app/projetos/<id>/pessoas?periodo=7|30|90|tudo` (supervisor+) e painel
    “Pessoas · 7 dias” no detalhe (só supervisor+; o operador não vê). Datas no fuso da empresa.
  - [x] Arrastar: `POST /app/projetos/<id>/etapas/ordem` (lista COMPLETA, campo `order`
    repetido; id fora do projeto/empresa → 404; lista diferente das etapas atuais ou repetida →
    409; auditoria `stages.reordered`) e `POST /app/atividades/<id>/posicionar` (`stage_id`,
    `position`, `version`; etapa de outro projeto/empresa → 404; versão velha → 409; renumera
    origem e destino, incrementa a versão, audita `activity.moved`, recalcula o status do
    projeto). UI: `app/static/js/arrastar.js` (HTML5 drag-and-drop nativo, sem biblioteca, só
    pela alça ⠿, carregado só na tela de edição via `asset_urls("arrastar.js")` e no manifesto
    do `build_assets`); o JS só preenche e envia formulários POST com CSRF. Sem JS: Subir/Descer
    e o seletor “Mover” (para outra etapa, vai para o fim).
- Critérios de pronto:
  - [x] Testes novos verdes (`tests/test_etapa_d.py`, 17 casos) e antigos verdes em SQLite
  - [x] Teste A/B para cada rota nova (`ROUTES_ETAPA_D` em `tests/test_isolation.py`, com ids
    da própria empresa e da outra no corpo; casos extras: responsável de B na atividade de A,
    etapa de B ao mover/reordenar no projeto de A)
  - [x] `calc.py` continua puro (teste AST); nenhum cálculo no template/JS
  - [ ] Suíte em PostgreSQL 16 (não rodada: banco local ocupado por outro processo)
  - [ ] Telas conferidas em 375/768/1280 claro/escuro (sem navegador nesta sessão; só tokens,
    `test_visual` verde)
  - [x] Revisão de segurança do diff (manual)
- Testes: SQLite `565 passed, 57 skipped, 3 xfailed` (antes da etapa: 528 passed).
- /security-review (manual): company_id sempre da sessão; ids do corpo (`assignee_id`,
  `stage_id`, `order`) resolvidos na empresa da sessão/projeto da URL; papéis checados na rota
  (supervisor+) e esconder controles não substitui a recusa (testes 403); evento sem nome/e-mail.
- Decisões tomadas (confirmar com o usuário): progresso por pessoa visível só para
  supervisor+ (dado de desempenho individual); mover/editar invalida a versão compartilhada da
  atividade; reordenar etapas não incrementa `stages.version` (versão protege o nome).
- Pendências:
  - Etapa F: consumir `activity.assigned` (e-mail ao responsável).
  - Arrastar no toque (celular): o DnD nativo do HTML5 não funciona em navegadores móveis;
    lá valem Subir/Descer e “Mover”.
  - Conferência visual das telas novas (edição com alças, `/pessoas`, painel no detalhe).
  - Rodar a suíte em PostgreSQL (`TEST_DATABASE_URL`) e a migration no PG.

## Etapa E — dashboard completo do projeto

- [x] `calc.py` (puro): `razao`, `equipe_x_prazo` (aba Equipe, 1–6 pessoas), `contagem_status`, `etapas_sem_tempo`, `tempo_trabalhado_min/h` (etapa e projeto). Paridade com `acompanhamento_montagem_v4.xlsx` em `tests/test_calc.py::test_paridade_dashboard_com_planilha_de_referencia` (Tabela 1, Tabela 2, totais, status, resumo final 377–385, equipe × prazo).
- [x] `app/services/charts.py` (puro, só geometria: medidor, rosca, colunas empilhadas, treemap squarified) e `app/services/dashboard.py` (monta o contexto a partir do `ResultadoProjeto`; sem Flask/banco). Testes em `tests/test_charts.py` e `tests/test_etapa_e.py`.
- [x] Rota `GET /app/projetos/<uuid>/painel` (operador+, só leitura) + `?tabela=tarefas|unidades`; botão “Painel” no detalhe. Detalhe aceita `?etapa=<uuid>` (só etapa do próprio projeto; id solto é ignorado) para abrir a etapa clicada e lançar peças.
- [x] Tela: 6 KPIs (progresso geral em medidor, unidades prontas, unidades concluídas, tarefas, tempo que falta, dias úteis até o prazo), tarefas × unidades (barras agrupadas), status (rosca), peso (treemap), horas trabalhadas × faltam (colunas empilhadas), equipe × prazo, tabelas 1 e 2 com clique para lançar. SVG no servidor, `<title>`/`<desc>`/aria, texto ao lado de toda cor, só tokens, sem script/estilo inline/CDN.
- [x] Teste A/B em `tests/test_isolation.py` (`ROUTES_ETAPA_E`, inclui `?etapa=` de outra empresa).
- [ ] Não feito de propósito: destaque de etapas futuras “aguardando peça” (o campo não existe; não foi criado).
- [ ] Suíte em PostgreSQL não rodada (banco local ocupado). Conferência visual feita por captura automática (375/768/1280, claro/escuro, sem rolagem horizontal da página); revisão humana pendente. Treemap tem texto pequeno no celular (a tabela repete os valores).
- Testes SQLite: tudo verde (painel, calc, charts, isolamento, visual, fase6 com manifesto de assets reconstruído).

## Etapa F — worker, aguardando peça, alertas e e-mails
- Status: concluída em SQLite (pendências abaixo) · 2026-10-15
- Entregas:
  - [x] **Worker** (ADR-0010, proposto): `flask worker run` (laço; `SIGTERM` para no fim do
    ciclo), `--once` (cron/testes), `--task events|alerts|weekly|reconcile|tokens`,
    `flask worker status`. Laço **empresa a empresa com `rls.set_context`**, sem papel
    `BYPASSRLS`. Outbox: um evento por transação, `FOR UPDATE SKIP LOCKED`, `attempts` +
    `next_attempt_at` (60 s × 2^n, teto 6 h) + `last_error` (só o nome da exceção), limite
    `WORKER_EVENT_MAX_ATTEMPTS` (8). Tarefas idempotentes: alertas (dedupe), relatório
    semanal (`job_runs`), `billing.reconcile_all` (reaproveitado), limpeza de tokens
    (`lgpd.purge_expired_tokens`, auditada em `platform_audit_logs`). Runbook
    `docs/plano/worker.md`. Migration `e2b7f1c3a9d0` (down `d4a8c2e6f1b3`): colunas no outbox +
    `job_runs` (RLS).
  - [x] **Aguardando peça**: `stages.waiting_part`, `part_expected_on`, `part_note` (140),
    `part_updated_at` — migration `f3c8a2d4b1e5`. `POST /app/etapas/<id>/aguardando-peca`
    (supervisor+, `version` → 409, auditoria `stage.waiting_part` sem a observação livre, 404
    cruzado). Só sinaliza: registro de peças continua livre (teste). Selo texto + ícone
    (`i-package`) na lista de projetos, no resumo da etapa do detalhe, no painel (cabeçalho e
    tabelas). Resolve a pendência da Etapa E (“destaque de aguardando peça”).
  - [x] **Alertas**: regra PURA `calc.alertas_projeto` (atraso previsto, prazo em risco, etapa
    parada há X dias úteis, peça atrasada) + `calc.dias_parada_valido`. Tabela `alerts`
    (RLS, `UNIQUE(company_id, dedupe_key, day)`), `companies.stalled_days` (padrão 3, CHECK
    1..60, validado no formulário e no serviço), migration `a5d9e3f7c2b8`. Tela `/app/alertas`
    (supervisor+, 14 dias, item “Alertas” no menu). E-mail-resumo a supervisores/proprietários
    com `notify_alerts`, a partir das 7h locais; a mesma situação volta ao e-mail no máx. 1×
    a cada 7 dias.
  - [x] **Atribuição**: consumidor de `activity.assigned` → e-mail com link
    (`/app/atividades/<id>`, base `APP_BASE_URL`) ao responsável com `notify_assignment`;
    não envia se a pessoa se atribuiu (payload ganhou `assigned_by_user_id`, só id), se foi
    reatribuída, se saiu da empresa ou se a atividade foi arquivada; falha → backoff.
  - [x] **Relatório semanal**: segunda, a partir das 7h locais, uma vez por semana ISO por
    empresa; projetos (calc/serviços) e pessoas (`calc.progresso_por_pessoa`, todos os
    projetos, últimos 7 dias); anexo XLSX (`exporter.weekly_xlsx`, células neutralizadas).
  - [x] Preferências por usuário em `/conta/perfil#notificacoes` (`users.notify_assignment`,
    `notify_alerts`, `notify_weekly`, padrão ligado; valem em todas as empresas).
  - [x] E-mail: anexos (`email.Attachment`; Resend em base64), `email.send_now` (síncrono,
    levanta `EmailError` para o worker), `email.request_scope` (links fora de requisição),
    rodapé por bloco (`emails/_base.*`) com o link para desligar. Aviso à equipe da requisição
    de identidade visual (`STAFF_NOTIFY_EMAIL`) — resolve a pendência da Etapa C.
- Critérios de pronto:
  - [x] Testes novos verdes (`test_etapa_f_worker.py` 12, `test_etapa_f_peca.py` 6,
    `test_etapa_f_alertas.py` 21, `test_etapa_f_atribuicao.py` 6, `test_etapa_f_semanal.py` 4)
    e antigos verdes em SQLite
  - [x] Teste A/B para cada rota nova (`ROUTES_ETAPA_F` + `test_etapa_f_alertas_so_da_propria_empresa`
    e `test_etapa_f_preferencias_so_do_proprio_usuario` em `tests/test_isolation.py`)
  - [x] `calc.py` continua puro; nenhum cálculo no template (contagem de etapas aguardando
    peça vem de `dashboard.build`/serviço)
  - [x] `RLS_TABLES` + políticas nas tabelas novas (`job_runs`, `alerts`); `test_schema` verde;
    `flask db heads` = `a5d9e3f7c2b8`; upgrade → downgrade → upgrade sem drift em SQLite
  - [ ] Suíte e migrations em PostgreSQL 16 (não rodadas: banco local ocupado por outro processo)
  - [ ] Telas conferidas em 375/768/1280 claro/escuro (sem navegador nesta sessão; só macros e
    tokens, `test_visual` verde, manifesto de assets reconstruído)
  - [x] Revisão de segurança do diff (manual, abaixo)
- Testes: SQLite `646 passed, 59 skipped, 3 xfailed` (antes da etapa: 593 passed).
- /security-review (manual): empresa sempre da sessão (rotas) ou do evento/laço (worker, com
  `set_context` antes de cada consulta); ids do payload resolvidos com `company_id` do evento;
  destinatários só com vínculo `usable()`, sem suporte, usuário ativo e preferência ligada;
  e-mails só com nome da empresa/projeto/etapa/atividade e links de `APP_BASE_URL`; HTML dos
  e-mails com autoescape; `last_error` sem mensagem (pode ter PII); logs sem endereço; XLSX
  neutralizado; CSRF em todo POST novo; papel checado na rota (403) além de esconder o botão.
- ADRs: 0010 (worker laço por empresa) — **proposto, confirmar**; atualizações em 0003 (tabela
  de fluxos) e 0005.
- Decisões a confirmar com o usuário:
  - Preferências de e-mail no USUÁRIO (valem em todas as empresas), não por vínculo.
  - Alertas e relatório só para supervisor+ (operador não vê `/app/alertas`).
  - “Etapa parada” em dias ÚTEIS (feriados e fins de semana não contam) e só para etapa “Em
    andamento”; etapa aguardando peça não gera “parada”. Margens fixas no calc: folga ≤ 1 dia
    útil = prazo em risco; sem previsão, prazo em ≤ 5 dias úteis = risco.
  - E-mail de alertas a partir das 7h locais; repetição no máx. 1×/7 dias por situação;
    relatório semanal na segunda a partir das 7h (semana anterior, seg–dom).
  - Marcar/desmarcar “aguardando peça” incrementa `stages.version` (invalida um renomear aberto).
  - Empresas com exclusão pedida (carência LGPD) não recebem alertas nem relatório.
  - Eventos públicos sem consumidor são marcados publicados (até existirem webhooks de saída).
- Pendências:
  - PDF do relatório semanal: fora (sem dependência leve no `requirements.txt`; reportlab/
    weasyprint são pesadas) — só XLSX.
  - Rodar no PostgreSQL: suíte com `TEST_DATABASE_URL`, `tests/test_migrations.py` (roundtrip
    das 3 migrations + políticas `tenant_isolation` em `job_runs`/`alerts`), `tests/test_rls.py`
    (as tabelas novas entram no parametrize de `RLS_TABLES`), worker com `RLS_ENABLED=1` e papel
    `NOSUPERUSER NOBYPASSRLS` (`flask worker run --once` com RLS forçado), `FOR UPDATE SKIP
    LOCKED` com dois workers simultâneos, e o ramo da migration que liga ENABLE/FORCE quando o RLS
    já está ativo.
  - Link do e-mail de atribuição abre na empresa ATIVA da sessão; quem tem várias empresas pode
    cair em 404 até trocar de empresa (texto do e-mail avisa). Melhoria: parâmetro de troca
    segura de empresa no link.
  - Render: criar o Background Worker (`flask worker run`) ou cron `flask worker run --once`;
    definir `STAFF_NOTIFY_EMAIL`.
  - Conferência visual: `/app/alertas`, formulário/selo de aguardando peça (detalhe, lista,
    painel), seção “Notificações por e-mail” no perfil e “Alertas” em `/app/empresa`.
  - Eventos esgotados não são apagados pela retenção (só os publicados): acompanhar com
    `flask worker status`.


## Etapa G — qualidade (fotos e comentários, checklist de inspeção, número de série)
- Status: concluída em SQLite (pendências abaixo) · 2026-10-15 · branch `claude/etapa-g-qualidade`
- ADR: **0011 (proposto, confirmar)** — armazenamento S3 compatível com SigV4 próprio (sem boto3),
  fotos só por rota autenticada, checklist só sinaliza, unidades como rastreabilidade.
- Entregas:
  - [x] **Bloco 1 — fotos e comentários por atividade** (`/app/atividades/<id>/evidencias`):
    `app/services/storage.py` (interface; `local` em `instance/uploads` só dev/test — produção
    recusa no boot; `s3` para R2/AWS/MinIO com SigV4 conferido pelo vetor da AWS; `none` = fotos
    desligadas, padrão em produção sem `STORAGE_*`). `app/services/photos.py`: magic bytes
    (JPEG/PNG/WebP), dimensões ≤ 40 MP antes de decodificar, decodificação com Pillow, reencode
    para JPEG sem EXIF/GPS/ICC + miniatura, ≤ 5 MB (teto de corpo só nesta rota via
    `InMemoryUploadRequest.max_content_length`), 20 por atividade, 5000 por empresa, rate limit;
    chave `<company_id>/fotos/<uuid>.jpg`; objeto antes da linha (falha → objeto apagado);
    SHA-256 conferido na leitura. `/app/fotos/<uuid>` (`?tamanho=mini`): `Content-Type` fixo,
    `nosniff`, `Cache-Control: private`, CSP `sandbox`. Comentários 1..1000 (operador+);
    supervisor+ apaga foto/comentário com auditoria sem o conteúdo. Link “Fotos e comentários”
    por etapa no detalhe. Migration `b6e1f4a2c9d3`.
  - [x] **Bloco 2 — checklist de inspeção**: itens no modelo (`template_checklist_items`, entram
    na assinatura da versão — mudar o checklist cria versão nova) e “exigir checklist” por etapa
    do modelo; copiados ao projeto (`stage_checklist_items`) na criação, ao duplicar e ao aplicar
    versão (itens novos entram, nenhum é apagado). Supervisor+ inclui/arquiva itens e liga a
    exigência na tela da etapa (`/app/etapas/<id>/checklist`). Inspeção (`stage_inspections`):
    rascunho (operador+, UPDATE condicional por `version` → 409) → assinada (usuário da sessão +
    hora do servidor; todo item ativo respondido; “não conforme” exige observação). Depois:
    respostas com `locked_at` e guarda ORM; correção = nova linha `supersedes_id` (UNIQUE) +
    motivo, só supervisor+, a antiga fica e aparece no histórico do item. Selo “Checklist
    pendente/assinado” no resumo da etapa — **só sinal**, registro de peças livre (teste).
    Migration `c8f2a5d1e7b4`.
  - [x] **Bloco 3 — unidades**: `units` (série única por empresa+projeto, normalizada em
    maiúsculas, status em produção/concluída/expedida/refugada com `version`), supervisor+ gera
    faixa (prefixo + início + dígitos) ou cola lista; limite = `quantity` do projeto (e a
    quantidade não pode descer abaixo das unidades). `progress_entries.unit_id` e
    `stage_inspections.unit_id` opcionais. “Registrar nesta unidade” = +1 pela regra normal
    (`register_progress`), uma vez por atividade+unidade (desfazer libera; o compensatório leva
    a unidade). `/app/projetos/<id>/unidades` (lista, busca, cadastro), `/app/unidades/<id>`
    (histórico: lançamentos, inspeções, mudanças de status), `/app/unidades?q=` (busca na
    empresa, `LIKE` com escape) e item “Unidades” no menu. `calc.py` intocado; teste prova que
    cadastrar unidades não muda o resumo. Migration `d9a3b6e2f8c5`.
  - [x] LGPD: expurgo apaga os objetos de foto antes das linhas (falha do armazenamento desfaz o
    expurgo; `objects_deleted` no resultado, no CLI e em `platform_audit_logs`); exportação lista
    os metadados das fotos e explica no LEIA-ME que os arquivos não vão no ZIP.
  - [x] Docs: ADR-0011, `seguranca.md` (fotos, checklist, unidades), `lgpd.md` (inventário,
    operador R2/S3, exportação/expurgo de fotos), README, `.env.example` (`STORAGE_*`, limites).
    Dependência nova: `Pillow==12.3.0`.
- Critérios de pronto:
  - [x] Testes novos verdes: `test_etapa_g_evidencias.py` (32, inclui não-imagem com `.jpg`,
    GIF, SVG, PDF, magic de JPEG falso, polyglot JPEG+HTML+ZIP, > 5 MB nos dois tetos, PNG com
    3,6 bilhões de pixels declarados, objeto adulterado), `test_etapa_g_storage.py` (22),
    `test_etapa_g_checklist.py` (10), `test_etapa_g_unidades.py` (10)
  - [x] Teste A/B para CADA rota nova (`ROUTES_ETAPA_G`, `ROUTES_ETAPA_G_CHECKLIST`,
    `ROUTES_ETAPA_G_UNIDADES` em `tests/test_isolation.py`, com ids da própria empresa e da outra
    no corpo; objeto no armazenamento de B conferido intacto; casos extras: item de B na
    inspeção de A, unidade de B na inspeção de A, atividade de B na unidade de A, busca)
  - [x] RLS: 7 tabelas novas em `RLS_TABLES` com política `tenant_isolation` nas migrations;
    `test_schema` verde; `flask db heads` = `d9a3b6e2f8c5`; upgrade → downgrade → upgrade +
    `flask db check` sem drift em SQLite para cada migration
  - [x] Tokens CSS (só `var(--…)`, `test_visual` verde), CSP sem inline, manifesto de assets
    reconstruído
  - [ ] Suíte e migrations em PostgreSQL 16 (não rodadas: banco local é de outro processo)
  - [ ] Telas conferidas em 375/768/1280 claro/escuro (sem navegador nesta sessão)
  - [x] Revisão de segurança do diff (manual, tabela em `seguranca.md`)
- Testes: SQLite `763 passed, 66 skipped, 3 xfailed` (~8 min; antes da etapa: 646 passed).
- Decisões a confirmar com o usuário (ADR-0011):
  - S3 compatível com SigV4 próprio (sem boto3); R2 recomendado; produção sem `STORAGE_*` sobe
    com fotos desligadas.
  - Tudo reencodado para JPEG (PNG/WebP com transparência ganham fundo branco); lado máximo
    2560 px; miniatura 480 px.
  - Limites 5 MB, 20 fotos/atividade, 5000/empresa por configuração — não ligados ao plano.
  - Exportação LGPD só com metadados das fotos (arquivos fora do ZIP).
  - Apagar comentário/foto = remoção de verdade + auditoria sem o conteúdo (não “soft delete”).
  - Checklist: operador+ assina; correção só supervisor+; “exigir” só sinaliza.
  - Unidade: série em maiúsculas; registrar na unidade é sempre +1 e uma vez por
    atividade+unidade; menu “Unidades” para todos os papéis.
- Pendências / verificar no PostgreSQL:
  - `TEST_DATABASE_URL` com a suíte inteira; `tests/test_migrations.py` (roundtrip das 3
    migrations, ADD COLUMN em `stages`/`template_stages`, batch de `progress_entries` e
    `stage_inspections` com a FK nova); `tests/test_rls.py` (as 7 tabelas novas entram no
    parametrize de `RLS_TABLES`: consulta crua sem contexto = 0 linhas); expurgo LGPD com RLS
    forçado apagando fotos; o ramo da migration que liga ENABLE/FORCE quando o RLS já está ativo;
    `length(body)`/`length(serial)` nos CHECK; busca `LIKE ... ESCAPE '\'` no PG.
  - Homologar R2 de verdade (PUT/GET/DELETE com a chave restrita; `addressing=path`,
    região `auto`) — a rede deste ambiente não foi usada.
  - Conferência visual: evidências, checklist, inspeção, unidades, unidade, busca, selos no
    detalhe e campo de checklist no editor de modelo.
  - Sem varredura de objetos órfãos no bucket (falha ao apagar depois do commit só loga
    `photos.orphan_object`); sem cópia dos arquivos de foto na exportação LGPD.
  - API v1 não expõe fotos/checklist/unidades.

### Etapa H — Deploy e lançamento
- Status: concluída no repositório; **o lançamento depende do dono** (`lancamento.md`, Parte B)
- Datas: início 2026-10-15 · fim 2026-10-15
- Entregas:
  - [x] **Bloco 1 — saúde**: `GET /saude` (liveness, sem banco/sessão/dado interno, `no-store`) como
    health check do Render; `/health` segue como prontidão. Testes em `tests/test_etapa_h_saude.py`.
  - [x] **Bloco 2 — configuração**: `flask config-check` (`--online`, `--strict`, `--ignorar`) e
    `scripts/config_check.py` (`app/configcheck.py`); `flask mail-test`, `storage-test`,
    `sentry-test`, `worker status --check` + `queue_metrics` e linha de vida do worker a cada 5 min.
  - [x] **Bloco 3 — backup**: `backup_dump.sh` (age + assinatura `ssh-keygen -Y` + R2 + retenção 30 dias
    com mínimo), `backup_photos.sh` (espelho com trava), `backup_restore_check.sh` (assinatura
    obrigatória antes de descriptografar; restore como papel temporário sem privilégios; contagens);
    `docker/backup/Dockerfile`. Recusa quando o papel não enxerga todas as linhas (RLS forçado).
  - [x] **Bloco 4 — deploy**: `Dockerfile`, `.dockerignore`, `gunicorn.conf.py`, gerador de `render.yaml` /
    `render.staging.yaml`, job `docker` e conferências no CI.
  - [x] **Bloco 5 — docs**: `operacao.md`, `lancamento.md`, ADR-0012 (proposto), README, `.env.example`;
    `scripts/smoke_check.py` com teste local.
- Critérios de pronto:
  - [x] Testes novos verdes (SQLite e PostgreSQL 16 privado): `test_etapa_h_saude/config/backup/render/smoke`
  - [x] Teste de isolamento: nenhuma rota com `<uuid:>` nova (só `/saude`, pública); `test_isolation` verde
  - [x] Sem regra de negócio alterada (`calc.py` intocado); mudanças de app: rota `/saude`, comandos de CLI,
    `queue_metrics`, linha de vida do worker
  - [ ] `docker build` (sem daemon neste ambiente — CI) e `render blueprints validate` (sem CLI)
  - [ ] Telas 375/768/1280 (nenhuma tela nova)
- Testes: ver linha “Suíte” abaixo.
- Decisões a confirmar: ADR-0012 (liveness separada, imagem única, crons fora do worker, backup assinado;
  §6 aberta: papel do banco no Render).
- Pendências para o dono: tudo da Parte B de `lancamento.md` (domínio, contas, DNS/SPF/DKIM/DMARC, chaves,
  R2, Asaas produção e homologação, contador, advogado, `rls enable`, `seed-holidays`, `staff conceder`,
  teste de restore, alertas, smoke test, cobrança real estornada).
- Limitações conhecidas: a assinatura do backup protege contra token do bucket vazado, não contra o
  comprometimento do próprio ambiente do cron; espelho de fotos na mesma conta Cloudflare;
  `send_default_pii` do Sentry aparece como depreciado na versão instalada (migrar para
  `data_collection` em manutenção).

## Identidade visual “Prumo Noturno” (2026-10-15)

- Entregue: novos tokens (claro e escuro), fonte Geist, símbolo e imagens da marca, componentes
  (botão principal com brilho, foco com halo, rótulos em frase normal, faixa final azul, menu lateral
  em pílula), hero maior no desktop, docs de marca/contraste e ADR-0013.
- Verificação: `pytest` completo verde (873 passed, 77 skipped, 3 xfailed; os skips são os testes
  que exigem PostgreSQL), `scripts/build_assets.py --check` ok, contraste recalculado (claro e escuro).
- Pendências: telas conferidas em 375/768/1280 px no navegador (sem navegador neste ambiente);
  regerar `docs/design/capturas/`; decidir o nome comercial.

## Reestruturação R8 — servidor (restaurar o projeto para uma data)

- Status: parte de servidor concluída; tela definitiva pendente (vem com o visual novo).
- Datas: início 2026-10-21 · fim 2026-10-21
- Entregas:
  - `app/services/restore.py`: `restore_preview(project, at)` (peças de cada atividade ativa no
    instante, diferença agora → depois por etapa/atividade, resumo do projeto antes/depois via
    `calc.resumo_projeto` e um `token` = assinatura do estado lido: versão e peças de cada atividade,
    quantidade e instante); `restore_apply(project, at, actor_id, expected_token)` (token diferente
    → `RestoreConflict`/409; grava UM lançamento compensatório por atividade que muda, com UPDATE
    condicional na versão, eventos de progresso/conclusão, status do projeto e auditoria
    `project.restored` com quem, para quando, quantos lançamentos); `restore_undo(project,
    restore_id, actor_id)` (inverte os lançamentos da restauração, uma vez só, recusa desfazer um
    desfazer e recusa se a inversão sairia de 0..previstas; auditoria `project.restore_undone`);
    `restorations(project)` para a lista.
  - `calc.pecas_no_instante`: peças de agora menos tudo o que foi lançado depois do instante
    (registros, desfazeres e restaurações), limitado a 0..previstas de agora. Conta para trás, então
    funciona mesmo se o histórico não começa em zero.
  - Migration `e8c4a7b2d1f9` (revisa `d9a3b6e2f8c5`): `progress_entries.restore_id` e
    `restore_undoes_id` (Uuid, NULL nas linhas antigas, sem FK: a operação vive em `audit_logs`),
    índices por empresa e CHECK `restore_undoes_id IS NULL OR restore_id IS NOT NULL`. O histórico
    continua append-only; RLS sem mudança.
  - Rotas (supervisor+; operador 403; projeto de outra empresa ou arquivado 404):
    `GET /app/projetos/<id>/restaurar[?ate=AAAA-MM-DDTHH:MM]` (prévia; data inválida 400),
    `POST /app/projetos/<id>/restaurar` (`ate`, `token`, `confirm`; 409 com a prévia nova se mudou),
    `POST /app/projetos/<id>/restauracoes/<restore_id>/desfazer` (`confirm`; restauração de outro
    projeto/empresa 404). Template mínimo `edicao/restore.html` com componentes existentes.
  - Desfazer registro (`undo_progress`) recusa lançamento de restauração (só sai a restauração
    inteira); o histórico não mostra “Desfazer” nesses lançamentos.
- Regras:
  - A data digitada é local, no fuso da empresa (padrão America/Sao_Paulo), e vale o início do
    minuto: “10:30” = 10:30:00; lançamento às 10:30:20 fica depois e é desfeito.
  - Escopo: só as peças concluídas das atividades ATIVAS (o que o histórico registra). Fora do
    escopo, porque o histórico não guarda esses estados: nomes, tempos ideais, quantidade, pessoas,
    horas por dia, estrutura de etapas e atividades (criar, mover, arquivar), “aguardando peça”,
    checklist, fotos, comentários e unidades (número de série). Atividade/etapa arquivada não muda.
  - Se a quantidade do projeto diminuiu depois do instante, o valor restaurado é limitado às
    previstas de agora.
  - Desfazer a restauração é relativo (como desfazer registro): o que foi lançado depois dela fica.
- Critérios de pronto: [x] restaura e desfaz sem perder histórico · [x] prévia antes de aplicar ·
  [x] 409 se mudou entre prévia e confirmação · [x] A/B para cada rota nova · [ ] tela definitiva no
  visual novo, capturas 375/768/1280 claro/escuro.
- Testes: `tests/test_r8_restaurar.py` (18: calc, fuso, restaurar antes de N lançamentos, futuro
  não muda nada, concorrência por token e por versão no banco, desfazer, limites, isolamento entre
  empresas, projeto arquivado, atividade arquivada, eventos de conclusão, rotas e 403 do operador) e
  bloco R8 em `tests/test_isolation.py` (404 com token válido de B, rota funciona em A, varredura do
  url_map). Suíte completa em SQLite verde; migrations ida e volta em SQLite.
- /security-review: não rodado neste ambiente (sem achado conhecido; empresa sempre via
  `get_or_404` + `company_id` do projeto em todas as consultas).
- Telas conferidas: n/a (tela mínima provisória).
- Pendências para a tela: botão “Restaurar” na tela de histórico (link para
  `edicao.project_restore`), campo data/hora no visual novo, tabela antes → depois com o resumo
  (`preview.before`/`preview.after`), lista de restaurações com “Desfazer restauração”, mensagem de
  409 e de “nada a restaurar”, selo “restauração” nas linhas do histórico (`entry.restore_id`).

## Reestruturação R7 — servidor (planilha)

- Entregue (só serviço + rotas mínimas; o visual definitivo fica com a reestruturação das telas):
  - **Importar qualquer planilha** (`app/services/import_mapping.py`): a leitura virou uma grade em
    memória (`importer.load_grid`, mesmas proteções: tamanho, zip bomb, DTD, senha; tetos de
    5000 linhas × 60 colunas × 30 abas). `inspect` devolve abas, linha de cabeçalho detectada (ou
    escolhida), colunas com amostras e a sugestão de mapeamento por nome (sem acento/caixa).
    `parse_mapped` aplica etapa (obrigatória), subatividade, tempo, previstas, concluídas, % e prazo e
    gera o mesmo `ImportResult` (erros por linha; etapa vazia herda a de cima; linhas “Total” ignoradas).
    CSV/XLSX do site e a planilha de referência seguem reconhecidos sozinhos (`importer.auto_parse`).
  - **Modo simples** (só etapa + %): `ImportResult.mode = "simples"`. TODO(R4): o modelo não tem o modo;
    cada etapa vira UMA subatividade com o nome da etapa e peças = `calc.pecas_de_percentual(%, meta)`
    (sem meta: 100 unidades, com aviso). Quando a R4 criar o campo, `importer.save` grava o modo e o %.
  - **Exportar no layout da base** (`app/services/export_layout.py`): abas Acompanhamento (título, meta,
    indicadores, blocos por etapa, RESUMO FINAL, Tabela 1, Tabela 2 com status colorido) e Equipe
    (cenários 1–6 pessoas, início e prazo) com as MESMAS fórmulas da referência, entradas em amarelo
    `#FFF9DB`, formatos %/número, validação de dados, painéis congelados. Textos do usuário neutralizados.
    Só etapas/atividades ativas (arquivadas ficam na exportação em lista).
  - Rotas: `POST /app/importar/colunas` (etapa de colunas; grade assinada com empresa+usuário, 1 h) e
    `GET /app/projetos/<id>/exportar-planilha.xlsx`. `/app/importar` manda planilhas desconhecidas (ou com
    “Quero escolher as colunas”) para a etapa de colunas. Tela mínima `dados/import_map.html`.
- Testes: `tests/test_r7_planilha.py` (sugestão, inspeção, mapeamento detalhado/simples, erros por linha,
  limites, formatos próprios, fórmulas iguais à referência, neutralização, **recalculo no LibreOffice
  comparado com `calc.resumo_projeto`**, referência importada→exportada bate com a original, round-trip
  exportar→importar, rotas); `test_isolation.py`: rota de exportação no A/B e grade de outra empresa recusada.
- Verificação: `recalc.py` da skill xlsx na exportação da referência: 1444 fórmulas, 0 erros.
- Pendências: tela definitiva da etapa de colunas e o link “Exportar planilha” no projeto (UI);
  conferência no Excel real; telas 375/768/1280; PostgreSQL não rodado (só SQLite nesta fase).
- Limites: grade assinada até ~400 kB (planilhas muito grandes pedem para deixar só a aba dos dados);
  uma meta por projeto (meta diferente por linha é erro); vários prazos → usa o último.

## Reestruturação R1–R2 (2026-10-21)

Plano: `docs/plano/reestruturacao.md` (aprovado). ADR-0015 (visual da base) substitui a ADR-0013.

- **R1 · Moldura** — entregue:
  - [x] Tokens novos (claro/escuro) com os nomes antigos preservados + status, séries, campo editável,
    `--color-action` (botão quase preto), `--color-text-subtle`; cópia idêntica em `docs/design/tokens.css`
  - [x] IBM Plex Sans 400/600 local (OFL); Geist removida (arquivos, `@font-face`, preloads)
  - [x] Escala 12/14/16/24/32 (nada acima de 32 px), cards de raio 8 sem sombra, tabela com separador e
    cabeçalho sem faixa, controles 36 px no desktop e 44 px no celular
  - [x] Menu de 4 telas + Projetos/Histórico + Configurações (rodapé); celular com 4 telas + “Mais”
  - [x] Avisos de e-mail e de assinatura numa faixa fina que pode ser fechada
  - [x] `/app` abre o Painel; login e troca de empresa levam ao Painel
  - [ ] Telas próprias de Preencher etapas (R3), Meta e equipe e Como funciona (R5): por ora
    `/app/preencher`, `/app/meta-e-equipe` e `/app/como-funciona` redirecionam (TODO no código)
- **R2 · Painel** — entregue:
  - [x] Painel da operação (`/app`) e do projeto (`/app/projetos/<id>/painel`): frase-resumo, 5 indicadores
    (anel + 4; celular sem indicador órfão), esteira de etapas (largura ∝ tempo, cor da situação, clique
    abre a etapa, marca de hoje), tarefas × unidades, rosca com lista “atrasadas / aguardando peça”, horas
    por etapa (nome no eixo), equipe × prazo e Tabelas 1/2 clicáveis
  - [x] Contas novas só em `calc.py` (puras, testadas): `fracao_prazo_decorrida`, `fatias_da_esteira`,
    `etapas_atrasadas`, `status_visual`, `contagem_visual`, `resumo_operacao`
  - [x] ECharts 5.5.1 vendorizado (Apache-2.0 + NOTICE + LICENSE-d3), só nas páginas de painel, canvas,
    dados num bloco JSON, cores dos tokens, texto ≥ 11 px, tabela de dados em `<details>`
  - [x] Numeração duplicada (“1. 1. Preparação”) corrigida (`dashboard.rotulo_etapa`)
  - [x] Testes A/B: atalhos do menu com `?projeto=` de outra empresa → 404; painel da operação não mostra B
- Verificação: suíte SQLite completa (ver resumo da entrega); `scripts/build_assets.py --check` ok;
  capturas 375/768/1280 claro/escuro de `/app`, painel do projeto e lista de projetos (fora do repositório);
  auditoria Web Interface Guidelines nos arquivos mexidos (números de eixo em pt-BR, `touch-action`).
- Decisões a confirmar (ADR-0015): regra de “etapa atrasada” pela linha de base do prazo; prioridade das
  cores; “faltam” em cinza; operação somando projetos.
- Pendências: `charts.py` e macros SVG de `components/chart.html` sem uso no painel (remover na R9);
  `<meta name="theme-color">` (exige cor no template; resolver com token/CSS na R9); capturas em
  `docs/design/capturas/` desatualizadas; testes em PostgreSQL não rodados nesta fase (só SQLite, a pedido).

## Reestruturação R7–R8 — telas (planilha e restaurar) (2026-10-21)

- Status: entregue (telas no visual da ADR-0015). Branch `claude/r7-r8-telas`.
- **Importar** (`/app/importar`, Configurações › Planilha, botão “Importar planilha” em Projetos):
  - [x] Indicador de passos 1–2–3 (`components/steps.html`, classe `wizard`)
  - [x] Passo 1: envio com botão próprio em pt-BR (`components/field.html::file_upload`: input nativo
    escondido mas focável, rótulo vira botão, foco visível; nome do arquivo com JS); limite (2 MB, 5.000 linhas)
    dito antes; arquivo grande → 413 com a mensagem do limite e o que fazer
  - [x] Passo 2 (colunas): aba e linha de cabeçalho (“Reler a aba”), tabela coluna + 3 exemplos + select
    “Isto é…” (Etapa; Subatividade, Tempo ideal, Previstas/meta, Concluídas, % da etapa, Prazo “(opcional)”),
    sugestão já marcada, aviso do modo (simples × detalhado) e de coluna repetida/sem Etapa decidido no
    servidor (`GET /app/importar/colunas/modo`, HTMX troca só o aviso); aba sem dados avisada
    (`import_mapping.mapping_from_columns`, `mode_of`, `COLUMN_CHOICES`; o formato antigo campo → coluna
    continua aceito)
  - [x] Passo 3: prévia (modo, etapas, atividades, meta, prazo; tabela por etapa), erros por linha numa tabela
    (Linha · Coluna · Problema) com “Voltar às colunas” sem reenviar o arquivo (grade assinada)
  - [x] **Arquivo com vários projetos** (pedido do dono): regra das três abas — “Acompanhamento”, “Equipe”,
    “Como funciona” (principal) e “<Nome> - Acompanhamento/Equipe/Como funciona” (demais). Funções puras
    `importer.reference_projects`, `project_name_from_title` (A1 “Acompanhamento da Montagem – X” → “X”) e
    `parse_reference_many`; `parse_reference` mantém o comportamento de um projeto. Passo 2 lista os projetos
    (nome, etapas, atividades, meta; todos marcados; projeto com erro aparece com os erros e sem caixa),
    passo 3 prévia, confirmação cria um projeto por item numa transação. Limite do plano conferido no backend
    antes de gravar (402 com “dá para importar N: desmarque K”) e de novo em cada `create_project`.
    Rotas `POST /app/importar/projetos` e `POST /app/importar/confirmar-varios` (lista assinada com
    empresa + usuário + 1 h). Implementação própria; testada só com planilha SINTÉTICA gerada da referência
    pública (nenhum dado de cliente no repositório).
- **Exportar** (`components/export_menu.html`): menu no detalhe, no painel e no histórico do projeto
  (supervisor+): “Planilha no formato da equipe (.xlsx)” (padrão, abas sem prefixo) e “Lista simples
  (.csv/.xlsx)”. No celular o menu ocupa a largura da faixa de ações (sem rolagem lateral).
- **Restaurar** (`edicao/restore.html`): botão “Restaurar para uma data” no histórico do projeto
  (supervisor+, projeto não arquivado); campo data e hora local (fuso da empresa, `max` = agora), resumo
  antes → depois (progresso, unidades prontas, tarefas, tempo que falta), tabela por etapa e atividade
  (agora · depois · diferença), confirmação; 409 “Algo mudou desde a prévia” com a prévia nova; “Nada a
  restaurar”; lista das restaurações (voltou para, feita em, por, lançamentos) com “Desfazer restauração”
  em diálogo de confirmação; selo “restauração”/“desfaz restauração” nas linhas do histórico, sem “Desfazer”.
- Testes: `tests/test_r7_varios_projetos.py` (9: regra das três abas, nome pelo título, um resultado por
  projeto, planilha de um projeto igual, projeto com erro, escolher e importar, limite do plano no lote,
  operador 403, “quero escolher as colunas”); `test_isolation.py`: aviso do modo não lê dados (A/B) e
  recusa operador, lista de vários projetos assinada para B recusada nas duas rotas; testes de tela de
  `test_r7_planilha.py`, `test_fase4_routes.py` e `test_r8_restaurar.py` ajustados aos textos novos.
  Suíte completa em SQLite (PostgreSQL não rodado, a pedido).
- Verificação: fluxo real com playwright-cli num servidor local (SQLite próprio): planilha “Fase/Item/
  Minutos/Feitas” (modo detalhado), “Etapa/%” (modo simples), planilha com erros, aba sem dados, arquivo
  de 3 MB, arquivo sintético com 3 projetos (importados 2); exportação aberta e recalculada no LibreOffice
  sem erro; restaurar, 409 com duas abas, nada a restaurar e desfazer. Capturas 375/768/1280 claro/escuro
  fora do repositório. Auditoria Web Interface Guidelines nos arquivos mexidos (rótulo específico no
  passo 1, `autocomplete="off"`, foco/hover no resumo dos projetos, numeração dupla nas etapas).
- Pendências: o campo `datetime-local` segue o idioma do navegador (em navegador em inglês aparece
  mm/dd/yyyy); arquivo de vários projetos aceita até 10 projetos (teto de 30 abas da leitura); modo simples
  ainda grava 1 subatividade por etapa (TODO R4); `/security-review` não rodado neste ambiente.

