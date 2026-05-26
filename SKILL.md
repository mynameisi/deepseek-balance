---
name: deepseek-balance
description: Use when checking or monitoring DeepSeek API balance/consumption. Query balance, track spending over time, set up auto-monitoring cron jobs.
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [deepseek, api, balance, monitoring, billing]
    related_skills: [cronjob-research-monitoring]
---

# DeepSeek Balance Tracker

## Overview

Check DeepSeek API account balance and track consumption over time. Supports one-shot queries and periodic monitoring via cron jobs.

**API Endpoint:** `GET https://api.deepseek.com/user/balance`
**Auth:** `Authorization: Bearer <api_key>`
**API key is stored in memory** — load from memory before querying.

## When to Use

- User asks "check my DeepSeek balance"
- User asks "how much DeepSeek credit do I have left"
- User asks to set up auto-tracking for DeepSeek spending
- Monitoring DeepSeek API usage and cost trends

## One-Shot Balance Check

```bash
curl -s "https://api.deepseek.com/user/balance" \
  -H "Authorization: Bearer <API_KEY>"
```

Response format:
```json
{
  "is_available": true,
  "balance_infos": [
    {
      "currency": "CNY",
      "total_balance": "102.32",
      "granted_balance": "0.00",
      "topped_up_balance": "102.32"
    }
  ]
}
```

### Presenting Results

**CLI / interactive sessions** — use emoji and rich formatting:

```
| 项目 | 金额 |
|------|------|
| 💰 总余额 | ¥XXX.XX CNY |
| 🔴 充值余额 | ¥XXX.XX |
| 🎁 赠送余额 | ¥XXX.XX |
| ✅ 状态 | 可用 / 不可用 |
```

**Feishu / cron delivery** — NO emoji, simple pipe-and-dash tables only. Feishu's `post` message type degrades complex markdown and emoji often render as garbage. Use plain text:

```
| 项目 | 金额 |
| --- | --- |
| 总余额 | ¥XXX.XX CNY |
| 充值余额 | ¥XXX.XX |
| 赠送余额 | ¥0.00 |
| 状态 | 可用 |
```

Cron reports additionally require:
- Daily consumption history table (date | balance | daily delta)
- Cumulative consumption (today | this week)
- Alert status table (check | threshold | actual | status)

Alert statuses: "正常" (OK), "触发" (fired), "关注" (watch).
All output in Chinese for this user.

If previous balance data exists in memory, calculate and show the delta:
- Period: "since last check (YYYY-MM-DD)"
- Δ total: change amount
- If negative, flag as consumption

## Tracking Consumption with Cron

To set up periodic monitoring, use the `cronjob` tool:

```python
cronjob(
    action="create",
    schedule="0 10 * * *",  # Daily at 10am
    name="DeepSeek balance check",
    prompt="Check DeepSeek API balance. Retrieve API key from memory. Query GET https://api.deepseek.com/user/balance with Bearer auth. Compare to last known balance. Report current balance and consumption since last check in a clean table format. If consumption rate is unusually high, flag it.",
    deliver="origin"
)
```

### Recommended Schedules

- **Daily tracking:** `"0 10 * * *"` (10am daily) — good for active usage
- **Weekly tracking:** `"0 10 * * 1"` (Monday 10am) — good for moderate usage
- **Bi-weekly:** `"0 10 1,15 * *"` (1st and 15th)

### Consumption Alert Thresholds

When setting up cron jobs, include these thresholds in the prompt:
- **Warning:** >¥5 consumed in a single day
- **Alert:** >¥20 consumed in a week
- **Critical:** balance below ¥10

## Common Pitfalls

1. **Wrong API key format.** DeepSeek keys start with `sk-`. Keys with other prefixes (e.g. `tml-` from 腾讯云模型平台) return 401 with message: `"Authentication Fails, Your api key: ****<last4> is invalid"`. If user provides a non-`sk-` key, ask if they meant to share a different one — don't assume it's wrong without asking.
2. **Forgetting to update memory after balance check.** Always save the latest balance + timestamp to memory so delta comparisons work. Format: `最近一次余额（YYYY-MM-DD）：¥XXX.XX CNY（充值/赠送明细）`.
3. **Currency assumption.** DeepSeek balances are in CNY. Don't convert to USD unless explicitly asked.
4. **Granted vs topped-up balance.** `granted_balance` may be promotional credits that expire. Warn the user if they have granted balance nearing expiry.
5. **API returns 401 on known-good `sk-` key.** The key may have been rotated or revoked. Ask the user for the new key.
6. **API key masked in file reads.** Tools like `read_file` and `grep` may mask secret values (showing `sk-xxx...xxxx`). In cron/sandboxed environments, source the `.env` file and use the environment variable. **Watch out for other `.env` vars with spaces in their values** (e.g. `OBSIDIAN_VAULT_PATH="/path/with spaces/valt"`), which cause `export $(grep -v '^#' .env | xargs)` to error out. Workarounds:
    - **Best**: extract only the key you need: `DEEPSEEK_API_KEY=$(grep '^DEEPSEEK_API_KEY=' ~/.hermes/.env | cut -d= -f2-); curl -s "https://api.deepseek.com/user/balance" -H "Authorization: Bearer $DEEPSEEK_API_KEY"`
    - **Alternative**: filter out problematic vars: `source <(grep -v '^#' .env | grep -v 'OBSIDIAN_VAULT_PATH' | grep -v 'WIKI_PATH') && curl ...`
7. **Memory tool unavailable in cron.** The `memory` action may fail in cron environments. Fall back to patching `~/.hermes/memories/MEMORY.md` directly with the `patch` tool to update the balance line between runs.

**MEMORY.md format drift:** The balance line format may evolve over time (user edits it manually between cron runs). Observed formats this user has used:
    - Verbose: `最新(2026-05-22): ¥95.74 CNY`
    - Price line: `当前余额: ¥95.74 CNY。`
    - Compact single-line: `DeepSeek key sk-xxx...fdd9, ¥85.72(5/23)。`

**Always read MEMORY.md first to detect the current format**, then use `patch` with the actual line text found. Do NOT assume a fixed format. The extraction pattern `¥(\d+\.\d+)` in the line works across all formats. Save the new balance in the same format you found.

## Token Monitoring (Cron Self-Comparison)

For cron jobs that track metrics over time (token counts, balance deltas, etc.),
each run must compare against the previous run to report a trend. The cross-session
comparison pattern — `session_search` first, then grep session JSON files as
fallback — is documented in `references/token-monitor-cron-comparison.md`.

The token monitor script lives at `~/.hermes/scripts/token_monitor.py`
(cron job ID `<job_id>`, runs every 3 hours), reading `~/.hermes/logs/agent.log`
with regex `API call #\d+.*?in=(\d+)`.

## Verification Checklist

- [ ] API key retrieved from memory (no hardcoding in commands)
- [ ] Balance query returned `is_available: true`
- [ ] Results presented in clean table format (no emoji for Feishu/cron delivery)
- [ ] If previous balance exists, delta calculated and shown
- [ ] Latest balance + timestamp saved to memory (or patched to MEMORY.md if memory tool unavailable)
- [ ] User asked if they want cron monitoring (if not already set up)
- [ ] Cron/Feishu delivery: confirmed zero emoji in output, all tables use | --- | format
