---
name: deepseek-usage
description: DeepSeek billing — API balance with local delta tracking, platform usage export (per model/day/API key), anonymized analysis, and cron-friendly monitoring. Use for balance checks, spend breakdown, or monthly usage reports.
version: 2.0.0
license: MIT
---

# DeepSeek Usage & Balance

Combined upgrade of balance tracking + platform usage export. Python 3 stdlib only.

## Privacy rules (mandatory)

1. **Never commit** `data/`, `~/.config/deepseek/platform_token`, `balance_history.json`, or CSV/ZIP exports.
2. **Never print** full API keys, platform tokens, or raw `user_id` from CSV in chat.
3. **Default analysis is anonymized** (`key_1`, `key_2`, …). Use `--show-names` only when the user explicitly wants labeled keys in a private session.
4. **Platform token** requires an interactive browser login — see [references/browser-login.md](references/browser-login.md). Do not read `localStorage` until the user has logged in on a **visible** browser tab.

## Credentials

| Credential | Env / file | Used for |
|------------|------------|----------|
| API Key (`sk-…`) | `DEEPSEEK_API_KEY` or `DEEPSEEK_API_KEY_FILE` | `GET https://api.deepseek.com/user/balance` |
| Platform token | `DEEPSEEK_PLATFORM_TOKEN` or `~/.config/deepseek/platform_token` | Usage export & summary APIs |

## Quick commands

Run from this repo root:

```bash
# Balance only (+ save snapshot & show delta)
export DEEPSEEK_API_KEY=sk-...
python3 scripts/check_balance.py

# Full report (needs platform token after browser login)
python3 scripts/report.py

# Usage export for a month (no web「导出」dialog)
python3 scripts/fetch_platform_usage.py --year 2026 --month 5

# Analyze local export (anonymized by default)
python3 scripts/analyze_usage_export.py data/usage_2026_5/
```

Open system browser for login (user completes sign-in):

```bash
python3 scripts/open_usage_login.py
```

## When to use what

| User intent | Tool |
|-------------|------|
| 还剩多少钱 / 今天花了多少（估） | `check_balance.py` |
| 本月消费、按模型/按 key 明细 | `fetch_platform_usage.py` + `analyze_usage_export.py` |
| 一次看完余额 + 用量 | `report.py` |
| 每天自动盯余额 | [references/cron-monitoring.md](references/cron-monitoring.md) |
| 需要登录平台 | [references/browser-login.md](references/browser-login.md) |

## Platform login (agent)

1. `browser_navigate` → `https://platform.deepseek.com/usage` with **`position: "active"`**.
2. Ask user to log in; wait until「用量信息」dashboard is visible.
3. Read `userToken` from `localStorage` once; save to `~/.config/deepseek/platform_token` (`chmod 600`).
4. **Do not** echo the token. **Do not** click web「导出」; use `fetch_platform_usage.py` (same API, no save dialog).

Full steps: [references/browser-login.md](references/browser-login.md).

## APIs

| Endpoint | Auth |
|----------|------|
| `GET api.deepseek.com/user/balance` | API Key |
| `GET platform.deepseek.com/api/v0/usage/export` | Platform token |
| `GET platform.deepseek.com/api/v0/usage/amount` | Platform token |
| `GET platform.deepseek.com/api/v0/usage/cost` | Platform token |
| `GET platform.deepseek.com/api/v0/users/get_user_summary` | Platform token |

## Balance presentation

**Interactive / CLI** — emoji OK.

**Cron / Feishu** — plain pipe tables, no emoji:

```
| 项目 | 金额 |
| --- | --- |
| 总余额 | ¥XXX.XX CNY |
```

## Pitfalls

1. API keys must start with `sk-`. Other prefixes → 401.
2. API key ≠ platform token. Balance API does not return per-key usage.
3. Export rate limit (429) — retry after ~1 minute.
4. Balances are **CNY** unless API says otherwise.
5. `granted_balance` may be promotional; warn if non-zero.

## Verification checklist

- [ ] API key from env/file only (not hardcoded in repo)
- [ ] Platform token obtained only after user login in visible browser
- [ ] Token/key never printed in full
- [ ] Usage analysis uses anonymized labels unless user opted in
- [ ] `data/` and `~/.config/deepseek/*` not committed
