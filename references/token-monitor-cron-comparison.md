# Token Monitor — Cron Self-Comparison Pattern

When running a recurring monitoring cron job (token consumption, balance checks,
or any time-series metric), each run needs to compare against the previous run's
output to report a trend. This reference covers the pattern.

## Script

`~/.hermes/scripts/token_monitor.py` parses
`~/.hermes/logs/agent.log` for the last 20 API calls:

- **Regex:** `API call #\d+.*?in=(\d+)`
- **Output format:** `Token Monitor: last 20 calls, avg input=<N>, min=<N>, max=<N>`
- **Cron job ID:** `<job_id>` (schedule: `0 */3 * * *`)

## Cross-Session Comparison Pattern

### Step 1 — session_search (primary)

```
session_search(query="token_monitor OR avg input OR Token Monitor", limit=3)
```

Find the most recent previous cron run that includes the script output in its
summary. The session naming convention for cron jobs is:

```
cron_<job_id>_<YYYYMMDD_HHMMSS>
```

### Step 2 — grep session JSON (fallback)

When `session_search` can't find the target session by keyword (common when the
LLM summary doesn't include the literal metrics), fall back to grepping the
session transcript JSON files directly:

```bash
# List recent sessions for this cron job
ls ~/.hermes/sessions/session_cron_<job_id>_* 2>/dev/null

# Extract the previous run's output
grep -o "avg input=[0-9,]*" ~/.hermes/sessions/session_cron_<job_id>_<timestamp>.json
```

More specifically, to get the full metric line with context:

```bash
grep -B2 -A2 "avg input=<N>" ~/.hermes/sessions/session_cron_<job_id>_<timestamp>.json
```

The `"output"` field inside the `"terminal"` tool result contains the raw script
output. This approach bypasses LLM summarization and gives exact numbers.

### Step 3 — compare and report

Compute the delta (current − previous) and percentage change. Report in a simple
table:

| 指标 | 本次 | 上次 | 变化 |
|------|------|------|------|
| 平均输入 | N | N | ↑/↓ X% |

## Why session_search Can Miss

`session_search` relies on LLM-generated session summaries indexed in the
session store. These summaries sometimes paraphrase the metrics (e.g. "average
was about 50k" instead of "avg input=50,483"), making keyword-based retrieval
unreliable. The JSON grep approach reads the raw tool output directly.
