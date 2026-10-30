"""Etapa G — interface de armazenamento: disco local (dev/test), S3 compatível (SigV4 próprio)
e configuração por ambiente (segredos só em env; disco local nunca em produção)."""

from __future__ import annotations

import hashlib
import os
import stat
import uuid
from datetime import datetime, timezone

import pytest

from app import create_app
from app.services import storage
from app.services.storage import EMPTY_SHA256, LocalStorage, S3Storage, sign_v4

COMPANY = uuid.UUID("11111111-2222-4333-8444-555555555555")
OBJ = uuid.UUID("66666666-7777-4888-9999-aaaaaaaaaaaa")
KEY = f"{COMPANY}/fotos/{OBJ}.jpg"


# ---------------------------------------------------------------- chaves


def test_chave_gerada_tem_prefixo_da_empresa():
    assert storage.photo_key(COMPANY, OBJ) == KEY
    assert storage.photo_key(COMPANY, OBJ, mini=True) == f"{COMPANY}/fotos/{OBJ}-mini.jpg"


@pytest.mark.parametrize(
    "key",
    [
        f"{COMPANY}/fotos/../{OBJ}.jpg",
        f"../{COMPANY}/fotos/{OBJ}.jpg",
        f"/{COMPANY}/fotos/{OBJ}.jpg",
        f"{COMPANY}/fotos/{OBJ}.svg",
        f"{COMPANY}/outra/{OBJ}.jpg",
        f"{COMPANY}/fotos/{OBJ}.jpg?x=1",
        "foto.jpg",
        "",
    ],
)
def test_chave_fora_do_formato_recusada(key, tmp_path):
    with pytest.raises(storage.StorageError):
        storage.check_key(key)
    with pytest.raises(storage.StorageError):
        LocalStorage(tmp_path).put(key, b"x", "image/jpeg")


# ---------------------------------------------------------------- disco local


def test_local_grava_le_apaga_idempotente_e_sem_permissao_para_outros(tmp_path):
    store = LocalStorage(tmp_path / "uploads")
    store.put(KEY, b"conteudo", "image/jpeg")
    path = tmp_path / "uploads" / KEY
    assert path.read_bytes() == b"conteudo"
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    assert store.get(KEY) == b"conteudo"
    store.delete(KEY)
    store.delete(KEY)  # idempotente
    with pytest.raises(storage.ObjectNotFound):
        store.get(KEY)


def test_pasta_local_padrao_fica_em_instance_fora_de_static(app_factory):
    app = app_factory({"STORAGE_LOCAL_DIR": None})
    with app.app_context():
        store = storage.build(app)
    assert isinstance(store, LocalStorage)
    assert str(store.root).startswith(os.path.realpath(app.instance_path))
    assert "static" not in store.root.parts


# ---------------------------------------------------------------- SigV4


def test_assinatura_sigv4_bate_com_o_vetor_da_documentacao_da_aws():
    """Exemplo “GET Object” da documentação do S3 (Signature Version 4, header-based auth)."""
    headers = sign_v4(
        "GET",
        "https://examplebucket.s3.amazonaws.com/test.txt",
        {"Range": "bytes=0-9"},
        EMPTY_SHA256,
        access_key="AKIAIOSFODNN7EXAMPLE",
        secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        region="us-east-1",
        now=datetime(2013, 5, 24, tzinfo=timezone.utc),
    )
    assert headers["Authorization"] == (
        "AWS4-HMAC-SHA256 Credential=AKIAIOSFODNN7EXAMPLE/20130524/us-east-1/s3/aws4_request, "
        "SignedHeaders=host;range;x-amz-content-sha256;x-amz-date, "
        "Signature=f0e8bdb87c964420e857bd35b5d6ed310bd44f0170aba48dd91039c6036bdb41"
    )


class _Resp:
    def __init__(self, status: int, content: bytes = b""):
        self.status_code = status
        self.content = content


class _FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, data=None, headers=None, timeout=None, allow_redirects=True):
        self.calls.append({"method": method, "url": url, "data": data, "headers": headers, "timeout": timeout,
                           "allow_redirects": allow_redirects})
        return self.responses.pop(0)


def _s3(responses, **kw):
    session = _FakeSession(responses)
    store = S3Storage(
        endpoint=kw.pop("endpoint", "https://conta.r2.cloudflarestorage.com"),
        bucket="fotos-prod",
        region="auto",
        access_key="AKIATESTE",
        secret_key="segredo-que-nao-pode-vazar",
        session=session,
        **kw,
    )
    return store, session


def test_s3_put_get_delete_path_style_assinados(caplog):
    store, session = _s3([_Resp(200), _Resp(200, b"jpeg"), _Resp(204), _Resp(404)])
    store.put(KEY, b"jpeg", "image/jpeg")
    assert store.get(KEY) == b"jpeg"
    store.delete(KEY)
    store.delete(KEY)  # 404 ao apagar = já apagado
    put, get, delete, _ = session.calls
    assert put["method"] == "PUT" and put["url"] == f"https://conta.r2.cloudflarestorage.com/fotos-prod/{KEY}"
    assert put["headers"]["x-amz-content-sha256"] == hashlib.sha256(b"jpeg").hexdigest()
    assert put["headers"]["Content-Type"] == "image/jpeg"
    assert put["headers"]["Authorization"].startswith("AWS4-HMAC-SHA256 Credential=AKIATESTE/")
    assert "/auto/s3/aws4_request" in put["headers"]["Authorization"]
    assert get["headers"]["x-amz-content-sha256"] == EMPTY_SHA256
    assert delete["method"] == "DELETE"
    assert all(c["allow_redirects"] is False and c["timeout"] for c in session.calls)
    for c in session.calls:
        assert "segredo-que-nao-pode-vazar" not in str(c["headers"])
    assert "segredo" not in repr(store)
    assert "segredo-que-nao-pode-vazar" not in caplog.text


def test_s3_virtual_host():
    store, session = _s3([_Resp(200)], endpoint="https://s3.sa-east-1.amazonaws.com", addressing="virtual")
    store.put(KEY, b"x", "image/jpeg")
    assert session.calls[0]["url"] == f"https://fotos-prod.s3.sa-east-1.amazonaws.com/{KEY}"


def test_s3_erros_viram_storage_error_sem_segredo():
    store, _ = _s3([_Resp(403), _Resp(404), _Resp(500), _Resp(500)])
    with pytest.raises(storage.StorageError) as exc:
        store.put(KEY, b"x", "image/jpeg")
    assert "segredo" not in str(exc.value)
    with pytest.raises(storage.ObjectNotFound):
        store.get(KEY)
    with pytest.raises(storage.StorageError):
        store.get(KEY)
    with pytest.raises(storage.StorageError):
        store.delete(KEY)


def test_s3_falha_de_rede_vira_storage_error():
    class Boom:
        def request(self, *a, **k):
            raise ConnectionError("https://conta/...?X-Amz-Signature=abc")

    store = S3Storage(endpoint="https://x.example", bucket="b-1", region="auto", access_key="k", secret_key="s",
                      session=Boom())
    with pytest.raises(storage.StorageError) as exc:
        store.get(KEY)
    assert "Signature" not in str(exc.value)


def test_s3_exige_https_e_bucket_valido():
    with pytest.raises(storage.StorageError):
        S3Storage(endpoint="http://r2.example", bucket="ok-bucket", region="auto", access_key="k", secret_key="s",
                  session=object())
    with pytest.raises(storage.StorageError):
        S3Storage(endpoint="https://r2.example", bucket="../x", region="auto", access_key="k", secret_key="s",
                  session=object())


# ---------------------------------------------------------------- configuração por ambiente

PROD = {
    "SECRET_KEY": "x" * 40,
    "SQLALCHEMY_DATABASE_URI": "sqlite://",
    "APP_BASE_URL": "https://app.exemplo.com.br",
    "RATELIMIT_STORAGE_URI": "redis://localhost:6379/0",
}


def test_producao_sem_storage_sobe_com_fotos_desligadas():
    app = create_app("production", dict(PROD))
    with app.app_context():
        assert storage.build(app).enabled is False
    assert app.config["STORAGE_BACKEND"] == "none"


def test_producao_recusa_disco_local():
    with pytest.raises(RuntimeError, match="development/test"):
        create_app("production", {**PROD, "STORAGE_BACKEND": "local"})


def test_producao_s3_exige_todas_as_variaveis_e_https():
    with pytest.raises(RuntimeError, match="STORAGE_S3_BUCKET"):
        create_app("production", {**PROD, "STORAGE_BACKEND": "s3", "STORAGE_S3_ENDPOINT": "https://r2.example"})
    full = {
        **PROD,
        "STORAGE_BACKEND": "s3",
        "STORAGE_S3_ENDPOINT": "https://conta.r2.cloudflarestorage.com",
        "STORAGE_S3_BUCKET": "fotos",
        "STORAGE_S3_ACCESS_KEY_ID": "k",
        "STORAGE_S3_SECRET_ACCESS_KEY": "s",
    }
    app = create_app("production", full)
    with app.app_context():
        assert isinstance(storage.build(app), S3Storage)
    with pytest.raises(RuntimeError, match="https"):
        create_app("production", {**full, "STORAGE_S3_ENDPOINT": "http://conta.r2.cloudflarestorage.com"})


def test_backend_desconhecido_recusado():
    with pytest.raises(RuntimeError, match="STORAGE_BACKEND"):
        create_app("test", {"STORAGE_BACKEND": "ftp"})


def test_segredos_vem_do_ambiente(monkeypatch):
    monkeypatch.setenv("STORAGE_S3_SECRET_ACCESS_KEY", "do-ambiente")
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    app = create_app("test")
    assert app.config["STORAGE_S3_SECRET_ACCESS_KEY"] == "do-ambiente"
