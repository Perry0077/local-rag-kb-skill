from __future__ import annotations

import argparse

from ..config import load_config
from ..operations import delete_named_kb


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Delete a local knowledge base.")
    parser.add_argument("--kb", required=True, help="Knowledge-base name.")
    parser.add_argument("--host", default=None, help="Host target: codex, openclaw, or claude-code.")
    parser.add_argument("--data-root", default=None, help="Override the skill data root directory.")
    parser.add_argument("--env-file", default=None, help="Optional .env file.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(host=args.host, data_root=args.data_root, env_file=args.env_file)
    delete_named_kb(config, args.kb)
    print(f"Deleted KB: {args.kb}")


if __name__ == "__main__":
    main()
