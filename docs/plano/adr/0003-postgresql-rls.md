# ADR-0003 — PostgreSQL com Row Level Security como segunda barreira

- Status: aceito (Fase 3) · Proposto: 2026-10-13 · Decisão final: 2026-10-13

## Contexto
Vazamento entre empresas é o pior incidente possível. O filtro por `company_id` na
aplicação (`tenancy.py`) é a primeira barreira; um esquecimento numa consulta basta para
vazar.

## Decisão
PostgreSQL 16 em todos os ambientes, inclusive testes (SQLite só como atalho local).
Políticas RLS em toda tabela com dado de cliente, **prontas e ligáveis, desligadas por
padrão**.

Como ficou na Fase 3:

1. **Políticas** (migration `b3e9f1a2c4d5`, só no PostgreSQL), nas 17 tabelas de
   `app/rls.py::RLS_TABLES` (toda tabela com `company_id NOT NULL` + `holidays`):
   - `tenant_isolation` (ler e gravar):
     `company_id = NULLIF(current_setting('app.company_id', true), '')::uuid`.
     O `NULLIF` é necessário: depois do primeiro `SET LOCAL` na conexão, a variável volta a
     `''` (não a NULL) e `''::uuid` daria erro.
   - `memberships_own_user` (só SELECT): `user_id = app.user_id` — o login precisa achar os
     vínculos do usuário antes de existir empresa ativa.
   - `holidays_national_read` (só SELECT): `company_id IS NULL` (feriados nacionais).
     Gravar continua restrito à própria empresa.
2. **Contexto por transação**: com `RLS_ENABLED=1`, o evento `after_begin` do `db.session`
   executa `set_config('app.company_id', …, true)` e `set_config('app.user_id', …, true)`
   (equivalentes a `SET LOCAL`) no início de **cada** transação, com os valores que
   `tenancy.py` validou (empresa só depois de conferir o vínculo ativo; nunca valor do
   formulário). Se a transação já está aberta quando o contexto muda, aplica na hora.
   `SET LOCAL` some no commit/rollback: conexão devolvida ao pool não carrega empresa.
3. **Cobrança**: `ENABLE` + `FORCE ROW LEVEL SECURITY` por `flask rls enable` (recusa sem
   `RLS_ENABLED=1`, para não deixar o app “cego”); `flask rls disable` desliga sem apagar as
   políticas; `flask rls status` mostra tabela a tabela e avisa se o papel atual ignora RLS.
   `FORCE` faz o RLS valer até para o dono das tabelas (no Render o app conecta com o
   próprio dono).
4. **Papel do banco**: RLS não vale para superusuário nem para papel com `BYPASSRLS`. O app
   precisa conectar com papel comum. No docker-compose o usuário `controle` é superusuário
   (conveniência de dev) — lá o RLS não tem efeito.
5. **Ordem para ligar em um ambiente**: (a) `RLS_ENABLED=1` no app e deploy (inofensivo:
   só passa a informar a empresa); (b) `flask seed-holidays` dos anos necessários;
   (c) `RLS_ENABLED=1 flask rls enable` com o papel dono; (d) `flask rls status`.

Testes (`tests/test_rls.py`, só com `TEST_DATABASE_URL` em PostgreSQL): criam um papel
`LOGIN NOSUPERUSER NOBYPASSRLS` só com DML, ligam o RLS e provam que consulta crua sem
`app.company_id` volta 0 linhas em todas as 17 tabelas; com a empresa A, só linhas de A;
gravar/alterar/apagar linha de B falha ou afeta 0 linhas; `SET LOCAL` não vaza para a
transação seguinte; ORM sem filtro fica na empresa do contexto; e os mesmos casos A/B de
`tests/test_isolation.py`, cadastro e registro de peças passam com o app inteiro rodando
como esse papel e `RLS_ENABLED=1`.

## Consequências
- (+) Erro na aplicação não vaza dados quando ligado; isolamento A/B testado com RLS ativo.
- (+) Ligar/desligar é operação de um comando, sem migration, e não muda o resto do código.
- (−) Tarefas entre empresas precisam de papel de plataforma com `BYPASSRLS` (ou rodar
  antes do `flask rls enable`): gravar feriados nacionais (`flask seed-holidays`), worker
  do outbox (`domain_events` de todas as empresas), reconciliação do Asaas e webhooks
  (achar a assinatura pelo id do provedor), aceitar convite e autenticar token da API
  (busca por `token_hash` antes de saber a empresa), apagamento LGPD. Cada fluxo desses
  decide na sua fase entre papel de plataforma ou função `SECURITY DEFINER` estreita.
- (−) Pool de conexões exige `SET LOCAL` por transação (nunca `SET` de sessão) — feito pelo
  hook; código que abrir conexão fora do `db.session` precisa chamar o mesmo `set_config`.

## Atualização da Fase 7 — fluxos entre empresas (papel de plataforma)

Decisão: **nenhum fluxo do app usa papel com `BYPASSRLS`**. Cada fluxo que começa antes de
saber a empresa ganha uma política SELECT estreita, ligada a um segredo que só quem tem o
direito conhece, ou roda empresa a empresa no próprio contexto.

| Fluxo | Caminho | Onde |
|---|---|---|
| Aceitar convite | política `invitations_by_token` (`token_hash = app.token_hash`) | migration `4d8a644d753b`, Fase 5 |
| Autenticar token da API | política `api_tokens_by_token` (mesmo padrão); depois `app.company_id` = empresa do token | migration `228fffa5a2d8`, `services/api_tokens.py::find_by_raw`; `tests/test_rls.py::test_token_da_api_autentica_com_rls_forcado_so_pelo_hash` |
| Login (vínculos do usuário) | `memberships_own_user` | Fase 3 |
| Exportação LGPD | contexto da empresa da sessão (rota comum) | `tests/test_rls.py::test_lgpd_exportar_e_expurgar_com_rls_forcado` |
| Expurgo LGPD | contexto da empresa expurgada para apagar; para saber se um usuário tem vínculo em OUTRA empresa usa `memberships_own_user` (contexto de usuário) — nunca apaga quem ainda pertence a outra empresa | `services/lgpd.py::purge_company`; mesmo teste |
| Retenção, suporte (`flask suporte ...`) | laço por empresa (`companies` não tem RLS), `set_context(company_id=…)` em cada uma e `flush` dentro do contexto | `services/lgpd.py::apply_retention`, `services/support.py`; `test_retencao_e_suporte_com_rls_forcado` |
| Worker do outbox (Fase 8) | mesmo laço por empresa (o índice parcial `ix_domain_events_unpublished` continua útil por empresa) **ou** papel de plataforma dedicado só ao worker | a decidir na Fase 8 |
| Webhook/reconciliação do Asaas (Fase 8) | política estreita `subscriptions_provider_lookup` (SELECT só da linha cujo `provider_subscription_id` = `app.billing_lookup`); depois grava no contexto da empresa achada | migration `d8b2e6f4a1c7` (Fase 8) |
| `flask seed-holidays` (nacionais, `company_id` NULL) | rodar com o papel dono **antes** de `flask rls enable` ou com papel de plataforma no deploy | Fase 10 (runbook) |

Por que não `SECURITY DEFINER`: com `FORCE ROW LEVEL SECURITY` (necessário porque no Render
o app conecta como dono das tabelas) o RLS vale também para o dono da função; a função só
escaparia se o dono fosse superusuário ou tivesse `BYPASSRLS`, o que reintroduz o papel
privilegiado que queremos evitar. A política estreita dá a mesma garantia (só a linha cujo
hash foi apresentado; somente leitura) sem papel especial e é testada com o papel comum.

Se algum fluxo precisar mesmo de papel de plataforma (worker), ele terá: papel separado
(`controle_platform`, `BYPASSRLS`, só as tabelas necessárias), `DATABASE_URL` própria
usada só pelo processo do worker/CLI, nunca pelo processo web.

## Alternativas
Schema por empresa (migrations N vezes, não escala para muitos clientes pequenos); banco por
empresa (caro). Rejeitadas. Ligar o RLS dentro da própria migration (sempre ativo) foi
descartado nesta fase: quebraria os fluxos entre empresas ainda não desenhados (itens acima).
