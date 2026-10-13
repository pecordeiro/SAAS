# ADR-0008 — Design system em documento + tokens, sem o Claude Design

- Status: proposto, aguarda aprovação · Data: 2026-10-13

## Contexto
O roadmap prevê a Fase 1 (identidade visual, design system e telas) no Claude Design, com
handoff para o Claude Code. O Claude Design não está disponível neste ambiente. A Fase 2
(base visual no código) precisa de nomes de tokens estáveis, componentes especificados e
telas definidas em 375 e 1280 px para começar.

## Decisão
Produzir a Fase 1 como arquivos versionados em `docs/design/`:
- `marca.md` (3 direções, recomendada “Prumo” com nome provisório “Controle de Produção”);
- `logo.svg`, `favicon.svg`, `og-image.svg` desenhados à mão, só com cores da paleta;
- `tokens.css` com todas as variáveis (cores claro/escuro, tipografia, espaçamento 4 px,
  raios, sombras, foco, alvo de toque, breakpoints documentados), copiado para
  `app/static/css/tokens.css` na Fase 2;
- `contraste.md` com o cálculo WCAG 2.1 de todos os pares e o script para refazê-lo;
- `design-system.md` (componentes, variantes, estados, tokens) e `telas.md` (wireframes
  ASCII em 375/1280 px, hierarquia, dados fictícios genéricos).

Os **nomes dos tokens** (`--color-*`, `--font-*`, `--space-1..12`, `--radius-*`,
`--shadow-*`, `--focus-*`, `--touch-*`, etc.) são o contrato com o código.

## Consequências
- (+) A Fase 2 começa sem esperar ferramenta; tudo revisável em diff, no mesmo repositório.
- (+) Contraste verificado por cálculo reproduzível, não por inspeção visual.
- (−) Não há protótipo clicável: o critério “registrar peças em ≤ 2 toques no protótipo de
  375 px” passa a ser demonstrado na tela real da Fase 2 (captura/Playwright).
- (−) Wireframes em texto comunicam estrutura, não acabamento visual; o acabamento é
  conferido nas capturas da Fase 2.
- (~) O design pode ser **refeito no Claude Design depois**, quando disponível, **mantendo os
  nomes de tokens**: trocar valores em `tokens.css` não exige mudar templates nem macros.

## Alternativas
- Esperar o Claude Design: bloqueia as fases 2 em diante.
- Começar a Fase 2 sem design system: gera cores e espaçamentos soltos e retrabalho,
  violando a regra 6 do `CLAUDE.md`.
- Ferramenta externa (Figma etc.): fora do repositório, sem diff e com licença/conta à parte.
