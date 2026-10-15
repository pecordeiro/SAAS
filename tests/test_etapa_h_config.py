"""Etapa H — ``flask config-check``, ``flask mail-test``, ``flask storage-test`` e métricas do worker."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app import configcheck
from app.extensions import db
from app.models import DomainEvent
from app.services import email as email_svc
from app.services import events, storage, worker
from tests.conftest import make_tenant, requires_postgres

SEGREDO = "k3y-aleatoria-9f8e7d6c5b4a39281706f5e4d3c2b1a0-ok"


def prod_config(**over) -> dict:
    """Uma configuração de produção válida; cada teste estraga uma coisa."""
    cfg = {
        "SECRET_KEY": SEGREDO,
        "MFA_ENCRYPTION_KEY": "m3f4-outra-chave-aleatoria-1234567890abcdef-xyz",
        "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://u:p@dpg-abc.oregon-postgres.render.com/controle",
        "APP_BASE_URL": "https://app.controleproducao.com.br",
        "CONTACT_EMAIL": "contato@controleproducao.com.br",
        "TRUSTED_PROXY_COUNT": 1,
        "SESSION_COOKIE_SECURE": True,
        "REMEMBER_COOKIE_SECURE": True,
        "RATELIMIT_ENABLED": True,
        "RATELIMIT_STORAGE_URI": "redis://red-abc:6379",
        "RLS_ENABLED": True,
        "MAIL_BACKEND": "resend",
        "RESEND_API_KEY": "re_chave_de_teste",
        "MAIL_FROM": "Controle de Produção <nao-responda@controleproducao.com.br>",
        "STORAGE_BACKEND": "s3",
        "STORAGE_S3_ENDPOINT": "https://conta.r2.cloudflarestorage.com",
        "STORAGE_S3_BUCKET": "fotos",
        "STORAGE_S3_ACCESS_KEY_ID": "id",
        "STORAGE_S3_SECRET_ACCESS_KEY": "segredo",
        "BILLING_PROVIDER": "asaas",
        "ASAAS_API_KEY": "$aact_prod_abcdef",
        "ASAAS_BASE_URL": "https://api.asaas.com/v3",
        "ASAAS_WEBHOOK_TOKEN": "t" * 40,
        "READ_ONLY_ENFORCED": True,
        "SENTRY_DSN": "https://abc@o1.ingest.sentry.io/1",
        "STAFF_NOTIFY_EMAIL": "equipe@controleproducao.com.br",
        "LOG_JSON": True,
        "LOG_LEVEL": "INFO",
        "SECRET_KEY_FALLBACKS": [],
        "FEATURE_PUBLIC_API": False,
    }
    cfg.update(over)
    return cfg


@pytest.fixture(autouse=True)
def _app_env_definido(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")


def codes(findings, level=None):
    return {f.code for f in findings if level is None or f.level == level}


def test_configuracao_valida_de_producao_passa_sem_erro_nem_aviso():
    findings, ok = configcheck.evaluate(prod_config(), "production", strict=True)
    assert ok, [f.line() for f in findings if f.level != configcheck.INFO]
    assert codes(findings, configcheck.ERRO) == set()


@pytest.mark.parametrize(
    "mudanca, codigo",
    [
        ({"SECRET_KEY": None}, "SECRET_KEY"),
        ({"SECRET_KEY": "curta"}, "SECRET_KEY"),
        ({"SECRET_KEY": "a" * 40}, "SECRET_KEY"),
        ({"SECRET_KEY": "troque-esta-chave-por-uma-aleatoria-123456"}, "SECRET_KEY"),
        ({"MFA_ENCRYPTION_KEY": None}, "MFA_ENCRYPTION_KEY"),
        ({"MFA_ENCRYPTION_KEY": "fraca"}, "MFA_ENCRYPTION_KEY"),
        ({"SQLALCHEMY_DATABASE_URI": None}, "DATABASE_URL"),
        ({"SQLALCHEMY_DATABASE_URI": "sqlite:///dev.db"}, "DATABASE_URL"),
        ({"SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://u:p@localhost/controle"}, "DATABASE_URL"),
        ({"APP_BASE_URL": None}, "APP_BASE_URL"),
        ({"APP_BASE_URL": "http://app.controleproducao.com.br"}, "APP_BASE_URL"),
        ({"APP_BASE_URL": "https://localhost:5000"}, "APP_BASE_URL"),
        ({"CONTACT_EMAIL": "contato@controledeproducao.example"}, "CONTACT_EMAIL"),
        ({"TRUSTED_PROXY_COUNT": 0}, "TRUSTED_PROXY_COUNT"),
        ({"SESSION_COOKIE_SECURE": False}, "COOKIES"),
        ({"RATELIMIT_ENABLED": False}, "RATELIMIT"),
        ({"RATELIMIT_STORAGE_URI": "memory://"}, "REDIS_URL"),
        ({"RLS_ENABLED": False}, "RLS_ENABLED"),
        ({"MAIL_BACKEND": "console"}, "MAIL_BACKEND"),
        ({"MAIL_BACKEND": "", "RESEND_API_KEY": None}, "MAIL_BACKEND"),
        ({"RESEND_API_KEY": None}, "RESEND_API_KEY"),
        ({"MAIL_FROM": "Controle <nao-responda@localhost>"}, "MAIL_FROM"),
        ({"STORAGE_BACKEND": "local"}, "STORAGE_BACKEND"),
        ({"STORAGE_S3_BUCKET": None}, "STORAGE_S3"),
        ({"STORAGE_S3_ENDPOINT": "http://minio:9000"}, "STORAGE_S3"),
        ({"BILLING_PROVIDER": "fake", "ASAAS_API_KEY": None}, "BILLING_PROVIDER"),
        ({"ASAAS_API_KEY": None}, "ASAAS_API_KEY"),
        ({"ASAAS_BASE_URL": "https://api-sandbox.asaas.com/v3"}, "ASAAS_BASE_URL"),
        ({"ASAAS_API_KEY": "$aact_hmlg_abcdef"}, "ASAAS_API_KEY"),
        ({"ASAAS_WEBHOOK_TOKEN": None}, "ASAAS_WEBHOOK_TOKEN"),
        ({"READ_ONLY_ENFORCED": False}, "READ_ONLY_ENFORCED"),
    ],
)
def test_cada_problema_de_producao_reprova(mudanca, codigo):
    findings, ok = configcheck.evaluate(prod_config(**mudanca), "production")
    assert not ok
    assert codigo in codes(findings, configcheck.ERRO)


def test_lista_tudo_de_uma_vez_e_ordena_erros_primeiro():
    cfg = prod_config(SECRET_KEY=None, RLS_ENABLED=False, MAIL_BACKEND="console", SENTRY_DSN=None)
    findings, ok = configcheck.evaluate(cfg, "production")
    assert not ok
    assert {"SECRET_KEY", "RLS_ENABLED", "MAIL_BACKEND"} <= codes(findings, configcheck.ERRO)
    niveis = [f.level for f in findings]
    assert niveis == sorted(niveis, key=lambda n: {"erro": 0, "aviso": 1, "info": 2}[n])


def test_avisos_so_reprovam_com_strict():
    cfg = prod_config(SENTRY_DSN=None, STORAGE_BACKEND="none")
    findings, ok = configcheck.evaluate(cfg, "production")
    assert ok and {"SENTRY_DSN", "STORAGE_BACKEND"} <= codes(findings, configcheck.AVISO)
    _, ok_strict = configcheck.evaluate(cfg, "production", strict=True)
    assert not ok_strict


def test_staging_pode_usar_sandbox_e_rls_desligado_vira_aviso():
    cfg = prod_config(ASAAS_BASE_URL="https://api-sandbox.asaas.com/v3", ASAAS_API_KEY="$aact_hmlg_x", RLS_ENABLED=False)
    findings, ok = configcheck.evaluate(cfg, "staging")
    assert ok
    assert "RLS_ENABLED" in codes(findings, configcheck.AVISO)
    assert "ASAAS_BASE_URL" not in codes(findings, configcheck.ERRO)


def test_staging_com_asaas_de_producao_avisa():
    findings, _ = configcheck.evaluate(prod_config(), "staging")
    assert "ASAAS_BASE_URL" in codes(findings, configcheck.AVISO)


def test_fora_de_producao_erro_vira_aviso_e_nao_reprova():
    findings, ok = configcheck.evaluate(prod_config(SECRET_KEY=None, MAIL_BACKEND="console"), "development", strict=True)
    assert ok
    assert not codes(findings, configcheck.ERRO)
    assert "SECRET_KEY" in codes(findings, configcheck.AVISO)


def test_ignorar_um_codigo_o_rebaixa_para_info():
    findings, ok = configcheck.evaluate(prod_config(RLS_ENABLED=False), "production", ignore=("rls_enabled",))
    assert ok
    assert "RLS_ENABLED" in codes(findings, configcheck.INFO)


def test_mensagens_nunca_trazem_valor_de_segredo():
    segredos = {
        "SECRET_KEY": "valor-secreto-unico-do-teste",
        "RESEND_API_KEY": "re_SEGREDO_UNICO_123",
        "ASAAS_API_KEY": "$aact_hmlg_SEGREDO_UNICO_456",
        "ASAAS_WEBHOOK_TOKEN": "curto-SEGREDO_UNICO_789",
        "MFA_ENCRYPTION_KEY": "mfa-SEGREDO_UNICO_000",
        "STORAGE_S3_SECRET_ACCESS_KEY": "s3-SEGREDO_UNICO_111",
        "SQLALCHEMY_DATABASE_URI": "sqlite://user:SENHA_UNICA_222@x/y",
    }
    findings, _ = configcheck.evaluate(prod_config(**segredos), "production", strict=True)
    texto = "\n".join(f.line() for f in findings)
    for valor in segredos.values():
        assert valor not in texto
    assert "SEGREDO_UNICO" not in texto and "SENHA_UNICA" not in texto


def test_weak_secret():
    assert configcheck.weak_secret("x" * 10)
    assert configcheck.weak_secret("ab" * 20)
    assert configcheck.weak_secret("minha-senha-super-secreta-123456789012")
    assert configcheck.weak_secret(SEGREDO) is None


def test_build_config_le_o_ambiente_sem_criar_o_app(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", SEGREDO)
    monkeypatch.setenv("REDIS_URL", "redis://red:6379")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    cfg, env_name = configcheck.build_config()
    assert env_name == "production"
    assert cfg["SECRET_KEY"] == SEGREDO and cfg["RATELIMIT_STORAGE_URI"] == "redis://red:6379"
    findings, ok = configcheck.evaluate(cfg, env_name)
    assert not ok and "DATABASE_URL" in codes(findings, configcheck.ERRO)


# ------------------------------------------------------------------ comando flask config-check


def test_cli_config_check_reprova_com_codigo_1_e_nomeia_o_que_falta(app):
    app.config["ENV_NAME"] = "production"  # o app de teste finge ser produção para o comando
    result = app.test_cli_runner().invoke(args=["config-check"])
    assert result.exit_code == 1
    assert "REPROVADO" in result.output
    for codigo in ("MFA_ENCRYPTION_KEY", "TRUSTED_PROXY_COUNT", "REDIS_URL", "MAIL_BACKEND", "RLS_ENABLED"):
        assert codigo in result.output
    assert app.config["SECRET_KEY"] not in result.output


def test_cli_config_check_aprova_configuracao_valida(app):
    app.config.update(prod_config(SQLALCHEMY_DATABASE_URI=app.config["SQLALCHEMY_DATABASE_URI"]))
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg://u:p@db.interno/controle"
    app.config["ENV_NAME"] = "production"
    result = app.test_cli_runner().invoke(args=["config-check", "--strict"])
    assert result.exit_code == 0, result.output
    assert "APROVADO" in result.output


def test_cli_config_check_em_desenvolvimento_so_avisa(app):
    result = app.test_cli_runner().invoke(args=["config-check", "--strict"])
    assert result.exit_code == 0
    assert "ensaio" in result.output


def test_cli_config_check_ignorar(app):
    app.config.update(prod_config())
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg://u:p@db.interno/controle"
    app.config["RLS_ENABLED"] = False
    app.config["ENV_NAME"] = "production"
    assert app.test_cli_runner().invoke(args=["config-check"]).exit_code == 1
    assert app.test_cli_runner().invoke(args=["config-check", "--ignorar", "RLS_ENABLED"]).exit_code == 0


# ------------------------------------------------------------------ flask mail-test


def test_mail_test_envia_pelo_backend_console_em_dev(app):
    result = app.test_cli_runner().invoke(args=["mail-test", "Pedro@Exemplo.com.br"])
    assert result.exit_code == 0, result.output
    assert "***@exemplo.com.br" in result.output and "Pedro" not in result.output
    (mensagem,) = email_svc.outbox(app)
    assert mensagem.to == "Pedro@exemplo.com.br" and mensagem.subject.startswith("[teste]")
    assert "Authentication-Results" in mensagem.text


def test_mail_test_recusa_destino_invalido(app):
    result = app.test_cli_runner().invoke(args=["mail-test", "isto-nao-e-email"])
    assert result.exit_code == 1
    assert email_svc.outbox(app) == []


def test_mail_test_recusa_console_em_producao(app):
    app.config["ENV_NAME"] = "production"
    result = app.test_cli_runner().invoke(args=["mail-test", "a@b.com.br"])
    assert result.exit_code == 1
    assert "RESEND_API_KEY" in result.output
    assert email_svc.outbox(app) == []


def test_mail_test_com_resend_ok_e_falha_sem_vazar_chave(app, monkeypatch):
    import requests

    chamadas = []

    class Resposta:
        def __init__(self, status):
            self.status_code = status

    def post(url, headers, json, timeout):
        chamadas.append((url, json["to"]))
        return Resposta(200 if len(chamadas) == 1 else 403)

    monkeypatch.setattr(requests, "post", post)
    chave = "re_CHAVE_QUE_NAO_PODE_VAZAR"
    app.extensions["email_sender"] = email_svc.ResendEmailSender(chave, "Controle <nao-responda@dominio.com.br>", 3)
    ok = app.test_cli_runner().invoke(args=["mail-test", "dono@dominio.com.br"])
    assert ok.exit_code == 0 and "Enviado" in ok.output
    assert chamadas[0] == (email_svc.RESEND_URL, ["dono@dominio.com.br"])
    falha = app.test_cli_runner().invoke(args=["mail-test", "dono@dominio.com.br"])
    assert falha.exit_code == 1
    assert "domínio" in falha.output
    assert chave not in ok.output and chave not in falha.output


# ------------------------------------------------------------------ flask storage-test


def test_storage_test_local_grava_le_e_apaga(app, tmp_path):
    storage.set_storage(app, storage.LocalStorage(tmp_path))
    result = app.test_cli_runner().invoke(args=["storage-test"])
    assert result.exit_code == 0, result.output
    assert "PUT ok" in result.output and "DELETE ok" in result.output
    assert [p for p in tmp_path.rglob("*") if p.is_file()] == []


def test_storage_test_desligado_falha(app):
    storage.set_storage(app, storage.DisabledStorage())
    result = app.test_cli_runner().invoke(args=["storage-test"])
    assert result.exit_code == 1


def test_storage_test_falha_de_rede_apaga_e_sai_com_erro(app):
    class Quebrado(storage.Storage):
        name = "s3"

        def put(self, key, data, content_type):
            raise storage.StorageError("HTTP 403")

        def delete(self, key):
            pass

    storage.set_storage(app, Quebrado())
    result = app.test_cli_runner().invoke(args=["storage-test"])
    assert result.exit_code == 1 and "HTTP 403" in result.output


# ------------------------------------------------------------------ worker status --check


def test_worker_status_check_fila_vazia_ok(app):
    with app.app_context():
        make_tenant("A")
        worker.process_events(datetime.now(timezone.utc))
    result = app.test_cli_runner().invoke(args=["worker", "status", "--check"])
    assert result.exit_code == 0, result.output
    assert "worker_queue pending=0 dead=0" in result.output


def test_worker_status_check_acusa_evento_parado_e_esgotado(app):
    with app.app_context():
        a = make_tenant("A")
        evento = db.session.query(DomainEvent).filter_by(company_id=a.company_id).first()
        evento.created_at = datetime.now(timezone.utc) - timedelta(minutes=40)
        db.session.commit()
        metricas = worker.queue_metrics()
    assert metricas["pending"] == 1 and metricas["dead"] == 0 and metricas["oldest_pending_seconds"] >= 40 * 60
    parado = app.test_cli_runner().invoke(args=["worker", "status", "--check"])
    assert parado.exit_code == 1 and "worker parado" in parado.output
    tolerante = app.test_cli_runner().invoke(args=["worker", "status", "--check", "--max-idade-min", "120"])
    assert tolerante.exit_code == 0

    with app.app_context():
        evento = db.session.query(DomainEvent).first()
        evento.attempts = worker.max_attempts()
        db.session.commit()
    esgotado = app.test_cli_runner().invoke(args=["worker", "status", "--check", "--max-idade-min", "120"])
    assert esgotado.exit_code == 1 and "dead=1" in esgotado.output


def test_worker_status_sem_flags_continua_igual(app):
    result = app.test_cli_runner().invoke(args=["worker", "status"])
    assert result.exit_code == 0


def test_online_redis_inacessivel_reprova_sem_vazar_a_url():
    cfg = prod_config(RATELIMIT_STORAGE_URI="redis://:senha-do-redis@127.0.0.1:1/0", SQLALCHEMY_DATABASE_URI="sqlite://")
    findings, ok = configcheck.evaluate(cfg, "production", online=True)
    assert not ok and "REDIS_ONLINE" in codes(findings, configcheck.ERRO)
    assert "senha-do-redis" not in "\n".join(f.line() for f in findings)
    assert "DB_ONLINE" in codes(findings, configcheck.AVISO)


@requires_postgres
def test_online_postgres_confere_papel_migrations_e_rls(app):
    from tests.conftest import get_test_database_url

    cfg = prod_config(SQLALCHEMY_DATABASE_URI=get_test_database_url(), RATELIMIT_STORAGE_URI="memory://")
    findings, _ = configcheck.evaluate(cfg, "production", online=True)
    por_codigo = {f.code: f for f in findings}
    assert por_codigo["DB_ONLINE"].level == configcheck.INFO
    assert por_codigo["MIGRATIONS"].message == "Schema na última migration."
    # A suíte roda com superusuário no compose: com RLS_ENABLED o app seria reprovado por isso.
    assert por_codigo["DB_ROLE"].level in {configcheck.INFO, configcheck.ERRO}
    assert por_codigo["RLS_FORCED"].level in {configcheck.INFO, configcheck.AVISO}


# ------------------------------------------------------------------ flask sentry-test (filtro validado de ponta a ponta)


def test_sentry_test_sem_dsn_falha(app):
    result = app.test_cli_runner().invoke(args=["sentry-test"])
    assert result.exit_code == 1 and "SENTRY_DSN" in result.output


def test_sentry_test_evento_sai_filtrado(app_factory, monkeypatch):
    import json

    import sentry_sdk
    from sentry_sdk.transport import Transport

    capturados: list[dict] = []

    class Captura(Transport):
        def capture_envelope(self, envelope):
            for item in envelope.items:
                if item.headers.get("type") == "event":
                    capturados.append(json.loads(item.get_bytes()))

    original = sentry_sdk.init
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: original(**kw, transport=Captura()))
    try:
        app = app_factory({"SENTRY_DSN": "https://chave@o1.ingest.sentry.io/1"})
        result = app.test_cli_runner().invoke(args=["sentry-test"])
        assert result.exit_code == 0, result.output
        assert len(capturados) == 1
        bruto = json.dumps(capturados[0])
        for vazamento in ("pessoa@exemplo.com", "cp_abcdefghijklmnopqrstuvwxyz012345", "203.0.113.7"):
            assert vazamento not in bruto, vazamento
        assert capturados[0]["user"] == {"id": "usuario-de-teste"}
        assert capturados[0]["extra"]["token"] == "[filtrado]"
    finally:
        monkeypatch.undo()
        sentry_sdk.init()  # desliga o cliente global para não vazar para outros testes
