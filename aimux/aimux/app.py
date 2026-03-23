from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label
from textual.binding import Binding


class AimuxApp(App):
    TITLE = "aimux"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]

    CSS = """
    Screen {
        align: center middle;
    }

    #placeholder {
        color: $text-muted;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(
            "aimux — agent session manager\n\nNo sessions yet.",
            id="placeholder",
        )
        yield Footer()
