"""Etapa G — armazenamento de arquivos (fotos de evidência) atrás de uma interface.

Backends:
- ``local``: disco, em ``STORAGE_LOCAL_DIR`` (padrão ``instance/uploads`` — FORA de ``static``,
  nunca servido direto). Só development/test: ``config.finalize_config`` recusa em produção.
- ``s3``: S3 compatível (Cloudflare R2, AWS S3, MinIO). Assinatura AWS SigV4 feita aqui com
  ``requests`` (já é dependência), sem ``boto3`` — ADR-0011: três operações (PUT/GET/DELETE de um
  objeto) não justificam ~15 MB de boto3/botocore; a assinatura é conferida com o vetor de teste
  publicado pela AWS (``tests/test_etapa_g_storage.py``).
- ``none``: fotos desligadas (produção sem ``STORAGE_*``): a tela avisa e o upload é recusado.

Regras que valem para todos:
- A CHAVE do objeto é gerada pelo servidor (``photo_key``): ``<company_id>/fotos/<uuid>.jpg`` —
  prefixo da empresa, uuid novo, nunca o nome enviado. ``check_key`` recusa qualquer outra forma
  (sem ``..``, sem barra extra), então nem um bug de chamada consegue sair da pasta/bucket.
- O bucket é PRIVADO: o app nunca gera URL pública nem pré-assinada; tudo passa pela rota
  autenticada ``/app/fotos/<uuid>`` (empresa conferida, 404 cruzado).
- Segredos (``STORAGE_S3_ACCESS_KEY_ID``/``STORAGE_S3_SECRET_ACCESS_KEY``) só por variável de
  ambiente; nunca entram em log nem em mensagem de erro.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit

from flask import Flask, current_app

log = logging.getLogger(__name__)

BACKENDS = ("local", "s3", "none")
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
# ADR-0019: ``briefing/`` guarda o logo e as fotos de produto do briefing de identidade visual.
KEY_RE = re.compile(rf"^{_UUID}/(?:fotos|briefing)/{_UUID}(?:-mini)?\.jpg$")


class StorageError(Exception):
    """Falha do armazenamento (rede, permissão, configuração). Mensagem sem segredo."""


class ObjectNotFound(StorageError):
    """O objeto não existe (já apagado ou nunca gravado)."""


class StorageDisabled(StorageError):
    """Nenhum backend configurado (``STORAGE_BACKEND=none``)."""


def photo_key(company_id: uuid.UUID, object_id: uuid.UUID, *, mini: bool = False) -> str:
    """Chave do objeto: prefixo da empresa + uuid gerado aqui (nunca o nome do arquivo enviado)."""
    key = f"{uuid.UUID(str(company_id))}/fotos/{uuid.UUID(str(object_id))}{'-mini' if mini else ''}.jpg"
    return check_key(key)


def briefing_key(company_id: uuid.UUID, object_id: uuid.UUID, *, mini: bool = False) -> str:
    """ADR-0019: chave de um arquivo do briefing (logo/foto de produto), na pasta da empresa."""
    key = f"{uuid.UUID(str(company_id))}/briefing/{uuid.UUID(str(object_id))}{'-mini' if mini else ''}.jpg"
    return check_key(key)


def check_key(key: str) -> str:
    if not isinstance(key, str) or not KEY_RE.fullmatch(key):
        raise StorageError("Chave de objeto inválida.")
    return key


class Storage:
    """Interface: gravar, ler e apagar um objeto por chave."""

    name = "abstract"
    enabled = True

    def put(self, key: str, data: bytes, content_type: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def get(self, key: str) -> bytes:  # pragma: no cover - interface
        raise NotImplementedError

    def delete(self, key: str) -> None:  # pragma: no cover - interface
        """Idempotente: apagar o que não existe não é erro."""
        raise NotImplementedError


class DisabledStorage(Storage):
    name = "none"
    enabled = False

    def put(self, key, data, content_type):
        raise StorageDisabled("Armazenamento de fotos não configurado.")

    def get(self, key):
        raise StorageDisabled("Armazenamento de fotos não configurado.")

    def delete(self, key):
        raise StorageDisabled("Armazenamento de fotos não configurado.")


class LocalStorage(Storage):
    """Disco local (development/test). Arquivos com permissão 0600, pastas 0700."""

    name = "local"

    def __init__(self, root: str | os.PathLike):
        self.root = Path(root).resolve()

    def _path(self, key: str) -> Path:
        path = (self.root / check_key(key)).resolve()
        if self.root not in path.parents:  # defesa em profundidade (check_key já impede)
            raise StorageError("Chave de objeto inválida.")
        return path

    def put(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            os.chmod(tmp, 0o600)
            os.replace(tmp, path)
        except Exception:
            Path(tmp).unlink(missing_ok=True)
            raise

    def get(self, key: str) -> bytes:
        try:
            return self._path(key).read_bytes()
        except FileNotFoundError:
            raise ObjectNotFound("Objeto não encontrado.") from None

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


# ---------------------------------------------------------------- S3 compatível (SigV4)


def _hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def signing_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    k_date = _hmac(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = _hmac(k_date, region)
    k_service = _hmac(k_region, service)
    return _hmac(k_service, "aws4_request")


def sign_v4(
    method: str,
    url: str,
    headers: dict[str, str],
    payload_sha256: str,
    *,
    access_key: str,
    secret_key: str,
    region: str,
    service: str = "s3",
    now: datetime | None = None,
) -> dict[str, str]:
    """Cabeçalhos assinados (AWS Signature Version 4) para uma requisição sem query string.

    Devolve os cabeçalhos de entrada + ``Host``, ``x-amz-date``, ``x-amz-content-sha256`` e
    ``Authorization``. ``now`` só para o teste com o vetor da documentação da AWS."""
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    parts = urlsplit(url)
    if parts.query:
        raise StorageError("Requisição assinada não aceita query string.")
    host = parts.netloc
    canonical_uri = quote(parts.path or "/", safe="/-_.~")
    all_headers = {k.lower(): " ".join(str(v).split()) for k, v in headers.items()}
    all_headers["host"] = host
    all_headers["x-amz-date"] = amz_date
    all_headers["x-amz-content-sha256"] = payload_sha256
    names = sorted(all_headers)
    canonical_headers = "".join(f"{n}:{all_headers[n]}\n" for n in names)
    signed_headers = ";".join(names)
    canonical_request = "\n".join([method.upper(), canonical_uri, "", canonical_headers, signed_headers, payload_sha256])
    scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join(
        ["AWS4-HMAC-SHA256", amz_date, scope, hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()]
    )
    signature = hmac.new(
        signing_key(secret_key, date_stamp, region, service), string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    out = dict(headers)
    out["Host"] = host
    out["x-amz-date"] = amz_date
    out["x-amz-content-sha256"] = payload_sha256
    out["Authorization"] = (
        f"AWS4-HMAC-SHA256 Credential={access_key}/{scope}, SignedHeaders={signed_headers}, Signature={signature}"
    )
    return out


class S3Storage(Storage):
    """Bucket S3 compatível. ``addressing="path"`` (padrão; R2 e MinIO) monta
    ``<endpoint>/<bucket>/<chave>``; ``"virtual"`` monta ``<bucket>.<host>/<chave>`` (AWS)."""

    name = "s3"

    def __init__(
        self,
        *,
        endpoint: str,
        bucket: str,
        region: str,
        access_key: str,
        secret_key: str,
        timeout: float = 10,
        addressing: str = "path",
        session=None,
    ):
        parts = urlsplit(endpoint)
        if parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname in {"localhost", "127.0.0.1"}):
            raise StorageError("STORAGE_S3_ENDPOINT precisa ser https://.")
        if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket or ""):
            raise StorageError("STORAGE_S3_BUCKET inválido.")
        if addressing not in {"path", "virtual"}:
            raise StorageError("STORAGE_S3_ADDRESSING deve ser path ou virtual.")
        self.scheme = parts.scheme
        self.host = parts.netloc
        self.bucket = bucket
        self.region = region or "auto"
        self._access_key = access_key
        self._secret_key = secret_key
        self.timeout = timeout
        self.addressing = addressing
        if session is None:
            import requests

            session = requests.Session()
        self._session = session

    def __repr__(self) -> str:  # nunca mostra as chaves
        return f"<S3Storage {self.scheme}://{self.host} bucket={self.bucket} region={self.region}>"

    def _url(self, key: str) -> str:
        key = check_key(key)
        if self.addressing == "virtual":
            return f"{self.scheme}://{self.bucket}.{self.host}/{key}"
        return f"{self.scheme}://{self.host}/{self.bucket}/{key}"

    def _request(self, method: str, key: str, data: bytes = b"", headers: dict | None = None):
        url = self._url(key)
        payload_hash = hashlib.sha256(data).hexdigest() if data else EMPTY_SHA256
        signed = sign_v4(
            method, url, headers or {}, payload_hash,
            access_key=self._access_key, secret_key=self._secret_key, region=self.region,
        )
        try:
            return self._session.request(
                method, url, data=data or None, headers=signed, timeout=self.timeout, allow_redirects=False
            )
        except Exception as exc:  # noqa: BLE001 - rede: só o nome da exceção (sem URL assinada)
            log.warning("storage.s3_request_failed", extra={"method": method, "error": type(exc).__name__})
            raise StorageError("Falha ao falar com o armazenamento de fotos.") from None

    def put(self, key: str, data: bytes, content_type: str) -> None:
        response = self._request(
            "PUT", key, data, {"Content-Type": content_type, "Content-Length": str(len(data))}
        )
        if response.status_code not in (200, 201):
            log.warning("storage.s3_put_status", extra={"status": response.status_code})
            raise StorageError("O armazenamento recusou a foto.")

    def get(self, key: str) -> bytes:
        response = self._request("GET", key)
        if response.status_code == 404:
            raise ObjectNotFound("Objeto não encontrado.")
        if response.status_code != 200:
            log.warning("storage.s3_get_status", extra={"status": response.status_code})
            raise StorageError("Falha ao ler a foto.")
        return response.content

    def delete(self, key: str) -> None:
        response = self._request("DELETE", key)
        if response.status_code not in (200, 204, 404):
            log.warning("storage.s3_delete_status", extra={"status": response.status_code})
            raise StorageError("Falha ao apagar a foto.")


# ---------------------------------------------------------------- configuração


def resolve_backend(app_config: dict, env_name: str) -> str:
    """``STORAGE_BACKEND`` explícito, ou automático: local em development/test, senão none."""
    backend = str(app_config.get("STORAGE_BACKEND") or "").strip().lower()
    if not backend:
        backend = "local" if env_name in {"development", "test"} else "none"
    if backend not in BACKENDS:
        raise RuntimeError(f"STORAGE_BACKEND desconhecido: {backend!r} (use local, s3 ou none).")
    return backend


def validate_config(app_config: dict, env_name: str) -> None:
    """Chamado por ``config.finalize_config``: disco local nunca em produção; S3 completo."""
    backend = resolve_backend(app_config, env_name)
    if backend == "local" and env_name not in {"development", "test"}:
        raise RuntimeError("STORAGE_BACKEND=local é só para development/test; em produção use s3 (R2/S3).")
    if backend == "s3":
        missing = [
            k for k in ("STORAGE_S3_ENDPOINT", "STORAGE_S3_BUCKET", "STORAGE_S3_ACCESS_KEY_ID", "STORAGE_S3_SECRET_ACCESS_KEY")
            if not app_config.get(k)
        ]
        if missing:
            raise RuntimeError("STORAGE_BACKEND=s3 exige " + ", ".join(missing) + ".")
        if not str(app_config["STORAGE_S3_ENDPOINT"]).startswith("https://") and env_name not in {"development", "test"}:
            raise RuntimeError("STORAGE_S3_ENDPOINT precisa ser https:// fora de development/test.")
    app_config["STORAGE_BACKEND"] = backend


def build(app: Flask) -> Storage:
    config = app.config
    backend = resolve_backend(config, config.get("ENV_NAME", "production"))
    if backend == "local":
        root = config.get("STORAGE_LOCAL_DIR") or os.path.join(app.instance_path, "uploads")
        return LocalStorage(root)
    if backend == "s3":
        return S3Storage(
            endpoint=config["STORAGE_S3_ENDPOINT"],
            bucket=config["STORAGE_S3_BUCKET"],
            region=config.get("STORAGE_S3_REGION") or "auto",
            access_key=config["STORAGE_S3_ACCESS_KEY_ID"],
            secret_key=config["STORAGE_S3_SECRET_ACCESS_KEY"],
            timeout=float(config.get("STORAGE_TIMEOUT_SECONDS") or 10),
            addressing=config.get("STORAGE_S3_ADDRESSING") or "path",
        )
    return DisabledStorage()


def get_storage() -> Storage:
    """Backend do app atual (criado uma vez por app; testes trocam por ``set_storage``)."""
    ext = current_app.extensions
    if "storage" not in ext:
        ext["storage"] = build(current_app)
    return ext["storage"]


def set_storage(app: Flask, storage: Storage) -> None:
    app.extensions["storage"] = storage
