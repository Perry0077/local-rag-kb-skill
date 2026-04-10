#!/usr/bin/env python3
from __future__ import annotations

import gzip
from pathlib import Path
import tarfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
SOURCE_ROOT = FIXTURES / "sources"
OUTPUT_ROOT = FIXTURES / "input"


def build_zip() -> Path:
    target = OUTPUT_ROOT / "nested_docs.zip"
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((SOURCE_ROOT / "archive_zip").rglob("*")):
            if path.is_file():
                archive.write(path, arcname=path.relative_to(SOURCE_ROOT / "archive_zip"))
    return target


def build_tar() -> Path:
    target = OUTPUT_ROOT / "mixed_docs.tar.gz"
    target.parent.mkdir(parents=True, exist_ok=True)

    def normalize(info: tarfile.TarInfo) -> tarfile.TarInfo:
        info.mtime = 0
        info.uid = 0
        info.gid = 0
        info.uname = ""
        info.gname = ""
        return info

    with target.open("wb") as raw_stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_stream, mtime=0) as gzip_stream:
            with tarfile.open(fileobj=gzip_stream, mode="w") as archive:
                for path in sorted((SOURCE_ROOT / "archive_tar").rglob("*")):
                    if path.is_file():
                        archive.add(path, arcname=path.relative_to(SOURCE_ROOT / "archive_tar"), filter=normalize)
    return target


def main() -> None:
    zip_path = build_zip()
    tar_path = build_tar()
    print(f"Built fixtures: {zip_path}")
    print(f"Built fixtures: {tar_path}")


if __name__ == "__main__":
    main()
