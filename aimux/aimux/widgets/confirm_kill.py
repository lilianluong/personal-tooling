"""Kill confirmation modal."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class ConfirmKill(ModalScreen[bool]):
    """Ask user to confirm killing a session."""

    DEFAULT_CSS = """
    ConfirmKill {
        align: center middle;
    }

    ConfirmKill > Static {
        width: 50;
        background: $surface;
        border: solid $error;
        padding: 1 2;
    }

    ConfirmKill #kill-title {
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }

    ConfirmKill #kill-msg {
        margin-bottom: 1;
    }

    ConfirmKill #btn-row {
        layout: horizontal;
        height: 3;
        align-horizontal: right;
    }

    ConfirmKill Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("y", "confirm", "Yes"),
    ]

    def __init__(self, session_name: str) -> None:
        super().__init__()
        self.session_name = session_name

    def compose(self) -> ComposeResult:
        with Static():
            yield Label("Kill session?", id="kill-title")
            yield Label(
                f"This will kill [bold]{self.session_name}[/bold] and its tmux session.",
                id="kill-msg",
            )
            with Static(id="btn-row"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Kill", variant="error", id="btn-kill")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-kill")

    def action_cancel(self) -> None:
        self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)
