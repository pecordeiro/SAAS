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
  - Feriados: `holidays.company_id` é NOT NULL (só feriados da empresa); feriados nacionais
    compartilhados ficam para a Fase 3 (decidir entre linha global ou seed por empresa).
  - `users.email` é `String` em minúsculas; `citext` no PostgreSQL fica para a Fase 3.
  - Rate limit em memória e sem bloqueio progressivo por conta (Fase 5/7, Redis).
  - CSP sem nonce (não há script ainda); RLS não ligado (`RLS_ENABLED`, Fase 3).
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
