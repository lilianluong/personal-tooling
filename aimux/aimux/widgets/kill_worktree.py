"""Worktree kill picker and confirmation modals."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from aimux.discovery import Workspace, discover_workspaces


class KillWorktreePicker(ModalScreen[Workspace | None]):
    """Pick a linked worktree to remove."""

    DEFAULT_CSS = """
    KillWorktreePicker {
        align: center middle;
    }

    KillWorktreePicker > Static {
        width: 70;
        max-height: 24;
        background: $surface;
        border: solid $error;
        padding: 1 2;
    }

    KillWorktreePicker #picker-title {
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }

    KillWorktreePicker #filter-input {
        margin-bottom: 1;
    }

    KillWorktreePicker ListView {
        height: 14;
        border: solid $panel-lighten-1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("up", "list_up", "Up", show=False),
        Binding("down", "list_down", "Down", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Static():
            yield Label("Remove worktree", id="picker-title")
            yield Input(placeholder="Type to filter...", id="filter-input")
            yield ListView(id="worktree-list")

    def on_mount(self) -> None:
        all_ws = discover_workspaces(refresh=True)
        self._all_worktrees = [w for w in all_ws if w.is_worktree]
        self._render_list(self._all_worktrees)
        self.query_one("#filter-input", Input).focus()

    def _render_list(self, worktrees: list[Workspace]) -> None:
        lv = self.query_one("#worktree-list", ListView)
        lv.clear()
        for wt in worktrees:
            item = ListItem(Label(wt.display))
            item._workspace = wt  # type: ignore[attr-defined]
            lv.append(item)

    def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value.lower()
        filtered = [w for w in self._all_worktrees if query in w.display.lower()]
        self._render_list(filtered)

    def on_input_submitted(self, _: Input.Submitted) -> None:
        self._select_highlighted()

    def action_list_up(self) -> None:
        self.query_one("#worktree-list", ListView).action_cursor_up()

    def action_list_down(self) -> None:
        self.query_one("#worktree-list", ListView).action_cursor_down()

    def _select_highlighted(self) -> None:
        lv = self.query_one("#worktree-list", ListView)
        item = lv.highlighted_child
        ws = getattr(item, "_workspace", None)
        if ws:
            self.dismiss(ws)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        ws = getattr(event.item, "_workspace", None)
        if ws:
            self.dismiss(ws)

    def action_cancel(self) -> None:
        self.dismiss(None)


class ConfirmKillWorktree(ModalScreen[bool]):
    """Confirm worktree removal, blocking if a session is open."""

    DEFAULT_CSS = """
    ConfirmKillWorktree {
        align: center middle;
    }

    ConfirmKillWorktree > Static {
        width: 62;
        background: $surface;
        border: solid $error;
        padding: 1 2;
    }

    ConfirmKillWorktree #title {
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }

    ConfirmKillWorktree #path-label {
        color: $text-muted;
        margin-bottom: 1;
    }

    ConfirmKillWorktree #notice {
        margin-bottom: 1;
    }

    ConfirmKillWorktree #btn-row {
        layout: horizontal;
        height: 3;
        align-horizontal: right;
    }

    ConfirmKillWorktree Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("y", "confirm", "Yes"),
    ]

    def __init__(
        self,
        worktree: Workspace,
        open_session_names: list[str],
        has_unstaged: bool,
    ) -> None:
        super().__init__()
        self.worktree = worktree
        self.open_session_names = open_session_names
        self.has_unstaged = has_unstaged
        self._blocked = bool(open_session_names)

    def compose(self) -> ComposeResult:
        with Static():
            yield Label("Remove worktree?", id="title")
            yield Label(self.worktree.display, id="path-label")
            if self._blocked:
                names = ", ".join(self.open_session_names)
                yield Label(
                    f"[bold red]Cannot remove:[/bold red] session(s) still open here:\n"
                    f"  [bold]{names}[/bold]\n\n"
                    "Kill those sessions first.",
                    id="notice",
                )
            elif self.has_unstaged:
                yield Label(
                    "[bold yellow]⚠ Warning:[/bold yellow] this worktree has unstaged changes.\n"
                    "They will be permanently lost if you continue.",
                    id="notice",
                )
            with Static(id="btn-row"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                if not self._blocked:
                    yield Button("Yes, remove", variant="error", id="btn-yes")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-yes")

    def action_cancel(self) -> None:
        self.dismiss(False)

    def action_confirm(self) -> None:
        if not self._blocked:
            self.dismiss(True)
