#!/usr/bin/env python3
"""Hook script for Claude Code 'Stop' event.

Reads last_assistant_message from hook input, speaks a summary,
then switches avatar to listen state.
"""

import json
import sys
import datetime
from pathlib import Path

from avatar.bridge.hooks import respond, listen

LOG = Path("/tmp/avatar-hooks.log")


def log(msg: str):
    with open(LOG, "a") as f:
        f.write(f"{datetime.datetime.now().isoformat()} [stop] {msg}\n")


def summarize_for_speech(text: str, max_chars: int = 200) -> str:
    """Take the first 1-2 sentences, cap at max_chars."""
    if not text:
        return ""

    text = text.replace("**", "").replace("```", "").replace("`", "")
    text = text.replace("#", "").strip()

    # Collapse whitespace
    text = " ".join(text.split())

    sentences = []
    current = ""
    for char in text:
        current += char
        if char in ".!?" and len(current.strip()) > 10:
            sentences.append(current.strip())
            current = ""
            if len(" ".join(sentences)) > max_chars // 2:
                break

    if sentences:
        result = " ".join(sentences)
    else:
        result = text[:max_chars]

    return result[:max_chars].strip()


def main():
    log("hook fired")

    try:
        stdin_data = sys.stdin.read()
        log(f"stdin keys: {list(json.loads(stdin_data).keys()) if stdin_data.strip() else 'empty'}")
        hook_input = json.loads(stdin_data) if stdin_data.strip() else {}
    except (json.JSONDecodeError, EOFError) as e:
        log(f"stdin parse error: {e}")
        hook_input = {}

    socket_path = "/tmp/ascii-avatar.sock"

    # Claude Code provides last_assistant_message directly in the hook input
    last_message = hook_input.get("last_assistant_message", "")
    log(f"last_assistant_message length: {len(last_message)}")
    log(f"first 200 chars: {last_message[:200]}")

    speech = summarize_for_speech(last_message)
    log(f"speech: {speech[:100]}")

    if speech:
        try:
            respond(speech, socket_path=socket_path)
            log("speak sent OK")
        except Exception as e:
            log(f"speak failed: {e}")
    else:
        log("no speech to send")

    try:
        listen(socket_path=socket_path)
        log("listen sent OK")
    except Exception as e:
        log(f"listen failed: {e}")


if __name__ == "__main__":
    main()
