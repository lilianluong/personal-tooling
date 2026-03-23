"""New session modal: workspace picker + name prompt."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from aimux.discovery import Workspace, discover_workspaces


class WorkspacePicker(ModalScreen[Workspace | None]):
    """Step 1: pick a workspace from the discovered list."""

    DEFAULT_CSS = """
    WorkspacePicker {
        align: center middle;
    }

    WorkspacePicker > Static {
        width: 70;
        max-height: 24;
        background: $surface;
        border: solid $accent;
        padding: 1 2;
    }

    WorkspacePicker #picker-title {
        text-style: bold;
        margin-bottom: 1;
    }

    WorkspacePicker #filter-input {
        margin-bottom: 1;
    }

    WorkspacePicker ListView {
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
            yield Label("Select a workspace", id="picker-title")
            yield Input(placeholder="Type to filter...", id="filter-input")
            yield ListView(id="workspace-list")

    def on_mount(self) -> None:
        self._all_workspaces = discover_workspaces()
        self._render_list(self._all_workspaces)
        self.query_one("#filter-input", Input).focus()

    def _render_list(self, workspaces: list[Workspace]) -> None:
        lv = self.query_one("#workspace-list", ListView)
        lv.clear()
        for ws in workspaces:
            item = ListItem(Label(ws.display))
            item._workspace = ws  # type: ignore[attr-defined]
            lv.append(item)

    def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value.lower()
        filtered = [
            ws for ws in self._all_workspaces
            if query in ws.display.lower()
        ]
        self._render_list(filtered)

    def on_input_submitted(self, _: Input.Submitted) -> None:
        """Enter in the filter input selects the highlighted list item."""
        self._select_highlighted()

    def action_list_up(self) -> None:
        self.query_one("#workspace-list", ListView).action_cursor_up()

    def action_list_down(self) -> None:
        self.query_one("#workspace-list", ListView).action_cursor_down()

    def _select_highlighted(self) -> None:
        lv = self.query_one("#workspace-list", ListView)
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


class SessionNamePrompt(ModalScreen[str | None]):
    """Step 2: enter a name for the new session."""

    DEFAULT_CSS = """
    SessionNamePrompt {
        align: center middle;
    }

    SessionNamePrompt > Static {
        width: 60;
        background: $surface;
        border: solid $accent;
        padding: 1 2;
    }

    SessionNamePrompt #prompt-title {
        text-style: bold;
        margin-bottom: 1;
    }

    SessionNamePrompt #workspace-label {
        color: $text-muted;
        margin-bottom: 1;
    }

    SessionNamePrompt #name-input {
        margin-bottom: 1;
    }

    SessionNamePrompt #btn-row {
        layout: horizontal;
        height: 3;
        align-horizontal: right;
    }

    SessionNamePrompt Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, workspace: Workspace) -> None:
        super().__init__()
        self.workspace = workspace

    def compose(self) -> ComposeResult:
        with Static():
            yield Label("New session", id="prompt-title")
            yield Label(f"Workspace: {self.workspace.display}", id="workspace-label")
            yield Input(placeholder="Session name (e.g. refactor-auth)", id="name-input")
            with Static(id="btn-row"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Create", variant="primary", id="btn-create")

    def on_mount(self) -> None:
        self.query_one("#name-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-create":
            self._submit()
        else:
            self.dismiss(None)

    def on_input_submitted(self, _: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        name = self.query_one("#name-input", Input).value.strip()
        if name:
            self.dismiss(name)

    def action_cancel(self) -> None:
        self.dismiss(None)
