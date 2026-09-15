"""Command-line entrypoint for the Brand World canvas."""

import argparse
from pathlib import Path

from testflight_brand_world.server import serve


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="brand-world")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("workspaces/brand-hellobiotic-research"),
        help="Brand workspace path, relative to --root unless absolute",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8792)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    workspace = args.workspace if args.workspace.is_absolute() else args.root / args.workspace
    serve(args.root.resolve(), workspace.resolve(), args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
