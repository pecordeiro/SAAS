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

## 8. Decisões pendentes

Só você pode decidir. Cada item já tem uma sugestão padrão, usada no plano até você trocar.

| # | Decisão | Sugestão padrão | Por quê | Prazo |
|---|---|---|---|---|
| D1 | Nome do produto | “Controle de Produção” (provisório; 3 alternativas saem do Prompt 1) | Descritivo, fácil de achar | Antes da Fase 1 |
| D2 | Planos e limites | Essencial: 3 projetos ativos, 5 usuários · Profissional: 15 projetos, 25 usuários · Empresa: ilimitado, 100 usuários + MFA obrigatório + API | Escala com o tamanho da fábrica | Antes da Fase 8 |
| D3 | Preço mensal | Essencial R$ 149 · Profissional R$ 349 · Empresa R$ 799 | Abaixo de um salário de apontador; validar com 3 clientes | Antes da Fase 8 |
| D4 | Teste grátis | 14 dias, sem cartão, no plano Profissional | Tempo para rodar 1 lote completo | Antes da Fase 8 |
| D5 | Carência após vencimento | 7 dias, depois modo leitura (nunca apaga dados) | Boleto compensa em até 3 dias úteis | Antes da Fase 8 |
| D6 | Nota fiscal | Emitida manualmente por você (ou contador) no MVP; automação depois | Evita integração fiscal no MVP. **Converse com um contador antes de cobrar.** | Antes da Fase 8 |
| D7 | Hospedagem | Render (web + worker + Redis) + Postgres gerenciado do Render, região mais próxima do Brasil disponível | Simples, IaC com render.yaml, backups gerenciados | Antes da Fase 10 |
| D8 | E-mail transacional | Resend | API simples, SPF/DKIM guiados | Antes da Fase 5 |
| D9 | Monitoramento de erros | Sentry (plano gratuito) com filtro de dados sensíveis | Padrão de mercado | Antes da Fase 7 |
| D10 | Domínio | `controleproducao.com.br` (verificar disponibilidade no Registro.br) | Área logada em `/app` no mesmo domínio | Antes da Fase 10 |
| D11 | Unidade de tempo das atividades | Horas-padrão por unidade (ex.: 1,5 h/unidade) | Permite calcular horas restantes | Antes da Fase 0 |
| D12 | Jornada de trabalho padrão | 8,8 h/dia, seg–sex, configurável por empresa | Comum em indústria (44 h/semana) | Antes da Fase 0 |
| D13 | Quem pode registrar progresso | Operador, supervisor e proprietário; só supervisor+ desfaz registros | Operador não apaga histórico | Antes da Fase 4 |
| D14 | Pasta de referência “Pré-montagem de referencia base” | Enviar ao repositório em `docs/referencia/` para orientar etapas, campos e cálculos | O container na nuvem não acessa o disco local | Antes da Fase 0 |
