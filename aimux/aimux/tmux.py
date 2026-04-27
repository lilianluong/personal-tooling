"""tmux server management for aimux.

aimux runs all agent sessions in an isolated tmux server:
  tmux -L aimux

Each agent gets its own tmux session within that server.
The server is started on first use and persists until explicitly stopped.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Sequence


TMUX_SOCKET = "aimux"

_STATUS_OPTIONS: list[list[str]] = [
    ["set-option", "-g", "status", "on"],
    ["set-option", "-g", "status-style", "bg=colour235,fg=colour252"],
    ["set-option", "-g", "status-left",
     " #[fg=colour39,bold]#{s/aimux-//:session_name}  #[fg=colour245,nobold]#{b:session_path} "],
    ["set-option", "-g", "status-left-length", "80"],
    ["set-option", "-g", "status-right", ""],
    ["set-option", "-g", "window-status-format", ""],
    ["set-option", "-g", "window-status-current-format", ""],
]


def _tmux(args: Sequence[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["tmux", "-L", TMUX_SOCKET, *args],
        capture_output=True,
        text=True,
        check=check,
    )


# ── server lifecycle ──────────────────────────────────────────────────────────

def ensure_server() -> None:
    """Start the aimux tmux server if not already running, and apply keybindings."""
    result = _tmux(["list-sessions"], check=False)
    if result.returncode != 0:
        # Server not running — bootstrap with a dummy session.
        # It will be cleaned up once a real session is created.
        _tmux(["new-session", "-d", "-s", "aimux-init", "-x", "220", "-y", "50"])

    _apply_keybindings()
    _apply_options()


def _apply_keybindings() -> None:
    aimux_bin = shutil.which("aimux") or "aimux"
    bindings: list[list[str]] = [
        ["bind-key", "-n", "M-d", "detach-client"],
        ["bind-key", "-n", "M-z", "run-shell", f"{aimux_bin} cycle prev --current #{{session_name}}"],
        ["bind-key", "-n", "M-x", "run-shell", f"{aimux_bin} cycle next --current #{{session_name}}"],
    ]
    for binding in bindings:
        _tmux(binding)


def _apply_options() -> None:
    for option in _STATUS_OPTIONS:
        _tmux(option)


def server_running() -> bool:
    result = _tmux(["list-sessions"], check=False)
    return result.returncode == 0


# ── session management ────────────────────────────────────────────────────────

def session_name(session_id: str) -> str:
    """Convert an aimux session id to a tmux session name."""
    return f"aimux-{session_id}"


def create_session(session_id: str, workspace: str, env: dict[str, str] | None = None) -> None:
    """Create a new tmux session in the aimux server."""
    ensure_server()
    name = session_name(session_id)
    env_args: list[str] = []
    for k, v in (env or {}).items():
        env_args += ["-e", f"{k}={v}"]
    _tmux([
        "new-session", "-d",
        "-s", name,
        "-c", workspace,
        *env_args,
    ])
    # Clean up the bootstrap session now that a real session exists.
    _tmux(["kill-session", "-t", "aimux-init"], check=False)


def kill_session(session_id: str) -> None:
    """Kill a tmux session."""
    name = session_name(session_id)
    _tmux(["kill-session", "-t", name], check=False)


def session_exists(session_id: str) -> bool:
    name = session_name(session_id)
    result = _tmux(["has-session", "-t", name], check=False)
    return result.returncode == 0


def list_tmux_sessions() -> list[str]:
    """Return list of aimux tmux session names (without the 'aimux-' prefix)."""
    result = _tmux(["list-sessions", "-F", "#{session_name}"], check=False)
    if result.returncode != 0:
        return []
    names = result.stdout.strip().splitlines()
    prefix = "aimux-"
    return [n[len(prefix):] for n in names if n.startswith(prefix) and n != "aimux-init"]


def send_keys(session_id: str, keys: str, enter: bool = True) -> None:
    """Send keystrokes to a tmux session's active pane."""
    name = session_name(session_id)
    args = ["send-keys", "-t", name, keys]
    if enter:
        args.append("Enter")
    _tmux(args)


def capture_pane(session_id: str, lines: int = 50) -> str:
    """Capture the last N lines of output from a session's pane."""
    name = session_name(session_id)
    result = _tmux([
        "capture-pane", "-pt", name,
        "-S", f"-{lines}",
    ], check=False)
    if result.returncode != 0:
        return ""
    return result.stdout


def attach_session(session_id: str) -> None:
    """Attach the current terminal to a tmux session.

    This replaces the current process's terminal with the tmux session.
    Returns when the user detaches (Alt+d).
    """
    name = session_name(session_id)
    subprocess.run(["tmux", "-L", TMUX_SOCKET, "attach-session", "-t", name])


def cycle_session(direction: str, current_tmux_name: str) -> None:
    """Switch to prev/next session in menu order (alphabetical by workspace, then reg order)."""
    from aimux.state import list_sessions

    sessions = list_sessions()
    groups: dict[str, list[str]] = {}
    for info in sessions:
        groups.setdefault(info.workspace, []).append(info.id)
    sorted_ids: list[str] = []
    for workspace in sorted(groups):
        sorted_ids.extend(groups[workspace])

    if not sorted_ids:
        return

    prefix = "aimux-"
    current_id = current_tmux_name[len(prefix):] if current_tmux_name.startswith(prefix) else current_tmux_name

    try:
        idx = sorted_ids.index(current_id)
    except ValueError:
        return

    if direction == "prev":
        target_idx = (idx - 1) % len(sorted_ids)
    else:
        target_idx = (idx + 1) % len(sorted_ids)

    _tmux(["switch-client", "-t", session_name(sorted_ids[target_idx])])
