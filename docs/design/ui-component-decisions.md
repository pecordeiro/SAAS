# Decisões de componentes e bibliotecas (2026-10-28)

Ponto de partida: a Teroz é um site renderizado no servidor (Flask + Jinja + HTMX), sem React, com CSP estrita
(`script-src 'self' 'nonce-…'`, `style-src 'self'`) e todos os arquivos servidos pelo próprio site (regra 8 do
`CLAUDE.md`). Nenhuma dependência de execução nova entrou neste redesign.

| Candidato | Para quê | Decisão | Motivo |
|---|---|---|---|
| shadcn/ui (Blocks, Charts) | layouts de dashboard, gráficos | **descartado** | componentes React; exigiria trocar a stack |
| Tremor | cartões de KPI, listas com barras | **descartado** | React + Tailwind |
| MUI X (Data Grid, Charts) | tabelas e gráficos | **descartado** | React; partes pagas (Pro/Premium) |
| Ant Design / Pro Components | páginas densas, filtros | **descartado** | React; pacote grande |
| Radix Primitives | diálogos, menus, abas acessíveis | **descartado** | React; os equivalentes nativos bastam (abaixo) |
| Recharts | gráficos | **descartado** | React; o ECharts já resolve |
| **Apache ECharts 5.5.1** | gráficos do painel do projeto | **mantido** | já servido pelo site (`static/vendor`), canvas sem estilo inline, cores lidas dos tokens; tabela de dados equivalente em cada gráfico |
| **HTMX 2.0.4** | salvar campo sem recarregar, pedaços fora de banda | **mantido** | `allowEval:false`, `allowScriptTags:false`; respostas de erro tratadas (F-01, F-04) |
| **Lucide 0.460.0** (sprite) | ícones | **mantido** | uma família só, servida pelo site |
| `<details>`/`<summary>` nativo | "Simular o tamanho da equipe", menus "…" | **escolhido** | abre e fecha sem JS, teclado e leitor de tela de graça |
| Barra segmentada (links) | "Registrar produção / Configurar etapas" | **escolhido** | são duas URLs (`?modo=configurar`), funcionam sem JS e podem ser favoritadas; o servidor decide quem vê |
| Confirmação em folha (`.sheet` por âncora) | apagar etapa/subatividade/projeto | **mantido** | já existia, funciona sem JS, diz o impacto e como desfazer |
| `components/progress.html` (barra linear) | progresso no Painel da operação e na lista de etapas | **escolhido** no lugar de rosca e medidor | "x de y" + barra lê mais rápido que um anel (Carbon, CFPB) |
| axe-core | auditoria de acessibilidade | **só ferramenta** | usado do cache local do npm para auditar; não vai para o site |
| Pillow 13.0.0 | processar fotos enviadas | **atualizado** (de 12.3.0) | 39 vulnerabilidades conhecidas na 12.3.0 (F-02); testes de imagem verdes |

## Skills e plugins (seção 13 do prompt)

| Skill | Situação |
|---|---|
| frontend-design (Anthropic) | já instalada; usada na crítica das telas (textos, rótulos, abreviações) |
| Impeccable | **não instalada**: `impeccable.style` bloqueado e GitHub respondeu 403 pela rede do ambiente |
| Humbleteam design-review | **não instalada**: GitHub respondeu 403; no lugar, foram usadas as skills locais de crítica e de acessibilidade |
| accessibility-review (local) | usada: axe-core, teclado, alvos de toque e reflow (resultado em `redesign-2026-10-28.md` §7) |
