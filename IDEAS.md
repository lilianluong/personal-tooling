# Ideas

## TUI Session Manager

## Shell Config + Bootstrap.sh

## Task Tracker

## DAG Orchestrator

Takes the output of Claude plan mode (a structured `PLAN.md`), decomposes it into a strict DAG of work items with multiple independent roots where possible, and orchestrates execution by spawning `claude` sessions in parallel git worktrees for each node. Includes a local Vite + React Flow web app that visualizes the DAG in real-time, showing node status (pending / in-progress / done / failed) as agents complete their work.

## PR Stacking CLI

A CLI for managing commit-level stacked PRs (Graphite-style: 1 commit = 1 PR). Each commit on a branch becomes its own PR, chained so that PR B's base is PR A's branch. Commands: push the full stack (creating or updating PRs), sync after a merge (rebase remaining stack onto new base), list the stack with live PR status, and land the bottom PR then auto-sync the rest.

## PR Babysitter

Polls your open PRs and takes action when problems are found. For CI failures: fetches the logs, spawns a Claude session to analyze and push a fix. For merge conflicts: spawns Claude to resolve and push. Runs as a background daemon or via a cron-style loop, notifying you of what it attempted and whether it succeeded.
