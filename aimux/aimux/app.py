"""Main aimux Textual application."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Footer, Label, ListView, Static

from aimux.state import (
    SessionInfo,
    SessionState,
    get_killed_cost_today,
    get_session_state,
    list_sessions,
    remove_session,
)
from aimux.spawn import spawn_session
from aimux.tmux import attach_session, kill_session
from aimux.widgets.confirm_kill import ConfirmKill
from aimux.widgets.detail_panel import DetailPanel
from aimux.widgets.new_session import SessionNamePrompt, WorkspacePicker
from aimux.widgets.session_list import SessionList, SessionRow

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
    ]

    CSS = """
    Screen {
        layers: base overlay;
    }

    #main-area {
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
        with Horizontal(id="main-area"):
            yield SessionList()
            yield DetailPanel()
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#main-area").display = False
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
        bar = self.query_one(TopBar)
        bar.sessions_total = len(pairs)
        bar.sessions_waiting = sum(1 for _, s in pairs if s.status == "waiting")
        bar.cost_today = sum(s.cost_usd for _, s in pairs) + get_killed_cost_today()

        has_sessions = bool(pairs)
        self.query_one("#empty-hint").display = not has_sessions
        self.query_one("#main-area").display = has_sessions

        if has_sessions:
            sl = self.query_one(SessionList)
            sl.sessions = pairs
            self._sync_detail(pairs)

    def _sync_detail(self, pairs: list[tuple[SessionInfo, SessionState]]) -> None:
        sl = self.query_one(SessionList)
        dp = self.query_one(DetailPanel)
        selected_info = sl.get_selected_session()
        if selected_info is None:
            dp.selected = None
            return
        for info, state in pairs:
            if info.id == selected_info.id:
                dp.selected = (info, state)
                dp.refresh_detail()
                return

    def on_list_view_highlighted(self, _) -> None:
        self._sync_detail(self._sessions)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, SessionRow):
            event.stop()
            self._attach(event.item.session_info.id)

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
        spawn_session(str(workspace.path), name)
        self._attach(name)

    def _attach(self, session_id: str) -> None:
        with self.suspend():
            attach_session(session_id)
        self._refresh_state()

    def action_kill_session(self) -> None:
        try:
            info = self.query_one(SessionList).get_selected_session()
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
