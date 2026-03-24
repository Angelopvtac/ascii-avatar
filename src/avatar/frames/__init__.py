"""ASCII art frame set loader.

Supports two modes:
- "cyberpunk": hand-crafted ASCII art frames (legacy)
- "portrait": image-to-ASCII converted frames from a portrait image
- "portrait:<path>": custom image as avatar source
"""

from __future__ import annotations

from pathlib import Path

FRAME_RATES = {
    "idle": 0.8,
    "thinking": 0.15,
    "speaking": 0.1,
    "listening": 0.4,
    "error": 0.2,
}


def load_frame_set(
    name: str,
    width: int = 45,
    height: int = 22,
) -> tuple[dict[str, list[str]], dict[str, float]]:
    """Load a frame set by name.

    Args:
        name: "cyberpunk", "portrait", or "portrait:/path/to/image.png"
        width: ASCII art width in characters (for portrait mode).
        height: ASCII art height in lines (for portrait mode).

    Returns:
        (frames_dict, rates_dict)
    """
    if name == "cyberpunk":
        from avatar.frames.cyberpunk import FRAMES, FRAME_RATES as RATES
        return FRAMES, RATES

    if name.startswith("portrait"):
        return _load_portrait_frames(name, width, height)

    raise KeyError(f"Unknown frame set: {name}")


def _load_portrait_frames(
    name: str,
    width: int,
    height: int,
) -> tuple[dict[str, list[str]], dict[str, float]]:
    """Load portrait-based frames from an image or generate default."""
    from PIL import Image
    from avatar.frames.converter import generate_state_frames

    # Parse custom image path: "portrait:/path/to/image.png"
    if ":" in name and name != "portrait":
        image_path = name.split(":", 1)[1]
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Portrait image not found: {path}")
        base_image = Image.open(path)
    else:
        # Use default generated portrait
        from avatar.frames.portrait import generate_default_portrait
        base_image = generate_default_portrait()

    frames = generate_state_frames(base_image, width, height, charset="density")
    return frames, FRAME_RATES
