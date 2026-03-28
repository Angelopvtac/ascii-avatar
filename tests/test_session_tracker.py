import time
import pytest
from avatar.session_tracker import SessionInfo, SessionTracker


class TestSessionTracker:
    def test_update_creates_new_session(self):
        tracker = SessionTracker()
        tracker.update(
            session_id="abc123",
            cwd="/home/user/projects/vyzibl",
            hook_event="PreToolUse",
        )
        info = tracker.get("abc123")
        assert info is not None
        assert info.project == "vyzibl"
        assert info.status == "active"
        assert info.tool_count == 1
        assert info.error_count == 0
        assert info.last_event == "PreToolUse"

    def test_update_increments_tool_count(self):
        tracker = SessionTracker()
        tracker.update("s1", "/home/user/projects/vyzibl", "PreToolUse")
        tracker.update("s1", "/home/user/projects/vyzibl", "PostToolUse")
        tracker.update("s1", "/home/user/projects/vyzibl", "PreToolUse")
        info = tracker.get("s1")
        assert info.tool_count == 3

    def test_update_counts_errors(self):
        tracker = SessionTracker()
        tracker.update("s1", "/home/user/projects/vyzibl", "PostToolUse")
        tracker.update("s1", "/home/user/projects/vyzibl", "PostToolUseFailure")
        info = tracker.get("s1")
        assert info.error_count == 1
        assert info.status == "error"

    def test_project_from_cwd(self):
        tracker = SessionTracker()
        tracker.update("s1", "/home/user/projects/ascii-avatar", "PreToolUse")
        assert tracker.get("s1").project == "ascii-avatar"

    def test_project_from_home_dir(self):
        tracker = SessionTracker()
        tracker.update("s1", "/home/user", "PreToolUse")
        assert tracker.get("s1").project == "user"
