#!/usr/bin/env python3
"""Combined report: balance (API key) + optional platform usage export."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def run(cmd: list[str]) -> int:
    print(f"\n$ {' '.join(cmd)}\n")
    return subprocess.call(cmd)


def main():
    p = argparse.ArgumentParser(description="DeepSeek balance + usage combined report")
    p.add_argument("--balance-only", action="store_true")
    p.add_argument("--usage-only", action="store_true")
    p.add_argument("--year", type=int, default=datetime.utcnow().year)
    p.add_argument("--month", type=int, default=datetime.utcnow().month)
    p.add_argument("--no-save-balance", action="store_true")
    args = p.parse_args()

    py = sys.executable
    code = 0

    if not args.usage_only:
        balance_cmd = [py, str(SCRIPTS / "check_balance.py")]
        if args.no_save_balance:
            balance_cmd.append("--no-save")
        code |= run(balance_cmd)

    if not args.balance_only:
        usage_cmd = [
            py,
            str(SCRIPTS / "fetch_platform_usage.py"),
            "--year",
            str(args.year),
            "--month",
            str(args.month),
        ]
        code |= run(usage_cmd)
        out = Path(f"data/usage_{args.year}_{args.month}")
        if out.exists():
            code |= run([py, str(SCRIPTS / "analyze_usage_export.py"), str(out)])

    sys.exit(code)


if __name__ == "__main__":
    main()
