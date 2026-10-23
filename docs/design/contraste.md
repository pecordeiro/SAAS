# Contraste — verificação WCAG 2.1

## Revisão de 2026-10-23 — identidade oliva em todo o sistema (ADR-0018)

Os tokens semânticos (`--color-bg`, `--color-primary`, `--color-action`, `--color-focus`…) passaram a valer a
paleta oliva em toda a área logada. Texto normal ≥ 4,5:1; componentes de interface (borda de campo, foco,
séries de gráfico) ≥ 3:1. Links e foco usam o oliva/tinta, nunca o azul de “em andamento”. O azul só aparece
em dado (barra, rosca, esteira, selo “Em andamento”). Razões calculadas com a fórmula WCAG 2.1 (script
`ctr2` do histórico da ADR; reproduzível com qualquer calculadora de luminância relativa).

### Tema claro

| Par | Cores | Razão |
|---|---|---|
| texto / fundo | #14170D sobre #FBFBF6 | 17.5:1 |
| texto / superfície | #14170D sobre #FFFFFF | 18.1:1 |
| secundário / fundo | #5E6354 sobre #FBFBF6 | 6.0:1 |
| secundário / superfície-2 | #5E6354 sobre #F0F1E6 | 5.4:1 |
| sutil / fundo | #6A6F5E sobre #FBFBF6 | 5.0:1 |
| sutil / superfície | #6A6F5E sobre #FFFFFF | 5.2:1 |
| link e primary / fundo | #455A0F sobre #FBFBF6 | 7.4:1 |
| primary / superfície | #455A0F sobre #FFFFFF | 7.7:1 |
| primary / item ativo (primary-subtle) | #455A0F sobre #E4EAD0 | 6.2:1 |
| botão: branco / oliva | #FFFFFF sobre #455A0F | 7.7:1 |
| botão hover: branco / oliva-hover | #FFFFFF sobre #2E3D08 | 11.8:1 |
| borda de campo / fundo (UI ≥3) | #7C846A sobre #FBFBF6 | 3.8:1 |
| foco / fundo (UI ≥3) | #455A0F sobre #FBFBF6 | 7.4:1 |
| selo andamento: azul / subtle | #1F66BD sobre #EAF2FC | 5.0:1 |
| série neutra / superfície (UI) | #6B6A66 sobre #FFFFFF | 5.4:1 |
| sucesso / fundo | #18792F sobre #FBFBF6 | 5.3:1 |
| perigo / fundo | #B42F2F sobre #FBFBF6 | 6.0:1 |
| aviso / fundo | #8A5A00 sobre #FBFBF6 | 5.7:1 |

### Tema escuro

| Par | Cores | Razão |
|---|---|---|
| texto / fundo | #F0F3E4 sobre #0F120A | 16.8:1 |
| texto / superfície | #F0F3E4 sobre #181C10 | 15.4:1 |
| secundário / superfície | #A4AB94 sobre #181C10 | 7.3:1 |
| sutil / superfície | #99A088 sobre #181C10 | 6.4:1 |
| link e primary / fundo | #B7D064 sobre #0F120A | 11.0:1 |
| primary / superfície | #B7D064 sobre #181C10 | 10.1:1 |
| primary / item ativo | #B7D064 sobre #27301A | 8.0:1 |
| botão: tinta / oliva claro | #14170D sobre #B7D064 | 10.6:1 |
| botão hover | #14170D sobre #9DB84A | 8.1:1 |
| borda de campo / superfície (UI) | #6E7459 sobre #181C10 | 3.6:1 |
| foco / fundo (UI) | #B7D064 sobre #0F120A | 11.0:1 |
| selo andamento: azul / subtle | #6AA5EE sobre #1F3A5C | 4.5:1 |
| série neutra / superfície (UI) | #9A998F sobre #181C10 | 6.0:1 |
| sucesso / superfície | #5CC985 sobre #181C10 | 8.4:1 |
| perigo / superfície | #FF8A7F sobre #181C10 | 7.6:1 |
| aviso / superfície | #F2B755 sobre #181C10 | 9.6:1 |

Todos os pares passam. O menor é a borda de campo no tema escuro (3,6:1, componente de interface, mínimo 3:1)
e o selo “Em andamento” no escuro (4,5:1, texto, mínimo 4,5:1).

## Revisão de 2026-10-23 — marca oliva nas páginas públicas (ADR-0016)

Método e critérios abaixo (WCAG 2.1 AA). Só os pares usados nas páginas públicas.

| Tema | Par | Razão | Critério |
|---|---|---|---|
| Claro | `--color-brand-text` sobre `--color-brand-bg` | 17,47:1 | texto |
| Claro | `--color-brand-muted` sobre `--color-brand-bg` / `-surface` / `-surface-2` | 5,97 / 6,20 / 5,44:1 | texto |
| Claro | `--color-brand-subtle` sobre `--color-brand-bg` / `-surface-2` | 5,00 / 4,55:1 | texto |
| Claro | `--color-brand` sobre `--color-brand-bg` / `-surface` / `-soft` | 7,43 / 7,71 / 6,24:1 | texto (links, botão de contorno) |
| Claro | `--color-brand-contrast` sobre `--color-brand` / `-hover` | 7,71 / 11,75:1 | texto do botão |
| Claro | `--color-brand-block-text` sobre `--color-brand-block` | 6,39:1 | texto (chamada final) |
| Claro | `--color-brand-border` sobre `-bg` / `-surface` / `-surface-2` | 3,77 / 3,91 / 3,43:1 | UI |
| Escuro | `--color-brand-text` sobre `--color-brand-bg` | 16,78:1 | texto |
| Escuro | `--color-brand-muted` sobre `-bg` / `-surface` / `-surface-2` | 7,95 / 7,28 / 6,52:1 | texto |
| Escuro | `--color-brand-subtle` sobre `-surface` / `-surface-2` | 6,38 / 5,72:1 | texto |
| Escuro | `--color-brand` sobre `-bg` / `-surface` / `-soft` | 11,00 / 10,08 / 8,02:1 | texto |
| Escuro | `--color-brand-contrast` sobre `--color-brand` / `-hover` | 10,55 / 8,11:1 | texto do botão |
| Escuro | `--color-brand-block-text` sobre `--color-brand-block` | 8,40:1 | texto |
| Escuro | `--color-brand-border` sobre `-bg` / `-surface` / `-surface-2` | 3,87 / 3,55 / 3,18:1 | UI |

Regras: `--color-brand-muted` nunca sobre o bloco oliva claro (2,18:1; só `--color-brand-block-text`
vai sobre ele). `--color-brand-line` é divisória decorativa (1,25:1), sem função de identificar componente.
Cores de status do painel de exemplo seguem as regras da revisão anterior (sempre com rótulo em texto).

## Histórico — revisão de 2026-10-21 — base (valores da ADR-0015, superados pela ADR-0018 na área logada) “Controle de Atividades” (ADR-0015)

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
