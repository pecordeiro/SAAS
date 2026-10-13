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

## Alternativas
Schema por empresa (migrations N vezes, não escala para muitos clientes pequenos); banco por
empresa (caro). Rejeitadas. Ligar o RLS dentro da própria migration (sempre ativo) foi
descartado nesta fase: quebraria os fluxos entre empresas ainda não desenhados (itens acima).
