# ADR-0014 — Foco do produto em etapas; o resto é opcional

- Status: **aceito** em 2026-10-21, com a decisão D1 = os dois modos (simples como padrão). Ver `docs/plano/reestruturacao.md`.

## Contexto
O dono definiu que a função central do SaaS é acompanhar a produção por **etapas**: progresso,
status, prazo previsto em dias úteis e horas que faltam. O modelo atual gira em torno de
atividades e registro de peças (unidades). Fotos, checklist, número de série, atribuição, alertas,
relatório, "aguardando peça" e API foram construídos como parte do fluxo principal e precisam
sair do caminho principal sem serem removidos.

## Proposta
1. **Núcleo:** projeto → etapas → progresso e status de cada etapa, prazo e horas restantes.
2. **Opcional, rotulado como opcional e desligado por padrão, por empresa:**
   atividades e registro de peças; número de série; fotos e comentários; checklist de inspeção;
   atribuição e progresso por pessoa; alertas e relatório semanal; "aguardando peça";
   painel de identidade visual; API.
3. **Tela inicial:** dashboard visual da operação (progresso geral, etapas com cor de status,
   o que está atrasado e o que precisa de ação). A lista de projetos vira a segunda tela.
4. **Importação e exportação:** o usuário envia a própria planilha e mapeia as colunas
   (etapa, prazo, progresso). A exportação segue o padrão visual da planilha de referência.

## Decisão em aberto
- **Opção A:** o progresso é lançado direto na etapa (ex.: "60% concluída"). Atividades e peças
  viram opcionais.
- **Opção B:** a etapa continua calculada a partir das atividades (conta da planilha de
  referência), mas a tela principal mostra só a etapa.

## Consequências (se aprovado)
- `calc.py` e os testes de paridade com a planilha mudam conforme a opção escolhida.
- Migrations só para novos campos de configuração (opcional por empresa); nenhum dado é apagado.
- Os recursos opcionais continuam testados e isolados por empresa.
- Requer nova rodada de conferência visual (375, 768 e 1280 px, claro e escuro).
