# Limpeza (R9): o que ficou em dúvida e por quê

Levantamento da R9 (mapa do Graphify em `app/` + varredura por texto de templates, macros, classes CSS,
rotas, funções de serviço e dependências). Aqui está só o que **não** foi removido e merece decisão.
O que saiu está em `docs/plano/progresso.md` (seção "Reestruturação R9").

## Telas antigas que ainda têm uso

| O quê | Por que ficou | O que decidir |
|---|---|---|
| `app.project_detail` (`/app/projetos/<id>`), `app/project_detail.html` e `app/detail/*` | É o destino de ~25 links (lista de projetos, esteira do Painel, alertas, e-mails, redirecionamentos) e hospeda o registro de peças (`activity_progress`, folha/stepper), aguardando peça, fotos, comentários, checklist, unidades e quadro Pessoas. O Preencher etapas cobre progresso e estrutura, **não** esses módulos. | Quando os módulos opcionais ganharem tela própria (ou entrarem no Preencher), migrar os links e remover. |
| `edicao.project_edit` (`/app/projetos/<id>/editar`) e `edicao/project_edit.html` | Único lugar que edita os dados do projeto (nome, quantidade, prazo, pessoas, horas/dia, responsável), reordena etapas/atividades por arrastar (`arrastar.js`) e arquiva/duplica. O Preencher etapas renomeia, move e exclui, mas não edita esses campos. Usado por testes (`test_etapa_d.py`, `test_fase4_routes.py`). | Mover os campos do projeto para "Meta e equipe"/Preencher; só então remover a tela, `arrastar.js` e `edicao.stage_move/activity_move/stages_reorder`. |
| `edicao.project_compare` / `project_apply_template`, `edicao/compare.html` | Fluxo de comparar/aplicar versão do modelo; sem equivalente no front novo. | Manter enquanto houver modelos versionados. |
| `app.project_refresh`, `app.activity_preview`, `app.projects_export` | Chamados por JS/HTMX da tela de detalhe (`data-refresh-url`, prévia do stepper) e pelo menu de projetos. Saem junto com `project_detail`. | Idem acima. |
| `app.project_history`, `app.project_people`, `app.project_dashboard` | Têm link e teste; são telas vivas (Histórico do projeto, aba Pessoas, Painel do projeto). | Nenhuma. |
| `app.activity_detail` (`/app/atividades/<id>`) | Sem link na interface, mas é a URL que o e-mail de atribuição usa (`services/notifications.py`). Redireciona para o detalhe. | Remover só junto com o `project_detail` e trocar o link do e-mail. |

## Componentes e estilos

| O quê | Por que ficou |
|---|---|
| `components/chart.html` (`bar_chart`, `gauge`) e `services/charts.py::medidor` | Ainda renderizam o anel do Painel (`kpi_strip`), "Peças por pessoa", "Peças por dia" (Histórico), gráficos do detalhe do projeto e `/estilo`. Saem quando essas telas migrarem para ECharts. |
| Classes CSS montadas por nome dinâmico (`legend__swatch--*`, `chart-tip__dot--*`, `esteira__bloco--*`, `status-tag--*`, `pend__dot--*`, `prazo-text--*`, `kpi__sub--*`, `badge--*`, `alert--*`, `btn--*`, `icon--*`, `progress--*`, `stepper--*`) | O nome vem de variável no template ou no JS; a varredura por texto não prova que variante não é usada. Mantidas. |
| `.htmx-request`, `.site--marca` | Classes colocadas pelo htmx e pelo `<body>` do site público. |
| `static/css/estilo.css` e `dev/estilo.html` (`/estilo`) | Guia de estilo só em `development`, coberto por `test_visual.py`. |
| `tokens.css` e `docs/design/tokens.css` | Fora do escopo da limpeza (regra do pedido). |
| `calc.contagem_status`, `importer.parse_csv` | Sem chamada no app, mas são exercidas por testes de paridade/importação (`test_calc.py`, `test_fase4_services.py`). `calc.py` é a referência da planilha. |
| Validadores `validate_*` de `forms.py`, `User.get_id`, `_get_file_stream` | Chamados por convenção do framework (WTForms, Flask-Login, Werkzeug). |
| `billing/documents.mask_document`, `billing/fake.payments_of` | Cobrança está fora do escopo da limpeza. |
| `requirements*.txt` | Nenhuma dependência sem uso: `defusedxml` é usada pelo openpyxl (teste de segurança), `psycopg` e `gunicorn` são carregados por configuração, `pytest-cov` pelo CI. |
