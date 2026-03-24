#!/usr/bin/env python3
"""Hook script for Claude Code 'UserPromptSubmit' event.

Signals the avatar to start thinking when the user sends a message.
"""

import json
import sys

from avatar.bridge.hooks import think


def main():
    try:
        think(socket_path="/tmp/ascii-avatar.sock")
    except Exception:
        pass  # Avatar not running — that's fine


if __name__ == "__main__":
    main()
