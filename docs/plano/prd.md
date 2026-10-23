# PRD — Controle de Produção

Status: rascunho para aprovação · Dono: @Pedro · Atualizado: 2026-10-13

## 1. Problema

Pequenas e médias indústrias de montagem acompanham a produção em planilhas, quadros
brancos ou de memória. Isso causa três dores:

- **Ninguém sabe onde o lote está.** Quantas unidades passaram por cada etapa, quantas
  faltam e quanto tempo de trabalho ainda resta só se descobre perguntando no chão de fábrica.
- **Prazo vira chute.** Sem horas restantes e calendário de dias úteis, a data prometida ao
  cliente não se apoia em dados.
- **A planilha não aguenta a equipe.** Várias pessoas editando o mesmo arquivo geram versões
  conflitantes, fórmulas quebradas e nenhum histórico de quem fez o quê.

## 2. Público

Indústrias de montagem com **5 a 200 funcionários** (equipamentos, máquinas, painéis,
mobiliário técnico), que produzem por lotes ou encomendas com etapas repetíveis.
Usam o sistema no escritório (desktop) e no chão de fábrica (celular, às vezes com luvas e
luz forte).

## 2.1 Base: o que já existe

A equipe hoje usa a planilha `acompanhamento_montagem_v4.xlsx` (robô SoBot: 24 etapas,
subatividades com tempo ideal em minutos, meta de robôs, peças concluídas) e um painel local
em Flask que lê e grava esse Excel (`pecordeiro/controle-de-atividades`, só Windows + Excel,
sem login nem histórico). O SaaS **mantém as regras de cálculo** (ver `arquitetura.md §1.1`),
troca a planilha por banco de dados e acrescenta multiempresa, login, histórico, modelos
de etapas editáveis, pagamento e hospedagem na nuvem. As “próximas atualizações” do README antigo
(Postgres, login e perfis, histórico, etapas configuráveis) são exatamente o MVP aqui.

## 3. Personas

| Persona | Quem é | O que precisa | Papel no sistema |
|---|---|---|---|
| **Proprietário** | Dono ou gerente geral | Ver todos os projetos, prazos e gargalos; pagar a assinatura; gerir a equipe | `owner` |
| **Supervisor** | Líder de produção ou PCP | Montar projetos a partir de modelos, distribuir trabalho, acompanhar progresso, exportar | `supervisor` |
| **Operador** | Montador ou técnico | Registrar peças concluídas rápido, pelo celular, em até 2 toques | `operator` |

## 4. Jornadas principais

1. **Adoção** — Proprietário cadastra a empresa, confirma o e-mail, inicia o teste grátis,
   convida supervisores e operadores.
2. **Montar um projeto** — Supervisor cria um modelo de etapas (ou importa CSV), cria um
   projeto “Lote de 10 equipamentos” a partir dele, define prazo e equipe.
3. **Registrar progresso** — Operador abre o projeto no celular, toca na atividade e soma
   unidades. Indicadores e etapa se atualizam na hora.
4. **Acompanhar e prometer prazo** — Supervisor vê unidades concluídas, % de progresso, horas
   restantes e dias úteis até o prazo; consulta o histórico; exporta CSV/XLSX.
5. **Pagar** — Ao fim do teste, proprietário escolhe plano e paga por Pix, boleto ou cartão.
   Se atrasar, entra em carência e depois em modo leitura, sem perder dados.

## 5. Escopo do MVP

O MVP está pronto quando **uma empresa externa cria a conta, convida a equipe, monta um
projeto a partir de um modelo, registra progresso pelo celular, exporta os dados e paga a
assinatura, sem nunca enxergar dados de outra empresa.**

| Área | Entra no MVP | Fica para depois |
|---|---|---|
| Site público | Início, preços, termos, privacidade, SEO básico | Blog, casos de clientes, vários idiomas |
| Contas | Cadastro, confirmação de e-mail, convites, reset de senha, papéis, MFA TOTP | SSO corporativo (Google/Microsoft), SCIM |
| Produção | Projetos, modelos versionados, etapas, atividades, progresso, histórico, prazo | Gantt, dependências entre etapas, previsão por IA |
| Dados | Importar CSV, exportar CSV e XLSX, exportação LGPD | Integrações prontas com ERP |
| Pagamento | Teste grátis, 1 assinatura mensal por empresa, Pix/boleto/cartão, carência | Plano anual, cupons, nota fiscal automática |
| API de publicação | Contrato OpenAPI, tabelas, tokens e 2 rotas atrás de flag | Webhooks de saída ativos, servidor MCP |
| Operação | Staging e produção, backups testados, monitoramento | Multirregião, SLA contratual |

### Fora de escopo (explícito)
App nativo, SPA/React, planilha como fonte de dados, controle de estoque, apontamento de
horas por pessoa para folha de pagamento, emissão de NF-e pelo sistema.

## 6. Métricas de sucesso

| Métrica | Meta no piloto (90 dias) | Como medir |
|---|---|---|
| Ativação: empresa cria 1º projeto em até 24 h do cadastro | ≥ 60% | eventos `company.created` → `project.created` |
| Uso no chão: registros de progresso feitos pelo celular | ≥ 50% dos registros | user-agent/viewport no evento `activity.progress_updated` |
| Retenção semanal: empresas com registro em ≥ 3 dias da semana | ≥ 50% | domain_events por empresa/dia |
| Conversão teste → pago | ≥ 20% | subscriptions `trialing` → `active` |
| Tempo para registrar peças | ≤ 5 s, ≤ 2 toques | teste de usabilidade + Playwright |
| Incidentes de isolamento entre empresas | 0 | testes A/B + auditoria |

## 7. Requisitos não funcionais

- Português do Brasil; fuso `America/Sao_Paulo`; calendário de dias úteis com feriados
  nacionais e feriados próprios da empresa.
- Responsivo de 375 px a 1280+ px; alvos de toque ≥ 44 px; WCAG 2.1 AA.
- p95 < 300 ms nas páginas da área logada com 50 projetos ativos.
- Nenhuma requisição a terceiros no navegador (CSP estrita).
- LGPD: inventário de dados, exportação e exclusão da empresa.

## 7a. Planos (Etapa B)

Fonte única: tabela `plans` (semeada pelas migrations `b1e7c9d2a4f6` e `a9d3f5c1b7e2` (ADR-0019) e por `flask seed-plans`
a partir de `app/services/plans.py`). Telas e limites leem do banco; o servidor decide tudo.

| Plano | Código | Preço/mês | Projetos ativos | Pessoas | Teste grátis | Recursos | Como contrata |
|---|---|---|---|---|---|---|---|
| Essencial | `essencial` | R$ 249,90 | 5 | 5 | 14 dias | — | Autosserviço (Asaas) |
| Profissional | `profissional` | R$ 497,90 | 10 | 25 | 14 dias (plano do cadastro) | — | Autosserviço (Asaas) |
| Empresa | `empresa` | R$ 997,90 | ilimitado | ilimitado | não (cobrança imediata) | MFA obrigatório, API, identidade visual adaptada do site | Autosserviço (Asaas); abre requisição de identidade visual (Etapa C, evento `plan.visual_custom_contracted`) |
| Implantação | `implantacao` | sob orçamento (online ou presencial) | ilimitado | ilimitado | não | tudo do Empresa + implantação pela equipe técnica, 1 mês de acompanhamento e manutenção, treinamento do sistema (serviços: só texto, sem checagem no código) | Só a equipe: `flask billing-admin set-plan --plan implantacao --reason ...` |

## 8. Decisões pendentes

Só você pode decidir. Cada item já tem uma sugestão padrão, usada no plano até você trocar.

| # | Decisão | Sugestão padrão | Por quê | Prazo |
|---|---|---|---|---|
| D1 | Nome do produto | “Controle de Produção” (provisório; 3 alternativas saem do Prompt 1) | Descritivo, fácil de achar | Antes da Fase 1 |
| D2 | Planos e limites | **Decidido (ADR-0019, substitui a Etapa B)**: Essencial 5 projetos ativos, 5 pessoas · Profissional 10 projetos, 25 pessoas · Empresa ilimitado + MFA obrigatório + API + identidade visual adaptada do site · Implantação = tudo do Empresa + implantação pela equipe técnica, 1 mês de acompanhamento e manutenção, treinamento (ver tabela abaixo) | Escala com o tamanho da fábrica | Resolvido |
| D3 | Preço mensal | **Decidido (ADR-0019)**: Essencial R$ 249,90 · Profissional R$ 497,90 · Empresa R$ 997,90 · Implantação sob orçamento (online ou presencial). Não havia cliente pagante nos preços antigos (R$ 149/349/799 e depois R$ 497,00/997,00): só substituídos | Valor validado pelo usuário | Resolvido |
| D4 | Teste grátis | **Decidido (Etapa B, mantido no ADR-0019)**: 14 dias, sem cartão, só no Essencial e no Profissional; cadastro novo começa no Profissional. Empresa sem teste (cobrança imediata); Implantação fora do autosserviço | Tempo para rodar 1 lote completo | Resolvido |
| D5 | Carência após vencimento | 7 dias, depois modo leitura (nunca apaga dados); plano sob consulta (Implantação) não passa pelo recálculo do Asaas | Boleto compensa em até 3 dias úteis | Resolvido |
| D6 | Nota fiscal | Emitida manualmente por você (ou contador) no MVP; automação depois | Evita integração fiscal no MVP. **Converse com um contador antes de cobrar.** | Antes da Fase 8 |
| D7 | Hospedagem | Render (web + worker + Redis) + Postgres gerenciado do Render, região mais próxima do Brasil disponível | Simples, IaC com render.yaml, backups gerenciados | Antes da Fase 10 |
| D8 | E-mail transacional | Resend | API simples, SPF/DKIM guiados | Antes da Fase 5 |
| D9 | Monitoramento de erros | Sentry (plano gratuito) com filtro de dados sensíveis | Padrão de mercado | Antes da Fase 7 |
| D10 | Domínio | `controleproducao.com.br` (verificar disponibilidade no Registro.br) | Área logada em `/app` no mesmo domínio | Antes da Fase 10 |
| D11 | Unidade de tempo das atividades | **Minutos por unidade (“tempo ideal”)**, como na planilha de referência | Mesmo dado que a equipe já preenche | Antes da Fase 0 |
| D12 | Jornada e equipe padrão | **8 h/dia por pessoa**, 1 pessoa, seg–sex, por projeto (valores da aba Equipe); feriados opcionais por empresa | Igual à planilha; feriados são melhoria | Antes da Fase 0 |
| D13 | Quem pode registrar progresso | Operador, supervisor e proprietário; só supervisor+ desfaz registros | Operador não apaga histórico | Antes da Fase 4 |
| D14 | Material de referência | **Resolvido**: planilha `acompanhamento_montagem_v4.xlsx` (em `docs/referencia/`) e repositório `pecordeiro/controle-de-atividades` são a base funcional. A pasta local “Pré-montagem de referencia base” continua inacessível ao ambiente na nuvem; envie-a se tiver algo além da planilha | Regras e dados reais já estão no plano | — |
| D15 | Dados da SoBot nos exemplos e seed | Usar etapas genéricas fictícias no `seed-demo` e em testes públicos; manter os nomes reais só em `docs/referencia/` | O README do repositório antigo pede cautela sem autorização da empresa | Antes da Fase 0 |
