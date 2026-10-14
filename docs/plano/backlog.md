# Backlog do MVP

Prioridade MoSCoW: **M** (must, obrigatório no MVP), **S** (should), **C** (could).
Identificador `F<fase>-<n>`. Critérios no formato Dado / Quando / Então.

## Fase 0 — Esqueleto

**F0-1 (M) Cadastrar empresa**
Como proprietário, quero cadastrar minha empresa para começar a usar.
- Dado que não tenho conta, quando envio nome da empresa, meu nome, e-mail e senha válidos,
  então a empresa e meu usuário `owner` são criados e entro em `/app`.
- Dado um e-mail já cadastrado, quando tento cadastrar, então vejo erro sem revelar dados da
  outra conta.

**F0-2 (M) Entrar e sair**
- Dado credenciais válidas, quando entro, então vou para `/app/projetos` da minha empresa.
- Dado senha errada, quando tento entrar, então vejo mensagem genérica e a tentativa conta no
  rate limit.

**F0-3 (M) Criar projeto simples**
- Dado que sou supervisor, quando crio “Lote 10 equipamentos” com quantidade 10, etapas e
  atividades com horas por unidade, então o projeto aparece na lista com progresso 0%.
- Dado que sou operador, quando faço POST em criar projeto, então recebo 403.

**F0-4 (M) Registrar unidades**
- Dado uma atividade com 3/10 unidades, quando registro +2, então ela fica 5/10, um
  `progress_entry` é gravado e o progresso do projeto é recalculado por `calc.py`.
- Dado +20 numa atividade com 5/10, quando envio, então recebo erro “máximo 5”.

**F0-5 (M) Ver indicadores e prazo**
- Dado um projeto com 10 unidades, 1 pessoa e 8 h/dia, quando abro o detalhe, então vejo
  unidades concluídas (menor nº de peças entre as subatividades), progresso pelas tarefas,
  horas que faltam e dias úteis restantes = horas ÷ (pessoas × horas/dia), iguais aos da planilha.
- Dado feriados cadastrados, quando peço a data prevista de término, então os dias não úteis
  são pulados (melhoria sobre a planilha, que só divide).

**F0-5b (M) Paridade com a planilha**
- Dado o arquivo `docs/referencia/acompanhamento_montagem_v4.xlsx`, quando carrego as etapas
  e peças dele no serviço de cálculo, então progresso, unidades, tempos e status de cada etapa
  coincidem com os valores calculados no Excel (tolerância de 1e-9).

**F0-6 (M) Isolamento**
- Dado que estou na empresa A, quando acesso qualquer URL de recurso da empresa B, então
  recebo 404.

## Fase 1 — Identidade visual (Claude Design)

**F1-1 (M)** Dado 3 direções de marca, quando escolho uma, então o design system e as telas
seguem só ela.
**F1-2 (M)** Dado o design system, quando confiro os tokens, então todos os pares têm contraste
AA nos dois temas.

## Fase 2 — Base visual

**F2-1 (M) Tema claro e escuro**
- Dado sistema em modo escuro, quando abro o site, então ele aparece escuro; quando troco o
  tema no menu, então a escolha persiste (atributo `data-theme`).

**F2-2 (M) Navegação responsiva**
- Dado tela de 375 px, quando entro em `/app`, então vejo navegação inferior; em 1280 px,
  menu lateral; ambos com nome da empresa e meu papel.

**F2-3 (S) Página /estilo**
- Dado ambiente development, quando abro `/estilo`, então vejo todos os componentes e tokens;
  em produção, 404.

## Fase 3 — Banco

**F3-1 (M)** Dado banco vazio, quando rodo `flask db upgrade`, então todas as tabelas, índices,
constraints e planos seed existem.
**F3-2 (M)** Dado `RLS_ENABLED=1` e nenhuma empresa na sessão, quando consulto `projects` cru,
então recebo 0 linhas.
**F3-3 (S)** Dado `flask seed-demo`, quando entro com o usuário demo, então vejo 2 projetos com
3 a 6 etapas e histórico realista.

## Fase 4 — Backend

**F4-1 (M) Modelos de etapas versionados**
- Dado um modelo v1, quando edito uma atividade, então nasce a v2 e projetos criados da v1 não
  mudam.
- Dado um projeto da v1, quando abro “comparar com modelo atual”, então vejo as diferenças e
  só aplico com confirmação, que fica no histórico.

**F4-2 (M) Criar projeto a partir de modelo**
- Dado um modelo, quando crio projeto com quantidade 10, então etapas e atividades são copiadas
  (snapshot) com `template_version_id`.

**F4-3 (M) Edição sem perder histórico**
- Dado uma atividade com registros, quando a arquivo, então ela some da tela mas o histórico e
  a exportação a mantêm.
- Dado etapas A, B, C, quando reordeno para C, A, B, então a ordem persiste.

**F4-4 (S) Duplicar projeto**
- Dado um projeto, quando duplico, então nasce um projeto com as mesmas etapas e progresso zero.

**F4-5 (M) Importar CSV (e a planilha de referência)**
- Dado o modelo de CSV baixado do site, quando envio um arquivo válido, então vejo
  pré-visualização e, ao confirmar, tudo é gravado de uma vez.
- Dado um arquivo com erro na linha 7, coluna “tempo ideal (min)”, quando envio, então vejo
  “linha 7, tempo ideal, número inválido” e nada é gravado.
- Dado a planilha `acompanhamento_montagem_v4.xlsx`, quando a envio na importação inicial,
  então etapas, subatividades, tempos ideais e peças concluídas são lidos pelos títulos da
  coluna A (não por linhas fixas) e mostrados na pré-visualização antes de gravar.

**F4-6 (M) Exportar CSV e XLSX**
- Dado um projeto, quando exporto CSV ou XLSX, então recebo as mesmas colunas da tela, com
  células perigosas neutralizadas.

**F4-7 (M) Limites de plano**
- Dado plano Essencial com 3 projetos ativos, quando crio o 4º (tela ou POST direto), então
  recebo 402 com mensagem amigável e link para trocar de plano.
- Dado empresa sem assinatura ativa, quando tento qualquer escrita, então recebo 402 e vejo o
  aviso de modo leitura; a leitura continua liberada.

**F4-8 (M) Eventos e auditoria**
- Dado que registro progresso, então um `activity.progress_updated` é gravado na mesma transação.
- Dado que mudo um papel, então um `audit_log` com ator, IP e objeto é gravado.

## Fase 5 — Contas

**F5-1 (M) Confirmar e-mail** — Dado cadastro novo, quando clico no link em até 24 h, então o
e-mail fica confirmado; link reutilizado ou expirado mostra erro. Sem confirmação, após 7 dias
o acesso pede confirmação.
**F5-2 (M) Esqueci a senha** — Dado qualquer e-mail, quando peço reset, então vejo sempre a
mesma mensagem; o link vale 1 h, uma vez, e ao trocar a senha todas as outras sessões caem.
**F5-3 (M) Convites** — Dado que sou owner/supervisor, quando convido `ana@x.com` como
operadora, então ela recebe e-mail; ao aceitar, conta é criada ou vinculada; convite expira
em 7 dias, pode ser reenviado ou revogado e conta no limite de usuários.
**F5-4 (M) Gerir membros** — Dado que sou owner, quando desativo um membro, então ele perde
acesso na próxima requisição; não consigo rebaixar ou remover o último owner.
**F5-5 (S) Perfil** — trocar nome; trocar e-mail com reconfirmação; trocar senha pedindo a atual.
**F5-6 (S) Sair de todos os dispositivos** — incrementa `session_version`.
**F5-7 (M) MFA TOTP** — Dado MFA ativado, quando entro, então preciso do código ou de um
código de recuperação (uso único); empresa pode exigir MFA para owners.
**F5-8 (M) Bloqueio progressivo** — Dado 5 senhas erradas, então a conta espera 1 min, depois
5, 15…; o mesmo por IP.
**F5-9 (S) Trocar de empresa** — Dado vínculo com 2 empresas, quando troco, então só vejo
dados da escolhida.

## Fase 6 — Front-end

**F6-1 (M) Site público** — início, preços (de `plans`), termos, privacidade, contato, com
title, description, Open Graph, `sitemap.xml`, `robots.txt` e URLs em português
(`/precos`, `/termos`, `/privacidade`).
**F6-2 (M) Registro rápido** — Dado celular de 375 px, quando toco “+1” ou digito a quantidade
e confirmo, então em ≤ 2 toques a atividade, a etapa e os indicadores se atualizam sem recarregar.
**F6-3 (M) Conflito** — Dado que outro usuário registrou antes, quando envio, então vejo o valor
atual (409) e confirmo ou cancelo.
**F6-4 (S) Atualização automática** — Dado o detalhe aberto e a aba visível, então os
números se atualizam a cada 30 s; aba oculta não faz requisições.
**F6-5 (M) Lista de projetos com filtros** (status, prazo, busca por nome).
**F6-6 (M) Histórico paginado** com filtro por atividade e usuário.
**F6-7 (S) Gráficos** de progresso por etapa e horas restantes em SVG do servidor.
**F6-8 (M) Acessibilidade** — navegação por teclado, foco visível, erros ligados aos campos
(`aria-describedby`), toasts com `aria-live`.

## Fase 7 — Segurança e LGPD

**F7-1 (M)** Cabeçalhos e CSP com nonce em toda resposta.
**F7-2 (M)** Rate limit com Redis em login, cadastro, convites, reset, importação e webhooks.
**F7-3 (M)** Upload: > 2 MB ou tipo diferente de CSV recusado; nada gravado em disco público.
**F7-4 (M) Exportar dados da empresa** — Dado que sou owner, quando peço, então baixo um ZIP
com CSVs de todos os dados da empresa.
**F7-5 (M) Excluir empresa** — Dado que sou owner, quando peço exclusão, então a empresa entra
em carência de 30 dias (posso cancelar) e depois é apagada definitivamente.
**F7-6 (S) Acesso de suporte** — só com motivo, tempo limitado, aviso ao owner e audit_log.
**F7-7 (M)** Logs JSON com `request_id`, sem segredos; erros 500 no Sentry com scrub.

## Fase 8 — Pagamento

**F8-1 (M) Teste grátis** — Dado cadastro novo, então começo em `trialing` por 14 dias sem cartão.
**F8-2 (M) Assinar** — Dado o fim do teste, quando escolho plano e informo CPF/CNPJ válido,
então sou levado ao pagamento do Asaas (Pix, boleto ou cartão).
**F8-3 (M) Webhook** — Dado `PAYMENT_CONFIRMED` com token válido, então a assinatura fica
`active` e o período é estendido; repetido → 200 sem efeito; token inválido → 401.
**F8-4 (M) Atraso e carência** — Dado pagamento vencido, então status `past_due`, carência de
7 dias com aviso por e-mail e faixa no topo; depois modo leitura sem perda de dados.
**F8-5 (M) Trocar plano** — com projeção de valor; upgrade (ou mesmo preço) vale após o
pagamento, downgrade no fim do período. Etapa B: 4 planos (Essencial, Profissional, Empresa,
Implantação); teste grátis só nos 2 primeiros; Empresa com cobrança imediata; Implantação sob
consulta, fora do autosserviço (só `flask billing-admin set-plan`).
**F8-6 (M) Cancelar** — vale até o fim do período pago.
**F8-7 (S) Faturas** — lista com status e link de pagamento.
**F8-8 (S) Admin da plataforma** — estender teste ou dar desconto com motivo auditado.
**F8-9 (M) Reconciliação** — `flask billing-reconcile` corrige divergências com o Asaas.

## Fase 9 — API (reservada)

**F9-1 (C)** Contrato OpenAPI 3.1 de `/api/v1`.
**F9-2 (C)** Tokens por empresa com escopos, mostrados uma vez, revogáveis — atrás da flag.
**F9-3 (C)** `GET /projects` e `GET /projects/{id}/summary`; demais rotas 501.

## Fase 10 — Lançamento

**F10-1 (M)** Staging e produção no Render via `render.yaml`, migration no pre-deploy.
**F10-2 (M)** Domínio com HTTPS, redirecionamento www, e-mail com SPF/DKIM/DMARC.
**F10-3 (M)** Backup diário extra e restore testado.
**F10-4 (M)** Alertas: erro, uptime de `/health`, webhook falhando, outbox parada.
**F10-5 (M)** Cobrança real de valor baixo paga e estornada.
**F10-6 (S)** Página de status, e-mail de suporte, painel interno com métricas do PRD.
