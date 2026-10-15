"""Etapa H — render.yaml, Dockerfile e arquivos de implantação conferem com o app."""

from __future__ import annotations

import importlib.util
import re
import secrets
from pathlib import Path

import pytest
import yaml

from app import configcheck

ROOT = Path(__file__).resolve().parent.parent


def _load_generator():
    spec = importlib.util.spec_from_file_location("gen_render_yaml", ROOT / "scripts" / "gen_render_yaml.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def load(name: str) -> dict:
    return yaml.safe_load((ROOT / name).read_text(encoding="utf-8"))


def by_name(blueprint: dict, kind: str) -> dict:
    return {s["name"]: s for s in blueprint["services"] if s["type"] == kind}


def env_of(service: dict) -> dict:
    return {e["key"]: e for e in service["envVars"]}


@pytest.fixture(params=["render.yaml", "render.staging.yaml"])
def blueprint(request):
    return load(request.param), request.param


def test_arquivos_gerados_estao_em_dia():
    assert gen.main(["--check"]) == 0


def test_servicos_esperados(blueprint):
    bp, nome = blueprint
    tipos = sorted(s["type"] for s in bp["services"])
    if nome == "render.yaml":
        assert tipos == ["cron", "cron", "cron", "keyvalue", "web", "worker"]
    else:
        assert tipos == ["keyvalue", "web", "worker"]
    assert len(bp["databases"]) == 1
    assert bp["databases"][0]["postgresMajorVersion"] == "16"
    # Banco e Redis só na rede privada.
    assert bp["databases"][0]["ipAllowList"] == []
    (redis,) = [s for s in bp["services"] if s["type"] == "keyvalue"]
    assert redis["ipAllowList"] == []


def test_mesma_regiao_em_tudo_e_documentada(blueprint):
    bp, _ = blueprint
    regioes = {s["region"] for s in bp["services"]} | {d["region"] for d in bp["databases"]}
    assert regioes == {gen.REGION}
    assert gen.REGION == "virginia"
    texto = (ROOT / "docs" / "plano" / "operacao.md").read_text(encoding="utf-8")
    assert "Virginia" in texto and "São Paulo" in texto


def test_web_tem_health_check_pre_deploy_e_comando_certo(blueprint, app):
    bp, _ = blueprint
    (web,) = by_name(bp, "web").values()
    assert web["healthCheckPath"] == "/saude"
    assert app.test_client().get(web["healthCheckPath"]).status_code == 200
    pre = web["preDeployCommand"]
    ordem = [pre.index(c) for c in ("flask config-check", "flask db upgrade", "flask seed-plans")]
    assert ordem == sorted(ordem)
    assert "&&" in pre  # config-check reprovado impede a migration
    assert "--online" in pre


def test_comandos_do_worker_e_dos_crons_existem_no_cli(blueprint, app):
    bp, _ = blueprint
    comandos = set(app.cli.commands)
    (worker,) = by_name(bp, "worker").values()
    assert worker["dockerCommand"] == "flask worker run" and "worker" in comandos
    for cron in by_name(bp, "cron").values():
        if "dockerCommand" in cron:
            for parte in re.findall(r"flask ([a-z-]+)", cron["dockerCommand"]):
                assert parte in comandos, parte
        assert re.fullmatch(r"[\d*/, -]+( [\d*/, -]+){4}", cron["schedule"])


def test_segredos_nunca_tem_valor_no_arquivo(blueprint):
    bp, _ = blueprint
    sensivel = re.compile(r"SECRET|KEY|TOKEN|PASSWORD|DSN|ENDPOINT|BUCKET|RECIPIENT|EMAIL|MAIL_FROM|BASE_URL", re.I)
    for service in bp["services"]:
        for var in service.get("envVars", []):
            if sensivel.search(var["key"]) and var["key"] not in {"SENTRY_TRACES_SAMPLE_RATE", "STORAGE_S3_ADDRESSING", "STORAGE_S3_REGION", "ASAAS_BASE_URL"}:
                assert "value" not in var, f"{service['name']}: {var['key']} tem valor literal"
                assert "sync" in var and var["sync"] is False or "fromService" in var or "fromDatabase" in var
    bruto = (ROOT / "render.yaml").read_text(encoding="utf-8")
    assert not re.search(r"\$aact_|re_[A-Za-z0-9]{10,}|age1[a-z0-9]{20,}", bruto)


def test_segredos_so_sao_digitados_no_web(blueprint):
    bp, _ = blueprint
    (web,) = by_name(bp, "web").values()
    pedidos = {k for k, v in env_of(web).items() if v.get("sync") is False}
    assert pedidos == set(gen.SECRETS)
    for service in bp["services"]:
        if service["type"] in {"worker", "cron"} and service["name"] != "controle-backup" and not service["name"].startswith("controle-backup"):
            for key, var in env_of(service).items():
                assert var.get("sync") is not False, f"{service['name']}: {key} pediria o segredo de novo"
                if key in gen.SECRETS:
                    assert var["fromService"] == {"type": "web", "name": web["name"], "envVarKey": key}


def test_banco_e_redis_vem_dos_servicos_do_render(blueprint):
    bp, _ = blueprint
    (db,) = bp["databases"]
    (redis,) = [s for s in bp["services"] if s["type"] == "keyvalue"]
    for service in bp["services"]:
        if service["type"] == "keyvalue":
            continue
        env = env_of(service)
        assert env["DATABASE_URL"]["fromDatabase"] == {"name": db["name"], "property": "connectionString"}
        if "REDIS_URL" in env:
            assert env["REDIS_URL"]["fromService"] == {"type": "keyvalue", "name": redis["name"], "property": "connectionString"}


def test_producao_vs_staging(blueprint):
    bp, nome = blueprint
    (web,) = by_name(bp, "web").values()
    env = env_of(web)
    if nome == "render.yaml":
        assert env["APP_ENV"]["value"] == "production"
        assert "sandbox" not in env["ASAAS_BASE_URL"]["value"]
        assert web["autoDeploy"] is False  # produção só sobe por decisão (go/no-go)
        assert web["branch"] == "main"
    else:
        assert env["APP_ENV"]["value"] == "staging"
        assert "sandbox" in env["ASAAS_BASE_URL"]["value"]
        assert web["branch"] == "staging"


def test_toda_variavel_do_web_e_conhecida_pelo_app(blueprint):
    bp, _ = blueprint
    (web,) = by_name(bp, "web").values()
    exemplo = (ROOT / ".env.example").read_text(encoding="utf-8")
    from app.config import Config

    for key in env_of(web):
        assert key in exemplo or hasattr(Config, key), f"{key} não está em .env.example nem em Config"


def test_rls_e_proxy_ligados_no_blueprint(blueprint):
    bp, _ = blueprint
    (web,) = by_name(bp, "web").values()
    env = env_of(web)
    assert env["RLS_ENABLED"]["value"] == "true"
    assert env["TRUSTED_PROXY_COUNT"]["value"] == "1"
    assert env["READ_ONLY_ENFORCED"]["value"] == "true"
    assert env["MAIL_BACKEND"]["value"] == "resend"
    assert env["STORAGE_BACKEND"]["value"] == "s3"


def test_configuracao_do_blueprint_passa_no_config_check(blueprint, monkeypatch):
    """Preenche os segredos com valores plausíveis e confere que o web do Blueprint, como
    descrito, é aprovado pelo próprio config-check de produção (sem erro nem aviso)."""
    bp, nome = blueprint
    (web,) = by_name(bp, "web").values()
    ambiente = "production" if nome == "render.yaml" else "staging"
    for key, var in env_of(web).items():
        if "value" in var:
            monkeypatch.setenv(key, var["value"])
    producao = ambiente == "production"
    segredos = {
        "SECRET_KEY": secrets.token_hex(32),
        "MFA_ENCRYPTION_KEY": secrets.token_hex(32),
        "APP_BASE_URL": "https://app.controleproducao.com.br",
        "CONTACT_EMAIL": "contato@controleproducao.com.br",
        "MAIL_FROM": "Controle de Produção <nao-responda@controleproducao.com.br>",
        "RESEND_API_KEY": "re_" + secrets.token_hex(16),
        "ASAAS_API_KEY": ("$aact_prod_" if producao else "$aact_hmlg_") + secrets.token_hex(16),
        "ASAAS_WEBHOOK_TOKEN": secrets.token_urlsafe(32),
        "STORAGE_S3_ENDPOINT": "https://conta.r2.cloudflarestorage.com",
        "STORAGE_S3_BUCKET": "fotos",
        "STORAGE_S3_ACCESS_KEY_ID": "id",
        "STORAGE_S3_SECRET_ACCESS_KEY": "segredo",
        "SENTRY_DSN": "https://abc@o1.ingest.sentry.io/1",
        "STAFF_NOTIFY_EMAIL": "equipe@controleproducao.com.br",
        # Valores que o Render injeta:
        "DATABASE_URL": "postgresql://controle:senha@dpg-abc/controle",
        "REDIS_URL": "redis://red-abc:6379",
    }
    for key, value in segredos.items():
        monkeypatch.setenv(key, value)
    cfg, env_name = configcheck.build_config()
    assert env_name == ambiente
    findings, ok = configcheck.evaluate(cfg, env_name, strict=True)
    assert ok, [f.line() for f in findings if f.level != configcheck.INFO]


def test_dockerfile_producao():
    texto = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert len(re.findall(r"^FROM ", texto, re.M)) >= 2  # multi-stage
    assert re.search(r"^USER app$", texto, re.M)
    assert "build_assets.py" in texto
    assert 'CMD ["gunicorn"' in texto and "ENTRYPOINT" not in texto.replace("# Sem ENTRYPOINT", "")
    # Sem segredo nem arquivo de ambiente na imagem.
    assert not re.search(r"^(ENV|ARG)\s+\S*(SECRET|PASSWORD|TOKEN|API_KEY|DSN)\S*", texto, re.M | re.I)
    assert not re.search(r"COPY\s+.*\.env(\s|$)", texto)
    assert "EXPOSE 10000" in texto


def test_dockerignore_deixa_segredos_e_testes_de_fora():
    linhas = {l.strip() for l in (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()}
    for item in (".env", ".env.*", "instance/", "tests/", ".git", "*.db", "*.dump", "*.age"):
        assert item in linhas, item


def test_gunicorn_sem_log_de_acesso_com_token_no_caminho():
    spec = importlib.util.spec_from_file_location("gunicorn_conf", ROOT / "gunicorn.conf.py")
    conf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(conf)
    assert conf.accesslog is None
    assert conf.worker_class == "gthread"
    assert conf.bind.endswith(":10000")


def test_imagem_de_backup_sem_segredo_e_sem_root():
    texto = (ROOT / "docker" / "backup" / "Dockerfile").read_text(encoding="utf-8")
    assert re.search(r"^USER postgres$", texto, re.M)
    assert "age" in texto and "awscli" in texto
    assert not re.search(r"^(ENV|ARG)\s+\S*(SECRET|KEY|PASSWORD|TOKEN)", texto, re.M | re.I)
    render = load("render.yaml")
    (cron,) = [s for s in render["services"] if s["name"] == "controle-backup"]
    assert cron["dockerfilePath"] == "./docker/backup/Dockerfile"
    assert {k for k, v in env_of(cron).items() if v.get("sync") is False} == set(gen.BACKUP_SECRETS)
    assert env_of(cron)["BACKUP_RETENTION_DAYS"]["value"] == "30"  # docs/plano/lgpd.md


def test_arquivos_de_ambiente_listam_as_novas_variaveis():
    exemplo = (ROOT / ".env.example").read_text(encoding="utf-8")
    for nome in ("CONTACT_EMAIL", "BACKUP_AGE_RECIPIENT", "BACKUP_S3_BUCKET", "RESTORE_ADMIN_URL"):
        assert nome in exemplo, nome


def test_ferramentas_de_assets_do_dockerfile_batem_com_requirements_dev():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    dev = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    for pacote in ("rcssmin", "rjsmin"):
        no_dev = re.search(rf"^{pacote}==([\d.]+)", dev, re.M).group(1)
        assert f"{pacote}=={no_dev}" in dockerfile
