"""Conferência da configuração SEM subir o app (útil quando o boot já falha por falta de variável).

Uso:  python scripts/config_check.py [--online] [--strict] [--ignorar CODIGO ...] [--env production]

Mesma lógica de ``flask config-check`` (app/configcheck.py); lê as variáveis do ambiente.
Sai com 1 se houver erro (ou aviso, com --strict).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import configcheck  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--ignorar", action="append", default=[])
    parser.add_argument("--env", default=None, help="Ambiente (padrão: APP_ENV, senão production).")
    args = parser.parse_args(argv)
    cfg, env_name = configcheck.build_config(args.env)
    findings, ok = configcheck.evaluate(cfg, env_name, online=args.online, strict=args.strict, ignore=tuple(args.ignorar))
    print(f"config-check · ambiente={env_name}")
    for finding in findings:
        print(finding.line())
    print("APROVADO." if ok else "REPROVADO: corrija os itens acima antes do deploy.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
