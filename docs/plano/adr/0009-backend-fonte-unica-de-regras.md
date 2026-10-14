# ADR-0009 — Backend é a única fonte de regras; o front é só painel

- Status: aceito (plano novo aprovado pelo usuário, Etapa A) · Data: 2026-10-14

## Contexto
O produto é um site renderizado no servidor (ADR-0001) com HTMX (ADR-0002). Com o próximo
plano o painel deve ficar mais rico (inspirado no painel antigo), e cresce a tentação de
calcular progresso, prazo, horas restantes, limites de plano ou permissões no navegador
para “responder mais rápido”. Isso duplicaria regras (risco T2: divergência de cálculo),
abriria brecha de segurança (regra só na tela é contornável — regra inviolável 7) e
quebraria a paridade com a planilha garantida por `calc.py`.

## Decisão
1. **Toda regra mora no backend**: cálculos só em `app/services/calc.py`; limites de plano em
   `app/services/entitlements.py`; permissões e isolamento em `app/tenancy.py`
   (`tenant_required`, `get_or_404`) e nos serviços; validação de dados nos formulários do
   servidor e nos serviços.
2. **O front é só painel**: templates e JS (`app/static/js/app.js`, HTMX) apenas exibem o que o
   servidor já calculou e enviam intenções (POST com CSRF). Nenhum cálculo de negócio (%, horas,
   prazo, dias úteis, status), nenhum limite e nenhuma decisão de permissão no navegador.
3. Esconder um botão na tela é conveniência de interface, **nunca** a proteção: a rota recusa
   do mesmo jeito (402/403/404) e há teste disso.
4. Melhorias progressivas no JS são permitidas só para apresentação (abrir folha, foco, tema,
   trocar HTML recebido do servidor). Validação no navegador (ex.: `required`, `min`) é só
   ajuda ao usuário; o servidor valida de novo.
5. A API v1 segue a mesma regra: devolve números já calculados por `calc.py` (`/summary`).

## Consequências
- (+) Uma fonte de verdade testada (paridade com a planilha, testes A/B, limites no backend).
- (+) Segurança: não há regra para contornar no cliente.
- (−) Atualizar indicadores exige ida ao servidor (HTMX troca o fragmento); aceitável para o
  volume do produto.
- Revisão: PR que adicionar cálculo/limite/permissão em template ou JS deve ser recusado;
  `/security-review` confere.

## Alternativas
Duplicar cálculos em JS para atualizar a tela sem requisição — rejeitado (divergência e
brecha). SPA com regras no cliente — rejeitado pelo ADR-0001.
