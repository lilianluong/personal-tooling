"""Main aimux Textual application."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Footer, Label, ListView, Static

from aimux.agent import DEFAULT_AGENT
from aimux.discovery import discover_workspaces
from aimux.state import (
    SessionInfo,
    SessionState,
    get_killed_cost_today,
    get_session_state,
    list_sessions,
    remove_session,
    toggle_pause_session,
)
from aimux.spawn import check_worktree_has_unstaged, remove_worktree, spawn_session, spawn_worktree_session
from aimux.tmux import attach_session, kill_session, apply_options_if_running, session_exists
from aimux.widgets.confirm_kill import ConfirmKill
from aimux.widgets.detail_panel import DetailPanel
from aimux.widgets.kill_worktree import ConfirmKillAllWorktrees, ConfirmKillWorktree, KillWorktreePicker
from aimux.widgets.new_session import SessionNamePrompt, WorkspacePicker, WorktreeNamePrompt
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
    agent: reactive[str] = reactive("claude")

    def render(self) -> str:
        waiting_str = ""
        if self.sessions_waiting:
            waiting_str = f"  •  👀 {self.sessions_waiting} waiting"
        mode_str = f"  •  🤖 {self.agent} mode" if self.agent != "claude" else ""
        return (
            f"aimux  •  {self.sessions_total} sessions"
            f"{waiting_str}{mode_str}"
            f"  •  ${self.cost_today:.2f} today"
        )


class AimuxApp(App):
    TITLE = "aimux"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
        Binding("n", "new_session", "New"),
        Binding("w", "new_worktree", "Worktree"),
        Binding("k", "kill_session", "Kill"),
        Binding("c", "kill_worktree", "Kill WT"),
        Binding("C", "kill_orphaned_worktrees", "Kill Orphan WTs"),
        Binding("p", "toggle_pause", "Pause"),
        Binding("u", "focus_paused", "Paused"),
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

    def __init__(self, agent: str = DEFAULT_AGENT) -> None:
        super().__init__()
        self._agent = agent

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
        apply_options_if_running()
        self.query_one(TopBar).agent = self._agent
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

    def action_new_worktree(self) -> None:
        def _on_repo(workspace) -> None:
            if workspace is None:
                return
            def _on_name(name: str | None) -> None:
                if not name:
                    return
                spawn_worktree_session(str(workspace.path), name, agent=self._agent)
                self._attach(name)
            self.push_screen(WorktreeNamePrompt(workspace), _on_name)

        self.push_screen(WorkspacePicker(repos_only=True), _on_repo)

    def _spawn_session(self, workspace, name: str) -> None:
        spawn_session(str(workspace.path), name, agent=self._agent)
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

    def action_kill_worktree(self) -> None:
        def _on_worktree(worktree) -> None:
            if worktree is None:
                return

            open_names = [
                info.name
                for info in list_sessions()
                if info.workspace == str(worktree.path)
                and get_session_state(info.id).status != "ended"
            ]
            has_unstaged = check_worktree_has_unstaged(worktree.path)

            def _on_confirm(confirmed: bool) -> None:
                if confirmed:
                    wt_path = worktree.path
                    wt_root = worktree.repo_root

                    def _do_remove() -> None:
                        remove_worktree(wt_path, wt_root)
                        discover_workspaces(refresh=True)

                    self.run_worker(_do_remove, thread=True)
                self.push_screen(KillWorktreePicker(), _on_worktree)

            self.push_screen(ConfirmKillWorktree(worktree, open_names, has_unstaged), _on_confirm)

        self.push_screen(KillWorktreePicker(), _on_worktree)

    def action_kill_orphaned_worktrees(self) -> None:
        live_workspaces = {
            info.workspace
            for info in list_sessions()
            if get_session_state(info.id).status != "ended" and session_exists(info.id)
        }
        worktrees = [w for w in discover_workspaces(refresh=True) if w.is_worktree]
        orphaned = [w for w in worktrees if str(w.path) not in live_workspaces]

        if not orphaned:
            self.notify("No orphaned worktrees to kill.")
            return

        def _on_confirm(confirmed: bool) -> None:
            if not confirmed:
                return

            def _do_remove() -> None:
                for wt in orphaned:
                    remove_worktree(wt.path, wt.repo_root)
                discover_workspaces(refresh=True)

            self.run_worker(_do_remove, thread=True)

        self.push_screen(ConfirmKillAllWorktrees(orphaned), _on_confirm)

    def action_toggle_pause(self) -> None:
        try:
            info = self.query_one(SessionList).get_selected_session()
        except Exception:
            info = None
        if not info:
            return
        toggle_pause_session(info.id)
        self._refresh_state()

    def action_focus_paused(self) -> None:
        self.query_one(SessionList).jump_to_paused()
