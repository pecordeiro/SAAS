# ADR-0019 — Planos novos, briefing de identidade visual e agendamento de ligação

- Status: **aceito**. Aprovado pelo dono em 2026-10-23 (planos, briefing, agendamento, padrões abaixo e
  melhorias da importação de planilhas). Altera as decisões D2–D4 do PRD e a ADR de planos da Etapa B.

## Decisão

### 1. Planos (códigos de plano não mudam: só preço, limites e textos)
| Código | Nome | Preço/mês | Projetos | Pessoas | Teste grátis | Extras |
|---|---|---|---|---|---|---|
| `essencial` | Essencial | R$ 249,90 | 5 | 5 | 14 dias | — |
| `profissional` | Profissional | R$ 497,90 | 10 | 25 | 14 dias | — |
| `empresa` | Empresa | R$ 997,90 | ilimitado | ilimitado | não | MFA obrigatório, API, identidade visual adaptada do site (`visual_custom`) |
| `implantacao` | Implantação | sob orçamento (online ou presencial) | ilimitado | ilimitado | não | tudo do Empresa + implantação pela equipe técnica, 1 mês de acompanhamento e manutenção, treinamento |

- Implantação, acompanhamento de um mês e treinamento são **serviços**: aparecem como texto do plano, sem limite
  nem checagem no código. O plano `implantacao` continua fora do autosserviço (`billing-admin set-plan`).
- Trial de 14 dias só nos planos `essencial` e `profissional` (mantido; o dono não pediu mudança).
- Ainda não há cliente pagante nos preços antigos: os planos são **substituídos** (migration de dados nova;
  `flask seed-plans` sincroniza).

### 2. Briefing de identidade visual (planos `empresa` e `implantacao`)
- Dado **da empresa**: tabela com `company_id`, RLS `tenant_isolation`, isolamento A/B. O proprietário preenche e
  acompanha. Só quem está num plano com `visual_custom` acessa (checado no backend; sem o plano → 404).
- Campos: nome da empresa e dos produtos, cores de preferência, fontes de preferência, sites de referência,
  tom de voz (formal, neutro, descontraído ou em branco), contato para a ligação, logo e fotos de produto
  (armazenamento atual de fotos, só imagens, com limite).
- Estados: nova → briefing preenchido → em andamento → entregue (`VisualRequest` segue sendo o registro da
  plataforma; o briefing vive na empresa).
- O painel `/interno` **não lê o conteúdo do briefing** nesta entrega: mostra só status e horários. Ler o conteúdo
  é leitura entre empresas e fica para a decisão do acesso do profissional (item 4).

### 3. Agendamento da ligação
- A equipe cadastra horários disponíveis em `/interno` (dado da plataforma, sem `company_id`).
- O proprietário vê só horários livres e escolhe um. A reserva é atômica no servidor (restrição única por horário):
  horário ocupado é recusado mesmo com a tela desatualizada. Fuso: America/Sao_Paulo.
- E-mail de confirmação ao cliente e à equipe. Remarcar: o cliente pede pela tela; a equipe decide no painel.
- Spam: limite por IP e por empresa nas rotas novas e campo armadilha (honeypot) nos formulários.

### 4. E-mail de auditoria / profissional (plano `implantacao`) — **a definir**
- O dono vai abrir o e-mail depois (um profissional). Regra de acesso (o que lê, por quanto tempo, com MFA) fica
  para outro ADR quando o endereço existir. Nada deste ADR concede leitura de dado de cliente à equipe.

### 5. Importação de planilhas
- Mantém o mapeamento de colunas por lista (dropdown), sem arrastar. Acrescenta: texto de ajuda e exemplo por
  campo; seletor **minutos ou horas** para o tempo, com a conversão mostrada na prévia (o servidor converte e
  valida; o navegador só exibe).

## Consequências
- `plans.py`, testes que fixam números, páginas públicas de preços e docs (`prd.md`, `pagamentos.md`,
  `lancamento.md`) são atualizados.
- Duas tabelas novas de empresa (briefing, reserva) e uma de plataforma (horário), por migration Alembic revisada.
- O isolamento e o RLS dessas tabelas só ficam provados no PostgreSQL; até lá, valem os testes em SQLite.
