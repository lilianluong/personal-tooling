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

### Codex mode

By default new sessions launch `claude --dangerously-skip-permissions`. Start aimux with `--codex` to launch `codex` instead for every session created in that run (worktrees included):

```bash
aimux --codex
```

The flag only affects the current run — plain `aimux` always starts in claude mode. It's also available on the `spawn` CLI subcommand:

```bash
aimux spawn --workspace ~/some-repo --name my-session --codex
```

Status/cost/token tracking works the same way for codex sessions (see [Codex hooks](#codex-hooks) below), but `bg_tasks` tracking and the pause-on-question indicator (`PreToolUse`/`PostToolUse` for `AskUserQuestion`/`ExitPlanMode`/`Agent`) are Claude Code-specific tool names and aren't wired up for codex.

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

## Codex hooks

`setup.sh` also registers hooks in `~/.codex/hooks.json` for `SessionStart`, `Stop`, `UserPromptSubmit`, and `SessionEnd`. Codex's hook payload schema and JSON registration format are (intentionally, per Codex's own docs) compatible with Claude Code's, so the same hook scripts are reused for both — `aimux/hooks/_common.py::parse_transcript` detects which transcript format (Claude JSONL vs. Codex rollout JSONL) it's looking at and parses accordingly.

Codex requires hooks to be explicitly trusted before they run (`/hooks` inside a codex session). aimux launches codex with `--dangerously-bypass-hook-trust` (see `aimux/agent.py`) so tracking works immediately in headless sessions without a manual trust step.

Codex cost figures use a small hardcoded pricing table (`_CODEX_PRICING` in `_common.py`) — update it if OpenAI's pricing changes.

**First run in a new directory:** Codex shows a one-time "Do you trust the contents of this directory?" prompt per workspace, separate from hook/approval trust and not skipped by `--dangerously-bypass-approvals-and-sandbox`. It can eat some of the injected `--prompt` keystrokes on that first run (harmless, but the initial prompt may arrive garbled). Trust persists in `~/.codex/config.toml` after the first answer, so this only affects the very first codex session in a given workspace — every `w` (new worktree) creates a fresh directory, so expect it there each time.

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
