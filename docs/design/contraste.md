# Contraste — verificação WCAG 2.1

Status: calculado em 2026-10-13 · Direção “Prumo” · Fonte dos valores: `tokens.css`

Método: luminância relativa WCAG 2.1 (sRGB linearizado: `c/12,92` se `c ≤ 0,04045`, senão
`((c+0,055)/1,055)^2,4`; `L = 0,2126R + 0,7152G + 0,0722B`) e razão `(L1+0,05)/(L2+0,05)`.
Calculado com o script Python no fim deste arquivo (rodado em memória, sem dependências).

Critérios:
- Texto normal: **≥ 4,5:1** (1.4.3). Todos os pares de texto foram exigidos a 4,5 mesmo
  quando usados em tamanho grande.
- Componentes de UI e gráficos (bordas de campo, anel de foco, barra de progresso, barras do
  gráfico): **≥ 3:1** (1.4.11).
- Fora do cálculo, por regra: `--color-border-subtle` é só divisória decorativa (não
  identifica componente); estado desabilitado é isento pela WCAG, mas usamos
  `--color-text-muted` + opacidade nenhuma (ver design-system.md) para continuar legível.

Ajustes feitos até passar com folga:
- `--color-border` claro: `#7C8893` → **`#727F8A`** (era 3,08:1 sobre `--color-surface-2`;
  agora 3,48:1).
- `--color-warning` claro escurecido para `#8F5300` (âmbar como texto em fundo claro só passa
  bem escuro); o âmbar vivo fica no tema escuro.
- `--color-accent` (amarelo) **proibido como texto ou ícone sobre fundo claro** (1,7:1 sobre
  branco); no claro aparece só sobre grafite (logo) ou com texto `--color-accent-contrast`.
- Anel de foco em azul `--color-focus`, distinto da primária, para não sumir sobre botão
  primário (há também o vão de 2 px na cor do fundo).

## Pior par por tema

| Tema | Critério | Pior par | Razão |
|---|---|---|---|
| Claro | texto ≥ 4,5 | `--color-success` sobre `--color-success-subtle` (selo Concluída) | 5,11:1 |
| Claro | UI ≥ 3 | `--color-border` sobre `--color-surface-2` | 3,48:1 |
| Escuro | texto ≥ 4,5 | `--color-primary` sobre `--color-primary-subtle` (menu ativo) | 6,06:1 |
| Escuro | UI ≥ 3 | `--color-border` sobre `--color-surface-2` | 3,58:1 |

## Todos os pares

### Tema claro

| Uso | Frente | Fundo | Razão | Mínimo | Resultado |
|---|---|---|---:|---:|---|
| Texto principal na página | `--color-text` #151A1F | `--color-bg` #F3F5F6 | 16.01:1 | 4.5:1 | passa |
| Texto em card/tabela | `--color-text` #151A1F | `--color-surface` #FFFFFF | 17.51:1 | 4.5:1 | passa |
| Texto em cabeçalho de tabela/linha zebrada | `--color-text` #151A1F | `--color-surface-2` #E9EDF0 | 14.87:1 | 4.5:1 | passa |
| Texto secundário na página | `--color-text-muted` #4D5964 | `--color-bg` #F3F5F6 | 6.56:1 | 4.5:1 | passa |
| Texto secundário em card | `--color-text-muted` #4D5964 | `--color-surface` #FFFFFF | 7.17:1 | 4.5:1 | passa |
| Texto secundário em surface-2 | `--color-text-muted` #4D5964 | `--color-surface-2` #E9EDF0 | 6.09:1 | 4.5:1 | passa |
| Link/botão fantasma na página | `--color-primary` #0B5D72 | `--color-bg` #F3F5F6 | 6.80:1 | 4.5:1 | passa |
| Link/botão fantasma em card | `--color-primary` #0B5D72 | `--color-surface` #FFFFFF | 7.44:1 | 4.5:1 | passa |
| Link em surface-2 | `--color-primary` #0B5D72 | `--color-surface-2` #E9EDF0 | 6.32:1 | 4.5:1 | passa |
| Link em hover | `--color-primary-hover` #084A5B | `--color-surface` #FFFFFF | 9.81:1 | 4.5:1 | passa |
| Botão primário | `--color-primary-contrast` #FFFFFF | `--color-primary` #0B5D72 | 7.44:1 | 4.5:1 | passa |
| Botão primário em hover | `--color-primary-contrast` #FFFFFF | `--color-primary-hover` #084A5B | 9.81:1 | 4.5:1 | passa |
| Item de menu ativo | `--color-primary` #0B5D72 | `--color-primary-subtle` #E1EFF3 | 6.32:1 | 4.5:1 | passa |
| Texto em destaque primário | `--color-text` #151A1F | `--color-primary-subtle` #E1EFF3 | 14.88:1 | 4.5:1 | passa |
| Texto sobre amarelo sinalização | `--color-accent-contrast` #151A1F | `--color-accent` #F2B705 | 9.63:1 | 4.5:1 | passa |
| Botão perigo | `--color-danger-contrast` #FFFFFF | `--color-danger` #B3261E | 6.54:1 | 4.5:1 | passa |
| Botão perigo em hover | `--color-danger-contrast` #FFFFFF | `--color-danger-hover` #8F1E18 | 8.87:1 | 4.5:1 | passa |
| Texto de sucesso | `--color-success` #1D7238 | `--color-surface` #FFFFFF | 5.97:1 | 4.5:1 | passa |
| Selo Concluída | `--color-success` #1D7238 | `--color-success-subtle` #E2F1E6 | 5.11:1 | 4.5:1 | passa |
| Texto de aviso | `--color-warning` #8F5300 | `--color-surface` #FFFFFF | 6.17:1 | 4.5:1 | passa |
| Selo Em andamento / alerta de aviso | `--color-warning` #8F5300 | `--color-warning-subtle` #FBEFD9 | 5.42:1 | 4.5:1 | passa |
| Mensagem de erro na página | `--color-danger` #B3261E | `--color-bg` #F3F5F6 | 5.98:1 | 4.5:1 | passa |
| Mensagem de erro de campo | `--color-danger` #B3261E | `--color-surface` #FFFFFF | 6.54:1 | 4.5:1 | passa |
| Alerta de erro | `--color-danger` #B3261E | `--color-danger-subtle` #FBE6E4 | 5.46:1 | 4.5:1 | passa |
| Texto neutro | `--color-neutral` #55616C | `--color-surface` #FFFFFF | 6.34:1 | 4.5:1 | passa |
| Selo Não iniciada | `--color-neutral` #55616C | `--color-neutral-subtle` #E9EDF0 | 5.38:1 | 4.5:1 | passa |
| Toast | `--color-inverse-text` #F3F5F6 | `--color-inverse-surface` #151A1F | 16.01:1 | 4.5:1 | passa |
| Borda de campo/botão secundário na página | `--color-border` #727F8A | `--color-bg` #F3F5F6 | 3.75:1 | 3:1 | passa |
| Borda de campo em card | `--color-border` #727F8A | `--color-surface` #FFFFFF | 4.10:1 | 3:1 | passa |
| Borda em surface-2 | `--color-border` #727F8A | `--color-surface-2` #E9EDF0 | 3.48:1 | 3:1 | passa |
| Anel de foco na página | `--color-focus` #1B5FD1 | `--color-bg` #F3F5F6 | 5.33:1 | 3:1 | passa |
| Anel de foco em card | `--color-focus` #1B5FD1 | `--color-surface` #FFFFFF | 5.83:1 | 3:1 | passa |
| Anel de foco em surface-2 | `--color-focus` #1B5FD1 | `--color-surface-2` #E9EDF0 | 4.95:1 | 3:1 | passa |
| Barra de progresso (preenchimento × trilho) | `--color-primary` #0B5D72 | `--color-track` #D5DBE0 | 5.33:1 | 3:1 | passa |
| Barra de progresso concluída | `--color-success` #1D7238 | `--color-track` #D5DBE0 | 4.28:1 | 3:1 | passa |
| Barra do gráfico × fundo do card | `--color-primary` #0B5D72 | `--color-surface` #FFFFFF | 7.44:1 | 3:1 | passa |
| Borda de campo com erro | `--color-danger` #B3261E | `--color-surface` #FFFFFF | 6.54:1 | 3:1 | passa |
| Marca amarela sobre bloco grafite (logo) | `--color-accent` #F2B705 | `--color-inverse-surface` #151A1F | 9.63:1 | 3:1 | passa |

### Tema escuro

| Uso | Frente | Fundo | Razão | Mínimo | Resultado |
|---|---|---|---:|---:|---|
| Texto principal na página | `--color-text` #E7EBEE | `--color-bg` #0E1215 | 15.69:1 | 4.5:1 | passa |
| Texto em card/tabela | `--color-text` #E7EBEE | `--color-surface` #161B20 | 14.45:1 | 4.5:1 | passa |
| Texto em cabeçalho de tabela/linha zebrada | `--color-text` #E7EBEE | `--color-surface-2` #1F262C | 12.77:1 | 4.5:1 | passa |
| Texto secundário na página | `--color-text-muted` #A2ADB7 | `--color-bg` #0E1215 | 8.24:1 | 4.5:1 | passa |
| Texto secundário em card | `--color-text-muted` #A2ADB7 | `--color-surface` #161B20 | 7.59:1 | 4.5:1 | passa |
| Texto secundário em surface-2 | `--color-text-muted` #A2ADB7 | `--color-surface-2` #1F262C | 6.70:1 | 4.5:1 | passa |
| Link/botão fantasma na página | `--color-primary` #5BBBD1 | `--color-bg` #0E1215 | 8.49:1 | 4.5:1 | passa |
| Link/botão fantasma em card | `--color-primary` #5BBBD1 | `--color-surface` #161B20 | 7.82:1 | 4.5:1 | passa |
| Link em surface-2 | `--color-primary` #5BBBD1 | `--color-surface-2` #1F262C | 6.91:1 | 4.5:1 | passa |
| Link em hover | `--color-primary-hover` #82CDDF | `--color-surface` #161B20 | 9.69:1 | 4.5:1 | passa |
| Botão primário | `--color-primary-contrast` #0E1215 | `--color-primary` #5BBBD1 | 8.49:1 | 4.5:1 | passa |
| Botão primário em hover | `--color-primary-contrast` #0E1215 | `--color-primary-hover` #82CDDF | 10.53:1 | 4.5:1 | passa |
| Item de menu ativo | `--color-primary` #5BBBD1 | `--color-primary-subtle` #12333C | 6.06:1 | 4.5:1 | passa |
| Texto em destaque primário | `--color-text` #E7EBEE | `--color-primary-subtle` #12333C | 11.20:1 | 4.5:1 | passa |
| Texto sobre amarelo sinalização | `--color-accent-contrast` #0E1215 | `--color-accent` #F5C030 | 11.17:1 | 4.5:1 | passa |
| Botão perigo | `--color-danger-contrast` #0E1215 | `--color-danger` #FF8A7F | 8.24:1 | 4.5:1 | passa |
| Botão perigo em hover | `--color-danger-contrast` #0E1215 | `--color-danger-hover` #FFA59C | 9.96:1 | 4.5:1 | passa |
| Texto de sucesso | `--color-success` #5CC985 | `--color-surface` #161B20 | 8.38:1 | 4.5:1 | passa |
| Selo Concluída | `--color-success` #5CC985 | `--color-success-subtle` #16301F | 6.87:1 | 4.5:1 | passa |
| Texto de aviso | `--color-warning` #F2B755 | `--color-surface` #161B20 | 9.64:1 | 4.5:1 | passa |
| Selo Em andamento / alerta de aviso | `--color-warning` #F2B755 | `--color-warning-subtle` #33260F | 8.20:1 | 4.5:1 | passa |
| Mensagem de erro na página | `--color-danger` #FF8A7F | `--color-bg` #0E1215 | 8.24:1 | 4.5:1 | passa |
| Mensagem de erro de campo | `--color-danger` #FF8A7F | `--color-surface` #161B20 | 7.59:1 | 4.5:1 | passa |
| Alerta de erro | `--color-danger` #FF8A7F | `--color-danger-subtle` #3A1A18 | 6.86:1 | 4.5:1 | passa |
| Texto neutro | `--color-neutral` #A2ADB7 | `--color-surface` #161B20 | 7.59:1 | 4.5:1 | passa |
| Selo Não iniciada | `--color-neutral` #A2ADB7 | `--color-neutral-subtle` #252D34 | 6.12:1 | 4.5:1 | passa |
| Toast | `--color-inverse-text` #0E1215 | `--color-inverse-surface` #E7EBEE | 15.69:1 | 4.5:1 | passa |
| Borda de campo/botão secundário na página | `--color-border` #6F7C87 | `--color-bg` #0E1215 | 4.40:1 | 3:1 | passa |
| Borda de campo em card | `--color-border` #6F7C87 | `--color-surface` #161B20 | 4.05:1 | 3:1 | passa |
| Borda em surface-2 | `--color-border` #6F7C87 | `--color-surface-2` #1F262C | 3.58:1 | 3:1 | passa |
| Anel de foco na página | `--color-focus` #7DB0FF | `--color-bg` #0E1215 | 8.54:1 | 3:1 | passa |
| Anel de foco em card | `--color-focus` #7DB0FF | `--color-surface` #161B20 | 7.86:1 | 3:1 | passa |
| Anel de foco em surface-2 | `--color-focus` #7DB0FF | `--color-surface-2` #1F262C | 6.94:1 | 3:1 | passa |
| Barra de progresso (preenchimento × trilho) | `--color-primary` #5BBBD1 | `--color-track` #2C353D | 5.63:1 | 3:1 | passa |
| Barra de progresso concluída | `--color-success` #5CC985 | `--color-track` #2C353D | 6.03:1 | 3:1 | passa |
| Barra do gráfico × fundo do card | `--color-primary` #5BBBD1 | `--color-surface` #161B20 | 7.82:1 | 3:1 | passa |
| Borda de campo com erro | `--color-danger` #FF8A7F | `--color-surface` #161B20 | 7.59:1 | 3:1 | passa |
| Marca amarela sobre o fundo escuro | `--color-accent` #F5C030 | `--color-bg` #0E1215 | 11.17:1 | 3:1 | passa |

## Script

Para refazer após trocar qualquer cor: atualize o dicionário `T` e rode `python3 -` com o
conteúdo abaixo. Ele falha (`AssertionError`) se algum par ficar abaixo do mínimo.

```python
def lum(h):
    h = h.lstrip('#'); r, g, b = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def cr(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)

T = {
 'light': dict(bg='#F3F5F6', surface='#FFFFFF', surface2='#E9EDF0', text='#151A1F', muted='#4D5964',
   border='#727F8A', primary='#0B5D72', phover='#084A5B', pcont='#FFFFFF', psub='#E1EFF3',
   accent='#F2B705', acont='#151A1F', success='#1D7238', ssub='#E2F1E6', warning='#8F5300',
   wsub='#FBEFD9', danger='#B3261E', dhover='#8F1E18', dsub='#FBE6E4', dcont='#FFFFFF',
   neutral='#55616C', nsub='#E9EDF0', focus='#1B5FD1', inv='#151A1F', invtext='#F3F5F6',
   track='#D5DBE0'),
 'dark': dict(bg='#0E1215', surface='#161B20', surface2='#1F262C', text='#E7EBEE', muted='#A2ADB7',
   border='#6F7C87', primary='#5BBBD1', phover='#82CDDF', pcont='#0E1215', psub='#12333C',
   accent='#F5C030', acont='#0E1215', success='#5CC985', ssub='#16301F', warning='#F2B755',
   wsub='#33260F', danger='#FF8A7F', dhover='#FFA59C', dsub='#3A1A18', dcont='#0E1215',
   neutral='#A2ADB7', nsub='#252D34', focus='#7DB0FF', inv='#E7EBEE', invtext='#0E1215',
   track='#2C353D'),
}
TEXT = [('text','bg'),('text','surface'),('text','surface2'),('muted','bg'),('muted','surface'),
  ('muted','surface2'),('primary','bg'),('primary','surface'),('primary','surface2'),
  ('phover','surface'),('pcont','primary'),('pcont','phover'),('primary','psub'),('text','psub'),
  ('acont','accent'),('dcont','danger'),('dcont','dhover'),('success','surface'),('success','ssub'),
  ('warning','surface'),('warning','wsub'),('danger','bg'),('danger','surface'),('danger','dsub'),
  ('neutral','surface'),('neutral','nsub'),('invtext','inv')]
UI = [('border','bg'),('border','surface'),('border','surface2'),('focus','bg'),('focus','surface'),
  ('focus','surface2'),('primary','track'),('success','track'),('primary','surface'),('danger','surface')]
UI_EXTRA = {'light': [('accent','inv')], 'dark': [('accent','bg')]}
for tema, c in T.items():
    for pares, minimo in ((TEXT, 4.5), (UI + UI_EXTRA[tema], 3.0)):
        for a, b in pares:
            r = cr(c[a], c[b]); print(f'{tema:5} {a:8}/{b:8} {r:5.2f}')
            assert r >= minimo, (tema, a, b, r)
```
