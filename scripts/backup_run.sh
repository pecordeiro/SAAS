#!/usr/bin/env bash
# Entrada do Cron Job de backup: dump do banco E espelho das fotos. Um falhar não impede o outro;
# o código de saída é diferente de zero se qualquer um falhar (o Render avisa por e-mail).
# Fotos só rodam se PHOTOS_SRC_BUCKET estiver definido.
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
status=0
"$DIR/backup_dump.sh" || status=$?
if [[ -n "${PHOTOS_SRC_BUCKET:-}" ]]; then
  "$DIR/backup_photos.sh" || status=$?
else
  echo "$(date -u +%FT%TZ) backup: PHOTOS_SRC_BUCKET vazio: fotos fora deste backup" >&2
fi
exit "$status"
