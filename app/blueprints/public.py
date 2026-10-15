"""Site público, /saude (liveness), /health (prontidão) e troca de tema."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, Response, abort, current_app, jsonify, redirect, render_template, request, url_for
from sqlalchemy import text

from app.extensions import db, limiter
from app.services import plans as plan_catalog

bp = Blueprint("public", __name__)

THEME_COOKIE = "tema"
THEMES_FIXED = ("light", "dark")
THEMES = ("system",) + THEMES_FIXED


# Páginas públicas indexáveis (sitemap.xml): (endpoint, prioridade). URLs em português.
SITEMAP_PAGES = (
    ("public.index", "1.0"),
    ("public.pricing", "0.9"),
    ("auth.signup", "0.6"),
    ("auth.login", "0.3"),
    ("public.contact", "0.4"),
    ("public.terms", "0.2"),
    ("public.privacy", "0.2"),
)
# Texto dos documentos legais: RASCUNHO até a revisão jurídica (ver docs/plano/progresso.md).
LEGAL_UPDATED = date(2026, 10, 14)
FEATURED_PLAN = "profissional"
PLAN_EXTRAS = (
    ("mfa_required", "MFA obrigatório"),
    ("api", "API de integração"),
    ("visual_custom", "Identidade visual personalizada"),
    ("implantacao", "Implantação por técnicos nossos"),
)


def public_plans() -> list[dict]:
    """Planos ativos da tabela ``plans`` (preço e limites vêm do banco, nunca do template)."""
    def price(cents):
        if cents is None:
            return None  # sob consulta
        return cents // 100 if cents % 100 == 0 else cents / 100

    return [
        {
            "code": plan.code,
            "name": plan.name,
            "price": price(plan.price_cents),
            "projects": "Projetos ilimitados" if plan.max_projects is None else f"{plan.max_projects} projetos ativos",
            "users": f"{plan.max_users} pessoas" if plan.max_users else "Pessoas ilimitadas",
            "extras": [label for key, label in PLAN_EXTRAS if (plan.features or {}).get(key)],
            "features": {key: bool((plan.features or {}).get(key)) for key, _ in PLAN_EXTRAS},
            "trial": plan_catalog.has_trial(plan),
            "self_service": plan_catalog.is_self_service(plan),
            "featured": plan.code == FEATURED_PLAN,
        }
        for plan in plan_catalog.active_plans()
    ]


def _base_url() -> str:
    return (current_app.config.get("APP_BASE_URL") or request.url_root).rstrip("/")


@bp.app_context_processor
def inject_site():
    return {
        "contact_email": current_app.config.get("CONTACT_EMAIL"),
        "site_base_url": _base_url() if request else "",
        "trial_days": current_app.config.get("TRIAL_DAYS", 14),
    }


@bp.get("/")
def index():
    return render_template("public/index.html", plans=public_plans())


@bp.get("/precos")
def pricing():
    return render_template("public/precos.html", plans=public_plans())


@bp.get("/termos")
def terms():
    return render_template("public/termos.html", updated=LEGAL_UPDATED)


@bp.get("/privacidade")
def privacy():
    return render_template("public/privacidade.html", updated=LEGAL_UPDATED)


@bp.get("/contato")
def contact():
    return render_template("public/contato.html")


@bp.get("/sitemap.xml")
def sitemap():
    base = _base_url()
    urls = [
        f"  <url><loc>{base}{url_for(endpoint)}</loc><priority>{priority}</priority></url>"
        for endpoint, priority in SITEMAP_PAGES
    ]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    return Response(xml, mimetype="application/xml")


@bp.get("/robots.txt")
def robots():
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /app/",
        "Disallow: /conta/",
        "Disallow: /convite/",
        "Disallow: /senha/",
        "Disallow: /api/",
        f"Sitemap: {_base_url()}{url_for('public.sitemap')}",
    ]
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


@bp.get("/saude")
@limiter.exempt
def saude():
    """Liveness para o health check do host (Render) e monitor de uptime: o processo está de pé e
    responde HTTP. Não abre sessão, não toca no banco nem no Redis e não devolve versão, ambiente
    ou qualquer dado interno — só ``{"status": "ok"}``. Uma queda do banco não deve fazer o host
    reiniciar o web (isso é a prontidão, ``/health``)."""
    response = jsonify(status="ok")
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/health")
@limiter.exempt
def health():
    """Prontidão: além de responder, o banco precisa responder (``SELECT 1``). Para alerta de
    uptime com banco; NÃO usar como health check de reinício do host (ver ``/saude``)."""
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - não vaza detalhes do banco
        db.session.rollback()
        return jsonify(status="erro", database="indisponível"), 503
    return jsonify(status="ok")


@bp.post("/tema")
def set_theme():
    """Fallback sem JS do seletor de tema: grava o cookie e volta para a página (só caminho interno).

    Com JS, o mesmo cookie é gravado no navegador (static/js/app.js) sem esta requisição.
    """
    from app.blueprints.auth import safe_next

    value = request.form.get("tema", "")
    if value not in THEMES:
        abort(400)
    response = redirect(safe_next(request.form.get("next")) or url_for("public.index"), 303)
    if value == "system":
        response.delete_cookie(THEME_COOKIE, path="/")
    else:
        response.set_cookie(
            THEME_COOKIE,
            value,
            max_age=60 * 60 * 24 * 365,
            path="/",
            samesite="Lax",
            secure=bool(current_app.config.get("SESSION_COOKIE_SECURE")),
            httponly=False,  # o JS do seletor lê e grava o mesmo cookie; não é dado sensível
        )
    return response
