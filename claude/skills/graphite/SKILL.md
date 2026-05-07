---
name: graphite
description: Use when managing stacked PRs with Graphite (gt). Reference for gt commands, stacked PR workflow, and amending commits mid-stack.
---

Use this skill when managing stacked PRs with Graphite (`gt`).

## Mental model

Graphite tracks a stack of branches, each building on its parent. Each PR in a stack = one named branch with one cohesive commit (or small group of commits). Branches follow the convention `$TOOLING_USER/category/change` (e.g. `lilian/auth/add-model`).

## Key commands

| Command | What it does |
|---|---|
| `gt state` | Show branch state as JSON — use this to understand stack structure |
| `gt create -a -m "msg"` | Stage all changes, create a new branch, and commit |
| `gt modify -a` | Stage all changes and amend the current branch's commit |
| `gt restack` | Rebase all upstack branches after modifying a commit |
| `gt submit --stack` | Create or update all PRs in the stack |
| `gt sync` | Pull latest trunk, rebase open stacks, prune merged branches |
| `gt checkout` | Interactively check out any branch |
| `gt up` / `gt down` | Move one branch up or down the stack |

## Stacked PR workflow

1. Start from trunk (main): `gt sync`
2. For each PR in the stack: `gt create -a -m "commit message"`
3. Check stack structure: `gt state`
4. Push the stack: `gt submit --stack`

## Amending a commit mid-stack

```bash
gt checkout <branch>   # or gt up/down to navigate
gt modify -a           # amend with staged/all changes
gt restack             # rebase all upstack branches
gt submit --stack      # push updated stack
```

## PR title format

`[Category][Optional sub-category] Stack Title [X/N]: PR title`

Example: `[Voice][UX] Better logging [1/2]: update deps`
