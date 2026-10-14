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
