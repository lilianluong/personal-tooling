"""Spawn a new aimux session, optionally with an initial prompt."""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from aimux.state import SessionInfo, register_session
from aimux.tmux import create_session, ensure_server, send_keys


def get_tooling_user() -> str:
    config = Path.home() / ".config/personal-tooling/config"
    try:
        for line in config.read_text().splitlines():
            if line.startswith("TOOLING_USER="):
                return line.split("=", 1)[1].strip()
    except (FileNotFoundError, PermissionError):
        pass
    return "user"


def check_worktree_has_unstaged(path: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def remove_worktree(worktree_path: Path, repo_root: Path) -> None:
    result = subprocess.run(
        ["git", "worktree", "remove", "--force", str(worktree_path)],
        cwd=repo_root,
        capture_output=True,
    )
    if result.returncode != 0:
        # Metadata is stale/broken — remove directory manually and prune refs.
        shutil.rmtree(worktree_path, ignore_errors=True)
        subprocess.run(["git", "worktree", "prune"], cwd=repo_root, capture_output=True)


def spawn_worktree_session(repo_path: str, name: str) -> SessionInfo:
    """Create a git worktree at ~/<name> with branch <tooling_user>/<name> and spawn a session."""
    branch = f"{get_tooling_user()}/{name}"
    worktree_path = Path.home() / name
    subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(worktree_path)],
        cwd=repo_path,
        check=True,
    )
    return spawn_session(str(worktree_path), name)


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
