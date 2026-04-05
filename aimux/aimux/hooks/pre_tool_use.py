#!/usr/bin/env python3
"""Claude Code PreToolUse hook — marks session as waiting when Claude pauses for user input.

Fires for AskUserQuestion (inline Q&A) and ExitPlanMode (plan approval).
Only runs when AIMUX_SESSION_ID is set (i.e., when launched by aimux).
"""

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

    sys.stdin.read()  # consume payload

    from aimux.state import get_session_state, update_session_state
    import time

    state = get_session_state(session_id)
    state.status = "waiting"
    state.idle_since = time.time()
    update_session_state(state)


if __name__ == "__main__":
    main()
