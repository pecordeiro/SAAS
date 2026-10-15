"""Smoke test de um ambiente no ar (staging ou produção), sem navegador e sem login.

Uso:
    python scripts/smoke_check.py https://staging.seudominio.com.br
    python scripts/smoke_check.py https://www.seudominio.com.br --producao --outro-host https://seudominio.com.br

Confere o que dá para provar de fora: saúde, páginas públicas, cabeçalhos de segurança, cookies,
rotas privadas fechadas para quem não entrou, rotas internas/desligadas respondendo 404, SEO
(robots/sitemap com o host certo), erro sem rastro de pilha, redirecionamentos http→https e
apex↔www, validade do certificado. ``--producao`` torna obrigatórios os itens de lançamento
(textos legais sem “Rascunho”, e-mail de contato real, HSTS). Não cria conta nem altera nada;
o único POST é o webhook do Asaas com token inválido (deve dar 401).

Saída: 0 se tudo passou, 1 se algum item falhou. O roteiro com login (isolamento A/B, cobrança)
está em docs/plano/lancamento.md, Parte C.
"""

from __future__ import annotations

import argparse
import re
import socket
import ssl
import sys
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

import requests

TIMEOUT = 15


class Report:
    def __init__(self) -> None:
        self.failures = 0
        self.rows: list[tuple[str, bool, str]] = []

    def check(self, name: str, ok: bool, detail: str = "") -> bool:
        self.rows.append((name, ok, detail))
        print(f"[{'OK   ' if ok else 'FALHA'}] {name}" + (f" — {detail}" if detail and not ok else ""))
        if not ok:
            self.failures += 1
        return ok

    def skip(self, name: str, why: str) -> None:
        print(f"[PULOU] {name} — {why}")


def run(base: str, *, production: bool, other_host: str | None, session: requests.Session | None = None) -> int:
    base = base.rstrip("/")
    https = base.startswith("https://")
    http = session or requests.Session()
    http.headers["User-Agent"] = "controle-smoke-check/1.0"
    r = Report()

    def get(path: str, **kw):
        kw.setdefault("timeout", TIMEOUT)
        kw.setdefault("allow_redirects", False)
        return http.get(base + path, **kw)

    # 1. Saúde
    res = get("/saude")
    r.check("GET /saude = 200 {status: ok}", res.status_code == 200 and res.json() == {"status": "ok"}, f"HTTP {res.status_code}")
    r.check("/saude sem cache", "no-store" in res.headers.get("Cache-Control", ""), res.headers.get("Cache-Control", ""))
    res = get("/health")
    r.check("GET /health = 200 (banco responde)", res.status_code == 200 and res.json().get("status") == "ok", f"HTTP {res.status_code}")

    # 2. Páginas públicas e cabeçalhos
    home = get("/")
    r.check("GET / = 200", home.status_code == 200, f"HTTP {home.status_code}")
    r.check("home é o produto", "Controle de Produção" in home.text)
    headers = home.headers
    csp = headers.get("Content-Security-Policy", "")
    r.check("CSP estrita (sem unsafe-inline, com default-src 'self')", "default-src 'self'" in csp and "unsafe-inline" not in csp, csp[:80])
    r.check("X-Content-Type-Options: nosniff", headers.get("X-Content-Type-Options") == "nosniff")
    r.check("X-Frame-Options: DENY", headers.get("X-Frame-Options") == "DENY")
    r.check("Referrer-Policy presente", bool(headers.get("Referrer-Policy")))
    r.check("Permissions-Policy presente", bool(headers.get("Permissions-Policy")))
    if https:
        hsts = headers.get("Strict-Transport-Security", "")
        m = re.search(r"max-age=(\d+)", hsts)
        r.check("HSTS com max-age >= 1 ano", bool(m) and int(m.group(1)) >= 31536000, hsts)
    else:
        r.skip("HSTS", "base é http (local)")
    for path in ("/precos", "/entrar", "/cadastro", "/contato", "/termos", "/privacidade"):
        res = get(path)
        r.check(f"GET {path} = 200", res.status_code == 200, f"HTTP {res.status_code}")
    prices = get("/precos").text
    r.check("/precos mostra valores em R$", "R$" in prices)

    # 3. Cookie de sessão (a página de login grava o cookie do CSRF)
    login = get("/entrar")
    cookies = login.headers.get("Set-Cookie", "")
    if cookies:
        r.check("cookie HttpOnly", "httponly" in cookies.lower(), cookies[:60])
        r.check("cookie SameSite", "samesite" in cookies.lower())
        if https:
            r.check("cookie Secure e prefixo __Host-", "secure" in cookies.lower() and "__Host-" in cookies, cookies[:40])
    else:
        r.skip("flags do cookie", "a página não definiu cookie")

    # 4. Rotas privadas fechadas
    for path in ("/app/", f"/app/projetos/{uuid.uuid4()}", f"/app/fotos/{uuid.uuid4()}", "/conta", "/app/privacidade"):
        res = get(path)
        ok = res.status_code in (301, 302, 303, 307, 308, 401, 403, 404) and "/entrar" in (res.headers.get("Location", "") or "/entrar")
        r.check(f"{path} fechado sem login", ok and res.status_code != 200, f"HTTP {res.status_code} → {res.headers.get('Location', '')}")
    for path in ("/interno", "/estilo", "/api/v1/projects", "/app/integracoes/api"):
        res = get(path)
        r.check(f"{path} = 404 (equipe/dev/flag desligada)", res.status_code in (404, 401, 302, 303) and res.status_code != 200, f"HTTP {res.status_code}")
    res = get("/interno")
    r.check("/interno não revela existência (404)", res.status_code == 404, f"HTTP {res.status_code}")

    # 5. Webhook do Asaas recusa token inválido
    res = http.post(base + "/webhooks/asaas", json={"id": "smoke", "event": "TESTE"}, headers={"asaas-access-token": "invalido"}, timeout=TIMEOUT, allow_redirects=False)
    r.check("webhook Asaas: token inválido = 401", res.status_code == 401, f"HTTP {res.status_code}")

    # 6. Erros sem vazar detalhe
    res = get("/nao-existe-" + uuid.uuid4().hex[:8])
    r.check("404 amigável sem rastro de pilha", res.status_code == 404 and "Traceback" not in res.text and "werkzeug" not in res.text.lower())

    # 7. SEO com o host certo
    host = urlsplit(base).netloc
    robots = get("/robots.txt")
    r.check("robots.txt aponta o sitemap do host", robots.status_code == 200 and f"{host}/sitemap.xml" in robots.text, robots.text[-80:])
    sitemap = get("/sitemap.xml")
    r.check("sitemap.xml usa o host", sitemap.status_code == 200 and host in sitemap.text and "localhost" not in sitemap.text.replace(host, ""))

    # 8. Itens de lançamento
    legal = get("/termos").text + get("/privacidade").text
    contact = get("/contato").text
    if production:
        r.check("termos/privacidade sem “Rascunho para revisão jurídica”", "Rascunho para revisão jurídica" not in legal)
        r.check("termos/privacidade sem marcadores [entre colchetes] pendentes", not re.search(r"\[(razão social|número|endereço|data da publicação)[^\]]*\]", legal, re.I))
        r.check("e-mail de contato não é o de exemplo", ".example" not in contact and "controledeproducao.example" not in contact)
        r.check("é https", https)
    else:
        r.skip("itens de lançamento (textos legais, contato)", "use --producao")

    # 9. Redirecionamentos e certificado
    if https:
        insecure = base.replace("https://", "http://", 1)
        try:
            res = requests.get(insecure + "/", timeout=TIMEOUT, allow_redirects=False)
            r.check("http redireciona para https", res.status_code in (301, 308, 302, 307) and res.headers.get("Location", "").startswith("https://"), f"HTTP {res.status_code}")
        except requests.RequestException as exc:
            r.check("http redireciona para https", False, exc.__class__.__name__)
        if other_host:
            try:
                res = requests.get(other_host.rstrip("/") + "/", timeout=TIMEOUT, allow_redirects=False)
                r.check(f"{other_host} redireciona para {base}", res.status_code in (301, 308, 302, 307) and urlsplit(res.headers.get("Location", "")).netloc == host, f"HTTP {res.status_code} → {res.headers.get('Location', '')}")
            except requests.RequestException as exc:
                r.check(f"{other_host} responde", False, exc.__class__.__name__)
        try:
            hostname = urlsplit(base).hostname
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, urlsplit(base).port or 443), timeout=TIMEOUT) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as tls:
                    expires = datetime.fromtimestamp(ssl.cert_time_to_seconds(tls.getpeercert()["notAfter"]), timezone.utc)
            days = (expires - datetime.now(timezone.utc)).days
            r.check("certificado válido por mais de 14 dias", days > 14, f"{days} dias")
        except (OSError, ssl.SSLError, KeyError) as exc:
            r.check("certificado TLS válido", False, exc.__class__.__name__)
    else:
        r.skip("redirecionamento http→https, outro host e certificado", "base é http")

    # 10. Tempo de resposta (aviso de lentidão, não de falha dura)
    started = time.perf_counter()
    get("/saude")
    elapsed = (time.perf_counter() - started) * 1000
    r.check("/saude responde em < 1,5 s", elapsed < 1500, f"{elapsed:.0f} ms")

    total = len(r.rows)
    print(f"\n{total - r.failures}/{total} itens ok · {r.failures} falha(s)")
    return 1 if r.failures else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("base", help="URL base, ex.: https://www.seudominio.com.br")
    parser.add_argument("--producao", action="store_true", help="exige itens de lançamento (textos legais finais, contato real)")
    parser.add_argument("--outro-host", help="o outro host (apex/www) que deve redirecionar para a base")
    args = parser.parse_args(argv)
    return run(args.base, production=args.producao, other_host=args.outro_host)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
