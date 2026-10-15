#!/usr/bin/env bash
# Espelho diário do bucket de FOTOS para o bucket de backup (prefixo fotos/atual/).
#
# Premissas (docs/plano/operacao.md, seção Backup de fotos):
#   - os dois buckets estão na MESMA conta R2/S3 e a chave de backup lê o bucket de fotos e
#     escreve no bucket de backup (use um token só de backup, nunca a chave do app);
#   - é um ESPELHO com --delete: foto apagada no app (inclusive expurgo LGPD) some do backup na
#     próxima execução. Isso é intencional (lgpd.md: backups rotacionam em 30 dias). Trava de
#     segurança: se o bucket de origem aparecer VAZIO e o backup não, nada é apagado (exit 6).
#
# Variáveis: BACKUP_S3_ENDPOINT, BACKUP_S3_ACCESS_KEY_ID, BACKUP_S3_SECRET_ACCESS_KEY,
#            BACKUP_S3_BUCKET (destino), PHOTOS_SRC_BUCKET (origem), BACKUP_PHOTOS_PREFIX (padrão fotos/atual/)
#            BACKUP_DRY_RUN=1 (só mostra o que faria)
# Saída: 0 ok · 2 configuração · 5 falha do aws · 6 trava (origem vazia)
set -Eeuo pipefail
set +x

log() { printf '%s backup-fotos: %s\n' "$(date -u +%FT%TZ)" "$*" >&2; }
die() { local code="$1"; shift; log "ERRO: $*"; exit "$code"; }

for v in BACKUP_S3_ENDPOINT BACKUP_S3_ACCESS_KEY_ID BACKUP_S3_SECRET_ACCESS_KEY BACKUP_S3_BUCKET PHOTOS_SRC_BUCKET; do
  [[ -n "${!v:-}" ]] || die 2 "$v ausente"
done
[[ "$BACKUP_S3_ENDPOINT" == https://* ]] || die 2 "BACKUP_S3_ENDPOINT precisa ser https://"
[[ "$PHOTOS_SRC_BUCKET" != "$BACKUP_S3_BUCKET" ]] || die 2 "origem e destino são o mesmo bucket"
command -v aws >/dev/null || die 2 "ferramenta ausente: aws"

DEST_PREFIX="${BACKUP_PHOTOS_PREFIX:-fotos/atual/}"
[[ "$DEST_PREFIX" == */ ]] || DEST_PREFIX="${DEST_PREFIX}/"
export AWS_ACCESS_KEY_ID="$BACKUP_S3_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="$BACKUP_S3_SECRET_ACCESS_KEY"
export AWS_DEFAULT_REGION="${BACKUP_S3_REGION:-auto}"
export AWS_EC2_METADATA_DISABLED=true
AWS=(aws --endpoint-url "$BACKUP_S3_ENDPOINT")

count_objects() { # bucket prefix -> número de objetos
  local out
  out="$("${AWS[@]}" s3 ls "s3://$1/$2" --recursive --summarize 2>/dev/null | awk '/Total Objects:/ {print $3}')" || true
  echo "${out:-0}"
}

START=$SECONDS
SRC_COUNT="$(count_objects "$PHOTOS_SRC_BUCKET" "")"
DST_COUNT="$(count_objects "$BACKUP_S3_BUCKET" "$DEST_PREFIX")"
log "origem: ${SRC_COUNT} objeto(s); backup antes: ${DST_COUNT} objeto(s)"
if [[ "$SRC_COUNT" == "0" && "$DST_COUNT" != "0" ]]; then
  die 6 "origem vazia mas o backup tem ${DST_COUNT} objeto(s): não vou espelhar a ausência (credencial errada? bucket trocado?)"
fi

FLAGS=(--delete --only-show-errors)
[[ "${BACKUP_DRY_RUN:-0}" != "1" ]] || FLAGS+=(--dryrun)
"${AWS[@]}" s3 sync "s3://$PHOTOS_SRC_BUCKET/" "s3://$BACKUP_S3_BUCKET/$DEST_PREFIX" "${FLAGS[@]}" || die 5 "aws s3 sync falhou"
log "espelho concluído em $((SECONDS - START))s (dry-run=${BACKUP_DRY_RUN:-0})"
