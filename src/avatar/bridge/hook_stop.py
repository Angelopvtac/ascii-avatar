#!/usr/bin/env python3
"""Hook script for Claude Code 'Stop' event.

Reads last_assistant_message from hook input, transforms it into
a spoken status update via Haiku, speaks it, then switches to listen.
"""

import json
import sys
import datetime
from pathlib import Path

from avatar.bridge.hooks import respond, listen
from avatar.voice.summarizer import summarize_for_voice

LOG = Path("/tmp/avatar-hooks.log")


def log(msg: str):
    with open(LOG, "a") as f:
        f.write(f"{datetime.datetime.now().isoformat()} [stop] {msg}\n")


def main():
    log("hook fired")

    try:
        stdin_data = sys.stdin.read()
        hook_input = json.loads(stdin_data) if stdin_data.strip() else {}
    except (json.JSONDecodeError, EOFError) as e:
        log(f"stdin parse error: {e}")
        hook_input = {}

    socket_path = "/tmp/ascii-avatar.sock"

    last_message = hook_input.get("last_assistant_message", "")
    log(f"last_assistant_message length: {len(last_message)}")

    speech = summarize_for_voice(last_message)
    log(f"speech: {speech}")

    if speech:
        try:
            respond(speech, socket_path=socket_path)
            log("speak sent OK")
        except Exception as e:
            log(f"speak failed: {e}")

    try:
        listen(socket_path=socket_path)
        log("listen sent OK")
    except Exception as e:
        log(f"listen failed: {e}")


if __name__ == "__main__":
    main()
