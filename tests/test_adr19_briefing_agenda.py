"""ADR-0019 — briefing de identidade visual e agendamento da ligação.

- Briefing (dado da empresa): só plano com ``visual_custom`` (senão 404), só proprietário (403),
  modo leitura → 402, CSRF, campo armadilha, limite por IP e por empresa (429). Estados nova →
  briefing preenchido → em andamento → entregue; edição até "em andamento" (depois só reabrindo).
- Imagens: extensão E conteúdo validados, reencode, armazenamento privado, limites, rota com
  cabeçalhos fixos; expurgo LGPD apaga os objetos.
- Agenda: horários da plataforma (equipe, /interno), reserva atômica da empresa (UNIQUE slot_id,
  testada com duas tentativas), fuso America/Sao_Paulo, pedido de mudança decidido pela equipe.
- E-mails ao cliente e à equipe sem o texto do briefing; auditoria sem texto livre.
"""

from __future__ import annotations

import io
import threading
import uuid
import zipfile
from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy import select, text

from app.extensions import db
from app.models import (
    AuditLog,
    CallBooking,
    CallSlot,
    Company,
    PlatformAuditLog,
    Subscription,
    User,
    VisualBriefing,
    VisualBriefingFile,
    VisualRequest,
)
from app.models.base import utcnow
from app.services import agenda, lgpd, staff, storage, visual
from app.services import email as email_svc
from app.services.plans import get_plan
from tests import fotos
from tests.conftest import (
    csrf_token,
    login,
    make_tenant,
    post,
    requires_postgres,
    text_of,
)
from tests.test_etapa_c_interno import _session_as, _staff_user

BRIEFING = "/app/identidade-visual"
FILES = "/app/identidade-visual/arquivos"
CALL = "/app/identidade-visual/ligacao"
STAFF_EMAIL = "equipe-avisos@exemplo.com"

COMPLETE = {
    "company_name": "Metalúrgica Alfa",
    "products": "Painéis elétricos\nQuadros de comando",
    "colors": "verde-escuro e cinza",
    "fonts": "a do logo atual",
    "reference_sites": "https://exemplo.com.br\nhttp://outro.exemplo.com/pagina",
    "tone": "formal",
    "contact_name": "Maria Souza",
    "contact_phone": "(11) 98888-7777",
    "contact_email": "maria@alfa.example",
}


# ---------------------------------------------------------------- apoio


def _empresa(label: str, plan: str = "empresa"):
    return make_tenant(label, plan=plan)


@pytest.fixture()
def vapp(app_factory):
    return app_factory({"STAFF_NOTIFY_EMAIL": STAFF_EMAIL})


@pytest.fixture()
def vclient(vapp):
    return vapp.test_client()


@pytest.fixture()
def pair(vapp):
    with vapp.app_context():
        return _empresa("A"), _empresa("B")


def _slot(starts_in: timedelta = timedelta(days=2), minutes: int = 30) -> uuid.UUID:
    slot = CallSlot(starts_at=(utcnow() + starts_in).replace(second=0, microsecond=0), duration_minutes=minutes)
    db.session.add(slot)
    db.session.commit()
    return slot.id


def _company(company_id) -> Company:
    return db.session.get(Company, company_id)


def _request(company_id) -> VisualRequest | None:
    return visual.current_request(company_id)


def _upload(client, app, data: bytes, filename: str = "logo.jpg", kind: str = "logo", **extra):
    payload = {"arquivo": (io.BytesIO(data), filename), "tipo": kind, "csrf_token": csrf_token(client, app), **extra}
    return client.post(FILES, data=payload, content_type="multipart/form-data")


def _mails(app):
    return email_svc.outbox(app)


# ================================================================ serviço: validação


def test_sites_de_referencia_aceitam_so_http_e_https_com_limites():
    assert visual.parse_sites("https://a.com.br\n http://b.example/x ,https://a.com.br") == [
        "https://a.com.br",
        "http://b.example/x",
    ]
    assert visual.parse_sites("") == []
    for bad in (
        "ftp://a.com",
        "javascript:alert(1)",
        "www.semesquema.com",
        "https://localhost",
        "https://usuario:senha@a.com",
        "https://" + "a" * 300 + ".com",
        " ".join(f"https://s{i}.com" for i in range(6)),
    ):
        with pytest.raises(visual.VisualError):
            visual.parse_sites(bad)


def test_validacao_de_tom_telefone_email_e_tamanhos():
    ok = visual.validate(visual.BriefingInput(**COMPLETE))
    assert ok["tone"] == "formal" and ok["contact_email"] == "maria@alfa.example"
    assert visual.validate(visual.BriefingInput(tone=""))["tone"] is None
    for change in (
        {"tone": "agressivo"},
        {"contact_phone": "liga pra mim"},
        {"contact_email": "sem-arroba"},
        {"company_name": "x" * 121},
        {"products": "x" * 1001},
        {"colors": "x" * 301},
    ):
        with pytest.raises(visual.VisualError):
            visual.validate(visual.BriefingInput(**{**COMPLETE, **change}))


def test_completo_exige_nome_produtos_e_contato():
    assert not visual.is_complete(None)
    b = VisualBriefing(company_name="X", products="Y", contact_name="Z")
    assert visual.missing_fields(b) == ["Telefone ou e-mail do contato"]
    b.contact_email = "z@z.com"
    assert visual.is_complete(b)


# ================================================================ serviço: estados do briefing


def test_salvar_incompleto_fica_nova_e_completo_vai_para_briefing_preenchido(vapp, pair):
    a, _ = pair
    with vapp.app_context():
        company = _company(a.company_id)
        _, sent = visual.save_briefing(company, visual.BriefingInput(company_name="Alfa"), a.owner_id)
        db.session.commit()
        assert sent is False and _request(a.company_id).status == "new"
        _, sent = visual.save_briefing(company, visual.BriefingInput(**COMPLETE), a.owner_id)
        db.session.commit()
        assert sent is True and _request(a.company_id).status == "briefing_filled"
        # salvar de novo não reenvia
        _, sent = visual.save_briefing(company, visual.BriefingInput(**{**COMPLETE, "colors": "azul"}), a.owner_id)
        db.session.commit()
        assert sent is False
        logs = db.session.query(AuditLog).filter(AuditLog.company_id == a.company_id, AuditLog.action.like("visual.%")).all()
        assert {log.action for log in logs} == {audit_saved(), "visual.briefing_submitted"}
        blob = " ".join(str(log.details) for log in logs)
        assert "Maria" not in blob and "Painéis" not in blob and "exemplo.com" not in blob
        assert "contact_name" in blob  # só o NOME do campo
        platform = db.session.query(PlatformAuditLog).filter_by(action=staff.VISUAL_STATUS_CHANGED).one()
        assert platform.details["para"] == "briefing_filled" and "Maria" not in str(platform.details)


def audit_saved() -> str:
    from app.services import audit

    return audit.VISUAL_BRIEFING_SAVED


def test_em_andamento_trava_a_edicao_e_reabrir_libera(vapp, pair):
    a, _ = pair
    with vapp.app_context():
        company = _company(a.company_id)
        visual.save_briefing(company, visual.BriefingInput(**COMPLETE), a.owner_id)
        db.session.commit()
        req = _request(a.company_id)
        staff_user = db.session.get(User, _staff_user(vapp))
        staff.set_status(req, "in_progress", None, staff_user)
        with pytest.raises(visual.LockedError):
            visual.save_briefing(company, visual.BriefingInput(**COMPLETE), a.owner_id)
        db.session.rollback()
        with pytest.raises(visual.LockedError):
            visual.add_file(company, "logo", "logo.jpg", fotos.jpeg(), a.owner_id)
        db.session.rollback()
        staff.set_status(_request(a.company_id), "briefing_filled", None, staff_user)  # reabre
        visual.save_briefing(company, visual.BriefingInput(**{**COMPLETE, "fonts": "nova"}), a.owner_id)
        db.session.commit()
        assert visual.get_briefing(a.company_id).fonts == "nova"


def test_requisicao_entregue_fica_somente_leitura(vapp, pair):
    a, _ = pair
    with vapp.app_context():
        company = _company(a.company_id)
        req = visual.ensure_request(company)
        req.status = "delivered"
        db.session.commit()
        assert not visual.can_edit(_request(a.company_id))
        with pytest.raises(visual.LockedError):
            visual.save_briefing(company, visual.BriefingInput(**COMPLETE), a.owner_id)


# ================================================================ serviço: agenda


def test_fuso_brasilia_vira_utc():
    assert agenda.to_utc(date(2026, 12, 1), time(10, 0)) == datetime(2026, 12, 1, 13, 0, tzinfo=timezone.utc)
    assert agenda.local(datetime(2026, 12, 1, 13, 0, tzinfo=timezone.utc)).strftime("%H:%M") == "10:00"


def test_reserva_ocupa_o_horario_e_segunda_empresa_e_recusada(vapp, pair):
    a, b = pair
    with vapp.app_context():
        slot_id = _slot()
        contact = agenda.Contact("Maria", "11 98888-7777")
        booking = agenda.book(_company(a.company_id), slot_id, contact, a.owner_id)
        db.session.commit()
        assert booking.slot_id == slot_id
        slot = db.session.get(CallSlot, slot_id)
        assert slot.booked_at is not None and slot.booked_contact_name == "Maria"
        assert slot.visual_request_id == _request(a.company_id).id
        assert slot_id not in {s.id for s in agenda.free_slots()}
        with pytest.raises(agenda.SlotTaken):
            agenda.book(_company(b.company_id), slot_id, contact, b.owner_id)
        db.session.rollback()
        assert db.session.query(CallBooking).count() == 1
        assert agenda.booking_for(b.company_id) is None


def test_concorrencia_duas_tentativas_mesmo_horario_so_uma_fica(vapp, pair):
    """Tela desatualizada: as DUAS empresas viram o horário livre (a marca ainda não estava lá).
    A primeira inserção fica; a segunda bate na restrição UNIQUE(slot_id) e é recusada."""
    a, b = pair
    with vapp.app_context():
        slot_id = _slot()
        # 1ª tentativa: reserva de A gravada sem a marca (como se o UPDATE de A ainda não tivesse sido visto)
        db.session.add(CallBooking(company_id=a.company_id, slot_id=slot_id, contact_name="A", contact_phone="11 99999-0000"))
        db.session.commit()
        assert db.session.get(CallSlot, slot_id).booked_at is None
        # 2ª tentativa: B passa por todas as checagens e tenta inserir → violação tratada
        with pytest.raises(agenda.SlotTaken):
            agenda.book(_company(b.company_id), slot_id, agenda.Contact("B", "11 98888-0000"), b.owner_id)
        db.session.rollback()
        rows = db.session.query(CallBooking).filter_by(slot_id=slot_id).all()
        assert [r.company_id for r in rows] == [a.company_id]
        assert db.session.query(AuditLog).filter_by(company_id=b.company_id, action="call.booked").count() == 0


def test_reserva_valida_futuro_existencia_plano_e_uma_por_empresa(vapp, pair):
    a, _ = pair
    with vapp.app_context():
        company = _company(a.company_id)
        contact = agenda.Contact("Maria", "11 98888-7777")
        past = _slot(timedelta(hours=-1))
        soon = _slot(timedelta(minutes=10))  # dentro da antecedência mínima (60 min)
        for bad in (past, soon, uuid.uuid4(), "nao-e-uuid", None):
            with pytest.raises(agenda.AgendaError):
                agenda.book(company, bad, contact, a.owner_id)
            db.session.rollback()
        ok = _slot()
        agenda.book(company, ok, contact, a.owner_id)
        db.session.commit()
        with pytest.raises(agenda.AgendaError, match="já tem"):
            agenda.book(company, _slot(timedelta(days=3)), contact, a.owner_id)
        db.session.rollback()
        sem_plano = make_tenant("C", plan="profissional")
        with pytest.raises(agenda.AgendaError, match="planos Empresa"):
            agenda.book(_company(sem_plano.company_id), _slot(timedelta(days=4)), contact, sem_plano.owner_id)


def test_contato_da_ligacao_validado():
    with pytest.raises(agenda.AgendaError):
        agenda.validate_contact("", "11 99999-0000")
    with pytest.raises(agenda.AgendaError):
        agenda.validate_contact("Ana", "abc")
    assert agenda.validate_contact(" Ana ", " 11 99999-0000 ") == agenda.Contact("Ana", "11 99999-0000")


def test_equipe_cria_remove_e_decide_pedidos_com_auditoria(vapp, pair):
    a, _ = pair
    with vapp.app_context():
        actor = db.session.get(User, _staff_user(vapp))
        day = (datetime.now(agenda.TZ) + timedelta(days=5)).date()
        slot = agenda.create_slot(day, time(14, 30), 45, actor)
        assert agenda.local(slot.starts_at).strftime("%H:%M") == "14:30"
        with pytest.raises(agenda.AgendaError):
            agenda.create_slot(day, time(14, 30), 45, actor)  # duplicado
        with pytest.raises(agenda.AgendaError):
            agenda.create_slot(date(2020, 1, 1), time(9, 0), 30, actor)  # passado
        with pytest.raises(agenda.AgendaError):
            agenda.create_slot(day, time(9, 0), 5, actor)  # duração
        booking = agenda.book(_company(a.company_id), slot.id, agenda.Contact("Maria", "11 98888-7777"), a.owner_id)
        db.session.commit()
        with pytest.raises(agenda.AgendaError):
            agenda.remove_slot(db.session.get(CallSlot, slot.id), actor)
        agenda.request_change(_company(a.company_id), booking, "remarcar", a.owner_id)
        db.session.commit()
        assert db.session.get(CallSlot, slot.id).change_request == "remarcar"
        agenda.decline(db.session.get(CallSlot, slot.id), actor)
        assert db.session.get(CallSlot, slot.id).change_request is None
        assert agenda.booking_for(a.company_id).change_request is None
        agenda.release(db.session.get(CallSlot, slot.id), actor)
        freed = db.session.get(CallSlot, slot.id)
        assert freed.booked_at is None and freed.booked_contact_name is None and agenda.booking_for(a.company_id) is None
        agenda.remove_slot(freed, actor)
        actions = [r.action for r in db.session.query(PlatformAuditLog).order_by(PlatformAuditLog.at)]
        for action in (agenda.SLOT_CREATED, agenda.CHANGE_DECLINED, agenda.BOOKING_RELEASED, agenda.SLOT_REMOVED):
            assert action in actions
        company_actions = {r.action for r in db.session.query(AuditLog).filter_by(company_id=a.company_id)}
        assert {"call.booked", "call.change_requested", "call.change_declined", "call.released"} <= company_actions


# ================================================================ rotas: acesso


def _all_routes(file_id=None, booking_id=None):
    file_id = file_id or uuid.uuid4()
    booking_id = booking_id or uuid.uuid4()
    return [
        ("GET", BRIEFING, None),
        ("POST", BRIEFING, dict(COMPLETE)),
        ("POST", FILES, {"tipo": "logo"}),
        ("GET", f"{FILES}/{file_id}", None),
        ("POST", f"{FILES}/{file_id}/apagar", {}),
        ("GET", CALL, None),
        ("POST", CALL, {"slot_id": str(uuid.uuid4()), "contact_name": "X", "contact_phone": "11 99999-0000"}),
        ("POST", f"{CALL}/{booking_id}/pedido", {"tipo": "cancelar"}),
    ]


def _call(client, app, method, url, data):
    return client.get(url) if method == "GET" else post(client, app, url, data)


@pytest.mark.parametrize("plan", [None, "essencial", "profissional"])
def test_sem_visual_custom_toda_rota_responde_404(vapp, vclient, plan):
    with vapp.app_context():
        t = make_tenant("S", plan=plan)
    for email_ in (t.owner_email, t.operator_email):
        login(vclient, vapp, email_)
        for method, url, data in _all_routes():
            assert _call(vclient, vapp, method, url, data).status_code == 404, (email_, url)
        post(vclient, vapp, "/sair")
    with vapp.app_context():
        assert db.session.query(VisualBriefing).count() == 0 and db.session.query(VisualRequest).count() == 0


def test_supervisor_e_operador_recebem_403(vapp, vclient, pair):
    a, _ = pair
    for email_ in (a.supervisor_email, a.operator_email):
        login(vclient, vapp, email_)
        for method, url, data in _all_routes():
            assert _call(vclient, vapp, method, url, data).status_code == 403, (email_, url)
        post(vclient, vapp, "/sair")
    with vapp.app_context():
        assert db.session.query(VisualBriefing).count() == 0


def test_modo_leitura_responde_402_na_escrita_e_mostra_a_leitura(vapp, vclient, pair):
    a, _ = pair
    with vapp.app_context():
        sub = db.session.execute(select(Subscription).where(Subscription.company_id == a.company_id)).scalar_one()
        sub.status = "expired"
        slot_id = _slot()
        db.session.commit()
    login(vclient, vapp, a.owner_email)
    assert vclient.get(BRIEFING).status_code == 200
    assert vclient.get(CALL).status_code == 200
    assert post(vclient, vapp, BRIEFING, COMPLETE).status_code == 402
    assert post(vclient, vapp, CALL, {"slot_id": str(slot_id), "contact_name": "M", "contact_phone": "11 99999-0000"}).status_code == 402
    assert _upload(vclient, vapp, fotos.jpeg()).status_code == 402
    with vapp.app_context():
        assert visual.get_briefing(a.company_id) is None and agenda.booking_for(a.company_id) is None


def test_post_sem_csrf_e_recusado(vapp, vclient, pair):
    a, _ = pair
    login(vclient, vapp, a.owner_email)
    assert vclient.post(BRIEFING, data=COMPLETE).status_code == 400
    with vapp.app_context():
        assert visual.get_briefing(a.company_id) is None


def test_campo_armadilha_preenchido_e_recusado_sem_gravar(vapp, vclient, pair):
    a, _ = pair
    with vapp.app_context():
        slot_id = _slot()
    login(vclient, vapp, a.owner_email)
    assert post(vclient, vapp, BRIEFING, {**COMPLETE, "website": "http://spam.example"}).status_code == 400
    assert post(vclient, vapp, CALL, {"slot_id": str(slot_id), "contact_name": "M", "contact_phone": "11 99999-0000",
                                      "website": "x"}).status_code == 400
    assert _upload(vclient, vapp, fotos.jpeg(), website="x").status_code == 400
    with vapp.app_context():
        assert visual.get_briefing(a.company_id) is None and agenda.booking_for(a.company_id) is None
        assert db.session.query(VisualBriefingFile).count() == 0
    # O campo existe nas telas, escondido e fora do Tab.
    html = vclient.get(BRIEFING).get_data(as_text=True)
    assert 'name="website"' in html and 'tabindex="-1"' in html


def test_limite_por_ip_responde_429(app_factory):
    app = app_factory({"RATELIMIT_ENABLED": True, "VISUAL_RATE_LIMIT_IP": "2 per minute"})
    client = app.test_client()
    with app.app_context():
        a = _empresa("A")
    login(client, app, a.owner_email)
    codes = [post(client, app, BRIEFING, {"company_name": "X"}).status_code for _ in range(3)]
    assert codes[:2] == [303, 303] and codes[2] == 429
    assert client.get(BRIEFING).status_code == 200  # leitura não conta


def test_limite_por_empresa_vale_entre_ips_diferentes(app_factory):
    app = app_factory({"RATELIMIT_ENABLED": True, "VISUAL_RATE_LIMIT_IP": "100 per minute", "VISUAL_RATE_LIMIT_COMPANY": "2 per minute"})
    client = app.test_client()
    with app.app_context():
        a = _empresa("A")
    login(client, app, a.owner_email)
    codes = []
    for ip in ("10.0.0.1", "10.0.0.2", "10.0.0.3"):
        payload = {"company_name": "X", "csrf_token": csrf_token(client, app)}
        codes.append(client.post(BRIEFING, data=payload, environ_base={"REMOTE_ADDR": ip}).status_code)
    assert codes == [303, 303, 429]


# ================================================================ rotas: briefing


def test_proprietario_preenche_e_equipe_e_avisada_sem_texto_do_briefing(vapp, vclient, pair):
    a, _ = pair
    login(vclient, vapp, a.owner_email)
    page = vclient.get(BRIEFING)
    assert page.status_code == 200
    html = text_of(page)
    assert "Tom de voz é o jeito que a marca fala com o cliente" in html
    assert "Empresa A" in html  # nome da empresa sugerido
    before = len(_mails(vapp))
    partial = post(vclient, vapp, BRIEFING, {"company_name": "Alfa"})
    assert partial.status_code == 303 and len(_mails(vapp)) == before
    response = post(vclient, vapp, BRIEFING, COMPLETE)
    assert response.status_code == 303
    mails = _mails(vapp)[before:]
    assert [m.to for m in mails] == [STAFF_EMAIL]
    body = mails[0].text + mails[0].html
    assert "Empresa A" in body and "/interno/requisicoes/" in body
    for secret in ("Maria", "Painéis", "98888", "exemplo.com.br", "verde-escuro"):
        assert secret not in body
    with vapp.app_context():
        assert _request(a.company_id).status == "briefing_filled"
        b = visual.get_briefing(a.company_id)
        assert b.reference_sites == "https://exemplo.com.br\nhttp://outro.exemplo.com/pagina"
    html = text_of(vclient.get(BRIEFING))
    assert "Briefing enviado à equipe" in html and 'aria-current="step"' in vclient.get(BRIEFING).get_data(as_text=True)


def test_briefing_invalido_responde_400_e_nao_grava(vapp, vclient, pair):
    a, _ = pair
    login(vclient, vapp, a.owner_email)
    response = post(vclient, vapp, BRIEFING, {**COMPLETE, "reference_sites": "javascript:alert(1)"})
    assert response.status_code == 400 and "http://" in text_of(response)
    with vapp.app_context():
        assert visual.get_briefing(a.company_id) is None


def test_briefing_travado_mostra_respostas_e_recusa_edicao(vapp, vclient, pair):
    a, _ = pair
    login(vclient, vapp, a.owner_email)
    post(vclient, vapp, BRIEFING, COMPLETE)
    with vapp.app_context():
        req = _request(a.company_id)
        req.status = "in_progress"
        db.session.commit()
    html = text_of(vclient.get(BRIEFING))
    assert "A equipe já está trabalhando" in html and "Metalúrgica Alfa" in html and "Salvar briefing" not in html
    assert post(vclient, vapp, BRIEFING, COMPLETE).status_code == 409
    assert _upload(vclient, vapp, fotos.jpeg()).status_code == 409


def test_upload_valida_extensao_e_conteudo_e_serve_com_cabecalhos_fixos(vapp, vclient, pair):
    a, _ = pair
    login(vclient, vapp, a.owner_email)
    assert _upload(vclient, vapp, fotos.jpeg(), filename="logo.gif").status_code == 400  # extensão
    assert _upload(vclient, vapp, b"<svg onload=alert(1)>", filename="logo.jpg").status_code == 400  # conteúdo
    assert _upload(vclient, vapp, fotos.gif(), filename="logo.png").status_code == 400
    assert _upload(vclient, vapp, fotos.jpeg(), kind="outro").status_code == 400
    ok = _upload(vclient, vapp, fotos.png(), filename="Logo Final.PNG")
    assert ok.status_code == 303
    assert _upload(vclient, vapp, fotos.jpeg(), kind="logo").status_code == 400  # só 1 logo
    assert _upload(vclient, vapp, fotos.webp(), filename="produto.webp", kind="produto").status_code == 303
    # JPEG com bytes extras (script/zip no fim): aceito só depois do reencode, que descarta o resto.
    assert _upload(vclient, vapp, fotos.polyglot_jpeg(), filename="poliglota.jpg", kind="produto").status_code == 303
    with vapp.app_context():
        rows = visual.list_files(a.company_id)
        assert sorted(r.kind for r in rows) == ["logo", "produto", "produto"]
        for r in rows:
            stored = storage.get_storage().get(r.object_key)
            assert b"<script>" not in stored and b"PK\x03\x04" not in stored
        logo = next(r for r in rows if r.kind == "logo")
        assert logo.object_key.startswith(f"{a.company_id}/briefing/") and "Logo" not in logo.object_key
        assert storage.get_storage().get(logo.object_key)[:3] == b"\xff\xd8\xff"  # reencodado em JPEG
        logo_id = logo.id
        assert {r.details["tipo"] for r in db.session.query(AuditLog).filter_by(action="visual.file_added")} == {"logo", "produto"}
    response = vclient.get(f"{FILES}/{logo_id}")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "image/jpeg"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Content-Security-Policy"] == "default-src 'none'; sandbox"
    assert "private" in response.headers["Cache-Control"]
    assert vclient.get(f"{FILES}/{logo_id}?tamanho=mini").status_code == 200
    assert post(vclient, vapp, f"{FILES}/{logo_id}/apagar").status_code == 303
    with vapp.app_context():
        assert db.session.get(VisualBriefingFile, logo_id) is None
        with pytest.raises(storage.ObjectNotFound):
            storage.get_storage().get(logo.object_key)


def test_limite_de_fotos_de_produto(app_factory):
    app = app_factory({"BRIEFING_PHOTOS_MAX": 2})
    client = app.test_client()
    with app.app_context():
        a = _empresa("A")
    login(client, app, a.owner_email)
    codes = [_upload(client, app, fotos.jpeg(), filename=f"p{i}.jpg", kind="produto").status_code for i in range(3)]
    assert codes == [303, 303, 400]


def test_menu_so_para_proprietario_com_o_plano(vapp, vclient, pair):
    a, _ = pair
    login(vclient, vapp, a.owner_email)
    assert BRIEFING in vclient.get("/app/projetos").get_data(as_text=True)
    post(vclient, vapp, "/sair")
    login(vclient, vapp, a.supervisor_email)
    assert BRIEFING not in vclient.get("/app/projetos").get_data(as_text=True)
    post(vclient, vapp, "/sair")
    with vapp.app_context():
        t = make_tenant("P", plan="profissional")
    login(vclient, vapp, t.owner_email)
    assert BRIEFING not in vclient.get("/app/projetos").get_data(as_text=True)


# ================================================================ rotas: ligação


def test_agendar_mostra_so_livres_e_futuros_reserva_e_avisa_cliente_e_equipe(vapp, vclient, pair):
    a, b = pair
    with vapp.app_context():
        free = _slot(timedelta(days=2))
        taken = _slot(timedelta(days=3))
        past = _slot(timedelta(hours=-2))
        agenda.book(_company(b.company_id), taken, agenda.Contact("Bruno", "11 97777-0000"), b.owner_id)
        db.session.commit()
    login(vclient, vapp, a.owner_email)
    html = vclient.get(CALL).get_data(as_text=True)
    assert str(free) in html and str(taken) not in html and str(past) not in html and "Bruno" not in html
    before = len(_mails(vapp))
    response = post(vclient, vapp, CALL, {"slot_id": str(free), "contact_name": "Maria", "contact_phone": "(11) 98888-7777"})
    assert response.status_code == 303
    mails = _mails(vapp)[before:]
    assert sorted(m.to for m in mails) == sorted([a.owner_email, STAFF_EMAIL])
    with vapp.app_context():
        when = agenda.local(db.session.get(CallSlot, free).starts_at).strftime("%d/%m/%Y às %H:%M")
    client_mail = next(m for m in mails if m.to == a.owner_email)
    staff_mail = next(m for m in mails if m.to == STAFF_EMAIL)
    assert when in client_mail.text and "Brasília" in client_mail.text
    assert "Empresa A" in staff_mail.text and "98888" not in staff_mail.text  # contato só no painel
    page = text_of(vclient.get(CALL))
    assert "Sua ligação" in page and "Maria" in page


def test_horario_ocupado_com_tela_desatualizada_e_recusado(vapp, vclient, pair):
    a, b = pair
    with vapp.app_context():
        slot_id = _slot()
    login(vclient, vapp, a.owner_email)
    assert str(slot_id) in vclient.get(CALL).get_data(as_text=True)  # A viu livre
    with vapp.app_context():
        agenda.book(_company(b.company_id), slot_id, agenda.Contact("B", "11 97777-0000"), b.owner_id)
        db.session.commit()
    response = post(vclient, vapp, CALL, {"slot_id": str(slot_id), "contact_name": "M", "contact_phone": "11 98888-7777"})
    assert response.status_code == 409 and "acabou de ser reservado" in text_of(response)
    with vapp.app_context():
        assert agenda.booking_for(a.company_id) is None


def test_pedido_de_mudanca_vai_para_a_equipe_que_decide(vapp, vclient, pair):
    a, _ = pair
    with vapp.app_context():
        slot_id = _slot()
    login(vclient, vapp, a.owner_email)
    post(vclient, vapp, CALL, {"slot_id": str(slot_id), "contact_name": "Maria", "contact_phone": "11 98888-7777"})
    with vapp.app_context():
        booking_id = agenda.booking_for(a.company_id).id
    assert post(vclient, vapp, f"{CALL}/{booking_id}/pedido", {"tipo": "outro"}).status_code == 400
    before = len(_mails(vapp))
    assert post(vclient, vapp, f"{CALL}/{booking_id}/pedido", {"tipo": "remarcar"}).status_code == 303
    assert [m.to for m in _mails(vapp)[before:]] == [STAFF_EMAIL]
    assert "Pedido enviado" in text_of(vclient.get(CALL))
    with vapp.app_context():
        assert db.session.get(CallSlot, slot_id).change_request == "remarcar"
        assert agenda.booking_for(a.company_id) is not None  # nada muda sozinho
    # equipe libera → e-mail ao cliente; o cliente pode escolher outro horário
    staff_client = vapp.test_client()
    _session_as(staff_client, vapp, _staff_user(vapp))
    before = len(_mails(vapp))
    assert post(staff_client, vapp, f"/interno/horarios/{slot_id}/reserva", {"acao": "liberar"}).status_code == 303
    decided = _mails(vapp)[before:]
    assert [m.to for m in decided] == [a.owner_email] and "cancelou" in decided[0].text
    with vapp.app_context():
        assert agenda.booking_for(a.company_id) is None and db.session.get(CallSlot, slot_id).booked_at is None
    assert "Escolha um horário" in text_of(vclient.get(CALL))


# ================================================================ /interno


@pytest.mark.parametrize("who", ["anonimo", "dono", "equipe_sem_mfa", "nao_equipe"])
def test_horarios_do_interno_sao_404_para_quem_nao_e_equipe(vapp, vclient, pair, who):
    a, _ = pair
    with vapp.app_context():
        slot_id = _slot()
    if who == "dono":
        login(vclient, vapp, a.owner_email)
    elif who == "equipe_sem_mfa":
        _session_as(vclient, vapp, _staff_user(vapp, mfa=False))
    elif who == "nao_equipe":
        _session_as(vclient, vapp, _staff_user(vapp, is_staff=False))
    assert vclient.get("/interno/horarios").status_code == 404
    day = (datetime.now(agenda.TZ) + timedelta(days=9)).date().isoformat()
    assert post(vclient, vapp, "/interno/horarios", {"day": day, "at": "10:00", "duration": "30"}).status_code == 404
    assert post(vclient, vapp, f"/interno/horarios/{slot_id}/remover").status_code == 404
    assert post(vclient, vapp, f"/interno/horarios/{slot_id}/reserva", {"acao": "liberar"}).status_code == 404
    with vapp.app_context():
        assert db.session.query(CallSlot).count() == 1


def test_equipe_gerencia_horarios_e_ve_reservas_sem_ler_o_briefing(vapp, vclient, pair):
    a, _ = pair
    owner = vapp.test_client()
    login(owner, vapp, a.owner_email)
    post(owner, vapp, BRIEFING, {**COMPLETE, "products": "SEGREDO-DO-BRIEFING"})
    _upload(owner, vapp, fotos.jpeg())
    _session_as(vclient, vapp, _staff_user(vapp))
    day = (datetime.now(agenda.TZ) + timedelta(days=9)).date()
    created = post(vclient, vapp, "/interno/horarios", {"day": day.isoformat(), "at": "10:00", "duration": "30"})
    assert created.status_code == 303
    assert post(vclient, vapp, "/interno/horarios", {"day": day.isoformat(), "at": "10:00", "duration": "30"}).status_code == 400
    assert post(vclient, vapp, "/interno/horarios", {"day": "", "at": "10:00", "duration": "30"}).status_code == 400
    with vapp.app_context():
        slot = db.session.query(CallSlot).one()
        assert slot.starts_at.replace(tzinfo=timezone.utc).hour == 13  # 10:00 BRT = 13:00 UTC
        slot_id = slot.id
    page = text_of(vclient.get("/interno/horarios"))
    assert f"{day:%d/%m/%Y} 10:00" in page and "Livre" in page
    post(owner, vapp, CALL, {"slot_id": str(slot_id), "contact_name": "Maria", "contact_phone": "11 98888-7777"})
    page = text_of(vclient.get("/interno/horarios"))
    assert "Empresa A" in page and "Maria" in page and "98888-7777" in page and "Reservado" in page
    assert post(vclient, vapp, f"/interno/horarios/{slot_id}/remover").status_code == 409
    with vapp.app_context():
        req_id = _request(a.company_id).id
    detail = text_of(vclient.get(f"/interno/requisicoes/{req_id}"))
    assert "Briefing preenchido" in detail and "Maria" in detail
    for html in (page, detail, text_of(vclient.get("/interno"))):
        assert "SEGREDO-DO-BRIEFING" not in html and "/app/identidade-visual/arquivos/" not in html
    assert post(vclient, vapp, f"/interno/horarios/{slot_id}/reserva", {"acao": "manter"}).status_code == 409  # sem pedido
    assert post(vclient, vapp, f"/interno/horarios/{slot_id}/reserva", {"acao": "xyz"}).status_code == 400
    assert post(vclient, vapp, f"/interno/horarios/{uuid.uuid4()}/remover").status_code == 404
    with vapp.app_context():
        logs = db.session.query(PlatformAuditLog).filter_by(action=agenda.SLOT_CREATED).all()
        assert len(logs) == 1 and logs[0].operator == "equipe@exemplo.com"


def test_horarios_do_interno_mostram_data_em_pt_br_e_ajuda_do_seletor(vapp, vclient, pair):
    _session_as(vclient, vapp, _staff_user(vapp))
    day = (datetime.now(agenda.TZ) + timedelta(days=11)).date()
    created = post(vclient, vapp, "/interno/horarios", {"day": day.isoformat(), "at": "15:45", "duration": "30"})
    assert created.status_code == 303
    page = text_of(vclient.get("/interno/horarios", follow_redirects=False))
    assert f"Horário criado: {day:%d/%m/%Y} 15:45" in page  # confirmação em pt-BR (Brasília)
    assert f"{day:%d/%m/%Y} 15:45" in page  # lista sempre em dd/mm/aaaa HH:MM
    assert "Use o seletor; o formato depende do navegador" in page


def test_interno_filtra_e_rotula_o_estado_briefing_preenchido(vapp, vclient, pair):
    a, _ = pair
    owner = vapp.test_client()
    login(owner, vapp, a.owner_email)
    post(owner, vapp, BRIEFING, COMPLETE)
    _session_as(vclient, vapp, _staff_user(vapp))
    html = text_of(vclient.get("/interno?estado=briefing_filled"))
    assert "Empresa A" in html and "Briefing preenchido" in html


# ================================================================ LGPD


def test_expurgo_apaga_imagens_reservas_e_libera_horario(vapp, vclient, pair):
    a, b = pair
    with vapp.app_context():
        slot_a, slot_b = _slot(timedelta(days=2)), _slot(timedelta(days=3))
    login(vclient, vapp, a.owner_email)
    post(vclient, vapp, BRIEFING, COMPLETE)
    _upload(vclient, vapp, fotos.jpeg())
    post(vclient, vapp, CALL, {"slot_id": str(slot_a), "contact_name": "Maria", "contact_phone": "11 98888-7777"})
    with vapp.app_context():
        agenda.book(_company(b.company_id), slot_b, agenda.Contact("Bruno", "11 97777-0000"), b.owner_id)
        db.session.commit()
        keys = [k for r in visual.list_files(a.company_id) for k in (r.object_key, r.thumb_key)]
        assert keys
        company = _company(a.company_id)
        company.deletion_requested_at = utcnow() - timedelta(days=31)
        db.session.commit()
        lgpd.purge_company(a.company_id, operator="teste")
        for key in keys:
            with pytest.raises(storage.ObjectNotFound):
                storage.get_storage().get(key)
        for model in (VisualBriefing, VisualBriefingFile, CallBooking):
            assert db.session.query(model).filter_by(company_id=a.company_id).count() == 0
        freed = db.session.get(CallSlot, slot_a)
        assert freed.booked_at is None and freed.booked_contact_name is None and freed.booked_contact_phone is None
        kept = db.session.get(CallSlot, slot_b)
        assert kept.booked_contact_name == "Bruno" and agenda.booking_for(b.company_id) is not None


def test_exportacao_lgpd_leva_o_briefing_da_propria_empresa(vapp, vclient, pair):
    a, b = pair
    login(vclient, vapp, a.owner_email)
    post(vclient, vapp, BRIEFING, COMPLETE)
    with vapp.app_context():
        visual.save_briefing(_company(b.company_id), visual.BriefingInput(company_name="SEGREDO-B"), b.owner_id)
        db.session.commit()
        data, counts = lgpd.export_company(_company(a.company_id))
    zf = zipfile.ZipFile(io.BytesIO(data))
    assert counts["visual_briefings.csv"] == 1
    blob = b"".join(zf.read(n) for n in zf.namelist()).decode("utf-8")
    assert "Metalúrgica Alfa" in blob and "SEGREDO-B" not in blob


def test_tabelas_novas_no_rls_e_no_expurgo(app):
    from app import rls

    with app.app_context():
        names = {t.name for t in lgpd.company_tables()}
    assert {"visual_briefings", "visual_briefing_files", "call_bookings"} <= set(rls.RLS_TABLES)
    assert {"visual_briefings", "visual_briefing_files", "call_bookings"} <= names
    assert "call_slots" not in rls.RLS_TABLES and "call_slots" not in names


# ================================================================ migration (SQLite) e RLS (PostgreSQL)


def test_migration_status_novo_e_volta_sqlite(tmp_path):
    from app import create_app
    from tests.conftest import downgrade_migrations, run_migrations

    app = create_app("test", {"SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'v.db'}"})
    try:
        run_migrations(app)
        with app.app_context():
            conn = db.session.connection()
            rid = uuid.uuid4().hex
            conn.execute(
                text("INSERT INTO visual_requests (id, company_name, plan_code, status, created_at, updated_at) "
                     "VALUES (:id, 'X', 'empresa', 'briefing_filled', '2026-10-23', '2026-10-23')"),
                {"id": rid},
            )
            with pytest.raises(Exception):
                conn.execute(
                    text("INSERT INTO visual_requests (id, company_name, plan_code, status, created_at, updated_at) "
                         "VALUES (:id, 'Y', 'empresa', 'outro', '2026-10-23', '2026-10-23')"),
                    {"id": uuid.uuid4().hex},
                )
            db.session.rollback()
            conn = db.session.connection()
            conn.execute(
                text("INSERT INTO visual_requests (id, company_name, plan_code, status, created_at, updated_at) "
                     "VALUES (:id, 'X', 'empresa', 'briefing_filled', '2026-10-23', '2026-10-23')"),
                {"id": rid},
            )
            db.session.commit()
            db.session.remove()
        downgrade_migrations(app, "f1a7c3e9b2d4")
        with app.app_context():
            tables = set(db.inspect(db.engine).get_table_names())
            assert not {"visual_briefings", "visual_briefing_files", "call_slots", "call_bookings"} & tables
            assert db.session.execute(text("SELECT status FROM visual_requests")).scalar() == "new"
            db.session.remove()
        run_migrations(app)
    finally:
        with app.app_context():
            db.engine.dispose()


@requires_postgres
def test_rls_tabelas_novas_so_da_propria_empresa(app, tenants):
    """Papel comum (sem BYPASSRLS) com RLS forçado: A não lê nem grava briefing/reserva de B."""
    from tests.test_rls import _set

    a, b = tenants
    with app.app_context():
        slot_b = _slot()
        for t in (a, b):
            db.session.add(VisualBriefing(company_id=t.company_id, company_name=f"Briefing {t.company_id}"))
        db.session.add(CallBooking(company_id=b.company_id, slot_id=slot_b, contact_name="B", contact_phone="11 90000-0000"))
        db.session.commit()
    _rls_check(app, a, b, slot_b, _set)


def _rls_check(app, a, b, slot_b, _set):
    import secrets

    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url
    from sqlalchemy.exc import DBAPIError

    from app import rls
    from tests.conftest import get_test_database_url

    role = "controle_adr19_rls_test"
    password = secrets.token_hex(16)
    with app.app_context():
        with db.engine.begin() as conn:
            if conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname = :r"), {"r": role}).first():
                conn.execute(text(f"DROP OWNED BY {role}"))
                conn.execute(text(f"DROP ROLE {role}"))
            conn.execute(text(f"CREATE ROLE {role} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD '{password}'"))
            conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {role}"))
            conn.execute(text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {role}"))
            rls.enable(conn)
    engine = create_engine(make_url(get_test_database_url()).set(username=role, password=password))
    try:
        with engine.begin() as conn:
            _set(conn, company=a.company_id)
            for table in ("visual_briefings", "call_bookings", "visual_briefing_files"):
                ids = set(conn.execute(text(f'SELECT company_id FROM "{table}"')).scalars())
                assert ids <= {a.company_id}, table
            assert conn.execute(text("SELECT count(*) FROM call_bookings")).scalar() == 0
            # horários são da plataforma: todos visíveis (sem dado de empresa)
            assert conn.execute(text("SELECT count(*) FROM call_slots")).scalar() >= 1
        with engine.connect() as conn:
            trans = conn.begin()
            _set(conn, company=a.company_id)
            with pytest.raises(DBAPIError, match="row-level security"):
                conn.execute(
                    text("INSERT INTO visual_briefings (id, company_id, created_at, updated_at) VALUES (:id, :c, now(), now())"),
                    {"id": uuid.uuid4(), "c": b.company_id},
                )
            trans.rollback()
        with engine.begin() as conn:
            _set(conn, company=a.company_id)
            assert conn.execute(text("DELETE FROM call_bookings WHERE company_id = :c"), {"c": b.company_id}).rowcount == 0
            assert conn.execute(text("UPDATE visual_briefings SET company_name = 'x' WHERE company_id = :c"), {"c": b.company_id}).rowcount == 0
            # UNIQUE(slot_id) vale mesmo sem ver a linha de B: A não consegue reservar o horário de B
            with pytest.raises(DBAPIError):
                with conn.begin_nested():
                    conn.execute(
                        text("INSERT INTO call_bookings (id, company_id, slot_id, contact_name, contact_phone, created_at) "
                             "VALUES (:id, :c, :s, 'A', '11 90000-0000', now())"),
                        {"id": uuid.uuid4(), "c": a.company_id, "s": slot_b},
                    )
    finally:
        engine.dispose()
        with app.app_context():
            with db.engine.begin() as conn:
                rls.disable(conn)
                conn.execute(text(f"DROP OWNED BY {role}"))
                conn.execute(text(f"DROP ROLE {role}"))


@requires_postgres
def test_concorrencia_real_duas_conexoes_postgres(app_factory):
    """Duas requisições ao mesmo tempo (duas conexões): só uma reserva fica com o horário."""
    app = app_factory()
    with app.app_context():
        a, b = _empresa("A"), _empresa("B")
        slot_id = _slot()
    barrier = threading.Barrier(2)
    results: dict[str, str] = {}

    def attempt(tenant, label):
        with app.test_request_context():
            from app import rls

            rls.set_context(company_id=tenant.company_id)
            company = db.session.get(Company, tenant.company_id)
            visual.ensure_request(company)
            db.session.commit()
            barrier.wait()
            try:
                agenda.book(company, slot_id, agenda.Contact(label, "11 90000-0000"), tenant.owner_id)
                db.session.commit()
                results[label] = "ok"
            except agenda.SlotTaken:
                db.session.rollback()
                results[label] = "ocupado"
            finally:
                db.session.remove()

    threads = [threading.Thread(target=attempt, args=(t, lbl)) for t, lbl in ((a, "A"), (b, "B"))]
    for th in threads:
        th.start()
    for th in threads:
        th.join(30)
    assert sorted(results.values()) == ["ocupado", "ok"]
    with app.app_context():
        assert db.session.query(CallBooking).filter_by(slot_id=slot_id).count() == 1
        assert db.session.get(CallSlot, slot_id).booked_at is not None


# ================================================================ revisão de segurança: pedido e liberação


def test_empresa_b_nao_marca_pedido_no_horario_de_a(vapp, pair):
    """Reserva forjada/inconsistente de B apontando para o horário de A: o UPDATE na cópia do horário
    filtra por empresa, requisição e reservado; nada muda em A e B recebe erro."""
    a, b = pair
    with vapp.app_context():
        slot_a = _slot()
        agenda.book(_company(a.company_id), slot_a, agenda.Contact("Maria", "11 98888-7777"), a.owner_id)
        db.session.commit()
        req_b = visual.ensure_request(_company(b.company_id))
        db.session.commit()
        fake = CallBooking(company_id=b.company_id, slot_id=slot_a, visual_request_id=req_b.id,
                           contact_name="B", contact_phone="11 90000-0000")  # nunca gravada (UNIQUE)
        with pytest.raises(agenda.AgendaError):
            agenda.request_change(_company(b.company_id), fake, "remarcar", b.owner_id)
        db.session.rollback()
        # Mesmo com a empresa de A, uma requisição que não é a da reserva não marca nada.
        other = CallBooking(company_id=a.company_id, slot_id=slot_a, visual_request_id=uuid.uuid4(),
                            contact_name="X", contact_phone="11 90000-0000")
        with pytest.raises(agenda.AgendaError):
            agenda.request_change(_company(a.company_id), other, "cancelar", a.owner_id)
        db.session.rollback()
        slot = db.session.get(CallSlot, slot_a)
        assert slot.change_request is None and slot.booked_company_id == a.company_id
        assert agenda.booking_for(a.company_id).change_request is None
        assert db.session.query(AuditLog).filter_by(action="call.change_requested").count() == 0
        # Horário livre (sem reserva) também é recusado.
        free = _slot(timedelta(days=4))
        ghost = CallBooking(company_id=b.company_id, slot_id=free, visual_request_id=req_b.id,
                            contact_name="B", contact_phone="11 90000-0000")
        with pytest.raises(agenda.AgendaError):
            agenda.request_change(_company(b.company_id), ghost, "remarcar", b.owner_id)
        db.session.rollback()
        assert db.session.get(CallSlot, free).change_request is None


def test_equipe_libera_pela_empresa_do_horario_mesmo_sem_a_requisicao(vapp, pair):
    a, _ = pair
    with vapp.app_context():
        slot_id = _slot()
        agenda.book(_company(a.company_id), slot_id, agenda.Contact("Maria", "11 98888-7777"), a.owner_id)
        db.session.commit()
        slot = db.session.get(CallSlot, slot_id)
        slot.visual_request_id = None  # cópia sem a requisição (ex.: apagada)
        db.session.commit()
        actor = db.session.get(User, _staff_user(vapp))
        agenda.release(db.session.get(CallSlot, slot_id), actor)
        assert agenda.booking_for(a.company_id) is None
        freed = db.session.get(CallSlot, slot_id)
        assert freed.booked_at is None and freed.booked_company_id is None
        # o horário volta a ser reservável
        agenda.book(_company(a.company_id), slot_id, agenda.Contact("Maria", "11 98888-7777"), a.owner_id)
        db.session.commit()
