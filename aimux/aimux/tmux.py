"""tmux server management for aimux.

aimux runs all agent sessions in an isolated tmux server:
  tmux -L aimux

Each agent gets its own tmux session within that server.
The server is started on first use and persists until explicitly stopped.
"""

from __future__ import annotations

import subprocess
from typing import Sequence


TMUX_SOCKET = "aimux"

# Keybindings configured in the aimux tmux server (no prefix needed)
_KEYBINDINGS = [
    # Alt+d — detach from current session, returns user to aimux TUI
    "bind-key -n M-d detach-client",
    # Alt+z — switch to previous session
    "bind-key -n M-z switch-client -p",
    # Alt+x — switch to next session
    "bind-key -n M-x switch-client -n",
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


def _apply_keybindings() -> None:
    for binding in _KEYBINDINGS:
        _tmux(binding.split())


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


def send_keys(session_id: str, keys: str) -> None:
    """Send keystrokes to a tmux session's active pane."""
    name = session_name(session_id)
    _tmux(["send-keys", "-t", name, keys, "Enter"])


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
