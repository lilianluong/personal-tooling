---
name: aimux-spawn
description: Spawn a new Claude Code agent session in aimux. Use when the user asks to create a new agent session, run a task in a new session, or delegate work to a background agent in the TUI.
---

Spawn a new Claude Code agent session in aimux (the TUI session manager). The session is visible in the aimux TUI, tracked for cost, and stays open for follow-up after the initial prompt is answered.

```bash
aimux spawn --workspace <path> --name <slug> --prompt <text>
```

- `--workspace` defaults to cwd
- `--name` is a short kebab-case slug, unique among active sessions
- `--prompt` is the opening message sent to the new agent
