"""Agent launch commands for aimux sessions."""

from __future__ import annotations

DEFAULT_AGENT = "claude"

AGENT_COMMANDS: dict[str, str] = {
    "claude": "claude --dangerously-skip-permissions",
    "codex": "codex --dangerously-bypass-approvals-and-sandbox --dangerously-bypass-hook-trust",
}
