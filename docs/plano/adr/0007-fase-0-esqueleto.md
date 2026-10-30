# ADR-0007 — Fase 0 (esqueleto) antes da base visual

- Status: proposto, aguarda aprovação · Data: 2026-10-13

## Contexto
O roteiro assume um repositório com `calc.py`, `tenancy.py`, telas e testes. O repositório
começou vazio. A fase 2 (“migre as telas existentes”) e a regra “preserve o que já
funciona” não têm sobre o que agir.

## Decisão
Inserir a **Fase 0 — Esqueleto** (ver `roadmap.md`): app factory, modelos mínimos, primeira
migration, `tenancy.py`, `calc.py`, login/cadastro básicos, telas provisórias, testes de
cálculo e de isolamento, CI. Ela roda em paralelo com a Fase 1 (Claude Design) e é
pré-requisito das fases 2 e 3.

## Consequências
- (+) As regras invioláveis valem desde o primeiro commit de código.
- (+) A fase 2 tem telas reais para migrar e testes para manter verdes.
- (−) Uma sessão a mais; telas provisórias serão descartadas na fase 2.

## Alternativas
Começar direto pela fase 2 criando tudo junto: mistura design com regras de negócio e
dificulta a revisão.
