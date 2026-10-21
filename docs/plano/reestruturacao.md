# Plano de reestruturação — de volta à base do Controle de Atividades

Status: **proposta, aguarda aprovação do dono** · Data: 2026-10-21

Referências usadas: código do painel antigo (`pecordeiro/controle-de-atividades`, `sistema/server.py` e
`sistema/index.html`), capturas em `docs/referencia/painel-antigo/`, ADR-0014 (foco em etapas), uma
auditoria pelas Web Interface Guidelines da Vercel (cerca de 43 achados), uma revisão pela Taste Skill
(telas de aplicativo) e o grafo do código gerado pelo Graphify.

---

## 1. O que o dono pediu

Anotado nas conversas de 20 e 21/10:

- A base **tem que ser o Controle de Atividades**: a mesma organização de telas, o mesmo fluxo e o mesmo jeito direto.
- O produto acompanha a produção por **etapas**. O resto é **opcional, e a tela deixa claro que é opcional**.
- Hoje o site está **poluído**: muita informação junta, letras gigantes (o "h" cai para baixo do "100"),
  tudo monocromático, lista de projetos sem separação entre as linhas, fonte "com cara de IA".
- A **primeira tela é um dashboard visual da operação**, e a página flui na vertical.
- A planilha é a base de trabalho: precisa **aceitar a planilha que a pessoa já tem** e **exportar bem formatado**.
- Hoje não dá para **mover nem apagar atividades** de forma clara.
- O **log de quem mexeu** basta; **MFA** fica só como opcional.
- Falta uma função de **restaurar** (voltar a um ponto anterior).
- Nada mirabolante. Tem que ser útil e funcionar bem.

## 2. Diagnóstico

| | Base (Controle de Atividades) | SaaS hoje |
|---|---|---|
| Arquivos de tela | 1 (`index.html`, 741 linhas) | 105 templates |
| Rotas | 3 | 137 |
| Tabelas de dados | 0 (planilha) | 36 |
| Código (sem testes) | ~1.270 linhas | ~23.900 linhas |
| Telas no menu | 4 | 10 ou mais, conforme o papel |

O SaaS cresceu em funções (fotos, checklist, série, alertas, API, painel interno etc.) e cada uma ganhou
tela, botão e aviso no caminho principal. A base resolve o mesmo problema com 4 telas.

**O que a base faz melhor**, segundo as duas revisões:
- Uma faixa de 5 indicadores com 30px, a unidade menor e cinza, e nada de quebra de linha. O SaaS usa 48px, e o número compete com o título.
- Cor com significado: azul para andamento, verde para concluída, cinza para não iniciada, laranja para unidades. O SaaS usa âmbar (cor de alerta) para "em andamento" e o mesmo azul em tudo.
- A tela de **Preencher etapas** tem a lista de etapas à esquerda, com mini barras, e à direita uma tabela com **células amarelas** que salvam ao sair do campo. O SaaS tem cerca de 10 controles por atividade e páginas de 5.800px de altura.
- Texto em 14px, controles de 32px, raio de 10px. O SaaS usa 16px, 44px e raio de 20px no desktop.

**O que não copiar da base:** barra lateral escura, logo em degradê, faixa colorida em cada card,
violeta, pulso animado, gráficos por CDN, nenhum login, e só funcionar com Windows e Excel.

**Problemas sistêmicos do SaaS** (auditoria Vercel):
1. Hierarquia achatada: títulos de seção menores que o corpo; KPIs maiores que o título da página.
2. Parágrafos de explicação em todos os cards, no lugar de rótulos claros.
3. Muitos formulários por linha, ações destrutivas sem confirmação e sem aviso de alteração não salva.
4. Gráficos que dependem só de cor e de passar o mouse, com texto de 9 a 10px.
5. Conteúdo cortado em tabelas e ações que só existem no desktop.

## 3. Princípios da reestruturação

1. **A tela é a do painel antigo.** Mesmas 4 telas, mesmos nomes, mesmo fluxo. O SaaS só acrescenta
   o que a base não tinha: login, várias empresas, histórico, banco de dados e nuvem.
2. **Etapa é o núcleo.** Toda tela responde primeiro "onde está cada etapa".
3. **Opcional é opcional de verdade:** desligado por padrão, ligado em Configurações, e marcado com
   o selo "Opcional" onde aparece. Campo opcional em formulário diz "(opcional)".
4. **Menos coisa por tela.** Uma ação principal por tela, um modo de salvar por tela, e o resto num
   menu "Mais ações".
5. **Backend continua sendo a única fonte de regras** (ADR-0009). As contas continuam no `calc.py`,
   que já tem paridade com a planilha.
6. **Remover antes de acrescentar.** O que não servir é retirado do menu e do código, e não só escondido.

## 4. Produto-alvo

### 4.1 Menu (igual à base)

| Tela | O que tem |
|---|---|
| **Painel** (primeira tela) | Operação de todos os projetos, ou de um, na vertical |
| **Preencher etapas** | Lista de etapas à esquerda e tabela editável à direita |
| **Meta e equipe** | Meta, pessoas, horas por dia, e "e se mudar a equipe?" |
| **Como funciona** | Cada conta explicada com os números atuais |
| Configurações (rodapé do menu) | Empresa, pessoas, plano, módulos opcionais, planilha |

### 4.2 Painel (primeira tela), de cima para baixo

1. **Cabeçalho:** nome do projeto ou "Operação", uma frase de resumo
   (ex.: "Lote 10: termina 14/11, folga de 17 dias úteis, 3 etapas paradas"), hora da atualização e
   o botão "Preencher etapas".
2. **Faixa de 5 indicadores:** progresso geral (anel), unidades prontas, etapas concluídas,
   horas que faltam, dias úteis até o prazo.
3. **Esteira de etapas** (novo, específico do produto): uma faixa por projeto, com um bloco por
   etapa, largura proporcional ao tempo e cor do status. Clicar abre a etapa.
4. **Tarefas × unidades por etapa** (barras azul e laranja) e, ao lado, o status das etapas (rosca)
   com a lista "atrasadas / aguardando peça".
5. **Horas por etapa** (trabalhadas × faltam), com o nome da etapa no eixo.
6. **Equipe × prazo.**
7. **Tabela 1 e Tabela 2** (tarefas e unidades), linhas com separador e clique para preencher.

### 4.3 Preencher etapas

- **Esquerda:** lista de etapas com nome, % e duas mini barras. Arrastar para reordenar, com menu
  "Mover / Renomear / Excluir".
- **Direita:** tabela da etapa com as subatividades. Células amarelas editáveis (nome, tempo ideal,
  peças concluídas) que salvam ao sair do campo, com "Salvo" e quem salvou.
- Uma linha vazia no fim para adicionar subatividade.
- **Excluir** pede confirmação e pode ser desfeito pelo histórico.

### 4.4 Dois modos de lançar progresso (decisão D1)

- **Modo simples** (padrão sugerido): a pessoa lança o % da etapa direto. Sem subatividades.
- **Modo detalhado** (opcional, igual à planilha): subatividades com tempo ideal e peças
  concluídas. A etapa é calculada (a conta atual do `calc.py`).

Cada projeto escolhe o modo. Um projeto importado da planilha de referência entra no modo detalhado.

### 4.5 Módulos opcionais (desligados por padrão)

| Módulo | Estado hoje | Proposta |
|---|---|---|
| Atribuição e progresso por pessoa | pronto | opcional |
| Alertas e relatório semanal por e-mail | pronto | opcional |
| "Aguardando peça" | pronto | opcional |
| Fotos e comentários | pronto | opcional |
| Checklist de inspeção | pronto | opcional |
| Número de série por unidade | pronto | opcional |
| API | pronto, desligada | opcional (plano Empresa) |
| MFA | pronto | opcional por pessoa; obrigatório só para a equipe interna |
| Painel interno de identidade visual | pronto | fica, só para a equipe |
| Modelos de etapas | pronto | dentro de "Novo projeto", sem item de menu |

Desligado, o módulo some do menu, dos botões e das telas, e as rotas respondem 404.

### 4.6 Planilha

- **Importar qualquer planilha:** a pessoa envia o arquivo, o sistema mostra as abas e as colunas, e
  ela diz qual é etapa, subatividade (opcional), tempo (opcional), previstas e concluídas.
  Prévia com os erros, depois confirmar. O formato da planilha de referência continua sendo reconhecido sozinho.
- **Exportar no layout da base:** cabeçalho com nome e meta, um bloco por etapa com as subatividades,
  totais, Tabela 1 e Tabela 2, aba Equipe, cores e larguras de coluna. Com fórmulas, para continuar
  funcionando no Excel.

### 4.7 Restaurar

Na tela de histórico: "voltar o projeto para como estava em [data e hora]". O sistema mostra o que
vai mudar, pede confirmação e grava a restauração como um novo lançamento. Não apaga o histórico, e a
restauração também pode ser desfeita.

## 5. Direção visual

Base: o painel antigo, sem os enfeites dele. Substitui a ADR-0013 ("Prumo Noturno").

- **Fonte:** IBM Plex Sans (400, 500, 600), servida pelo próprio site. Tem cara técnica e algarismos
  alinhados. Sai a Geist.
- **Escala:** 12px (rótulos e eixos), 14px (corpo, tabela, menu), 16px (título de card), 24px
  (valores de indicador e título da página), 32px (só o número de progresso). Nada acima de 32px.
  Unidade menor, cinza e sem quebra ("92,7 h").
- **Cores:** fundo #F3F2F1, superfície #FFFFFF, linha #E6E4DF, texto #0B0B0B / #52514E / #6B6A66.
  Botão principal quase preto, sem brilho.
- **Status:**

  | Status | Cor |
  |---|---|
  | Concluída | verde #1F8A3B |
  | Em andamento | azul #2A78D6 |
  | Não iniciada | cinza #C9C7C1 |
  | Aguardando peça | amarelo #FAB219 |
  | Atrasada | vermelho #D03B3B |

- **Séries de gráfico:** "pelas tarefas" azul #2A78D6, "unidades" laranja #EB6834, sempre com o mesmo significado.
- **Campo editável:** amarelo #FFF9DB, como na planilha.
- **Densidade:** cards com raio de 8px, borda de 1px e sem sombra. Tabelas com linhas de 40px e
  separador. Controles de 32 a 36px no desktop e 44px no celular.
- **Menu lateral:** claro, com 220px de largura. Aviso de e-mail numa linha fina que pode ser fechada.
- **Gráficos:** ECharts (o mesmo da base) servido pelo próprio site, sem CDN. Texto nunca abaixo de 11px.
  Nomes das etapas no eixo. Tabela de dados como alternativa ao passar o mouse (decisão D4).
- **Tema escuro:** a paleta escura da base, com contraste corrigido.

## 6. O que fica, o que muda e o que sai

| Parte | Decisão |
|---|---|
| Login, várias empresas, isolamento A/B, RLS, LGPD, cobrança Asaas, worker, deploy | **Fica**, sem mudança de comportamento |
| `calc.py` e a paridade com a planilha | **Fica** e ganha o modo simples |
| Histórico e autoria | **Fica**, e passa a ser a base do "restaurar" |
| Telas `/app/*` | **Refeitas** nas 4 telas da base |
| Tela de edição separada (`/editar`) | **Sai**: a edição vira "Preencher etapas" |
| Gráficos em SVG do servidor (`chart.html`, `charts.py`) | **Trocados** por ECharts local |
| Identidade "Prumo Noturno" (Geist, azul) | **Sai** |
| Módulos da seção 4.5 | **Opcionais**, desligados por padrão |
| Templates, CSS e rotas sem uso depois disso | **Removidos** (o grafo do Graphify confirma o que ficou sem uso) |

## 7. Fases

Cada fase termina com testes verdes em SQLite e PostgreSQL, teste A/B para rota nova, capturas
em 375, 768 e 1280 px nos temas claro e escuro, a auditoria Vercel nas telas mexidas, e um commit.

| Fase | Entrega | Critério de pronto |
|---|---|---|
| **R0 · Decisões** | Você aprova este plano e as decisões da seção 9; ADR-0014 vira aceito; ADR-0015 de visual | Plano aprovado |
| **R1 · Moldura** | Tokens novos, IBM Plex Sans, menu de 4 telas + Configurações, aviso de e-mail compacto | Nenhuma tela antiga quebra; fonte e escala novas em todas |
| **R2 · Painel** | Painel como primeira tela, seções 1 a 7 da seção 4.2, ECharts local | Mesmos números do painel antigo com a mesma planilha (teste de paridade) |
| **R3 · Preencher etapas** | Lista + tabela editável, salvar ao sair do campo, mover, renomear, excluir com confirmação | Fluxo completo sem recarregar a página; histórico com autor |
| **R4 · Modo simples** | % direto na etapa; escolha de modo por projeto | Projeto novo usa o simples; importado da referência usa o detalhado |
| **R5 · Meta e equipe + Como funciona** | Telas iguais à base | Paridade com a aba Equipe e a aba Como funciona |
| **R6 · Opcionais** | Configurações › Módulos; selo "Opcional"; rotas desligadas respondem 404 | Empresa nova vê só o núcleo |
| **R7 · Planilha** | Importar com mapeamento de colunas; exportar no layout da base | Importa uma planilha qualquer de teste; o Excel abre a exportação com fórmulas funcionando |
| **R8 · Restaurar** | Voltar o projeto a uma data, com prévia e desfazer | Restaura e desfaz sem perder histórico |
| **R9 · Limpeza** | Remove telas, CSS e rotas sem uso; README e docs atualizados | Grafo sem nós órfãos do front antigo; suíte verde |
| **R10 · Página pública** | Início, preços e "como funciona com a sua planilha" no visual novo | Texto revisado; SEO básico |

Depois da R10 seguem os passos de lançamento que já estão em `docs/plano/lancamento.md`.

## 8. Ferramentas e onde cada uma entra

| Ferramenta | Uso | Onde |
|---|---|---|
| **Graphify** | Mapa do código antes de cada fase: o que chama o quê, o que fica sem uso | R1, R9 e antes de remover algo |
| **playwright-cli** | Navegar no site, preencher, tirar capturas em 3 larguras e 2 temas | Fim de cada fase |
| **Taste Skill** (`design-taste-frontend`) | Regras de telas de aplicativo: escala, cor nos dados, densidade | R1 a R5 |
| **web-design-guidelines** (Vercel) | Auditoria `arquivo:linha` nas telas mexidas | Fim de cada fase |
| **dataviz** | Cores, escalas e rótulos dos gráficos | R2 |
| **anthropic-skills:xlsx** | Exportação formatada com fórmulas | R7 |
| **design:ux-copy** | Textos de botões, avisos e erros | R1 a R8 |
| **design:accessibility-review** | Contraste e teclado | R1, R2, R3 |
| **awesome-design-md** | Não usado: a referência é o painel antigo | — |
| **codebase-memory-mcp** | Bloqueado pela permissão do ambiente; o Graphify cobre a mesma necessidade | — |

## 9. Decisões do dono

| # | Pergunta | Sugestão |
|---|---|---|
| D1 | Modo de progresso: simples (% na etapa), detalhado (subatividades) ou os dois | Os dois, com o simples como padrão |
| D2 | Fonte | IBM Plex Sans |
| D3 | Menu lateral claro (sugerido) ou escuro como na base | Claro |
| D4 | Gráficos: ECharts local (igual à base, interativo) ou SVG do servidor | ECharts local |
| D5 | Módulos opcionais: confirmar a lista da seção 4.5 e que tudo começa desligado | Sim |
| D6 | Restaurar: projeto a uma data (sugerido) ou empresa inteira por backup | Projeto a uma data |
| D7 | MFA: opcional por pessoa e obrigatório só para a equipe interna | Sim |
| D8 | Rótulo de unidade: "unidades" (genérico) ou "robôs" | "Unidades", com nome configurável por empresa |

## 10. Riscos

- **Tamanho da mudança:** R1 a R3 mexem em quase todas as telas. Mitigação: uma fase por vez, com testes e capturas, e o painel antigo como critério de pronto.
- **Paridade de números:** o painel precisa bater com a planilha. Mitigação: o teste de paridade do `calc.py` já existe e passa a cobrir as telas novas.
- **ECharts:** cerca de 1 MB (cerca de 350 KB compactado), carregado só no Painel. Precisa da licença Apache-2.0 junto.
- **Remover código:** só depois de o Graphify e os testes mostrarem que nada mais usa.
