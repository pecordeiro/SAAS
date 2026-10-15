#!/usr/bin/env bash
# Prova que o backup RESTAURA: dump -> restore em banco temporário -> conferência de contagens.
# Mede o tempo (insumo do RTO) e apaga o banco temporário no fim.
#
# Dois modos
#   1) Dump novo da fonte (dev/staging ou produção por leitura):
#        SOURCE_DATABASE_URL=postgresql://... RESTORE_ADMIN_URL=postgresql://postgres@localhost:5432/postgres \
#          scripts/backup_restore_check.sh
#   2) Arquivo de backup já existente (o do bucket, baixado):
#        AGE_IDENTITY_FILE=chave-privada.txt RESTORE_ADMIN_URL=... \
#          scripts/backup_restore_check.sh --dump controle-20261015T060000Z.dump.age [--sem-fonte]
#      Com SOURCE_DATABASE_URL também definido, compara com a fonte (aceite crescimento com
#      --tolerar-crescimento, pois a fonte continua recebendo escrita depois do dump).
#
# Autenticidade (OBRIGATÓRIA): todo --dump precisa de ARQUIVO.sig (ssh-keygen -Y, namespace
# controle-backup) conferido com a chave PÚBLICA do dono ANTES de descriptografar/restaurar. Falta de
# assinatura ou assinatura inválida = falha dura (saída 4). O .sha256 no bucket não autentica nada
# (quem escreve o dump escreve o hash). --allow-unsigned só em dev (aviso alto).
#
# Variáveis
#   BACKUP_SIGN_PUBKEY     chave pública de assinatura (linha "ssh-ed25519 AAAA…") ou BACKUP_SIGN_PUBKEY_FILE
#   SOURCE_DATABASE_URL    fonte (padrão: DATABASE_URL). Precisa enxergar todas as linhas (RLS).
#   RESTORE_ADMIN_URL      servidor ONDE restaurar, com permissão de CREATE/DROP DATABASE.
#                          NUNCA aponte para o banco de produção. Padrão: postgresql://postgres@localhost:5432/postgres
#   AGE_IDENTITY_FILE      chave privada age (só para --dump *.age)
#   KEEP_TEMP=1            não apaga o banco temporário (para inspecionar)
#
# Opções: --dump ARQUIVO · --allow-unsigned (dev) · --sem-fonte (só confere o restaurado) · --tolerar-crescimento
# Saída: 0 ok · 1 divergência · 2 uso/configuração · 3 papel sem acesso a todas as linhas · 4 falha de dump/restore
# Nunca imprime URL nem senha.
set -Eeuo pipefail
set +x

log() { printf '%s restore-check: %s\n' "$(date -u +%FT%TZ)" "$*" >&2; }
die() { local code="$1"; shift; log "ERRO: $*"; exit "$code"; }

DUMP_ARG=""
NO_SOURCE=0
GROWTH=0
ALLOW_UNSIGNED=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dump) DUMP_ARG="${2:-}"; [[ -n "$DUMP_ARG" ]] || die 2 "--dump precisa de um arquivo"; shift 2 ;;
    --sem-fonte) NO_SOURCE=1; shift ;;
    --allow-unsigned) ALLOW_UNSIGNED=1; shift ;;
    --tolerar-crescimento) GROWTH=1; shift ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
    *) die 2 "opção desconhecida: $1" ;;
  esac
done

for tool in pg_dump pg_restore psql; do
  command -v "$tool" >/dev/null || die 2 "ferramenta ausente: $tool"
done

norm_url() { local u="$1"; u="${u/postgresql+psycopg:\/\//postgresql://}"; u="${u/postgres:\/\//postgresql://}"; printf '%s' "$u"; }
# with_db URL NOME -> a mesma URL apontando para outro banco (preserva ?query).
with_db() {
  local url="$1" db="$2" base query=""
  if [[ "$url" == *\?* ]]; then query="?${url#*\?}"; url="${url%%\?*}"; fi
  base="${url%/*}"
  printf '%s/%s%s' "$base" "$db" "$query"
}

# with_user URL USUARIO SENHA -> troca as credenciais da URL (senha só alfanumérica).
with_user() {
  local url="$1" user="$2" pass="$3" scheme rest
  scheme="${url%%://*}"; rest="${url#*://}"; rest="${rest#*@}"
  printf '%s://%s:%s@%s' "$scheme" "$user" "$pass" "$rest"
}

ADMIN_URL="$(norm_url "${RESTORE_ADMIN_URL:-postgresql://postgres@localhost:5432/postgres}")"
SOURCE_URL=""
if [[ "$NO_SOURCE" != "1" ]]; then
  SOURCE_URL="$(norm_url "${SOURCE_DATABASE_URL:-${DATABASE_URL:-}}")"
  if [[ -z "$SOURCE_URL" && -z "$DUMP_ARG" ]]; then
    die 2 "defina SOURCE_DATABASE_URL (ou use --dump ARQUIVO --sem-fonte)"
  fi
  [[ -n "$SOURCE_URL" ]] || NO_SOURCE=1
fi

WORK="$(mktemp -d)"
umask 077
TMPDB="restore_check_$(date -u +%Y%m%d%H%M%S)_$$"
TMPDB_CREATED=0
TMPROLE_CREATED=0
cleanup() {
  if [[ "${KEEP_TEMP:-0}" == "1" ]]; then
    [[ "$TMPDB_CREATED" != "1" ]] || log "KEEP_TEMP=1: banco temporário mantido: $TMPDB (papel $TMPROLE)"
  else
    if [[ "$TMPDB_CREATED" == "1" ]]; then
      psql "$ADMIN_URL" -qAt -c "DROP DATABASE IF EXISTS \"$TMPDB\" WITH (FORCE)" >/dev/null 2>&1 \
        && log "banco temporário apagado" || log "AVISO: apague o banco temporário $TMPDB manualmente"
    fi
    if [[ "$TMPROLE_CREATED" == "1" ]]; then
      psql "$ADMIN_URL" -qAt -c "DROP ROLE IF EXISTS \"$TMPROLE\"" >/dev/null 2>&1 \
        && log "papel temporário removido" || log "AVISO: apague o papel $TMPROLE manualmente"
    fi
  fi
  rm -rf "$WORK"
}
trap cleanup EXIT

# O script só cria e apaga UM banco com nome novo (restore_check_*) no servidor de restauração.
psql "$ADMIN_URL" -Atqc "SELECT 1" >/dev/null || die 2 "não consegui conectar ao servidor de restauração (RESTORE_ADMIN_URL)"
[[ -z "$SOURCE_URL" ]] || psql "$SOURCE_URL" -Atqc "SELECT 1" >/dev/null || die 2 "não consegui conectar à fonte"

# 1) O arquivo a restaurar.
START_ALL=$SECONDS
if [[ -n "$DUMP_ARG" ]]; then
  [[ -f "$DUMP_ARG" ]] || die 2 "arquivo não encontrado: $DUMP_ARG"
  DUMP="$DUMP_ARG"
  if [[ "$ALLOW_UNSIGNED" == "1" ]]; then
    log "################ AVISO ALTO: --allow-unsigned: autenticidade do backup NÃO verificada. Só em dev. ################"
  else
    command -v ssh-keygen >/dev/null || die 2 "ferramenta ausente: ssh-keygen"
    [[ -f "$DUMP_ARG.sig" ]] || die 4 "assinatura ausente ($DUMP_ARG.sig): backup sem assinatura não é restaurado (use --allow-unsigned só em dev)"
    PUB="${BACKUP_SIGN_PUBKEY:-}"
    [[ -n "$PUB" || -z "${BACKUP_SIGN_PUBKEY_FILE:-}" ]] || PUB="$(cat "$BACKUP_SIGN_PUBKEY_FILE")"
    [[ -n "$PUB" ]] || die 2 "defina BACKUP_SIGN_PUBKEY (ou _FILE) com a chave pública de assinatura"
    printf 'controle-backup %s\n' "$PUB" > "$WORK/allowed_signers"
    ssh-keygen -Y verify -f "$WORK/allowed_signers" -I controle-backup -n controle-backup -s "$DUMP_ARG.sig" < "$DUMP_ARG" >/dev/null 2>&1 \
      || die 4 "assinatura INVÁLIDA: o arquivo foi alterado ou não foi assinado pela chave do dono. Não restaurar."
    log "assinatura confere (chave do dono)"
  fi
  if [[ -f "$DUMP_ARG.sha256" ]]; then
    ( cd "$(dirname "$DUMP_ARG")" && sha256sum --check --status "$(basename "$DUMP_ARG").sha256" ) \
      && log "sha256 confere (integridade; a autenticidade vem da assinatura)" || die 4 "sha256 NÃO confere: backup corrompido"
  fi
  if [[ "$DUMP" == *.age ]]; then
    command -v age >/dev/null || die 2 "ferramenta ausente: age"
    [[ -n "${AGE_IDENTITY_FILE:-}" && -f "${AGE_IDENTITY_FILE}" ]] || die 2 "AGE_IDENTITY_FILE (chave privada) ausente para um .age"
    age -d -i "$AGE_IDENTITY_FILE" -o "$WORK/restaurar.dump" "$DUMP" || die 4 "não consegui descriptografar o backup"
    DUMP="$WORK/restaurar.dump"
  fi
else
  can_see_all="$(psql "$SOURCE_URL" -Atqc "SELECT (rolsuper OR rolbypassrls) FROM pg_roles WHERE rolname = current_user")"
  forced="$(psql "$SOURCE_URL" -Atqc "SELECT count(*) FROM pg_class WHERE relkind='r' AND relforcerowsecurity AND relnamespace='public'::regnamespace")"
  if [[ "$can_see_all" != "t" && "$forced" != "0" ]]; then
    die 3 "o papel da fonte não enxerga todas as linhas (RLS forçado em $forced tabela(s)): dump e contagem seriam incompletos."
  fi
  DUMP="$WORK/fonte.dump"
  t0=$SECONDS
  pg_dump "$SOURCE_URL" --format=custom --no-owner --no-privileges --file "$DUMP" || die 4 "pg_dump falhou"
  log "dump da fonte: $(stat -c %s "$DUMP") bytes em $((SECONDS - t0))s"
fi
pg_restore --list "$DUMP" >/dev/null || die 4 "o arquivo não é um dump válido do pg_dump"

# 2) Restaurar em banco temporário, com um papel NÃO-super que é dono só dele (nada de pg_restore
#    como superusuário: um dump malicioso não executa comando de superusuário). O papel é criado
#    aqui e removido no fim. O administrador (RESTORE_ADMIN_URL) só cria/derruba e lê as contagens.
TMPROLE="restore_role_${TMPDB#restore_check_}"
TMPPASS="$(head -c 24 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 24)"
psql "$ADMIN_URL" -qAt -c "CREATE ROLE \"$TMPROLE\" LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD '$TMPPASS'" >/dev/null \
  || die 2 "sem permissão para CREATE ROLE no servidor de restauração (precisa de CREATEROLE)"
TMPROLE_CREATED=1
psql "$ADMIN_URL" -qAt -c "CREATE DATABASE \"$TMPDB\" OWNER \"$TMPROLE\"" >/dev/null || die 2 "sem permissão para CREATE DATABASE no servidor de restauração"
TMPDB_CREATED=1
RESTORED_URL="$(with_db "$ADMIN_URL" "$TMPDB")"                       # leitura das contagens (admin)
RESTORER_URL="$(with_user "$(with_db "$ADMIN_URL" "$TMPDB")" "$TMPROLE" "$TMPPASS")"
t0=$SECONDS
# --no-owner/--no-privileges SÓ porque os papéis de origem (dono, app) não existem neste servidor de
# teste: os objetos passam a ser do papel temporário. Não dá privilégio nenhum; qualquer outra coisa
# que exija superusuário (CREATE EXTENSION não confiável, CREATE ROLE…) continua FALHANDO aqui.
pg_restore --no-owner --no-privileges --exit-on-error --dbname "$RESTORER_URL" "$DUMP" 2> "$WORK/restore.err" \
  || { log "$(head -c 600 "$WORK/restore.err" | sed "s/$TMPPASS/***/g")"; die 4 "pg_restore falhou (como papel sem privilégios; extensão ou objeto que exige superusuário?)"; }
RESTORE_SECONDS=$((SECONDS - t0))
log "restore em ${RESTORE_SECONDS}s (papel temporário sem privilégios)"

# 3) Contagens por tabela (lista de tabelas vem do próprio banco; nomes sempre entre aspas).
counts() {
  local url="$1" sql
  sql="$(psql "$url" -Atqc "SELECT coalesce(string_agg(format('SELECT %L AS t, count(*) AS n FROM public.%I', table_name, table_name), ' UNION ALL ' ORDER BY table_name), 'SELECT NULL WHERE false') FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")"
  psql "$url" -Atq -F '|' -c "SELECT t, n FROM ($sql) c ORDER BY t"
}
rls_summary() {
  psql "$1" -Atq -c "SELECT count(*) FILTER (WHERE relrowsecurity) || ' ligadas, ' || count(*) FILTER (WHERE relforcerowsecurity) || ' forçadas, ' || (SELECT count(*) FROM pg_policies WHERE schemaname='public') || ' políticas' FROM pg_class WHERE relkind='r' AND relnamespace='public'::regnamespace"
}
revision() { psql "$1" -Atq -c "SELECT string_agg(version_num, ',') FROM alembic_version" 2>/dev/null || echo "?"; }

counts "$RESTORED_URL" > "$WORK/restored.counts"
N_TABLES="$(wc -l < "$WORK/restored.counts")"
[[ "$N_TABLES" -gt 0 ]] || die 1 "o banco restaurado não tem nenhuma tabela"
TOTAL_ROWS="$(awk -F'|' '{s+=$2} END{print s+0}' "$WORK/restored.counts")"
REV_RESTORED="$(revision "$RESTORED_URL")"
RESULT=0

echo "== Banco restaurado: ${N_TABLES} tabelas, ${TOTAL_ROWS} linhas, migration ${REV_RESTORED}, RLS: $(rls_summary "$RESTORED_URL")"
if [[ -n "$SOURCE_URL" ]]; then
  counts "$SOURCE_URL" > "$WORK/source.counts"
  REV_SOURCE="$(revision "$SOURCE_URL")"
  echo "== Fonte:            $(wc -l < "$WORK/source.counts") tabelas, $(awk -F'|' '{s+=$2} END{print s+0}' "$WORK/source.counts") linhas, migration ${REV_SOURCE}, RLS: $(rls_summary "$SOURCE_URL")"
  [[ "$REV_SOURCE" == "$REV_RESTORED" ]] || { echo "DIVERGE: migration da fonte ($REV_SOURCE) != restaurada ($REV_RESTORED)"; RESULT=1; }
  while IFS='|' read -r table n_src; do
    n_res="$(awk -F'|' -v t="$table" '$1==t {print $2}' "$WORK/restored.counts")"
    if [[ -z "$n_res" ]]; then
      echo "DIVERGE: tabela ausente no restore: $table"; RESULT=1
    elif [[ "$n_res" != "$n_src" ]]; then
      if [[ "$GROWTH" == "1" && "$n_res" -le "$n_src" ]]; then
        printf 'cresceu na fonte depois do dump: %-28s restaurado=%s fonte=%s\n' "$table" "$n_res" "$n_src"
      else
        printf 'DIVERGE: %-28s restaurado=%s fonte=%s\n' "$table" "$n_res" "$n_src"; RESULT=1
      fi
    fi
  done < "$WORK/source.counts"
  while IFS='|' read -r table _; do
    grep -q "^${table}|" "$WORK/source.counts" || { echo "DIVERGE: tabela só no restore: $table"; RESULT=1; }
  done < "$WORK/restored.counts"
else
  # Sem fonte: sanidade mínima do próprio restore.
  for required in companies users memberships projects plans alembic_version; do
    grep -q "^${required}|" "$WORK/restored.counts" || { echo "DIVERGE: tabela obrigatória ausente: $required"; RESULT=1; }
  done
  [[ "$(awk -F'|' '$1=="plans"{print $2}' "$WORK/restored.counts")" -gt 0 ]] || { echo "DIVERGE: tabela plans vazia"; RESULT=1; }
fi

echo "== Contagens restauradas (tabela|linhas):"
sed 's/^/   /' "$WORK/restored.counts"
echo "== Tempos: restore ${RESTORE_SECONDS}s · total $((SECONDS - START_ALL))s (RTO: some a isto o tempo de baixar o arquivo e trocar o DATABASE_URL)"
if [[ "$RESULT" == "0" ]]; then echo "RESULTADO: OK — backup restaurado e conferido."; else echo "RESULTADO: FALHOU — ver DIVERGE acima."; fi
exit "$RESULT"
