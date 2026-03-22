"""Git repo and worktree auto-discovery under ~.

Scans the home directory (max depth 3) for git repos, then expands each
repo's worktrees via `git worktree list`. Results are cached for the
lifetime of the process; call discover_workspaces(refresh=True) to re-scan.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


MAX_DEPTH = 3
_SKIP_DIRS = {
    ".cache", ".local", ".config", ".mozilla", ".npm", ".nvm",
    ".cargo", ".rustup", "node_modules", ".git",
}


@dataclass(frozen=True)
class Workspace:
    path: Path          # absolute path to the worktree/repo
    repo_root: Path     # absolute path to the main repo (may == path)
    is_worktree: bool   # True if this is a linked worktree, False if main

    @property
    def display(self) -> str:
        home = Path.home()
        try:
            return "~/" + str(self.path.relative_to(home))
        except ValueError:
            return str(self.path)


_cache: list[Workspace] | None = None


def discover_workspaces(refresh: bool = False) -> list[Workspace]:
    """Return all discovered workspaces, sorted by path."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    _cache = _scan()
    return _cache


def _scan() -> list[Workspace]:
    home = Path.home()
    git_dirs: set[Path] = set()
    _walk(home, 0, git_dirs)

    workspaces: list[Workspace] = []
    seen: set[Path] = set()

    for git_dir in sorted(git_dirs):
        worktrees = _get_worktrees(git_dir)
        for wt in worktrees:
            if wt.path not in seen:
                seen.add(wt.path)
                workspaces.append(wt)

    return sorted(workspaces, key=lambda w: w.path)


def _walk(directory: Path, depth: int, result: set[Path]) -> None:
    if depth > MAX_DEPTH:
        return
    try:
        entries = list(directory.iterdir())
    except PermissionError:
        return

    has_git = any(e.name == ".git" for e in entries)
    if has_git:
        result.add(directory)
        return  # don't descend further into a repo (worktrees handled separately)

    for entry in entries:
        if not entry.is_dir() or entry.is_symlink():
            continue
        if entry.name in _SKIP_DIRS or entry.name.startswith("."):
            continue
        _walk(entry, depth + 1, result)


def _get_worktrees(repo_path: Path) -> list[Workspace]:
    """Run `git worktree list` and return all worktrees for this repo."""
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return [Workspace(path=repo_path, repo_root=repo_path, is_worktree=False)]

    if result.returncode != 0:
        return [Workspace(path=repo_path, repo_root=repo_path, is_worktree=False)]

    worktrees: list[Workspace] = []
    current_path: Path | None = None
    is_bare = False

    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            current_path = Path(line[len("worktree "):])
        elif line == "bare":
            is_bare = True
        elif line == "" and current_path is not None:
            if not is_bare:
                is_wt = current_path != repo_path
                worktrees.append(Workspace(
                    path=current_path,
                    repo_root=repo_path,
                    is_worktree=is_wt,
                ))
            current_path = None
            is_bare = False

    # Handle last entry (no trailing blank line)
    if current_path is not None and not is_bare:
        is_wt = current_path != repo_path
        worktrees.append(Workspace(
            path=current_path,
            repo_root=repo_path,
            is_worktree=is_wt,
        ))

    return worktrees if worktrees else [Workspace(path=repo_path, repo_root=repo_path, is_worktree=False)]
