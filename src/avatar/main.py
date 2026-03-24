"""ASCII Avatar — entry point."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time

from avatar.event_bus import AvatarEvent, EventBus
from avatar.personas import DEFAULT_PERSONA, get_persona, list_personas
from avatar.renderer import AvatarRenderer
from avatar.state_machine import AvatarState, AvatarStateMachine
from avatar.voice.audio_player import AudioPlayer
from avatar.voice.base import TTSEngine

log = logging.getLogger(__name__)


def resolve_tts_engine(persona) -> TTSEngine | None:
    """Resolve TTS engine from persona config. Returns None if unavailable."""
    if persona.voice_engine == "kokoro":
        from avatar.voice.kokoro_engine import KokoroEngine
        engine = KokoroEngine(voice=persona.voice_id)
        if engine.is_available():
            return engine
        log.warning(
            "Kokoro model not found. Run scripts/install.sh to download. "
            "Running in animation-only mode."
        )
        return None
    elif persona.voice_engine == "elevenlabs":
        from avatar.voice.elevenlabs_engine import ElevenLabsEngine
        engine = ElevenLabsEngine(voice_id=persona.voice_id)
        if engine.is_available():
            return engine
        log.warning(
            "ELEVENLABS_API_KEY not set. Falling back to Kokoro."
        )
        # Fall back to kokoro
        from avatar.voice.kokoro_engine import KokoroEngine
        fallback = KokoroEngine(voice=persona.voice_id)
        return fallback if fallback.is_available() else None
    elif persona.voice_engine == "piper":
        from avatar.voice.piper_engine import PiperEngine
        engine = PiperEngine()
        return engine if engine.is_available() else None
    return None


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="ASCII Avatar for Claude Code")
    parser.add_argument(
        "--persona", default=DEFAULT_PERSONA,
        choices=list_personas(),
        help=f"Persona preset (default: {DEFAULT_PERSONA})",
    )
    parser.add_argument(
        "--socket", default="/tmp/ascii-avatar.sock",
        help="Unix socket path for event bus",
    )
    parser.add_argument("--no-voice", action="store_true", help="Disable TTS")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument(
        "--voice", default=None,
        help="Override persona voice ID",
    )
    parser.add_argument(
        "--audio-device", default=None, type=int,
        help="Override audio output device index",
    )
    parser.add_argument("--compact", action="store_true", help="Compact mode")
    parser.add_argument(
        "--portrait", default=None,
        help="Path to portrait image for avatar (overrides persona frame set)",
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Headless mode: run event bus and state machine without terminal rendering (for testing)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    persona = get_persona(args.persona)
    if args.voice:
        # Override voice from persona
        from avatar.personas import Persona
        persona = Persona(
            name=persona.name, frames=persona.frames,
            voice_engine=persona.voice_engine, voice_id=args.voice,
            accent_color=persona.accent_color, personality=persona.personality,
            frame_rate_modifier=persona.frame_rate_modifier,
        )

    # Audio device override
    if args.audio_device is not None:
        import sounddevice as sd
        sd.default.device = args.audio_device

    # TTS engine
    tts: TTSEngine | None = None
    if not args.no_voice:
        tts = resolve_tts_engine(persona)

    audio_player = AudioPlayer()

    # State machine
    sm = AvatarStateMachine(idle_timeout=30)

    # Event bus
    bus = EventBus(socket_path=args.socket)
    connected = False

    def handle_event(event: AvatarEvent) -> None:
        nonlocal connected
        connected = True
        if event.event == "state_change":
            try:
                new_state = AvatarState(event.state)
                sm.transition(new_state)
            except ValueError:
                log.warning("Unknown state: %s", event.state)
        elif event.event == "speak_start":
            sm.transition(AvatarState.SPEAKING)
            if tts and event.text:
                try:
                    audio, timings = tts.synthesize(event.text)
                    audio_player.play(
                        audio,
                        sample_rate=tts.sample_rate,
                        word_timings=timings,
                        on_word=lambda wt: None,  # Could update mouth frame
                        on_complete=lambda: sm.transition(AvatarState.IDLE),
                    )
                except Exception as e:
                    log.error("TTS failed: %s", e)
        elif event.event == "speak_end":
            sm.transition(AvatarState.IDLE)

    bus.on_event = handle_event

    # Shutdown handler
    running = True

    def shutdown(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Start
    bus.start()
    log.info("Avatar started. Persona: %s. Socket: %s", persona.name, args.socket)
    log.info("TTS: %s", "enabled" if tts else "disabled (animation only)")

    if args.headless:
        # Headless mode: no terminal rendering, just spin the event loop
        log.info("Running in headless mode (no terminal rendering).")
        try:
            while running:
                time.sleep(0.1)
        finally:
            audio_player.stop()
            sm.shutdown()
            bus.stop()
            log.info("Avatar stopped.")
        return

    # Renderer (only needed for interactive mode)
    import blessed
    term = blessed.Terminal()
    if args.no_color:
        term.number_of_colors = 2
    # Determine frame set: --portrait overrides persona frames
    frame_set = persona.frames
    if args.portrait:
        frame_set = f"portrait:{args.portrait}"
    elif persona.frames == "portrait":
        frame_set = "portrait"

    renderer = AvatarRenderer(
        terminal=term,
        frame_set=frame_set,
        frame_rate_modifier=persona.frame_rate_modifier,
    )

    frame_index = 0
    last_event = ""

    try:
        with term.fullscreen(), term.hidden_cursor():
            while running:
                state = sm.state
                frame = renderer.get_current_frame(state, frame_index)
                status = renderer.format_status_bar(
                    state=state,
                    connected=connected,
                    tts_loaded=tts is not None,
                    last_event=last_event,
                )
                renderer.render_frame(frame, status)

                rate = renderer.get_frame_rate(state)
                time.sleep(rate)
                frame_index = renderer.next_frame_index(state, frame_index)

                # Check for quit key
                key = term.inkey(timeout=0)
                if key == "q" or key.name == "KEY_ESCAPE":
                    break
    finally:
        audio_player.stop()
        sm.shutdown()
        bus.stop()
        log.info("Avatar stopped.")


if __name__ == "__main__":
    main()
