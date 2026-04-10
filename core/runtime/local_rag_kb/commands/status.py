from __future__ import annotations

import argparse

from ..config import load_config
from ..operations import ensure_kb_ready, resolve_query_kb_name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show status for a knowledge base.")
    parser.add_argument("--kb", default=None, help="Knowledge-base name.")
    parser.add_argument("--host", default=None, help="Host target: codex, openclaw, or claude-code.")
    parser.add_argument("--data-root", default=None, help="Override the skill data root directory.")
    parser.add_argument("--env-file", default=None, help="Optional .env file.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(host=args.host, data_root=args.data_root, env_file=args.env_file)
    kb_name = resolve_query_kb_name(config, args.kb)
    paths, registry = ensure_kb_ready(config, kb_name)
    try:
        stats = registry.stats(kb_name)
        print(f"KB: {kb_name}")
        print(f"Root: {paths.root}")
        print(f"Documents: {stats['documents']}")
        print(f"Chunks: {stats['chunks']}")
        print(f"Collection: {config.collection_name(kb_name)}")
    finally:
        registry.close()


if __name__ == "__main__":
    main()
