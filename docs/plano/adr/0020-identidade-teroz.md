# ADR-0020 — Identidade Teroz (logotipo, ícones e favicon)

- Status: **proposto**, aguardando a aprovação do dono para o commit (prévia publicada antes). O dono escolheu a
  Proposta 1 do logotipo Teroz em 2026-10-27 e pediu: "aplique essa identidade no site", "mantenha a fonte antiga"
  (a fonte nova vale só dentro do logotipo) e, na área logada, "só o símbolo, menor e centralizado".
  Estende a ADR-0016 e a ADR-0018 e **supera só o item de logotipo e favicon** da ADR-0016 (símbolo "medidor").

## Decisão
1. **Logotipo** em SVG vetorial: símbolo de três formas em pílula (oliva escuro `#455A0F` e lima `#B7D064`) e a
   palavra "Teroz" desenhada em curvas (sem fonte carregada). Variantes em `app/static/img/`: `logo.svg` (fundo
   claro), `logo-escuro.svg`, `logo-1cor.svg` (preto), `simbolo.svg`, `simbolo-escuro.svg`, `icone-claro.svg`,
   `icone-oliva.svg`, `icone-preto.svg` e `favicon.svg`; PNGs `favicon-16.png`, `favicon-32.png`,
   `apple-touch-icon.png` (180) e `og-image.png` (1200×630).
2. **Fontes do site não mudam:** DM Sans no texto e Newsreader em títulos e números grandes (ADR-0018). A sans
   geométrica bold existe só na palavra do logotipo, que é desenho, não texto.
3. **Aplicação:** macro `components/brand.html` (`logo` e `symbol`), duas imagens por variante e troca por tema em
   CSS (`.brand__logo--claro/--escuro` em `layout.css`), sem JavaScript e sem `style=`. Site público: logotipo
   completo. Área logada: só o símbolo, pequeno e centralizado no menu lateral; barra superior do celular e páginas
   de erro também usam o símbolo.
4. **Paleta:** a de sempre (ADR-0018). O lima `#B7D064` só aparece em formas do logotipo, nunca como texto sobre o
   fundo claro (contraste insuficiente) e nunca em dado.
5. **Nome do produto:** o texto "Controle de Produção" continua nos títulos de página, e-mails, termos, exportações e
   no emissor do autenticador. **Trocar o nome em texto para "Teroz" é decisão separada** (impacta termos, e-mails,
   MFA e cobrança) e fica pendente.

## Consequências
- `tests/test_marca_teroz.py` cobre as variantes, os tamanhos dos PNGs, a troca claro/escuro e o símbolo na área logada.
- O símbolo foi vetorizado a partir da imagem aprovada, e a palavra usa DM Sans Bold em curvas. Se o dono tiver o
  arquivo vetorial original do logotipo, ele substitui estes arquivos sem mudar o resto.
- `docs/design/logo.svg` e `docs/design/favicon.svg` foram atualizados; `docs/design/marca.md` ainda descreve o
  símbolo antigo e precisa ser reescrito na aprovação.
