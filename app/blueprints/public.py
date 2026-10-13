"""Site público, /health e troca de tema."""

from __future__ import annotations

from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, url_for
from sqlalchemy import text

from app.extensions import db, limiter

bp = Blueprint("public", __name__)

THEME_COOKIE = "tema"
THEMES_FIXED = ("light", "dark")
THEMES = ("system",) + THEMES_FIXED


@bp.get("/")
def index():
    return render_template("public/index.html")


@bp.get("/health")
@limiter.exempt
def health():
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
