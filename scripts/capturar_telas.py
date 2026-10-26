"""Captura cada tela em 375, 768 e 1280 px, tema claro e escuro (Playwright + Chromium).

Uso:  python scripts/capturar_telas.py <pasta>   (CAP_ONLY=a,b  CAP_WIDTHS=375  CAP_SCHEMES=light filtram)
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
from app.services import units as units_svc  # noqa: E402
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
        # Números de série (módulo unidades): sem eles a tela de unidade não tem link para capturar.
        units_svc.generate(project, "CX10-", 1, 5, 3, users[ROLE_OWNER].id)
        db.session.add(Holiday(company_id=company.id, day=date(today.year, 12, 24), name="Recesso de fim de ano"))
        db.session.commit()
        return project.id, template.id, project.stages[1].activities[2].id


def shot(page, path: Path):
    png = page.screenshot(full_page=True)
    image = Image.open(io.BytesIO(png)).convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    image.save(path, optimize=True)


def enable_modules(app):
    """Liga os módulos opcionais para a captura (alertas, API, unidades/qualidade)."""
    from app.services import modules as msvc

    with app.app_context():
        company = db.session.execute(db.select(Company)).scalars().first()
        msvc.set_modules(company, {m.key: True for m in msvc.available()}, None)
        db.session.commit()


# (nome, caminho) das telas fixas; {pid} = projeto, {tid} = modelo, {aid} = atividade.
PUBLIC = [("inicio", "/"), ("precos", "/precos"), ("como-funciona-pub", "/como-funciona"), ("termos", "/termos"),
          ("privacidade-pub", "/privacidade"), ("contato", "/contato")]
AUTH = [("entrar", "/entrar"), ("cadastro", "/cadastro"), ("senha-esqueci", "/senha/esqueci"),
        ("senha-redefinir", "/senha/redefinir/token-invalido"), ("cadastro-confirme", "/cadastro/confirme"),
        ("convite", "/convite/token-invalido"), ("erro-404", "/nao-existe")]
LOGGED = [
    ("painel-operacao", "/app/"),
    ("painel-projeto", "/app/projetos/{pid}/painel"),
    ("preencher", "/app/preencher?projeto={pid}"),
    ("meta-equipe", "/app/meta-e-equipe?projeto={pid}"),
    ("como-funciona", "/app/como-funciona"),
    ("projetos", "/app/projetos"),
    ("projeto-novo", "/app/projetos/novo"),
    ("projeto-detalhe", "/app/projetos/{pid}"),
    ("projeto-pessoas", "/app/projetos/{pid}/pessoas"),
    ("projeto-historico", "/app/projetos/{pid}/historico"),
    ("projeto-editar", "/app/projetos/{pid}/editar"),
    ("projeto-modelo", "/app/projetos/{pid}/modelo"),
    ("projeto-restaurar", "/app/projetos/{pid}/restaurar"),
    ("projeto-unidades", "/app/projetos/{pid}/unidades"),
    ("historico", "/app/historico"),
    ("importar", "/app/importar"),
    ("modelos", "/app/modelos"),
    ("modelo-novo", "/app/modelos/novo"),
    ("modelo-editar", "/app/modelos/{tid}"),
    ("modelo-versoes", "/app/modelos/{tid}/versoes"),
    ("empresa", "/app/empresa"),
    ("modulos", "/app/empresa/modulos"),
    ("usuarios", "/app/usuarios"),
    ("assinatura", "/app/assinatura"),
    ("assinatura-planos", "/app/assinatura/planos"),
    ("assinatura-cobranca", "/app/assinatura/cobranca"),
    ("assinatura-faturas", "/app/assinatura/faturas"),
    ("privacidade", "/app/privacidade"),
    ("alertas", "/app/alertas"),
    ("api", "/app/integracoes/api"),
    ("unidades-busca", "/app/unidades"),
    ("perfil", "/conta/perfil"),
    ("mfa", "/conta/mfa"),
    ("empresas", "/conta/empresas"),
]
# Telas que dependem de um link da listagem: (nome, listagem, seletor do link)
FOLLOW = [
    ("unidade", "/app/projetos/{pid}/unidades", "a[href*='/app/unidades/']"),
    ("checklist", "/app/projetos/{pid}", "a[href*='/checklist']"),
    ("evidencias", "/app/projetos/{pid}", "a[href*='/evidencias']"),
]


def main(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.png"):
        old.unlink()
    only = os.environ.get("CAP_ONLY")  # lista de nomes separados por vírgula
    widths = tuple(int(w) for w in os.environ.get("CAP_WIDTHS", "375,768,1280").split(","))
    schemes = tuple(os.environ.get("CAP_SCHEMES", "light,dark").split(","))
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    tmp = tempfile.mkdtemp()
    app = create_app("test", {"SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp}/c.db", "SECRET_KEY": "x" * 40, "APP_BASE_URL": base,
                              "FEATURE_PUBLIC_API": True})
    with app.app_context():
        db.create_all()
    project_id, template_id, activity_id = seed(app)
    enable_modules(app)
    server = make_server("127.0.0.1", port, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    ids = {"pid": project_id, "tid": template_id, "aid": activity_id}
    problems: list[str] = []

    def want(name):
        return not only or name in only.split(",")

    def snap(page, name, width, scheme, wait=0):
        if wait:
            page.wait_for_timeout(wait)
        shot(page, out / f"{name}-{width}-{scheme}.png")
        over = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        if over > 0:
            problems.append(f"overflow horizontal {over}px: {name} {width} {scheme}")

    exe = os.environ.get("E2E_CHROMIUM") or CHROME_FALLBACK
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception:  # noqa: BLE001
            browser = pw.chromium.launch(executable_path=exe)
        for scheme in schemes:
            for width in widths:
                ctx = browser.new_context(viewport={"width": width, "height": 800}, color_scheme=scheme, locale="pt-BR")
                page = ctx.new_page()
                for name, path in PUBLIC + AUTH:
                    if want(name):
                        page.goto(base + path)
                        snap(page, name, width, scheme)
                page.goto(base + "/entrar")
                page.fill("#email", "owner@exemplo.com.br")
                page.fill("#password", PASSWORD)
                page.click("button[type=submit].btn--primary")
                page.wait_for_url(lambda u: "/entrar" not in u)
                for name, path in LOGGED:
                    if want(name):
                        resp = page.goto(base + path.format(**ids))
                        if resp is not None and resp.status >= 400:
                            problems.append(f"HTTP {resp.status}: {path}")
                        snap(page, name, width, scheme, wait=1200 if name.startswith("painel") else 150)
                for name, listing, selector in FOLLOW:
                    if want(name):
                        page.goto(base + listing.format(**ids))
                        link = page.query_selector(selector)
                        if link:
                            page.goto(base + link.get_attribute("href"))
                            snap(page, name, width, scheme)
                        else:
                            problems.append(f"sem link para {name}")
                if want("registro"):
                    page.goto(f"{base}/app/projetos/{project_id}#registrar-{activity_id}")
                    snap(page, "registro", width, scheme, wait=300)
                ctx.close()
        browser.close()
    server.shutdown()
    total = sum(p.stat().st_size for p in out.glob("*.png"))
    print(f"{len(list(out.glob('*.png')))} PNGs, {total / 1e6:.1f} MB em {out}")
    for item in problems:
        print("PROBLEMA:", item)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/design/capturas/fase6")
