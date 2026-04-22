"""Right panel: session detail view.

Shows for a selected session:
  - Live tmux pane preview (last N lines)
  - Cost breakdown (input/output tokens, cost, context%)
  - git status of the session's worktree
"""

from __future__ import annotations

import subprocess
import time

from rich.markup import escape
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static

from aimux.state import SessionInfo, SessionState
from aimux.tmux import capture_pane, session_exists


class DetailPanel(Widget):
    """Right panel showing details for the selected session."""

    DEFAULT_CSS = """
    DetailPanel {
        width: 2fr;
        height: 1fr;
        padding: 0 1;
    }

    DetailPanel #detail-header {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    DetailPanel #pane-preview {
        height: 12;
        border: solid $panel-lighten-1;
        background: $surface;
        padding: 0 1;
        overflow-y: auto;
        margin-bottom: 1;
    }

    DetailPanel #cost-section {
        margin-bottom: 1;
    }

    DetailPanel .section-title {
        text-style: bold;
        color: $text-muted;
    }

    DetailPanel #git-section {
        height: auto;
    }

    DetailPanel #no-selection {
        color: $text-muted;
        text-align: center;
        margin-top: 4;
    }
    """

    selected: reactive[tuple[SessionInfo, SessionState] | None] = reactive(None)

    def compose(self) -> ComposeResult:
        yield Label("No session selected.", id="no-selection")
        yield Static("", id="detail-header")
        yield Static("", id="pane-preview")
        yield Static("", id="cost-section")
        yield Static("", id="git-section")

    def watch_selected(self, value: tuple[SessionInfo, SessionState] | None) -> None:
        self._draw(value)

    def refresh_detail(self) -> None:
        """Called by the app on its poll interval to refresh live data."""
        self._draw(self.selected)

    def _draw(self, value: tuple[SessionInfo, SessionState] | None) -> None:
        no_sel = self.query_one("#no-selection", Label)
        header = self.query_one("#detail-header", Static)
        pane = self.query_one("#pane-preview", Static)
        cost = self.query_one("#cost-section", Static)
        git = self.query_one("#git-section", Static)

        if value is None:
            no_sel.display = True
            header.display = False
            pane.display = False
            cost.display = False
            git.display = False
            return

        no_sel.display = False
        info, state = value
        header.display = True
        pane.display = True
        cost.display = True
        git.display = True

        header.update(escape(f"{info.name}  —  {info.workspace}"))

        # Pane preview
        if session_exists(info.id):
            raw = capture_pane(info.id, lines=20)
            pane.update(escape(raw) if raw else "(empty)")
        else:
            pane.update("(session not running)")

        # Cost breakdown
        idle_str = ""
        if state.idle_since:
            secs = int(time.time() - state.idle_since)
            idle_str = f"  •  idle {secs}s"
        cost.update(
            f"[bold]Cost[/bold]\n"
            f"  Input:   {state.input_tokens:,} tokens\n"
            f"  Output:  {state.output_tokens:,} tokens\n"
            f"  Total:   ${state.cost_usd:.4f}\n"
            f"  Context: {state.context_pct:.1f}%{idle_str}"
        )

        # Git status
        git_out = _git_status(info.workspace)
        if git_out:
            git.update(f"[bold]Git status[/bold]\n{escape(git_out)}")
        else:
            git.update("[bold]Git status[/bold]\n  (clean)")


def _git_status(workspace: str) -> str:
    """Return `git status --short` output for the workspace."""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().splitlines()
            return "\n".join(f"  {line}" for line in lines[:20])
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return ""
