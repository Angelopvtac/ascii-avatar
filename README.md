# ascii-avatar

A terminal-based ASCII avatar companion for Claude Code. It runs as a separate Python process, animating a cyberpunk character in response to Claude's activity (thinking, speaking, listening, idle) and reading responses aloud via local TTS. The persona system bundles frame sets, voice engines, and visual style into named presets.

## Architecture

```
Claude Code (hooks/MCP) ──PUSH──> PULL── Avatar Process
                         ipc://              |-- State Machine
                                             |-- Renderer (blessed)
                                             |-- Persona Manager
                                             '-- Voice Engine
                                                  |-- KokoroEngine (default)
                                                  |-- ElevenLabsEngine (opt-in)
                                                  '-- PiperEngine (fallback)
```

Claude Code pushes events over a Unix socket (ZeroMQ PUSH/PULL). The avatar process pulls those events, drives the state machine, animates the terminal renderer, and synthesizes speech.

## Quick Start

```bash
# 1. Install dependencies (portaudio + Kokoro models)
bash scripts/install.sh

# 2. Start the avatar
python -m avatar.main

# 3. Send a test event from another terminal
python -m avatar.bridge.cli think
```

Press `q` or `Esc` to quit.

## Personas

| Persona | Voice Engine | Voice ID | Color | Personality | Frame Speed |
|---------|-------------|----------|-------|-------------|-------------|
| `ghost` (default) | Kokoro | af_bella | cyan | minimal | 1.0x |
| `oracle` | Kokoro | bf_emma | amber | sage | 0.8x |
| `spectre` | ElevenLabs | — | green | glitch | 1.3x |

Select a persona with `--persona ghost|oracle|spectre`.

## Requirements

- Python 3.11+
- `portaudio` system library (for audio output)
  - Debian/Ubuntu: `sudo apt install portaudio19-dev`
  - Fedora/RHEL: `sudo dnf install portaudio-devel`
- Kokoro ONNX models (optional, downloaded by `scripts/install.sh`):
  - `~/.cache/ascii-avatar/models/kokoro-v1.0.onnx`
  - `~/.cache/ascii-avatar/models/voices-v1.0.bin`
- ElevenLabs API key in `ELEVENLABS_API_KEY` (required only for `spectre` persona)

The avatar runs in animation-only mode if Kokoro models are absent or `--no-voice` is passed.

## License

MIT
