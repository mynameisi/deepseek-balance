# Balance monitoring (cron)

Lightweight daily check using **API key only** (no browser login).

## Schedule example

```cron
0 10 * * * DEEPSEEK_API_KEY=sk-... /usr/bin/python3 /path/to/deepseek_usage/scripts/check_balance.py >> /tmp/deepseek-balance.log 2>&1
```

Prefer env file readable only by the user:

```bash
set -a && source ~/.config/deepseek/env && set +a
python3 /path/to/deepseek_usage/scripts/check_balance.py
```

## Thresholds (include in cron wrapper or agent prompt)

| Level | Condition |
|-------|-----------|
| 关注 | Single-day balance drop > ¥5 vs previous snapshot |
| 告警 | 7-day cumulative drop > ¥20 |
| 严重 | Balance < ¥10 |

Snapshots are stored in `~/.config/deepseek/balance_history.json` (local only).

## Feishu / plain-text delivery

Use pipe tables, **no emoji**:

```
| 项目 | 金额 |
| --- | --- |
| 总余额 | ¥102.32 CNY |
```

## Monthly deep dive

Cron cannot replace platform login. Run manually or on a schedule where a human completes browser login first, then:

```bash
python3 scripts/report.py --year YYYY --month M
```
