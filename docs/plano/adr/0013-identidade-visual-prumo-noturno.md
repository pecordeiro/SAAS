# ADR-0013 — Identidade visual “Prumo Noturno”

Status: aplicada a pedido do dono · Data: 2026-10-15

## Contexto
O dono pediu uma identidade nova, inspirada em um vídeo de dashboard claro e em uma referência de
landing escura, mas sem copiar marca alguma, e a aplicação a todas as páginas. O protótipo foi
desenhado no Claude Design (canvas com 35 telas) e depois portado para o código.

## Decisão
- Só tokens mudam de valor (`tokens.css`, cópia idêntica em `docs/design/tokens.css`): nenhum nome de
  variável foi alterado, então templates e macros seguem iguais.
- Paleta clara: fundo `#EEF1F5`, superfície branca, primária azul `#2759F0`; escura equivalente.
  Todos os pares passam WCAG 2.1 AA (`docs/design/contraste.md`).
- Fonte única **Geist** (OFL, servida pelo próprio site, CSP intacta) no lugar de Barlow Semi Condensed
  + IBM Plex Sans.
- Raios 8/12/20 px; botão principal com brilho suave (`--shadow-primary`); rótulos em frase normal
  (fim das caixas altas); faixa final azul.
- Símbolo novo (medidor de 3 segmentos em bloco azul); favicon, apple-touch e og-image refeitos.
- O nome do produto não foi trocado no código: continua “Controle de Produção” até o dono decidir.

## Consequências
- Rebuild de `app/static/dist` (`scripts/build_assets.py`).
- Imagens PNG da marca foram geradas por script a partir do mesmo desenho do SVG.
- Capturas em `docs/design/capturas/` ficam desatualizadas até serem regeradas
  (`scripts/capturar_telas.py`, precisa de navegador).
