"""Layered 2.5D avatar compositing system.

Decomposes the avatar face into depth-ordered transparent PNG layers.
Pre-composites layer combinations into sixel frames at startup.
At runtime, the avatar indexes into pre-baked frames for zero-CPU animation.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

CANVAS_SIZE = (512, 512)

ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets" / "layers"

CACHE_DIR = Path.home() / ".cache" / "ascii-avatar" / "frames"

# Parallax horizontal pixel offsets per layer at max head rotation (±15 deg).
# Deeper layers shift more to create depth illusion.
PARALLAX_OFFSETS: dict[str, int] = {
    "background": 12,
    "hair": 8,
    "face": 5,
    "eyes": 2,
    "eyebrows": 2,
    "nose": 1,
    "mouth": 1,
    "overlay": 0,
}

# Layer definitions: ordered bottom-to-top, each with named variants.
LAYER_DEFS: dict[str, dict[str, Any]] = {
    "background": {
        "depth": 0,
        "variants": [
            {"name": "dim", "file": "background/bg_dim.png"},
            {"name": "pulse", "file": "background/bg_pulse.png"},
            {"name": "error", "file": "background/bg_error.png"},
        ],
    },
    "hair": {
        "depth": 1,
        "variants": [
            {"name": "center", "file": "hair/hair_center.png"},
            {"name": "left", "file": "hair/hair_left.png"},
            {"name": "right", "file": "hair/hair_right.png"},
        ],
    },
    "face": {
        "depth": 2,
        "variants": [
            {"name": "center", "file": "face/face_center.png"},
            {"name": "left15", "file": "face/face_left15.png"},
            {"name": "right15", "file": "face/face_right15.png"},
            {"name": "up10", "file": "face/face_up10.png"},
            {"name": "down10", "file": "face/face_down10.png"},
        ],
    },
    "eyes": {
        "depth": 3,
        "variants": [
            {"name": "center_open", "file": "eyes/eyes_center_open.png"},
            {"name": "center_half", "file": "eyes/eyes_center_half.png"},
            {"name": "center_closed", "file": "eyes/eyes_center_closed.png"},
            {"name": "left_open", "file": "eyes/eyes_left_open.png"},
            {"name": "left_half", "file": "eyes/eyes_left_half.png"},
            {"name": "left_closed", "file": "eyes/eyes_left_closed.png"},
            {"name": "right_open", "file": "eyes/eyes_right_open.png"},
            {"name": "right_half", "file": "eyes/eyes_right_half.png"},
            {"name": "right_closed", "file": "eyes/eyes_right_closed.png"},
            {"name": "up_open", "file": "eyes/eyes_up_open.png"},
            {"name": "up_half", "file": "eyes/eyes_up_half.png"},
            {"name": "up_closed", "file": "eyes/eyes_up_closed.png"},
            {"name": "down_open", "file": "eyes/eyes_down_open.png"},
            {"name": "down_half", "file": "eyes/eyes_down_half.png"},
            {"name": "down_closed", "file": "eyes/eyes_down_closed.png"},
        ],
    },
    "eyebrows": {
        "depth": 4,
        "variants": [
            {"name": "neutral", "file": "eyebrows/brows_neutral.png"},
            {"name": "raised", "file": "eyebrows/brows_raised.png"},
            {"name": "furrowed", "file": "eyebrows/brows_furrowed.png"},
            {"name": "asymmetric", "file": "eyebrows/brows_asymmetric.png"},
        ],
    },
    "nose": {
        "depth": 5,
        "variants": [
            {"name": "center", "file": "nose/nose_center.png"},
            {"name": "left", "file": "nose/nose_left.png"},
            {"name": "right", "file": "nose/nose_right.png"},
        ],
    },
    "mouth": {
        "depth": 6,
        "variants": [
            {"name": "closed", "file": "mouth/mouth_closed.png"},
            {"name": "slight", "file": "mouth/mouth_slight.png"},
            {"name": "open", "file": "mouth/mouth_open.png"},
            {"name": "wide", "file": "mouth/mouth_wide.png"},
            {"name": "smile", "file": "mouth/mouth_smile.png"},
            {"name": "glitch", "file": "mouth/mouth_glitch.png"},
        ],
    },
    "overlay": {
        "depth": 7,
        "variants": [
            {"name": "scanline_light", "file": "overlay/scanline_light.png"},
            {"name": "scanline_heavy", "file": "overlay/scanline_heavy.png"},
            {"name": "crt_bloom", "file": "overlay/crt_bloom.png"},
            {"name": "holo_flicker", "file": "overlay/holo_flicker.png"},
            {"name": "chrom_aberr", "file": "overlay/chrom_aberr.png"},
            {"name": "glitch_corrupt", "file": "overlay/glitch_corrupt.png"},
            {"name": "noise_bands", "file": "overlay/noise_bands.png"},
            {"name": "red_tint", "file": "overlay/red_tint.png"},
        ],
    },
}


def _head_angle_to_name(angle: str) -> dict[str, str]:
    """Map a head angle keyword to face/hair/nose variant names."""
    mapping = {
        "center": {"face": "center", "hair": "center", "nose": "center"},
        "left": {"face": "left15", "hair": "left", "nose": "left"},
        "right": {"face": "right15", "hair": "right", "nose": "right"},
        "up": {"face": "up10", "hair": "center", "nose": "center"},
        "down": {"face": "down10", "hair": "center", "nose": "center"},
    }
    return mapping[angle]


def _build_combo(
    head: str,
    eyes: str,
    brows: str,
    mouth: str,
    overlay: str,
    bg: str = "dim",
) -> dict[str, str]:
    """Build a layer combination dict from semantic parameters."""
    angle = _head_angle_to_name(head)
    return {
        "background": bg,
        "hair": angle["hair"],
        "face": angle["face"],
        "eyes": eyes,
        "eyebrows": brows,
        "nose": angle["nose"],
        "mouth": mouth,
        "overlay": overlay,
    }


# State-to-frame mapping: each state is a list of layer combination dicts.
# Each combo is one pre-rendered frame.

# --- Idle: ~30 frames ---
_idle_frames = []
# Base idle loop: center, open eyes, breathing glow
for overlay in ["scanline_light", "crt_bloom", "scanline_light"]:
    _idle_frames.append(_build_combo("center", "center_open", "neutral", "closed", overlay))
# Blink cycle
_idle_frames.append(_build_combo("center", "center_half", "neutral", "closed", "scanline_light"))
_idle_frames.append(_build_combo("center", "center_closed", "neutral", "closed", "scanline_light"))
_idle_frames.append(_build_combo("center", "center_half", "neutral", "closed", "scanline_light"))
_idle_frames.append(_build_combo("center", "center_open", "neutral", "closed", "scanline_light"))
# Glance left
_idle_frames.append(_build_combo("center", "left_open", "neutral", "closed", "scanline_light"))
_idle_frames.append(_build_combo("center", "left_open", "neutral", "closed", "scanline_light"))
_idle_frames.append(_build_combo("center", "center_open", "neutral", "closed", "scanline_light"))
# Subtle head drift left
for overlay in ["scanline_light", "crt_bloom", "scanline_light"]:
    _idle_frames.append(_build_combo("left", "center_open", "neutral", "closed", overlay))
# Return center
for overlay in ["scanline_light", "crt_bloom"]:
    _idle_frames.append(_build_combo("center", "center_open", "neutral", "closed", overlay))
# Glance right
_idle_frames.append(_build_combo("center", "right_open", "neutral", "closed", "scanline_light"))
_idle_frames.append(_build_combo("center", "right_open", "neutral", "closed", "scanline_light"))
_idle_frames.append(_build_combo("center", "center_open", "neutral", "closed", "scanline_light"))
# Head drift right
for overlay in ["scanline_light", "crt_bloom", "scanline_light"]:
    _idle_frames.append(_build_combo("right", "center_open", "neutral", "closed", overlay))
# Settle back center
for overlay in ["scanline_light", "crt_bloom", "scanline_light"]:
    _idle_frames.append(_build_combo("center", "center_open", "neutral", "closed", overlay))
# Second blink
_idle_frames.append(_build_combo("center", "center_half", "neutral", "closed", "scanline_light"))
_idle_frames.append(_build_combo("center", "center_closed", "neutral", "closed", "scanline_light"))
_idle_frames.append(_build_combo("center", "center_half", "neutral", "closed", "scanline_light"))
_idle_frames.append(_build_combo("center", "center_open", "neutral", "closed", "crt_bloom"))

# --- Thinking: ~20 frames ---
_thinking_frames = []
# Slow drift with furrowed brows, half-closed eyes, chromatic aberration
for head in ["left", "left", "center", "center", "right", "right", "center", "center"]:
    _thinking_frames.append(_build_combo(head, "center_half", "furrowed", "closed", "chrom_aberr", bg="pulse"))
# Pupil wander
for eyes in ["left_half", "up_half", "right_half", "center_half"]:
    _thinking_frames.append(_build_combo("center", eyes, "furrowed", "closed", "scanline_heavy", bg="pulse"))
# Scanline sweep phases
for overlay in ["scanline_heavy", "chrom_aberr", "scanline_heavy", "crt_bloom"]:
    _thinking_frames.append(_build_combo("center", "center_half", "furrowed", "closed", overlay, bg="pulse"))
# More drift
for head in ["left", "center", "right", "center"]:
    _thinking_frames.append(_build_combo(head, "left_half", "furrowed", "closed", "chrom_aberr", bg="pulse"))

# --- Speaking: ~24 frames ---
_speaking_frames = []
# Mouth cycle with head nod, 4 mouth shapes × 2 head positions × 3 overlays
for head in ["center", "up"]:
    for mouth in ["closed", "slight", "open", "wide", "open", "slight"]:
        for overlay in ["scanline_light", "crt_bloom"]:
            _speaking_frames.append(_build_combo(head, "center_open", "neutral", mouth, overlay))

# --- Listening: ~12 frames ---
_listening_frames = []
# Attentive: wide eyes, raised brows, slight smile, head slightly tilted
for head in ["left", "center", "center", "right"]:
    for overlay in ["crt_bloom", "scanline_light", "crt_bloom"]:
        _listening_frames.append(_build_combo(head, "center_open", "raised", "smile", overlay))

# --- Error: ~16 frames ---
_error_frames = []
# Jitter with glitch overlays, dead eyes, furrowed brows
for head in ["left", "right", "center", "up", "down", "left", "right", "center"]:
    _error_frames.append(_build_combo(head, "center_closed", "furrowed", "glitch", "glitch_corrupt", bg="error"))
    _error_frames.append(_build_combo(head, "down_open", "furrowed", "glitch", "noise_bands", bg="error"))

# --- Micro-events ---
_blink_frames = [
    _build_combo("center", "center_open", "neutral", "closed", "scanline_light"),
    _build_combo("center", "center_half", "neutral", "closed", "scanline_light"),
    _build_combo("center", "center_closed", "neutral", "closed", "scanline_light"),
    _build_combo("center", "center_half", "neutral", "closed", "scanline_light"),
]

_glitch_frames = [
    _build_combo("center", "center_open", "neutral", "closed", "glitch_corrupt"),
    _build_combo("left", "center_open", "neutral", "closed", "noise_bands"),
    _build_combo("right", "center_open", "neutral", "closed", "glitch_corrupt"),
    _build_combo("center", "center_half", "neutral", "closed", "red_tint"),
    _build_combo("center", "center_open", "neutral", "closed", "noise_bands"),
    _build_combo("center", "center_open", "neutral", "closed", "glitch_corrupt"),
]

_flicker_frames = [
    _build_combo("center", "center_open", "neutral", "closed", "holo_flicker"),
    _build_combo("center", "center_half", "neutral", "closed", "holo_flicker"),
    _build_combo("center", "center_open", "neutral", "closed", "scanline_light"),
]

STATE_FRAME_MAP: dict[str, list[dict[str, str]]] = {
    "idle": _idle_frames,
    "thinking": _thinking_frames,
    "speaking": _speaking_frames,
    "listening": _listening_frames,
    "error": _error_frames,
    "blink": _blink_frames,
    "glitch": _glitch_frames,
    "flicker": _flicker_frames,
}
