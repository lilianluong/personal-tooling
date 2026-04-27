from __future__ import annotations

import argparse
import os
import sys


def main() -> None:
    if len(sys.argv) > 1:
        _run_cli()
    else:
        from aimux.app import AimuxApp
        AimuxApp().run()


def _run_cli() -> None:
    parser = argparse.ArgumentParser(prog="aimux")
    sub = parser.add_subparsers(dest="command")

    sp = sub.add_parser("spawn", help="Spawn a new aimux session")
    sp.add_argument("--workspace", default=os.getcwd(), help="Working directory (default: cwd)")
    sp.add_argument("--name", required=True, help="Session name/slug")
    sp.add_argument("--prompt", default=None, help="Initial prompt to send to claude")

    cp = sub.add_parser("cycle", help="Cycle to prev/next session in menu order")
    cp.add_argument("direction", choices=["prev", "next"])
    cp.add_argument("--current", required=True, help="Current tmux session name")

    args = parser.parse_args()

    if args.command == "spawn":
        from aimux.spawn import spawn_session
        spawn_session(args.workspace, args.name, args.prompt)
        print(args.name)
    elif args.command == "cycle":
        from aimux.tmux import cycle_session
        cycle_session(args.direction, args.current)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
