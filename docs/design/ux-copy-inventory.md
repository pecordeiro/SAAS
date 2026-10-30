# Inventário de textos das telas redesenhadas (2026-10-28)

> Substituído pela auditoria completa de 2026-10-29: inventário de todos os textos em
> [`docs/ux-copy-inventory.md`](../ux-copy-inventory.md), glossário em [`docs/teroz-terminologia.md`](../teroz-terminologia.md)
> e voz em [`docs/teroz-voice-and-tone.md`](../teroz-voice-and-tone.md). Este arquivo fica como registro do redesign.

Textos que a pessoa lê nas três tarefas (registrar, acompanhar, configurar), com o arquivo e a decisão. Regra:
nomear pelo que a pessoa reconhece, por extenso, em voz ativa; a mesma ação tem o mesmo nome do botão à mensagem.

## Termos fixos (usar sempre igual)

| Termo | Significa | Onde aparece |
|---|---|---|
| Progresso pelas tarefas | quanto do trabalho previsto foi feito, contando peças parciais (1 − horas que faltam ÷ horas totais) | Painel da operação, painel do projeto, Preencher etapas |
| Unidades prontas | equipamentos com todas as etapas prontas (a etapa/subatividade mais atrasada manda) | idem |
| Peças prontas (total) | o total acumulado de uma subatividade, não o do dia | Preencher etapas |
| Peso no projeto / na etapa | quanto do tempo total a etapa ou subatividade representa | só no modo Configurar |
| Dias úteis | segunda a sexta (ou os dias da empresa) sem feriados; sempre por extenso, nunca "d.u." | painéis, Meta e equipe, lista de projetos, e-mail |
| Dias de trabalho | trabalho que falta ÷ (pessoas × horas por dia) | Meta e equipe |

## Preencher etapas

| Local | Texto | Decisão |
|---|---|---|
| `preencher/fill.html:71-72` | Registrar produção · Configurar etapas | novo: os dois trabalhos com nome de ação |
| `preencher/fill.html:80` | Etapas · progresso pelas tarefas | novo: diz o que a barra da lista mede |
| `preencher/_partes.html:23` | "x de y unid. prontas" | novo; "unid." mantido por espaço na lista estreita |
| `preencher/_partes.html:54` | Unidades prontas da etapa (conta a subatividade mais atrasada) | antes "Unidades prontas ÷ meta (a menor contagem entre as subatividades)" |
| `preencher/_painel.html:89` | Peças prontas (total) | antes "Peças concluídas": deixa claro que é o acumulado |
| `preencher/_painel.html:173` | Digite o **total** de peças prontas de cada subatividade, não só as de hoje. Salva ao sair do campo (Tab ou Enter); Esc desfaz. | encurtado: a explicação das contas saiu (já está nas caixas) |
| `preencher/_painel.html` (dica do modo Configurar) | Aqui ficam o nome, o tempo ideal de cada subatividade… Para lançar peças, volte a "Registrar produção". | novo: aponta a saída |
| `preencher/fill.html:109`, `_painel.html:35,139` | Apagar etapa / Apagar subatividade | mantido; a confirmação diz o que some e como desfazer |
| `preencher/_partes.html:61-63` (`#salvo-status`) | Salvo (campo) · quem, hora | mantido |
| `static/js/preencher.js` | Sem conexão: não salvou. Confira a internet e saia do campo de novo. | novo (F-04) |
| `static/js/preencher.js` | A página expirou: não salvou. Recarregue a página e digite de novo. | novo (F-04) |
| `static/js/preencher.js` | Erro no servidor: não salvou. Tente de novo em instantes. | novo (F-04) |
| servidor (`preencher.py`) | Outra pessoa mudou "…" enquanto você editava: agora … O seu valor ficou no campo: saia dele de novo para salvar por cima. | mantido: já explicava o conflito |

| `preencher/_painel.html` (módulos) | Marcar aguardando peça · Atualizar aguardando peça · Fotos e comentários · Checklist de inspeção · Progresso por pessoa | novo: mesmos nomes da tela antiga, com o selo "Opcional" |
| `preencher/_partes.html` (bolinha) | Atribuir a · Digite um nome ou um e-mail · Sugestões · Tirar o responsável · Ninguém encontrado. | novo: janelinha do responsável; a bolinha tem o nome da pessoa no rótulo para leitor de tela |
| `preencher/_cabecalho.html` (módulo) | Unidades | novo: link do projeto, só com o módulo ligado |

## Painel da operação

| Local | Texto | Decisão |
|---|---|---|
| `app/painel.html:18` | Painel da operação | antes "Operação"; agora igual ao menu ("Painel") e ao link de volta |
| `app/painel.html:33-49` | Progresso pelas tarefas · Unidades prontas · Horas que faltam · Próximo prazo | 4 indicadores, cada um com unidade e uma linha de apoio |
| `app/painel.html:52` | "Lote 2026-014 · folga de 16 dias úteis" | "d.u." por extenso |
| `app/painel.html:61` | Precisa de atenção | novo |
| `app/painel.html:74` | Nada precisa de atenção agora: nenhuma etapa atrasada (ou aguardando peça). | novo: estado normal dito com discrição |
| `app/painel.html:89` | Progresso pelas tarefas · Unidades prontas · Etapas concluídas · Horas que faltam (h) · Prazo | cabeçalhos com unidade |

## Meta e equipe

| Local | Texto | Decisão |
|---|---|---|
| `preencher/goal_team.html:30` | Meta, equipe e prazo | antes "Meta e equipe" no cartão |
| `preencher/goal_team.html:31` | A meta vale para todas as etapas: cada uma precisa chegar a esse número de unidades. | antes "A meta vira as “previstas” de todas as etapas." (jargão da planilha) |
| `preencher/_equipe.html:12` | Com a equipe atual: N pessoas × h por dia | novo: a premissa da previsão à vista |
| `preencher/_equipe.html:13` | Termina em [data] · folga (ou atraso) de N dias úteis | novo |
| `preencher/_equipe.html:26,31` | Dias de trabalho para terminar · Dias de trabalho para a meta inteira | mantidos, separados de "dias úteis até o prazo" |
| `preencher/goal_team.html:65` | Simular o tamanho da equipe · De 1 a 6 pessoas | novo: a simulação abre sob demanda |

## Fora das três telas

| Local | Texto | Decisão |
|---|---|---|
| `app/projects.html:69` | Atraso previsto · N dias úteis | antes "N d.u." |
| `emails/weekly_report.{html,txt}` | atraso de N dias úteis | antes "N d.u." |
| `static/js/painel.js:288` | prazo: N dias úteis (linha do gráfico Equipe × prazo) | antes "prazo: N d" |
| títulos das abas | "… · Controle de Produção" | pendente: trocar por "Teroz" é decisão de marca (F-10) |
