# Personal Claude Instructions

## Behavior

- Don't add comments, docstrings, or type annotations to code I didn't touch.
- Don't add error handling or validation beyond what the task requires.

## Git workflow

- Use git-branchless for stacked PR work.
- Each PR in a stack = one commit (or a small cohesive group of commits), on a named branch.
- Branch naming convention: `$TOOLING_USER/category/change` (e.g. `lilian/auth/add-model`). `$TOOLING_USER` is set in `~/.config/personal-tooling/config`.
- After amending any commit, run `git restack` to rebase descendants.
- Use `git sl` to visualize the current stack before and after operations.
