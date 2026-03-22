"""State management for aimux.

All state lives under ~/.local/share/aimux/:
  sessions.json            — registry of all sessions
  sessions/<id>.json       — per-session metadata (cost, tokens, status, etc.)
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

STATE_DIR = Path(os.environ.get("AIMUX_STATE_DIR", Path.home() / ".local/share/aimux"))
SESSIONS_FILE = STATE_DIR / "sessions.json"
SESSIONS_DIR = STATE_DIR / "sessions"

SessionStatus = Literal["active", "waiting", "ended"]


@dataclass
class SessionInfo:
    """Lightweight session entry stored in sessions.json."""

    id: str                 # unique slug, also the tmux session name
    name: str               # display name (same as id for now)
    workspace: str          # absolute path to the worktree/repo
    tmux_session: str       # tmux session name within the aimux server
    created_at: float = field(default_factory=time.time)


@dataclass
class SessionState:
    """Per-session metadata stored in sessions/<id>.json."""

    id: str
    status: SessionStatus = "active"
    idle_since: float | None = None   # epoch when agent last stopped
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    context_pct: float = 0.0          # 0–100
    last_tool: str | None = None


# ── helpers ───────────────────────────────────────────────────────────────────

def _ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _write_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    tmp.replace(path)


# ── session registry ──────────────────────────────────────────────────────────

def list_sessions() -> list[SessionInfo]:
    _ensure_dirs()
    raw = _read_json(SESSIONS_FILE)
    sessions = raw.get("sessions", [])
    return [SessionInfo(**s) for s in sessions]


def get_session(session_id: str) -> SessionInfo | None:
    for s in list_sessions():
        if s.id == session_id:
            return s
    return None


def register_session(session: SessionInfo) -> None:
    _ensure_dirs()
    raw = _read_json(SESSIONS_FILE)
    sessions = raw.get("sessions", [])
    # Remove existing entry with same id (idempotent)
    sessions = [s for s in sessions if s.get("id") != session.id]
    sessions.append(asdict(session))
    _write_json(SESSIONS_FILE, {"sessions": sessions})


def remove_session(session_id: str) -> None:
    _ensure_dirs()
    raw = _read_json(SESSIONS_FILE)
    sessions = [s for s in raw.get("sessions", []) if s.get("id") != session_id]
    _write_json(SESSIONS_FILE, {"sessions": sessions})
    state_file = SESSIONS_DIR / f"{session_id}.json"
    if state_file.exists():
        state_file.unlink()


# ── per-session state ─────────────────────────────────────────────────────────

def get_session_state(session_id: str) -> SessionState:
    path = SESSIONS_DIR / f"{session_id}.json"
    raw = _read_json(path)
    if not raw:
        return SessionState(id=session_id)
    return SessionState(**raw)


def update_session_state(state: SessionState) -> None:
    _ensure_dirs()
    path = SESSIONS_DIR / f"{state.id}.json"
    _write_json(path, asdict(state))
