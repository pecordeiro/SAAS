# ADR-0001 — Site renderizado no servidor em vez de SPA

- Status: proposto · Data: 2026-10-13

## Contexto
O produto é usado por supervisores no escritório e operadores no celular, em redes de
fábrica às vezes lentas. A equipe é pequena e o stack é Python. Precisamos de SEO nas
páginas públicas e CSP estrita.

## Decisão
Páginas renderizadas no servidor com Flask + Jinja. Sem SPA, sem React, sem build de
front-end além de minificação de CSS/JS.

## Consequências
- (+) Um só código e uma só linguagem; páginas leves; SEO natural; CSP simples.
- (+) Isolamento multiempresa fica todo no backend, mais fácil de testar.
- (−) Interações ricas exigem HTMX (ADR-0002) e cuidado com fragmentos.
- (−) Sem modo offline no MVP.

## Alternativas
SPA React + API JSON: dobra a superfície (API + cliente), exige build e autenticação de API
desde o dia 1. Rejeitada para o MVP.
