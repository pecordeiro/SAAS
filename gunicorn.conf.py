"""Gunicorn em produção (``gunicorn -c gunicorn.conf.py run:app``). Tudo ajustável por ambiente.

- Sem log de acesso do Gunicorn: o caminho real da requisição leva token (convite, reset,
  confirmação). O app já escreve o log de acesso com a ROTA (molde), sem token nem query
  (app/logging_config.py).
- ``gthread``: poucas threads por processo bastam para uma app com I/O (banco, e-mail em
  thread de fundo). Render Starter (512 MB): 2 processos x 4 threads.
- Reciclagem periódica (``max_requests``) contém vazamento lento de memória.
"""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
worker_class = "gthread"
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "30"))
graceful_timeout = 30
# Acima do ocioso do balanceador do host, para ele nunca reutilizar conexão já fechada.
keepalive = 75
max_requests = 1000
max_requests_jitter = 100
worker_tmp_dir = "/dev/shm"

accesslog = None
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "warning")
