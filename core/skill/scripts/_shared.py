from __future__ import annotations

from pathlib import Path
import sys


def bootstrap_runtime_path() -> None:
    current = Path(__file__).resolve()
    candidates = [
        current.parents[1] / "runtime",
        current.parents[2] / "runtime",
    ]
    for candidate in candidates:
        if candidate.exists():
            sys.path.insert(0, str(candidate))
            return
    raise SystemExit("Could not locate runtime/ next to the skill scripts.")
