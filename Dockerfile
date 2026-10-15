# syntax=docker/dockerfile:1
# Imagem de PRODUÇÃO (Render e qualquer host de contêiner). Um build serve web, worker e crons:
# o comando muda (gunicorn / flask worker run / flask lgpd-...), a imagem é a mesma.
#
#   docker build -t controle-producao .
#   docker run --rm -p 10000:10000 --env-file .env controle-producao      # web
#   docker run --rm --env-file .env controle-producao flask worker run    # worker
#
# Sem segredo na imagem: tudo vem de variável de ambiente em tempo de execução (.dockerignore
# exclui .env). Roda como usuário sem privilégios; assets minificados com hash gerados aqui.

ARG PYTHON_VERSION=3.12

# ---------------------------------------------------------------- build: dependências + assets
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /build
COPY requirements.txt ./
# Todas as dependências têm wheel (psycopg[binary], Pillow, cryptography): sem compilador.
RUN pip install -r requirements.txt \
 && pip install "rcssmin==1.2.0" "rjsmin==1.2.4"

COPY app ./app
COPY scripts/build_assets.py ./scripts/build_assets.py
RUN python scripts/build_assets.py \
 && python scripts/build_assets.py --check

# ---------------------------------------------------------------- runtime
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:${PATH}" \
    FLASK_APP=run.py \
    APP_ENV=production \
    PORT=10000

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /srv --shell /usr/sbin/nologin app

WORKDIR /srv
COPY --from=builder /opt/venv /opt/venv
COPY app ./app
# Assets reconstruídos no estágio de build substituem os do repositório.
RUN rm -rf app/static/dist
COPY --from=builder /build/app/static/dist ./app/static/dist
COPY migrations ./migrations
COPY run.py gunicorn.conf.py ./
COPY scripts/config_check.py ./scripts/config_check.py

# O código fica de root (somente leitura para o app); só instance/ é gravável.
RUN mkdir -p /srv/instance && chown app:app /srv/instance

USER app
EXPOSE 10000

# Sem ENTRYPOINT: o preDeployCommand e os comandos do worker/cron do Render rodam direto.
# Liveness: GET /saude (sem banco). Prontidão: GET /health.
CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:app"]
