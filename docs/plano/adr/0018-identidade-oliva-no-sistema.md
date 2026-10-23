# ADR-0018 — Identidade oliva em todo o sistema

- Status: **aceito**. Aprovado pelo dono em 2026-10-23. Ele pediu o design verde-oliva “em todas as páginas”,
  “também dentro do sistema”, “não só o verde-oliva, mas a fonte, tudo”, porém “menos animações, foco na
  eficiência”. Supera a ADR-0015 **só em fonte, cor e formas**; densidade e foco em eficiência continuam. Estende
  a ADR-0016 (que valia só para o site público).

## Decisão
1. **Tokens semânticos valem a marca.** `--color-bg`, `--color-surface`, `--color-text*`, `--color-border*`,
   `--color-primary*`, `--color-action*`, `--color-focus`, `--color-track`, `--font-sans`, `--font-display` e os
   raios têm os valores da identidade oliva (off-white `#FBFBF6`, tinta `#14170D`, oliva escuro `#455A0F`,
   `#8F9F78` como bloco no site) em `app/static/css/tokens.css` (cópia idêntica em `docs/design/tokens.css`).
   O remapeamento `.site--marca` de tokens saiu do `publico.css` (não é mais necessário). Tema escuro com os
   tokens da ADR-0016 (fundo `#0F120A`, marca `#B7D064`). Os tokens `--color-brand-*` seguem como paleta nomeada
   do site público.
2. **Dado nunca usa o oliva.** Situação e gráfico mantêm: concluída verde `#1F8A3B`, em andamento azul
   `#2A78D6`, não iniciada cinza, aguardando amarelo, atrasada vermelho; séries tarefas azul, unidades laranja.
   Barra de progresso, anel, gráfico de barras e esteira usam esses tokens (não `--color-primary`). Novos:
   `--color-doing-text/-subtle` (selo “Em andamento”, `.badge--progress`) e `--color-series-neutral` (cinza puro
   para “até o prazo”). Links e foco da área logada são oliva/tinta com contraste AA, nunca o azul de status.
   `--color-editable-text` passou a tinta.
3. **Fonte:** DM Sans no texto e Newsreader em títulos de página e de card (h1, h2), marca, números grandes
   (indicadores, preços, número do stepper). Newsreader só tem o peso 400: nada de negrito sintético (títulos
   em Newsreader ficam em 400). IBM Plex Sans removida (arquivos e licença). DM Sans 400/500 e 600/700 já
   estavam vendorizadas.
4. **Escala:** corpo 14–16 px; título de página 24 px (celular) e 28 px (desktop); título de card 18 px;
   indicador do Painel 28 px e número principal 40 px, ambos em Newsreader. Isso **revisa o teto de 32 px** da
   ADR-0015: só números grandes em serifa podem passar dele; o resto continua compacto. Controles 36 px no
   desktop e 44 px no celular, linhas de tabela 40 px — sem aumentar alturas nem espaçamentos.
5. **Formas:** botão principal oliva com raio **8 px** (escolhido em vez da pílula: mais denso e coerente com
   campos e cards); raio de card e modal 12 px; selos em pílula. Menu lateral claro com item ativo em oliva suave
   (`--color-primary-subtle` com texto oliva). Foco visível de 3 px (`--focus-width`).
6. **Menos animação** (área logada): ficam só transição curta de hover/foco (100 ms), realce da linha salva
   (`row-flash`), abrir/fechar de menus e diálogos (150 ms), toast com fade, gráfico desenhando uma vez (400 ms,
   não repete ao trocar tema) e o spinner do HTMX. Saíram: escala ao clicar no botão, rotação animada dos
   chevrons, pulso do esqueleto, deslocamentos do toast. Tudo zera com `prefers-reduced-motion`. As páginas
   públicas mantêm a vitrine animada da ADR-0016.
7. **Login, cadastro, recuperação, MFA, convite e erros** usam o mesmo cabeçalho com o logotipo oliva; o rodapé
   fica no fim da janela. **E-mails** usam atributos HTML legados (`bgcolor`, `<font face color>`) com valores
   lidos de `tokens.css` (`email_brand()`), porque e-mail não enxerga CSS do site nem aceita `style=` aqui.

## Consequências
- Testes novos em `tests/test_visual.py` (tokens oliva, dado sem oliva, sem animação decorativa, e-mail).
- `THEME_COLORS["app"]` passou para `#FBFBF6` / `#0F120A`.
- Contraste em `docs/design/contraste.md`.
- Pendências: cabeçalho do site público em 768 px tem 29 px de rolagem horizontal (anterior a esta mudança,
  fora do escopo); e-mail sem cor de link (cliente decide).
