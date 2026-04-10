from __future__ import annotations

from pathlib import Path


def _is_source_root(candidate: Path) -> bool:
    return (
        (candidate / "requirements.txt").exists()
        and (candidate / "core" / "runtime").is_dir()
        and (candidate / "core" / "skill" / "scripts").is_dir()
    )


def _is_built_skill_root(candidate: Path) -> bool:
    return (
        (candidate / "requirements.txt").exists()
        and (candidate / "runtime").is_dir()
        and (candidate / "scripts").is_dir()
    )


def resolve_project_root(current_file: str | Path | None = None) -> Path:
    current = Path(current_file or __file__).resolve()
    for candidate in current.parents:
        if _is_built_skill_root(candidate) or _is_source_root(candidate):
            return candidate
    raise RuntimeError(f"Could not resolve local-rag-kb project root from {current}")


PROJECT_ROOT = resolve_project_root()
