import pytest
from pathlib import Path
from PIL import Image

from avatar.frames.layered import LAYER_DEFS, STATE_FRAME_MAP, PARALLAX_OFFSETS, LayerCompositor, CANVAS_SIZE


@pytest.fixture
def mock_assets(tmp_path):
    """Create minimal 32x32 RGBA PNGs for every layer variant in LAYER_DEFS.

    Images have a distinct bright pixel at (0, 0) so that parallax shifts
    (which move layers horizontally) produce visibly different composites
    for left vs right head angles.
    """
    for layer_name, layer_def in LAYER_DEFS.items():
        for variant in layer_def["variants"]:
            file_path = tmp_path / variant["file"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            img = Image.new("RGBA", (32, 32), (128, 128, 128, 200))
            # Place a bright opaque pixel at the left edge to make shifts detectable
            img.putpixel((0, 16), (255, 255, 255, 255))
            img.save(file_path)
    return tmp_path


class TestLayerCompositor:
    def test_load_layers(self, mock_assets):
        compositor = LayerCompositor(mock_assets, canvas_size=(32, 32))
        assert len(compositor.layers) == 8
        for layer_name in LAYER_DEFS:
            assert layer_name in compositor.layers
            expected_variants = {v["name"] for v in LAYER_DEFS[layer_name]["variants"]}
            assert set(compositor.layers[layer_name].keys()) == expected_variants

    def test_composite_single_combo(self, mock_assets):
        compositor = LayerCompositor(mock_assets, canvas_size=(32, 32))
        combo = {
            "background": "dim",
            "hair": "center",
            "face": "center",
            "eyes": "center_open",
            "eyebrows": "neutral",
            "nose": "center",
            "mouth": "closed",
            "overlay": "scanline_light",
        }
        result = compositor.composite(combo, "center")
        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"
        assert result.size == (32, 32)

    def test_parallax_shifts_differ_by_head_angle(self, mock_assets):
        compositor = LayerCompositor(mock_assets, canvas_size=(32, 32))
        combo = {
            "background": "dim",
            "hair": "center",
            "face": "center",
            "eyes": "center_open",
            "eyebrows": "neutral",
            "nose": "center",
            "mouth": "closed",
            "overlay": "scanline_light",
        }
        img_left = compositor.composite(combo, "left")
        img_right = compositor.composite(combo, "right")
        assert list(img_left.getdata()) != list(img_right.getdata())


class TestLayerConfig:
    def test_layer_defs_has_all_layers(self):
        expected = ["background", "hair", "face", "eyes", "eyebrows", "nose", "mouth", "overlay"]
        assert list(LAYER_DEFS.keys()) == expected

    def test_each_layer_has_variants(self):
        for name, layer in LAYER_DEFS.items():
            assert len(layer["variants"]) >= 1, f"{name} needs at least 1 variant"

    def test_parallax_offsets_match_layers(self):
        for name in LAYER_DEFS:
            assert name in PARALLAX_OFFSETS, f"Missing parallax offset for {name}"

    def test_state_frame_map_has_all_states(self):
        for state in ["idle", "thinking", "speaking", "listening", "error"]:
            assert state in STATE_FRAME_MAP, f"Missing state: {state}"

    def test_state_frame_map_references_valid_variants(self):
        for state, combos in STATE_FRAME_MAP.items():
            assert len(combos) >= 1, f"{state} needs at least 1 frame combo"
            for combo in combos:
                for layer_name, variant_name in combo.items():
                    assert layer_name in LAYER_DEFS, f"Unknown layer: {layer_name}"
                    valid = [v["name"] for v in LAYER_DEFS[layer_name]["variants"]]
                    assert variant_name in valid, (
                        f"{state}: {layer_name}={variant_name} not in {valid}"
                    )
