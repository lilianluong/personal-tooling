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
    "active":  "⏳",
    "waiting": "👀",
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


class WrapListView(ListView):
    """ListView with wrap-around keyboard navigation and optional paused-row skipping."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._skip_paused: bool = True

    def _is_paused_row(self, node) -> bool:
        return isinstance(node, SessionRow) and node.session_paused

    def _should_skip(self, node) -> bool:
        if node.disabled:
            return True
        if self._skip_paused and self._is_paused_row(node):
            return True
        return False

    def action_cursor_up(self) -> None:
        nodes = list(self._nodes)
        if not nodes:
            return
        current = self.index if self.index is not None else 0
        n = len(nodes)
        for delta in range(1, n + 1):
            idx = (current - delta) % n
            if not self._should_skip(nodes[idx]):
                self.index = idx
                if not self._is_paused_row(nodes[idx]):
                    self._skip_paused = True
                return

    def action_cursor_down(self) -> None:
        nodes = list(self._nodes)
        if not nodes:
            return
        current = self.index if self.index is not None else 0
        n = len(nodes)
        for delta in range(1, n + 1):
            idx = (current + delta) % n
            if not self._should_skip(nodes[idx]):
                self.index = idx
                if not self._is_paused_row(nodes[idx]):
                    self._skip_paused = True
                return

    def jump_to_first_paused(self) -> bool:
        """Move cursor to first paused session row. Returns True if one was found."""
        nodes = list(self._nodes)
        for i, node in enumerate(nodes):
            if self._is_paused_row(node):
                self._skip_paused = False
                self.index = i
                return True
        return False


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
    SessionRow.paused {
        color: $text-muted;
        text-style: dim;
    }
    SessionRow.paused.-selected {
        background: $surface;
    }
    """

    def __init__(self, info: SessionInfo, state: SessionState) -> None:
        super().__init__()
        self.session_info = info
        self.session_state = state
        self.session_paused = state.paused
        if state.paused:
            self.add_class("paused")

    def compose(self) -> ComposeResult:
        info = self.session_info
        state = self.session_state
        if state.paused:
            emoji = "⏸"
        else:
            emoji = _STATUS_EMOJI.get(state.status, "❓")
        wt = _worktree_label(info.workspace)
        cost = f"${state.cost_usd:.2f}"
        ctx = f"{state.context_pct:.0f}%"
        idle = _idle_str(state.idle_since)
        idle_part = f"  {idle} ago" if idle else ""
        bg_part = f"  🔄 {state.bg_tasks}" if state.bg_tasks > 0 else ""
        yield Label(
            f"{emoji}  {info.name:<22} {wt:<12} {cost:>7}  {ctx:>4}{bg_part}{idle_part}"
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


class PausedHeader(ListItem):
    """Non-interactive divider above the paused sessions section."""

    DEFAULT_CSS = """
    PausedHeader {
        height: 1;
        padding: 0 1;
        background: $surface;
        color: $text-muted;
        margin-top: 1;
    }
    PausedHeader:hover {
        background: $surface;
    }
    """

    def __init__(self) -> None:
        super().__init__(disabled=True)

    def compose(self) -> ComposeResult:
        yield Label("PAUSED  (press u to navigate, p to unpause)")


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
        yield WrapListView(id="session-listview")

    def on_mount(self) -> None:
        self._repopulate(self.sessions)

    def watch_sessions(self, new_sessions: list[tuple[SessionInfo, SessionState]]) -> None:
        try:
            self._repopulate(new_sessions)
        except Exception:
            pass  # widget not yet mounted

    def _repopulate(self, sessions: list[tuple[SessionInfo, SessionState]]) -> None:
        lv = self.query_one("#session-listview", WrapListView)
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

        target_index = None
        first_active_index = None
        first_paused_index = None

        for i, child in enumerate(items):
            if isinstance(child, SessionRow):
                if child.session_paused:
                    if first_paused_index is None:
                        first_paused_index = i
                else:
                    if first_active_index is None:
                        first_active_index = i
                if selected_id is not None and child.session_info.id == selected_id:
                    target_index = i
                    break

        # If the selected session was paused, move focus to first active row instead
        if target_index is not None:
            item = items[target_index]
            if isinstance(item, SessionRow) and item.session_paused:
                target_index = first_active_index

        if target_index is not None:
            lv.index = target_index
        elif first_active_index is not None:
            lv.index = first_active_index

    def _build_items(self, sessions: list[tuple[SessionInfo, SessionState]]) -> list[ListItem]:
        active = [(info, state) for info, state in sessions if not state.paused]
        paused = [(info, state) for info, state in sessions if state.paused]

        # Active sessions grouped by workspace
        groups: dict[str, list[tuple[SessionInfo, SessionState]]] = {}
        for info, state in active:
            groups.setdefault(info.workspace, []).append((info, state))

        items: list[ListItem] = []
        for workspace in sorted(groups):
            items.append(WorkspaceHeader(workspace))
            for info, state in groups[workspace]:
                items.append(SessionRow(info, state))

        # Paused sessions at the bottom, ungrouped
        if paused:
            items.append(PausedHeader())
            for info, state in paused:
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

    def jump_to_paused(self) -> bool:
        """Move cursor into the paused section. Returns True if any paused session exists."""
        try:
            lv = self.query_one("#session-listview", WrapListView)
        except Exception:
            return False
        return lv.jump_to_first_paused()
