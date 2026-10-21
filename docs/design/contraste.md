# Contraste — verificação WCAG 2.1

## Revisão de 2026-10-21 — base “Controle de Atividades” (ADR-0015)

Os valores abaixo valem a partir da R1; a análise da “Prumo Noturno” logo depois fica como histórico.

| Tema | Par | Razão | Critério |
|---|---|---|---|
| Claro | `--color-text` sobre `--color-surface` | 19,68:1 | texto |
| Claro | `--color-text-muted` sobre `--color-surface` | 7,94:1 | texto |
| Claro | `--color-text-subtle` sobre `--color-bg` (pior caso) | 4,84:1 | texto |
| Claro | `--color-primary` sobre `--color-primary-subtle` | 5,04:1 | texto |
| Claro | `--color-success` sobre `--color-success-subtle` | 4,79:1 | texto |
| Claro | `--color-danger` sobre `--color-danger-subtle` | 5,29:1 | texto |
| Claro | `--color-warning` sobre `--color-warning-subtle` | 5,49:1 | texto |
| Claro | `--color-editable-text` sobre `--color-editable` | 6,26:1 | texto |
| Claro | `--color-border` sobre `--color-surface` | 3,50:1 | UI |
| Claro | `--color-action-contrast` sobre `--color-action` | 17,42:1 | texto |
| Escuro | `--color-text-muted` sobre `--color-surface` | 9,72:1 | texto |
| Escuro | `--color-text-subtle` sobre `--color-surface-2` (pior caso) | 5,56:1 | texto |
| Escuro | `--color-primary` sobre `--color-primary-subtle` | 4,53:1 | texto |
| Escuro | `--color-border` sobre `--color-surface` | 3,99:1 | UI |
| Escuro | `--color-action-contrast` sobre `--color-action` | 17,38:1 | texto |

Cores de status e de série são **marcas de dado**, nunca texto. Azul/laranja das séries passam no
validador de daltonismo da skill `dataviz` (ΔE CVD 24,7 claro / 24,3 escuro). Cinza “não iniciada” e
amarelo “aguardando peça” ficam abaixo de 3:1 sobre o branco (são cores pedidas pelo plano): por isso
a situação sempre aparece também em texto (legenda com contagem, lista, tabela de dados, título do bloco).

Status: recalculado em 2026-10-15 para a identidade “Prumo Noturno” (claro e arejado, azul ação) ·
Fonte dos valores: `tokens.css`

Método: luminância relativa WCAG 2.1 (sRGB linearizado: `c/12,92` se `c ≤ 0,04045`, senão
`((c+0,055)/1,055)^2,4`; `L = 0,2126R + 0,7152G + 0,0722B`) e razão `(L1+0,05)/(L2+0,05)`.

Critérios:
- Texto normal: **≥ 4,5:1** (1.4.3), exigido mesmo em tamanho grande.
- Componentes de UI e gráficos (bordas de campo, anel de foco, barra de progresso): **≥ 3:1** (1.4.11).
- `--color-border-subtle` é só divisória decorativa (não identifica componente); estado
  desabilitado é isento pela WCAG.

Decisões desta revisão:
- Primária azul `#2759F0` (5,57:1 sobre branco); o hover escurece para `#1A43C4`.
- `--color-success` `#0E6B3C` e `--color-danger` `#B3261E` escurecidos até passar 4,5:1 também
  sobre os fundos suaves dos selos.
- `--color-accent` laranja `#D9731A` é só **segunda série de gráfico** (nunca texto). As quatro
  cores de série (azul, laranja, verde-azulado, roxo) foram validadas para daltonismo na
  prototipação; texto e rótulos sempre acompanham a cor.
- Anel de foco na mesma cor da primária: o vão de 2 px na cor do fundo o separa do botão azul.

## Pior par por tema

| Tema | Critério | Pior par | Razão |
|---|---|---|---|
| Claro | texto ≥ 4,5 | `--color-primary` sobre `--color-primary-subtle` | 4.87:1 |
| Claro | UI ≥ 3 | `--color-border` sobre `--color-surface-2` | 3.03:1 |
| Escuro | texto ≥ 4,5 | `--color-primary` sobre `--color-primary-subtle` | 6.13:1 |
| Escuro | UI ≥ 3 | `--color-border` sobre `--color-surface-2` | 3.58:1 |

## Todos os pares

### Tema claro

| Par | Razão | Critério |
|---|---|---|
| `--color-text` sobre `--color-bg` | 16.00:1 | texto ≥ 4,5 ok |
| `--color-text` sobre `--color-surface` | 18.13:1 | texto ≥ 4,5 ok |
| `--color-text` sobre `--color-surface-2` | 15.01:1 | texto ≥ 4,5 ok |
| `--color-text-muted` sobre `--color-bg` | 6.78:1 | texto ≥ 4,5 ok |
| `--color-text-muted` sobre `--color-surface` | 7.68:1 | texto ≥ 4,5 ok |
| `--color-text-muted` sobre `--color-surface-2` | 6.36:1 | texto ≥ 4,5 ok |
| `--color-primary` sobre `--color-surface` | 5.57:1 | texto ≥ 4,5 ok |
| `--color-primary` sobre `--color-bg` | 4.91:1 | texto ≥ 4,5 ok |
| `--color-primary-contrast` sobre `--color-primary` | 5.57:1 | texto ≥ 4,5 ok |
| `--color-primary-hover` sobre `--color-surface` | 7.94:1 | texto ≥ 4,5 ok |
| `--color-primary` sobre `--color-primary-subtle` | 4.87:1 | texto ≥ 4,5 ok |
| `--color-success` sobre `--color-success-subtle` | 5.77:1 | texto ≥ 4,5 ok |
| `--color-success` sobre `--color-surface` | 6.59:1 | texto ≥ 4,5 ok |
| `--color-warning` sobre `--color-warning-subtle` | 5.52:1 | texto ≥ 4,5 ok |
| `--color-warning` sobre `--color-surface` | 6.17:1 | texto ≥ 4,5 ok |
| `--color-danger` sobre `--color-danger-subtle` | 5.55:1 | texto ≥ 4,5 ok |
| `--color-danger` sobre `--color-surface` | 6.54:1 | texto ≥ 4,5 ok |
| `--color-danger-contrast` sobre `--color-danger` | 6.54:1 | texto ≥ 4,5 ok |
| `--color-danger-contrast` sobre `--color-danger-hover` | 8.87:1 | texto ≥ 4,5 ok |
| `--color-neutral` sobre `--color-neutral-subtle` | 6.36:1 | texto ≥ 4,5 ok |
| `--color-inverse-text` sobre `--color-inverse-surface` | 16.00:1 | texto ≥ 4,5 ok |
| `--color-border` sobre `--color-surface` | 3.66:1 | UI ≥ 3 ok |
| `--color-border` sobre `--color-bg` | 3.23:1 | UI ≥ 3 ok |
| `--color-border` sobre `--color-surface-2` | 3.03:1 | UI ≥ 3 ok |
| `--color-focus` sobre `--color-bg` | 4.91:1 | UI ≥ 3 ok |
| `--color-focus` sobre `--color-surface` | 5.57:1 | UI ≥ 3 ok |
| `--color-primary` sobre `--color-track` | 4.31:1 | UI ≥ 3 ok |

### Tema escuro

| Par | Razão | Critério |
|---|---|---|
| `--color-text` sobre `--color-bg` | 16.93:1 | texto ≥ 4,5 ok |
| `--color-text` sobre `--color-surface` | 15.42:1 | texto ≥ 4,5 ok |
| `--color-text` sobre `--color-surface-2` | 13.64:1 | texto ≥ 4,5 ok |
| `--color-text-muted` sobre `--color-bg` | 8.53:1 | texto ≥ 4,5 ok |
| `--color-text-muted` sobre `--color-surface` | 7.77:1 | texto ≥ 4,5 ok |
| `--color-text-muted` sobre `--color-surface-2` | 6.87:1 | texto ≥ 4,5 ok |
| `--color-primary` sobre `--color-surface` | 7.49:1 | texto ≥ 4,5 ok |
| `--color-primary` sobre `--color-bg` | 8.22:1 | texto ≥ 4,5 ok |
| `--color-primary-contrast` sobre `--color-primary` | 8.22:1 | texto ≥ 4,5 ok |
| `--color-primary-hover` sobre `--color-surface` | 9.80:1 | texto ≥ 4,5 ok |
| `--color-primary` sobre `--color-primary-subtle` | 6.13:1 | texto ≥ 4,5 ok |
| `--color-success` sobre `--color-success-subtle` | 6.88:1 | texto ≥ 4,5 ok |
| `--color-success` sobre `--color-surface` | 8.46:1 | texto ≥ 4,5 ok |
| `--color-warning` sobre `--color-warning-subtle` | 8.20:1 | texto ≥ 4,5 ok |
| `--color-warning` sobre `--color-surface` | 9.74:1 | texto ≥ 4,5 ok |
| `--color-danger` sobre `--color-danger-subtle` | 6.86:1 | texto ≥ 4,5 ok |
| `--color-danger` sobre `--color-surface` | 7.66:1 | texto ≥ 4,5 ok |
| `--color-danger-contrast` sobre `--color-danger` | 8.41:1 | texto ≥ 4,5 ok |
| `--color-danger-contrast` sobre `--color-danger-hover` | 10.17:1 | texto ≥ 4,5 ok |
| `--color-neutral` sobre `--color-neutral-subtle` | 6.20:1 | texto ≥ 4,5 ok |
| `--color-inverse-text` sobre `--color-inverse-surface` | 16.93:1 | texto ≥ 4,5 ok |
| `--color-border` sobre `--color-surface` | 4.04:1 | UI ≥ 3 ok |
| `--color-border` sobre `--color-bg` | 4.44:1 | UI ≥ 3 ok |
| `--color-border` sobre `--color-surface-2` | 3.58:1 | UI ≥ 3 ok |
| `--color-focus` sobre `--color-bg` | 8.22:1 | UI ≥ 3 ok |
| `--color-focus` sobre `--color-surface` | 7.49:1 | UI ≥ 3 ok |
| `--color-primary` sobre `--color-track` | 5.65:1 | UI ≥ 3 ok |
