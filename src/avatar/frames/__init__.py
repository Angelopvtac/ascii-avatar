"""ASCII art frame set loader."""

from __future__ import annotations


def load_frame_set(name: str) -> tuple[dict[str, list[str]], dict[str, float]]:
    """Load a frame set by name. Returns (frames_dict, rates_dict)."""
    if name == "cyberpunk":
        from avatar.frames.cyberpunk import FRAMES, FRAME_RATES
        return FRAMES, FRAME_RATES
    raise KeyError(f"Unknown frame set: {name}")
