#!/usr/bin/env bash
# aimux/setup.sh — install aimux and register Claude Code hooks
# Safe to run multiple times.

set -euo pipefail

AIMUX_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

green() { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }

# ── install uv ────────────────────────────────────────────────────────────────

export PATH="$HOME/.local/bin:$PATH"

if command -v uv &>/dev/null; then
  yellow "  already installed: uv"
else
  echo "  installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  green "  installed: uv"
fi

# ── install aimux ─────────────────────────────────────────────────────────────

echo "  installing aimux..."
uv tool install --editable "$AIMUX_DIR" --reinstall
green "  installed: aimux"

# ── register hooks (added in aimux/hooks commit) ──────────────────────────────
# Hook registration will be added here once hooks are implemented.
