from __future__ import annotations

import argparse

from ..config import load_config
from ..storage import list_kbs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List all local knowledge bases.")
    parser.add_argument("--host", default=None, help="Host target: codex, openclaw, or claude-code.")
    parser.add_argument("--data-root", default=None, help="Override the skill data root directory.")
    parser.add_argument("--env-file", default=None, help="Optional .env file.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(host=args.host, data_root=args.data_root, env_file=args.env_file)
    items = list_kbs(config)
    if not items:
        print("No knowledge bases found.")
        return
    for item in items:
        print(f"{item['kb_name']} | {item['root']}")


if __name__ == "__main__":
    main()
