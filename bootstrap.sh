#!/usr/bin/env bash
# bootstrap.sh — set up personal dev environment on a fresh machine
# Usage: bash bootstrap.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── helpers ──────────────────────────────────────────────────────────────────

green() { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }

symlink() {
  local src="$1" dst="$2"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    yellow "  already linked: $dst"
  else
    if [ -e "$dst" ] && ! [ -L "$dst" ]; then
      yellow "  backing up existing $dst -> ${dst}.bak"
      mv "$dst" "${dst}.bak"
    fi
    ln -sf "$src" "$dst"
    green "  linked: $dst -> $src"
  fi
}

add_source_line() {
  local rc_file="$1" source_line="$2"
  if [ ! -f "$rc_file" ]; then
    yellow "  $rc_file not found, skipping"
    return
  fi
  if grep -qF "$source_line" "$rc_file"; then
    yellow "  already in $rc_file"
  else
    printf '\n%s\n' "$source_line" >> "$rc_file"
    green "  added to $rc_file"
  fi
}

# ── packages ─────────────────────────────────────────────────────────────────

install_pkg() {
  local pkg="$1"
  if command -v "$pkg" &>/dev/null; then
    yellow "  already installed: $pkg"
  else
    echo "  installing $pkg..."
    if command -v apt-get &>/dev/null; then
      sudo apt-get install -y "$pkg"
    elif command -v brew &>/dev/null; then
      brew install "$pkg"
    else
      yellow "  no supported package manager found, install $pkg manually"
    fi
    green "  installed: $pkg"
  fi
}

# ── user config ──────────────────────────────────────────────────────────────

echo "Setting up user config..."

CONFIG_FILE="$HOME/.config/personal-tooling/config"
if [ -f "$CONFIG_FILE" ]; then
  yellow "  already exists: $CONFIG_FILE"
else
  mkdir -p "$(dirname "$CONFIG_FILE")"
  printf 'Enter your name for git branch prefixes (default: lilian): '
  read -r input_user
  tooling_user="${input_user:-lilian}"
  printf 'TOOLING_USER=%s\n' "$tooling_user" > "$CONFIG_FILE"
  green "  created: $CONFIG_FILE (TOOLING_USER=$tooling_user)"
fi

echo ""

echo "Installing packages..."

install_pkg tmux

if command -v git-branchless &>/dev/null; then
  yellow "  already installed: git-branchless"
else
  echo "  installing git-branchless..."
  if command -v brew &>/dev/null; then
    brew install git-branchless
  elif command -v cargo &>/dev/null; then
    cargo install git-branchless
  else
    yellow "  install git-branchless manually: https://github.com/arxanas/git-branchless"
  fi
  green "  installed: git-branchless"
fi

if command -v claude &>/dev/null; then
  yellow "  already installed: claude"
else
  echo "  installing claude..."
  curl -fsSL https://claude.ai/install.sh | bash
  green "  installed: claude"
fi

echo ""

# ── shell config ─────────────────────────────────────────────────────────────

echo "Setting up shell config..."

symlink "$REPO_DIR/shell/.shell_config" "$HOME/.shell_config"

SOURCE_LINE='[ -f ~/.shell_config ] && source ~/.shell_config'
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'

# Add to whichever rc files exist
for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
  add_source_line "$rc" "$PATH_LINE"
  add_source_line "$rc" "$SOURCE_LINE"
done

echo ""

# ── claude config ─────────────────────────────────────────────────────────────

echo "Setting up Claude config..."

# Mirror claude/ into ~/.claude/, symlinking each file at its relative path
while IFS= read -r -d '' src; do
  rel="${src#"$REPO_DIR/claude/"}"
  dst="$HOME/.claude/$rel"
  mkdir -p "$(dirname "$dst")"
  symlink "$src" "$dst"
done < <(find "$REPO_DIR/claude" -type f -print0)

# Configure statusline in ~/.claude/settings.json (not symlinked — merged in place)
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
mkdir -p "$(dirname "$CLAUDE_SETTINGS")"
if [ ! -f "$CLAUDE_SETTINGS" ]; then
  echo '{}' > "$CLAUDE_SETTINGS"
fi
python3 - "$CLAUDE_SETTINGS" <<'EOF'
import json, sys
path = sys.argv[1]
with open(path) as f:
    s = json.load(f)
s['statusLine'] = {'type': 'command', 'command': 'bash ~/.claude/statusline-command.sh'}
with open(path, 'w') as f:
    json.dump(s, f, indent=2)
    f.write('\n')
EOF
green "  configured statusLine in $CLAUDE_SETTINGS"

echo ""

# ── aimux ─────────────────────────────────────────────────────────────────────

echo "Setting up aimux..."
bash "$REPO_DIR/aimux/setup.sh"
echo ""

green "Done. Restart your shell or run: source ~/.shell_config"
