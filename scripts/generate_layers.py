"""Procedural asset generator for the Layered 2.5D Avatar system.

Generates all 47 layer PNGs: backgrounds, overlays, face structure,
and expression layers (eyes, eyebrows, mouth) in a bold cyberpunk style.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance


def _blank_rgba(canvas_size: tuple[int, int]) -> Image.Image:
    return Image.new("RGBA", canvas_size, (0, 0, 0, 0))


# ---------------------------------------------------------------------------
# Backgrounds
# ---------------------------------------------------------------------------

def generate_backgrounds(output_dir: Path | str, canvas_size: tuple[int, int] = (512, 512)) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    w, h = canvas_size

    # bg_dim: dark gradient + noise
    rng = np.random.default_rng(7)
    grad = np.linspace(12, 5, h, dtype=np.float32)
    arr = np.zeros((h, w, 3), dtype=np.float32)
    arr[:, :, 0] = grad[:, None]
    arr[:, :, 1] = grad[:, None]
    arr[:, :, 2] = (grad * 1.3)[:, None]
    noise = rng.integers(-3, 4, size=(h, w, 3), dtype=np.int8).astype(np.float32)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    alpha = np.full((h, w, 1), 255, dtype=np.uint8)
    Image.fromarray(np.concatenate([arr, alpha], axis=2), "RGBA").save(output_dir / "bg_dim.png")

    # bg_pulse: dark base + cyan radial glow
    cx, cy = w // 2, h // 2
    ys, xs = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2).astype(np.float32)
    max_r = np.sqrt(cx ** 2 + cy ** 2)
    glow = np.clip(1.0 - dist / (max_r * 0.5), 0, 1) ** 1.5
    base = np.zeros((h, w, 4), dtype=np.uint8)
    base[..., 0] = np.clip(5 + glow * 30, 0, 255).astype(np.uint8)
    base[..., 1] = np.clip(8 + glow * 100, 0, 255).astype(np.uint8)
    base[..., 2] = np.clip(12 + glow * 110, 0, 255).astype(np.uint8)
    base[..., 3] = 255
    Image.fromarray(base, "RGBA").save(output_dir / "bg_pulse.png")

    # bg_error: dark base + red vignette
    vign = np.clip(1.0 - dist / (max_r * 0.7), 0, 1) ** 1.2
    base2 = np.zeros((h, w, 4), dtype=np.uint8)
    base2[..., 0] = np.clip(10 + vign * 80, 0, 255).astype(np.uint8)
    base2[..., 1] = np.clip(3, 0, 255).astype(np.uint8)
    base2[..., 2] = np.clip(5 + vign * 15, 0, 255).astype(np.uint8)
    base2[..., 3] = 255
    Image.fromarray(base2, "RGBA").save(output_dir / "bg_error.png")


# ---------------------------------------------------------------------------
# Overlays
# ---------------------------------------------------------------------------

def generate_overlays(output_dir: Path | str, canvas_size: tuple[int, int] = (512, 512)) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    w, h = canvas_size

    # scanline_light
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[::4, :] = (0, 0, 0, 35)
    Image.fromarray(arr, "RGBA").save(output_dir / "scanline_light.png")

    # scanline_heavy
    arr2 = np.zeros((h, w, 4), dtype=np.uint8)
    arr2[::2, :] = (0, 0, 0, 70)
    Image.fromarray(arr2, "RGBA").save(output_dir / "scanline_heavy.png")

    # crt_bloom
    cx, cy = w // 2, h // 2
    ys, xs = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2).astype(np.float32)
    max_r = np.sqrt(cx ** 2 + cy ** 2)
    fade = np.clip(1.0 - dist / max_r, 0, 1) ** 2
    bloom = np.zeros((h, w, 4), dtype=np.uint8)
    bloom[..., 0] = (fade * 20).astype(np.uint8)
    bloom[..., 1] = (fade * 90).astype(np.uint8)
    bloom[..., 2] = (fade * 100).astype(np.uint8)
    bloom[..., 3] = (fade * 100).astype(np.uint8)
    Image.fromarray(bloom, "RGBA").save(output_dir / "crt_bloom.png")

    # holo_flicker
    rng_holo = np.random.default_rng(13)
    flicker = np.zeros((h, w, 4), dtype=np.uint8)
    for y in range(0, h, 6):
        if rng_holo.random() > 0.4:
            a = int(rng_holo.integers(15, 60))
            flicker[y:y + 3, :] = (0, 180, 200, a)
    Image.fromarray(flicker, "RGBA").save(output_dir / "holo_flicker.png")

    # chrom_aberr
    chrom = np.zeros((h, w, 4), dtype=np.uint8)
    for y in range(0, h, 12):
        chrom[y:y + 6, :] = (180, 0, 0, 25)
        y2 = y + 6
        if y2 < h:
            chrom[y2:y2 + 6, :] = (0, 180, 180, 25)
    Image.fromarray(chrom, "RGBA").save(output_dir / "chrom_aberr.png")

    # glitch_corrupt
    rng42 = np.random.default_rng(42)
    glitch = np.zeros((h, w, 4), dtype=np.uint8)
    for _ in range(40):
        bx = int(rng42.integers(0, w - 40))
        by = int(rng42.integers(0, h - 8))
        bw = int(rng42.integers(20, 120))
        bh = int(rng42.integers(2, 12))
        r, g, b = int(rng42.integers(0, 256)), int(rng42.integers(0, 256)), int(rng42.integers(0, 256))
        a = int(rng42.integers(50, 140))
        glitch[by:by + bh, bx:min(bx + bw, w)] = (r, g, b, a)
    Image.fromarray(glitch, "RGBA").save(output_dir / "glitch_corrupt.png")

    # noise_bands
    rng99 = np.random.default_rng(99)
    noise_img = np.zeros((h, w, 4), dtype=np.uint8)
    for y in range(0, h, 3):
        val = int(rng99.integers(0, 80))
        a_val = int(rng99.integers(15, 60))
        noise_img[y:y + 3, :] = (val, val, val, a_val)
    Image.fromarray(noise_img, "RGBA").save(output_dir / "noise_bands.png")

    # red_tint
    red_tint = np.full((h, w, 4), (200, 20, 20, 45), dtype=np.uint8)
    Image.fromarray(red_tint, "RGBA").save(output_dir / "red_tint.png")


# ---------------------------------------------------------------------------
# Cyberpunk Face Drawing Helpers
# ---------------------------------------------------------------------------

def _draw_glow_ellipse(draw, bbox, color, glow_color, glow_radius=6, width=3):
    """Draw an ellipse with outer glow effect."""
    for i in range(glow_radius, 0, -1):
        alpha = int(glow_color[3] * (1 - i / glow_radius) * 0.5)
        gc = (*glow_color[:3], alpha)
        expanded = [bbox[0] - i, bbox[1] - i, bbox[2] + i, bbox[3] + i]
        draw.ellipse(expanded, outline=gc, width=1)
    draw.ellipse(bbox, outline=color, width=width)


def _draw_glow_line(draw, points, color, glow_color, glow_radius=4, width=3):
    """Draw a line with outer glow."""
    for i in range(glow_radius, 0, -1):
        alpha = int(glow_color[3] * (1 - i / glow_radius) * 0.4)
        gc = (*glow_color[:3], alpha)
        draw.line(points, fill=gc, width=width + i * 2)
    draw.line(points, fill=color, width=width)


# ---------------------------------------------------------------------------
# Face Structure Layers
# ---------------------------------------------------------------------------

def generate_face_layers(
    reference: Image.Image,
    output_dir: Path | str,
    canvas_size: tuple[int, int] = (512, 512),
) -> None:
    output_dir = Path(output_dir)
    w, h = canvas_size

    # Build a detailed cyberpunk face base instead of using the raw reference
    face_base = _draw_cyberpunk_face(canvas_size)

    # face/
    face_dir = output_dir / "face"
    face_dir.mkdir(parents=True, exist_ok=True)

    face_base.save(face_dir / "face_center.png")
    # Angle variants: shift + slight perspective
    for name, x_off, scale_x in [
        ("face_left15.png", -20, 0.94),
        ("face_right15.png", 20, 0.94),
    ]:
        shifted = _blank_rgba(canvas_size)
        fw = int(w * scale_x)
        resized = face_base.resize((fw, h), Image.LANCZOS)
        shifted.paste(resized, (x_off + (w - fw) // 2, 0), resized)
        shifted.save(face_dir / name)
    for name, y_off in [("face_up10.png", -12), ("face_down10.png", 12)]:
        shifted = _blank_rgba(canvas_size)
        shifted.paste(face_base, (0, y_off), face_base)
        shifted.save(face_dir / name)

    # hair/
    hair_dir = output_dir / "hair"
    hair_dir.mkdir(parents=True, exist_ok=True)
    hair_base = _draw_cyberpunk_hair(canvas_size)
    hair_base.save(hair_dir / "hair_center.png")
    for name, x_off in [("hair_left.png", -12), ("hair_right.png", 12)]:
        shifted = _blank_rgba(canvas_size)
        shifted.paste(hair_base, (x_off, 0), hair_base)
        shifted.save(hair_dir / name)

    # nose/
    nose_dir = output_dir / "nose"
    nose_dir.mkdir(parents=True, exist_ok=True)
    nose_base = _draw_cyberpunk_nose(canvas_size)
    nose_base.save(nose_dir / "nose_center.png")
    for name, x_off in [("nose_left.png", -4), ("nose_right.png", 4)]:
        shifted = _blank_rgba(canvas_size)
        shifted.paste(nose_base, (x_off, 0), nose_base)
        shifted.save(nose_dir / name)


def _draw_cyberpunk_face(canvas_size):
    """Draw a detailed cyberpunk face outline — jawline, cheekbones, implant lines."""
    w, h = canvas_size
    img = _blank_rgba(canvas_size)
    draw = ImageDraw.Draw(img)

    cx, cy = w // 2, h // 2

    # Face oval — large, fills most of canvas
    face_w = int(w * 0.38)
    face_top = int(h * 0.12)
    face_bot = int(h * 0.82)
    face_bbox = [cx - face_w, face_top, cx + face_w, face_bot]

    # Face fill: dark with slight gradient (drawn as solid for now)
    draw.ellipse(face_bbox, fill=(18, 15, 25, 240))

    # Jawline — sharper than the oval, cyberpunk angular
    jaw_y = int(h * 0.72)
    chin_y = int(h * 0.82)
    jaw_w = int(w * 0.34)
    chin_w = int(w * 0.12)
    jaw_points = [
        (cx - jaw_w, int(h * 0.55)),  # left cheek
        (cx - jaw_w + 5, jaw_y),       # left jaw angle
        (cx - chin_w, chin_y),          # left chin
        (cx, chin_y + 8),              # chin point
        (cx + chin_w, chin_y),          # right chin
        (cx + jaw_w - 5, jaw_y),       # right jaw angle
        (cx + jaw_w, int(h * 0.55)),   # right cheek
    ]
    _draw_glow_line(draw, jaw_points, (0, 180, 170, 180), (0, 200, 200, 100), glow_radius=3, width=2)

    # Cheekbone lines — cybernetic implant look
    for side in [-1, 1]:
        cheek_x = cx + side * int(w * 0.30)
        cheek_y1 = int(h * 0.38)
        cheek_y2 = int(h * 0.52)
        _draw_glow_line(draw,
            [(cheek_x, cheek_y1), (cheek_x + side * 8, cheek_y2)],
            (80, 0, 180, 140), (120, 0, 255, 80), glow_radius=3, width=2)

    # Forehead implant — horizontal tech line
    imp_y = int(h * 0.18)
    imp_w = int(w * 0.22)
    _draw_glow_line(draw,
        [(cx - imp_w, imp_y), (cx + imp_w, imp_y)],
        (0, 160, 200, 160), (0, 200, 255, 80), glow_radius=4, width=2)
    # Implant dots
    for dx in [-imp_w, -imp_w // 2, 0, imp_w // 2, imp_w]:
        draw.ellipse([cx + dx - 3, imp_y - 3, cx + dx + 3, imp_y + 3],
                     fill=(0, 255, 220, 200))

    # Temple circuit traces
    for side in [-1, 1]:
        tx = cx + side * int(w * 0.36)
        for i, ty in enumerate(range(int(h * 0.22), int(h * 0.42), 12)):
            alpha = 180 - i * 20
            draw.rectangle([tx - 2, ty, tx + 2, ty + 6],
                          fill=(0, 200, 180, max(40, alpha)))

    return img


def _draw_cyberpunk_hair(canvas_size):
    """Draw stylized hair — flowing angular shapes."""
    w, h = canvas_size
    img = _blank_rgba(canvas_size)
    draw = ImageDraw.Draw(img)
    cx = w // 2

    # Main hair mass — dark with purple/teal highlights
    hair_points = [
        (int(w * 0.12), int(h * 0.35)),
        (int(w * 0.08), int(h * 0.20)),
        (int(w * 0.15), int(h * 0.08)),
        (int(w * 0.30), int(h * 0.03)),
        (cx, int(h * 0.01)),
        (int(w * 0.70), int(h * 0.03)),
        (int(w * 0.85), int(h * 0.08)),
        (int(w * 0.92), int(h * 0.20)),
        (int(w * 0.88), int(h * 0.35)),
        (int(w * 0.82), int(h * 0.50)),
        (int(w * 0.78), int(h * 0.60)),
        # sweep back through face area
        (int(w * 0.70), int(h * 0.30)),
        (cx, int(h * 0.12)),
        (int(w * 0.30), int(h * 0.30)),
        (int(w * 0.22), int(h * 0.60)),
        (int(w * 0.18), int(h * 0.50)),
    ]
    draw.polygon(hair_points, fill=(12, 8, 22, 230))

    # Hair highlight strands
    strand_color = (40, 15, 70, 160)
    for i in range(6):
        sx = int(w * 0.25) + i * int(w * 0.09)
        sy = int(h * 0.05) + (i % 3) * 5
        ey = int(h * 0.40) + (i % 2) * int(h * 0.15)
        draw.line([(sx, sy), (sx + (i - 3) * 8, ey)],
                  fill=strand_color, width=3)

    # Teal edge highlight
    for i in range(len(hair_points) - 1):
        p1, p2 = hair_points[i], hair_points[i + 1]
        draw.line([p1, p2], fill=(0, 100, 120, 80), width=2)

    return img


def _draw_cyberpunk_nose(canvas_size):
    """Draw a subtle nose bridge with tech accent."""
    w, h = canvas_size
    img = _blank_rgba(canvas_size)
    draw = ImageDraw.Draw(img)
    cx = w // 2

    # Nose bridge — thin vertical line
    ny1 = int(h * 0.44)
    ny2 = int(h * 0.56)
    _draw_glow_line(draw,
        [(cx, ny1), (cx, ny2)],
        (0, 140, 130, 120), (0, 180, 170, 60), glow_radius=2, width=2)

    # Nostrils — small dots
    nostril_y = int(h * 0.555)
    for dx in [-12, 12]:
        draw.ellipse([cx + dx - 4, nostril_y - 3, cx + dx + 4, nostril_y + 3],
                     fill=(0, 120, 110, 100))

    return img


# ---------------------------------------------------------------------------
# Expression Layers — BOLD cyberpunk style
# ---------------------------------------------------------------------------

def generate_expression_layers(
    output_dir: Path | str,
    canvas_size: tuple[int, int] = (512, 512),
) -> None:
    output_dir = Path(output_dir)
    w, h = canvas_size

    # Eye geometry — LARGE, prominent
    eye_cy = int(h * 0.36)
    left_cx = int(w * 0.33)
    right_cx = int(w * 0.67)
    eye_rx = int(w * 0.12)   # wide
    eye_ry_open = int(h * 0.07)
    eye_ry_half = int(h * 0.035)
    pupil_r = int(min(eye_rx, eye_ry_open) * 0.5)
    iris_r = int(min(eye_rx, eye_ry_open) * 0.75)

    # Colors
    CYAN = (0, 240, 220, 255)
    CYAN_GLOW = (0, 200, 255, 120)
    DARK = (5, 8, 15, 255)
    IRIS_COLOR = (0, 200, 200, 255)
    PUPIL_COLOR = (0, 255, 240, 255)
    HIGHLIGHT = (255, 255, 255, 240)
    TEAL = (0, 180, 160, 255)
    TEAL_GLOW = (0, 200, 180, 100)
    RED_GLOW = (255, 0, 50, 100)

    pupil_offsets = {
        "center": (0, 0),
        "left": (-int(eye_rx * 0.35), 0),
        "right": (int(eye_rx * 0.35), 0),
        "up": (0, -int(eye_ry_open * 0.35)),
        "down": (0, int(eye_ry_open * 0.35)),
    }

    # ---- eyes/ ----
    eyes_dir = output_dir / "eyes"
    eyes_dir.mkdir(parents=True, exist_ok=True)

    for direction, (px_off, py_off) in pupil_offsets.items():
        for state in ["open", "half", "closed"]:
            img = _blank_rgba(canvas_size)
            draw = ImageDraw.Draw(img)

            if state == "closed":
                # Glowing horizontal lines where eyes are
                for ecx in [left_cx, right_cx]:
                    _draw_glow_line(draw,
                        [(ecx - eye_rx, eye_cy), (ecx + eye_rx, eye_cy)],
                        CYAN, CYAN_GLOW, glow_radius=6, width=3)
                    # Small lash marks
                    for dx in range(-eye_rx + 8, eye_rx, 14):
                        draw.line([(ecx + dx, eye_cy), (ecx + dx, eye_cy + 6)],
                                  fill=(0, 180, 170, 120), width=1)
            else:
                ery = eye_ry_open if state == "open" else eye_ry_half

                for ecx in [left_cx, right_cx]:
                    bbox = [ecx - eye_rx, eye_cy - ery, ecx + eye_rx, eye_cy + ery]

                    # Outer glow
                    _draw_glow_ellipse(draw, bbox, CYAN, CYAN_GLOW,
                                       glow_radius=8, width=3)

                    # Eye fill
                    inner = [bbox[0] + 3, bbox[1] + 3, bbox[2] - 3, bbox[3] - 3]
                    draw.ellipse(inner, fill=DARK)

                    if state == "open":
                        # Iris ring
                        ir = min(iris_r, ery - 4)
                        iris_bbox = [
                            ecx + px_off - ir, eye_cy + py_off - ir,
                            ecx + px_off + ir, eye_cy + py_off + ir,
                        ]
                        draw.ellipse(iris_bbox, outline=IRIS_COLOR, width=3)

                        # Inner iris gradient (smaller ring)
                        ir2 = int(ir * 0.7)
                        draw.ellipse([
                            ecx + px_off - ir2, eye_cy + py_off - ir2,
                            ecx + px_off + ir2, eye_cy + py_off + ir2,
                        ], outline=(0, 160, 160, 180), width=2)

                    # Pupil (bright center)
                    pr = pupil_r if state == "open" else int(pupil_r * 0.7)
                    draw.ellipse([
                        ecx + px_off - pr, eye_cy + py_off - pr,
                        ecx + px_off + pr, eye_cy + py_off + pr,
                    ], fill=PUPIL_COLOR)

                    # Specular highlight
                    hl_r = max(2, pr // 2)
                    hl_x = ecx + px_off - int(pr * 0.3)
                    hl_y = eye_cy + py_off - int(pr * 0.4)
                    draw.ellipse([hl_x - hl_r, hl_y - hl_r, hl_x + hl_r, hl_y + hl_r],
                                 fill=HIGHLIGHT)

                    # Secondary highlight (smaller, opposite side)
                    hl2_r = max(1, hl_r // 2)
                    hl2_x = ecx + px_off + int(pr * 0.3)
                    hl2_y = eye_cy + py_off + int(pr * 0.2)
                    draw.ellipse([hl2_x - hl2_r, hl2_y - hl2_r, hl2_x + hl2_r, hl2_y + hl2_r],
                                 fill=(200, 255, 255, 160))

                    # Tech detail: small circuit dots along eye rim
                    if state == "open":
                        for angle_deg in range(0, 360, 45):
                            rad = math.radians(angle_deg)
                            dx = int(eye_rx * math.cos(rad))
                            dy = int(ery * math.sin(rad))
                            dot_x = ecx + dx
                            dot_y = eye_cy + dy
                            draw.ellipse([dot_x - 1, dot_y - 1, dot_x + 1, dot_y + 1],
                                         fill=(0, 200, 200, 100))

            img.save(eyes_dir / f"eyes_{direction}_{state}.png")

    # ---- eyebrows/ ----
    brows_dir = output_dir / "eyebrows"
    brows_dir.mkdir(parents=True, exist_ok=True)

    brow_y = eye_cy - int(h * 0.10)
    brow_hw = int(w * 0.13)
    brow_thick = max(3, int(h * 0.018))

    def _draw_brows(fname, left_inner_dy, left_outer_dy, right_inner_dy, right_outer_dy):
        img = _blank_rgba(canvas_size)
        draw = ImageDraw.Draw(img)
        # Left brow (outer to inner = left to right)
        _draw_glow_line(draw,
            [(left_cx - brow_hw, brow_y + left_outer_dy),
             (left_cx + brow_hw, brow_y + left_inner_dy)],
            TEAL, TEAL_GLOW, glow_radius=5, width=brow_thick)
        # Right brow (inner to outer = left to right)
        _draw_glow_line(draw,
            [(right_cx - brow_hw, brow_y + right_inner_dy),
             (right_cx + brow_hw, brow_y + right_outer_dy)],
            TEAL, TEAL_GLOW, glow_radius=5, width=brow_thick)
        img.save(brows_dir / fname)

    _draw_brows("brows_neutral.png", 0, 0, 0, 0)
    lift = int(h * 0.04)
    _draw_brows("brows_raised.png", -lift, -int(lift * 0.5), -int(lift * 0.5), -lift)
    furrow = int(h * 0.035)
    _draw_brows("brows_furrowed.png", furrow, -int(furrow * 0.3), furrow, -int(furrow * 0.3))
    _draw_brows("brows_asymmetric.png", -lift, -int(lift * 0.3), 0, int(furrow * 0.3))

    # ---- mouth/ ----
    mouth_dir = output_dir / "mouth"
    mouth_dir.mkdir(parents=True, exist_ok=True)

    mouth_cy = int(h * 0.64)
    mouth_hw = int(w * 0.14)
    mouth_thick = max(3, int(h * 0.015))

    # closed: glowing horizontal line
    img = _blank_rgba(canvas_size)
    draw = ImageDraw.Draw(img)
    _draw_glow_line(draw,
        [(w // 2 - mouth_hw, mouth_cy), (w // 2 + mouth_hw, mouth_cy)],
        TEAL, TEAL_GLOW, glow_radius=5, width=mouth_thick)
    img.save(mouth_dir / "mouth_closed.png")

    # slight, open, wide: ellipses of increasing size with glow
    for fname, ry_frac in [("mouth_slight.png", 0.025), ("mouth_open.png", 0.055), ("mouth_wide.png", 0.085)]:
        img = _blank_rgba(canvas_size)
        draw = ImageDraw.Draw(img)
        m_ry = int(h * ry_frac)
        bbox = [w // 2 - mouth_hw, mouth_cy - m_ry, w // 2 + mouth_hw, mouth_cy + m_ry]
        # Dark interior
        inner = [bbox[0] + 3, bbox[1] + 3, bbox[2] - 3, bbox[3] - 3]
        draw.ellipse(inner, fill=(5, 5, 10, 220))
        # Glowing outline
        _draw_glow_ellipse(draw, bbox, TEAL, TEAL_GLOW, glow_radius=6, width=mouth_thick)
        # Teeth hint for wide
        if ry_frac >= 0.08:
            teeth_y = mouth_cy - int(m_ry * 0.3)
            draw.line([(w // 2 - mouth_hw + 15, teeth_y), (w // 2 + mouth_hw - 15, teeth_y)],
                      fill=(60, 60, 70, 180), width=2)
        img.save(mouth_dir / fname)

    # smile: curved arc with glow
    img = _blank_rgba(canvas_size)
    draw = ImageDraw.Draw(img)
    arc_ry = int(h * 0.04)
    arc_bbox = [w // 2 - mouth_hw, mouth_cy - arc_ry, w // 2 + mouth_hw, mouth_cy + arc_ry]
    # Glow pass
    for i in range(5, 0, -1):
        alpha = int(80 * (1 - i / 5))
        expanded = [arc_bbox[0] - i, arc_bbox[1] - i, arc_bbox[2] + i, arc_bbox[3] + i]
        draw.arc(expanded, start=5, end=175, fill=(*TEAL_GLOW[:3], alpha), width=2)
    draw.arc(arc_bbox, start=5, end=175, fill=TEAL, width=mouth_thick)
    img.save(mouth_dir / "mouth_smile.png")

    # glitch: jagged broken line with red/cyan
    img = _blank_rgba(canvas_size)
    draw = ImageDraw.Draw(img)
    rng77 = random.Random(77)
    segments = 12
    step = mouth_hw * 2 // segments
    x = w // 2 - mouth_hw
    points = [(x, mouth_cy)]
    for i in range(segments):
        x += step
        y = mouth_cy + rng77.randint(-int(h * 0.04), int(h * 0.04))
        points.append((x, y))
    # Draw with alternating red/cyan
    for i in range(len(points) - 1):
        color = (255, 0, 80, 220) if i % 2 == 0 else (0, 255, 200, 220)
        draw.line([points[i], points[i + 1]], fill=color, width=mouth_thick)
    # Glitch artifacts
    for _ in range(5):
        gx = rng77.randint(w // 2 - mouth_hw, w // 2 + mouth_hw)
        gy = rng77.randint(mouth_cy - int(h * 0.04), mouth_cy + int(h * 0.04))
        draw.rectangle([gx, gy, gx + rng77.randint(5, 20), gy + 3],
                       fill=(255, 0, 80, 150))
    img.save(mouth_dir / "mouth_glitch.png")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate layered avatar assets")
    parser.add_argument("--output", type=Path, default=Path("assets/layers"))
    parser.add_argument("--canvas-size", type=int, default=512)
    parser.add_argument("--reference", type=Path, default=None)
    args = parser.parse_args()

    canvas = (args.canvas_size, args.canvas_size)

    print("Generating backgrounds...")
    generate_backgrounds(args.output / "background", canvas_size=canvas)

    print("Generating overlays...")
    generate_overlays(args.output / "overlay", canvas_size=canvas)

    if args.reference and args.reference.exists():
        ref_img = Image.open(args.reference).convert("RGB")
    else:
        ref_img = Image.new("RGB", canvas, (30, 20, 40))

    print("Generating face layers...")
    generate_face_layers(ref_img, args.output, canvas_size=canvas)

    print("Generating expression layers...")
    generate_expression_layers(args.output, canvas_size=canvas)

    count = sum(1 for _ in args.output.rglob("*.png"))
    print(f"Done. {count} PNGs generated.")


if __name__ == "__main__":
    main()
