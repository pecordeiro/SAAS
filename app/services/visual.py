"""ADR-0019 §2 — briefing de identidade visual (dado da empresa).

Regras (todas aqui, no servidor; a tela só mostra o que este módulo decide — ADR-0009):
- Só empresa com a feature ``visual_custom`` no plano em vigor (``available``); a rota responde 404
  sem ela. Só o proprietário preenche (papel conferido na rota).
- Estados (na requisição da plataforma, ``visual_requests``): nova → briefing preenchido →
  em andamento → entregue. Salvar o briefing COMPLETO numa requisição ``new`` passa para
  ``briefing_filled`` (a rota avisa a equipe por e-mail). Edição liberada só em ``new`` e
  ``briefing_filled``; depois, só se a equipe reabrir (voltar o estado no painel).
- Sites de referência: até ``SITES_MAX`` endereços http/https, cada um com até ``SITE_MAX_CHARS``.
- Imagens: logo (1) e fotos de produto (``BRIEFING_PHOTOS_MAX``), validadas pela extensão do nome
  E pelo conteúdo (``photos.process``: magic bytes, dimensões, decodificação completa e reencode
  em JPEG sem metadados). Armazenamento privado (``storage.briefing_key``).
- Auditoria (``audit_logs``) sem o texto do briefing: só quais campos estão preenchidos.
"""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from dataclasses import dataclass
from urllib.parse import urlsplit

from flask import current_app
from sqlalchemy import func, select

from app.extensions import db
from app.models import (
    VISUAL_BRIEFING_FILLED,
    VISUAL_DELIVERED,
    VISUAL_NEW,
    Company,
    PlatformAuditLog,
    VisualRequest,
)
from app.models.base import utcnow
from app.models.visual import (
    EMAIL_MAX,
    FILE_KINDS,
    FILE_LOGO,
    FILE_PRODUCT,
    NAME_MAX,
    PHONE_MAX,
    PREFS_MAX,
    PRODUCTS_MAX,
    SITES_MAX_CHARS,
    TONES,
    VisualBriefing,
    VisualBriefingFile,
)
from app.services import audit
from app.services import photos as photos_svc
from app.services import storage as storage_mod

log = logging.getLogger(__name__)

FEATURE = "visual_custom"
EDITABLE_STATUSES = (VISUAL_NEW, VISUAL_BRIEFING_FILLED)
SITES_MAX = 5
SITE_MAX_CHARS = 300
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
CONTENT_TYPE = "image/jpeg"
TONE_LABELS = {"formal": "Formal", "neutro": "Neutro", "descontraido": "Descontraído"}
PHONE_RE = re.compile(r"^[0-9+()\-. ]{8,30}$")
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]+$")
# Campos de texto do briefing (os nomes vão para a auditoria; o conteúdo, nunca).
TEXT_FIELDS = (
    "company_name", "products", "colors", "fonts", "reference_sites", "tone",
    "contact_name", "contact_phone", "contact_email",
)


class VisualError(Exception):
    """Ação recusada (mensagem pronta para a tela)."""


class LockedError(VisualError):
    """Briefing em andamento ou entregue: só a equipe reabre."""


# ---------------------------------------------------------------- acesso e requisição


def available(company: Company) -> bool:
    """A empresa tem a feature ``visual_custom`` no plano em vigor (checado no backend)."""
    from app.services import entitlements

    return entitlements.has_feature(company, FEATURE)


def current_request(company_id: uuid.UUID) -> VisualRequest | None:
    """Requisição em aberto (não entregue) mais recente; senão a última entregue; senão ``None``."""
    rows = list(
        db.session.execute(
            select(VisualRequest)
            .where(VisualRequest.company_id == company_id)
            .order_by(VisualRequest.created_at.desc(), VisualRequest.id)
        ).scalars()
    )
    for row in rows:
        if row.status != VISUAL_DELIVERED:
            return row
    return rows[0] if rows else None


def ensure_request(company: Company) -> VisualRequest:
    """Requisição em aberto da empresa; abre uma se não houver (ex.: plano dado por linha de
    comando sem o gancho da troca de plano). Sem commit."""
    from app.services import entitlements, staff

    current = current_request(company.id)
    if current is not None and current.status != VISUAL_DELIVERED:
        return current
    if current is not None:
        # Entregue: segue nela (somente leitura) até a equipe abrir outra.
        return current
    opened = staff.open_visual_request(company.id, entitlements.effective_plan(company).code)
    return opened if opened is not None else current_request(company.id)  # type: ignore[return-value]


def can_edit(request_: VisualRequest | None) -> bool:
    return request_ is None or request_.status in EDITABLE_STATUSES


def get_briefing(company_id: uuid.UUID) -> VisualBriefing | None:
    return db.session.execute(
        select(VisualBriefing).where(VisualBriefing.company_id == company_id)
    ).scalar_one_or_none()


def _ensure_briefing(company: Company, request_: VisualRequest | None) -> VisualBriefing:
    briefing = get_briefing(company.id)
    if briefing is None:
        briefing = VisualBriefing(company_id=company.id)
        db.session.add(briefing)
    if request_ is not None:
        briefing.visual_request_id = request_.id
    db.session.flush()
    return briefing


# ---------------------------------------------------------------- validação


@dataclass
class BriefingInput:
    company_name: str = ""
    products: str = ""
    colors: str = ""
    fonts: str = ""
    reference_sites: str = ""
    tone: str = ""
    contact_name: str = ""
    contact_phone: str = ""
    contact_email: str = ""


def _clean(value: str | None) -> str:
    return (value or "").strip()


def parse_sites(text: str | None) -> list[str]:
    """Um endereço por linha (vírgula ou espaço também separam). Só http/https com domínio, sem
    usuário/senha no endereço, até ``SITE_MAX_CHARS`` cada e ``SITES_MAX`` no total."""
    raw = _clean(text)
    if not raw:
        return []
    if len(raw) > SITES_MAX_CHARS:
        raise VisualError(f"Sites de referência: no máximo {SITES_MAX} endereços.")
    items = [p for p in re.split(r"[\s,]+", raw) if p]
    if len(items) > SITES_MAX:
        raise VisualError(f"Sites de referência: no máximo {SITES_MAX} endereços.")
    out: list[str] = []
    for item in items:
        if len(item) > SITE_MAX_CHARS:
            raise VisualError(f"Sites de referência: cada endereço com até {SITE_MAX_CHARS} caracteres.")
        parts = urlsplit(item)
        host = parts.hostname or ""
        if (
            parts.scheme.lower() not in ("http", "https")
            or not host
            or "." not in host
            or "@" in parts.netloc
            or any(ord(ch) < 33 for ch in item)
        ):
            raise VisualError("Sites de referência: use endereços completos, começando com http:// ou https://.")
        if item not in out:
            out.append(item)
    return out


def _limit(label: str, value: str, size: int) -> str:
    if len(value) > size:
        raise VisualError(f"{label}: no máximo {size} caracteres.")
    return value


def validate(data: BriefingInput) -> dict:
    """Normaliza e valida; devolve os valores para gravar (vazio vira ``None``)."""
    values = {
        "company_name": _limit("Nome da empresa", _clean(data.company_name), NAME_MAX),
        "products": _limit("Produtos", _clean(data.products), PRODUCTS_MAX),
        "colors": _limit("Cores de preferência", _clean(data.colors), PREFS_MAX),
        "fonts": _limit("Fontes de preferência", _clean(data.fonts), PREFS_MAX),
        "contact_name": _limit("Nome do contato", _clean(data.contact_name), NAME_MAX),
        "contact_phone": _limit("Telefone do contato", _clean(data.contact_phone), PHONE_MAX),
        "contact_email": _limit("E-mail do contato", _clean(data.contact_email), EMAIL_MAX).lower(),
    }
    tone = _clean(data.tone)
    if tone and tone not in TONES:
        raise VisualError("Tom de voz inválido.")
    values["tone"] = tone
    values["reference_sites"] = "\n".join(parse_sites(data.reference_sites))
    if values["contact_phone"] and not PHONE_RE.fullmatch(values["contact_phone"]):
        raise VisualError("Telefone do contato: use só números, espaço, parênteses, + ou -.")
    if values["contact_email"] and not EMAIL_RE.fullmatch(values["contact_email"]):
        raise VisualError("E-mail do contato inválido.")
    return {k: (v or None) for k, v in values.items()}


def missing_fields(briefing: VisualBriefing | None) -> list[str]:
    """O que falta para o briefing contar como completo (rótulos para a tela)."""
    if briefing is None:
        return ["Nome da empresa", "Produtos", "Nome do contato", "Telefone ou e-mail do contato"]
    out = []
    if not briefing.company_name:
        out.append("Nome da empresa")
    if not briefing.products:
        out.append("Produtos")
    if not briefing.contact_name:
        out.append("Nome do contato")
    if not (briefing.contact_phone or briefing.contact_email):
        out.append("Telefone ou e-mail do contato")
    return out


def is_complete(briefing: VisualBriefing | None) -> bool:
    return not missing_fields(briefing)


# ---------------------------------------------------------------- casos de uso


def save_briefing(company: Company, data: BriefingInput, user_id: uuid.UUID | None) -> tuple[VisualBriefing, bool]:
    """Grava o briefing (sem commit). Devolve ``(briefing, enviado_agora)``: ``True`` quando este
    salvamento completou o briefing e passou a requisição de ``new`` para ``briefing_filled``."""
    request_ = ensure_request(company)
    if not can_edit(request_):
        raise LockedError("A equipe já está trabalhando na sua identidade visual. Para mudar algo, fale com a equipe.")
    values = validate(data)
    briefing = _ensure_briefing(company, request_)
    for key, value in values.items():
        setattr(briefing, key, value)
    now = utcnow()
    briefing.updated_at, briefing.updated_by_id = now, user_id
    complete = is_complete(briefing)
    audit.record(
        audit.VISUAL_BRIEFING_SAVED,
        company_id=company.id,
        actor_user_id=user_id,
        object_type="visual_briefing",
        object_id=briefing.id,
        details={"completo": complete, "campos": [k for k in TEXT_FIELDS if getattr(briefing, k)]},
    )
    submitted = False
    if complete and request_ is not None and request_.status == VISUAL_NEW:
        request_.status, request_.updated_at = VISUAL_BRIEFING_FILLED, now
        briefing.submitted_at = now
        submitted = True
        audit.record(
            audit.VISUAL_BRIEFING_SUBMITTED,
            company_id=company.id,
            actor_user_id=user_id,
            object_type="visual_briefing",
            object_id=briefing.id,
        )
        from app.services import staff

        db.session.add(
            PlatformAuditLog(
                action=staff.VISUAL_STATUS_CHANGED,
                subject_company_id=company.id,
                operator="cliente",
                details={"request_id": str(request_.id), "de": VISUAL_NEW, "para": VISUAL_BRIEFING_FILLED},
            )
        )
    db.session.flush()
    return briefing, submitted


def _cfg(key: str, default: int) -> int:
    return int(current_app.config.get(key, default))


def max_files(kind: str) -> int:
    return 1 if kind == FILE_LOGO else _cfg("BRIEFING_PHOTOS_MAX", 10)


def list_files(company_id: uuid.UUID) -> list[VisualBriefingFile]:
    return list(
        db.session.execute(
            select(VisualBriefingFile)
            .where(VisualBriefingFile.company_id == company_id)
            .order_by(VisualBriefingFile.kind, VisualBriefingFile.created_at, VisualBriefingFile.id)
        ).scalars()
    )


def storage_enabled() -> bool:
    return storage_mod.get_storage().enabled


def check_filename(filename: str | None) -> None:
    name = (filename or "").strip().lower()
    if not name.endswith(IMAGE_EXTENSIONS):
        raise VisualError("Envie uma imagem .jpg, .jpeg, .png ou .webp.")


def add_file(company: Company, kind: str, filename: str | None, data: bytes, user_id: uuid.UUID | None) -> VisualBriefingFile:
    """Valida (extensão E conteúdo), reencoda, grava objetos e linha (flush, sem commit). Falha
    depois de gravar o objeto → objeto apagado. Quem chama faz o commit; se falhar, chama
    ``discard_objects``."""
    if kind not in FILE_KINDS:
        raise VisualError("Tipo de imagem inválido.")
    store = storage_mod.get_storage()
    if not store.enabled:
        raise VisualError("O envio de imagens não está disponível neste ambiente.")
    request_ = ensure_request(company)
    if not can_edit(request_):
        raise LockedError("A equipe já está trabalhando na sua identidade visual. Para mudar algo, fale com a equipe.")
    check_filename(filename)
    limit = max_files(kind)
    count = db.session.execute(
        select(func.count())
        .select_from(VisualBriefingFile)
        .where(VisualBriefingFile.company_id == company.id, VisualBriefingFile.kind == kind)
    ).scalar_one()
    if count >= limit:
        if kind == FILE_LOGO:
            raise VisualError("Já há um logo. Apague o atual para enviar outro.")
        raise VisualError(f"O limite é de {limit} fotos de produto. Apague uma para enviar outra.")
    try:
        processed = photos_svc.process(data)
    except photos_svc.PhotoError as exc:
        raise VisualError(str(exc).replace("foto", "imagem").replace("Foto", "Imagem")) from None
    briefing = _ensure_briefing(company, request_)
    file_id = uuid.uuid4()
    row = VisualBriefingFile(
        id=file_id,
        company_id=company.id,
        briefing_id=briefing.id,
        kind=kind,
        object_key=storage_mod.briefing_key(company.id, file_id),
        thumb_key=storage_mod.briefing_key(company.id, file_id, mini=True),
        content_type=CONTENT_TYPE,
        size_bytes=len(processed.data),
        width=processed.width,
        height=processed.height,
        sha256=processed.sha256,
        uploaded_by_id=user_id,
    )
    try:
        store.put(row.object_key, processed.data, CONTENT_TYPE)
        store.put(row.thumb_key, processed.thumb, CONTENT_TYPE)
        db.session.add(row)
        audit.record(
            audit.VISUAL_FILE_ADDED,
            company_id=company.id,
            actor_user_id=user_id,
            object_type="visual_briefing",
            object_id=briefing.id,
            details={"arquivo_id": str(file_id), "tipo": kind, "size_bytes": row.size_bytes},
        )
        db.session.flush()
    except Exception:
        discard_objects(row)
        raise
    return row


def discard_objects(row: VisualBriefingFile) -> None:
    store = storage_mod.get_storage()
    for key in (row.object_key, row.thumb_key):
        try:
            store.delete(key)
        except storage_mod.StorageError:
            log.warning("visual.orphan_object", extra={"file_id": str(row.id)})


def read_file(row: VisualBriefingFile, *, mini: bool = False) -> bytes:
    data = storage_mod.get_storage().get(row.thumb_key if mini else row.object_key)
    if not mini and hashlib.sha256(data).hexdigest() != row.sha256:
        log.warning("visual.integrity_mismatch", extra={"file_id": str(row.id)})
        raise storage_mod.ObjectNotFound("Imagem corrompida.")
    return data


def delete_file(company: Company, row: VisualBriefingFile, user_id: uuid.UUID | None) -> None:
    """Objetos primeiro (falha → nada muda), depois linha + auditoria. Sem commit."""
    if not can_edit(current_request(company.id)):
        raise LockedError("A equipe já está trabalhando na sua identidade visual. Para mudar algo, fale com a equipe.")
    store = storage_mod.get_storage()
    store.delete(row.object_key)
    store.delete(row.thumb_key)
    audit.record(
        audit.VISUAL_FILE_DELETED,
        company_id=company.id,
        actor_user_id=user_id,
        object_type="visual_briefing",
        object_id=row.briefing_id,
        details={"arquivo_id": str(row.id), "tipo": row.kind, "size_bytes": row.size_bytes},
    )
    db.session.delete(row)
    db.session.flush()


def delete_company_objects(company_id: uuid.UUID, *, dry_run: bool = False) -> int:
    """Expurgo LGPD: apaga do armazenamento os arquivos do briefing da empresa ANTES das linhas
    (as chaves estão nelas). Falha do armazenamento propaga (o expurgo é desfeito e repetido)."""
    rows = db.session.execute(
        select(VisualBriefingFile.object_key, VisualBriefingFile.thumb_key).where(
            VisualBriefingFile.company_id == company_id
        )
    ).all()
    keys = [k for row in rows for k in row]
    if dry_run or not keys:
        return len(keys)
    store = storage_mod.get_storage()
    if not store.enabled:
        raise storage_mod.StorageDisabled("Há imagens do briefing, mas o armazenamento não está configurado.")
    for key in keys:
        store.delete(key)
    return len(keys)

