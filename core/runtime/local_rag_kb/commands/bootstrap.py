from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

from ..config import PROJECT_ROOT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap the local-rag-kb skill runtime.")
    parser.add_argument("--python", default=sys.executable, help="Python interpreter to use for the virtual environment.")
    parser.add_argument("--venv", default=str(PROJECT_ROOT / ".venv"), help="Virtualenv path.")
    parser.add_argument("--upgrade-pip", action="store_true", help="Upgrade pip before installing dependencies.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    venv_path = Path(args.venv).expanduser().resolve()
    requirements_path = PROJECT_ROOT / "requirements.txt"
    if not requirements_path.exists():
        raise SystemExit(f"requirements.txt not found at {requirements_path}")

    if not venv_path.exists():
        subprocess.run([args.python, "-m", "venv", str(venv_path)], check=True)

    pip_path = venv_path / "bin" / "pip"
    if args.upgrade_pip:
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(pip_path), "install", "-r", str(requirements_path)], check=True)
    print(f"Bootstrap complete: {venv_path}")


if __name__ == "__main__":
    main()
