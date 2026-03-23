#!/usr/bin/env python3
"""Claude Code SessionStart hook — registers session with aimux state.

Only runs when AIMUX_SESSION_ID is set (i.e., when launched by aimux).
"""

import json
import os
import sys
from pathlib import Path

# Must happen before any aimux imports — hook runs with system python3
_pkg_root = str(Path(__file__).parent.parent.parent)
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)


def main() -> None:
    session_id = os.environ.get("AIMUX_SESSION_ID")
    if not session_id:
        return

    payload = json.loads(sys.stdin.read())
    workspace = payload.get("cwd", "")

    from aimux.state import SessionInfo, SessionState, register_session, update_session_state

    info = SessionInfo(
        id=session_id,
        name=session_id,
        workspace=workspace,
        tmux_session=f"aimux-{session_id}",
    )
    register_session(info)

    state = SessionState(id=session_id, status="active")
    update_session_state(state)


if __name__ == "__main__":
    main()
