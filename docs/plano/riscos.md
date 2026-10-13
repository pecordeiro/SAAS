# Riscos

Escala: probabilidade e impacto em Baixo/Médio/Alto.

## Técnicos

| # | Risco | Prob. | Impacto | Mitigação | Fase |
|---|---|---|---|---|---|
| T1 | Vazamento entre empresas (IDOR, consulta sem `company_id`) | M | A | `tenancy.scoped/get_or_404`; teste A/B por rota; teste do `url_map`; RLS como 2ª barreira; security-guidance | 0, 3, 7 |
| T2 | Erro de cálculo de prazo/horas mina a confiança | M | A | `calc.py` puro com casos conferidos à mão; feriados por empresa; teste de propriedade | 0, 4 |
| T3 | Registros simultâneos sobrescrevem progresso | M | M | `progress_entries` append-only com delta; `version` otimista e 409 | 0, 6 |
| T4 | Webhook do Asaas repetido, fora de ordem ou forjado | A | A | `compare_digest`; UNIQUE no id; consulta ao Asaas em dúvida; reconciliação diária | 8 |
| T5 | Migration quebra produção | B | A | migrations revisadas, downgrade testado no CI, pre-deploy, backup antes do release | 3, 10 |
| T6 | RLS complica pool de conexões e jobs | M | M | `SET LOCAL` por transação; papel de plataforma separado; flag `RLS_ENABLED` | 3 |
| T7 | Design se afasta do código | M | B | mudanças visuais só pelo Claude Design + handoff; teste de cores/px soltos | 2, 6 |
| T8 | Dependência vulnerável | M | M | versões fixadas, pip-audit no CI, Dependabot | 7 |
| T9 | Repositório começou vazio: retrabalho na fase 2 sobre telas provisórias | A | B | telas da fase 0 deliberadamente mínimas | 0 |

## Produto

| # | Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|---|
| P1 | Operador não registra no celular (luvas, pressa) | M | A | campo numérico grande, ≤ 2 toques, teste de usabilidade na fábrica do piloto |
| P2 | Modelo de etapas não reflete a realidade de cada fábrica | M | M | modelos editáveis e versionados; importação CSV; usar a pasta de referência do cliente |
| P3 | Preço fora da disposição de pagar | M | A | validar D2/D3 com 3 clientes antes da fase 8; teste grátis de 14 dias |
| P4 | Volta para a planilha | M | A | exportação XLSX igual à tela; importação fácil; onboarding assistido |
| P5 | Escopo cresce (Gantt, estoque, ERP) | A | M | tabela “fica para depois” do PRD; ADR para cada desvio |

## Legais e LGPD

| # | Risco | Prob. | Impacto | Mitigação | Fase |
|---|---|---|---|---|---|
| L1 | Tratamento de dados pessoais (nome, e-mail, IP) sem base legal clara | M | A | inventário em `lgpd.md`; base legal: execução de contrato e legítimo interesse; política de privacidade | 7 |
| L2 | Transferência internacional (hospedagem fora do Brasil) | M | M | declarar na política (art. 33); contrato com operadores; avaliar região Brasil | 7, 10 |
| L3 | Pedido de exclusão/portabilidade sem processo | M | M | exportação ZIP e exclusão com carência de 30 dias pelo proprietário | 7 |
| L4 | Incidente de segurança sem comunicação à ANPD/titulares | B | A | `incidentes.md` com prazos (comunicação à ANPD em até 3 dias úteis, Res. CD/ANPD 15/2024) | 7 |
| L5 | Cobrança sem nota fiscal ou com enquadramento tributário errado | M | A | decisão D6 com contador antes da fase 8 | 8 |
| L6 | Termos e privacidade sem revisão jurídica | A | M | marcados como rascunho; revisão é critério go/no-go | 7, 10 |
| L7 | Logs com dados pessoais ou segredos | M | M | logs JSON filtrados; Sentry com scrub; retenção de 90 dias | 7 |
