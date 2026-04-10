#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
CORE_SKILL = ROOT / "core" / "skill"
CORE_RUNTIME = ROOT / "core" / "runtime"
WRAPPERS = ROOT / "wrappers"
DIST = ROOT / "dist"
SKILL_NAME = "local-rag-kb"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build dist targets for local-rag-kb skill hosts.")
    parser.add_argument("--host", choices=["all", "openclaw", "codex", "claude-code"], default="all")
    return parser


def render_skill_md(host: str) -> str:
    template = (CORE_SKILL / "SKILL.template.md").read_text(encoding="utf-8")
    host_meta = json.loads((WRAPPERS / host / "host.json").read_text(encoding="utf-8"))
    return (
        template.replace("{{HOST_NAME}}", host_meta["host_name"])
        .replace("{{HOST_TRIGGER_SNIPPET}}", host_meta["trigger_snippet"])
    )


def copy_tree(source: Path, destination: Path) -> None:
    if source.exists():
        shutil.copytree(source, destination)


def build_host(host: str) -> Path:
    host_root = DIST / host
    skill_root = host_root / SKILL_NAME
    if host_root.exists():
        shutil.rmtree(host_root)
    host_root.mkdir(parents=True, exist_ok=True)

    copy_tree(CORE_SKILL / "scripts", skill_root / "scripts")
    copy_tree(CORE_SKILL / "references", skill_root / "references")
    if (CORE_SKILL / "assets").exists():
        copy_tree(CORE_SKILL / "assets", skill_root / "assets")
    copy_tree(CORE_RUNTIME, skill_root / "runtime")

    (skill_root / "SKILL.md").write_text(render_skill_md(host), encoding="utf-8")
    shutil.copy2(ROOT / "requirements.txt", skill_root / "requirements.txt")
    shutil.copy2(ROOT / ".env.example", skill_root / ".env.example")

    openai_yaml = WRAPPERS / host / "openai.yaml"
    if openai_yaml.exists():
        agents_dir = skill_root / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(openai_yaml, agents_dir / "openai.yaml")

    claude_md = WRAPPERS / host / "CLAUDE.md"
    if claude_md.exists():
        shutil.copy2(claude_md, host_root / "CLAUDE.md")

    return skill_root


def main() -> None:
    args = build_parser().parse_args()
    hosts = ["openclaw", "codex", "claude-code"] if args.host == "all" else [args.host]
    for host in hosts:
        target = build_host(host)
        print(f"Built {host}: {target}")


if __name__ == "__main__":
    main()
