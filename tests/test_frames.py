from avatar.frames import load_frame_set


class TestFrameSet:
    def test_load_cyberpunk(self):
        frames, rates = load_frame_set("cyberpunk")
        assert isinstance(frames, dict)
        assert isinstance(rates, dict)

    def test_all_states_present(self):
        frames, rates = load_frame_set("cyberpunk")
        for state in ["idle", "thinking", "speaking", "listening", "error"]:
            assert state in frames, f"Missing state: {state}"
            assert state in rates, f"Missing rate: {state}"

    def test_each_state_has_frames(self):
        frames, _ = load_frame_set("cyberpunk")
        for state, frame_list in frames.items():
            assert len(frame_list) >= 2, f"{state} needs at least 2 frames"
            for i, frame in enumerate(frame_list):
                assert isinstance(frame, str), f"{state}[{i}] is not a string"
                assert len(frame) > 0, f"{state}[{i}] is empty"

    def test_frame_rates_are_positive(self):
        _, rates = load_frame_set("cyberpunk")
        for state, rate in rates.items():
            assert rate > 0, f"{state} rate must be positive"

    def test_frames_fit_in_terminal(self):
        frames, _ = load_frame_set("cyberpunk")
        for state, frame_list in frames.items():
            for i, frame in enumerate(frame_list):
                lines = frame.strip("\n").split("\n")
                assert len(lines) <= 25, f"{state}[{i}] too tall: {len(lines)} lines"

    def test_unknown_frame_set_raises(self):
        import pytest
        with pytest.raises(KeyError):
            load_frame_set("nonexistent")
