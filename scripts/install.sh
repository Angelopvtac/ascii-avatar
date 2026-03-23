#!/bin/bash
set -euo pipefail

echo "=== ASCII Avatar — Dependency Installer ==="

# System deps
echo "[1/3] Installing system dependencies..."
if command -v dnf &>/dev/null; then
    echo "  sudo dnf install portaudio-devel"
    echo "  (Run manually — this script does not use sudo)"
elif command -v apt &>/dev/null; then
    echo "  sudo apt install portaudio19-dev"
    echo "  (Run manually — this script does not use sudo)"
fi

# Kokoro models
MODEL_DIR="$HOME/.cache/ascii-avatar/models"
mkdir -p "$MODEL_DIR"

RELEASE_URL="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"

echo "[2/3] Downloading Kokoro TTS models..."
if [ ! -f "$MODEL_DIR/kokoro-v1.0.onnx" ]; then
    echo "  Downloading kokoro-v1.0.onnx (~311MB)..."
    wget -q --show-progress -O "$MODEL_DIR/kokoro-v1.0.onnx" "$RELEASE_URL/kokoro-v1.0.onnx"
else
    echo "  kokoro-v1.0.onnx already exists."
fi

if [ ! -f "$MODEL_DIR/voices-v1.0.bin" ]; then
    echo "  Downloading voices-v1.0.bin (~27MB)..."
    wget -q --show-progress -O "$MODEL_DIR/voices-v1.0.bin" "$RELEASE_URL/voices-v1.0.bin"
else
    echo "  voices-v1.0.bin already exists."
fi

# Python deps
echo "[3/3] Installing Python dependencies..."
cd "$(dirname "$0")/.."
if [ -d .venv ]; then
    source .venv/bin/activate
fi
uv pip install -e ".[dev]"

echo ""
echo "=== Done! ==="
echo "Models: $MODEL_DIR"
echo "Test:   python -m avatar.main --no-voice"
