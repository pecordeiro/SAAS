# Benchmark de padrões (2026-10-28)

**Limite:** nenhuma das páginas de referência abriu nesta sessão (a rede do ambiente bloqueou Stripe, Grafana,
Vercel, Atlassian, Carbon e IBM). Os padrões abaixo vêm de conhecimento prévio desses produtos e sistemas, não de
uma inspeção feita agora; cada um foi conferido só contra as telas reais da Teroz. Para revisar ao vivo, liberar os
domínios nas configurações de rede do ambiente.

| Referência | Padrão | Problema que resolve | Para a Teroz | Risco de copiar | Decisão |
|---|---|---|---|---|---|
| Stripe Dashboard | Página inicial com poucos números e a atividade recente; o detalhe fica dentro do recurso | primeira tela que responde "como estamos" sem afogar | Painel da operação com 4 indicadores e a lista; gráficos ficam no painel do projeto | números de negócio financeiro não são os da fábrica | **adotado** |
| Stripe Dashboard | Situação como etiqueta curta na linha da tabela | ler o estado sem abrir o item | etiquetas de situação nas etapas e no "Precisa de atenção" | etiqueta em todo texto vira ruído | **adotado** (só situação) |
| Grafana | O painel conta uma história: o mais importante no alto, à esquerda | ordem de leitura | progresso em destaque, depois atenção, depois lista | — | **adotado** |
| Grafana | Link do painel para o detalhe (drill-down) | ir do sintoma à causa | pendência → etapa em Preencher etapas; projeto → painel do projeto | — | **adotado** |
| Grafana | Evitar excesso de painéis | gráficos que repetem a tabela | 4 gráficos saíram do Painel da operação | — | **adotado** |
| Grafana | Variáveis e filtros no topo | muitos dados | a Teroz tem poucos projetos por empresa e já tem abas de projeto | complexidade sem ganho | **descartado** |
| Vercel Geist | Tokens de cor e tipografia com contraste alto e foco visível | consistência | tokens da Teroz (oliva, ADR-0018) e anel de foco | trocar a identidade | **adaptado** (só o princípio) |
| Vercel Geist | Fonte monoespaçada para dados | alinhar números | números tabulares da própria DM Sans | mono deixa a tela genérica | **descartado** |
| Atlassian | Edição no lugar com estado de salvamento e erro junto ao campo | autosave ambíguo | "Salvo · quem, hora", erro no campo e na linha de status (F-04) | — | **adotado** |
| Atlassian | Ações raras no menu "…" da linha | tabela com botões demais | menus só no modo Configurar | esconder ação frequente | **adotado** |
| Carbon / IBM | Poucos KPIs, uma cor por série, cores de situação estáveis | painel colorido demais | 4 indicadores; `--color-status-*` iguais em barra, rosca e etiqueta; oliva nunca colore dado | — | **adotado** |
| Carbon / IBM | Tabela de dados equivalente a cada gráfico | acessibilidade e leitura exata | `<details>` com a tabela em cada gráfico do painel do projeto | — | **mantido** (já existia) |
| CFPB | Perguntar se uma frase ou tabela não basta | gráfico decorativo | teste das quatro perguntas (seção 5 do redesign) | — | **adotado** |
