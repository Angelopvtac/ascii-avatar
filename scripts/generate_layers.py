"""Procedural asset generator for backgrounds and overlays (Layered 2.5D Avatar)."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def _blank_rgba(canvas_size: tuple[int, int]) -> Image.Image:
    """Return a fully transparent RGBA canvas."""
    return Image.new("RGBA", canvas_size, (0, 0, 0, 0))


# ---------------------------------------------------------------------------
# Backgrounds
# ---------------------------------------------------------------------------

def generate_backgrounds(output_dir: Path | str, canvas_size: tuple[int, int] = (512, 512)) -> None:
    """Generate 3 background PNGs into *output_dir*."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    w, h = canvas_size

    # --- bg_dim.png: dark gradient + subtle noise ---
    rng = np.random.default_rng(7)
    # Vertical gradient from ~10,10,15 at top to ~5,5,8 at bottom
    grad_r = np.linspace(10, 5, h, dtype=np.float32)
    grad_g = np.linspace(10, 5, h, dtype=np.float32)
    grad_b = np.linspace(15, 8, h, dtype=np.float32)
    noise = rng.integers(0, 8, size=(h, w, 3), dtype=np.uint8)
    arr = np.stack([grad_r, grad_g, grad_b], axis=1)  # (h, 3)
    arr = np.broadcast_to(arr[:, np.newaxis, :], (h, w, 3)).copy().astype(np.uint8)
    arr = np.clip(arr.astype(np.int16) + noise - 4, 0, 255).astype(np.uint8)
    alpha = np.full((h, w, 1), 255, dtype=np.uint8)
    rgba = np.concatenate([arr, alpha], axis=2)
    Image.fromarray(rgba, "RGBA").save(output_dir / "bg_dim.png")

    # --- bg_pulse.png: dark base + cyan radial glow at center ---
    base = np.zeros((h, w, 4), dtype=np.uint8)
    base[..., 3] = 255
    cx, cy = w // 2, h // 2
    ys, xs = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2).astype(np.float32)
    max_r = np.sqrt(cx ** 2 + cy ** 2)
    glow = np.clip(1.0 - dist / (max_r * 0.6), 0, 1) ** 2
    base[..., 0] = np.clip(5 + glow * 20, 0, 255).astype(np.uint8)   # R
    base[..., 1] = np.clip(5 + glow * 80, 0, 255).astype(np.uint8)   # G (cyan)
    base[..., 2] = np.clip(8 + glow * 80, 0, 255).astype(np.uint8)   # B (cyan)
    Image.fromarray(base, "RGBA").save(output_dir / "bg_pulse.png")

    # --- bg_error.png: dark base + red vignette ---
    base2 = np.zeros((h, w, 4), dtype=np.uint8)
    base2[..., 3] = 255
    vign = np.clip(dist / max_r, 0, 1) ** 1.5  # stronger at edges
    base2[..., 0] = np.clip(8 + vign * 60, 0, 255).astype(np.uint8)  # R
    base2[..., 1] = np.clip(5, 0, 255).astype(np.uint8)               # G
    base2[..., 2] = np.clip(5, 0, 255).astype(np.uint8)               # B
    Image.fromarray(base2, "RGBA").save(output_dir / "bg_error.png")


# ---------------------------------------------------------------------------
# Overlays
# ---------------------------------------------------------------------------

def generate_overlays(output_dir: Path | str, canvas_size: tuple[int, int] = (512, 512)) -> None:
    """Generate 8 overlay PNGs into *output_dir*."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    w, h = canvas_size

    # --- scanline_light.png: horizontal lines every 4px, alpha=40 ---
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[::4, :] = (255, 255, 255, 40)
    Image.fromarray(arr, "RGBA").save(output_dir / "scanline_light.png")

    # --- scanline_heavy.png: horizontal lines every 2px, alpha=80 ---
    arr2 = np.zeros((h, w, 4), dtype=np.uint8)
    arr2[::2, :] = (255, 255, 255, 80)
    Image.fromarray(arr2, "RGBA").save(output_dir / "scanline_heavy.png")

    # --- crt_bloom.png: cyan radial glow fading from center ---
    cx, cy = w // 2, h // 2
    ys, xs = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2).astype(np.float32)
    max_r = np.sqrt(cx ** 2 + cy ** 2)
    fade = np.clip(1.0 - dist / max_r, 0, 1) ** 2
    bloom = np.zeros((h, w, 4), dtype=np.uint8)
    bloom[..., 1] = (fade * 80).astype(np.uint8)   # G
    bloom[..., 2] = (fade * 80).astype(np.uint8)   # B
    bloom[..., 3] = (fade * 120).astype(np.uint8)  # A
    Image.fromarray(bloom, "RGBA").save(output_dir / "crt_bloom.png")

    # --- holo_flicker.png: random horizontal bands with cyan tint ---
    rng_holo = np.random.default_rng(13)
    flicker = np.zeros((h, w, 4), dtype=np.uint8)
    band_h = 8
    for y in range(0, h, band_h):
        if rng_holo.random() > 0.5:
            alpha_val = int(rng_holo.integers(10, 50))
            flicker[y:y + band_h, :] = (0, 200, 200, alpha_val)
    Image.fromarray(flicker, "RGBA").save(output_dir / "holo_flicker.png")

    # --- chrom_aberr.png: red/cyan horizontal offset bands ---
    chrom = np.zeros((h, w, 4), dtype=np.uint8)
    band_h2 = 16
    for y in range(0, h, band_h2 * 2):
        chrom[y:y + band_h2, :, 0] = 180   # R band
        chrom[y:y + band_h2, :, 3] = 30
        y2 = y + band_h2
        if y2 < h:
            chrom[y2:y2 + band_h2, :, 1] = 180  # G
            chrom[y2:y2 + band_h2, :, 2] = 180  # B (cyan)
            chrom[y2:y2 + band_h2, :, 3] = 30
    Image.fromarray(chrom, "RGBA").save(output_dir / "chrom_aberr.png")

    # --- glitch_corrupt.png: random block artifacts (seed=42) ---
    rng42 = np.random.default_rng(42)
    glitch = np.zeros((h, w, 4), dtype=np.uint8)
    for _ in range(30):
        bx = int(rng42.integers(0, w - 40))
        by = int(rng42.integers(0, h - 8))
        bw = int(rng42.integers(10, 80))
        bh = int(rng42.integers(2, 10))
        r = int(rng42.integers(0, 256))
        g = int(rng42.integers(0, 256))
        b = int(rng42.integers(0, 256))
        a = int(rng42.integers(40, 120))
        glitch[by:by + bh, bx:bx + bw] = (r, g, b, a)
    Image.fromarray(glitch, "RGBA").save(output_dir / "glitch_corrupt.png")

    # --- noise_bands.png: horizontal noise stripes (seed=99) ---
    rng99 = np.random.default_rng(99)
    noise_img = np.zeros((h, w, 4), dtype=np.uint8)
    stripe_h = 4
    for y in range(0, h, stripe_h):
        val = int(rng99.integers(0, 60))
        a_val = int(rng99.integers(10, 50))
        noise_img[y:y + stripe_h, :, 0] = val
        noise_img[y:y + stripe_h, :, 1] = val
        noise_img[y:y + stripe_h, :, 2] = val
        noise_img[y:y + stripe_h, :, 3] = a_val
    Image.fromarray(noise_img, "RGBA").save(output_dir / "noise_bands.png")

    # --- red_tint.png: full-canvas red overlay at low opacity ---
    red_tint = np.full((h, w, 4), (200, 20, 20, 35), dtype=np.uint8)
    Image.fromarray(red_tint, "RGBA").save(output_dir / "red_tint.png")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate procedural background/overlay assets.")
    parser.add_argument("--output", type=Path, default=Path("assets/layers"),
                        help="Output directory (default: assets/layers)")
    parser.add_argument("--canvas-size", type=int, default=512,
                        help="Canvas width and height in pixels (default: 512)")
    args = parser.parse_args()

    canvas = (args.canvas_size, args.canvas_size)
    bg_dir = args.output / "background"
    ov_dir = args.output / "overlay"

    print(f"Generating backgrounds → {bg_dir}")
    generate_backgrounds(bg_dir, canvas_size=canvas)

    print(f"Generating overlays   → {ov_dir}")
    generate_overlays(ov_dir, canvas_size=canvas)

    print("Done.")


if __name__ == "__main__":
    main()
