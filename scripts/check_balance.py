#!/usr/bin/env python3
"""Query DeepSeek balance (API key) and optional delta vs last local snapshot."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from deepseek_common import BALANCE_HISTORY_FILE, BALANCE_URL, ensure_config_dir, load_api_key


def fetch_balance(api_key: str) -> dict:
    req = urllib.request.Request(BALANCE_URL)
    req.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def load_history() -> list[dict]:
    if not BALANCE_HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(BALANCE_HISTORY_FILE.read_text())
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def save_snapshot(total: float, currency: str) -> None:
    ensure_config_dir()
    history = load_history()
    history.append(
        {
            "at": datetime.now(timezone.utc).isoformat(),
            "total_balance": total,
            "currency": currency,
        }
    )
    history = history[-90:]
    BALANCE_HISTORY_FILE.write_text(json.dumps(history, indent=2))
    BALANCE_HISTORY_FILE.chmod(0o600)


def print_table(balance: dict, show_delta: bool, save: bool):
    available = balance.get("is_available", False)
    infos = balance.get("balance_infos") or [{}]
    info = infos[0]
    currency = info.get("currency", "CNY")
    total = float(info.get("total_balance", 0))
    topped = float(info.get("topped_up_balance", 0))
    granted = float(info.get("granted_balance", 0))

    print("| 项目 | 金额 |")
    print("| --- | --- |")
    print(f"| 总余额 | ¥{total:.2f} {currency} |")
    print(f"| 充值余额 | ¥{topped:.2f} |")
    print(f"| 赠送余额 | ¥{granted:.2f} |")
    print(f"| 状态 | {'可用' if available else '不可用'} |")

    if show_delta:
        history = load_history()
        if history:
            prev = history[-1]
            prev_total = float(prev.get("total_balance", 0))
            delta = total - prev_total
            prev_at = prev.get("at", "")[:10]
            sign = "+" if delta >= 0 else ""
            print()
            print(f"| 对比上次 ({prev_at}) | {sign}¥{delta:.2f} |")
            if delta < 0:
                print(f"| 期间消费（估） | ¥{-delta:.2f} |")

    if save:
        save_snapshot(total, currency)
        print()
        print(f"(已记录快照 -> {BALANCE_HISTORY_FILE})")


def main():
    parser = argparse.ArgumentParser(description="DeepSeek API balance check")
    parser.add_argument("--no-save", action="store_true", help="Do not write balance snapshot")
    parser.add_argument("--no-delta", action="store_true", help="Skip comparison with last snapshot")
    parser.add_argument("--json", action="store_true", help="Raw JSON output (no secrets)")
    args = parser.parse_args()

    try:
        api_key = load_api_key()
        balance = fetch_balance(api_key)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(balance, indent=2))
        return

    info = (balance.get("balance_infos") or [{}])[0]
    total = float(info.get("total_balance", 0))
    currency = info.get("currency", "CNY")
    print_table(balance, show_delta=not args.no_delta, save=not args.no_save)


if __name__ == "__main__":
    main()
