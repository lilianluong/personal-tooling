# Personal Claude Instructions

## Behavior

- Don't add comments, docstrings, or type annotations to code I didn't touch.
- Don't add error handling or validation beyond what the task requires.

## Git workflow

- Use **Graphite** (`gt`) for stacked PR work; fall back to **git-branchless** only if `gt` is not available.
- Branch naming convention: `$TOOLING_USER/category/change` (e.g. `lilian/auth/add-model`). `$TOOLING_USER` is set in `~/.config/personal-tooling/config`.
- PR title format: `[Category][Optional sub-category] Stack Title [X/N]: PR title` — e.g. `[Voice][UX] Better logging [1/2]: update deps`.
- See the `graphite` skill for `gt` commands, or the `git-branchless` skill for `git sl` / `git submit` commands.
