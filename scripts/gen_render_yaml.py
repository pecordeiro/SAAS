"""Gera render.yaml (produção) e render.staging.yaml (homologação) a partir de UMA descrição.

Por que gerar: web, worker e crons repetem dezenas de variáveis; editar três lugares à mão
em dois arquivos é como as configurações divergem. Aqui a lista está num só lugar e o CI roda
``python scripts/gen_render_yaml.py --check`` (falha se os arquivos commitados ficarem fora de sincronia).

Uso:
    python scripts/gen_render_yaml.py            # reescreve render.yaml e render.staging.yaml
    python scripts/gen_render_yaml.py --check    # só confere (CI)

Regras do desenho (docs/plano/operacao.md e lancamento.md):
- Segredo NUNCA tem valor aqui: ``sync: false`` (o Render pergunta uma vez, na criação do Blueprint).
  Só o serviço web recebe os segredos; worker e crons os leem do web com ``fromService``/``envVarKey``,
  então cada segredo é digitado uma única vez.
- DATABASE_URL vem do banco (``fromDatabase``) e REDIS_URL do Key Value (``fromService``).
- Região única para tudo (rede privada exige a mesma região).
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# O Render não tem região em São Paulo. A mais próxima do Brasil é Virginia (leste dos EUA);
# confirme no painel se surgiu uma região melhor (a lista muda) e troque aqui: tudo no mesmo lugar.
REGION = "virginia"

HEADER = (
    "# GERADO por scripts/gen_render_yaml.py — NÃO edite à mão (o CI confere). Veja docs/plano/lancamento.md.\n"
    "# Valide antes de criar o Blueprint:  render blueprints validate {name}\n"
    "# Segredos: todos `sync: false` — o Render pergunta o valor uma única vez, no serviço web.\n"
)

# Segredos e valores próprios da conta/domínio: pedidos uma vez, no web.
SECRETS = (
    "SECRET_KEY",
    "MFA_ENCRYPTION_KEY",
    "APP_BASE_URL",
    "CONTACT_EMAIL",
    "MAIL_FROM",
    "RESEND_API_KEY",
    "ASAAS_API_KEY",
    "ASAAS_WEBHOOK_TOKEN",
    "STORAGE_S3_ENDPOINT",
    "STORAGE_S3_BUCKET",
    "STORAGE_S3_ACCESS_KEY_ID",
    "STORAGE_S3_SECRET_ACCESS_KEY",
    "SENTRY_DSN",
    "STAFF_NOTIFY_EMAIL",
)

BACKUP_SECRETS = (
    "BACKUP_S3_ENDPOINT",
    "BACKUP_S3_BUCKET",
    "BACKUP_S3_ACCESS_KEY_ID",
    "BACKUP_S3_SECRET_ACCESS_KEY",
    "BACKUP_AGE_RECIPIENT",
)


def environments() -> dict[str, dict]:
    return {
        "production": {
            "file": "render.yaml",
            "suffix": "",
            "branch": "main",
            "auto_deploy": False,  # deploy manual, depois do go/no-go (lancamento.md)
            "app_env": "production",
            "asaas_url": "https://api.asaas.com/v3",
            "db_plan": "basic-1gb",
            "kv_plan": "starter",
            "compute_plan": "starter",
            "crons": True,
        },
        "staging": {
            "file": "render.staging.yaml",
            "suffix": "-staging",
            "branch": "staging",
            "auto_deploy": True,  # homologação acompanha o branch staging
            "app_env": "staging",
            "asaas_url": "https://api-sandbox.asaas.com/v3",
            "db_plan": "basic-256mb",
            "kv_plan": "starter",
            "compute_plan": "starter",
            "crons": False,
        },
    }


def app_env_vars(env: dict, names: dict, *, owner: str | None) -> list[dict]:
    """Variáveis de qualquer serviço que sobe o app. ``owner`` = None para o web (dono dos segredos);
    nos demais, cada segredo vira ``fromService`` apontando para o web."""
    values = {
        "APP_ENV": env["app_env"],
        "LOG_JSON": "true",
        "LOG_LEVEL": "INFO",
        "RLS_ENABLED": "true",
        "FEATURE_PUBLIC_API": "false",
        "READ_ONLY_ENFORCED": "true",
        "BILLING_PROVIDER": "asaas",
        "ASAAS_BASE_URL": env["asaas_url"],
        "MAIL_BACKEND": "resend",
        "STORAGE_BACKEND": "s3",
        "STORAGE_S3_REGION": "auto",
        "STORAGE_S3_ADDRESSING": "path",
        "SENTRY_TRACES_SAMPLE_RATE": "0",
    }
    out: list[dict] = [{"key": k, "value": v} for k, v in values.items()]
    out.append({"key": "DATABASE_URL", "fromDatabase": {"name": names["db"], "property": "connectionString"}})
    out.append({"key": "REDIS_URL", "fromService": {"type": "keyvalue", "name": names["redis"], "property": "connectionString"}})
    for key in SECRETS:
        if owner is None:
            out.append({"key": key, "sync": False})
        else:
            out.append({"key": key, "fromService": {"type": "web", "name": owner, "envVarKey": key}})
    return out


def build(env: dict) -> dict:
    s = env["suffix"]
    names = {
        "web": f"controle-web{s}",
        "worker": f"controle-worker{s}",
        "lgpd": f"controle-lgpd{s}",
        "backup": f"controle-backup{s}",
        "monitor": f"controle-monitor{s}",
        "redis": f"controle-redis{s}",
        "db": f"controle-db{s}",
    }
    docker = {
        "runtime": "docker",
        "region": REGION,
        "plan": env["compute_plan"],
        "dockerfilePath": "./Dockerfile",
        "dockerContext": ".",
        "branch": env["branch"],
    }
    web_vars = app_env_vars(env, names, owner=None)
    # Atrás do proxy do Render há exatamente 1 salto: sem isto, todo cliente teria o IP do proxy.
    web_vars.insert(1, {"key": "TRUSTED_PROXY_COUNT", "value": "1"})
    web = {
        "type": "web",
        "name": names["web"],
        **docker,
        "autoDeploy": env["auto_deploy"],
        # Liveness sem banco (app/blueprints/public.py::saude): queda do banco não reinicia o web.
        "healthCheckPath": "/saude",
        # Falha aqui (config insegura, migration quebrada) cancela o deploy e mantém a versão atual.
        "preDeployCommand": 'sh -c "flask config-check --online && flask db upgrade && flask seed-plans"',
        "envVars": web_vars,
    }
    worker = {
        "type": "worker",
        "name": names["worker"],
        **docker,
        "autoDeploy": env["auto_deploy"],
        "dockerCommand": "flask worker run",
        "envVars": app_env_vars(env, names, owner=names["web"])
        + [{"key": "WORKER_INTERVAL_SECONDS", "value": "30"}],
    }
    services = [web, worker]
    if env["crons"]:
        services.append(
            {
                "type": "cron",
                "name": names["lgpd"],
                **docker,
                "autoDeploy": env["auto_deploy"],
                # 06:00 UTC = 03:00 em Brasília. Retenção e expurgo LGPD (docs/plano/lgpd.md).
                "schedule": "0 6 * * *",
                "dockerCommand": 'sh -c "flask lgpd-retencao && flask lgpd-purge"',
                "envVars": app_env_vars(env, names, owner=names["web"]),
            }
        )
        services.append(
            {
                "type": "cron",
                "name": names["backup"],
                "runtime": "docker",
                "region": REGION,
                "plan": env["compute_plan"],
                "dockerfilePath": "./docker/backup/Dockerfile",
                "dockerContext": ".",
                "branch": env["branch"],
                "autoDeploy": env["auto_deploy"],
                # 07:00 UTC = 04:00 em Brasília, depois do expurgo das 03:00.
                "schedule": "0 7 * * *",
                "envVars": [
                    {"key": "DATABASE_URL", "fromDatabase": {"name": names["db"], "property": "connectionString"}},
                    {"key": "BACKUP_RETENTION_DAYS", "value": "30"},
                    {"key": "BACKUP_PREFIX", "value": "db/"},
                    # Espelho das fotos: bucket de origem = o do app (a chave de backup precisa de leitura nele).
                    {"key": "PHOTOS_SRC_BUCKET", "fromService": {"type": "web", "name": names["web"], "envVarKey": "STORAGE_S3_BUCKET"}},
                    *({"key": k, "sync": False} for k in BACKUP_SECRETS),
                ],
            }
        )
    if env["crons"]:
        services.append(
            {
                "type": "cron",
                "name": names["monitor"],
                **docker,
                "autoDeploy": env["auto_deploy"],
                # Sai com 1 se há evento esgotado ou pendente há > 15 min: o Render avisa de cron que falhou.
                "schedule": "*/10 * * * *",
                "dockerCommand": "flask worker status --check",
                "envVars": app_env_vars(env, names, owner=names["web"]),
            }
        )
    services.append(
        {
            "type": "keyvalue",
            "name": names["redis"],
            "region": REGION,
            "plan": env["kv_plan"],
            # Contadores do rate limit: se faltar memória, descartar o mais antigo é aceitável.
            "maxmemoryPolicy": "allkeys-lru",
            "ipAllowList": [],  # só a rede privada do Render
        }
    )
    return {
        "services": services,
        "databases": [
            {
                "name": names["db"],
                "databaseName": "controle",
                "user": "controle",
                "region": REGION,
                "plan": env["db_plan"],
                "postgresMajorVersion": "16",
                "ipAllowList": [],  # só a rede privada; para pg_dump externo, libere o seu IP no painel
            }
        ],
    }


def render(name: str, env: dict) -> str:
    body = yaml.safe_dump(build(env), sort_keys=False, allow_unicode=True, width=120, default_flow_style=False)
    return HEADER.format(name=env["file"]) + body


def main(argv: list[str]) -> int:
    check = "--check" in argv
    status = 0
    for name, env in environments().items():
        path = ROOT / env["file"]
        text = render(name, env)
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                print(f"{env['file']} fora de sincronia: rode python scripts/gen_render_yaml.py", file=sys.stderr)
                status = 1
        else:
            path.write_text(text, encoding="utf-8")
            print(f"escrito {env['file']}")
    return status


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
