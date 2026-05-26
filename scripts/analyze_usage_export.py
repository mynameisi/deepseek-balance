#!/usr/bin/env python3
"""Analyze usage export ZIP/CSV. Default: anonymized labels (no raw user_id / key names in output)."""

from __future__ import annotations

import argparse
import csv
import io
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from deepseek_common import anonymize_label  # noqa: E402


def read_csv_from_source(src: Path, pattern: str) -> list[dict]:
    if src.is_dir():
        matches = sorted(src.glob(pattern))
        if not matches:
            raise FileNotFoundError(f"No {pattern} under {src}")
        with matches[0].open(newline="") as f:
            return list(csv.DictReader(f))
    with zipfile.ZipFile(src) as zf:
        needle = pattern.replace("*", "").replace(".csv", "")
        name = next(n for n in zf.namelist() if needle in n and n.endswith(".csv"))
        return list(csv.DictReader(io.StringIO(zf.read(name).decode())))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument(
        "--show-names",
        action="store_true",
        help="Print api_key_name as in CSV (default: anonymize to key_1, key_2, ...)",
    )
    args = p.parse_args()
    src = args.source.resolve()

    amount_rows = read_csv_from_source(src, "amount-*.csv")
    cost_rows = read_csv_from_source(src, "cost-*.csv")
    name_map: dict[str, str] = {}

    print("=" * 72)
    print(f"  用量导出分析: {src.name}")
    print("=" * 72)
    print(f"  amount 行数: {len(amount_rows)}")
    print(f"  cost 行数:   {len(cost_rows)}")

    by_model_cost: dict[str, float] = defaultdict(float)
    by_day: dict[str, float] = defaultdict(float)
    for row in cost_rows:
        c = float(row["cost"])
        by_model_cost[row["model"]] += c
        by_day[row["utc_date"]] += c

    print("\n  费用 by 模型:")
    for m, v in sorted(by_model_cost.items(), key=lambda x: -x[1]):
        print(f"    {m}: ¥{v:.2f}")
    print(f"    合计: ¥{sum(by_model_cost.values()):.2f}")

    print("\n  费用 Top 5 日期:")
    for d, v in sorted(by_day.items(), key=lambda x: -x[1])[:5]:
        print(f"    {d}: ¥{v:.2f}")

    agg: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    unique_keys = set()
    for row in amount_rows:
        raw_name = row.get("api_key_name", "")
        label = raw_name if args.show_names else anonymize_label(raw_name, name_map)
        unique_keys.add(label)
        key = (label, row["model"])
        t = row["type"]
        try:
            amt = int(float(row["amount"] or 0))
        except ValueError:
            amt = 0
        agg[key][t] += amt

    print(f"\n  API key 数量: {len(unique_keys)}")
    if not args.show_names:
        print("  (使用匿名标签 key_N；加 --show-names 显示 CSV 中的名称)")
    print("  按 key（请求数降序）:")
    ranked = sorted(agg.items(), key=lambda x: -x[1].get("request_count", 0))
    shown = 0
    for (name, model), m in ranked:
        req = m.get("request_count", 0)
        if req == 0:
            continue
        hit = m.get("input_cache_hit_tokens", 0)
        miss = m.get("input_cache_miss_tokens", 0)
        out = m.get("output_tokens", 0)
        total_in = hit + miss
        cr = hit / total_in * 100 if total_in else 0
        print(
            f"    {name} / {model}: req={req:,}  "
            f"cache_hit={hit:,}  miss={miss:,}  out={out:,}  hit={cr:.1f}%"
        )
        shown += 1
        if shown >= 15:
            remaining = sum(1 for _, mm in ranked if mm.get("request_count", 0)) - shown
            if remaining > 0:
                print(f"    ... 另有 {remaining} 个 key")
            break


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
