#!/usr/bin/env python3
"""Claude Code PostToolUse hook — decrements bg_tasks when a background Agent finishes.

Fires for the Agent tool; only acts when run_in_background is true.
Only runs when AIMUX_SESSION_ID is set (i.e., when launched by aimux).
"""

import json
import os
import sys
from pathlib import Path

_pkg_root = str(Path(__file__).parent.parent.parent)
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)


def main() -> None:
    session_id = os.environ.get("AIMUX_SESSION_ID")
    if not session_id:
        return

    payload = json.loads(sys.stdin.read())
    if not payload.get("tool_input", {}).get("run_in_background"):
        return

    from aimux.state import get_session_state, update_session_state

    state = get_session_state(session_id)
    state.bg_tasks = max(0, state.bg_tasks - 1)
    update_session_state(state)


if __name__ == "__main__":
    main()
