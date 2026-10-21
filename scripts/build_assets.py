"""Gera os assets de produção: CSS/JS minificados com hash do conteúdo no nome.

Uso:  python scripts/build_assets.py [--check]

Saída em ``app/static/dist/``:
- ``site.<hash>.css``  = tokens + base + layout + components + pages + utilities, minificado
- ``app.<hash>.js``    = ``static/js/app.js`` minificado
- ``arrastar.<hash>.js`` = ``static/js/arrastar.js`` minificado (só na edição do projeto)
- ``htmx.<hash>.js``   = ``static/js/htmx.min.js`` copiado (já vem minificado)
- ``painel.<hash>.js``  = ``static/js/painel.js`` minificado (só nas páginas de painel)
- ``preencher.<hash>.js`` = ``static/js/preencher.js`` minificado (Preencher etapas e Meta e equipe)
- ``manifest.json``    = {"site.css": "dist/site.<hash>.css", ...}

O ECharts (``static/vendor/echarts-5.5.1/``) não passa por aqui: já vem minificado e a versão
está no caminho, então é servido direto com cache longo (sem duplicar 1 MB no dist/).
``app/assets.py`` lê o manifesto e o ``url_for`` aponta para o arquivo com hash (cache longo,
``immutable``). Sem manifesto (checkout limpo), os templates caem nos arquivos-fonte.
``--check`` só confere se o manifesto bate com os fontes (usado nos testes/CI).
Ferramentas fixadas em requirements-dev.txt: rcssmin, rjsmin.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
DIST = STATIC / "dist"

CSS_ORDER = ("tokens", "base", "layout", "components", "pages", "utilities")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:10]


def build_outputs() -> dict[str, tuple[str, bytes]]:
    """{nome lógico: (nome do arquivo com hash, conteúdo)}."""
    import rcssmin
    import rjsmin

    css = "\n".join((STATIC / "css" / f"{n}.css").read_text(encoding="utf-8") for n in CSS_ORDER)
    css_min = rcssmin.cssmin(css).encode("utf-8")
    js_min = rjsmin.jsmin((STATIC / "js" / "app.js").read_text(encoding="utf-8")).encode("utf-8")
    drag_min = rjsmin.jsmin((STATIC / "js" / "arrastar.js").read_text(encoding="utf-8")).encode("utf-8")
    htmx = (STATIC / "js" / "htmx.min.js").read_bytes()
    painel_min = rjsmin.jsmin((STATIC / "js" / "painel.js").read_text(encoding="utf-8")).encode("utf-8")
    fill_min = rjsmin.jsmin((STATIC / "js" / "preencher.js").read_text(encoding="utf-8")).encode("utf-8")
    return {
        "site.css": (f"site.{_digest(css_min)}.css", css_min),
        "app.js": (f"app.{_digest(js_min)}.js", js_min),
        "arrastar.js": (f"arrastar.{_digest(drag_min)}.js", drag_min),
        "htmx.js": (f"htmx.{_digest(htmx)}.js", htmx),
        "painel.js": (f"painel.{_digest(painel_min)}.js", painel_min),
        "preencher.js": (f"preencher.{_digest(fill_min)}.js", fill_min),
    }


def main(argv: list[str]) -> int:
    outputs = build_outputs()
    manifest = {logical: f"dist/{name}" for logical, (name, _) in outputs.items()}
    if "--check" in argv:
        path = DIST / "manifest.json"
        current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if current != manifest:
            print("manifesto desatualizado: rode python scripts/build_assets.py", file=sys.stderr)
            return 1
        return 0
    DIST.mkdir(parents=True, exist_ok=True)
    for old in DIST.iterdir():
        old.unlink()
    for name, data in outputs.values():
        (DIST / name).write_bytes(data)
    (DIST / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for logical, rel in manifest.items():
        print(f"{logical} -> {rel} ({(STATIC / rel).stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
