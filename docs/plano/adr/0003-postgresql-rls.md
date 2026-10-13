# ADR-0003 — PostgreSQL com Row Level Security como segunda barreira

- Status: proposto · Data: 2026-10-13

## Contexto
Vazamento entre empresas é o pior incidente possível. O filtro por `company_id` na
aplicação (`tenancy.py`) é a primeira barreira; um esquecimento numa consulta basta para
vazar.

## Decisão
PostgreSQL 16 em todos os ambientes, inclusive testes (SQLite só como atalho local).
Políticas RLS em toda tabela com `company_id`:
`USING (company_id = current_setting('app.company_id', true)::uuid)`, com `FORCE ROW LEVEL
SECURITY`. Cada requisição/transação faz `SET LOCAL app.company_id`. O app conecta com papel
sem `BYPASSRLS`; migrations e jobs de plataforma usam papel separado.
As políticas nascem na migration da fase 3 e são ligadas pela flag `RLS_ENABLED`. Se
atrapalhar o MVP, ficam prontas e desligadas, sem mudar o resto.

## Consequências
- (+) Erro na aplicação não vaza dados; testes A/B rodam com RLS ligado.
- (−) Jobs entre empresas (reconciliação, LGPD) precisam do papel de plataforma e auditoria.
- (−) Pool de conexões exige `SET LOCAL` por transação (nunca `SET` de sessão).

## Alternativas
Schema por empresa (migrations N vezes, não escala para muitos clientes pequenos); banco por
empresa (caro). Rejeitadas.
