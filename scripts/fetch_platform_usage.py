#!/usr/bin/env python3
"""Fetch DeepSeek platform usage export (same ZIP as the usage page Export button)."""

from __future__ import annotations

import argparse
import csv
import io
import sys
import urllib.error
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from deepseek_common import (  # noqa: E402
    fetch_balance,
    load_api_key_optional,
    load_platform_token,
    parse_platform_json,
    platform_get,
)


def export_month(token: str, year: int, month: int, out_dir: Path) -> Path:
    raw = platform_get(
        f"usage/export?month={month}&year={year}",
        token,
        accept="application/zip,application/octet-stream,*/*",
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"usage_{year}_{month}.zip"
    zip_path.write_bytes(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        zf.extractall(out_dir)
    return zip_path


def summarize_cost_csv(cost_path: Path) -> dict[str, float]:
    by_model: dict[str, float] = defaultdict(float)
    with cost_path.open(newline="") as f:
        for row in csv.DictReader(f):
            by_model[row["model"]] += float(row["cost"])
    return dict(by_model)


def usage_type_label(t: str) -> str:
    return {
        "PROMPT_TOKEN": "prompt",
        "PROMPT_CACHE_HIT_TOKEN": "cache_hit",
        "PROMPT_CACHE_MISS_TOKEN": "cache_miss",
        "RESPONSE_TOKEN": "output",
        "REQUEST": "requests",
    }.get(t, t.lower())


def print_summary(token: str, year: int, month: int, out_dir: Path, api_key: str | None):
    summary = parse_platform_json(platform_get("users/get_user_summary", token))
    amount = parse_platform_json(
        platform_get(f"usage/amount?month={month}&year={year}", token)
    )
    cost = parse_platform_json(
        platform_get(f"usage/cost?month={month}&year={year}", token)
    )

    print("=" * 72)
    print(f"  DeepSeek 用量报告  {year}-{month:02d}  (UTC, ~5min delay)")
    print("=" * 72)

    wallets = summary.get("normal_wallets", [])
    monthly_costs = summary.get("monthly_costs", [])
    bal = wallets[0]["balance"] if wallets else "?"
    cur = wallets[0]["currency"] if wallets else "CNY"
    month_spend = monthly_costs[0]["amount"] if monthly_costs else "?"

    print(f"  充值余额     ¥{float(bal):.2f} {cur}")
    print(f"  本月消费     ¥{float(month_spend):.2f} {cur}")
    print(f"  本月 tokens  {summary.get('monthly_token_usage', '?')}")

    if api_key:
        try:
            bal_api = fetch_balance(api_key)
            infos = bal_api.get("balance_infos", [{}])[0]
            print(f"  API 余额     ¥{float(infos.get('total_balance', 0)):.2f} (api.deepseek.com)")
        except urllib.error.HTTPError as e:
            print(f"  API 余额     (query failed: HTTP {e.code})")

    print()
    print("  模型汇总 (amount API)")
    for block in amount.get("total", []):
        model = block["model"]
        parts = [
            f"{usage_type_label(u['type'])}={u['amount']}"
            for u in block.get("usage", [])
        ]
        print(f"    {model}: {', '.join(parts)}")

    print()
    print("  模型费用 CNY (cost API)")
    if isinstance(cost, list):
        # API returns [{ "total": [...], "days": [...], "currency": "CNY" }]
        cost_total = cost[0].get("total", []) if cost and isinstance(cost[0], dict) else []
    else:
        cost_total = cost.get("total", [])
    if cost_total:
        for block in cost_total:
            model = block.get("model", "unknown")
            cny = sum(
                float(u["amount"])
                for u in block.get("usage", [])
                if u["type"] != "REQUEST"
            )
            print(f"    {model}: ¥{cny:.2f}")

    cost_csv = out_dir / f"cost-{year}-{month}.csv"
    if cost_csv.exists():
        by_model = summarize_cost_csv(cost_csv)
        total = sum(by_model.values())
        print()
        print("  导出 CSV 汇总 (cost-*.csv)")
        for m, v in sorted(by_model.items(), key=lambda x: -x[1]):
            print(f"    {m}: ¥{v:.2f}")
        print(f"    合计: ¥{total:.2f}")
        print(f"    数据目录: {out_dir}/ (本地，勿提交 git)")


def main():
    parser = argparse.ArgumentParser(description="Fetch DeepSeek platform usage export + summary")
    parser.add_argument("--year", type=int, default=datetime.utcnow().year)
    parser.add_argument("--month", type=int, default=datetime.utcnow().month)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--export-only", action="store_true")
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    token = load_platform_token()
    api_key = load_api_key_optional()
    out_dir = (args.out or Path(f"data/usage_{args.year}_{args.month}")).resolve()

    if not args.summary_only:
        try:
            zip_path = export_month(token, args.year, args.month, out_dir)
            print(f"Exported -> {zip_path}")
            print(f"Extracted -> {out_dir}/")
        except urllib.error.HTTPError as e:
            print(f"Export failed: HTTP {e.code}", file=sys.stderr)
            if e.code == 429:
                print("Rate limited — retry later or use --summary-only.", file=sys.stderr)
            sys.exit(1)

    if not args.export_only:
        print_summary(token, args.year, args.month, out_dir, api_key)


if __name__ == "__main__":
    main()
