#!/usr/bin/env python3
"""Claude Code Stop hook — marks session as waiting, updates cost from transcript.

Only runs when AIMUX_SESSION_ID is set (i.e., when launched by aimux).
"""

import json
import os
import sys
import time
from pathlib import Path

_pkg_root = str(Path(__file__).parent.parent.parent)
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)


def main() -> None:
    session_id = os.environ.get("AIMUX_SESSION_ID")
    if not session_id:
        return

    payload = json.loads(sys.stdin.read())
    transcript_path = payload.get("transcript_path", "")

    from aimux.hooks._common import parse_transcript, context_pct
    from aimux.state import get_session_state, update_session_state

    state = get_session_state(session_id)

    if transcript_path:
        usage = parse_transcript(transcript_path)
        state.input_tokens = usage["input_tokens"]
        state.output_tokens = usage["output_tokens"]
        state.cost_usd = usage["cost_usd"]
        state.context_pct = context_pct(usage["context_input_tokens"], usage["model"])

    state.status = "waiting"
    state.idle_since = time.time()

    update_session_state(state)


if __name__ == "__main__":
    main()
