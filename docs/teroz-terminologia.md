# Teroz — terminologia

Vocabulário único para telas, mensagens, e-mails e site. Cada termo segue o que o sistema faz de verdade
(`app/services/calc.py`, modelos em `app/models/`). Se dois conceitos são diferentes no cálculo, têm nomes
diferentes no texto. Revisado em 2026-10-29 (auditoria de copy).

| Termo preferido | O que é no produto | Onde usar | Evitar | Observações |
|---|---|---|---|---|
| **Teroz** | o nome do produto (feminino: “a Teroz”, “na Teroz”) | títulos, rodapé, e-mails, textos legais | “Controle de Produção” como nome | “controle de produção” continua como descrição do que o produto faz. O remetente dos e-mails (`MAIL_FROM` no ambiente) ainda usa o nome antigo: muda na configuração de produção, não no código. |
| **Projeto** | o que se acompanha: um lote, uma encomenda ou um equipamento, com meta, equipe e prazo (`Project`) | toda a área logada | “lote” como nome da entidade | “lote” é a palavra do cliente e aparece no site público (“saiba em que etapa está cada lote”) e em exemplos (“Lote 2026-014”). |
| **Etapa** | um grupo de trabalho do projeto, na ordem de montagem (`Stage`) | sempre | “fase”, “estação” | “Fase” só aparece como exemplo de nome de coluna da planilha do cliente. |
| **Subatividade** | o item dentro de uma etapa, com tempo ideal e peças prontas (`Activity`) | sempre que se fala do item | “atividade”, “tarefa”, “serviço” | É o termo da planilha de referência e o que o dono usa. Endereços (`/atividades/...`) e nomes internos não mudaram. “Atividade” só fica no sentido genérico (ex.: “atividade ilegal” nos Termos). |
| **Peças prontas** | total acumulado de peças feitas numa subatividade (`units_done`), de 0 até a meta | Preencher etapas, importação, histórico | “peças concluídas”, “peças feitas”, “adicionar peças” | É um TOTAL, não o do dia: o campo diz “Peças prontas (total)”. Na tela antiga de detalhe do projeto o registro é por soma (“Quantidade a somar”), e o texto diz isso. |
| **Unidades prontas** | equipamentos com todas as etapas prontas: a menor contagem entre as etapas (`unidades_concluidas`) | painéis, relatório semanal | “unidades concluídas”, “robôs prontos” | Na etapa, a menor contagem entre as subatividades (“conta a subatividade mais atrasada”). |
| **Meta** | quantas unidades o projeto vai montar (`Project.quantity`), igual para todas as etapas | Meta e equipe, painéis, importação | “previstas”, “quantidade de equipamentos” (como rótulo de indicador) | A importação mostra “Meta (previstas)” para reconhecer a coluna da planilha do cliente. O formulário antigo de novo projeto ainda pergunta “Quantidade de equipamentos” (pendente). |
| **Progresso pelas tarefas** | quanto do trabalho previsto foi feito, contando as parciais: 1 − horas que faltam ÷ horas totais | painéis, Preencher etapas, Como funciona | “progresso geral”, “% concluído” (para este indicador) | Nome histórico do indicador (planilha e painel antigos); por isso “tarefas” só aparece aqui. Não confundir com unidades prontas. |
| **Subatividades em 100%** | quantas subatividades já chegaram à meta | painel do projeto, restauração | “tarefas concluídas” | |
| **Peso** | quanto uma subatividade pesa na etapa, ou uma etapa no projeto, pelo tempo ideal | só no modo Configurar e em Como funciona | “importância”, “prioridade” | |
| **Tempo ideal** | minutos para fazer uma unidade daquela subatividade | modo Configurar, modelos, importação | “tempo padrão”, “tempo” sozinho | Sempre com a unidade: “(min por unidade)”. |
| **Horas que faltam** | trabalho restante em horas (soma dos tempos ideais × peças que faltam) | painéis, Meta e equipe | “tempo restante” | Na tabela do modo Configurar fica “Tempo que falta (min)”, porque ali a unidade é minuto. |
| **Horas trabalhadas** | horas-padrão já feitas (pelas peças prontas × tempo ideal) | Painel da operação | “horas gastas”, “apontamento” | São horas-padrão, não horas de relógio. |
| **Dias úteis** | dias de trabalho da empresa, sem fins de semana e feriados | prazos e previsões | “d.u.”, “dias” sozinho quando o cálculo é em dias úteis | Sempre por extenso. |
| **Dias de trabalho** | horas que faltam ÷ (pessoas × horas por dia) | Meta e equipe | “dias úteis” para este número | É trabalho, não calendário: “dias de trabalho para terminar” ≠ “dias úteis até o prazo”. |
| **Prazo** | data de entrega informada pela empresa | sempre | “data limite”, “deadline” | |
| **Término previsto** | data em que o trabalho acaba no ritmo da equipe atual (estimativa) | painéis, e-mails | “data de conclusão” (soa como garantia) | É previsão, nunca garantia. |
| **Folga / atraso** | diferença em dias úteis entre término previsto e prazo | painéis, Meta e equipe, alertas | “adiantado”, “risco” sem regra | “Prazo em risco” só quando a regra de alertas diz isso. |
| **Situação** | estado de uma etapa, projeto, fatura ou unidade | sempre | “status” | Valores da etapa: Concluída, Em andamento, Aguardando peça, Atrasada, Não iniciada. A regra de “Atrasada” supõe etapas em sequência (F-06, decisão pendente). |
| **Aguardando peça** | marca opcional de que a etapa parou por falta de peça | Preencher etapas, painéis | “bloqueada”, “travada” | Só sinaliza; não trava o lançamento. |
| **Registrar produção / lançar** | digitar as peças prontas | Preencher etapas | “apontar”, “alimentar” | “Registro” é o lançamento gravado no histórico. |
| **Configurar etapas** | criar, renomear, ordenar etapas e subatividades, tempos e pesos | Preencher etapas (supervisor+) | “editar estrutura” | |
| **Responsável** | quem cuida de uma subatividade | bolinha ao lado da subatividade, e-mail | “dono”, “atribuído” como substantivo | |
| **Pessoas** | quantas pessoas montam (número do cálculo) | Meta e equipe | “usuários” | “Usuários” são contas com acesso (Configurações › Usuários). |
| **Papel** | Operador, Supervisor, Proprietário | Usuários, convites | “perfil”, “cargo” | |
| **Verificação em duas etapas** | código do celular além da senha | conta, Usuários, preços | “MFA”, “2FA” | A sigla só fica em comentários de código. |
| **Modo leitura** | assinatura vencida ou cancelada: dá para ver e exportar, não para gravar | assinatura, avisos | “bloqueio” | |
| **Prévia** | a conferência antes de gravar uma importação ou restauração | importação, restauração | “pré-visualização” | |
| **Fotos e comentários** | registro de fotos e observações por subatividade (módulo) | botão, título da tela, módulo | “evidências” | |
