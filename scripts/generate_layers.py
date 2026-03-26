"""Procedural asset generator for backgrounds, overlays, face, and expression layers (Layered 2.5D Avatar)."""

from __future__ import annotations

import argparse
import math
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
# Face Layers
# ---------------------------------------------------------------------------

def _paste_region_onto_canvas(
    region: Image.Image,
    canvas_size: tuple[int, int],
    offset: tuple[int, int] = (0, 0),
    scale: tuple[float, float] = (1.0, 1.0),
) -> Image.Image:
    """Paste a region image onto a blank RGBA canvas with optional offset and scale."""
    canvas = _blank_rgba(canvas_size)
    w, h = region.size
    new_w = max(1, int(w * scale[0]))
    new_h = max(1, int(h * scale[1]))
    resized = region.resize((new_w, new_h), Image.LANCZOS)
    paste_x = offset[0] + (w - new_w) // 2
    paste_y = offset[1] + (h - new_h) // 2
    canvas.paste(resized, (paste_x, paste_y), resized if resized.mode == "RGBA" else None)
    return canvas


def generate_face_layers(
    reference: Image.Image,
    output_dir: Path | str,
    canvas_size: tuple[int, int] = (512, 512),
) -> None:
    """Generate face, hair, and nose layers from a reference PIL Image."""
    output_dir = Path(output_dir)
    w, h = canvas_size

    # Convert reference to RGBA at canvas_size
    ref = reference.convert("RGBA").resize(canvas_size, Image.LANCZOS)

    # ---- face/ ----
    face_dir = output_dir / "face"
    face_dir.mkdir(parents=True, exist_ok=True)

    # Extract center 60% of image as face region
    fx0 = int(w * 0.20)
    fy0 = int(h * 0.20)
    fx1 = int(w * 0.80)
    fy1 = int(h * 0.80)
    face_region = ref.crop((fx0, fy0, fx1, fy1))

    def _face_canvas(offset_x: int = 0, offset_y: int = 0, scale_x: float = 1.0) -> Image.Image:
        canvas = _blank_rgba(canvas_size)
        rw, rh = face_region.size
        new_w = max(1, int(rw * scale_x))
        resized = face_region.resize((new_w, rh), Image.LANCZOS)
        px = fx0 + offset_x + (rw - new_w) // 2
        py = fy0 + offset_y
        canvas.paste(resized, (px, py), resized)
        return canvas

    _face_canvas().save(face_dir / "face_center.png")
    _face_canvas(offset_x=-15, scale_x=0.95).save(face_dir / "face_left15.png")
    _face_canvas(offset_x=15, scale_x=0.95).save(face_dir / "face_right15.png")
    _face_canvas(offset_y=-8).save(face_dir / "face_up10.png")
    _face_canvas(offset_y=8).save(face_dir / "face_down10.png")

    # ---- hair/ ----
    hair_dir = output_dir / "hair"
    hair_dir.mkdir(parents=True, exist_ok=True)

    # Extract top 40% of image
    hy1 = int(h * 0.40)
    hair_region = ref.crop((0, 0, w, hy1))

    def _hair_canvas(offset_x: int = 0) -> Image.Image:
        canvas = _blank_rgba(canvas_size)
        rw, rh = hair_region.size
        canvas.paste(hair_region, (offset_x, 0), hair_region)
        return canvas

    _hair_canvas().save(hair_dir / "hair_center.png")
    _hair_canvas(offset_x=-8).save(hair_dir / "hair_left.png")
    _hair_canvas(offset_x=8).save(hair_dir / "hair_right.png")

    # ---- nose/ ----
    nose_dir = output_dir / "nose"
    nose_dir.mkdir(parents=True, exist_ok=True)

    # Extract small center region (nose: ~40-60% x, ~45-60% y)
    nx0 = int(w * 0.40)
    ny0 = int(h * 0.45)
    nx1 = int(w * 0.60)
    ny1 = int(h * 0.60)
    nose_region = ref.crop((nx0, ny0, nx1, ny1))

    def _nose_canvas(offset_x: int = 0) -> Image.Image:
        canvas = _blank_rgba(canvas_size)
        canvas.paste(nose_region, (nx0 + offset_x, ny0), nose_region)
        return canvas

    _nose_canvas().save(nose_dir / "nose_center.png")
    _nose_canvas(offset_x=-3).save(nose_dir / "nose_left.png")
    _nose_canvas(offset_x=3).save(nose_dir / "nose_right.png")


# ---------------------------------------------------------------------------
# Expression Layers
# ---------------------------------------------------------------------------

def generate_expression_layers(
    output_dir: Path | str,
    canvas_size: tuple[int, int] = (512, 512),
) -> None:
    """Generate cyberpunk-style eyes, eyebrows, and mouth expression layers."""
    output_dir = Path(output_dir)
    w, h = canvas_size

    # Eye positions: ~38% down, at 32% and 68% horizontal
    eye_cy = int(h * 0.38)
    left_eye_cx = int(w * 0.32)
    right_eye_cx = int(w * 0.68)
    eye_rx = int(w * 0.07)   # horizontal radius
    eye_ry = int(h * 0.055)  # vertical radius (open)
    pupil_r = max(2, int(min(eye_rx, eye_ry) * 0.45))

    # Pupil offsets per direction
    direction_offsets = {
        "center": (0, 0),
        "left": (-int(eye_rx * 0.4), 0),
        "right": (int(eye_rx * 0.4), 0),
        "up": (0, -int(eye_ry * 0.35)),
        "down": (0, int(eye_ry * 0.35)),
    }

    # ---- eyes/ ----
    eyes_dir = output_dir / "eyes"
    eyes_dir.mkdir(parents=True, exist_ok=True)

    CYAN_OUTLINE = (0, 230, 230, 255)
    EYE_FILL = (5, 10, 15, 255)
    PUPIL_COLOR = (0, 255, 255, 255)
    HIGHLIGHT = (255, 255, 255, 220)

    for direction, (px_off, py_off) in direction_offsets.items():
        for state in ["open", "half", "closed"]:
            img = _blank_rgba(canvas_size)
            draw = ImageDraw.Draw(img)

            # State determines eye vertical radius
            if state == "open":
                ery = eye_ry
            elif state == "half":
                ery = max(2, eye_ry // 2)
            else:  # closed
                ery = max(1, eye_ry // 8)

            for cx in (left_eye_cx, right_eye_cx):
                # Eye white/outline ellipse
                draw.ellipse(
                    [cx - eye_rx, eye_cy - ery, cx + eye_rx, eye_cy + ery],
                    fill=EYE_FILL,
                    outline=CYAN_OUTLINE,
                    width=2,
                )
                if state != "closed":
                    # Pupil
                    draw.ellipse(
                        [
                            cx + px_off - pupil_r,
                            eye_cy + py_off - pupil_r,
                            cx + px_off + pupil_r,
                            eye_cy + py_off + pupil_r,
                        ],
                        fill=PUPIL_COLOR,
                    )
                    # Highlight dot
                    hl_r = max(1, pupil_r // 3)
                    draw.ellipse(
                        [
                            cx + px_off - hl_r - 1,
                            eye_cy + py_off - pupil_r + 1,
                            cx + px_off + hl_r - 1,
                            eye_cy + py_off - pupil_r + 1 + hl_r * 2,
                        ],
                        fill=HIGHLIGHT,
                    )

            img.save(eyes_dir / f"eyes_{direction}_{state}.png")

    # ---- eyebrows/ ----
    brows_dir = output_dir / "eyebrows"
    brows_dir.mkdir(parents=True, exist_ok=True)

    BROW_COLOR = (0, 180, 160, 255)
    brow_y = eye_cy - int(h * 0.07)  # above eyes
    brow_half_w = int(w * 0.08)
    brow_thickness = max(2, int(h * 0.012))

    def _draw_brow(draw: ImageDraw.ImageDraw, cx: int, y_left: int, y_right: int) -> None:
        x0 = cx - brow_half_w
        x1 = cx + brow_half_w
        draw.line([(x0, y_left), (x1, y_right)], fill=BROW_COLOR, width=brow_thickness)

    # neutral: flat
    img = _blank_rgba(canvas_size)
    draw = ImageDraw.Draw(img)
    for cx in (left_eye_cx, right_eye_cx):
        _draw_brow(draw, cx, brow_y, brow_y)
    img.save(brows_dir / "brows_neutral.png")

    # raised: angled upward (inner higher)
    img = _blank_rgba(canvas_size)
    draw = ImageDraw.Draw(img)
    lift = int(h * 0.025)
    _draw_brow(draw, left_eye_cx, brow_y - lift, brow_y)
    _draw_brow(draw, right_eye_cx, brow_y, brow_y - lift)
    img.save(brows_dir / "brows_raised.png")

    # furrowed: angled downward toward center
    img = _blank_rgba(canvas_size)
    draw = ImageDraw.Draw(img)
    furrow = int(h * 0.02)
    _draw_brow(draw, left_eye_cx, brow_y, brow_y - furrow)
    _draw_brow(draw, right_eye_cx, brow_y - furrow, brow_y)
    img.save(brows_dir / "brows_furrowed.png")

    # asymmetric: left raised, right neutral
    img = _blank_rgba(canvas_size)
    draw = ImageDraw.Draw(img)
    _draw_brow(draw, left_eye_cx, brow_y - int(h * 0.03), brow_y - int(h * 0.01))
    _draw_brow(draw, right_eye_cx, brow_y, brow_y)
    img.save(brows_dir / "brows_asymmetric.png")

    # ---- mouth/ ----
    mouth_dir = output_dir / "mouth"
    mouth_dir.mkdir(parents=True, exist_ok=True)

    MOUTH_COLOR = (0, 200, 180, 255)
    mouth_cy = int(h * 0.62)
    mouth_half_w = int(w * 0.12)
    mouth_thickness = max(2, int(h * 0.012))

    # closed: thin horizontal line
    img = _blank_rgba(canvas_size)
    draw = ImageDraw.Draw(img)
    draw.line(
        [(w // 2 - mouth_half_w, mouth_cy), (w // 2 + mouth_half_w, mouth_cy)],
        fill=MOUTH_COLOR,
        width=mouth_thickness,
    )
    img.save(mouth_dir / "mouth_closed.png")

    # slight: thin ellipse
    for fname, m_ry in [("mouth_slight.png", int(h * 0.015)), ("mouth_open.png", int(h * 0.035)), ("mouth_wide.png", int(h * 0.06))]:
        img = _blank_rgba(canvas_size)
        draw = ImageDraw.Draw(img)
        draw.ellipse(
            [w // 2 - mouth_half_w, mouth_cy - m_ry, w // 2 + mouth_half_w, mouth_cy + m_ry],
            outline=MOUTH_COLOR,
            width=mouth_thickness,
        )
        img.save(mouth_dir / fname)

    # smile: arc
    img = _blank_rgba(canvas_size)
    draw = ImageDraw.Draw(img)
    arc_box = [
        w // 2 - mouth_half_w,
        mouth_cy - int(h * 0.04),
        w // 2 + mouth_half_w,
        mouth_cy + int(h * 0.04),
    ]
    draw.arc(arc_box, start=10, end=170, fill=MOUTH_COLOR, width=mouth_thickness)
    img.save(mouth_dir / "mouth_smile.png")

    # glitch: jagged random lines (seed=77)
    img = _blank_rgba(canvas_size)
    draw = ImageDraw.Draw(img)
    rng77 = random.Random(77)
    x = w // 2 - mouth_half_w
    y = mouth_cy
    points = [(x, y)]
    step = mouth_half_w * 2 // 8
    for i in range(8):
        x += step
        y = mouth_cy + rng77.randint(-int(h * 0.025), int(h * 0.025))
        points.append((x, y))
    draw.line(points, fill=MOUTH_COLOR, width=mouth_thickness)
    img.save(mouth_dir / "mouth_glitch.png")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate procedural background/overlay/face/expression assets.")
    parser.add_argument("--output", type=Path, default=Path("assets/layers"),
                        help="Output directory (default: assets/layers)")
    parser.add_argument("--canvas-size", type=int, default=512,
                        help="Canvas width and height in pixels (default: 512)")
    parser.add_argument("--reference", type=Path, default=None,
                        help="Reference face image for face layers (default: generated placeholder)")
    args = parser.parse_args()

    canvas = (args.canvas_size, args.canvas_size)
    bg_dir = args.output / "background"
    ov_dir = args.output / "overlay"
    face_dir = args.output
    expr_dir = args.output

    print(f"Generating backgrounds → {bg_dir}")
    generate_backgrounds(bg_dir, canvas_size=canvas)

    print(f"Generating overlays   → {ov_dir}")
    generate_overlays(ov_dir, canvas_size=canvas)

    # Build or load reference image
    if args.reference and args.reference.exists():
        print(f"Loading reference face → {args.reference}")
        ref_img = Image.open(args.reference).convert("RGB")
    else:
        print("Generating placeholder reference face...")
        w, h = canvas
        ref_img = Image.new("RGB", canvas, (180, 140, 120))
        draw = ImageDraw.Draw(ref_img)
        draw.ellipse([int(w * 0.15), int(h * 0.05), int(w * 0.85), int(h * 0.95)], fill=(200, 160, 140))

    print(f"Generating face layers → {face_dir}")
    generate_face_layers(ref_img, face_dir, canvas_size=canvas)

    print(f"Generating expression layers → {expr_dir}")
    generate_expression_layers(expr_dir, canvas_size=canvas)

    print("Done.")


if __name__ == "__main__":
    main()
