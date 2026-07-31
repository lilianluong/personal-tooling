# Personal Claude Instructions

## Behavior

- Don't add comments, docstrings, or type annotations to code I didn't touch.
- Don't add error handling or validation beyond what the task requires.
- Code comments state what a thing *is*, in a short one-liner. Never explain *why* a decision was made and never narrate past design (what the code used to do, what was broken, what changed) — rationale and history go in the PR/commit, not the code.

- Never post comments or reviews on GitHub PRs unless explicitly asked. When asked to "comment on" or "respond to" PR comments, summarize or reply in the chat — do not post to GitHub.

## Git workflow

- Use **Graphite** (`gt`) for stacked PR work; fall back to **git-branchless** only if `gt` is not available.
- Branch naming convention: `$TOOLING_USER/category/change` (e.g. `lilian/auth/add-model`). `$TOOLING_USER` is set in `~/.config/personal-tooling/config`.
- PR title format: `[Category][Optional sub-category] Stack Title [X/N]: PR title` — e.g. `[Voice][UX] Better logging [1/2]: update deps`.
- See the `graphite` skill for `gt` commands, or the `git-branchless` skill for `git sl` / `git submit` commands.
