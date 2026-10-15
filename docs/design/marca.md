# Marca — 3 direções e a recomendada

> **Identidade vigente (2026-10-15): “Prumo Noturno”** — claro e arejado, azul ação `#2759F0`,
> cards brancos de cantos grandes sobre fundo névoa, fonte única Geist (OFL), símbolo em forma de
> medidor segmentado. Substitui a direção A abaixo (petróleo + amarelo + Barlow/IBM Plex); as três
> direções originais ficam como histórico. O **nome comercial ainda não foi decidido**: o wordmark é
> texto em HTML, então trocar o nome não exige novo arquivo de imagem (ver ADR-0013).
> Valores em `tokens.css`; contraste em `contraste.md`.


Status: proposta para aprovação (Fase 1, decisão D1 do `prd.md`) · Atualizado: 2026-10-13

Produzido sem o Claude Design (ver ADR-0008). **Você pode trocar a direção ou o nome a
qualquer momento**: o código só conhece os nomes dos tokens em `tokens.css`, então trocar
marca = trocar valores, não templates.

## Restrições que guiaram as três

- Público: supervisores e donos de indústrias de montagem, no escritório e no chão de
  fábrica, no celular, às vezes com luvas e sob luz forte.
- Tom: preciso, confiável, industrial sem ser pesado. Nada de gradiente roxo, ilustração 3D
  ou mascote.
- Números no centro: unidades concluídas, %, horas que faltam, dias úteis. Fontes com
  algarismos tabulares e boa leitura à distância.
- Fontes livres (SIL Open Font License, Google Fonts), servidas pelo próprio site (CSP estrita).
- Símbolo legível em 16 px (favicon) e sem depender de texto.

---

## Direção A — “Prumo” (recomendada)

- **Nome alternativo:** Prumo. Curto, português, remete ao fio de prumo do montador: algo
  “no prumo” está certo, alinhado, verificado.
- **Conceito:** a produção no prumo — saber com exatidão onde cada lote está e quanto falta.
- **Logotipo:** bloco quadrado grafite com cantos levemente arredondados e três barras
  horizontais alinhadas à esquerda, de comprimento decrescente (etapas). As duas primeiras
  em branco (feitas), a última em amarelo sinalização (em andamento). Lê-se como “progresso
  por etapa” e também como uma lista de tarefas. Wordmark ao lado, em HTML (não no SVG):
  “Controle de Produção” (ou “Prumo”) em Barlow Semi Condensed 600.
- **Paleta:**

  | Papel | Claro | Escuro |
  |---|---|---|
  | Grafite (texto, bloco do logo) | `#151A1F` | `#E7EBEE` |
  | Azul petróleo (primária) | `#0B5D72` | `#5BBBD1` |
  | Amarelo sinalização (acento, só gráfico) | `#F2B705` | `#F5C030` |
  | Fundo / superfície | `#F3F5F6` / `#FFFFFF` | `#0E1215` / `#161B20` |
  | Sucesso / aviso / perigo | `#1D7238` / `#8F5300` / `#B3261E` | `#5CC985` / `#F2B755` / `#FF8A7F` |

- **Fontes (OFL):** **Barlow Semi Condensed** (títulos e números grandes — desenhada a partir
  da sinalização rodoviária, larga leitura à distância, semicondensada cabe números grandes
  em 375 px) + **IBM Plex Sans** (texto, tabelas, campos; algarismos tabulares `tnum`).
  IBM Plex Mono opcional para códigos de lote/token.

## Direção B — “Esteira”

- **Nome alternativo:** Esteira.
- **Conceito:** a produção fluindo etapa após etapa, sem gargalo escondido.
- **Logotipo:** três chevrons (›››) em sequência sobre uma linha de base, o último preenchido.
  Em 16 px vira dois chevrons grossos.
- **Paleta:** azul cobalto `#1F4FA3` (primária), laranja segurança `#D9480F` (acento),
  aço `#2B3138` (texto), papel `#F6F7F9` (fundo).
- **Fontes (OFL):** **Archivo** (títulos, largura variável) + **Atkinson Hyperlegible**
  (texto, foco em legibilidade para baixa visão).
- **Por que não foi a escolhida:** laranja de acento briga com os estados de aviso e perigo
  (vermelho/âmbar) que o produto usa o tempo todo nos selos de etapa; cobalto é próximo
  demais do azul genérico de SaaS.

## Direção C — “Marco”

- **Nome alternativo:** Marco (marco de obra / marco de prazo).
- **Conceito:** prometer prazo com base em dado, não em chute.
- **Logotipo:** losango sólido apoiado numa base horizontal (marco topográfico), com um
  corte vertical no centro.
- **Paleta:** verde musgo `#2F4A3A` (primária), creme `#F7F3EA` (fundo), terracota
  `#B5532F` (acento), carvão `#1E1E1C` (texto).
- **Fontes (OFL):** **Public Sans** (texto e títulos) + **JetBrains Mono** (números).
- **Por que não foi a escolhida:** a primária verde conflita com o verde de “Concluída”;
  fundo creme perde contraste percebido sob luz forte; números em mono ocupam muita largura
  no celular.

---

## Recomendação

**Direção A — Prumo**, mantendo **“Controle de Produção” como nome provisório** até você
decidir D1 (o símbolo não contém texto, então o nome pode mudar sem refazer o logo).

Justificativa:
1. **Status sem conflito.** A primária azul petróleo não se confunde com verde (Concluída),
   âmbar (Em andamento) nem vermelho (erro). O amarelo fica restrito à marca e a destaques
   gráficos, como na sinalização de fábrica.
2. **Leitura no chão de fábrica.** Grafite sobre quase-branco dá 16:1; Barlow Semi Condensed
   foi feita para ser lida à distância e permite números de 48 px em 375 px sem quebrar.
3. **Símbolo funciona em 16 px** (barras de 2 px com vãos de 3 px em grade inteira) e
   comunica o produto (etapas com progresso) sem precisar de palavra.
4. **Industrial sem ser pesado:** cinzas frios, cantos pequenos (4–10 px), sem gradiente.
5. **Contraste verificado** em todos os pares nos dois temas (`contraste.md`).

Nome “Prumo”: se agradar, verificar marca no INPI e domínio no Registro.br antes de adotar
(há empresas com nomes parecidos em construção civil). Até lá, “Controle de Produção”.

## Uso do logo

| Arquivo | Uso |
|---|---|
| `logo.svg` | Símbolo 32×32 (escala livre). Cabeçalho do site e do app, ao lado do wordmark em HTML. |
| `favicon.svg` | Grade 16×16 alinhada ao pixel. `<link rel="icon" type="image/svg+xml">`. Gerar `favicon.ico` 32 px e `apple-touch-icon.png` 180 px na Fase 2. |
| `og-image.svg` | Imagem de compartilhamento 1200×630. Converter para PNG na Fase 2 (redes não aceitam SVG). |

Regras: área de respiro = metade do lado do símbolo; tamanho mínimo 16 px; não recolorir as
barras; no tema escuro o bloco grafite ganha borda `--color-border-subtle` quando estiver
sobre `--color-bg`. Amarelo nunca como cor de texto em fundo claro (1,7:1).

## Se você escolher outra direção

Troque os valores em `tokens.css` (mesmos nomes), refaça `contraste.md` com o mesmo script
e redesenhe os três SVGs. Templates e macros não mudam.
