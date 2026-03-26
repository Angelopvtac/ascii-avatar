from avatar.frames.layered import LAYER_DEFS, STATE_FRAME_MAP, PARALLAX_OFFSETS


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
