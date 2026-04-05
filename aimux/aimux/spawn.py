"""Spawn a new aimux session, optionally with an initial prompt."""

from __future__ import annotations

import time

from aimux.state import SessionInfo, register_session
from aimux.tmux import create_session, ensure_server, send_keys


def spawn_session(workspace: str, name: str, prompt: str | None = None) -> SessionInfo:
    """Create a new aimux session and start claude interactively.

    If *prompt* is given it is injected as keystrokes after claude starts,
    leaving the session open for follow-up interaction.
    """
    ensure_server()
    create_session(session_id=name, workspace=workspace, env={"AIMUX_SESSION_ID": name})
    info = SessionInfo(id=name, name=name, workspace=workspace, tmux_session=f"aimux-{name}")
    register_session(info)
    send_keys(name, "claude --dangerously-skip-permissions")
    if prompt:
        time.sleep(2.0)
        send_keys(name, prompt, enter=False)
        time.sleep(1.5)
        send_keys(name, "", enter=True)
    return info
