from __future__ import annotations

import argparse
from pathlib import Path

from ..config import load_config
from ..operations import ingest_input


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest a file or archive into a local knowledge base.")
    parser.add_argument("--kb", default=None, help="Knowledge-base name. Defaults to the configured default KB.")
    parser.add_argument("--input", required=True, help="Path to a .md, .txt, .zip, .tar, .tar.gz, or .tgz file.")
    parser.add_argument("--mode", choices=["append", "replace-kb"], default="append", help="Ingestion mode.")
    parser.add_argument("--parser", choices=["auto", "markdown", "txt"], default="auto", help="Parser override.")
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
    report = ingest_input(
        config,
        kb_name,
        Path(args.input),
        mode=args.mode,
        parser=args.parser,
        local_test_embeddings=args.local_test_embeddings,
    )
    print(f"KB: {report.kb_name}")
    print(f"Input: {report.input_path}")
    print(f"Mode: {report.mode}")
    print(f"Supported files: {len(report.supported_files)}")
    print(f"Skipped files: {len(report.skipped_files)}")
    print(f"Updated docs: {len(report.updated_docs)}")
    print(f"Unchanged docs: {len(report.unchanged_docs)}")
    print(f"Replaced docs: {len(report.replaced_docs)}")
    print(f"Total chunks: {report.total_chunks}")
    if report.updated_docs:
        print("Updated:")
        for item in report.updated_docs:
            print(f"- {item}")
    if report.skipped_files:
        print("Skipped:")
        for item in report.skipped_files:
            print(f"- {item}")
    if report.unchanged_docs:
        print("Unchanged:")
        for item in report.unchanged_docs:
            print(f"- {item}")


if __name__ == "__main__":
    main()
