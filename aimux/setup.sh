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

def set_hook(event, script, matcher=""):
    """Add aimux hook command if not already present (idempotent by command string)."""
    cmd = f"python3 {hook_dir}/{script}"
    entries = hooks.setdefault(event, [])
    for entry in entries:
        if isinstance(entry, dict) and entry.get("matcher") == matcher and entry.get("hooks"):
            for h in entry["hooks"]:
                if h.get("command") == cmd:
                    return
    entries.append({"matcher": matcher, "hooks": [{"type": "command", "command": cmd}]})

set_hook("SessionStart", "session_start.py")
set_hook("Stop", "stop.py")
set_hook("UserPromptSubmit", "prompt_submit.py")
set_hook("SessionEnd", "session_end.py")
set_hook("PreToolUse", "pre_tool_use.py", "AskUserQuestion")
set_hook("PreToolUse", "pre_tool_use.py", "ExitPlanMode")
set_hook("PostToolUse", "post_tool_use.py", "AskUserQuestion")
set_hook("PostToolUse", "post_tool_use.py", "ExitPlanMode")
set_hook("PreToolUse", "bg_task_start.py", "Agent")
set_hook("PostToolUse", "bg_task_end.py", "Agent")

with open(settings_path, "w") as f:
    json.dump(s, f, indent=2)
    f.write("\n")

print("  hooks registered in", settings_path)
PYEOF
green "  registered Claude Code hooks"

# ── register hooks in ~/.codex/hooks.json ───────────────────────────────────

CODEX_HOOKS="$HOME/.codex/hooks.json"

mkdir -p "$(dirname "$CODEX_HOOKS")"
[ -f "$CODEX_HOOKS" ] || echo '{}' > "$CODEX_HOOKS"

python3 - "$CODEX_HOOKS" "$HOOK_PYTHON" <<'PYEOF'
import json, sys

hooks_path = sys.argv[1]
hook_dir = sys.argv[2]

with open(hooks_path) as f:
    s = json.load(f)

hooks = s.setdefault("hooks", {})

def set_hook(event, script, matcher=None):
    """Add aimux hook command if not already present (idempotent by command string)."""
    cmd = f"python3 {hook_dir}/{script}"
    entries = hooks.setdefault(event, [])
    for entry in entries:
        if isinstance(entry, dict) and entry.get("matcher") == matcher and entry.get("hooks"):
            for h in entry["hooks"]:
                if h.get("command") == cmd:
                    return
    entry = {"hooks": [{"type": "command", "command": cmd}]}
    if matcher is not None:
        entry["matcher"] = matcher
    entries.append(entry)

set_hook("SessionStart", "session_start.py", matcher="startup|resume|clear|compact")
set_hook("Stop", "stop.py")
set_hook("UserPromptSubmit", "prompt_submit.py")
set_hook("SessionEnd", "session_end.py")

with open(hooks_path, "w") as f:
    json.dump(s, f, indent=2)
    f.write("\n")

print("  hooks registered in", hooks_path)
PYEOF
green "  registered Codex hooks"
