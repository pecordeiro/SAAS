# Telas — wireframes, hierarquia e dados de exemplo

Status: proposta para aprovação · Atualizado: 2026-10-13 · Componentes: `design-system.md`

Cada tela tem wireframe em **375 px** (celular, ~40 colunas) e **1280 px** (desktop, ~96
colunas), hierarquia de conteúdo (ordem de importância = ordem de leitura e de foco),
componentes usados e dados. Wireframes são estruturais: cores e medidas vêm dos tokens.
Legenda: `[Botão]` primário · `(Botão)` secundário · `‹link›` fantasma/link · `▓▓░░` barra
de progresso · `{Selo}` selo de status · `☰` menu · `‹›` navegação.

## 0. Dados fictícios usados em todas as telas

Etapas **genéricas** (D15 — nada da SoBot). Hoje = ter 13/10/2026, empresa “Metalúrgica
Exemplo Ltda.”, plano Profissional (teste grátis, 5 dias restantes).

**Projeto principal: “Lote 2026-014 · Equipamento compacto CX-10”** — 10 unidades, início
05/10/2026, prazo **23/10/2026**, equipe 3 pessoas × 8 h/dia, seg–sex.

| # | Etapa | Atividade (tempo ideal/un.) | Feitas | Unid. etapa | Progresso etapa | Faltam | Status |
|---|---|---|---|---|---|---|---|
| 1 | Preparação de chassi | Corte e rebarba (60 min) · Furação (45) · Pintura (75) | 10 · 10 · 10 | 10/10 | 100% | 0 h | Concluída |
| 2 | Montagem mecânica | Fixação da base (120) · Montagem de eixos (180) · Alinhamento (60) | 9 · 8 · 7 | 7/10 | 82% | 11 h | Em andamento |
| 3 | Instalação elétrica | Passagem de cabos (150) · Montagem do painel (210) · Conexões (120) | 6 · 5 · 4 | 4/10 | 51% | 39 h 30 min | Em andamento |
| 4 | Testes funcionais | Teste em vazio (90) · Teste com carga (150) | 2 · 2 | 2/10 | 20% | 32 h | Em andamento |
| 5 | Embalagem e expedição | Limpeza final (30) · Embalagem (90) | 1 · 1 | 1/10 | 10% | 18 h | Em andamento |

Indicadores do projeto (fórmulas de `arquitetura.md §1.1`):
- Unidades concluídas: **1 de 10** (mínimo entre etapas).
- Progresso geral: **56%** (1 − 6.030 ÷ 13.800 min).
- Horas que faltam: **100 h 30 min** (tempo total 230 h).
- Dias úteis de trabalho: **4,2** (100,5 h ÷ (3 × 8 h)) → término previsto **20/10/2026**.
- Até o prazo: **8 dias úteis** → **no prazo, folga de 3,8 dias**.

Outros projetos da lista:

| Projeto | Unid. | Progresso | Prazo | Status |
|---|---|---|---|---|
| Lote 2026-014 · Equipamento compacto CX-10 | 1/10 | 56% | 23/10/2026 | Em andamento · no prazo |
| Lote 2026-015 · Painel de comando PC-4 | 0/6 | 12% | 30/10/2026 | Em andamento · 2 dias de atraso previsto |
| Encomenda 2026-009 · Bancada técnica BT-2 | 4/4 | 100% | 09/10/2026 | Concluída |
| Lote 2026-016 · Módulo de transporte MT-1 | 0/20 | 0% | 27/11/2026 | Não iniciada |

Equipe: Ana Souza (proprietária), Carlos Lima (supervisor), João Pereira (operador),
Marina Alves (operadora); convite pendente para rafael.costa@exemplo.com.br (operador).

---

# Telas públicas

Layout `base_publica.html`: cabeçalho com logo + “Controle de Produção”, links Preços ·
Entrar, botão [Teste grátis]; no celular, ☰ abre folha com os links. Rodapé: Termos ·
Privacidade · contato · © 2026.

## 1. Início (`/`)

**Hierarquia:** 1) proposta de valor + CTA teste grátis · 2) prova (painel real) · 3) como
funciona em 3 passos · 4) para quem · 5) preços resumidos · 6) CTA final.

375 px:
```
┌────────────────────────────────────────┐
│ ▣ Controle de Produção             ☰  │
├────────────────────────────────────────┤
│ Saiba onde cada lote está.             │  2xl display
│ Unidades concluídas, horas que faltam  │
│ e prazo em dias úteis. Do celular ao   │
│ escritório, sem planilha.              │
│ [   Começar teste grátis de 14 dias  ] │  lg, largura total
│ ‹Ver preços›                           │
│ Sem cartão · cancela quando quiser     │  muted sm
│ ┌────────────────────────────────────┐ │
│ │ Lote 2026-014 · 10 equipamentos    │ │  painel de prova
│ │ PROGRESSO          FALTAM          │ │  (kpi reais, imagem
│ │ 56%                100 h           │ │   feita em HTML)
│ │ ▓▓▓▓▓▓▓▓▓▓▓░░░░░░░ PRAZO 4,2 d úteis│ │
│ │ {Em andamento}  no prazo           │ │
│ └────────────────────────────────────┘ │
│ COMO FUNCIONA                          │
│ ① Monte o modelo de etapas             │
│   Etapas, atividades e tempo ideal.    │
│ ② Crie o lote e chame a equipe         │
│   Quantidade, prazo, pessoas.          │
│ ③ Registre peças pelo celular          │
│   2 toques; o prazo se recalcula.      │
│ FEITO PARA MONTAGEM                    │
│ Equipamentos, máquinas, painéis…       │
│ PREÇOS                                 │
│ Essencial  R$ 149/mês  3 projetos      │
│ Profissional R$ 349/mês 15 projetos ★  │
│ Empresa   R$ 799/mês  ilimitado        │
│ ‹Comparar planos›                      │
│ [   Começar teste grátis           ]   │
│ Termos · Privacidade · contato         │
└────────────────────────────────────────┘
```
1280 px:
```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ▣ Controle de Produção                                  Preços   Entrar  [Teste grátis]  │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  Saiba onde cada lote está.                     ┌──────────────────────────────────────┐ │
│  Unidades concluídas, horas que faltam e        │ Lote 2026-014 · 10 equipamentos      │ │
│  prazo em dias úteis — do celular ao            │ UNID.   PROGRESSO  FALTAM   PRAZO    │ │
│  escritório, sem planilha.                      │ 1/10    56%        100 h    4,2 d    │ │
│  [Começar teste grátis de 14 dias] ‹Ver preços› │ Preparação de chassi ▓▓▓▓▓▓▓▓ 100%   │ │
│  Sem cartão · cancela quando quiser             │ Montagem mecânica    ▓▓▓▓▓▓░░  82%   │ │
│                                                 │ Instalação elétrica  ▓▓▓▓░░░░  51%   │ │
│                                                 │ Testes funcionais    ▓░░░░░░░  20%   │ │
│                                                 └──────────────────────────────────────┘ │
│  COMO FUNCIONA                                                                           │
│  ① Monte o modelo de etapas   ② Crie o lote e chame a equipe   ③ Registre pelo celular   │
│  texto curto                  texto curto                      texto curto               │
│  PREÇOS  ┌ Essencial ─────┐ ┌ Profissional ★ ─┐ ┌ Empresa ───────┐                       │
│          │ R$ 149/mês     │ │ R$ 349/mês      │ │ R$ 799/mês     │  ‹Comparar planos›    │
│          └────────────────┘ └─────────────────┘ └────────────────┘                       │
│  ┌ faixa grafite ──── Pare de perguntar no chão de fábrica.  [Começar teste grátis] ──┐  │
│  Termos · Privacidade · contato@…                                          © 2026        │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```
Componentes: botão primário lg, kpi, progress, status_badge, bar_chart (horizontal),
cards de preço. SEO: `<h1>` = proposta de valor; og-image.

## 2. Preços (`/precos`)

**Hierarquia:** 1) três planos lado a lado, Profissional destacado (é o do teste) · 2) o que
todos incluem · 3) perguntas frequentes (pagamento, carência, cancelamento, nota fiscal).

| | **Essencial** | **Profissional** ★ | **Empresa** |
|---|---|---|---|
| Preço | R$ 149/mês | R$ 349/mês | R$ 799/mês |
| Projetos ativos | 3 | 15 | ilimitados |
| Usuários | 5 | 25 | 100 |
| Extras | — | — | MFA obrigatório, API |
| CTA | (Começar) | [Começar teste grátis] | (Começar) |

Todos: modelos de etapas, histórico, exportação CSV/XLSX, Pix/boleto/cartão, 14 dias grátis
sem cartão, dados nunca apagados por atraso (7 dias de carência, depois modo leitura).

375 px:
```
┌────────────────────────────────────────┐
│ ▣ Controle de Produção             ☰  │
│ Preços simples, por empresa            │  xl
│ 14 dias grátis no Profissional.        │
│ ┌──────────────────────────────────┐   │
│ │ PROFISSIONAL   {Mais escolhido}  │   │  primeiro no celular
│ │ R$ 349 /mês                      │   │  3xl display
│ │ ✓ 15 projetos ativos             │   │
│ │ ✓ 25 usuários                    │   │
│ │ [ Começar teste grátis         ] │   │
│ └──────────────────────────────────┘   │
│ ┌ ESSENCIAL  R$ 149/mês ──────────┐    │
│ │ ✓ 3 projetos · ✓ 5 usuários     │    │
│ │ ( Começar com o Essencial )     │    │
│ └─────────────────────────────────┘    │
│ ┌ EMPRESA  R$ 799/mês ────────────┐    │
│ │ ✓ ilimitado · ✓ 100 usuários    │    │
│ │ ✓ MFA obrigatório · ✓ API       │    │
│ │ ( Começar com o Empresa )       │    │
│ └─────────────────────────────────┘    │
│ TODOS OS PLANOS INCLUEM  …             │
│ PERGUNTAS ▸ Como pago? ▸ E se atrasar? │  <details>, 44 px
└────────────────────────────────────────┘
```
1280 px:
```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ▣ Controle de Produção                                  Preços   Entrar  [Teste grátis]  │
│                    Preços simples, por empresa — 14 dias grátis                          │
│   ┌ Essencial ──────────┐  ┌ Profissional ★ (borda primária) ┐  ┌ Empresa ────────────┐  │
│   │ R$ 149/mês          │  │ R$ 349/mês                      │  │ R$ 799/mês          │  │
│   │ 3 projetos ativos   │  │ 15 projetos ativos              │  │ Projetos ilimitados │  │
│   │ 5 usuários          │  │ 25 usuários                     │  │ 100 usuários        │  │
│   │                     │  │                                 │  │ MFA obrigatório·API │  │
│   │ (Começar)           │  │ [Começar teste grátis]          │  │ (Começar)           │  │
│   └─────────────────────┘  └─────────────────────────────────┘  └─────────────────────┘  │
│   Tabela comparativa completa (data_table)                                               │
│   Perguntas frequentes (2 colunas de <details>)                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```
Componentes: card de plano (surface + borda; destacado com `--border-width-strong`
`--color-primary`), status_badge, button, data_table.

## 3. Entrar (`/entrar`)

**Hierarquia:** 1) e-mail e senha · 2) Entrar · 3) Esqueci a senha · 4) criar conta.
Etapa extra se MFA ativo: campo de código de 6 dígitos (`inputmode="numeric"`,
`autocomplete="one-time-code"`).

375 px:
```
┌────────────────────────────────────────┐
│ ▣ Controle de Produção                 │
│ Entrar                                 │  xl
│ E-mail                                 │
│ ┌────────────────────────────────────┐ │
│ │ ana@exemplo.com.br                 │ │
│ └────────────────────────────────────┘ │
│ Senha                       ‹Mostrar›  │
│ ┌────────────────────────────────────┐ │
│ │ ••••••••                           │ │
│ └────────────────────────────────────┘ │
│ ☐ Manter conectado neste aparelho      │
│ [            Entrar                  ] │
│ ‹Esqueci a senha›                      │
│ ───────────────────────────────────    │
│ Ainda não tem conta? ‹Cadastre a empresa›│
└────────────────────────────────────────┘
```
Erro: alerta danger no topo “E-mail ou senha incorretos.” (mensagem genérica; após 5
tentativas: “Muitas tentativas. Tente de novo em 15 minutos.”).

1280 px: mesmo formulário centralizado em card `--content-narrow` (440 px) sobre
`--color-bg`; à esquerda (opcional) faixa grafite com logo e frase “Saiba onde cada lote está.”
```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ▣ Controle de Produção                                                                   │
│                        ┌ Entrar ─────────────────────────┐                               │
│                        │ E-mail [______________________] │                               │
│                        │ Senha  [______________] Mostrar │                               │
│                        │ ☐ Manter conectado              │                               │
│                        │ [            Entrar           ] │                               │
│                        │ ‹Esqueci a senha›               │                               │
│                        └─────────────────────────────────┘                               │
│                        Ainda não tem conta? ‹Cadastre a empresa›                         │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## 4. Cadastrar empresa (`/cadastro`)

**Hierarquia:** 1) dados mínimos (nome da empresa, seu nome, e-mail, senha) · 2) aceite de
termos · 3) Criar conta · 4) o que acontece depois (“enviamos um e-mail de confirmação;
14 dias grátis no Profissional, sem cartão”). CNPJ e endereço ficam para Configurações.

375 px:
```
┌────────────────────────────────────────┐
│ ▣ Controle de Produção                 │
│ Comece o teste grátis                  │
│ 14 dias no Profissional · sem cartão   │
│ Nome da empresa                        │
│ [Metalúrgica Exemplo Ltda.          ]  │
│ Seu nome                               │
│ [Ana Souza                          ]  │
│ E-mail de trabalho                     │
│ [ana@exemplo.com.br                 ]  │
│ Senha                       ‹Mostrar›  │
│ [••••••••••                         ]  │
│ Mín. 10 caracteres.                    │  dica
│ ☐ Li e aceito os ‹Termos› e a          │
│   ‹Política de privacidade›            │
│ [          Criar conta              ]  │
│ Já tem conta? ‹Entrar›                 │
└────────────────────────────────────────┘
```
Erro de campo (exemplo): borda danger em E-mail + “Este e-mail já tem conta. ‹Entrar›”.
Sucesso: tela “Confirme seu e-mail” com o endereço, botão (Reenviar e-mail) (desabilitado 60 s,
contador tabular) e ‹Trocar e-mail›.

1280 px: card de 440 px centralizado; à direita, lista “O que você ganha no teste” (3 itens
com ✓) — some no celular.

## 5. Esqueci a senha (`/senha/esqueci` e `/senha/redefinir/<token>`)

**Hierarquia:** 1) e-mail · 2) Enviar link · 3) voltar a Entrar. Resposta sempre igual
(“Se houver conta com esse e-mail, enviamos um link válido por 1 hora.”) para não revelar
cadastros.

375 px:
```
┌────────────────────────────────────────┐
│ ‹ Entrar                               │
│ Esqueci a senha                        │
│ Enviaremos um link para criar uma nova.│
│ E-mail                                 │
│ [ana@exemplo.com.br                 ]  │
│ [        Enviar link                ]  │
│ ┌ ✓ Se houver conta com esse e-mail, ┐ │  alert success (após envio)
│ │   enviamos um link válido por 1 h. │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```
Redefinir: Nova senha + Confirmar + [Salvar nova senha]; token vencido → alerta warning
“Este link venceu. ‹Pedir outro›”.
1280 px: mesmo card de 440 px centralizado.

## 6. Termos de uso e Política de privacidade (`/termos`, `/privacidade`)

**Hierarquia:** 1) título + “Atualizado em” · 2) sumário (âncoras) · 3) texto em seções
numeradas · 4) contato do encarregado (LGPD).

375 px:
```
┌────────────────────────────────────────┐
│ ▣ Controle de Produção             ☰  │
│ Política de privacidade                │
│ Atualizado em 13/10/2026               │  muted
│ ▸ Nesta página (sumário recolhível)    │
│ 1. Quem somos                          │  lg
│ Texto corrido 16 px, linha 1,5…        │
│ 2. Dados que coletamos                 │
│ …                                      │
│ ‹Voltar ao topo›                       │
└────────────────────────────────────────┘
```
1280 px: coluna de texto `--content-text` (720 px) + sumário fixo à esquerda (240 px,
sticky) com item atual destacado.
```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ▣ Controle de Produção                                  Preços   Entrar  [Teste grátis]  │
│  NESTA PÁGINA        │ Política de privacidade                                           │
│  1 Quem somos ◀      │ Atualizado em 13/10/2026                                          │
│  2 Dados coletados   │ 1. Quem somos                                                     │
│  3 Para que usamos   │ Texto corrido, máx. 720 px…                                       │
│  4 Seus direitos     │ 2. Dados que coletamos …                                          │
│  5 Contato (DPO)     │                                                                   │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# Área logada (`/app`)

Layout `base_app.html`:
- **375 px**: barra superior 56 px (logo + nome da empresa abreviado + botão do usuário),
  conteúdo, navegação inferior fixa (Projetos · Histórico · Modelos · Mais). Faixa de
  assinatura (alerta) abaixo da barra quando em teste/carência.
- **1280 px**: menu lateral 248 px + conteúdo até 1200 px; ações da página no cabeçalho.

## 7. Lista de projetos (`/app/projetos`)

**Hierarquia:** 1) projetos ativos com progresso, unidades e situação de prazo · 2) filtro
por status e busca · 3) Novo projeto (supervisor+) · 4) concluídos/arquivados.

375 px:
```
┌────────────────────────────────────────┐
│ ▣ Metalúrgica Exemplo          (AS)    │
│ ┌ ℹ Teste grátis: faltam 5 dias.     ┐ │  alert info
│ │   ‹Escolher plano›                 │ │
│ └────────────────────────────────────┘ │
│ Projetos                    [+ Novo]   │  xl
│ (Ativos ▾)  [🔍 Buscar lote…        ]  │
│ ┌────────────────────────────────────┐ │
│ │ Lote 2026-014                      │ │  card = link inteiro
│ │ Equipamento compacto CX-10         │ │
│ │ ▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░  56%           │ │
│ │ 1/10 un. · faltam 100 h            │ │  tabular
│ │ {Em andamento}  Prazo 23/10 ✓ no prazo│
│ └────────────────────────────────────┘ │
│ ┌────────────────────────────────────┐ │
│ │ Lote 2026-015 · Painel PC-4        │ │
│ │ ▓▓░░░░░░░░░░░░░░░░░  12%           │ │
│ │ 0/6 un. · faltam 84 h              │ │
│ │ {Em andamento} {! 2 dias de atraso}│ │
│ └────────────────────────────────────┘ │
│ ┌ Lote 2026-016 · Módulo MT-1  0% ──┐  │
│ │ {Não iniciada} Prazo 27/11         │ │
│ └────────────────────────────────────┘ │
│ ‹Ver concluídos (1)›                   │
├────────────────────────────────────────┤
│ ▦ Projetos  ↺ Histórico  ☷ Modelos  ⋯ │  bottom nav 64 px
└────────────────────────────────────────┘
```
1280 px:
```
┌────────────┬─────────────────────────────────────────────────────────────────────────────┐
│ ▣ Controle │ Projetos                                    (Exportar) [+ Novo projeto]     │
│ Metalúrgica│ ┌ ℹ Teste grátis: faltam 5 dias. ‹Escolher plano› ────────────────────────┐ │
│ Exemplo ▾  │ [Ativos (3)] [Concluídos (1)] [Todos]          [🔍 Buscar lote ou produto]  │
│▌Projetos   │ PROJETO                     UNID.   PROGRESSO          FALTAM  PRAZO   STATUS│
│ Histórico  │ Lote 2026-014 · CX-10       1/10   ▓▓▓▓▓▓░░░░ 56%     100 h   23/10 {Em and.}│
│ Modelos    │ Lote 2026-015 · PC-4        0/6    ▓░░░░░░░░░ 12%      84 h   30/10 {! Atraso}│
│ Usuários   │ Lote 2026-016 · MT-1        0/20   ░░░░░░░░░░  0%     460 h   27/11 {Não ini.}│
│ Empresa    │                                                   Mostrando 1–3 de 3        │
│ Assinatura │                                                                             │
│ ─────────  │                                                                             │
│ Ana Souza  │                                                                             │
│ Tema ◐ Sair│                                                                             │
└────────────┴─────────────────────────────────────────────────────────────────────────────┘
```
Componentes: sidebar/bottom_nav, alert, data_table (cards no celular), progress,
status_badge, pagination, button, empty_state (ver 16). Operador não vê “Novo”/“Exportar”.

## 8. Detalhe do projeto (`/app/projetos/<id>`) — tela principal

**Hierarquia:** 1) indicadores (unidades, progresso, horas que faltam, dias úteis/prazo) ·
2) etapas com atividades e **registro rápido** · 3) equipe e prazo · 4) atividade recente ·
5) ações (Editar, Exportar, Arquivar — supervisor+).

### Registro rápido em 2 toques (celular)
1. **Toque 1:** tocar na linha da atividade (alvo inteiro ≥ 56 px, mostra “7/10” e botão
   “+”) → abre a folha de registro com quantidade **1**.
2. **Toque 2:** [Registrar +1 (→ 8 de 10)] → HTMX grava, fecha a folha, atualiza linha,
   etapa e indicadores, toast “+1 em Alinhamento · 8 de 10”.

Para registrar mais de 1: −/+ ou digitar no número antes do toque 2. A etapa atual (primeira
não concluída) vem aberta; as demais recolhidas (`<details>`), etapas concluídas no fim.

375 px:
```
┌────────────────────────────────────────┐
│ ‹ Projetos                       ⋯     │
│ Lote 2026-014                          │  xl display
│ Equipamento compacto CX-10             │  muted
│ {Em andamento} ✓ no prazo              │
│ ┌──────────────────┬─────────────────┐ │
│ │ UNIDADES         │ PROGRESSO       │ │  kpi 2×2
│ │ 1/10             │ 56%             │ │  2xl tabular
│ │ concluídas       │ ▓▓▓▓▓▓░░░░      │ │
│ ├──────────────────┼─────────────────┤ │
│ │ FALTAM           │ DIAS ÚTEIS      │ │
│ │ 100 h 30         │ 4,2             │ │
│ │ de 230 h         │ prazo em 8 ✓    │ │
│ └──────────────────┴─────────────────┘ │
│ ETAPAS                     5 · ‹Gráfico›│
│ ┌ ▾ 2 Montagem mecânica  {Em andamento}┐│
│ │ 7/10 un. · 82% ▓▓▓▓▓▓▓▓░░ · 11 h    ││
│ │ ┌──────────────────────────────────┐││
│ │ │ Fixação da base     9/10    [ + ]│││  linha 56 px
│ │ ├──────────────────────────────────┤││
│ │ │ Montagem de eixos   8/10    [ + ]│││
│ │ ├──────────────────────────────────┤││
│ │ │ Alinhamento         7/10    [ + ]│││  ← toque 1
│ │ └──────────────────────────────────┘││
│ └─────────────────────────────────────┘│
│ ▸ 3 Instalação elétrica 4/10 51% {Em a.}│
│ ▸ 4 Testes funcionais   2/10 20% {Em a.}│
│ ▸ 5 Embalagem           1/10 10% {Em a.}│
│ ▸ 1 Preparação chassi 10/10 {Concluída} │
│ EQUIPE E PRAZO                         │
│ 3 pessoas × 8 h/dia · seg–sex          │
│ Início 05/10 · Prazo 23/10/2026        │
│ Término previsto 20/10 (folga 3,8 d)   │
│ ‹Editar›                               │
│ RECENTE                                │
│ 14:32 João P. +1 Alinhamento (7/10)    │
│ ‹Ver histórico do projeto›             │
├────────────────────────────────────────┤
│ ▦ Projetos  ↺ Histórico  ☷ Modelos  ⋯ │
└────────────────────────────────────────┘
```
Folha de registro (após toque 1):
```
┌────────────────────────────────────────┐
│ (conteúdo escurecido pelo overlay)     │
├─────────────── ▬▬ ─────────────────────┤
│ Montagem mecânica › Alinhamento   ✕    │
│ 7 de 10 concluídas · faltam 3          │
│  ┌─────┐   ┌──────────────┐  ┌─────┐   │
│  │  −  │   │      1       │  │  +  │   │  56 px, 3xl
│  └─────┘   └──────────────┘  └─────┘   │
│ [   Registrar +1  (→ 8 de 10)        ] │  ← toque 2 (lg, zona do polegar)
└────────────────────────────────────────┘
```
1280 px:
```
┌────────────┬─────────────────────────────────────────────────────────────────────────────┐
│ ▣ Controle │ ‹Projetos  Lote 2026-014 · Equipamento compacto CX-10                       │
│ …          │ {Em andamento} ✓ no prazo           (Exportar ▾) (Editar) ‹Histórico›       │
│▌Projetos   │ ┌ UNIDADES ──┐ ┌ PROGRESSO ─┐ ┌ FALTAM ─────┐ ┌ DIAS ÚTEIS ─────────────┐   │
│ Histórico  │ │ 1/10       │ │ 56%        │ │ 100 h 30    │ │ 4,2   prazo em 8 ✓      │   │
│ …          │ │ concluídas │ │ ▓▓▓▓▓░░░░  │ │ de 230 h    │ │ término prev. 20/10     │   │
│            │ └────────────┘ └────────────┘ └─────────────┘ └─────────────────────────┘   │
│            │ ETAPAS                                                  │ EQUIPE E PRAZO    │
│            │ # ETAPA                 UNID.  PROGRESSO        FALTAM   │ 3 pessoas × 8 h   │
│            │ 1 Preparação de chassi  10/10  ▓▓▓▓▓▓▓▓ 100%     0 h  {C}│ seg–sex           │
│            │ 2 Montagem mecânica ▾    7/10  ▓▓▓▓▓▓░░  82%    11 h  {E}│ Início 05/10      │
│            │   Fixação da base   120 min   9/10  ▓▓▓▓▓▓▓░  (−)[1](+) [Registrar]│ Prazo 23/10│
│            │   Montagem de eixos 180 min   8/10  ▓▓▓▓▓▓░░  (−)[1](+) [Registrar]│ ‹Editar›   │
│            │   Alinhamento        60 min   7/10  ▓▓▓▓▓░░░  (−)[1](+) [Registrar]│ RECENTE    │
│            │ 3 Instalação elétrica ▸  4/10  ▓▓▓▓░░░░  51%  39 h 30 {E}│ 14:32 João +1   │
│            │ 4 Testes funcionais ▸    2/10  ▓░░░░░░░  20%    32 h  {E}│ 13:05 Marina +2 │
│            │ 5 Embalagem e expedição ▸1/10  ▓░░░░░░░  10%    18 h  {E}│ ‹Ver histórico› │
│            │ ‹Ver gráfico por etapa› (bar_chart horizontal)           │                   │
└────────────┴─────────────────────────────────────────────────────────────────────────────┘
```
No desktop o stepper fica inline na linha da atividade (2 toques: foco/clique já com 1 →
Registrar). Componentes: kpi, progress, status_badge, piece_stepper, data_table, bar_chart,
toast, alert (modo leitura desabilita registro: “Assinatura em modo leitura — registros
pausados”), confirm_dialog (arquivar). Atualização periódica via HTMX a cada 30 s
(pausada com a folha aberta).

## 9. Histórico (`/app/historico` e `/app/projetos/<id>/historico`)

**Hierarquia:** 1) lista cronológica de registros (quando, quem, onde, quanto) · 2) filtros
(projeto, pessoa, período) · 3) gráfico de unidades por dia · 4) exportar · 5) desfazer
(supervisor+, D13).

375 px:
```
┌────────────────────────────────────────┐
│ ▣ Metalúrgica Exemplo          (AS)    │
│ Histórico                  (Filtros 2) │  abre folha de filtros
│ Lote 2026-014 · Últimos 7 dias  ✕      │  filtros ativos (chips 44 px)
│ ┌ PEÇAS POR DIA ─────────────────────┐ │
│ │ ▇   ▅   ▆   ▃   ▇                   │ │  bar_chart vertical
│ │ 07  08  09  12  13                  │ │
│ └────────────────────────────────────┘ │
│ HOJE, 13/10                            │
│ ┌────────────────────────────────────┐ │
│ │ 14:32  João Pereira          +1    │ │
│ │ Montagem mecânica › Alinhamento    │ │
│ │ 6 → 7 de 10                ‹Desfazer›│  supervisor+
│ ├────────────────────────────────────┤ │
│ │ 13:05  Marina Alves          +2    │ │
│ │ Instalação elétrica › Conexões     │ │
│ │ 2 → 4 de 10                        │ │
│ ├────────────────────────────────────┤ │
│ │ 11:40  Carlos Lima   ↶ desfeito    │ │  registro desfeito, riscado
│ │ Testes funcionais › Teste em vazio │ │
│ └────────────────────────────────────┘ │
│ ONTEM, 12/10 (feriado)                 │
│ …                                      │
│ (        Carregar mais              )  │
├────────────────────────────────────────┤
│ ▦ Projetos  ↺ Histórico  ☷ Modelos  ⋯ │
└────────────────────────────────────────┘
```
1280 px:
```
┌────────────┬─────────────────────────────────────────────────────────────────────────────┐
│ menu       │ Histórico                                              (Exportar CSV/XLSX)  │
│            │ Projeto [Lote 2026-014 ▾] Pessoa [Todas ▾] Período [07/10–13/10] (Limpar)   │
│            │ ┌ PEÇAS REGISTRADAS POR DIA ───────────────────────────────────────────────┐│
│            │ │ barras verticais 07/10 … 13/10, valor acima                               ││
│            │ └───────────────────────────────────────────────────────────────────────────┘│
│            │ QUANDO          PESSOA         PROJETO   ETAPA › ATIVIDADE         QTD  DE→PARA│
│            │ 13/10 14:32     João Pereira   2026-014  Mont. mecânica › Alinham.  +1  6→7 ‹Desfazer›│
│            │ 13/10 13:05     Marina Alves   2026-014  Inst. elétrica › Conexões  +2  2→4  │
│            │ 13/10 11:40     Carlos Lima    2026-014  Testes › Teste em vazio  desfeito    │
│            │                                     Mostrando 1–25 de 132  ‹ 1 2 3 … 6 ›    │
└────────────┴─────────────────────────────────────────────────────────────────────────────┘
```
Componentes: data_table, bar_chart vertical, pagination / “Carregar mais”, confirm_dialog
(desfazer: “Desfazer +1 de João Pereira em Alinhamento? O total volta para 6 de 10.”),
empty_state.

## 10. Novo projeto (`/app/projetos/novo`) — supervisor+

**Hierarquia:** 1) modelo de etapas · 2) nome e quantidade · 3) prazo e equipe · 4) resumo
calculado (tempo total, dias úteis necessários, término previsto) · 5) Criar.

375 px:
```
┌────────────────────────────────────────┐
│ ‹ Projetos                             │
│ Novo projeto                           │
│ Modelo de etapas                       │
│ ( ● Equipamento compacto v3 · 5 etapas)│  radio cards 56 px
│ ( ○ Painel de comando v1 · 4 etapas   )│
│ ‹Criar modelo›                         │
│ Nome do projeto                        │
│ [Lote 2026-017                      ]  │
│ Produto (opcional)                     │
│ [Equipamento compacto CX-10         ]  │
│ Quantidade de unidades                 │
│ [ − ] [   10   ] [ + ]                 │  stepper reutilizado
│ Início         Prazo                   │
│ [26/10/2026]   [13/11/2026]            │
│ Pessoas na equipe   Horas por dia      │
│ [ 3 ]               [ 8 ]              │
│ Dias de trabalho ☑S ☑T ☑Q ☑Q ☑S ☐S ☐D │  44 px cada
│ ┌ RESUMO ────────────────────────────┐ │
│ │ 230 h de trabalho                  │ │  atualiza via HTMX
│ │ 9,6 dias úteis · término 09/11     │ │
│ │ ✓ cabe no prazo (14 dias úteis)    │ │
│ └────────────────────────────────────┘ │
│ [          Criar projeto            ]  │
│ ( Cancelar )                           │
└────────────────────────────────────────┘
```
Erro de limite de plano: alerta warning “Seu plano Essencial permite 3 projetos ativos.
Arquive um projeto ou ‹mude de plano›.” e botão Criar desabilitado (checado também no
backend).
1280 px: formulário em 2 colunas (dados à esquerda 640 px; resumo fixo à direita como card
sticky com kpi). Componentes: field, radio card, piece_stepper (modo quantidade), kpi,
alert, button.

## 11. Modelos de etapas (`/app/modelos`, `/app/modelos/<id>`) — supervisor+

**Hierarquia (lista):** 1) modelos com versão, nº de etapas e tempo por unidade ·
2) Novo modelo / Importar CSV. **(editor):** 1) etapas em ordem com atividades e tempo ideal ·
2) tempo total por unidade calculado · 3) Salvar como nova versão (projetos existentes
mantêm a versão antiga).

375 px (editor):
```
┌────────────────────────────────────────┐
│ ‹ Modelos                              │
│ Equipamento compacto   {v3}            │
│ 5 etapas · 23 h por unidade            │
│ ┌ 1 Preparação de chassi    3 h  ⋮ ┐   │  ⋮ = mover/renomear/excluir
│ │ Corte e rebarba      [ 60] min    │   │  campo numérico 44 px
│ │ Furação              [ 45] min    │   │
│ │ Pintura              [ 75] min    │   │
│ │ ‹+ Atividade›                     │   │
│ └───────────────────────────────────┘   │
│ ▸ 2 Montagem mecânica         6 h       │
│ ▸ 3 Instalação elétrica       8 h       │
│ ▸ 4 Testes funcionais         4 h       │
│ ▸ 5 Embalagem e expedição     2 h       │
│ (+ Etapa)                              │
│ ┌ ℹ 2 projetos usam a v3. Ao salvar, ┐ │
│ │ criamos a v4; eles não mudam.      │ │
│ └────────────────────────────────────┘ │
│ [      Salvar como versão 4         ]  │
└────────────────────────────────────────┘
```
1280 px:
```
┌────────────┬─────────────────────────────────────────────────────────────────────────────┐
│ menu       │ Modelos de etapas                          (Importar CSV) [+ Novo modelo]   │
│            │ MODELO                    VERSÃO  ETAPAS  TEMPO/UN.  EM USO   ATUALIZADO    │
│            │ Equipamento compacto      v3      5       23 h       2 proj.  02/10/2026    │
│            │ Painel de comando         v1      4       14 h       1 proj.  20/09/2026    │
│            │ ─ editor (ao abrir) ─ etapas à esquerda (lista ordenável, ↑↓ com teclado),   │
│            │   atividades da etapa selecionada à direita em tabela editável             │
└────────────┴─────────────────────────────────────────────────────────────────────────────┘
```
Reordenar: botões ↑/↓ (44 px) — sem depender de arrastar. Importar CSV: página com
upload, prévia em tabela e erros por linha (“Linha 7: tempo ideal precisa ser número”).
Componentes: data_table, field (numérico), status_badge (versão), alert, confirm_dialog
(excluir etapa), empty_state.

## 12. Usuários e convites (`/app/usuarios`) — proprietário (supervisor vê só leitura)

**Hierarquia:** 1) pessoas ativas com papel · 2) convites pendentes · 3) Convidar ·
4) uso do plano (“4 de 25 usuários”).

375 px:
```
┌────────────────────────────────────────┐
│ Usuários                  [+ Convidar] │
│ 4 de 25 usuários · Profissional        │
│ ▓▓░░░░░░░░░░░░░░░░░░                    │
│ ┌────────────────────────────────────┐ │
│ │ Ana Souza (você)                   │ │
│ │ ana@exemplo.com.br                 │ │
│ │ {Proprietária}                     │ │
│ ├────────────────────────────────────┤ │
│ │ Carlos Lima           {Supervisor} │ │
│ │ carlos@exemplo.com.br        ⋮     │ │  ⋮ → mudar papel / remover
│ ├────────────────────────────────────┤ │
│ │ João Pereira          {Operador}  ⋮│ │
│ │ Marina Alves          {Operadora} ⋮│ │
│ └────────────────────────────────────┘ │
│ CONVITES PENDENTES                     │
│ rafael.costa@exemplo.com.br {Operador} │
│ Enviado 12/10 · vence 19/10            │
│ ‹Reenviar›  ‹Cancelar convite›         │
└────────────────────────────────────────┘
```
Convidar (folha/modal): E-mail + Papel (radio com descrição: Operador “registra peças”,
Supervisor “monta projetos e exporta”, Proprietário “tudo, inclusive assinatura”) +
[Enviar convite]. Remover usuário → confirm_dialog perigo.
1280 px: data_table (Nome · E-mail · Papel · Último acesso · MFA · ações) + seção de
convites abaixo; uso do plano no cabeçalho.

## 13. Configurações da empresa (`/app/empresa`) — proprietário

**Hierarquia:** 1) dados da empresa (nome, CNPJ, endereço de cobrança) · 2) calendário
(dias de trabalho padrão, horas/dia padrão, feriados próprios; feriados nacionais
automáticos) · 3) segurança (exigir MFA — plano Empresa) · 4) dados e LGPD (exportar tudo,
excluir empresa).

375 px:
```
┌────────────────────────────────────────┐
│ Empresa                                │
│ [Dados] [Calendário] [Segurança] [Dados e LGPD]│ abas roláveis, 44 px
│ Nome   [Metalúrgica Exemplo Ltda.   ]  │
│ CNPJ   [12.345.678/0001-90          ]  │
│ E-mail de cobrança [financeiro@…    ]  │
│ [            Salvar                 ]  │
│ ── Calendário ──                       │
│ Padrão: 8 h/dia · seg–sex              │
│ Feriados da empresa         (+ Feriado)│
│ 24/12/2026  Recesso de fim de ano  ✕   │
│ Nacionais: automáticos ✓               │
│ ── Dados e LGPD ──                     │
│ (Exportar todos os dados)              │
│ ( Excluir a empresa )  ← perigo, modal │
└────────────────────────────────────────┘
```
1280 px: navegação de seções à esquerda do conteúdo (lista vertical) e formulário de
720 px. Componentes: field, data_table (feriados), alert, confirm_dialog (excluir empresa:
digitar o nome).

## 14. Assinatura e faturas (`/app/assinatura`) — proprietário

**Hierarquia:** 1) situação (plano, status, próxima cobrança/fim do teste) · 2) ação
principal (Escolher plano / Pagar fatura em aberto) · 3) uso vs. limites · 4) faturas ·
5) forma de pagamento e cancelamento.

375 px:
```
┌────────────────────────────────────────┐
│ Assinatura                             │
│ ┌────────────────────────────────────┐ │
│ │ Profissional   {Teste grátis}      │ │
│ │ Faltam 5 dias (até 18/10/2026)     │ │
│ │ [     Escolher plano e pagar     ] │ │
│ └────────────────────────────────────┘ │
│ USO                                    │
│ Projetos ativos  3 de 15 ▓▓▓░░░░░░░░   │
│ Usuários         4 de 25 ▓▓░░░░░░░░░   │
│ FATURAS                                │
│ ┌────────────────────────────────────┐ │
│ │ Nenhuma fatura ainda.              │ │  empty_state compacto
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```
Variante ativa com faturas (dados): 18/10/2026 R$ 349,00 {Paga} Pix ‹Recibo› ·
18/11/2026 R$ 349,00 {Em aberto} Boleto ‹Pagar›. Carência: alerta warning “Fatura de
18/11 em atraso. Em 5 dias a conta entra em modo leitura (nada é apagado). ‹Pagar agora›”.
Modo leitura: alerta danger fixo em todas as telas logadas.
Escolher plano: 3 cards (como Preços) → forma de pagamento (Pix · Boleto · Cartão, radio
cards 56 px) → confirmação.
1280 px: situação + uso lado a lado (2 cards), data_table de faturas abaixo (Vencimento ·
Valor · Forma · Status · ações), ‹Cancelar assinatura› discreto no rodapé.

## 15. Erros 404 e 403

**Hierarquia:** 1) o que houve em linguagem simples · 2) saída (voltar para Projetos /
início). Recurso de outra empresa responde **404** (regra 1) — mesma tela, sem revelar
existência.

375 px / 1280 px (centralizado, `--content-narrow`):
```
┌────────────────────────────────────────┐
│ ▣                                      │
│ 404                                    │  3xl display, muted
│ Página não encontrada                  │  xl
│ O endereço pode ter mudado ou você não │
│ tem acesso a este item.                │
│ [      Ir para Projetos             ]  │
│ ‹Página inicial›                       │
└────────────────────────────────────────┘
```
403: “Você não tem permissão para isto” + “Peça a um supervisor ou proprietário.” +
[Voltar]. 500: “Algo deu errado do nosso lado. Já fomos avisados.” + código do erro
(mono) para suporte. Layout logado mantém menu; público mantém cabeçalho do site.

## 16. Estados vazios e de carregamento

| Tela | Estado vazio (título · texto · ação) |
|---|---|
| Projetos (empresa nova) | “Nenhum projeto ainda” · “Crie um modelo de etapas e depois o primeiro lote.” · [Criar modelo de etapas] (se já houver modelo: [Novo projeto]) |
| Projetos (operador) | “Nenhum projeto para você” · “Quando um supervisor criar um projeto, ele aparece aqui.” · — |
| Projetos (filtro) | “Nenhum projeto com esses filtros” · ‹Limpar filtros› |
| Detalhe sem registros | Indicadores mostram 0 e “—”; etapa 1 aberta; dica “Toque em + para registrar a primeira peça.” |
| Histórico | “Nenhum registro neste período” · “Os registros aparecem quando alguém soma peças.” · ‹Ir para Projetos› |
| Modelos | “Nenhum modelo de etapas” · “Monte etapas e atividades com tempo ideal, ou importe um CSV.” · [Novo modelo] (Importar CSV) |
| Usuários | “Só você por aqui” · “Convide supervisores e operadores.” · [Convidar] |
| Faturas | “Nenhuma fatura ainda” · “A primeira chega ao fim do teste.” |

Carregamento:
- **Página inteira**: renderizada no servidor (sem spinner de página).
- **Fragmentos HTMX** > 400 ms: skeleton com a forma final — indicadores (4 blocos
  `--color-surface-2` 2xl), linhas de tabela (5 barras), cards de projeto (3 cards com
  barra), gráfico (barras cinza).
- **Botões**: estado carregando (“Salvando…”, spinner, largura mantida).
- **Registro de peças**: botão Registrar carregando; stepper bloqueado; sem otimismo
  (o número só muda com resposta do servidor, para não mentir no chão de fábrica).
- **Sem conexão**: alerta warning “Sem conexão. O registro não foi salvo — tente de novo.”

375 px (skeleton do detalhe):
```
┌────────────────────────────────────────┐
│ ‹ Projetos                             │
│ ████████████                           │
│ ┌────────────────┬───────────────────┐ │
│ │ ▒▒▒▒▒▒         │ ▒▒▒▒▒▒            │ │
│ │ ████           │ ████              │ │
│ ├────────────────┼───────────────────┤ │
│ │ ▒▒▒▒▒▒         │ ▒▒▒▒▒▒            │ │
│ │ ████           │ ████              │ │
│ └────────────────┴───────────────────┘ │
│ ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒          │
│ ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒                 │
└────────────────────────────────────────┘
```
1280 px: mesmo princípio, 4 indicadores em linha + 5 linhas de tabela.

---

## Checklist da Fase 1 (telas × larguras)

| Tela | 375 | 1280 |
|---|---|---|
| 1 Início | ✓ | ✓ |
| 2 Preços | ✓ | ✓ |
| 3 Entrar (+ MFA) | ✓ | ✓ |
| 4 Cadastrar empresa (+ confirme o e-mail) | ✓ | ✓ (descrito) |
| 5 Esqueci / redefinir senha | ✓ | ✓ (descrito) |
| 6 Termos e privacidade | ✓ | ✓ |
| 7 Lista de projetos | ✓ | ✓ |
| 8 Detalhe do projeto + folha de registro (2 toques) | ✓ | ✓ |
| 9 Histórico | ✓ | ✓ |
| 10 Novo projeto | ✓ | ✓ (descrito) |
| 11 Modelos de etapas (lista + editor + importar) | ✓ | ✓ |
| 12 Usuários e convites | ✓ | ✓ (descrito) |
| 13 Configurações da empresa | ✓ | ✓ (descrito) |
| 14 Assinatura e faturas | ✓ | ✓ (descrito) |
| 15 404 / 403 / 500 | ✓ | ✓ |
| 16 Estados vazios e carregamento | ✓ | ✓ |

Pendente para a aprovação (Fase 1): você confirmar a direção de marca (registrar em
`progresso.md`) e validar o fluxo de 2 toques num protótipo — como não há Claude Design, a
demonstração em 375 px acontece na Fase 2 com a tela real (captura Playwright).
