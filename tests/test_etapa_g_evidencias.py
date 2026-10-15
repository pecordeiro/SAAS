"""Etapa G (bloco 1) — comentários e fotos por atividade.

Regras: só membros da empresa; operador+ comenta/envia; supervisor+ apaga com auditoria; foto
validada pelo CONTEÚDO (magic bytes + decodificação), reencodada sem EXIF/GPS, ≤ 5 MB, N por
atividade, chave gerada com prefixo da empresa, servida só pela rota autenticada com
Content-Type fixo, nosniff, Cache-Control private e CSP sandbox. Expurgo LGPD apaga os objetos.
"""

from __future__ import annotations

import io
import io as _io
import zipfile
from datetime import timedelta

import pytest
from PIL import Image
from sqlalchemy import func, select

from app.extensions import db
from app.models import AuditLog, Company
from app.models.base import utcnow
from app.models.quality import ActivityComment, ActivityPhoto
from app.services import audit, lgpd, photos, storage
from tests import fotos
from tests.conftest import csrf_token, login, post, text_of


def _upload(client, app, activity_id, data: bytes, filename: str = "foto.jpg", caption: str | None = None):
    payload = {"photo": (io.BytesIO(data), filename), "csrf_token": csrf_token(client, app)}
    if caption is not None:
        payload["caption"] = caption
    return client.post(f"/app/atividades/{activity_id}/fotos", data=payload, content_type="multipart/form-data")


def _photos(app, company_id=None) -> list[ActivityPhoto]:
    with app.app_context():
        q = select(ActivityPhoto)
        if company_id is not None:
            q = q.where(ActivityPhoto.company_id == company_id)
        rows = list(db.session.execute(q).scalars())
        db.session.expunge_all()
        return rows


def _stored(app, key: str) -> bytes:
    with app.app_context():
        return storage.get_storage().get(key)


def _exists(app, key: str) -> bool:
    try:
        _stored(app, key)
        return True
    except storage.ObjectNotFound:
        return False


# ---------------------------------------------------------------- comentários


def test_operador_comenta_e_todos_da_empresa_veem(app, client, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    url = f"/app/atividades/{a.activity_id}/comentarios"
    response = post(client, app, url, {"body": "  Parafuso M6 faltando na base <b>urgente</b>  "})
    assert response.status_code == 303
    page = client.get(f"/app/atividades/{a.activity_id}/evidencias")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "Parafuso M6 faltando na base &lt;b&gt;urgente&lt;/b&gt;" in html  # autoescape
    assert "operator A" in html
    with app.app_context():
        comment = db.session.execute(select(ActivityComment)).scalar_one()
        assert comment.body == "Parafuso M6 faltando na base <b>urgente</b>"
        assert comment.company_id == a.company_id and comment.author_id == a.operator_id


@pytest.mark.parametrize("body", ["", "   ", "x" * 1001])
def test_comentario_vazio_ou_longo_recusado(app, client, tenants, body):
    a, _ = tenants
    login(client, app, a.operator_email)
    response = post(client, app, f"/app/atividades/{a.activity_id}/comentarios", {"body": body})
    assert response.status_code == 400
    with app.app_context():
        assert db.session.execute(select(func.count()).select_from(ActivityComment)).scalar_one() == 0


def test_so_supervisor_apaga_comentario_e_fica_auditado_sem_texto(app, tenants):
    a, _ = tenants
    op = app.test_client()
    login(op, app, a.operator_email)
    post(op, app, f"/app/atividades/{a.activity_id}/comentarios", {"body": "Texto sigiloso do comentário"})
    with app.app_context():
        comment_id = db.session.execute(select(ActivityComment.id)).scalar_one()
    assert post(op, app, f"/app/comentarios/{comment_id}/apagar").status_code == 403
    page = op.get(f"/app/atividades/{a.activity_id}/evidencias").get_data(as_text=True)
    assert f"/app/comentarios/{comment_id}/apagar" not in page  # botão escondido E rota recusa
    sup = app.test_client()
    login(sup, app, a.supervisor_email)
    assert f"/app/comentarios/{comment_id}/apagar" in sup.get(f"/app/atividades/{a.activity_id}/evidencias").get_data(as_text=True)
    assert post(sup, app, f"/app/comentarios/{comment_id}/apagar").status_code == 303
    with app.app_context():
        assert db.session.get(ActivityComment, comment_id) is None
        log = db.session.execute(select(AuditLog).where(AuditLog.action == audit.COMMENT_DELETED)).scalar_one()
        assert log.company_id == a.company_id and log.details["chars"] == len("Texto sigiloso do comentário")
        assert "sigiloso" not in str(log.details)


# ---------------------------------------------------------------- fotos: caminho feliz


def test_foto_valida_e_reencodada_sem_exif_gps_e_servida_com_cabecalhos_fixos(app, client, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    original = fotos.jpeg(with_gps=True)
    assert fotos.GPS_MARK in original
    response = _upload(client, app, a.activity_id, original, filename="../../etc/passwd.jpg", caption="Base montada")
    assert response.status_code == 303
    [photo] = _photos(app)
    # chave gerada: prefixo da empresa + uuid; nunca o nome enviado
    assert photo.object_key == f"{a.company_id}/fotos/{photo.id}.jpg"
    assert photo.thumb_key == f"{a.company_id}/fotos/{photo.id}-mini.jpg"
    assert "passwd" not in photo.object_key and photo.caption == "Base montada"
    stored = _stored(app, photo.object_key)
    assert stored != original and fotos.GPS_MARK not in stored and b"CameraMarca" not in stored
    img = Image.open(io.BytesIO(stored))
    assert img.format == "JPEG" and dict(img.getexif()) == {} and "icc_profile" not in img.info
    assert (img.width, img.height) == (photo.width, photo.height) == (64, 48)

    served = client.get(f"/app/fotos/{photo.id}")
    assert served.status_code == 200 and served.data == stored
    assert served.headers["Content-Type"] == "image/jpeg"
    assert served.headers["X-Content-Type-Options"] == "nosniff"
    assert served.headers["Cache-Control"].startswith("private")
    assert served.headers["Content-Security-Policy"] == "default-src 'none'; sandbox"
    assert served.headers["Content-Disposition"].startswith("inline;")
    mini = client.get(f"/app/fotos/{photo.id}?tamanho=mini")
    assert mini.status_code == 200 and mini.headers["Content-Type"] == "image/jpeg"
    # a página da atividade continua com a CSP estrita de sempre (sem unsafe-inline)
    page = client.get(f"/app/atividades/{a.activity_id}/evidencias")
    assert "unsafe-inline" not in page.headers["Content-Security-Policy"]
    assert f"/app/fotos/{photo.id}?tamanho=mini" in page.get_data(as_text=True)


@pytest.mark.parametrize("maker", [fotos.png, fotos.webp], ids=["png", "webp"])
def test_png_e_webp_aceitos_e_guardados_como_jpeg(app, client, tenants, maker):
    a, _ = tenants
    login(client, app, a.operator_email)
    assert _upload(client, app, a.activity_id, maker(), filename="x.png").status_code == 303
    [photo] = _photos(app)
    assert Image.open(io.BytesIO(_stored(app, photo.object_key))).format == "JPEG"


def test_foto_grande_e_reduzida(app_factory):
    app = app_factory({"PHOTO_MAX_SIDE": 100, "PHOTO_THUMB_SIDE": 20})
    with app.app_context():
        processed = photos.process(fotos.jpeg(400, 200, with_gps=False))
    assert (processed.width, processed.height) == (100, 50)
    assert Image.open(io.BytesIO(processed.thumb)).size == (20, 10)


def test_anonimo_nao_ve_foto(app, client, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    _upload(client, app, a.activity_id, fotos.jpeg())
    [photo] = _photos(app)
    anon = app.test_client()
    response = anon.get(f"/app/fotos/{photo.id}")
    assert response.status_code in (302, 401)
    assert response.headers.get("Content-Type", "").startswith("image/") is False


# ---------------------------------------------------------------- fotos: uploads maliciosos


@pytest.mark.parametrize(
    "data,filename",
    [
        (fotos.HTML_AS_JPG, "foto.jpg"),  # não-imagem com extensão .jpg
        (b"GIF89a" + b"\x00" * 50, "foto.jpg"),
        (fotos.SVG, "desenho.svg"),  # SVG recusado (pode carregar script)
        (fotos.SVG, "desenho.jpg"),
        (fotos.FAKE_JPEG_HEADER, "foto.jpg"),  # magic de JPEG + HTML: não decodifica
        (b"%PDF-1.7\n%...", "foto.jpg"),
        (b"", "foto.jpg"),
    ],
    ids=["html-com-jpg", "gif-truncado", "svg", "svg-com-jpg", "magic-jpeg-falso", "pdf", "vazio"],
)
def test_upload_malicioso_recusado_e_nada_gravado(app, client, tenants, data, filename):
    a, _ = tenants
    login(client, app, a.operator_email)
    response = _upload(client, app, a.activity_id, data, filename=filename)
    assert response.status_code == 400
    assert _photos(app) == []
    root = app.config["STORAGE_LOCAL_DIR"]
    import os

    assert not any(files for _, _, files in os.walk(root))


def test_gif_valido_recusado(app, client, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    assert _upload(client, app, a.activity_id, fotos.gif(), filename="anim.gif").status_code == 400
    assert _photos(app) == []


def test_polyglot_jpeg_com_html_e_zip_colados_sai_limpo(app, client, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    data = fotos.polyglot_jpeg()
    assert fotos.POLYGLOT_PAYLOAD in data
    assert _upload(client, app, a.activity_id, data).status_code == 303
    [photo] = _photos(app)
    stored = _stored(app, photo.object_key)
    assert b"<script>" not in stored and b"PK\x03\x04" not in stored
    served = client.get(f"/app/fotos/{photo.id}")
    assert served.headers["Content-Type"] == "image/jpeg" and b"<script>" not in served.data


def test_imagem_enorme_em_pixels_recusada_sem_decodificar(app, client, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    data = fotos.png_huge_dimensions()
    assert len(data) < 1024  # poucos bytes, 3,6 bilhões de pixels declarados
    response = _upload(client, app, a.activity_id, data, filename="bomba.png")
    assert response.status_code == 400
    assert "dimensões grandes demais" in text_of(response)
    assert _photos(app) == []


def test_foto_acima_de_5_mb_recusada(app, client, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    limit = app.config["PHOTO_MAX_BYTES"]
    # Corpo acima do teto da rota → 413 antes de ler (mensagem com o limite de foto).
    big = fotos.jpeg(with_gps=False) + b"\x00" * (app.config["PHOTO_MAX_REQUEST_BYTES"] + 10)
    response = _upload(client, app, a.activity_id, big)
    assert response.status_code == 413 and "5 MB" in text_of(response)
    # Arquivo de 5 MB + 1 byte, dentro do teto da requisição → recusado pelo serviço.
    just_over = fotos.jpeg(with_gps=False) + b"\x00" * (limit + 1 - len(fotos.jpeg(with_gps=False)))
    assert len(just_over) == limit + 1
    response = _upload(client, app, a.activity_id, just_over)
    assert response.status_code == 400 and "maior que 5 MB" in text_of(response)
    assert _photos(app) == []


def test_outras_rotas_continuam_com_o_teto_global(app, client, tenants):
    """O teto maior vale SÓ para o upload de foto: comentário com corpo de 3 MB → 413."""
    a, _ = tenants
    login(client, app, a.operator_email)
    body = "x" * (app.config["MAX_CONTENT_LENGTH"] + 10)
    response = post(client, app, f"/app/atividades/{a.activity_id}/comentarios", {"body": body})
    assert response.status_code == 413


def test_limite_de_fotos_por_atividade(app_factory):
    from tests.conftest import make_tenant

    app = app_factory({"PHOTOS_MAX_PER_ACTIVITY": 2})
    with app.app_context():
        a = make_tenant("A")
    client = app.test_client()
    login(client, app, a.operator_email)
    for _ in range(2):
        assert _upload(client, app, a.activity_id, fotos.jpeg()).status_code == 303
    response = _upload(client, app, a.activity_id, fotos.jpeg())
    assert response.status_code == 400 and "máximo" in text_of(response)
    assert len(_photos(app)) == 2


def test_so_supervisor_apaga_foto_e_objetos_somem(app, tenants):
    a, _ = tenants
    op = app.test_client()
    login(op, app, a.operator_email)
    _upload(op, app, a.activity_id, fotos.jpeg())
    [photo] = _photos(app)
    assert post(op, app, f"/app/fotos/{photo.id}/apagar").status_code == 403
    assert _exists(app, photo.object_key)
    sup = app.test_client()
    login(sup, app, a.supervisor_email)
    assert post(sup, app, f"/app/fotos/{photo.id}/apagar").status_code == 303
    assert _photos(app) == []
    assert not _exists(app, photo.object_key) and not _exists(app, photo.thumb_key)
    assert sup.get(f"/app/fotos/{photo.id}").status_code == 404
    with app.app_context():
        log = db.session.execute(select(AuditLog).where(AuditLog.action == audit.PHOTO_DELETED)).scalar_one()
        assert log.details["photo_id"] == str(photo.id) and log.company_id == a.company_id


def test_objeto_adulterado_no_armazenamento_nao_e_servido(app, client, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    _upload(client, app, a.activity_id, fotos.jpeg())
    [photo] = _photos(app)
    with app.app_context():
        storage.get_storage().put(photo.object_key, b"<html>trocado</html>", "image/jpeg")
    assert client.get(f"/app/fotos/{photo.id}").status_code == 404


def test_sem_armazenamento_configurado_upload_recusado(app_factory):
    from tests.conftest import make_tenant

    app = app_factory({"STORAGE_BACKEND": "none"})
    with app.app_context():
        a = make_tenant("A")
    client = app.test_client()
    login(client, app, a.operator_email)
    page = client.get(f"/app/atividades/{a.activity_id}/evidencias")
    assert "não está configurado" in text_of(page)
    response = _upload(client, app, a.activity_id, fotos.jpeg())
    assert response.status_code == 400 and _photos(app) == []


def test_modo_leitura_bloqueia_envio(app, client, tenants):
    a, _ = tenants
    with app.app_context():
        company = db.session.get(Company, a.company_id)
        company.created_at = utcnow() - timedelta(days=400)  # teste implícito vencido, sem assinatura
        db.session.commit()
    login(client, app, a.operator_email)
    assert _upload(client, app, a.activity_id, fotos.jpeg()).status_code == 402
    assert post(client, app, f"/app/atividades/{a.activity_id}/comentarios", {"body": "oi"}).status_code == 402
    assert client.get(f"/app/atividades/{a.activity_id}/evidencias").status_code == 200


def test_detalhe_do_projeto_tem_link_para_evidencias_com_contagem(app, client, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    post(client, app, f"/app/atividades/{a.activity_id}/comentarios", {"body": "ok"})
    _upload(client, app, a.activity_id, fotos.jpeg())
    html = client.get(f"/app/projetos/{a.project_id}").get_data(as_text=True)
    assert f"/app/atividades/{a.activity_id}/evidencias" in html
    assert "(2)" in html


# ---------------------------------------------------------------- LGPD


def test_exportacao_lista_metadados_das_fotos_sem_a_imagem(app, client, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    _upload(client, app, a.activity_id, fotos.jpeg())
    [photo] = _photos(app)
    with app.app_context():
        data, counts = lgpd.export_company(db.session.get(Company, a.company_id))
    zf = zipfile.ZipFile(_io.BytesIO(data))
    assert counts["activity_photos.csv"] == 1 and counts["activity_comments.csv"] == 0
    csv_text = zf.read("activity_photos.csv").decode("utf-8-sig")
    assert str(photo.id) in csv_text and photo.sha256 in csv_text
    assert not any(name.endswith(".jpg") for name in zf.namelist())
    assert "Fotos de evidência" in zf.read("LEIA-ME.txt").decode()


def test_expurgo_apaga_os_objetos_das_fotos_e_so_da_empresa(app, tenants):
    a, b = tenants
    for t in (a, b):
        c = app.test_client()
        login(c, app, t.operator_email)
        assert _upload(c, app, t.activity_id, fotos.jpeg()).status_code == 303
    [pa] = _photos(app, a.company_id)
    [pb] = _photos(app, b.company_id)
    with app.app_context():
        company = db.session.get(Company, a.company_id)
        company.deletion_requested_at = utcnow() - timedelta(days=31)
        db.session.commit()
        [dry] = lgpd.purge_due(operator="teste", dry_run=True)
        assert dry.objects_deleted == 2
    assert _exists(app, pa.object_key)  # dry-run não apaga
    with app.app_context():
        [result] = lgpd.purge_due(operator="teste")
        assert result.objects_deleted == 2 and result.rows["activity_photos"] == 1
    assert not _exists(app, pa.object_key) and not _exists(app, pa.thumb_key)
    assert _exists(app, pb.object_key) and _exists(app, pb.thumb_key)


class _BrokenStorage(storage.Storage):
    name = "quebrado"

    def __init__(self, inner):
        self.inner = inner

    def put(self, key, data, content_type):
        self.inner.put(key, data, content_type)

    def get(self, key):
        return self.inner.get(key)

    def delete(self, key):
        raise storage.StorageError("fora do ar")


def test_expurgo_para_se_o_armazenamento_falhar_e_nada_some_do_banco(app, client, tenants):
    a, _ = tenants
    login(client, app, a.operator_email)
    _upload(client, app, a.activity_id, fotos.jpeg())
    with app.app_context():
        storage.set_storage(app, _BrokenStorage(storage.get_storage()))
        company = db.session.get(Company, a.company_id)
        company.deletion_requested_at = utcnow() - timedelta(days=31)
        db.session.commit()
        with pytest.raises(storage.StorageError):
            lgpd.purge_company(a.company_id, operator="teste")
        assert db.session.get(Company, a.company_id) is not None
        assert db.session.execute(select(func.count()).select_from(ActivityPhoto)).scalar_one() == 1


def test_falha_ao_gravar_linha_apaga_o_objeto(app, tenants, monkeypatch):
    a, _ = tenants
    with app.app_context():
        from app.models import Activity

        activity = db.session.get(Activity, a.activity_id)
        original_flush = db.session.flush

        def boom(*args, **kwargs):
            raise RuntimeError("banco caiu")

        monkeypatch.setattr(db.session, "flush", boom)
        with pytest.raises(RuntimeError):
            photos.add_photo(activity, fotos.jpeg(), a.operator_id)
        monkeypatch.setattr(db.session, "flush", original_flush)
    import os

    assert not any(files for _, _, files in os.walk(app.config["STORAGE_LOCAL_DIR"]))
