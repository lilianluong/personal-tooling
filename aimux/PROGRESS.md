# aimux — Build Progress

## Commit Stack

| # | Branch | Status | Notes |
|---|---|---|---|
| 1 | `aimux/scaffold` | ✅ done | Project structure, empty Textual app, setup.sh |
| 2 | `aimux/state` | ✅ done | State storage: sessions.json + per-session JSON |
| 3 | `aimux/tmux-backend` | ✅ done | tmux server lifecycle, Alt+d/z/x keybindings |
| 4 | `aimux/hooks` | ✅ done | Claude Code hooks writing to state |
| 5 | `aimux/discovery` | ✅ done | Git repo + worktree auto-discovery under ~ |
| 6 | `aimux/tui-list` | ✅ done | Top bar + workspace-grouped session list |
| 7 | `aimux/new-session` | ✅ done | n hotkey: workspace picker + spawn claude |
| 8 | `aimux/kill` | ✅ done | k hotkey: kill with confirmation |
| 9 | `aimux/tui-detail` | ✅ done | Right panel: pane preview, cost, git status |
| 10 | `aimux/bootstrap-wire` | ⬜ todo | Wire setup.sh into bootstrap.sh |

## Current: Commit 1 — scaffold

### Files created
- `aimux/pyproject.toml` — package definition, textual dependency
- `aimux/setup.sh` — installs pipx + aimux via `pipx install --editable`
- `aimux/aimux/__init__.py`
- `aimux/aimux/main.py` — `aimux` CLI entry point
- `aimux/aimux/app.py` — placeholder Textual app (q/Esc to quit)
- `aimux/aimux/state.py` — stub
- `aimux/aimux/tmux.py` — stub
- `aimux/aimux/discovery.py` — stub
- `aimux/aimux/widgets/` — stubs for all widgets
- `aimux/aimux/hooks/` — stubs for all hooks

### Verification
- [x] `bash aimux/setup.sh` installs without errors
- [x] `aimux` command available at `~/.local/bin/aimux`
- [x] `from aimux.app import AimuxApp` imports cleanly
- [ ] `aimux` launches full-screen TUI (requires real terminal — verify manually)
- [ ] `q` and `Esc` quit cleanly (requires real terminal)
