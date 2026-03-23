# aimux

A full-screen TUI for managing Claude Code agent sessions. Agents run headlessly in a background tmux server; aimux lets you monitor all sessions, view live output and costs, spawn new ones, and attach/detach with single keystrokes.

## Installation

`bootstrap.sh` handles installation automatically. To install manually:

```bash
bash aimux/setup.sh
```

This installs `uv` (if absent), installs aimux as a `uv` tool, and registers Claude Code hooks in `~/.claude/settings.json`.

## Usage

```bash
aimux
```

### Menu hotkeys

| Key | Action |
|---|---|
| `↑` / `↓` | Navigate sessions |
| `Enter` | Attach to selected session |
| `n` | New session (workspace picker → name prompt) |
| `k` | Kill session (with confirmation) |
| `q` / `Esc` | Quit aimux (sessions keep running) |

### In-session hotkeys (no prefix needed)

| Key | Action |
|---|---|
| `Alt+d` | Detach — return to aimux menu |
| `Alt+z` | Switch to previous session |
| `Alt+x` | Switch to next session |

These are configured on the aimux tmux server and require no setup.

## Workspace discovery

On startup and when creating a new session, aimux scans `~` (max depth 3) for git repos and their worktrees. Hidden directories and common noise dirs (`node_modules`, `.cargo`, etc.) are skipped.

To see what was discovered, run:

```python
python3 -c "
import sys; sys.path.insert(0, 'path/to/aimux')
from aimux.discovery import discover_workspaces
for w in discover_workspaces():
    print(w.display, '[worktree]' if w.is_worktree else '')
"
```

## State files

All state lives at `~/.local/share/aimux/`:

```
~/.local/share/aimux/
  sessions.json         # registry of all sessions
  sessions/<id>.json    # per-session: status, cost, tokens, context%
```

Override the location with `AIMUX_STATE_DIR` (useful for testing).

## Claude Code hooks

`setup.sh` registers four hooks in `~/.claude/settings.json`:

| Hook | What it does |
|---|---|
| `SessionStart` | Registers session, sets `status=active` |
| `Stop` | Sets `status=waiting`, parses transcript for cost/tokens/context% |
| `UserPromptSubmit` | Sets `status=active`, clears idle timer |
| `SessionEnd` | Sets `status=ended` |

Hooks only run when `AIMUX_SESSION_ID` is set in the environment — regular (non-aimux) Claude sessions are unaffected.

`AIMUX_SESSION_ID` is set automatically when aimux spawns a session. If you launch `claude` manually and want aimux to track it, set the variable before running:

```bash
AIMUX_SESSION_ID=my-session claude
```

## Troubleshooting

**Check the tmux server is running:**
```bash
tmux -L aimux ls
```

**Inspect state files:**
```bash
cat ~/.local/share/aimux/sessions.json
ls ~/.local/share/aimux/sessions/
```

**Verify hooks are registered:**
```bash
cat ~/.claude/settings.json | python3 -m json.tool | grep -A5 '"hooks"'
```

**Re-run setup if hooks are missing:**
```bash
bash aimux/setup.sh
```
