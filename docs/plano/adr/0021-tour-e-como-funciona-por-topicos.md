# ADR-0021 — Tour de primeiro acesso e Como funciona por tópicos

- Status: **proposto**, aguardando a aprovação do dono para o commit (prévia mostrada antes). Pedido do dono em
  2026-10-30: "na primeira vez que entrasse no site pelo login, entrasse com um tutorial não obrigatório mostrando o
  funcionamento de cada parte, e a aba Como funciona fosse um tutorial por tópicos que posso escolher qual tô em
  dúvida, que mostrasse as contas e o funcionamento". Escolhas do dono: tour nas próprias telas, para todos os papéis
  com passos ajustados ao papel, e tópicos com a conta passo a passo.

## Decisão
1. **Tour pelas telas** (`components/tour.html`, `static/js/tour.js`): abre sozinho no Painel enquanto
   `users.tour_seen_at` for nulo; destaca o item do menu de cada passo (`data-tour`) e mostra um balão com Voltar,
   Próximo e Pular. No celular, o item que está no menu Mais aponta para o botão Mais e o texto diz isso.
   Esc fecha; o foco fica no balão enquanto ele está aberto e volta para a página ao fechar.
2. **Não é obrigatório:** Pular fecha na hora; sem JavaScript o tour não aparece e nada fica bloqueado.
3. **Passos decididos no servidor** (`services/tour.py`, ADR-0009): Operador, Supervisor e Proprietário veem
   passos diferentes (Configurações só para quem tem acesso; o texto de Meta e equipe muda para quem só consulta).
4. **Visto uma vez, em qualquer aparelho:** a coluna da conta é marcada quando o tour começa
   (`POST /app/tutorial/visto`, com CSRF, liberada também em modo leitura porque é preferência da pessoa e não dado
   da empresa). "Rever o tour pelas telas" (em Como funciona) abre de novo por `?tutorial=1`, sem mexer na coluna.
5. **Quem já usava o sistema** (tinha `last_login_at`) fica como "já viu" na migration: o tour é para o primeiro
   acesso. Quem quiser ver usa o link em Como funciona.
6. **Como funciona por tópicos** (`calc.topicos_como_funciona`, puro): oito dúvidas (nove no modo simples), cada uma
   com a resposta em linguagem simples, a regra e a conta montada passo a passo com os números de agora do projeto,
   a conclusão e onde o número aparece. A previsão de término e a situação das etapas usam as mesmas funções do
   Painel (`svc.forecast_end`, `calc.etapas_atrasadas`, `calc.status_visual`). Cada dúvida é um link
   (`?topico=…#resposta`): funciona sem JavaScript e dá para mandar o endereço. A tabela antiga com todas as contas
   continua, recolhida, no fim da página.

## Consequências
- Migration `d7b2f4a9c1e3` (`users.tour_seen_at`, nulo). Downgrade apaga a coluna.
- `tests/test_tour.py`: abre no primeiro acesso, marca visto só a própria conta, exige login e CSRF, passos por papel,
  só no Painel, rever, contas dos tópicos (progresso, unidades, peso, dias, folga e atraso) e escolha do tópico.
- Nenhuma regra de cálculo mudou: os tópicos só explicam as contas que já existem.
- O tour depende dos itens do menu ter `data-tour`; um item novo no menu precisa do atributo para entrar no tour.
