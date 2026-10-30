# ADR-0012 — Deploy no Render: liveness separada, imagem única, backup criptografado e papéis de banco

- Status: **proposto** (aguarda aprovação do dono; o item 6 é decisão aberta) · Data: 2026-10-15
- Complementa o [ADR-0006](0006-hospedagem-render.md) (que continua valendo).

## Contexto
A Etapa H leva o produto ao ar (`docs/plano/lancamento.md`). Surgiram escolhas que o ADR-0006
não cobria ou que ele indicava de outra forma.

## Decisão

1. **Duas rotas de saúde.** `GET /saude` = *liveness* (200 `{"status":"ok"}`, sem banco, sem
   sessão, sem dado interno) é o `healthCheckPath` do Render. `GET /health` (já existente) =
   *prontidão* (`SELECT 1`, 503 se o banco cai) é o que o monitor de uptime consulta. O ADR-0006
   dizia `/health` no health check; trocamos porque, com o banco fora do ar, o health check
   do host reprovaria o web em laço de reinício sem que reiniciar resolvesse nada.
2. **Uma imagem Docker** (`Dockerfile`, multi-stage, usuário sem privilégios, assets construídos
   no build, sem segredo) para web, worker e crons; só o comando muda. Nada de `ENTRYPOINT`, para o
   `preDeployCommand` e os comandos do Render rodarem direto.
3. **`render.yaml` e `render.staging.yaml` gerados** por `scripts/gen_render_yaml.py` (CI confere
   a sincronia). Segredos só `sync: false` no web; worker e crons os leem do web
   (`fromService`/`envVarKey`). Região única **virginia** (a mais próxima do Brasil; ver
   `operacao.md`). Produção sem auto-deploy; staging com auto-deploy do branch `staging`.
4. **Tarefas agendadas fora do worker.** `flask lgpd-retencao`/`lgpd-purge` (diário), o monitor
   (`worker status --check`, 10 min) e o backup são **Cron Jobs** do Render, sem alterar o
   worker (nenhuma regra de negócio muda). Alternativa descartada: novas tarefas no laço do
   worker (menos serviços, mas expurgo irreversível dentro do laço de eventos e mudança de código).
5. **Backup em camadas**: backups gerenciados do Render + dump `pg_dump -Fc` diário criptografado
   com `age` (chave pública no servidor, privada com o dono) em bucket R2 **separado** das
   fotos, retenção 30 dias (`lgpd.md`); espelho do bucket de fotos com `--delete` (o expurgo LGPD
   propaga). Ferramentas padrão (`pg_dump`, `age`, `aws`), sem serviço próprio.
6. **Aberta — papel do banco.** O RLS não vale para superusuário/`BYPASSRLS`, e `pg_dump` de
   papel comum falha com RLS forçado. Se o usuário do `DATABASE_URL` do Render for superusuário ou
   tiver `BYPASSRLS`, é preciso **um papel comum para o app/worker/crons** e o papel dono só para
   migrations e backup — ou seja, uma variável nova (`MIGRATION_DATABASE_URL`) e o `preDeployCommand`
   usando-a. **Não implementado** (muda a configuração de runtime). O `flask config-check --online`
   detecta o problema (`DB_ROLE`) antes do go-live. Verificação em `operacao.md` §4.

## Consequências
- (+) Deploy reprovado cedo e com lista completa do que falta (`flask config-check`); restauração
  provada por script; um só lugar para a lista de variáveis do Render.
- (+) Banco fora do ar não derruba o web em laço.
- (−) Quatro Cron Jobs a mais (custo) e um serviço de log externo para a retenção de 6 meses.
- (−) A imagem de backup depende de pacotes Debian (`age`, `awscli`); o espelho de fotos fica na
  mesma conta Cloudflare (não cobre comprometimento da conta).
- (−) Região nos EUA: transferência internacional de dados (LGPD art. 33) a declarar na política.
