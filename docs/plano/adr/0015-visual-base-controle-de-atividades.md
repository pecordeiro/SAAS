# ADR-0015 — Visual da base “Controle de Atividades” (substitui a ADR-0013)

- Nota: **fonte, cor e formas superadas pela ADR-0018** (densidade e eficiência continuam).
- Status: **aceito** junto com o plano de reestruturação (`docs/plano/reestruturacao.md` §5, aprovado em
  2026-10-21); aplicado na fase R1. Substitui a ADR-0013 (“Prumo Noturno”).

## Contexto
O dono pediu que a base visual e de organização seja o painel antigo (Controle de Atividades:
`sistema/index.html` e as capturas em `docs/referencia/painel-antigo/`). O site estava poluído: letras
gigantes (KPI de 48 px), tudo monocromático, âmbar para “em andamento”, fonte “com cara de IA” (Geist),
tabelas sem separador e controles de 44 px no desktop.

## Decisão
1. **Tokens** (`app/static/css/tokens.css`, cópia idêntica em `docs/design/tokens.css`): os nomes
   existentes ficam (templates e macros não quebram); mudam os valores e entram tokens novos:
   - paleta do painel antigo: fundo `#F3F2F1`, superfície `#FFFFFF`, linha `#E6E4DF`, texto
     `#0B0B0B` / `#52514E` / `#6B6A66` (`--color-text-subtle`, novo);
   - status (`--color-status-done|doing|todo|waiting|late`): verde `#1F8A3B`, azul `#2A78D6`, cinza
     `#C9C7C1`, amarelo `#FAB219`, vermelho `#D03B3B`;
   - séries de gráfico: `--color-series-tasks` azul `#2A78D6` (pelas tarefas) e `--color-series-units`
     laranja `#EB6834` (unidades), sempre com o mesmo significado;
   - campo editável `--color-editable` `#FFF9DB` (para a R3);
   - botão principal quase preto (`--color-action` `#1A1A19`), sem brilho (`--shadow-primary: none`);
   - links e foco em azul escurecido `#1F66BD` (5,7:1 sobre branco); textos de sucesso/erro
     escurecidos até 4,5:1;
   - tema escuro: a paleta escura da base (`#0D0D0D` / `#1A1A19`), com o cinza terciário clareado para
     `#9A998F` (6,1:1) e links `#6AA5EE`.
2. **Fonte:** IBM Plex Sans servida pelo próprio site (OFL). Só há os arquivos 400 e 600 (vieram do
   histórico do git): 500 cai no 400 e 700 no 600 (o `@font-face` do 600 cobre 600–700, sem negrito
   sintético). Sai a Geist.
3. **Escala:** 12 px (rótulos, eixos), 14 px (corpo, tabela, menu), 16 px (título de card), 24 px
   (título da página e valor de indicador), 32 px (só o número de progresso). Nada acima de 32 px.
   Unidade do número menor, cinza e sem quebra (“92,7 h”).
4. **Densidade:** cards com raio 8 px, borda de 1 px e sem sombra; tabela com separador de linha,
   cabeçalho sem faixa e linhas de 40 px; controles de 36 px no desktop e 44 px no celular (os tokens
   `--control-height`/`--touch-min` mudam por `@media` dentro de `tokens.css`).
5. **Menu:** lateral claro de 220 px com as 4 telas da base (Painel, Preencher etapas, Meta e equipe,
   Como funciona), depois Projetos e Histórico; “Configurações” no rodapé agrupa Empresa, Usuários,
   Assinatura, Privacidade, Modelos, Alertas, API e Unidades. Item ativo em pílula neutra. No celular:
   navegação inferior com as 4 telas + “Mais”. Avisos (e-mail, assinatura) numa faixa fina de uma
   linha que pode ser fechada.
6. **Gráficos:** ECharts 5.5.1 vendorizado em `app/static/vendor/echarts-5.5.1/` (Apache-2.0, LICENSE,
   NOTICE e LICENSE-d3 junto), carregado só nas páginas de painel, renderizador canvas. Dados num
   `<script type="application/json">` gerado pelo servidor; o JS só desenha, com cores lidas dos tokens.
   Tooltip só com classes (a CSP bloqueia `style=` em HTML). Texto de gráfico ≥ 11 px; nomes das etapas
   no eixo; tabela de dados em `<details>` como alternativa ao passar o mouse.

## Decisões tomadas na R2 (a confirmar pelo dono)
- **Etapa atrasada** (o plano pede a cor, mas não define a regra): as etapas, em ordem, ocupam o prazo
  (início → prazo, em dias úteis) proporcionalmente ao tempo — a mesma divisão da esteira. Se a faixa
  da etapa terminou antes da fração do prazo que já passou e ela não está concluída, está atrasada.
  Sem início ou sem prazo, nada fica atrasado. Regra pura em `calc.etapas_atrasadas`.
- **Prioridade da cor:** concluída > aguardando peça > atrasada > em andamento > não iniciada.
- **Horas por etapa:** “faltam” em cinza (status “não iniciada”), não em laranja, para o laranja
  significar só “unidades”.
- **Painel da operação** soma os projetos ativos com a mesma conta do E414 (`calc.resumo_operacao`);
  “Equipe × prazo” vira, na operação, “trabalho que falta × dias úteis até o prazo” por projeto.

## Consequências
- `app/static/dist` reconstruído (`scripts/build_assets.py`, agora com `painel.js`); o ECharts não
  passa pelo dist (versão no caminho, cache longo em `vendor/`).
- `tests/test_visual.py` aceita só o bloco `application/json` como `<script>` sem `src`.
- `charts.py` (geometria SVG da Etapa E) e as macros de gráfico SVG de `components/chart.html` deixam
  de ser usadas no painel; a remoção fica para a R9 (o histórico e a tela de pessoas ainda usam
  `bar_chart`).
- Capturas antigas em `docs/design/capturas/` ficam desatualizadas; as da R1–R2 foram geradas fora do
  repositório.
