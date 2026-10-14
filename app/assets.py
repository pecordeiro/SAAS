"""URLs dos assets de produção (CSS/JS minificados com hash no nome).

``python scripts/build_assets.py`` grava ``static/dist/manifest.json``. Com o manifesto,
``asset_urls("site.css")`` devolve ``/static/dist/site.<hash>.css`` (cache de 1 ano, imutável);
sem ele (checkout limpo) devolve os arquivos-fonte, e a página funciona igual.
"""

from __future__ import annotations

import json
from pathlib import Path

from flask import Flask, url_for

STATIC_DIR = Path(__file__).resolve().parent / "static"
ONE_YEAR = 60 * 60 * 24 * 365

# Fallback sem build: o que o site.css reúne, na mesma ordem.
SOURCE_FALLBACK = {
    "site.css": [f"css/{n}.css" for n in ("tokens", "base", "layout", "components", "pages", "utilities")],
    "app.js": ["js/app.js"],
    "htmx.js": ["js/htmx.min.js"],
}


def load_manifest() -> dict[str, str]:
    try:
        data = json.loads((STATIC_DIR / "dist" / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in data.items() if isinstance(v, str) and (STATIC_DIR / v).is_file()}


def init_app(app: Flask) -> None:
    manifest = {} if app.config.get("ASSETS_USE_SOURCES") else load_manifest()

    def asset_urls(logical: str) -> list[str]:
        if logical in manifest:
            return [url_for("static", filename=manifest[logical])]
        return [url_for("static", filename=name) for name in SOURCE_FALLBACK[logical]]

    app.jinja_env.globals["asset_urls"] = asset_urls

    # Arquivos com hash no nome (dist/) e fontes não mudam sem mudar de URL: cache longo.
    def get_send_file_max_age(filename: str | None):
        if filename and (filename.startswith("dist/") or filename.startswith("fonts/")):
            return ONE_YEAR
        return app.config.get("SEND_FILE_MAX_AGE_DEFAULT")

    app.get_send_file_max_age = get_send_file_max_age  # type: ignore[method-assign]
