# Teroz — voz e tom

Para quem escreve qualquer texto da Teroz: tela, mensagem, e-mail ou site. O vocabulário está em
[`teroz-terminologia.md`](teroz-terminologia.md); o inventário de textos em [`ux-copy-inventory.md`](ux-copy-inventory.md).

## A voz

A Teroz fala como alguém que conhece a fábrica: direta, calma e precisa. Dá a informação que a pessoa precisa para
agir, sem enfeite.

- **Clara:** uma ideia por frase, palavras do chão de fábrica, nada de jargão de tecnologia.
- **Confiável:** só afirma o que o sistema faz. Estimativa é chamada de previsão; nada vira garantia.
- **Prática:** depois de dizer o que aconteceu, diz o que fazer.
- **Respeitosa:** sem exclamação, sem gíria, sem tratar todo mundo no masculino.

## O tom muda com quem lê

| Quem | O que precisa | Como escrever | Exemplo |
|---|---|---|---|
| Operador (Preencher etapas) | saber o que digitar e se salvou | frases curtas, verbo no começo, confirmação clara | “Digite o total de peças prontas de cada subatividade, não só as de hoje.” |
| Gestor (painéis, Meta e equipe) | situação, prazo, o que precisa de atenção | número com unidade e escopo; sem recomendação que os dados não sustentam | “Termina em 29/10/2026 · folga de 16 dias úteis” |
| Proprietário (Configurações, assinatura) | consequências antes de decidir | diga o efeito e se dá para desfazer | “Desligar esconde o módulo para todos na empresa, mas não apaga nada.” |
| Visitante (site) | entender o problema que resolve e o próximo passo | benefício concreto, sem número ou depoimento inventado | “Acompanhe a produção etapa por etapa: quanto cada uma já avançou, quantas unidades estão prontas…” |

Persuasão só no site público e na escolha de plano. Nas telas de trabalho, o texto ajuda a trabalhar.

## Regras de escrita

1. Português do Brasil, frase curta, voz ativa. “Salve a meta” e não “A meta deve ser salva”.
2. Sentença com maiúscula só no começo (“Meta e equipe”, não “Meta E Equipe”). Nada em CAIXA ALTA na tela.
3. Número sempre com unidade: `h`, `min`, `dias úteis`, `unidades`, `peças`. Nunca abreviação que exija adivinhar (“d.u.”).
4. Datas `dd/mm/aaaa`; horas `14:30`; decimal com vírgula.
5. Sem exclamação, sem emoji, sem superlativo (“incrível”, “revolucionário”).
6. Linguagem neutra: “Você agora faz parte de…”, não “Bem-vindo”.
7. Sem sigla técnica na tela (MFA, API só onde é o nome do recurso para integradores, CSV/XLSX quando a pessoa precisa saber o formato).
8. Não use placeholder como rótulo; o placeholder dá exemplo (“Ex.: Lote 2026-015”).

## Padrões por tipo de texto

**Títulos de página:** o nome da tarefa ou do lugar (“Preencher etapas”, “Meta e equipe”, “Painel da operação”). O
`<title>` é “Página · Projeto · Teroz”.

**Botões:** verbo + objeto quando cabe (“Salvar meta” seria ideal; “Salvar” serve quando o formulário tem um campo só).
O nome do botão é o mesmo na mensagem de sucesso (“Incluir etapa” → “Etapa incluída.”). Destrutivo diz o que destrói
(“Apagar etapa”, nunca “Remover” para algo que vai para a lixeira de etapas).

**Campos:** rótulo diz o que é; a ajuda diz o que não é óbvio (unidade, se é total ou do dia, se é opcional). Valor
calculado aparece como texto, nunca como campo editável.

**Sucesso:** o que foi feito, no passado, e o resultado quando ajuda: “Salvo (peças prontas de “Cortar perfis”) · Ana,
14:30”. Nunca diga “salvo” antes de o servidor confirmar.

**Erro:** o que aconteceu + o que fazer. “Sem conexão: não salvou. Confira a internet e saia do campo de novo.” Não
invente a causa; quando não se sabe, diga o que dá para tentar. Nada de código, caminho de arquivo ou detalhe interno.

**Conflito:** diga o valor de agora e como confirmar o seu (“Outra pessoa mudou… agora 45 min e 3 de 10 peças. O seu
valor ficou no campo: saia dele de novo para salvar por cima.”).

**Estado vazio:** por que está vazio + como começar. Vazio normal não é erro (“Nada precisa de atenção agora”).

**Confirmação de ação destrutiva:** pergunta com o nome do item, o efeito e se dá para desfazer (“Apagar “Montagem” e
todas as suas subatividades? Ela sai da tela e das contas. As peças lançadas ficam no histórico, e dá para desfazer em
“Etapas apagadas””).

**E-mail:** assunto diz o que aconteceu; corpo abre com “Olá, Nome.”, explica em uma frase, um botão, o endereço em texto
e por que a pessoa recebeu. Não peça resposta: a caixa de envio não é lida.

**Site e planos:** comece pelo problema do cliente, mostre como a Teroz resolve, tire a dúvida real (cartão, planilha,
celular, dados) e feche com um próximo passo. Só fatos verificáveis no produto.
