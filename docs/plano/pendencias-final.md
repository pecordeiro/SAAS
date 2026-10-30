# Pendências finais (branch `claude/pendencias-final`)

1. **Rolagem horizontal de 29 px no cabeçalho público em 768 px.** Causa: a navegação completa (4 links + botão) é
   exibida a partir de 48em, mas com o respiro de desktop (`--space-4` de padding por link) não cabia ao lado da marca
   entre 768 e 1023 px. Correção em `publico.css` (faixa 48em–63.99em: padding dos links `--space-2` e margem do botão
   `--space-1`, só tokens). 375 e 1280 px seguem sem rolagem. Pendência da ADR-0018 fechada.
2. **"Sem link para unidade" no `capturar_telas.py`.** Era só o seed do script (sem unidades): a lista
   `/app/projetos/<id>/unidades` já linka cada série para `qualidade.unit_detail` (módulo `unidades`, R6 intacto). O seed
   agora gera 5 números de série; nenhuma mudança de UI.
3. **Rótulo do plano Implantação:** "Sob consulta" virou "Sob orçamento" (com "online ou presencial") nos cards
   públicos, tabela de preços, `/app/assinatura*` e na mensagem de recusa do autosserviço. Preço `NULL` continua
   significando "sem checkout". Testes ajustados sem afrouxar.
4. **/interno/horarios:** ajuda nos campos ("Use o seletor; o formato depende do navegador"), lista sempre em
   `dd/mm/aaaa HH:MM` (America/Sao_Paulo) e mensagem de confirmação "Horário criado: dd/mm/aaaa HH:MM (Brasília)".
   A validação do servidor não mudou. Os campos continuam `date` e `time` nativos (o formato do seletor é do navegador).
5. **Configuração de produção:** `VISUAL_RATE_LIMIT_IP`, `VISUAL_RATE_LIMIT_COMPANY`, `INTERNO_RATE_LIMIT`,
   `BRIEFING_PHOTOS_MAX` e `CALL_MIN_LEAD_MINUTES` entram nos Blueprints com os padrões do `Config` (regenerados por
   `scripts/gen_render_yaml.py`); `STAFF_NOTIFY_EMAIL` segue `sync: false` (só no web). `.env.example` já documentava
   todas. `flask config-check` trata `STAFF_NOTIFY_EMAIL` ausente como AVISO (erro só com `--strict`) e nunca imprime o
   valor. Testes em `tests/test_etapa_h_render.py` e `tests/test_etapa_h_config.py`.
6. **Formulário público de contato:** não existe. `/contato` (`public.contact`) é só um GET com o e-mail de atendimento
   (`CONTACT_EMAIL`), sem POST. Nada foi criado; limite por IP, honeypot e CSRF só fazem sentido se um formulário
   for decidido (exigiria ADR).
