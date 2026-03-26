import pytest
from pathlib import Path
from PIL import Image
from scripts.generate_layers import generate_backgrounds, generate_overlays


class TestProceduralLayers:
    def test_generate_backgrounds(self, tmp_path):
        generate_backgrounds(tmp_path / "background", canvas_size=(512, 512))
        for name in ["bg_dim.png", "bg_pulse.png", "bg_error.png"]:
            fpath = tmp_path / "background" / name
            assert fpath.exists(), f"Missing: {fpath}"
            img = Image.open(fpath)
            assert img.size == (512, 512)
            assert img.mode == "RGBA"

    def test_generate_overlays(self, tmp_path):
        generate_overlays(tmp_path / "overlay", canvas_size=(512, 512))
        expected = [
            "scanline_light.png", "scanline_heavy.png", "crt_bloom.png",
            "holo_flicker.png", "chrom_aberr.png", "glitch_corrupt.png",
            "noise_bands.png", "red_tint.png",
        ]
        for name in expected:
            fpath = tmp_path / "overlay" / name
            assert fpath.exists(), f"Missing: {fpath}"
            img = Image.open(fpath)
            assert img.size == (512, 512)
            assert img.mode == "RGBA"
