from __future__ import annotations

import argparse

from ..answering import (
    build_host_answer_bundle,
    extract_cited_reference_indices,
    format_host_answer_bundle_json,
    format_references,
    generate_answer,
)
from ..config import load_config
from ..operations import ensure_kb_ready, resolve_query_kb_name
from ..retrieval import format_hits, query_kb


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query a local knowledge base.")
    parser.add_argument("--kb", default=None, help="Knowledge-base name.")
    parser.add_argument("--question", required=True, help="Question text to search for.")
    parser.add_argument("--top-k", type=int, default=None, help="How many hits to show.")
    parser.add_argument("--retrieve-k", type=int, default=None, help="How many candidate chunks to retrieve.")
    parser.add_argument("--answer", action="store_true", help="Generate an answer with references.")
    parser.add_argument(
        "--emit-host-bundle",
        action="store_true",
        help="Emit a structured JSON bundle for host-model orchestration instead of generating the answer inside Python.",
    )
    parser.add_argument("--show-details", action="store_true", help="Show answer contexts and raw retrieved hits.")
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
    kb_name = resolve_query_kb_name(config, args.kb)
    paths, registry = ensure_kb_ready(config, kb_name)
    try:
        result = query_kb(
            config,
            paths,
            registry,
            args.question,
            top_k=args.top_k,
            retrieve_k=args.retrieve_k,
            local_test_embeddings=args.local_test_embeddings,
        )
        if not result.hits:
            print("No results found.")
            return

        if args.emit_host_bundle:
            bundle = build_host_answer_bundle(
                args.question,
                kb_name,
                result.contexts,
                result.hits,
                include_hits=args.show_details,
            )
            print(format_host_answer_bundle_json(bundle))
        elif args.answer:
            answer = generate_answer(config, args.question, result.contexts)
            cited = extract_cited_reference_indices(answer)
            print("Answer:")
            print(answer)
            print("")
            print(format_references(result.contexts, cited))
            if args.show_details:
                print("")
                print("Answer Contexts:")
                for index, context in enumerate(result.contexts, start=1):
                    print(
                        f"[{index}] {context.title} | {context.source_rel_path} | "
                        f"mode={context.mode} | hits={context.hit_count}"
                    )
                print("")
                print(format_hits(result.hits))
        else:
            print(format_hits(result.hits))
    finally:
        registry.close()


if __name__ == "__main__":
    main()
