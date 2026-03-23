"""Terminal renderer for ASCII avatar using blessed."""

from __future__ import annotations

import re
import time
from typing import Any

from avatar.frames import load_frame_set
from avatar.state_machine import AvatarState

ANSI_ESCAPE = re.compile(r"\033\[[0-9;]*m")


class AvatarRenderer:
    """Renders ASCII art frames to a terminal.

    Args:
        terminal: A blessed Terminal instance (or fake for testing).
        frame_set: Name of the frame set to load.
        frame_rate_modifier: Multiplier on base frame rates (from persona).
    """

    def __init__(
        self,
        terminal: Any,
        frame_set: str = "cyberpunk",
        frame_rate_modifier: float = 1.0,
    ) -> None:
        self._term = terminal
        self._frames, self._rates = load_frame_set(frame_set)
        self._modifier = frame_rate_modifier
        self._supports_color = getattr(terminal, "number_of_colors", 0) >= 256

    def get_current_frame(self, state: AvatarState, frame_index: int) -> str:
        frames = self._frames.get(state.value, self._frames["idle"])
        if not frames:
            frames = self._frames["idle"]
        idx = frame_index % len(frames)
        frame = frames[idx]
        if not self._supports_color:
            frame = ANSI_ESCAPE.sub("", frame)
        return frame

    def next_frame_index(self, state: AvatarState, current_index: int) -> int:
        frames = self._frames.get(state.value, self._frames["idle"])
        if not frames:
            return 0
        return (current_index + 1) % len(frames)

    def get_frame_rate(self, state: AvatarState) -> float:
        base = self._rates.get(state.value, 0.8)
        return base * self._modifier

    def format_status_bar(
        self,
        state: AvatarState,
        connected: bool,
        tts_loaded: bool,
        last_event: str = "",
    ) -> str:
        conn = "● connected" if connected else "○ waiting"
        tts = "♪ TTS" if tts_loaded else "♪ no TTS"
        return f" {state.value.upper()} │ {conn} │ {tts} │ last: {last_event} "

    def render_frame(self, frame: str, status_bar: str) -> None:
        """Render a frame and status bar to the terminal."""
        with self._term.hidden_cursor():
            print(self._term.home + self._term.clear(), end="")
            print(frame)
            # Status bar at bottom
            y = self._term.height - 1
            with self._term.location(0, y):
                print(status_bar[:self._term.width], end="", flush=True)
