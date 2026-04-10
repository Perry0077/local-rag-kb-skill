#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
SKILL_NAME = "local-rag-kb"
DEFAULT_INSTALL_DIRS = {
    "codex": Path.home() / ".codex" / "skills" / SKILL_NAME,
    "openclaw": Path.home() / ".agents" / "skills" / SKILL_NAME,
    "claude-code": Path.home() / ".claude" / "skills" / SKILL_NAME,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync built skill targets into host install directories.")
    parser.add_argument("--host", choices=["all", "openclaw", "codex", "claude-code"], default="all")
    parser.add_argument("--no-build", action="store_true", help="Skip running build_targets.py first.")
    parser.add_argument("--codex-dir", default=None, help="Override Codex install directory.")
    parser.add_argument("--openclaw-dir", default=None, help="Override OpenClaw install directory.")
    parser.add_argument("--claude-dir", default=None, help="Override Claude Code install directory.")
    return parser


def install_dir_for(host: str, args: argparse.Namespace) -> Path:
    if host == "codex" and args.codex_dir:
        return Path(args.codex_dir).expanduser().resolve()
    if host == "openclaw" and args.openclaw_dir:
        return Path(args.openclaw_dir).expanduser().resolve()
    if host == "claude-code" and args.claude_dir:
        return Path(args.claude_dir).expanduser().resolve()
    return DEFAULT_INSTALL_DIRS[host]


def sync_host(host: str, args: argparse.Namespace) -> Path:
    source = DIST / host / SKILL_NAME
    if not source.exists():
        raise SystemExit(f"Build output missing for {host}: {source}")
    target = install_dir_for(host, args)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    return target


def main() -> None:
    args = build_parser().parse_args()
    hosts = ["openclaw", "codex", "claude-code"] if args.host == "all" else [args.host]
    if not args.no_build:
        subprocess.run([sys.executable, str(ROOT / "tools" / "build_targets.py"), "--host", args.host], check=True)
    for host in hosts:
        target = sync_host(host, args)
        print(f"Synced {host}: {target}")


if __name__ == "__main__":
    main()
