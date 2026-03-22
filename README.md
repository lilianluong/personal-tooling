# personal-tooling

My personal dev environment config and bootstrap script.

## What's included

- **`bootstrap.sh`** — one-shot setup script for a fresh machine
- **`shell/dev_tooling`** — shell aliases and environment config (git, Claude Code, misc)

## Bootstrap

```bash
git clone <this-repo> ~/personal-tooling
cd ~/personal-tooling
bash bootstrap.sh
```

The script will:

1. Install **tmux** (via `apt` on Linux, `brew` on macOS)
2. Install **Claude Code** (via the official installer)
3. Symlink `shell/dev_tooling` to `~/.dev_tooling`
4. Add a source line to `~/.zshrc` and/or `~/.bashrc` if they exist

## Compatibility

| | Linux | macOS |
|---|---|---|
| zsh | ✓ | ✓ |
| bash | ✓ | ✓ |

Package installation uses `apt-get` on Linux and `brew` on macOS. If neither is found, the script will prompt you to install the package manually.
