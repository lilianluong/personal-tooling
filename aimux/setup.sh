#!/usr/bin/env bash
# aimux/setup.sh — install aimux and register Claude Code hooks
# Safe to run multiple times.

set -euo pipefail

AIMUX_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

green() { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }

# ── install uv ────────────────────────────────────────────────────────────────

export PATH="$HOME/.local/bin:$PATH"

if command -v uv &>/dev/null; then
  yellow "  already installed: uv"
else
  echo "  installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  green "  installed: uv"
fi

# ── install aimux ─────────────────────────────────────────────────────────────

echo "  installing aimux..."
uv tool install --editable "$AIMUX_DIR" --reinstall
green "  installed: aimux"

# ── register hooks in ~/.claude/settings.json ─────────────────────────────────

CLAUDE_SETTINGS="$HOME/.claude/settings.json"
HOOK_PYTHON="$AIMUX_DIR/aimux/hooks"

mkdir -p "$(dirname "$CLAUDE_SETTINGS")"
[ -f "$CLAUDE_SETTINGS" ] || echo '{}' > "$CLAUDE_SETTINGS"

python3 - "$CLAUDE_SETTINGS" "$HOOK_PYTHON" <<'PYEOF'
import json, sys

settings_path = sys.argv[1]
hook_dir = sys.argv[2]

with open(settings_path) as f:
    s = json.load(f)

hooks = s.setdefault("hooks", {})

def set_hook(event, script):
    """Add aimux hook command if not already present."""
    cmd = f"python3 {hook_dir}/{script}"
    entries = hooks.setdefault(event, [])
    # Check by command string to stay idempotent
    for entry in entries:
        if isinstance(entry, dict) and entry.get("hooks"):
            for h in entry["hooks"]:
                if h.get("command") == cmd:
                    return
    entries.append({"matcher": "", "hooks": [{"type": "command", "command": cmd}]})

set_hook("SessionStart", "session_start.py")
set_hook("Stop", "stop.py")
set_hook("UserPromptSubmit", "prompt_submit.py")
set_hook("SessionEnd", "session_end.py")

with open(settings_path, "w") as f:
    json.dump(s, f, indent=2)
    f.write("\n")

print("  hooks registered in", settings_path)
PYEOF
green "  registered Claude Code hooks"
