#!/bin/bash
# One-click launcher for GPT-Quick-TTS (macOS)
# Place this file in the project root and double-click it in Finder to open Terminal

set -e

# Resolve script directory
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Optional: uncomment and set your API key here if you don't want to export it globally
# export OPENAI_API_KEY="sk-..."

echo "Starting GPT-Quick-TTS in: $DIR"

# Prefer the project's venv python when available
if [ -x "$DIR/.venv/bin/python3" ]; then
  "$DIR/.venv/bin/python3" "$DIR/tts_console.py"
else
  python3 "$DIR/tts_console.py"
fi

echo
read -p "Press ENTER to close this window..."
