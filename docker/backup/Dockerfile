# Cron Job de backup lógico (render.yaml: controle-backup). Contexto de build = raiz do repositório.
#   docker build -f docker/backup/Dockerfile -t controle-backup .
# pg_dump 16 (mesma major do banco; ao subir o Postgres para 17, troque a tag), age (criptografia),
# aws-cli (envio ao bucket S3/R2). Roda sem root. Nenhum segredo na imagem: tudo por variável.
FROM postgres:16-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends age awscli ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY scripts/backup_dump.sh scripts/backup_photos.sh scripts/backup_run.sh /usr/local/bin/
RUN chmod 0755 /usr/local/bin/backup_dump.sh /usr/local/bin/backup_photos.sh /usr/local/bin/backup_run.sh

# A imagem oficial do Postgres já traz o usuário "postgres" (uid 999) sem shell de login.
USER postgres
# Substitui o entrypoint do Postgres (que subiria um servidor).
# Dump criptografado do banco + espelho do bucket de fotos (se PHOTOS_SRC_BUCKET estiver definido).
ENTRYPOINT ["/usr/local/bin/backup_run.sh"]
