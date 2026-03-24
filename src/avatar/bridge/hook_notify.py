#!/usr/bin/env python3
"""Hook script for Claude Code 'Notification' event.

Speaks the notification aloud so the user knows Claude needs attention
without looking at the screen.
"""

import json
import sys
import datetime
from pathlib import Path

from avatar.bridge.hooks import respond

LOG = Path("/tmp/avatar-hooks.log")


def log(msg: str):
    with open(LOG, "a") as f:
        f.write(f"{datetime.datetime.now().isoformat()} [notify] {msg}\n")


def main():
    log("hook fired")

    try:
        stdin_data = sys.stdin.read()
        hook_input = json.loads(stdin_data) if stdin_data.strip() else {}
    except (json.JSONDecodeError, EOFError) as e:
        log(f"stdin parse error: {e}")
        hook_input = {}

    socket_path = "/tmp/ascii-avatar.sock"
    notification_type = hook_input.get("notification_type", "")
    message = hook_input.get("message", "")

    log(f"type: {notification_type}, message: {message[:100]}")

    # Speak contextually based on notification type
    if notification_type == "permission_prompt":
        speech = "I need your permission to continue."
    elif notification_type == "idle_prompt":
        speech = "I'm done. Waiting for you."
    elif message:
        # Trim to something speakable
        speech = message[:150]
    else:
        speech = "Hey, I need your attention."

    try:
        respond(speech, socket_path=socket_path)
        log(f"speak sent: {speech}")
    except Exception as e:
        log(f"speak failed: {e}")


if __name__ == "__main__":
    main()
