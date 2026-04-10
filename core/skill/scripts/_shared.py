from __future__ import annotations

import os
from pathlib import Path
import sys


def resolve_project_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (
            (candidate / "requirements.txt").exists()
            and (
                ((candidate / "scripts").is_dir() and (candidate / "runtime").is_dir())
                or (
                    (candidate / "core" / "skill" / "scripts").is_dir()
                    and (candidate / "core" / "runtime").is_dir()
                )
            )
        ):
            return candidate
    raise SystemExit(f"Could not resolve local-rag-kb project root from {current}")


def prefer_local_python(project_root: Path) -> None:
    local_python = project_root / ".venv" / "bin" / "python"
    if not local_python.exists():
        return
    if os.environ.get("LOCAL_RAG_KB_SKIP_REEXEC") == "1":
        return
    current_python = Path(sys.executable).resolve()
    local_python = local_python.resolve()
    if current_python == local_python:
        return
    env = os.environ.copy()
    env["LOCAL_RAG_KB_SKIP_REEXEC"] = "1"
    os.execve(str(local_python), [str(local_python), *sys.argv], env)


def bootstrap_runtime_path() -> None:
    project_root = resolve_project_root()
    prefer_local_python(project_root)
    candidates = [
        project_root / "runtime",
        project_root / "core" / "runtime",
    ]
    for candidate in candidates:
        if candidate.exists():
            sys.path.insert(0, str(candidate))
            return
    raise SystemExit("Could not locate runtime/ next to the skill scripts.")
