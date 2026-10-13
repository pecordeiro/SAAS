# Controle de Produção — contexto para o Claude

## Produto
SaaS web multiempresa para acompanhar produção por etapas e atividades: progresso,
unidades concluídas, tempo restante, prazo em dias úteis, histórico e exportação.
Público: pequenas e médias indústrias de montagem. Interface em português do Brasil.

## Forma do produto
- É um SITE: páginas renderizadas no servidor (Flask + Jinja), interatividade com HTMX,
  responsivo do celular ao desktop. Não é app nativo, não é SPA, não usa React.
- Páginas públicas (início, preços, termos, privacidade) + área logada (/app).

## Stack
Python 3.12, Flask 3, SQLAlchemy 2, Alembic (Flask-Migrate), PostgreSQL 16,
Flask-Login, Flask-WTF (CSRF), Flask-Limiter, Gunicorn, pytest. Pagamento: Asaas.

## Estado atual
O repositório começou vazio. `app/`, `app/services/calc.py`, `app/tenancy.py`, testes e
migrations ainda não existem: nascem na Fase 0 do roadmap (docs/plano/roadmap.md).
Os caminhos abaixo são os alvos.

## Regras invioláveis
1. Multiempresa: toda tabela com dado de cliente tem company_id. A empresa vem da
   sessão (app/tenancy.py), nunca do formulário. Recurso de outra empresa = 404.
   Toda rota nova ganha teste de acesso cruzado A/B em tests/test_isolation.py.
2. Regras de cálculo só em app/services/calc.py (puro, sem Flask nem banco).
3. Mudança de schema só por migration Alembic revisada. Nunca db.create_all em produção.
4. Segredos só em variáveis de ambiente. Nada de chave em código, log ou commit.
5. Sem planilha como fonte de dados. Excel/CSV só para importar e exportar.
6. Cores, fontes e espaçamentos só por tokens (app/static/css/tokens.css).
   Nenhuma cor solta em template.
7. Limites de plano são checados no backend, não só escondidos na tela.
8. Assets servidos pelo próprio site (sem CDN em produção) para manter a CSP estrita.

## Comandos
- Testes: python -m pytest -q
- Banco: flask db migrate -m "..." / flask db upgrade
- Dados fictícios: flask seed-demo
- Rodar: python run.py

## Definição de pronto (toda fase)
- Testes novos e antigos verdes; teste de isolamento para cada rota nova.
- /security-review sem achado aberto.
- Telas conferidas em 375, 768 e 1280 px, tema claro e escuro.
- README e docs/plano/progresso.md atualizados; commit por fase.

## Planejamento
Plano, ADRs e progresso ficam em docs/plano/. Leia antes de começar qualquer tarefa.
Decisão fora do plano: registre um ADR e peça aprovação.
