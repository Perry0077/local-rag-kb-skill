from __future__ import annotations

import argparse

from ..config import load_config
from ..operations import rebuild_kb


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rebuild a knowledge base from cached documents.")
    parser.add_argument("--kb", default=None, help="Knowledge-base name.")
    parser.add_argument("--host", default=None, help="Host target: codex, openclaw, or claude-code.")
    parser.add_argument("--data-root", default=None, help="Override the skill data root directory.")
    parser.add_argument("--env-file", default=None, help="Optional .env file.")
    parser.add_argument(
        "--local-test-embeddings",
        action="store_true",
        help="Use deterministic local embeddings for testing without a remote embedding API.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(host=args.host, data_root=args.data_root, env_file=args.env_file)
    kb_name = args.kb or config.default_kb_name
    chunk_count = rebuild_kb(config, kb_name, local_test_embeddings=args.local_test_embeddings)
    print(f"Rebuilt KB: {kb_name}")
    print(f"Chunks: {chunk_count}")


if __name__ == "__main__":
    main()
