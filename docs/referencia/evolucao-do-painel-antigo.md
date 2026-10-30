# Como o painel antigo evoluiu (referência de algo validado)

Estudo feito em 2026-10-21 a partir das quatro versões da planilha de acompanhamento e dos dois estados
do código do painel (servidor e tela). Não contém dados de clientes nem nomes reais de etapas.
O painel antigo é **referência de comportamento validado em uso**, não código a copiar.

## Linha do tempo

| Versão | O que mudou | Lição |
|---|---|---|
| v1 | Uma aba. "Feitas" e "Previstas" por atividade; o peso ("quanto representa") era digitado à mão. | Peso manual é frágil e não fecha em 100%. |
| v2 | Abas **Equipe** e **Como funciona**; peso calculado pelo **tempo ideal**; quadro de separação de materiais. | A explicação das contas mora junto dos números. |
| v3 | Coluna principal virou **% concluído** digitado; etapas numeradas. | % digitado engana: 90% em tudo parece pronto. |
| v4 | **Peças concluídas** no lugar do %. Duas visões: Tabela 1 (tarefas, conta parciais) e Tabela 2 (unidades, só o que passou por todas as etapas). | O dado digitado é o fato; o resto é cálculo. |
| multi-projeto | Vários projetos no mesmo arquivo (3 abas cada); botões de projeto, criar, renomear, apagar; nova etapa, apagar etapa, arrastar. | A necessidade real foi reaproveitar o modelo para outros produtos. |

## O que ficou validado

1. Só se digita o fato (peças, tempo ideal, meta); todo o resto é cálculo.
2. Duas visões do progresso respondem perguntas diferentes (trabalho feito × unidades prontas).
3. "Como funciona" mostra cada conta com os números atuais.
4. "E se mudar a equipe?" (1 a 6 pessoas) é uma das telas mais úteis.
5. Fluxo curto: subatividades e tempos → meta → peças.
6. A estrutura é achada pelos títulos, não por linhas fixas.
7. Células amarelas = entrada; só elas são gravadas, e o servidor valida (sem negativos, peças ≤ previstas).

## Como o SaaS trata cada ponto

- Cálculos idênticos, com teste de paridade (`tests/test_calc.py`, `calc.py`).
- Painel com as duas tabelas, esteira de etapas e equipe × prazo (R2).
- Preencher etapas com células amarelas e salvar ao sair do campo (R3).
- Modo simples (só %) existe como opcional e avisa que não separa "tarefas" de "unidades" (R4).
- Vários projetos, importação de planilha com mapeamento de colunas e exportação no formato da equipe (R7).
- Fora de escopo por ora: separação de materiais e estoque (v2 do produto).
