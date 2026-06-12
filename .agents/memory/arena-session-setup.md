---
name: Arena session setup
description: How to restore the arena-cli environment after a Replit reboot (everything at /home/runner/ is wiped)
---

## The problem
Only `/home/runner/workspace/` persists across reboots. Everything at `/home/runner/` (including `~/.arena/credentials`, `~/.arena/bin/arena`) is wiped.

## One-command fix
```bash
source /home/runner/workspace/arena_start.sh
```
This script:
1. Reinstalls arena CLI into `/home/runner/workspace/.arena/` if needed
2. Restores credentials from `/home/runner/workspace/.arena/credentials` → `~/.arena/credentials`
3. Rebuilds `/tmp/arena-project/` symlinks (lost on reboot)
4. Exports `ARENA_INSTALL_DIR`, `OPENROUTER_API_KEY`, `PATH`

## Manual steps if script fails
```bash
# 1. Restore venv
WS=/home/runner/workspace
$WS/.local/bin/uv venv $WS/.arena/venv --python $WS/.local/bin/python3.13 --quiet
$WS/.local/bin/uv pip install --python $WS/.arena/venv/bin/python $WS/*.whl --quiet

# 2. Restore credentials
mkdir -p ~/.arena && cp $WS/.arena/credentials ~/.arena/credentials

# 3. Rebuild /tmp symlinks
mkdir -p /tmp/arena-project
for item in arena.yaml mcp prompts skills .arena; do ln -sf $WS/$item /tmp/arena-project/$item; done

# 4. Export env
export ARENA_INSTALL_DIR=$WS/.arena
export OPENROUTER_API_KEY="$OPENAI_API_KEY"   # OPENAI_API_KEY starts with sk-or-v1- — it IS an OpenRouter key
```

## Auth token
Stored at `/home/runner/workspace/.arena/credentials` (persisted). Last used token: do NOT save here. User has it.

**Why:** arena stores credentials at `~/.arena/credentials` by default (from `cli_commons` settings). That path is under `/home/runner/` which is ephemeral.
