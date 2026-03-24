#!/usr/bin/env python3
"""Hook script for Claude Code 'UserPromptSubmit' event.

Signals the avatar to start thinking when the user sends a message.
"""

import json
import sys
import datetime
from pathlib import Path

LOG = Path("/tmp/avatar-hooks.log")


def log(msg: str):
    with open(LOG, "a") as f:
        f.write(f"{datetime.datetime.now().isoformat()} [think] {msg}\n")


def main():
    log("hook fired")
    try:
        stdin_data = sys.stdin.read()
        log(f"stdin: {stdin_data[:200]}")
    except Exception as e:
        log(f"stdin error: {e}")

    try:
        from avatar.bridge.hooks import think
        think(socket_path="/tmp/ascii-avatar.sock")
        log("think sent OK")
    except Exception as e:
        log(f"think failed: {e}")


if __name__ == "__main__":
    main()
