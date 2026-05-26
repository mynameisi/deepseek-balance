"""Shared config, credentials, and redaction helpers. No secrets in repo."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "deepseek"
TOKEN_FILE = CONFIG_DIR / "platform_token"
BALANCE_HISTORY_FILE = CONFIG_DIR / "balance_history.json"
BALANCE_URL = "https://api.deepseek.com/user/balance"
PLATFORM_BASE = "https://platform.deepseek.com/api/v0"
USAGE_PAGE = "https://platform.deepseek.com/usage"


def ensure_config_dir() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_api_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    key_file = os.environ.get("DEEPSEEK_API_KEY_FILE", "").strip()
    if key_file:
        return Path(key_file).read_text().strip()
    raise SystemExit(
        "Missing API key. Set DEEPSEEK_API_KEY or DEEPSEEK_API_KEY_FILE.\n"
        "Get a key at https://platform.deepseek.com/api_keys"
    )


def load_api_key_optional() -> str | None:
    try:
        return load_api_key()
    except SystemExit:
        return None


def load_platform_token(*, required: bool = True) -> str | None:
    token = os.environ.get("DEEPSEEK_PLATFORM_TOKEN", "").strip()
    if token:
        return token
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    if required:
        raise SystemExit(
            "Missing platform login token.\n"
            "  1. Open browser: python3 scripts/open_usage_login.py\n"
            "  2. Log in at https://platform.deepseek.com/usage\n"
            "  3. Agent saves token to "
            f"{TOKEN_FILE}\n"
            "  Or: export DEEPSEEK_PLATFORM_TOKEN='...'\n"
            "See SKILL.md § Platform login."
        )
    return None


def save_platform_token(token: str) -> Path:
    ensure_config_dir()
    TOKEN_FILE.write_text(token.strip())
    TOKEN_FILE.chmod(0o600)
    return TOKEN_FILE


def platform_get(path: str, token: str, accept: str = "application/json") -> bytes:
    url = f"{PLATFORM_BASE}/{path.lstrip('/')}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", accept)
    req.add_header(
        "User-Agent",
        "Mozilla/5.0 (compatible; deepseek-usage/1.0)",
    )
    req.add_header("Referer", USAGE_PAGE)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def fetch_balance(api_key: str) -> dict:
    req = urllib.request.Request(BALANCE_URL)
    req.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def parse_platform_json(raw: bytes) -> dict:
    payload = json.loads(raw.decode())
    if payload.get("code") != 0:
        raise RuntimeError(payload.get("msg") or str(payload))
    data = payload.get("data") or {}
    return data.get("biz_data", data)


def mask_api_key(key: str) -> str:
    key = key.strip()
    if len(key) <= 12:
        return "***"
    return f"{key[:7]}***{key[-4:]}"


def anonymize_label(name: str, mapping: dict[str, str]) -> str:
    if name not in mapping:
        mapping[name] = f"key_{len(mapping) + 1}"
    return mapping[name]
