"""Tests for the avatar agent decision loop."""
import json
import time
from unittest.mock import MagicMock, patch

import pytest

from avatar.agent import AgentLoop


class TestAgentLoop:
    def test_process_raw_event_updates_tracker(self):
        agent = AgentLoop(socket_path="/dev/null", dry_run=True)
        agent._process_raw_event({
            "hook": "PreToolUse",
            "session_id": "s1",
            "cwd": "/home/user/projects/vyzibl",
            "tool_name": "Bash",
        })
        info = agent._tracker.get("s1")
        assert info is not None
        assert info.project == "vyzibl"

    def test_ignores_event_without_hook_field(self):
        agent = AgentLoop(socket_path="/dev/null", dry_run=True)
        # Legacy events without "hook" field should be ignored
        agent._process_raw_event({"event": "state_change", "state": "thinking"})
        assert agent._tracker.active_count == 0

    def test_maps_hook_to_visual_state(self):
        agent = AgentLoop(socket_path="/dev/null", dry_run=True)
        assert agent._hook_to_state("PreToolUse") == "thinking"
        assert agent._hook_to_state("PostToolUse") == "thinking"
        assert agent._hook_to_state("PostToolUseFailure") == "error"
        assert agent._hook_to_state("UserPromptSubmit") == "listening"
        assert agent._hook_to_state("Stop") == "idle"

    def test_visual_state_priority(self):
        agent = AgentLoop(socket_path="/dev/null", dry_run=True)
        # error > thinking > listening > idle
        assert agent._highest_priority_state(["thinking", "error", "idle"]) == "error"
        assert agent._highest_priority_state(["thinking", "listening"]) == "thinking"
        assert agent._highest_priority_state(["idle", "listening"]) == "listening"
        assert agent._highest_priority_state([]) == "idle"

    def test_debounce_blocks_speech(self):
        agent = AgentLoop(socket_path="/dev/null", dry_run=True)
        agent._last_speech_time = time.monotonic()  # just spoke
        assert agent._should_suppress_speech() is True

    def test_debounce_allows_after_timeout(self):
        agent = AgentLoop(socket_path="/dev/null", dry_run=True)
        agent._last_speech_time = time.monotonic() - 15  # spoke 15s ago
        assert agent._should_suppress_speech() is False

    def test_debounce_allows_when_never_spoke(self):
        agent = AgentLoop(socket_path="/dev/null", dry_run=True)
        assert agent._should_suppress_speech() is False

    @patch("avatar.agent.anthropic")
    def test_decide_calls_haiku(self, mock_anthropic):
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text='{"state": "thinking", "speak": null}')]
        )

        agent = AgentLoop(socket_path="/dev/null", dry_run=True)
        agent._client = mock_client
        agent._process_raw_event({
            "hook": "PreToolUse",
            "session_id": "s1",
            "cwd": "/home/user/projects/vyzibl",
        })
        state, speak = agent._decide()

        assert state == "thinking"
        assert speak is None
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"
        assert call_kwargs["max_tokens"] == 100

    def test_decide_skips_api_when_no_events(self):
        agent = AgentLoop(socket_path="/dev/null", dry_run=True)
        # No events processed → no API call, return idle
        state, speak = agent._decide()
        assert state == "idle"
        assert speak is None
