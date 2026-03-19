# Ideas

## TUI Session Manager

A tmux wrapper that serves as the main engine for running parallel Claude Code agents. A persistent window shows all active agent sessions in a left panel — each entry displays the session name, current status indicator, and live token/dollar usage. Navigate between sessions with arrow keys. The right panel shows a preview of the selected session's output; press a key to fully expand into that session and another to return to the overview. Wraps tmux under the hood, managing pane creation, attachment, and status polling automatically.

## Shell Config + Bootstrap.sh

A `.aliases` file (or similar) containing all personal shell shortcuts: launching new Claude Code sessions with `--dangerously-skip-permissions`, and variants for resuming, continuing, or starting fresh sessions. Also houses git aliases and other workflow shortcuts. Alongside it, a single `bootstrap.sh` at the root of this repo — since every tool lives as a subdirectory here, this script is the one-stop setup for a new machine: installs dependencies, symlinks configs, and initializes all the projects in one run.

## Task Tracker

## DAG Orchestrator

Takes the output of Claude plan mode (a structured `PLAN.md`), decomposes it into a strict DAG of work items with multiple independent roots where possible, and orchestrates execution by spawning `claude` sessions in parallel git worktrees for each node. Includes a local Vite + React Flow web app that visualizes the DAG in real-time, showing node status (pending / in-progress / done / failed) as agents complete their work.

## PR Stacking CLI

A CLI for managing commit-level stacked PRs (Graphite-style: 1 commit = 1 PR). Each commit on a branch becomes its own PR, chained so that PR B's base is PR A's branch. Commands: push the full stack (creating or updating PRs), sync after a merge (rebase remaining stack onto new base), list the stack with live PR status, and land the bottom PR then auto-sync the rest.

## PR Babysitter

Polls your open PRs and takes action when problems are found. For CI failures: fetches the logs, spawns a Claude session to analyze and push a fix. For merge conflicts: spawns Claude to resolve and push. Runs as a background daemon or via a cron-style loop, notifying you of what it attempted and whether it succeeded.
