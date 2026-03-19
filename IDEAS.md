# Ideas

## DAG Orchestrator

Takes the output of Claude plan mode (a structured `PLAN.md`), decomposes it into a strict DAG of work items with multiple independent roots where possible, and orchestrates execution by spawning `claude` sessions in parallel git worktrees for each node. Includes a local Vite + React Flow web app that visualizes the DAG in real-time, showing node status (pending / in-progress / done / failed) as agents complete their work.

## PR Stacking CLI

A CLI for managing commit-level stacked PRs (Graphite-style: 1 commit = 1 PR). Each commit on a branch becomes its own PR, chained so that PR B's base is PR A's branch. Commands: push the full stack (creating or updating PRs), sync after a merge (rebase remaining stack onto new base), list the stack with live PR status, and land the bottom PR then auto-sync the rest.

## PR Babysitter

Polls your open PRs and takes action when problems are found. For CI failures: fetches the logs, spawns a Claude session to analyze and push a fix. For merge conflicts: spawns Claude to resolve and push. Runs as a background daemon or via a cron-style loop, notifying you of what it attempted and whether it succeeded.

## Git Archaeology

CLI tool that answers "why does this code exist?" by tracing `git blame` → commit → PR → linked issue and outputting a plain-English narrative. Give it a file and line range, get back a summary of the history and intent behind that code.

## Env Doctor

Checks a new machine for all your expected dev tools (node, python, gh, fzf, ripgrep, etc.), shows a pass/fail table, and prints the exact install command for anything missing.

## PR Context Builder

Before opening a PR, generates a rich description by summarizing the diff, linking related files, and suggesting a test plan. Outputs markdown ready to paste into GitHub.

## Repo Summarizer

Walks an unfamiliar repo and generates a `CODEBASE.md` — architecture overview, key files map, data flow, entry points. Useful to drop into context at the start of a Claude session.

## Commit Linter

A `commit-msg` hook that enforces your preferred commit style (conventional commits, length limits, no vague "fix" messages), with Claude suggesting a better message if it fails.

## Scratch

A structured scratchpad convention: timestamped `.md` files for half-baked ideas, gitignored. `scratch new "idea name"` to create, `scratch ls` to list. A fast, low-friction place to dump thoughts without polluting the repo.

## Context Compressor

Takes a directory and produces a single concatenated, annotated text file of all source files (like `files-to-prompt`), optimized for pasting into Claude context. Respects `.gitignore`, adds file headers, optionally strips comments.

## Alias Explainer

A `wtf <command>` tool: given any shell command or alias, explains in plain English what it does. Useful when you come back to your own dotfiles after 6 months.

## Issue to Branch

Given a GitHub issue URL or number, creates a sensibly-named branch, generates a starter `TODO_DO_NOT_COMMIT.md` from the issue body, and optionally opens a Claude session scoped to that task.

## Dotfiles

Standard dotfiles (`.zshrc`, `.gitconfig`, `.vimrc`, `.tmux.conf`) with preferred settings, managed so `bootstrap.sh` can symlink them all in one step on a new machine.

## Claude Cost Tracker

Parses Claude Code session logs to show token usage and estimated cost per session/day/week. Simple script + terminal table output.

## Review Bot

A local pre-push hook that runs Claude on your diff and outputs a structured self-review (potential bugs, missing tests, style issues) before you even open a PR.

## Snippet Library

A searchable, `fzf`-powered collection of code snippets for boilerplate you always look up: argparse setup, async context managers, Dockerfile starters, etc. `snip <query>` to find, pipe to clipboard.

## Tmux Layouts

Named tmux layout presets. `tmux-layout load dev` gives you editor + test runner + Claude pane. Stored as scripts, applied in one command.

## Changelog Writer

Given a tag range (`v1.2..v1.3`), reads all commits and generates a human-readable `CHANGELOG.md` section grouped by type (feat / fix / chore).

## Notification Hook

A Claude Code `Stop` hook that sends a desktop notification (or Slack/Discord webhook) when a long-running Claude session finishes. Never wonder if Claude is done.

## Project Init

`pinit <type> <name>` scaffolds a new project with your preferred structure, drops in the right `CLAUDE.md` template, initializes git, creates a GitHub repo, and opens a Claude session.

## Dependency Changelog

Given a `package.json` or `pyproject.toml`, diffs the current lockfile against `main` and summarizes what changed in each updated dependency by pulling from changelogs and release notes.
