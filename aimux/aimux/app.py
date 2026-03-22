"""Main aimux Textual application."""

from __future__ import annotations

import time

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Footer, Label, Static

from aimux.state import (
    SessionInfo,
    SessionState,
    get_session_state,
    list_sessions,
    register_session,
    remove_session,
)
from aimux.tmux import attach_session, create_session, ensure_server, kill_session, send_keys
from aimux.widgets.confirm_kill import ConfirmKill
from aimux.widgets.new_session import SessionNamePrompt, WorkspacePicker
from aimux.widgets.session_list import SessionList

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
        def _on_workspace(workspace) -> None:
            if workspace is None:
                return
            def _on_name(name: str | None) -> None:
                if not name:
                    return
                self._spawn_session(workspace, name)
            self.push_screen(SessionNamePrompt(workspace), _on_name)

        self.push_screen(WorkspacePicker(), _on_workspace)

    def _spawn_session(self, workspace, name: str) -> None:
        ensure_server()
        create_session(
            session_id=name,
            workspace=str(workspace.path),
            env={"AIMUX_SESSION_ID": name},
        )
        info = SessionInfo(
            id=name,
            name=name,
            workspace=str(workspace.path),
            tmux_session=f"aimux-{name}",
        )
        register_session(info)
        # Send `claude` command to the new session then attach
        send_keys(name, "claude --dangerously-skip-permissions")
        self._attach(name)

    def _attach(self, session_id: str) -> None:
        with self.suspend():
            attach_session(session_id)
        # Refresh state after returning from tmux
        self._refresh_state()

    def action_attach_session(self) -> None:
        try:
            sl = self.query_one(SessionList)
            info = sl.get_selected_session()
            if info:
                self._attach(info.id)
        except Exception:
            pass

    def action_kill_session(self) -> None:
        try:
            sl = self.query_one(SessionList)
            info = sl.get_selected_session()
        except Exception:
            info = None

        if not info:
            return

        def _on_confirm(confirmed: bool) -> None:
            if confirmed:
                kill_session(info.id)
                remove_session(info.id)
                self._refresh_state()

        self.push_screen(ConfirmKill(info.name), _on_confirm)
