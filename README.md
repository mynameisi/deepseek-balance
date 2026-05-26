# DeepSeek Balance Tracker

查询 DeepSeek API 余额与消费追踪。支持单次查询和每日 cron 自动监控。

## 用法

```bash
curl -s "https://api.deepseek.com/user/balance" \
  -H "Authorization: Bearer <API_KEY>"
```

已配置每日 10:00 cron 自动查询 + 余额对比。

## 文件

- `SKILL.md` — 完整 skill 定义
