#!/usr/bin/env python3
"""Open DeepSeek usage page in the system browser for interactive login."""

from __future__ import annotations

import webbrowser

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from deepseek_common import USAGE_PAGE


def main():
    print("Opening browser for DeepSeek platform login:")
    print(f"  {USAGE_PAGE}")
    print()
    print("After you log in and see the usage dashboard:")
    print("  - Let your agent continue (it will read the session), or")
    print("  - Run fetch_platform_usage.py once the agent has saved the token.")
    webbrowser.open(USAGE_PAGE)


if __name__ == "__main__":
    main()
