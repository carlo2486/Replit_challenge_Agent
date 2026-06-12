#!/usr/bin/env bash
# Run this at the start of every session to restore the arena environment.
# Usage: source arena_start.sh   (or: bash arena_start.sh)
set -euo pipefail

ARENA_BIN=/home/runner/workspace/.arena/bin/arena
ARENA_CREDENTIALS=/home/runner/workspace/.arena/credentials

echo "=== Arena session setup ==="

# 1. Reinstall CLI if venv was wiped
if [[ ! -x "$ARENA_BIN" ]]; then
  echo "  Reinstalling arena CLI..."
  WS=/home/runner/workspace
  $WS/.local/bin/uv venv $WS/.arena/venv \
    --python $WS/.local/bin/python3.13 --quiet
  $WS/.local/bin/uv pip install --python $WS/.arena/venv/bin/python \
    $WS/arena_core_data-*.whl $WS/arena_core-*.whl \
    $WS/harbor-*.whl $WS/arena_sdk-*.whl \
    $WS/cli_commons-*.whl $WS/arena_cli-*.whl --quiet
  mkdir -p $WS/.arena/bin
  printf '#!/bin/bash\nexec /home/runner/workspace/.arena/venv/bin/arena "$@"\n' \
    > $WS/.arena/bin/arena
  chmod +x $WS/.arena/bin/arena
  cp $WS/env.json $WS/.arena/env.json
  echo "  CLI reinstalled."
fi

# 2. Restore credentials to ~/.arena (arena looks there by default)
if [[ -f "$ARENA_CREDENTIALS" ]]; then
  mkdir -p ~/.arena
  cp "$ARENA_CREDENTIALS" ~/.arena/credentials
  echo "  Credentials restored."
else
  echo "  WARNING: No credentials found at $ARENA_CREDENTIALS"
  echo "  Run: $ARENA_BIN auth login --token <your-token>"
fi

# 3. Rebuild /tmp/arena-project symlinks (lost on reboot)
rm -rf /tmp/arena-project
mkdir -p /tmp/arena-project
WS=/home/runner/workspace
for item in arena.yaml mcp prompts skills .arena; do
  ln -sf "$WS/$item" "/tmp/arena-project/$item"
done
echo "  /tmp/arena-project ready."

# 4. Export environment
export ARENA_INSTALL_DIR=/home/runner/workspace/.arena
export OPENROUTER_API_KEY="$OPENAI_API_KEY"
export PATH="/home/runner/workspace/.arena/bin:$PATH"

echo ""
echo "=== Setup complete ==="
echo "  arena binary : $ARENA_BIN"
echo "  project dir  : /tmp/arena-project"
echo ""
echo "Commands:"
echo "  cd /tmp/arena-project && arena doctor"
echo "  cd /tmp/arena-project && arena history"
echo "  cd /tmp/arena-project && arena submit"
