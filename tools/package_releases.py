#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
RELEASES = ROOT / "release"
SKILL_NAME = "local-rag-kb"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Package built skill targets into zip files for GitHub releases.")
    parser.add_argument("--host", choices=["all", "openclaw", "codex", "claude-code"], default="all")
    return parser


def package_host(host: str) -> Path:
    source_dir = DIST / host / SKILL_NAME
    if not source_dir.exists():
        raise SystemExit(f"Build output missing for {host}: {source_dir}. Run tools/build_targets.py first.")
    RELEASES.mkdir(parents=True, exist_ok=True)
    archive_base = RELEASES / f"{SKILL_NAME}-{host}"
    archive_path = shutil.make_archive(str(archive_base), "zip", root_dir=source_dir.parent, base_dir=source_dir.name)
    return Path(archive_path)


def main() -> None:
    args = build_parser().parse_args()
    hosts = ["openclaw", "codex", "claude-code"] if args.host == "all" else [args.host]
    for host in hosts:
        archive = package_host(host)
        print(f"Packaged {host}: {archive}")


if __name__ == "__main__":
    main()
