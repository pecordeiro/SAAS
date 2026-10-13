"""Site público (provisório) e /health."""

from __future__ import annotations

from flask import Blueprint, jsonify, render_template
from sqlalchemy import text

from app.extensions import db, limiter

bp = Blueprint("public", __name__)


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
