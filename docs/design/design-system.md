# Design system — Controle de Produção (direção “Prumo”)

Status: proposta para aprovação · Atualizado: 2026-10-13 · Tokens: `tokens.css` ·
Contraste: `contraste.md` · Telas: `telas.md`

Este documento substitui o handoff do Claude Design (ADR-0008). Na Fase 2 cada componente
vira uma macro Jinja em `app/templates/components/` com o nome indicado em **Macro**, e
aparece na página `/estilo` (só em development).

## 0. Princípios

1. **O número é o herói.** Indicadores em `--font-display`, `--font-size-2xl` (celular) /
   `--font-size-3xl` (desktop), peso 700, `font-variant-numeric: var(--font-numeric)`.
   Rótulo pequeno em caixa alta acima, unidade ao lado em `--color-text-muted`.
2. **Polegar primeiro.** Todo alvo ≥ `--touch-min` (44 px); ações de chão de fábrica
   ≥ `--touch-comfortable` (56 px), com ≥ `--space-2` (8 px) entre alvos vizinhos. Ação
   principal no celular fica na metade inferior da tela.
3. **Cor nunca sozinha.** Status sempre com texto (e ícone quando couber); erro com mensagem.
4. **Funciona sem JS.** Todo componente interativo tem fallback de formulário/link (ADR-0002).
   HTMX só melhora.
5. **Só tokens.** Nenhuma cor, fonte, tamanho ou espaçamento literal fora de `tokens.css`.

### Convenções gerais
- Fonte base `--font-sans` `--font-size-md` / `--line-height-normal`, cor `--color-text`
  sobre `--color-bg`.
- **Foco**: `:focus-visible { outline: var(--focus-width) solid var(--color-focus);
  outline-offset: var(--focus-offset); }` em todo elemento interativo. Nunca `outline: none`
  sem substituto.
- **Desabilitado**: `cursor: not-allowed`, fundo `--color-surface-2`, texto
  `--color-text-muted`, borda `--color-border-subtle`; atributo `disabled` ou
  `aria-disabled="true"` (quando precisa continuar focável para explicar o motivo via
  `aria-describedby`). Sem opacidade, para continuar legível sob sol.
- **Carregando** (HTMX): classe `htmx-request` no elemento; botão mostra spinner de 16 px
  (borda `currentColor`, animação `--duration-normal`), mantém a largura e recebe
  `aria-busy="true"`; texto vira “Salvando…”. Requisições > 400 ms mostram skeleton.
- **Ícones**: SVG inline (sprite próprio, sem CDN), `--icon-size`, `currentColor`,
  `aria-hidden="true"` quando há texto.
- **Movimento**: transições `--duration-fast` `--easing-standard`; zeradas com
  `prefers-reduced-motion`.

---

## 1. Botões — Macro `button(label, variant, size, icon, type, href, disabled, loading)`

Altura `--control-height` (44 px), `lg` = `--control-height-lg` (56 px). Padding horizontal
`--space-4`; raio `--radius-md`; `--font-size-md` `--font-weight-semibold`; gap ícone
`--space-2`. Largura total (`block`) no celular para ação principal.

| Variante | Repouso | Hover | Ativo (pressionado) | Uso |
|---|---|---|---|---|
| **Primário** | fundo `--color-primary`, texto `--color-primary-contrast` | fundo `--color-primary-hover` | fundo `--color-primary-hover` + `translateY(1px)` | 1 por tela/área: Salvar, Registrar, Criar projeto |
| **Secundário** | fundo `--color-surface`, borda `--border-width` `--color-border`, texto `--color-text` | fundo `--color-surface-2` | idem + `translateY(1px)` | Cancelar, Exportar, ações alternativas |
| **Perigo** | fundo `--color-danger`, texto `--color-danger-contrast` | fundo `--color-danger-hover` | idem | Excluir, Remover usuário (sempre via modal de confirmação) |
| **Fantasma** | sem fundo/borda, texto `--color-primary` | fundo `--color-primary-subtle` | idem | Ações terciárias em tabela, “Ver histórico”, links com área de toque |

Estados comuns:
- **Foco**: anel `--color-focus` (ver Convenções).
- **Desabilitado**: ver Convenções; botão de plano bloqueado mostra motivo abaixo
  (“Seu plano permite 3 projetos ativos”).
- **Carregando**: spinner à esquerda, `aria-busy`, clique ignorado, largura preservada.
- **Erro**: botões não têm estado de erro; o erro aparece no alerta/campo relacionado.

Botão só-ícone (ex.: fechar, menu): quadrado `--touch-min`, `aria-label` obrigatório.

## 2. Campo de formulário — Macro `field(name, label, type, hint, error, required)`

Estrutura: rótulo (acima, `--font-size-sm` `--font-weight-semibold`, `--color-text`) →
campo → dica (`--font-size-sm` `--color-text-muted`) → erro.
- Campo: altura `--control-height`, padding `--space-3`, fundo `--color-surface`, borda
  `--border-width` `--color-border`, raio `--radius-md`, `--font-size-md` (16 px evita zoom
  no iOS).
- **Hover**: borda `--color-text-muted`.
- **Foco**: anel `--color-focus`; borda mantém.
- **Desabilitado / somente leitura**: fundo `--color-surface-2`, texto `--color-text-muted`.
- **Erro**: borda `--border-width-strong` `--color-danger`; mensagem abaixo em
  `--color-danger` com ícone “!” e texto que diz como corrigir (“Informe um e-mail válido,
  ex.: ana@empresa.com.br”); `aria-invalid="true"`, `aria-describedby` → id da mensagem.
  No envio com erros: alerta de erro no topo do formulário listando os campos (links que
  focam o campo) e foco movido para o alerta.
- **Carregando** (validação assíncrona, ex. CNPJ): spinner dentro do campo à direita.
- Obrigatório: “(obrigatório)” no rótulo em `--color-text-muted`, não só asterisco.
- Variações: `select`, `textarea`, `checkbox`/`radio` (alvo 44 px incluindo rótulo),
  `password` com botão “Mostrar”.

## 3. Registrador de peças (campo numérico grande) — Macro `piece_stepper(activity, done, planned)`

O componente mais importante do produto. Usado na **folha de registro** (bottom sheet no
celular, popover/linha expandida no desktop).

```
┌───────────────────────────────────────────┐
│ Montagem mecânica › Alinhamento            │  --font-size-md semibold
│ 7 de 10 concluídas · faltam 3              │  --color-text-muted, tabular
│                                             │
│  ┌──────┐   ┌──────────────┐   ┌──────┐    │
│  │  −   │   │      +1      │   │  +   │    │  botões 56×56, valor 48 px
│  └──────┘   └──────────────┘   └──────┘    │
│        quantidade a somar (editável)        │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │        Registrar +1  (→ 8 de 10)        │ │  primário lg, largura total
│ └─────────────────────────────────────────┘ │
└───────────────────────────────────────────┘
```

- Botões − / +: `--touch-comfortable` (56 px) quadrados, variante secundária, ícone 24 px,
  separados do valor por `--space-3`.
- Valor: `<input type="number" inputmode="numeric" pattern="[0-9]*" min="1" max="{faltam}">`,
  `--font-display` `--font-size-3xl` 700 `tabular-nums`, centralizado, altura 56 px, borda
  `--color-border`. **Entrada direta**: tocar no número seleciona o conteúdo e abre o teclado
  numérico.
- Padrão = **1** (o caso mais comum). O rótulo do botão principal acompanha o valor
  (“Registrar +3 (→ 10 de 10)”).
- Fluxo de **2 toques**: (1) tocar na atividade abre a folha já com +1 → (2) tocar
  “Registrar”. Ajustar quantidade é opcional e não conta como passo obrigatório.
- Limites: − desabilitado em 1; + desabilitado ao atingir “faltam”; valor acima do faltante
  mostra erro “Faltam só 3 peças nesta atividade”. Atividade completa: stepper substituído
  pelo selo Concluída.
- **Carregando**: botão principal em estado carregando; stepper bloqueado.
- **Sucesso**: folha fecha, linha da atividade pisca `--color-success-subtle` por
  `--duration-normal` (sem animação se movimento reduzido), indicadores atualizam via HTMX
  (`hx-swap-oob`), toast “+1 em Alinhamento · 8 de 10”.
- **Erro** (rede, conflito): folha continua aberta, alerta de erro dentro dela com “Tentar
  de novo”; nada é somado em dobro (chave de idempotência no formulário).
- Sem JS: formulário POST normal com o campo numérico e botão Registrar.
- Acessibilidade: grupo com `role="group"` e `aria-labelledby` no nome da atividade; botões
  “Diminuir quantidade”/“Aumentar quantidade”; resultado anunciado em região `aria-live`.
- Desfazer: só supervisor+ (D13), pelo histórico — o toast do operador não oferece desfazer.

## 4. Tabela densa — Macro `data_table(columns, rows, sort, empty)`

- Fundo `--color-surface`, borda externa `--color-border-subtle`, raio `--radius-lg`.
- Cabeçalho: fundo `--color-surface-2`, `--font-size-sm` `--font-weight-semibold`,
  `--letter-spacing-caps`, `--color-text-muted`; ordenável = botão com seta e
  `aria-sort`.
- Linhas: altura mínima 44 px, padding `--space-2` `--space-3`, divisória
  `--color-border-subtle`; hover `--color-surface-2`; linha clicável inteira = link
  (foco visível na linha).
- Números alinhados à direita, `tabular-nums`; datas `dd/mm/aaaa HH:MM`.
- Cabeçalho fixo (`position: sticky`, `--z-sticky`) em listas longas.
- **Celular (< 768 px)**: vira lista de cards (cada linha = card com 2–3 dados principais);
  nunca rolagem horizontal da página. Se a tabela precisar de muitas colunas (histórico),
  colunas secundárias somem e ficam no detalhe.
- **Carregando**: 5 linhas skeleton (`--color-surface-2`). **Vazio**: estado vazio dentro do
  card. **Erro**: alerta de erro no lugar das linhas.

## 5. Card de indicador — Macro `kpi(label, value, unit, sub, tone)`

```
┌───────────────────────┐
│ UNIDADES CONCLUÍDAS   │  --font-size-sm semibold caps, --color-text-muted
│ 1 / 10                │  --font-display --font-size-2xl|3xl 700 tabular
│ 7 na etapa mais longe │  --font-size-sm --color-text-muted
└───────────────────────┘
```
- Fundo `--color-surface`, borda `--color-border-subtle`, raio `--radius-lg`,
  `--shadow-1`, padding `--space-4` (celular) / `--space-6` (desktop).
- `tone`: `neutral` (padrão), `success` / `warning` / `danger` → sublinha em cor de status
  com ícone (“no prazo”, “2 dias de atraso”). O número fica sempre em `--color-text`.
- Grade: 2 colunas no celular, 4 no desktop. Card inteiro pode ser link (hover
  `--color-surface-2`).
- **Carregando**: barra skeleton no lugar do número. **Sem dado**: “—” e sub “sem etapas
  ainda”.

## 6. Barra de progresso — Macro `progress(value, max, label, size)`

- Trilho `--color-track`, preenchimento `--color-primary`; 100% = `--color-success`.
- Altura 8 px (`sm`, em listas) ou 12 px (`md`, detalhe); raio `--radius-pill`.
- Sempre acompanhada de texto (“56%” ou “7 de 10”) ao lado/acima; `role="progressbar"`
  com `aria-valuenow/min/max` e `aria-label`.
- Atrasado: preenchimento continua primário; o atraso é comunicado no selo/indicador.

## 7. Selo de status — Macro `status_badge(status)`

| Status | Fundo | Texto | Ícone |
|---|---|---|---|
| **Concluída** | `--color-success-subtle` | `--color-success` | ✓ |
| **Em andamento** | `--color-warning-subtle` | `--color-warning` | ◐ |
| **Não iniciada** | `--color-neutral-subtle` | `--color-neutral` | ○ |
| Atrasado (projeto) | `--color-danger-subtle` | `--color-danger` | ! |
| Teste grátis / Ativa / Em carência / Somente leitura (assinatura) | primary-subtle / success / warning / danger | cor correspondente | — |

`--font-size-sm` `--font-weight-semibold`, padding `--space-1` `--space-2`, raio
`--radius-sm`, altura ≥ 24 px (não é clicável; se for filtro, vira botão de 44 px).

## 8. Alerta — Macro `alert(kind, title, body, action)`

- Tipos: `info` (primary-subtle / primary), `success`, `warning`, `danger` — fundo
  `-subtle`, borda esquerda 4 px na cor, título `--font-weight-semibold` em `--color-text`,
  ícone na cor do tipo, corpo `--color-text`.
- Pode ter ação (botão fantasma) e botão fechar (44 px).
- `role="alert"` só para erro que acabou de acontecer; demais `role="status"`.
- Usos: erro de formulário, “Assinatura vence em 3 dias”, “Modo leitura: regularize o
  pagamento”, plano no limite.

## 9. Toast — Macro `toast(message, kind, action)`

- Fundo `--color-inverse-surface`, texto `--color-inverse-text`, raio `--radius-md`,
  `--shadow-2`, padding `--space-3` `--space-4`, `--z-toast`.
- Posição: celular acima da navegação inferior (bottom + `--bottom-nav-height` +
  `--space-2`), largura total menos gutter; desktop canto inferior direito, 360 px.
- Some em 5 s (pausa com foco/hover); 1 por vez; região `aria-live="polite"`.
- Nunca é o único lugar de uma informação crítica (erros vão em alerta).

## 10. Modal de confirmação — Macro `confirm_dialog(title, body, confirm_label, variant)`

- `<dialog>` nativo; overlay `--color-overlay`; caixa `--color-surface`, `--radius-lg`,
  `--shadow-3`, largura máx. 480 px, padding `--space-6`, `--z-modal`.
- Celular: vira folha inferior (bottom sheet) com botões empilhados, primário embaixo
  (alcance do polegar).
- Título diz a consequência (“Excluir o projeto Lote 2026-014?”), corpo explica o que se
  perde; para exclusões irreversíveis, digitar o nome do projeto.
- Botões: Cancelar (secundário, recebe foco inicial) + ação (perigo ou primário, rótulo
  verbo: “Excluir projeto”).
- Esc e clique no overlay fecham (exceto durante carregamento); foco preso; ao fechar,
  foco volta ao gatilho. Sem JS: página de confirmação dedicada.

## 11. Menu lateral (desktop ≥ 768 px) — Macro `sidebar(items, current)`

- Largura `--sidebar-width`, fundo `--color-surface`, borda direita `--color-border-subtle`.
- Topo: logo + nome da empresa (seletor se o usuário tiver mais de uma).
- Itens 44 px, ícone + rótulo, padding `--space-3`; ativo: fundo `--color-primary-subtle`,
  texto `--color-primary`, barra de 3 px `--color-primary` à esquerda, `aria-current="page"`;
  hover `--color-surface-2`.
- Itens: Projetos · Histórico · Modelos de etapas · Usuários · Empresa · Assinatura.
  Operador vê só Projetos e Histórico. Rodapé: usuário, tema (Sistema/Claro/Escuro), Sair.
- Entre 768 e 1023 px pode recolher para só ícones (64 px) com `title`/`aria-label`.

## 12. Navegação inferior (celular < 768 px) — Macro `bottom_nav(items, current)`

- Altura `--bottom-nav-height` (64 px) + `env(safe-area-inset-bottom)`, fundo
  `--color-surface`, borda superior `--color-border-subtle`, `--z-nav`, fixa.
- 4 itens no máximo, cada um ≥ 64×56: **Projetos · Histórico · Modelos · Mais**
  (Mais abre folha com Usuários, Empresa, Assinatura, Tema, Sair). Operador: Projetos ·
  Histórico · Conta.
- Ícone 24 px + rótulo `--font-size-sm` (rótulo sempre visível); ativo em `--color-primary`
  com indicador de 3 px no topo; demais `--color-text-muted`.
- Conteúdo da página recebe `padding-bottom` igual à altura da navegação.

## 13. Estado vazio — Macro `empty_state(title, body, action, icon)`

- Centralizado no card/área, padding `--space-12` vertical; ícone de linha 48 px
  `--color-text-muted` (desenho simples, sem ilustração); título `--font-size-lg`
  semibold; corpo `--color-text-muted` máx. 44 caracteres por linha; 1 ação primária.
- Sempre diz o próximo passo (“Crie o primeiro projeto a partir de um modelo de etapas”).
- Variante “sem resultado de filtro”: ação = “Limpar filtros” (fantasma).

## 14. Paginação — Macro `pagination(page, pages, total)`

- “Mostrando 1–25 de 132” (`--color-text-muted`, tabular) + botões Anterior/Próxima
  (secundários, 44 px) + números de página (44 px) no desktop; no celular só
  Anterior · “Página 2 de 6” · Próxima.
- Página atual: fundo `--color-primary-subtle`, texto `--color-primary`,
  `aria-current="page"`. Desabilitado nas pontas. Links reais (`?page=`), HTMX opcional.
- Histórico longo pode usar “Carregar mais” (botão secundário largura total) em vez de
  números.

## 15. Gráfico de barras simples (SVG) — Macro `bar_chart(series, max, unit)`

Uso: progresso por etapa e unidades por dia no histórico. SVG gerado no servidor, sem
biblioteca.

- Barras **horizontais** (rótulos longos de etapa cabem no celular): uma linha por etapa,
  rótulo acima da barra (`--font-size-sm`), valor à direita (`tabular-nums`, semibold).
- Trilho `--color-track` (100%), valor `--color-primary`; etapa concluída `--color-success`.
- Altura da barra 12 px, espaço entre linhas `--space-3`; cantos `--radius-sm`.
- Sem eixo e sem grade (o valor está escrito); legenda só se houver 2 séries.
- Barras verticais (unidades por dia): até 14 colunas, eixo X com datas `dd/mm`,
  valor acima da barra; linha de base `--color-border`.
- Acessibilidade: `<svg role="img" aria-labelledby>` com `<title>` + tabela equivalente
  (`<details>` “Ver dados em tabela”).
- Contraste: barra × fundo e barra × trilho ≥ 3:1 nos dois temas (ver `contraste.md`).
- **Carregando**: barras skeleton. **Vazio**: “Sem registros neste período”.

---

## 16. Outros padrões

- **Cabeçalho de página**: título `--font-size-xl` (celular) / `--font-size-2xl`
  (desktop) `--font-display` 600; subtítulo `--color-text-muted`; ações à direita no
  desktop, no celular a ação principal vira botão fixo acima da navegação inferior.
- **Skeleton**: blocos `--color-surface-2` com raio `--radius-sm`, pulso de opacidade
  (sem pulso com movimento reduzido). `aria-busy="true"` no contêiner.
- **Folha inferior (bottom sheet)**: `--color-surface`, raio superior `--radius-lg`,
  `--shadow-3`, alça de 4×32 px, máx. 85% da altura; mesmo comportamento de foco do modal.
- **Seletor de tema**: radio Sistema/Claro/Escuro → atributo `data-theme` no `<html>`
  (ausente = sistema), guardado em cookie para renderizar certo no servidor (sem flash).
- **Grade**: celular 1 coluna, gutter `--gutter`; ≥ 768 px gutter `--gutter-desktop`;
  conteúdo máx. `--content-max`.

## 17. Mapa componente → tokens (resumo)

| Componente | Cores | Tipo | Espaço/forma |
|---|---|---|---|
| Botões | primary, primary-hover, primary-contrast, danger, danger-hover, danger-contrast, surface, surface-2, border, text, focus | font-size-md, weight-semibold | control-height(-lg), space-2/4, radius-md |
| Campo | surface, surface-2, border, text, text-muted, danger, focus | font-size-sm/md | control-height, space-3, radius-md, border-width-strong |
| Registrador de peças | surface, border, primary, success-subtle, danger | font-display, font-size-3xl, font-numeric | touch-comfortable, space-3, radius-md |
| Tabela | surface, surface-2, border-subtle, text, text-muted | font-size-sm/md, letter-spacing-caps, font-numeric | space-2/3, radius-lg, z-sticky |
| Indicador | surface, border-subtle, text, text-muted, status | font-display, font-size-2xl/3xl, font-numeric | space-4/6, radius-lg, shadow-1 |
| Progresso | track, primary, success | font-numeric | radius-pill |
| Selo | *-subtle + status | font-size-sm, weight-semibold | space-1/2, radius-sm |
| Alerta | *-subtle + status, text | weight-semibold | space-4, radius-md |
| Toast | inverse-surface, inverse-text | font-size-md | space-3/4, radius-md, shadow-2, z-toast |
| Modal | overlay, surface | font-size-lg | space-6, radius-lg, shadow-3, z-modal |
| Menu lateral / navegação inferior | surface, border-subtle, primary, primary-subtle, text-muted | font-size-sm/md | sidebar-width, bottom-nav-height, touch-min |
| Gráfico | track, primary, success, border | font-size-sm, font-numeric | radius-sm |
