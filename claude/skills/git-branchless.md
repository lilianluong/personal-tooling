# git-branchless

Use this skill when managing stacked PRs.

## Mental model

git-branchless tracks commits by hash in a DAG — not by branch name. Branches are optional labels that don't affect correctness. Always create named branches for readability using the convention `$TOOLING_USER/category/change` (e.g. `lilian/auth/add-model`, `lilian/auth/add-routes`).

## Setup (per repo)

```bash
git branchless init
```

## Key commands

| Command | What it does |
|---|---|
| `git sl` | Visualize the commit graph (smartlog) |
| `git submit --stack` | Create or update all PRs in the stack |
| `git sync` | Pull from main and restack |
| `git restack` | Rebase all descendants after amending a commit |
| `git restack --continue` | Resume restack after resolving a conflict |

## Stacked PR workflow

1. For each PR, create a named branch and commit: `git checkout -b $TOOLING_USER/category/change && git commit`
2. Use descriptive commit messages; they become PR titles
3. `git sl` to verify the stack looks right
4. `git submit --stack` to push all PRs to GitHub

## Amending a commit mid-stack

```bash
git rebase -i    # amend the target commit
git restack      # rebase all descendants onto the new commit
```
