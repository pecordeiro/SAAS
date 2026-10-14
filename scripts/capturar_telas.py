"""Captura cada tela em 375, 768 e 1280 px, tema claro e escuro (Playwright + Chromium).

Uso:  python scripts/capturar_telas.py docs/design/capturas/fase6
Sobe o app com dados fictícios (telas.md §0: lote CX-10, 5 etapas) num SQLite temporário.
Os PNGs são reduzidos (paleta de 128 cores) para o conjunto ficar bem abaixo de 10 MB.
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import threading
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Company, Holiday, Membership, User, ROLE_OPERATOR, ROLE_OWNER, ROLE_SUPERVISOR  # noqa: E402
from app.services import projects as svc  # noqa: E402
from app.services import templates as tsvc  # noqa: E402
from app.services.holidays import seed_national_holidays  # noqa: E402
from app.services.passwords import hash_password  # noqa: E402
from app.services.plans import seed_plans  # noqa: E402
from tests.e2e.conftest import CHROME_FALLBACK, _free_port  # noqa: E402

PASSWORD = "senha-de-captura-123"
VIEWPORTS = (375, 768, 1280)
SCHEMES = ("light", "dark")
STAGES = [
    ("1. Preparação de chassi", [("Corte e rebarba", 60, 10), ("Furação", 45, 10), ("Pintura", 75, 10)]),
    ("2. Montagem mecânica", [("Fixação da base", 120, 9), ("Montagem de eixos", 180, 8), ("Alinhamento", 60, 7)]),
    ("3. Instalação elétrica", [("Passagem de cabos", 150, 6), ("Montagem do painel", 210, 5), ("Conexões", 120, 4)]),
    ("4. Testes funcionais", [("Teste em vazio", 90, 2), ("Teste com carga", 150, 2)]),
    ("5. Embalagem e expedição", [("Limpeza final", 30, 1), ("Embalagem", 90, 1)]),
]


def seed(app):
    with app.app_context():
        seed_plans()
        seed_national_holidays(date.today().year, date.today().year + 1)
        company = Company(name="Metalúrgica Exemplo Ltda.", cnpj="11.222.333/0001-81")
        db.session.add(company)
        db.session.flush()
        users = {}
        for role, name in ((ROLE_OWNER, "Ana Souza"), (ROLE_SUPERVISOR, "Carlos Lima"), (ROLE_OPERATOR, "João Pereira")):
            user = User(email=f"{role}@exemplo.com.br", name=name, password_hash=hash_password(PASSWORD),
                        email_confirmed_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc))
            db.session.add(user)
            db.session.flush()
            db.session.add(Membership(company_id=company.id, user_id=user.id, role=role))
            users[role] = user
        stages = [svc.NewStage(n, [svc.NewActivity(a, Decimal(m)) for a, m, _ in acts]) for n, acts in STAGES]
        template = tsvc.create_template(company, "Equipamento compacto", stages, users[ROLE_OWNER].id)
        today = date.today()
        project = tsvc.create_project_from_template(
            company, template, name="Lote 2026-014", product="Equipamento compacto CX-10", quantity=10,
            start_date=today - timedelta(days=8), due_date=today + timedelta(days=10), people=3, hours_per_day=Decimal("8"),
        )
        late = tsvc.create_project_from_template(
            company, template, name="Lote 2026-015", product="Painel de comando PC-4", quantity=6,
            start_date=today - timedelta(days=2), due_date=today + timedelta(days=3), people=1, hours_per_day=Decimal("4"),
        )
        tsvc.create_project_from_template(
            company, template, name="Lote 2026-016", product="Módulo de transporte MT-1", quantity=20,
            start_date=today + timedelta(days=5), due_date=today + timedelta(days=40), people=3, hours_per_day=Decimal("8"),
        )
        db.session.flush()
        for stage, (_, acts) in zip(project.stages, STAGES):
            for activity, (_, _, done) in zip(stage.activities, acts):
                left = done
                while left > 0:
                    step = min(left, 2 if left > 3 else 1)
                    who = users[ROLE_OPERATOR] if left % 2 else users[ROLE_SUPERVISOR]
                    svc.register_progress(activity, step, activity.version, who.id)
                    left -= step
        svc.register_progress(late.stages[0].activities[0], 1, 1, users[ROLE_OPERATOR].id)
        db.session.add(Holiday(company_id=company.id, day=date(today.year, 12, 24), name="Recesso de fim de ano"))
        db.session.commit()
        return project.id, template.id, project.stages[1].activities[2].id


def shot(page, path: Path):
    png = page.screenshot(full_page=True)
    image = Image.open(io.BytesIO(png)).convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    image.save(path, optimize=True)


def main(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.png"):
        old.unlink()
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    tmp = tempfile.mkdtemp()
    app = create_app("test", {"SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp}/c.db", "SECRET_KEY": "x" * 40, "APP_BASE_URL": base})
    with app.app_context():
        db.create_all()
    project_id, template_id, activity_id = seed(app)
    server = make_server("127.0.0.1", port, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    public = [("inicio", "/"), ("precos", "/precos"), ("termos", "/termos"), ("privacidade", "/privacidade"),
              ("contato", "/contato"), ("entrar", "/entrar"), ("cadastro", "/cadastro"), ("404", "/nao-existe")]
    logged = [
        ("projetos", "/app/projetos"),
        ("projetos-busca", "/app/projetos?q=painel&status=todos"),
        ("detalhe", f"/app/projetos/{project_id}"),
        ("historico-projeto", f"/app/projetos/{project_id}/historico"),
        ("historico-geral", "/app/historico"),
        ("novo-projeto", "/app/projetos/novo"),
        ("modelos", "/app/modelos"),
        ("modelo-editor", f"/app/modelos/{template_id}"),
        ("importar", "/app/importar"),
        ("usuarios", "/app/usuarios"),
        ("empresa", "/app/empresa"),
        ("perfil", "/conta/perfil"),
    ]
    exe = os.environ.get("E2E_CHROMIUM") or CHROME_FALLBACK
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception:  # noqa: BLE001
            browser = pw.chromium.launch(executable_path=exe)
        for scheme in SCHEMES:
            for width in VIEWPORTS:
                ctx = browser.new_context(viewport={"width": width, "height": 800}, color_scheme=scheme, locale="pt-BR")
                page = ctx.new_page()
                for name, path in public:
                    page.goto(base + path)
                    shot(page, out / f"{name}-{width}-{scheme}.png")
                page.goto(base + "/entrar")
                page.fill("#email", "owner@exemplo.com.br")
                page.fill("#password", PASSWORD)
                page.click("button[type=submit].btn--primary")
                page.wait_for_url(lambda u: "/entrar" not in u)
                for name, path in logged:
                    page.goto(base + path)
                    if name == "novo-projeto":
                        page.wait_for_timeout(600)  # resumo via HTMX
                    shot(page, out / f"{name}-{width}-{scheme}.png")
                # folha de registro (celular/tablet) ou linha inline (desktop)
                page.goto(f"{base}/app/projetos/{project_id}#registrar-{activity_id}")
                page.wait_for_timeout(400)
                shot(page, out / f"detalhe-registro-{width}-{scheme}.png")
                ctx.close()
        browser.close()
    server.shutdown()
    total = sum(p.stat().st_size for p in out.glob("*.png"))
    print(f"{len(list(out.glob('*.png')))} PNGs, {total / 1e6:.1f} MB em {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/design/capturas/fase6")
