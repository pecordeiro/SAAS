# Roadmap

Uma fase por sessão, na ordem. A próxima só começa quando todos os critérios de pronto da
anterior passarem e estiverem marcados em `progresso.md`. Além dos critérios próprios, toda
fase cumpre a **Definição de pronto** do `CLAUDE.md` (testes verdes, isolamento A/B para rota
nova, `/security-review` sem achado aberto, telas em 375/768/1280 claro/escuro quando houver
tela, README e progresso atualizados, commit por fase).

| Fase | Nome | Ferramenta | Depende de |
|---|---|---|---|
| 0 | Esqueleto do projeto | Claude Code | — |
| 1 | Identidade visual e telas | Claude Design | PRD |
| 2 | Base visual no código | Claude Code | 0, 1 |
| 3 | Banco de dados | Claude Code | 0 |
| 4 | Backend e regras de negócio | Claude Code | 3 |
| 5 | Login, convites e contas | Claude Code | 3 |
| 6 | Front-end completo | Claude Code | 2, 4, 5 |
| 7 | Segurança e LGPD | Claude Code | 6 |
| 8 | Assinaturas e pagamento | Claude Code | 4, 7 |
| 9 | API de publicação (reservada) | Claude Code | 4, 7 |
| 10 | Deploy e lançamento | Claude Code | 8 |

---

## Fase 0 — Esqueleto do projeto (nova; o repositório começou vazio)

Entregáveis:
- `pyproject.toml` (ou `requirements.txt` + `requirements-dev.txt`) com versões fixadas;
  `.gitignore`; `.env.example` sem valores reais; `run.py`.
- `app/__init__.py` (create_app), `config.py`, `extensions.py`; blueprints vazios `public`,
  `auth`, `app`; rota `/health`.
- Modelos mínimos: `companies`, `users`, `memberships`, `projects`, `stages`, `activities`,
  `progress_entries`, `holidays` + primeira migration Alembic.
- `app/tenancy.py` (load_company, tenant_required, scoped, get_or_404).
- `app/services/calc.py` puro: progresso, unidades concluídas, horas restantes, dias úteis,
  prazo previsto.
- Cadastro de empresa + login/logout básicos (Flask-Login, Argon2id, CSRF, rate limit em memória).
- Telas provisórias simples (sem design) para login, cadastro, projetos, detalhe, histórico,
  novo projeto e erro — serão migradas na fase 2.
- `flask seed-demo`; `tests/` com conftest (SQLite agora, Postgres na fase 3);
  `tests/test_calc.py`, `tests/test_isolation.py`; GitHub Actions rodando pytest.

Critérios de pronto:
- [ ] `python -m pytest -q` verde no CI e localmente.
- [ ] `test_calc.py` com ≥ 15 casos conferidos à mão, incluindo feriado, fim de semana,
      quantidade zero e atividade 100%.
- [ ] `calc.py` não importa `flask` nem `sqlalchemy` (teste que verifica os imports).
- [ ] Usuário da empresa A recebe 404 em GET/POST de projeto, etapa e atividade da empresa B.
- [ ] Operador recebe 403 ao criar projeto; POST sem CSRF recebe 400.
- [ ] `flask db upgrade` em banco vazio cria tudo; `/health` responde 200.

## Fase 1 — Identidade visual e telas (Claude Design)

Entregáveis: 3 direções de marca → 1 escolhida; design system salvo (tokens claro/escuro,
tipografia, espaçamento 4 px, componentes); todas as telas do Prompt 1 em 375 e 1280 px;
handoff para o Claude Code.

Critérios de pronto:
- [ ] Direção de marca aprovada por você (registrada em `progresso.md`).
- [ ] Todos os pares texto/fundo dos tokens com contraste ≥ 4,5:1 (≥ 3:1 para texto grande e
      bordas de componentes) nos dois temas.
- [ ] Logo legível em 16 px.
- [ ] Cada tela listada no Prompt 1 existe em 375 e 1280 px (checklist).
- [ ] Registrar peças demonstrado em ≤ 2 toques no protótipo de 375 px.

## Fase 2 — Base visual no código

Entregáveis: `tokens.css` com os nomes do design system; CSS próprio em camadas; fontes woff2
e HTMX servidos localmente; macros em `templates/components/`; `base_publica.html` e
`base_app.html`; telas da fase 0 migradas; `/estilo` só em development; logo, favicons e
imagem OG.

Critérios de pronto:
- [ ] Teste que varre `app/templates/` e falha se encontrar cor hexadecimal, `rgb(`, ou valor
      em `px` fora de `tokens.css`.
- [ ] Nenhuma referência a CDN em templates (teste por regex `https?://` em `<link>`/`<script>`).
- [ ] `/estilo` responde 404 com `FLASK_ENV=production`.
- [ ] Capturas (webapp-testing) de cada tela em 375/768/1280, claro e escuro; lista de
      diferenças com o handoff zerada ou justificada.
- [ ] Testes antigos verdes.

## Fase 3 — Banco de dados

Entregáveis: `docker-compose.yml` com Postgres 16; testes em Postgres via
`TEST_DATABASE_URL`; CI com serviço postgres; todas as tabelas de `arquitetura.md §4`;
índices compostos por `company_id`; CHECK/UNIQUE; políticas RLS atrás de `RLS_ENABLED`;
seed de planos; `seed-demo` atualizado; ER atualizado.

Critérios de pronto:
- [ ] `flask db upgrade` do zero → `flask db downgrade base` → `flask db upgrade` sem erro (no CI).
- [ ] Teste confirma que toda tabela com dado de cliente tem `company_id NOT NULL` e índice
      começando por `company_id` (inspeção do metadata).
- [ ] Com `RLS_ENABLED=1`, consulta crua sem `app.company_id` retorna 0 linhas (teste).
- [ ] Testes, inclusive isolamento A/B, verdes em PostgreSQL.
- [ ] `UNIQUE` em `payments.provider_payment_id` e `webhook_events.external_event_id` testados.

## Fase 4 — Backend e regras de negócio

Entregáveis: serviços de modelos versionados (snapshot, comparação e aplicação com
confirmação), edição completa (renomear, reordenar, arquivar, duplicar), importação CSV com
relatório por linha e gravação atômica, exportação CSV e XLSX, `entitlements.py`, eventos de
domínio, auditoria.

Critérios de pronto:
- [ ] Cobertura `pytest-cov` ≥ 90% em `app/services/`.
- [ ] Teste chamando a rota de criação direto (sem tela) recebe 402 ao estourar
      `max_projects`/`max_users`; empresa sem assinatura ativa recebe 402 em escrita.
- [ ] Exportar → importar o mesmo projeto produz dados iguais (teste round-trip).
- [ ] CSV com 1 linha inválida não grava nada e devolve linha, coluna e motivo.
- [ ] Célula exportada começando com `= + - @` sai neutralizada.
- [ ] Cada mudança relevante gera exatamente 1 `domain_events` na mesma transação (teste com rollback).
- [ ] Editar modelo não altera projeto existente até a confirmação.
- [ ] Isolamento A/B para cada rota/serviço novo.

## Fase 5 — Login, convites e contas

Entregáveis: `EmailSender` (console e Resend); confirmação de e-mail; recuperação de senha;
convites; gestão de membros; perfil; sessões versionadas; MFA TOTP; bloqueio progressivo;
troca de empresa.

Critérios de pronto:
- [ ] Testes de cada fluxo com token válido, expirado, reutilizado e de outra empresa.
- [ ] Pedido de reset devolve a mesma resposta e mesmo status para e-mail existente e inexistente.
- [ ] Usuário desativado é deslogado na requisição seguinte (teste).
- [ ] Último proprietário não pode ser removido nem rebaixado (teste).
- [ ] Busca no banco e nos logs capturados (caplog) não encontra nenhum token em texto puro.
- [ ] Após N tentativas erradas, login bloqueado por conta e por IP (teste).

## Fase 6 — Front-end completo

Entregáveis: site público (início, preços lidos de `plans`, termos, privacidade, contato,
SEO, sitemap, robots); todas as telas logadas; HTMX com fallback; gráficos SVG; WCAG AA;
assets minificados com hash.

Critérios de pronto:
- [ ] Playwright: cadastro → criar projeto a partir de modelo → registrar peças → histórico →
      exportar, passando em 375 e 1280 px.
- [ ] Playwright: operador tentando ações de supervisor recebe 403 e não vê os botões.
- [ ] Registrar peças funciona com JavaScript desligado (teste).
- [ ] 409 de conflito mostra valor atual e pede confirmação (teste).
- [ ] Lighthouse ≥ 90 em acessibilidade e boas práticas nas páginas públicas.
- [ ] Nenhuma requisição a outro domínio no navegador (Playwright monitora a rede).

## Fase 7 — Segurança e LGPD

Entregáveis: `seguranca.md` (STRIDE); cabeçalhos e CSP com nonce; cookies `__Host-`;
rate limit com Redis; limites de upload; pip-audit + Dependabot; logs JSON com
`request_id`; Sentry com filtro; `lgpd.md`; exportação ZIP e exclusão com carência de 30 dias;
acesso de suporte auditado; `incidentes.md`.

Critérios de pronto:
- [ ] Testes: CSP sem `unsafe-inline`, HSTS, cookies Secure/HttpOnly/SameSite, upload acima do
      limite recusado (413), rate limit devolve 429.
- [ ] Teste que lista o `url_map` e falha se rota com `<uuid>` não tiver caso A/B.
- [ ] `pip-audit` sem vulnerabilidade aberta no CI.
- [ ] Exportação LGPD gera ZIP só com dados da empresa (teste A/B).
- [ ] `/security-review` sem achado aberto.

## Fase 8 — Assinaturas e pagamento

Entregáveis: `PaymentProvider` + `AsaasProvider` + `FakeProvider`; fluxo teste grátis →
plano → dados de cobrança → checkout Asaas; webhook idempotente; estados locais e carência;
reconciliação diária; telas de assinatura e faturas; ações administrativas auditadas;
`pagamentos.md`.

Critérios de pronto:
- [ ] Testes com FakeProvider: aprovado, recusado, vencido, pago com atraso, cancelado,
      reembolso, webhook com token inválido (401), duplicado (200 sem efeito), fora de ordem.
- [ ] CPF/CNPJ inválido recusado no formulário e no serviço.
- [ ] Troca de plano muda limites na requisição seguinte (teste).
- [ ] Ciclo real no sandbox, do teste grátis ao cancelamento, documentado com prints.

## Fase 9 — API de publicação (reservada)

Entregáveis: `docs/api/openapi.yaml`; blueprint `/api/v1` atrás de `FEATURE_PUBLIC_API`;
tokens com escopo; `GET /projects` e `GET /projects/{id}/summary`; demais rotas como stubs
501; tela de tokens atrás da flag.

Critérios de pronto:
- [ ] Flag desligada: `/api/v1/*` → 404 e tela de tokens invisível (teste).
- [ ] Flag ligada: token de A não lê B (404), sem escopo → 403, revogado → 401, expirado → 401.
- [ ] `openapi.yaml` validado (openapi-spec-validator) e rotas implementadas batem com o contrato (teste).

## Fase 10 — Deploy e lançamento

Entregáveis: `render.yaml` (web, worker, Redis, Postgres) para staging e produção; pre-deploy
com migration; domínio com HTTPS e www; SPF/DKIM/DMARC; backup extra e restore testado;
monitoramento e alertas; Asaas produção; smoke tests; página de status; onboarding do piloto;
`operacao.md` com RPO/RTO e checklist go/no-go.

Critérios de pronto (go/no-go):
- [ ] Todos os itens do checklist de prontidão marcados.
- [ ] Restore em banco novo conferido e documentado (RPO ≤ 24 h, RTO ≤ 4 h).
- [ ] Isolamento A/B testado em produção com 2 empresas de teste.
- [ ] Cobrança real de valor baixo paga e estornada.
- [ ] Termos e privacidade revisados juridicamente.
- [ ] Smoke test Playwright verde em staging e produção.
- [ ] Se faltar isolamento, segredos, backup ou login em rota privada: **não lançar**.
