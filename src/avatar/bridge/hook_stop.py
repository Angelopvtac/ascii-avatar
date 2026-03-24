#!/usr/bin/env python3
"""Hook script for Claude Code 'Stop' event.

Reads the transcript, extracts the last assistant message,
speaks a short summary via avatar, then switches to listen.

Receives JSON on stdin with: session_id, transcript_path, cwd, etc.
"""

import json
import sys
from pathlib import Path

from avatar.bridge.hooks import respond, listen


def get_last_assistant_message(transcript_path: str) -> str:
    """Read the JSONL transcript and return the last assistant text."""
    path = Path(transcript_path)
    if not path.exists():
        return ""

    last_text = ""
    for line in path.read_text().strip().split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Claude Code transcript format: look for assistant messages
        if entry.get("role") == "assistant":
            # Extract text content
            content = entry.get("content", "")
            if isinstance(content, str):
                last_text = content
            elif isinstance(content, list):
                # Content blocks — extract text blocks
                texts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        texts.append(block.get("text", ""))
                if texts:
                    last_text = " ".join(texts)

    return last_text


def summarize_for_speech(text: str, max_chars: int = 200) -> str:
    """Take the first 1-2 sentences, cap at max_chars."""
    if not text:
        return ""

    # Strip markdown formatting
    text = text.replace("**", "").replace("```", "").replace("`", "")
    text = text.replace("#", "").strip()

    # Take first 1-2 sentences
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
        # No sentence boundaries — take first chunk
        result = text[:max_chars]

    return result[:max_chars].strip()


def main():
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    transcript_path = hook_input.get("transcript_path", "")
    socket_path = "/tmp/ascii-avatar.sock"

    if not transcript_path:
        listen(socket_path=socket_path)
        return

    # Get last assistant message
    text = get_last_assistant_message(transcript_path)
    speech = summarize_for_speech(text)

    if speech:
        try:
            respond(speech, socket_path=socket_path)
        except Exception:
            pass  # Avatar not running — that's fine

    try:
        listen(socket_path=socket_path)
    except Exception:
        pass


if __name__ == "__main__":
    main()
