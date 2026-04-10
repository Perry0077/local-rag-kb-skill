from __future__ import annotations

import shutil
import tarfile
import zipfile
from pathlib import Path

from .models import ExtractedInput
from .utils import SUPPORTED_TEXT_SUFFIXES, ensure_directory


def is_archive(path: Path) -> bool:
    lower = path.name.lower()
    return lower.endswith(".zip") or lower.endswith(".tar") or lower.endswith(".tar.gz") or lower.endswith(".tgz")


def extract_input(input_path: Path, staging_dir: Path) -> ExtractedInput:
    resolved = input_path.expanduser().resolve()
    if not resolved.exists():
        raise SystemExit(f"Input path does not exist: {resolved}")

    ensure_directory(staging_dir)
    if resolved.is_dir():
        files, skipped = _scan_files(resolved)
        return ExtractedInput(root_dir=resolved, files=files, extracted=False, skipped_files=skipped)

    if resolved.is_file() and resolved.suffix.lower() in {".md", ".markdown", ".txt"}:
        return ExtractedInput(root_dir=resolved.parent, files=[resolved], extracted=False, skipped_files=[])

    if not is_archive(resolved):
        raise SystemExit(f"Unsupported input type: {resolved.name}")

    extract_root = staging_dir / resolved.stem.replace(".", "_")
    if extract_root.exists():
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True, exist_ok=True)

    if resolved.name.lower().endswith(".zip"):
        with zipfile.ZipFile(resolved, "r") as archive:
            _safe_extract_zip(archive, extract_root)
    else:
        with tarfile.open(resolved, "r:*") as archive:
            _safe_extract_tar(archive, extract_root)

    files, skipped = _scan_files(extract_root)
    return ExtractedInput(root_dir=extract_root, files=files, extracted=True, cleanup_dir=extract_root, skipped_files=skipped)


def _safe_extract_zip(archive: zipfile.ZipFile, destination: Path) -> None:
    for member in archive.infolist():
        target = destination / member.filename
        if not str(target.resolve()).startswith(str(destination.resolve())):
            raise SystemExit(f"Unsafe zip member path: {member.filename}")
    archive.extractall(destination)


def _safe_extract_tar(archive: tarfile.TarFile, destination: Path) -> None:
    for member in archive.getmembers():
        target = destination / member.name
        if not str(target.resolve()).startswith(str(destination.resolve())):
            raise SystemExit(f"Unsafe tar member path: {member.name}")
    archive.extractall(destination)


def _scan_files(root_dir: Path) -> tuple[list[Path], list[str]]:
    supported: list[Path] = []
    skipped: list[str] = []
    for path in sorted(root_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root_dir).as_posix()
        if path.suffix.lower() in SUPPORTED_TEXT_SUFFIXES:
            supported.append(path)
        else:
            skipped.append(relative)
    return supported, skipped
