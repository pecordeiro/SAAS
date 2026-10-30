# ADR-0011 — Qualidade: armazenamento de fotos, checklist que só sinaliza e unidades como rastreabilidade

- Status: proposto (Etapa G) · Data: 2026-10-15 · Decisões a confirmar com o usuário

## Contexto
A Etapa G traz evidência de montagem/não conformidade (fotos e comentários por atividade),
checklist de inspeção por etapa com assinatura e número de série por unidade. Foto é o primeiro
arquivo binário enviado por cliente que fica GUARDADO (a importação lê em memória e descarta):
precisa de lugar fora do banco, sem pasta pública, com isolamento por empresa e entrando no
expurgo LGPD. O plano não fixava provedor nem regra do checklist.

## Decisão
1. **Armazenamento atrás de uma interface** (`app/services/storage.py`): `local` (disco em
   `instance/uploads`, só development/test — produção recusa no boot), `s3` (Cloudflare R2
   recomendado; AWS S3/MinIO compatíveis) e `none` (padrão em produção sem configuração: fotos
   desligadas, o app sobe). Config só por `STORAGE_*` no ambiente.
2. **S3 sem boto3**: assinatura AWS SigV4 própria (~60 linhas) com `requests`, que já é
   dependência. Motivo: só três operações (PUT/GET/DELETE de um objeto); boto3+botocore somam
   ~15 MB, muitas dependências transitivas e superfície para `pip-audit`. A assinatura é
   conferida com o vetor de teste publicado pela AWS. Se um dia precisar de multipart upload,
   URL pré-assinada ou listagem, reavaliar boto3.
3. **Nunca URL pública nem pré-assinada**: o bucket é privado e a foto só sai por
   `/app/fotos/<uuid>` (login, empresa da sessão, 404 cruzado), com `Content-Type: image/jpeg`
   fixo, `nosniff`, `Cache-Control: private, max-age=300`, `Content-Disposition: inline` e CSP
   própria `default-src 'none'; sandbox`. A CSP das páginas não muda (`img-src 'self'`).
4. **Validação pelo conteúdo e reencode**: magic bytes (só JPEG/PNG/WebP), dimensões do
   cabeçalho ≤ 40 MP antes de decodificar, decodificação completa com Pillow, e a imagem
   guardada é um JPEG NOVO (sem EXIF/GPS/ICC/bytes extras, lado ≤ 2560 px) + miniatura.
   Pillow entra no `requirements.txt`. Nome do objeto gerado: `<company_id>/fotos/<uuid>.jpg`.
5. **LGPD**: o expurgo apaga os objetos ANTES das linhas (falha do armazenamento desfaz o expurgo
   e ele roda de novo); a exportação lista os metadados (`activity_photos.csv`) mas não inclui os
   arquivos (ZIP em memória; fotos podem passar de centenas de MB).
6. **Checklist só sinaliza**: “exige checklist assinado” mostra “Checklist pendente/assinado”
   no detalhe e na tela da etapa, igual a “aguardando peça” — não bloqueia registro de peças nem
   conclusão. Bloquear exigiria nova decisão (revisar este ADR).
7. **Papéis do checklist**: supervisor+ define itens (no modelo ou na etapa do projeto) e liga a
   exigência; operador+ abre, preenche e ASSINA (quem inspeciona é quem está na linha);
   supervisor+ registra CORREÇÃO depois de assinada (nova linha com motivo; a antiga fica).
   Assinatura = usuário autenticado + data/hora do servidor; “não conforme” exige observação.
8. **Comentários e fotos**: operador+ envia; supervisor+ apaga (linha removida + auditoria sem
   o texto/imagem). Não há edição. Limites no backend: 1000 caracteres, 5 MB, 20 fotos por
   atividade e 5000 por empresa (configuráveis; não ligados ao plano por enquanto).
9. **Unidades são rastreabilidade**: `units` com série única por empresa+projeto, criadas por
   supervisor+ (faixa ou lista), no máximo `quantity` do projeto. O progresso continua vindo de
   `activities.units_done` (`calc.py` intocado). Registrar “nesta unidade” soma +1 pela regra
   normal (`register_progress`) e grava `progress_entries.unit_id`; uma vez por
   atividade+unidade (desfazer libera).

## Consequências
- (+) Nenhum arquivo de cliente em pasta pública; isolamento testado A/B; expurgo cobre fotos.
- (+) Sem dependência pesada nova além do Pillow.
- (−) Toda foto passa pelo processo web (memória até ~5 MB por upload e por leitura); com volume
  alto, servir por URL pré-assinada curta exigiria rever o item 3.
- (−) Objetos órfãos são possíveis se a remoção falhar depois do commit (log
  `photos.orphan_object`); não há varredura do bucket ainda.
- (−) Downgrade da migration de fotos apaga os metadados mas não os objetos.

## Alternativas
boto3 (rejeitado acima); guardar a foto no PostgreSQL (`bytea`) — rejeitado: banco e backups
crescem rápido e o plano do Render cobra por GB; servir do bucket com URL pública/pré-assinada —
rejeitado por ora (vazamento por link compartilhado, CSP/`img-src` externo).
