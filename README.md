# deepseek_usage

DeepSeek **余额监控** + **平台用量导出**（合并 [deepseek-balance](https://github.com/mynameisi/deepseek-balance) 与用量页导出能力）。

## 隐私

- 仓库内**无**密钥、无真实用量数据（`data/`、token 均在 `.gitignore`）。
- 分析输出默认 **匿名 key**（`key_1`…），避免把 API key 名称打进日志。
- 平台 token 必须**用户亲自在浏览器登录**后获取，见 [SKILL.md](SKILL.md) 与 [references/browser-login.md](references/browser-login.md)。

## 安装 skill（可选）

```bash
ln -sf "$(pwd)/SKILL.md" ~/.agents/skills/deepseek-usage/SKILL.md
```

## 配置（本机，勿提交）

```bash
export DEEPSEEK_API_KEY=sk-...          # 余额查询
# 登录平台后由 agent 写入：
# ~/.config/deepseek/platform_token
```

## 命令

```bash
python3 scripts/check_balance.py          # 余额 + 与上次快照对比
python3 scripts/open_usage_login.py       # 打开浏览器供登录
python3 scripts/fetch_platform_usage.py   # 拉取当月 ZIP（同网页导出）
python3 scripts/analyze_usage_export.py data/usage_2026_5/
python3 scripts/report.py                 # 余额 + 用量一条龙
```

## 不要用网页「导出」按钮做自动化

会弹出系统「另存为」。脚本直接请求同一 `usage/export` API，无弹窗。

## 文档

- [SKILL.md](SKILL.md) — Agent 完整指引
- [references/browser-login.md](references/browser-login.md) — 浏览器登录流程
- [references/cron-monitoring.md](references/cron-monitoring.md) — 定时余额监控
