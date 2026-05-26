# Platform login (browser session)

Platform usage APIs need a **login token**, not the API key. Never scrape credentials silently.

## Agent workflow (Cursor browser MCP)

1. **Open browser visibly** for the user:
   - `browser_navigate` → `https://platform.deepseek.com/usage`
   - Set `position: "active"` so the user sees the window.

2. **Tell the user** (Chinese example):
   > 请在打开的浏览器中登录 DeepSeek 开放平台。登录完成并看到「用量信息」页面后告诉我。

3. **Wait for login** — poll `browser_snapshot` until:
   - `menuitem` named `用量信息` is present, and
   - Page shows balance / monthly usage (not only a login form).

4. **After user confirms** (or logged-in UI is visible), read token once:
   ```javascript
   JSON.parse(localStorage.getItem('userToken')).value
   ```
   via `browser_cdp` → `Runtime.evaluate` with `returnByValue: true`.

5. **Save locally** (do not print token in chat):
   ```bash
   mkdir -p ~/.config/deepseek
   # write token to ~/.config/deepseek/platform_token, chmod 600
   ```
   Or call `save_platform_token()` from `scripts/deepseek_common.py` in a one-off helper.

6. **Run export** without clicking the web「导出」button (avoids OS save dialog):
   ```bash
   python3 scripts/fetch_platform_usage.py --year YYYY --month M
   ```

## Do not

- Read `localStorage` before the user has logged in.
- Commit `platform_token`, `data/`, or CSV exports to git.
- Paste full tokens, API keys, or `user_id` from CSV into chat logs.
- Click「导出」and expect automation to handle the system save dialog.

## Fallback (no browser MCP)

```bash
python3 scripts/open_usage_login.py   # opens system browser
# user logs in manually; agent still needs browser MCP or user sets DEEPSEEK_PLATFORM_TOKEN
```
