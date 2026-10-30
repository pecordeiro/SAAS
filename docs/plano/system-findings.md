# Achados do sistema (2026-10-28)

Gravidade: **P0** perda de dados, vazamento ou sistema fora do ar · **P1** fluxo central errado, sucesso falso ou
falha de segurança alcançável · **P2** problema real com contorno · **P3** melhoria ou limpeza.
Mapa e método em [`system-audit.md`](system-audit.md).

| ID | Grav. | Área | Achado | Situação |
|---|---|---|---|---|
| F-01 | P1 | Sessão / HTMX | Lançamento marcado como "salvo" sem ter salvo quando a sessão já caiu | **Corrigido e testado** |
| F-02 | P1 | Dependências | Pillow 12.3.0 com 39 vulnerabilidades conhecidas, duas alcançáveis pelo envio de fotos | **Corrigido e testado** |
| F-03 | P2 | Desempenho | Painel da operação fazia ~10 consultas por projeto | **Corrigido e testado** |
| F-04 | P2 | Feedback | Falha ao salvar sem internet ou com a página expirada não dizia nada | **Corrigido e conferido no navegador** |
| F-05 | P2 | Idempotência | Clique duplo em formulário comum criava registro duplicado | **Corrigido e conferido no navegador** |
| F-06 | P2 | Regra de negócio | "Etapa atrasada" supõe etapas em sequência | **Pendente: decisão do dono** |
| F-07 | P3 | Navegação | A mesma tela com três nomes | **Corrigido** |
| F-08 | P3 | Código | Dados e funções de gráficos que nenhuma tela usa | Pendente (limpeza com o teste) |
| F-09 | P3 | Testes | Suíte só em SQLite nesta sessão; RLS não exercitado | Pendente (precisa de PostgreSQL) |
| F-10 | P3 | Texto | Títulos ainda dizem "Controle de Produção", não "Teroz" | Pendente (decisão do dono) |
| F-11 | P3 | Feedback | A mensagem de F-04 cobre as células de Preencher etapas e Meta e equipe; o registro pela folha do detalhe do projeto ainda não | Pendente |
| F-12 | P1 | Produto / módulos | Módulos ligados em Configurações não mudavam nada em Preencher etapas | **Corrigido e testado** |

---

## F-01 · Lançamento "salvo" sem ter salvo quando a sessão já caiu (P1)
- **Local:** `app/static/js/preencher.js` (marca o campo pelo status da resposta) + Flask-Login (302 para `/entrar`).
- **Evidência:** com a senha trocada em outro aparelho (`session_version` incrementado), o POST da célula recebia
  302 → o XHR seguia sozinho até a página de login → 200 → o campo ficava verde ("salvo") e nada era gravado.
  Reproduzido no navegador e no teste.
- **Impacto:** o operador acredita que lançou as peças; o painel fica desatualizado sem ninguém perceber.
- **Correção:** `app/security.py::_htmx_login_redirect` — para pedidos do HTMX, o 302 para o login vira 401 com
  `HX-Redirect` para `/entrar?next=<tela atual>` (validado por `safe_next`, sem redirecionamento aberto). Navegação
  normal continua com 302.
- **Teste:** `tests/test_auditoria_sistema.py` (4 casos) e navegador (vai ao login com "Entre para continuar." e volta
  para a mesma etapa).
- **Desfazer:** remover o `after_request`; nada no banco.

## F-02 · Pillow com vulnerabilidades conhecidas (P1)
- **Local:** `requirements.txt` (`Pillow==12.3.0`), usado em `app/services/photos.py`.
- **Evidência:** `pip-audit -r requirements.txt` → 39 avisos, todos corrigidos na 13.0.0. O envio de fotos só abre
  JPEG, PNG e WebP (tipo pelos bytes), o que tira a maioria do alcance, mas PYSEC-2026-4342 (laço no EXIF de um PNG,
  negação de serviço) passa por `ImageOps.exif_transpose`. O CI roda `pip-audit`, então ele também falharia.
- **Correção:** `Pillow==13.0.0`. `pip-audit` de produção e de desenvolvimento: "No known vulnerabilities found".
- **Teste:** `test_etapa_g_evidencias.py`, `test_etapa_g_storage.py`, `test_adr19_briefing_agenda.py` → 97 passaram,
  2 pulados (os mesmos de antes), e a suíte completa.
- **Desfazer:** voltar o pino para 12.3.0 (não recomendado).

## F-03 · Painel da operação com uma consulta por etapa (P2)
- **Local:** `app/blueprints/app.py::home`, `app/services/projects.py::list_projects`, `app/services/holidays.py`.
- **Evidência:** 18 consultas com 1 projeto, 58 com 5, 108 com 10 (até ~200 no teto de 20 projetos). As
  subatividades eram lidas etapa por etapa e os feriados 3 a 4 vezes por projeto.
- **Correção:** `list_projects(..., with_stages=True)` traz etapas e subatividades em duas consultas; `holidays_for`
  aceita um cache por requisição que só o Painel da operação liga. Nenhuma conta mudou.
- **Resultado:** 16 consultas com 1, 5 ou 10 projetos.
- **Teste:** `test_painel_da_operacao_nao_cresce_uma_consulta_por_projeto` e os testes de números do painel
  (`test_etapa_e.py`).

## F-04 · Falha ao salvar sem explicação (P2)
- **Local:** `app/static/js/preencher.js`.
- **Evidência:** sem internet, com a página expirada (CSRF) ou com erro 5xx, o campo ficava vermelho e a linha de
  status continuava vazia. A pessoa não sabia que não tinha salvo nem o que fazer.
- **Correção:** quando o servidor não mandou a mensagem, a linha de status (`role="alert"`) diz o que houve e o que
  fazer: "Sem conexão: não salvou…", "A página expirou: não salvou. Recarregue a página…", "Erro no servidor…".
  Erros de validação continuam vindo do servidor.
- **Teste:** navegador (sem internet, cookies apagados e volta da conexão salvando normalmente). O projeto não tem
  testes automáticos de JavaScript.

## F-05 · Clique duplo cria registro duplicado (P2)
- **Local:** formulários POST comuns, por exemplo "Incluir etapa" em `preencher/fill.html`.
- **Evidência:** o clique duplo mandava dois POST e criava duas etapas iguais. Os formulários do htmx já descartavam o
  segundo pedido.
- **Correção:** `app/static/js/app.js` ignora um segundo envio do mesmo formulário em menos de 3 s (solta sozinho,
  porque um download não troca de página).
- **Teste:** navegador (8 etapas → clique duplo → 9).

## F-06 · "Etapa atrasada" supõe etapas em sequência (P2, decisão do dono)
- **Local:** `app/services/calc.py::etapas_atrasadas` (usa `fatias_da_esteira`).
- **Evidência:** a linha de base divide o prazo entre as etapas na ordem, proporcional ao tempo. Uma etapa que roda em
  paralelo pode aparecer "atrasada" sem estar. O dono já disse que "nem todo processo é linear".
- **Por que não foi corrigido:** muda uma regra de cálculo (regra 2 do `CLAUDE.md`) e o que aparece em "Precisa de
  atenção".
- **Opções:** (a) atraso só no projeto (previsão depois do prazo) e nas etapas paradas há N dias; (b) cada etapa com
  data prevista própria; (c) todas as etapas dividem o prazo inteiro: atrasada só se o prazo passou e ela não terminou.

## F-07 · A mesma tela com três nomes (P3)
- Menu "Painel", título "Operação" e link de volta "Painel da operação". O título passou a ser "Painel da operação"
  (o menu segue o pedido de ser igual à base).

## F-08 · Código de gráficos sem uso (P3)
- `dashboard.painel_operacao` ainda monta `grafico` (a tela não mostra mais gráficos; coberto por
  `tests/test_etapa_e.py:271`) e `painel.js::drawDeadline` não tem tela. Remover junto com o teste numa limpeza.

## F-09 · Testes só em SQLite nesta sessão (P3)
- 84 testes pulados precisam de PostgreSQL (RLS, concorrência real). Rodar com `TEST_DATABASE_URL` antes do commit
  final ou no CI.

## F-10 · Nome "Controle de Produção" nos títulos (P3)
- Títulos das abas e textos alternativos ainda usam o nome antigo. Trocar é decisão de marca.

## F-11 · Mensagem de falha fora de Preencher etapas (P3)
- O registro pela folha do detalhe do projeto (`register__form`) ainda só marca o formulário. F-01 (sessão) vale para
  ele também, porque a correção é no servidor.

## F-12 · Módulos opcionais sem efeito em "Preencher etapas" (P1)
- **Local:** `app/templates/preencher/_painel.html` (sem controles), `app/blueprints/app.py::stage_waiting_part`,
  `app/blueprints/edicao.py::activity_assign` (voltavam para a tela antiga do projeto).
- **Evidência:** com os 6 módulos ligados em Configurações › Módulos, "Preencher etapas" só mostrava a etiqueta
  "Aguardando peça" de uma etapa já marcada. Marcar aguardando peça, fotos e comentários, checklist, unidades e
  responsável só existiam na tela antiga do projeto (`/app/projetos/<id>`, aberta pelo nome na lista de Projetos). O
  `limpeza-pendente.md` já registrava que o Preencher "não cobre esses módulos"; o redesign tornou isso mais visível
  porque o Preencher virou a tela de uso diário.
- **Impacto:** a pessoa liga o módulo, volta à tela que usa e "nada acontece". Os módulos pareciam quebrados.
- **Correção:** a etapa aberta mostra, só para módulo ligado, "Marcar/Atualizar aguardando peça" (supervisor+, com
  aviso amarelo quando marcada), "Fotos e comentários" (uma entrada por subatividade, com contagem), "Checklist de inspeção", uma bolinha de responsável ao lado de cada subatividade (iniciais; supervisor+ clica e escolhe em "Atribuir a", com busca por nome ou e-mail) e "Unidades" no topo. As ações voltam para a
  mesma etapa (`voltar=preencher`); as telas dos módulos agora voltam para Preencher. As rotas não mudaram de
  regra: módulo desligado continua 404 e o papel continua checado no servidor.
- **Teste:** `tests/test_modulos_preencher.py` (12) e navegador (marcar peça, atribuir pela bolinha, buscar, tirar o
  responsável, abrir fotos, checklist e unidades, e voltar).
- **Pendente (decisão do dono):** "Aguardando peça" **só sinaliza**; nunca trava o lançamento de peças (regra da
  Etapa F, `services/projects.py::set_waiting_part`). Se a intenção é travar, é mudança de regra e precisa de ADR.
