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

echo "[2/3] Downloading Kokoro TTS models..."
if [ ! -f "$MODEL_DIR/kokoro-v1.0.onnx" ]; then
    echo "  Downloading kokoro-v1.0.onnx..."
    python -c "
from huggingface_hub import hf_hub_download
hf_hub_download('hexgrad/Kokoro-82M', 'kokoro-v1.0.onnx', local_dir='$MODEL_DIR')
print('  Done.')
"
else
    echo "  kokoro-v1.0.onnx already exists."
fi

if [ ! -f "$MODEL_DIR/voices-v1.0.bin" ]; then
    echo "  Downloading voices-v1.0.bin..."
    python -c "
from huggingface_hub import hf_hub_download
hf_hub_download('hexgrad/Kokoro-82M', 'voices-v1.0.bin', local_dir='$MODEL_DIR')
print('  Done.')
"
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
