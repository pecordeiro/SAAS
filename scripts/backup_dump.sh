#!/usr/bin/env bash
# Backup lógico diário do PostgreSQL: pg_dump -> criptografa com age -> envia ao bucket S3/R2
# (SEPARADO do bucket das fotos) -> apaga o que passou da retenção.
#
# Roda como Cron Job do Render (docker/backup/Dockerfile) ou à mão:
#   DATABASE_URL=... BACKUP_S3_ENDPOINT=... BACKUP_S3_BUCKET=... BACKUP_S3_ACCESS_KEY_ID=... \
#   BACKUP_S3_SECRET_ACCESS_KEY=... BACKUP_AGE_RECIPIENT=age1... scripts/backup_dump.sh
#
# Variáveis
#   DATABASE_URL                 banco a copiar (aceita postgres://, postgresql:// e postgresql+psycopg://)
#   BACKUP_S3_ENDPOINT/BUCKET/ACCESS_KEY_ID/SECRET_ACCESS_KEY   destino (Cloudflare R2, AWS, MinIO)
#   BACKUP_AGE_RECIPIENT         chave PÚBLICA age (age1...). A privada fica com o dono, offline.
#   BACKUP_PREFIX                pasta no bucket (padrão: db/)
#   BACKUP_RETENTION_DAYS        retenção (padrão 30 — docs/plano/lgpd.md)
#   BACKUP_MIN_KEEP              nunca apaga se restariam menos que isto (padrão 3)
#   BACKUP_DRY_RUN=1             gera e confere o dump, criptografa, mas NÃO envia nem apaga
#   BACKUP_OUT_DIR               onde deixar o .dump.age no modo dry-run (padrão: o diretório atual)
#
# Códigos de saída: 0 ok · 2 configuração · 3 o papel do banco não enxerga todas as linhas (RLS)
# · 4 dump inválido · 5 falha no envio/limpeza.
# Nunca imprime URL, senha, chave ou conteúdo do banco.
set -Eeuo pipefail
set +x

log() { printf '%s backup: %s\n' "$(date -u +%FT%TZ)" "$*" >&2; }
die() { local code="$1"; shift; log "ERRO: $*"; exit "$code"; }

[[ -n "${DATABASE_URL:-}" ]] || die 2 "DATABASE_URL ausente"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
MIN_KEEP="${BACKUP_MIN_KEEP:-3}"
PREFIX="${BACKUP_PREFIX:-db/}"
DRY_RUN="${BACKUP_DRY_RUN:-0}"
[[ "$RETENTION_DAYS" =~ ^[0-9]+$ ]] || die 2 "BACKUP_RETENTION_DAYS precisa ser inteiro"
[[ "$PREFIX" == */ ]] || PREFIX="${PREFIX}/"
[[ -n "${BACKUP_AGE_RECIPIENT:-}" ]] || die 2 "BACKUP_AGE_RECIPIENT ausente (chave pública age1...)"
[[ "$BACKUP_AGE_RECIPIENT" == age1* ]] || die 2 "BACKUP_AGE_RECIPIENT deve começar com age1 (chave PÚBLICA)"
if [[ "$DRY_RUN" != "1" ]]; then
  for v in BACKUP_S3_ENDPOINT BACKUP_S3_BUCKET BACKUP_S3_ACCESS_KEY_ID BACKUP_S3_SECRET_ACCESS_KEY; do
    [[ -n "${!v:-}" ]] || die 2 "$v ausente"
  done
  [[ "$BACKUP_S3_ENDPOINT" == https://* ]] || die 2 "BACKUP_S3_ENDPOINT precisa ser https://"
fi
for tool in pg_dump pg_restore psql age sha256sum; do
  command -v "$tool" >/dev/null || die 2 "ferramenta ausente: $tool"
done
[[ "$DRY_RUN" == "1" ]] || command -v aws >/dev/null || die 2 "ferramenta ausente: aws"

# libpq não entende o prefixo do SQLAlchemy.
PGURL="${DATABASE_URL/postgresql+psycopg:\/\//postgresql://}"
PGURL="${PGURL/postgres:\/\//postgresql://}"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
umask 077

# 1) O papel precisa enxergar TODAS as linhas. Com RLS forçado, pg_dump de um papel comum
#    falha (ou, pior, com --enable-row-security, gravaria um dump VAZIO): recusamos antes.
can_see_all="$(psql "$PGURL" -Atq -c "SELECT (rolsuper OR rolbypassrls) FROM pg_roles WHERE rolname = current_user")" \
  || die 2 "não consegui conectar ao banco"
forced="$(psql "$PGURL" -Atq -c "SELECT count(*) FROM pg_class WHERE relkind = 'r' AND relforcerowsecurity AND relnamespace = 'public'::regnamespace")"
if [[ "$can_see_all" != "t" && "$forced" != "0" ]]; then
  die 3 "o papel do DATABASE_URL não é superusuário nem tem BYPASSRLS e há $forced tabela(s) com RLS forçado: o dump sairia incompleto. Use um papel de backup (ver docs/plano/operacao.md, seção Backup)."
fi

# 2) Dump (formato custom, comprimido; sem dono/ACL para restaurar em qualquer servidor).
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
NAME="controle-${STAMP}.dump"
START=$SECONDS
pg_dump "$PGURL" --format=custom --no-owner --no-privileges --file "$WORK/$NAME" \
  || die 4 "pg_dump falhou"
DUMP_BYTES="$(stat -c %s "$WORK/$NAME")"
TABLES="$(pg_restore --list "$WORK/$NAME" | grep -c ' TABLE DATA ' || true)"
[[ "$TABLES" -gt 0 ]] || die 4 "dump sem nenhuma tabela de dados"
log "dump ok: ${DUMP_BYTES} bytes, ${TABLES} tabelas, $((SECONDS - START))s"

# 3) Criptografia (o bucket só guarda texto cifrado).
age -r "$BACKUP_AGE_RECIPIENT" -o "$WORK/$NAME.age" "$WORK/$NAME" || die 4 "falha ao criptografar"
rm -f "$WORK/$NAME"
( cd "$WORK" && sha256sum "$NAME.age" > "$NAME.age.sha256" )
log "criptografado: $(stat -c %s "$WORK/$NAME.age") bytes"

if [[ "$DRY_RUN" == "1" ]]; then
  OUT="${BACKUP_OUT_DIR:-.}"
  mkdir -p "$OUT"
  cp "$WORK/$NAME.age" "$WORK/$NAME.age.sha256" "$OUT/"
  log "DRY RUN: nada enviado; arquivo em $OUT/$NAME.age"
  exit 0
fi

# 4) Envio.
export AWS_ACCESS_KEY_ID="$BACKUP_S3_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="$BACKUP_S3_SECRET_ACCESS_KEY"
export AWS_DEFAULT_REGION="${BACKUP_S3_REGION:-auto}"
export AWS_EC2_METADATA_DISABLED=true
S3=(aws s3 --endpoint-url "$BACKUP_S3_ENDPOINT" --only-show-errors)
"${S3[@]}" cp "$WORK/$NAME.age" "s3://$BACKUP_S3_BUCKET/$PREFIX$NAME.age" || die 5 "falha no envio do dump"
"${S3[@]}" cp "$WORK/$NAME.age.sha256" "s3://$BACKUP_S3_BUCKET/$PREFIX$NAME.age.sha256" || die 5 "falha no envio do hash"
log "enviado: ${PREFIX}${NAME}.age"

# 5) Retenção: apaga dumps mais antigos que RETENTION_DAYS (data no nome), guardando no mínimo MIN_KEEP.
CUTOFF="$(date -u -d "-${RETENTION_DAYS} days" +%Y%m%d)"
mapfile -t KEYS < <(aws s3api --endpoint-url "$BACKUP_S3_ENDPOINT" list-objects-v2 \
  --bucket "$BACKUP_S3_BUCKET" --prefix "$PREFIX" --query 'Contents[].Key' --output text 2>/dev/null \
  | tr '\t' '\n' | grep -E 'controle-[0-9]{8}T[0-9]{6}Z\.dump\.age$' | sort || true)
TOTAL="${#KEYS[@]}"
DELETED=0
for key in "${KEYS[@]}"; do
  day="$(sed -E 's/.*controle-([0-9]{8})T.*/\1/' <<<"$key")"
  if [[ "$day" < "$CUTOFF" && $((TOTAL - DELETED)) -gt "$MIN_KEEP" ]]; then
    "${S3[@]}" rm "s3://$BACKUP_S3_BUCKET/$key" || die 5 "falha ao apagar dump antigo"
    "${S3[@]}" rm "s3://$BACKUP_S3_BUCKET/$key.sha256" || true
    DELETED=$((DELETED + 1))
  fi
done
log "retenção: ${RETENTION_DAYS} dias, ${TOTAL} dump(s) no bucket, ${DELETED} apagado(s)"
log "concluído em $((SECONDS - START))s"
