"""Main aimux Textual application."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Footer, Label, Static

from aimux.state import (
    SessionInfo,
    SessionState,
    get_session_state,
    list_sessions,
)
from aimux.widgets.session_list import SessionList

if TYPE_CHECKING:
    pass

_REFRESH_INTERVAL = 2.0  # seconds between state polls


class TopBar(Static):
    """Top status bar showing aggregate stats."""

    DEFAULT_CSS = """
    TopBar {
        height: 1;
        background: $accent;
        color: $text;
        padding: 0 1;
    }
    """

    sessions_total: reactive[int] = reactive(0)
    sessions_waiting: reactive[int] = reactive(0)
    cost_today: reactive[float] = reactive(0.0)

    def render(self) -> str:
        waiting_str = ""
        if self.sessions_waiting:
            waiting_str = f"  •  ⏳ {self.sessions_waiting} waiting"
        return (
            f"aimux  •  {self.sessions_total} sessions"
            f"{waiting_str}"
            f"  •  ${self.cost_today:.2f} today"
        )


class AimuxApp(App):
    TITLE = "aimux"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
        Binding("n", "new_session", "New"),
        Binding("k", "kill_session", "Kill"),
        Binding("enter", "attach_session", "Open", show=True),
    ]

    CSS = """
    Screen {
        layers: base overlay;
    }

    #main-area {
        layout: horizontal;
        height: 1fr;
    }

    #empty-hint {
        width: 1fr;
        height: 1fr;
        align: center middle;
        color: $text-muted;
    }
    """

    _sessions: reactive[list[tuple[SessionInfo, SessionState]]] = reactive(list)

    def compose(self) -> ComposeResult:
        yield TopBar()
        yield Label(
            "No sessions yet. Press [bold]n[/bold] to start one.",
            id="empty-hint",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(_REFRESH_INTERVAL, self._refresh_state)
        self._refresh_state()

    def _refresh_state(self) -> None:
        infos = list_sessions()
        pairs: list[tuple[SessionInfo, SessionState]] = []
        for info in infos:
            state = get_session_state(info.id)
            pairs.append((info, state))

        self._sessions = pairs
        self._update_ui(pairs)

    def _update_ui(self, pairs: list[tuple[SessionInfo, SessionState]]) -> None:
        # Update top bar
        bar = self.query_one(TopBar)
        bar.sessions_total = len(pairs)
        bar.sessions_waiting = sum(1 for _, s in pairs if s.status == "waiting")
        bar.cost_today = sum(s.cost_usd for _, s in pairs)

        has_sessions = len(pairs) > 0

        # Swap between empty hint and session list
        try:
            hint = self.query_one("#empty-hint")
            hint.display = not has_sessions
        except Exception:
            pass

        try:
            sl = self.query_one(SessionList)
            sl.display = has_sessions
            sl.sessions = pairs
        except Exception:
            if has_sessions:
                # Mount session list for the first time
                self._mount_session_list(pairs)

    def _mount_session_list(self, pairs: list[tuple[SessionInfo, SessionState]]) -> None:
        hint = self.query_one("#empty-hint")
        footer = self.query_one(Footer)
        sl = SessionList()
        sl.sessions = pairs
        self.mount(sl, before=footer)
        hint.display = False

    def action_new_session(self) -> None:
        # Implemented in aimux/new-session commit
        self.notify("New session: coming soon!", severity="information")

    def action_kill_session(self) -> None:
        # Implemented in aimux/kill commit
        self.notify("Kill: coming soon!", severity="information")

    def action_attach_session(self) -> None:
        # Implemented in aimux/new-session commit (attach logic)
        self.notify("Attach: coming soon!", severity="information")
