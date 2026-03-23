"""Left panel: workspace-grouped session list."""

from __future__ import annotations

import time
from pathlib import Path

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView

from aimux.state import SessionInfo, SessionState, SessionStatus


_STATUS_EMOJI: dict[SessionStatus, str] = {
    "active":  "🔄",
    "waiting": "⏳",
    "ended":   "💀",
}


def _idle_str(idle_since: float | None) -> str:
    if idle_since is None:
        return ""
    secs = int(time.time() - idle_since)
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}m"
    return f"{secs // 3600}h"


def _worktree_label(workspace: str) -> str:
    """Short name for the worktree: last path component."""
    return Path(workspace).name


class SessionRow(ListItem):
    """A single session row in the list."""

    DEFAULT_CSS = """
    SessionRow {
        height: 1;
        padding: 0 1;
    }
    SessionRow:hover {
        background: $boost;
    }
    SessionRow.-selected {
        background: $accent;
    }
    """

    def __init__(self, info: SessionInfo, state: SessionState) -> None:
        super().__init__()
        self.session_info = info
        self.session_state = state

    def compose(self) -> ComposeResult:
        info = self.session_info
        state = self.session_state
        emoji = _STATUS_EMOJI.get(state.status, "❓")
        wt = _worktree_label(info.workspace)
        cost = f"${state.cost_usd:.2f}"
        ctx = f"{state.context_pct:.0f}%"
        idle = _idle_str(state.idle_since)
        idle_part = f"  {idle} ago" if idle else ""
        yield Label(
            f"{emoji}  {info.name:<22} {wt:<12} {cost:>7}  {ctx:>4}{idle_part}"
        )


class WorkspaceHeader(ListItem):
    """Non-interactive workspace group header."""

    DEFAULT_CSS = """
    WorkspaceHeader {
        height: 1;
        padding: 0 1;
        background: $surface;
        color: $text-muted;
    }
    WorkspaceHeader:hover {
        background: $surface;
    }
    """

    def __init__(self, workspace_path: str) -> None:
        super().__init__(disabled=True)
        home = str(Path.home())
        display = workspace_path.replace(home, "~", 1)
        self._display = display

    def compose(self) -> ComposeResult:
        yield Label(f"WORKSPACE  {self._display}")


class SessionList(Widget):
    """Left panel: workspace-grouped list of sessions."""

    DEFAULT_CSS = """
    SessionList {
        width: 1fr;
        height: 1fr;
        border-right: solid $panel-lighten-1;
    }
    SessionList ListView {
        height: 1fr;
        border: none;
        padding: 0;
    }
    """

    # List of (SessionInfo, SessionState) pairs — set by the app
    sessions: reactive[list[tuple[SessionInfo, SessionState]]] = reactive(list)

    def compose(self) -> ComposeResult:
        yield ListView(id="session-listview")

    def on_mount(self) -> None:
        self._repopulate(self.sessions)

    def watch_sessions(self, new_sessions: list[tuple[SessionInfo, SessionState]]) -> None:
        try:
            self._repopulate(new_sessions)
        except Exception:
            pass  # widget not yet mounted

    def _repopulate(self, sessions: list[tuple[SessionInfo, SessionState]]) -> None:
        lv = self.query_one("#session-listview", ListView)
        # Remember which session is highlighted
        highlighted = lv.highlighted_child
        selected_id = (
            highlighted.session_info.id
            if isinstance(highlighted, SessionRow)
            else None
        )

        lv.clear()
        items = self._build_items(sessions)
        for item in items:
            lv.append(item)

        # Restore selection by session id
        if selected_id is not None:
            for i, child in enumerate(lv.children):
                if isinstance(child, SessionRow) and child.session_info.id == selected_id:
                    lv.index = i
                    break

    def _build_items(self, sessions: list[tuple[SessionInfo, SessionState]]) -> list[ListItem]:
        # Group by workspace
        groups: dict[str, list[tuple[SessionInfo, SessionState]]] = {}
        for info, state in sessions:
            groups.setdefault(info.workspace, []).append((info, state))

        items: list[ListItem] = []
        for workspace in sorted(groups):
            items.append(WorkspaceHeader(workspace))
            for info, state in groups[workspace]:
                items.append(SessionRow(info, state))
        return items

    def get_selected_session(self) -> SessionInfo | None:
        try:
            lv = self.query_one("#session-listview", ListView)
        except Exception:
            return None
        highlighted = lv.highlighted_child
        if isinstance(highlighted, SessionRow):
            return highlighted.session_info
        return None
