# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Personal dev environment config and tooling. Currently contains:

- `bootstrap.sh` — one-shot setup script for a fresh machine (installs tmux, Claude Code, symlinks shell config)
- `shell/dev_tooling` — shell aliases sourced by `.zshrc`/`.bashrc`

Each tool lives as a self-contained subdirectory of this repo. See `IDEAS.md` for planned tools (TUI session manager, DAG orchestrator, PR stacking CLI, PR babysitter).

## Compatibility requirements

All shell scripts must work on both **zsh and bash**, and on both **Linux and macOS**.

- Package installation: use `apt-get` on Linux, `brew` on macOS
- Avoid bashisms when writing scripts intended to be sourced by zsh, and vice versa
- `bootstrap.sh` uses `set -euo pipefail` — maintain this

## bootstrap.sh conventions

- `symlink src dst` — idempotent symlink helper (backs up existing files)
- `add_source_line rc_file line` — idempotently appends a source line to a shell rc file
- `install_pkg pkg` — installs via apt/brew, warns if neither is available
- New tools must live in their own subdirectory and be fully self-contained (dependencies, config, and code all within that directory)
- New tools should get a corresponding install/setup step in `bootstrap.sh`
