#!/usr/bin/env bash
# Tahsin 3D motoru kurulumu (bulut oturumu başına bir kez, ~2-3 dk).
set -euo pipefail
MODEL_DIR="${SHORTS_TOOLS_MODELS:-$HOME/.cache/shorts-tools}"; mkdir -p "$MODEL_DIR"
q() { grep -viE "warning|dependency resolver|requires|notice" || true; }

echo "[1/4] Blender (bpy) + yardımcı paketler"
pip install --break-system-packages -q bpy sherpa-onnx numpy pillow 2>&1 | q
python3 -c "import bpy; print('  Blender', bpy.app.version_string)"

echo "[2/4] Çevrimdışı Whisper small + Silero VAD (GitHub'dan; zamanla.py için)"
if [ ! -f "$MODEL_DIR/sherpa-onnx-whisper-small/small-encoder.int8.onnx" ]; then
  curl -sSL --retry 3 -o "$MODEL_DIR/w.tar.bz2" https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2
  tar xjf "$MODEL_DIR/w.tar.bz2" -C "$MODEL_DIR" sherpa-onnx-whisper-small/small-encoder.int8.onnx \
    sherpa-onnx-whisper-small/small-decoder.int8.onnx sherpa-onnx-whisper-small/small-tokens.txt
  rm -f "$MODEL_DIR/w.tar.bz2"
fi
[ -f "$MODEL_DIR/silero_vad.onnx" ] || curl -sSL --retry 3 -o "$MODEL_DIR/silero_vad.onnx" \
  https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx

echo "[3/4] earshot (çevrimdışı ses efekti ve müzik)"
command -v earshot >/dev/null || pip install --break-system-packages -q "earshot @ git+https://github.com/Leonxlnx/earshot" 2>&1 | q

echo "[4/4] ffmpeg kontrolü"
command -v ffmpeg >/dev/null && echo "  ffmpeg var" || { echo "  ffmpeg YOK"; exit 1; }
echo "Hazır."
