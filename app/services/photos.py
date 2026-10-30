"""Etapa G — fotos de evidência por atividade.

Validação (tudo no servidor; o ``accept`` do navegador é só ajuda):
1. Tamanho ≤ ``PHOTO_MAX_BYTES`` (5 MB) — além do teto do corpo da requisição (413).
2. Tipo pelo CONTEÚDO (magic bytes), nunca pela extensão nem pelo Content-Type enviados:
   só JPEG, PNG e WebP. SVG, GIF, HTML, PDF etc. são recusados.
3. Dimensões lidas do cabeçalho ANTES de decodificar: largura × altura ≤ ``PHOTO_MAX_PIXELS``
   (bomba de descompressão). O aviso ``DecompressionBombWarning`` do Pillow também vira erro.
4. Decodificação completa com Pillow (arquivo truncado/corrompido/polyglot que não é imagem
   de verdade → recusado) e o formato decodificado tem de ser o mesmo dos magic bytes.
5. REENCODE: a imagem guardada é um JPEG novo gerado aqui (orientação aplicada, reduzida a
   ``PHOTO_MAX_SIDE``, sem EXIF/GPS/ICC/XMP nem bytes extras do arquivo original) + miniatura.
   Por isso o tipo servido é sempre ``image/jpeg``.

Chaves: ``storage.photo_key`` (prefixo ``company_id``, uuid gerado). Ordem de gravação: objeto
primeiro, linha depois (falha na linha → objeto apagado). Ao apagar: objetos primeiro, linha
depois (nunca sobra arquivo de foto “apagada”). Expurgo LGPD: ``delete_company_objects`` apaga
os objetos ANTES das linhas; se o armazenamento falhar, o expurgo para e tenta de novo depois.
"""

from __future__ import annotations

import hashlib
import io
import logging
import uuid
import warnings
from dataclasses import dataclass

from flask import current_app
from sqlalchemy import func, select

from app.extensions import db
from app.models import Activity
from app.models.quality import PHOTO_CAPTION_MAX, ActivityPhoto
from app.services import audit
from app.services import storage as storage_mod

log = logging.getLogger(__name__)

JPEG_QUALITY = 85
THUMB_QUALITY = 80
CONTENT_TYPE = "image/jpeg"
FORMATS = {"jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}


class PhotoError(Exception):
    """Foto recusada (mensagem pronta para a tela)."""


@dataclass(frozen=True)
class ProcessedPhoto:
    data: bytes
    thumb: bytes
    width: int
    height: int
    sha256: str


def _cfg(key: str, default: int) -> int:
    return int(current_app.config.get(key, default))


def sniff(data: bytes) -> str | None:
    """Formato pelos magic bytes (assinatura no início do arquivo)."""
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _flatten(img):
    """RGB sem transparência (fundo branco) numa imagem NOVA — sem herdar ``info`` (EXIF/ICC)."""
    from PIL import Image

    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        clean = Image.new("RGB", rgba.size, (255, 255, 255))
        clean.paste(rgba, mask=rgba.getchannel("A"))
        return clean
    rgb = img.convert("RGB")
    clean = Image.new("RGB", rgb.size)
    clean.paste(rgb)
    return clean


def _encode(img, quality: int) -> bytes:
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=quality, optimize=True, progressive=True)
    return out.getvalue()


def process(data: bytes) -> ProcessedPhoto:
    """Valida e reencoda. Levanta ``PhotoError`` com a mensagem para a tela."""
    from PIL import Image, ImageOps, UnidentifiedImageError

    max_bytes = _cfg("PHOTO_MAX_BYTES", 5 * 1024 * 1024)
    if not data:
        raise PhotoError("Escolha uma foto.")
    if len(data) > max_bytes:
        raise PhotoError(f"Foto maior que {max_bytes // (1024 * 1024)} MB.")
    kind = sniff(data)
    if kind is None:
        raise PhotoError("Envie uma foto JPEG, PNG ou WebP.")
    max_pixels = _cfg("PHOTO_MAX_PIXELS", 40_000_000)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            img = Image.open(io.BytesIO(data), formats=[FORMATS[kind]])
            if (img.format or "").upper() != FORMATS[kind]:
                raise PhotoError("Envie uma foto JPEG, PNG ou WebP.")
            width, height = img.size
            if width < 1 or height < 1 or width * height > max_pixels:
                raise PhotoError("Foto com dimensões grandes demais.")
            img.seek(0)  # animação (APNG/WebP animado): só o primeiro quadro
            img.load()
            img = ImageOps.exif_transpose(img)
            clean = _flatten(img)
    except PhotoError:
        raise
    except (Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise PhotoError("Foto com dimensões grandes demais.") from None
    except (UnidentifiedImageError, Exception):  # noqa: BLE001 - qualquer falha do decodificador = recusa
        raise PhotoError("Não foi possível ler a foto. Envie um JPEG, PNG ou WebP válido.") from None
    side = _cfg("PHOTO_MAX_SIDE", 2560)
    clean.thumbnail((side, side), Image.Resampling.LANCZOS)
    main = _encode(clean, JPEG_QUALITY)
    thumb_side = _cfg("PHOTO_THUMB_SIDE", 480)
    mini = clean.copy()
    mini.thumbnail((thumb_side, thumb_side), Image.Resampling.LANCZOS)
    return ProcessedPhoto(
        data=main,
        thumb=_encode(mini, THUMB_QUALITY),
        width=clean.width,
        height=clean.height,
        sha256=hashlib.sha256(main).hexdigest(),
    )


# ---------------------------------------------------------------- casos de uso


def enabled() -> bool:
    return storage_mod.get_storage().enabled


def list_for(activity: Activity) -> list[ActivityPhoto]:
    return list(
        db.session.execute(
            select(ActivityPhoto)
            .where(ActivityPhoto.company_id == activity.company_id, ActivityPhoto.activity_id == activity.id)
            .order_by(ActivityPhoto.created_at.desc(), ActivityPhoto.id)
        ).scalars()
    )


def counts_by_activity(company_id: uuid.UUID, activity_ids) -> dict[uuid.UUID, int]:
    ids = list(activity_ids)
    if not ids:
        return {}
    rows = db.session.execute(
        select(ActivityPhoto.activity_id, func.count())
        .where(ActivityPhoto.company_id == company_id, ActivityPhoto.activity_id.in_(ids))
        .group_by(ActivityPhoto.activity_id)
    ).all()
    return {aid: n for aid, n in rows}


def _count(*conditions) -> int:
    return db.session.execute(select(func.count()).select_from(ActivityPhoto).where(*conditions)).scalar_one()


def add_photo(activity: Activity, data: bytes, user_id: uuid.UUID | None, caption: str | None = None) -> ActivityPhoto:
    """Valida, reencoda, grava os objetos e a linha (flush, sem commit).

    Limites no backend: ``PHOTOS_MAX_PER_ACTIVITY`` e ``PHOTOS_MAX_PER_COMPANY``. Se algo falhar
    depois de gravar o objeto, o objeto é apagado (sem órfão). Quem chama faz o commit e, se o
    commit falhar, chama ``discard_objects``."""
    store = storage_mod.get_storage()
    if not store.enabled:
        raise PhotoError("Fotos não estão disponíveis neste ambiente.")
    caption = (caption or "").strip() or None
    if caption is not None and len(caption) > PHOTO_CAPTION_MAX:
        raise PhotoError(f"A legenda tem no máximo {PHOTO_CAPTION_MAX} caracteres.")
    per_activity = _cfg("PHOTOS_MAX_PER_ACTIVITY", 20)
    if _count(ActivityPhoto.company_id == activity.company_id, ActivityPhoto.activity_id == activity.id) >= per_activity:
        raise PhotoError(f"Esta subatividade já tem {per_activity} fotos (o máximo). Apague uma para enviar outra.")
    per_company = _cfg("PHOTOS_MAX_PER_COMPANY", 5000)
    if _count(ActivityPhoto.company_id == activity.company_id) >= per_company:
        raise PhotoError("A empresa atingiu o limite de fotos guardadas. Apague fotos antigas ou fale com o suporte.")
    processed = process(data)
    photo_id = uuid.uuid4()
    photo = ActivityPhoto(
        id=photo_id,
        company_id=activity.company_id,
        activity_id=activity.id,
        object_key=storage_mod.photo_key(activity.company_id, photo_id),
        thumb_key=storage_mod.photo_key(activity.company_id, photo_id, mini=True),
        content_type=CONTENT_TYPE,
        size_bytes=len(processed.data),
        width=processed.width,
        height=processed.height,
        sha256=processed.sha256,
        caption=caption,
        uploaded_by_id=user_id,
    )
    try:
        store.put(photo.object_key, processed.data, CONTENT_TYPE)
        store.put(photo.thumb_key, processed.thumb, CONTENT_TYPE)
        db.session.add(photo)
        db.session.flush()
    except Exception:
        discard_objects(photo)
        raise
    return photo


def discard_objects(photo: ActivityPhoto) -> None:
    """Apaga os objetos de uma foto cuja linha não foi gravada (melhor esforço; loga falha)."""
    store = storage_mod.get_storage()
    for key in (photo.object_key, photo.thumb_key):
        try:
            store.delete(key)
        except storage_mod.StorageError:
            log.warning("photos.orphan_object", extra={"photo_id": str(photo.id)})


def read(photo: ActivityPhoto, *, mini: bool = False) -> bytes:
    """Bytes da foto (ou da miniatura). Integridade da foto grande conferida pelo SHA-256."""
    store = storage_mod.get_storage()
    data = store.get(photo.thumb_key if mini else photo.object_key)
    if not mini and hashlib.sha256(data).hexdigest() != photo.sha256:
        log.warning("photos.integrity_mismatch", extra={"photo_id": str(photo.id)})
        raise storage_mod.ObjectNotFound("Foto corrompida.")
    return data


def delete_photo(photo: ActivityPhoto, user_id: uuid.UUID | None) -> None:
    """Supervisor+ (na rota). Objetos primeiro (falha → nada muda), depois linha + auditoria
    (sem a imagem; só ids e tamanho). Sem commit."""
    store = storage_mod.get_storage()
    store.delete(photo.object_key)
    store.delete(photo.thumb_key)
    activity = photo.activity
    audit.record(
        audit.PHOTO_DELETED,
        company_id=photo.company_id,
        actor_user_id=user_id,
        object_type="project",
        object_id=activity.stage.project_id,
        details={
            "photo_id": str(photo.id),
            "activity_id": str(activity.id),
            "activity": activity.name,
            "uploaded_by_id": str(photo.uploaded_by_id) if photo.uploaded_by_id else None,
            "size_bytes": photo.size_bytes,
        },
    )
    db.session.delete(photo)
    db.session.flush()


def delete_company_objects(company_id: uuid.UUID, *, dry_run: bool = False) -> int:
    """Expurgo LGPD: apaga do armazenamento TODOS os objetos das fotos da empresa (chaves lidas
    das linhas, que ainda existem). Devolve quantos objetos. Falha do armazenamento propaga
    (o expurgo é desfeito e roda de novo no próximo ciclo; apagar é idempotente)."""
    rows = db.session.execute(
        select(ActivityPhoto.object_key, ActivityPhoto.thumb_key).where(ActivityPhoto.company_id == company_id)
    ).all()
    keys = [k for row in rows for k in row]
    if dry_run or not keys:
        return len(keys)
    store = storage_mod.get_storage()
    if not store.enabled:
        raise storage_mod.StorageDisabled("Há fotos da empresa, mas o armazenamento não está configurado.")
    for key in keys:
        store.delete(key)
    return len(keys)
