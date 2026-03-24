"""Convert images to ASCII art using vertical bar density mapping.

Produces the halftone/scanline portrait aesthetic from the reference image.
Characters are chosen by luminance — dark areas get dense block chars,
light areas get thin bars or spaces.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance


# Density ramp: darkest → lightest
# Vertical bar characters create the scanline aesthetic from the reference
DENSITY_CHARS = "█▓▒░│║┃|!:·. "

# Alternative: pure vertical bars with varying width
VBAR_CHARS = "█▌║│|¦ "


def image_to_ascii(
    image: Image.Image,
    width: int = 40,
    height: int = 20,
    charset: str = "density",
    invert: bool = False,
) -> str:
    """Convert a PIL Image to ASCII art string.

    Args:
        image: Source PIL Image (any mode).
        width: Output width in characters.
        height: Output height in lines.
        charset: "density" for full range, "vbar" for vertical bar style.
        invert: If True, invert luminance (white-on-black).

    Returns:
        Multi-line ASCII string.
    """
    chars = DENSITY_CHARS if charset == "density" else VBAR_CHARS

    # Convert to grayscale
    gray = image.convert("L")

    # Resize — chars are ~2x taller than wide, so double the width sampling
    gray = gray.resize((width * 2, height), Image.Resampling.LANCZOS)

    pixels = gray.load()
    lines = []

    for y in range(height):
        line = ""
        for x in range(0, width * 2, 2):
            # Average two horizontal pixels for each character
            lum = (pixels[x, y] + pixels[x + 1, y]) / 2

            if invert:
                lum = 255 - lum

            # Map luminance (0-255) to character index
            idx = int(lum / 256 * len(chars))
            idx = min(idx, len(chars) - 1)
            line += chars[idx]

        lines.append(line)

    return "\n".join(lines)


def load_and_convert(
    path: str | Path,
    width: int = 40,
    height: int = 20,
    charset: str = "density",
    invert: bool = False,
    contrast: float = 1.5,
    brightness: float = 1.0,
) -> str:
    """Load an image file and convert to ASCII art.

    Args:
        path: Path to image file.
        width: Output width in characters.
        height: Output height in lines.
        charset: Character set to use.
        invert: Invert luminance.
        contrast: Contrast multiplier (>1 = more contrast).
        brightness: Brightness multiplier.
    """
    img = Image.open(path)

    # Enhance for better ASCII conversion
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if brightness != 1.0:
        img = ImageEnhance.Brightness(img).enhance(brightness)

    return image_to_ascii(img, width, height, charset, invert)


def generate_state_frames(
    base_image: Image.Image,
    width: int = 40,
    height: int = 20,
    charset: str = "density",
) -> dict[str, list[str]]:
    """Generate all avatar state frames from a single base portrait.

    Applies visual effects per state:
    - idle: subtle brightness pulse (3 frames)
    - thinking: scanline sweep (4 frames)
    - speaking: lower-face distortion (4 frames)
    - listening: brightened, wide-eyed (3 frames)
    - error: red glitch, displaced rows (2 frames)
    """
    gray = base_image.convert("L")

    # Enhance base for cleaner conversion
    gray = ImageEnhance.Contrast(gray).enhance(1.6)

    frames: dict[str, list[str]] = {}

    # === IDLE: brightness pulse ===
    idle_frames = []
    for brightness in [1.0, 1.05, 1.1]:
        modified = ImageEnhance.Brightness(gray).enhance(brightness)
        ascii_art = image_to_ascii(modified, width, height, charset, invert=True)
        idle_frames.append(ascii_art)
    frames["idle"] = idle_frames

    # === THINKING: scanline sweep ===
    think_frames = []
    for scan_y in range(0, height, height // 4):
        # Create scanline overlay
        modified = gray.copy()
        draw = ImageDraw.Draw(modified)
        # Bright scanline band sweeping down
        band_height = max(2, height // 8)
        y_start = int(scan_y / height * modified.size[1])
        y_end = min(y_start + band_height * (modified.size[1] // height), modified.size[1])
        draw.rectangle(
            [0, y_start, modified.size[0], y_end],
            fill=200,
        )
        ascii_art = image_to_ascii(modified, width, height, charset, invert=True)
        think_frames.append(ascii_art)
    frames["thinking"] = think_frames

    # === SPEAKING: mouth area distortion ===
    speak_frames = []
    mouth_positions = [0, 3, 6, 3]  # closed, opening, open, closing
    for offset in mouth_positions:
        modified = gray.copy()
        pixels = modified.load()
        # Distort lower third (mouth area)
        mouth_start = int(modified.size[1] * 0.6)
        mouth_end = int(modified.size[1] * 0.75)
        for y in range(mouth_start, min(mouth_end, modified.size[1])):
            for x in range(modified.size[0]):
                # Shift pixels vertically to simulate mouth opening
                src_y = y - offset
                if 0 <= src_y < modified.size[1]:
                    pixels[x, y] = pixels[x, src_y]
                else:
                    pixels[x, y] = 40  # dark fill
        ascii_art = image_to_ascii(modified, width, height, charset, invert=True)
        speak_frames.append(ascii_art)
    frames["speaking"] = speak_frames

    # === LISTENING: brightened, enhanced ===
    listen_frames = []
    for brightness in [1.15, 1.2, 1.15]:
        modified = ImageEnhance.Brightness(gray).enhance(brightness)
        modified = ImageEnhance.Contrast(modified).enhance(1.2)
        ascii_art = image_to_ascii(modified, width, height, charset, invert=True)
        listen_frames.append(ascii_art)
    frames["listening"] = listen_frames

    # === ERROR: glitch effect ===
    error_frames = []
    for glitch_intensity in [3, 6]:
        lines = image_to_ascii(gray, width, height, charset, invert=True).split("\n")
        glitched = []
        for i, line in enumerate(lines):
            if i % (7 - glitch_intensity) == 0:
                # Horizontal displacement
                shift = glitch_intensity
                line = " " * shift + line[:-shift] if len(line) > shift else line
            if i % (9 - glitch_intensity) == 0:
                # Character corruption
                chars_list = list(line)
                for j in range(0, len(chars_list), 5):
                    if j < len(chars_list):
                        chars_list[j] = "╪" if glitch_intensity > 4 else "╫"
                line = "".join(chars_list)
            glitched.append(line)
        error_frames.append("\n".join(glitched))
    frames["error"] = error_frames

    return frames
