from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from .models import ParsedDocument
from .utils import SUPPORTED_TEXT_SUFFIXES, sha1_text

FRONTMATTER_RE = re.compile(r"^\s*---\s*$")
INLINE_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")


def detect_parser(path: Path, explicit_parser: Optional[str] = None) -> str:
    if explicit_parser and explicit_parser != "auto":
        return explicit_parser
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix == ".txt":
        return "txt"
    raise SystemExit(f"Unsupported file type: {path.suffix}")


def iter_supported_files(root_dir: Path) -> List[Path]:
    return sorted(
        path
        for path in root_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_TEXT_SUFFIXES
    )


def parse_document(path: Path, root_dir: Path, explicit_parser: Optional[str] = None) -> ParsedDocument:
    parser = detect_parser(path, explicit_parser)
    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    if parser == "markdown":
        title, body = parse_markdown(raw_text, path)
    else:
        title, body = parse_text(raw_text, path)

    source_rel_path = path.relative_to(root_dir).as_posix()
    content_hash = sha1_text(body)
    doc_id = sha1_text(f"{source_rel_path}|{content_hash}")
    return ParsedDocument(
        doc_id=doc_id,
        source_rel_path=source_rel_path,
        source_type=path.suffix.lower().lstrip("."),
        parser=parser,
        title=title,
        body=body,
        content_hash=content_hash,
    )


def normalize_line(line: str) -> str:
    return line.replace("\ufeff", "").replace("\xa0", " ").replace("\u200b", "").rstrip()


def collapse_blank_lines(lines: List[str]) -> List[str]:
    output: List[str] = []
    blank_pending = False
    for line in lines:
        if not line.strip():
            if output and not blank_pending:
                output.append("")
            blank_pending = True
            continue
        output.append(line)
        blank_pending = False
    while output and output[0] == "":
        output.pop(0)
    while output and output[-1] == "":
        output.pop()
    return output


def strip_frontmatter(lines: List[str]) -> List[str]:
    if not lines or not FRONTMATTER_RE.match(lines[0]):
        return lines
    for index in range(1, len(lines)):
        if FRONTMATTER_RE.match(lines[index]):
            return lines[index + 1 :]
    return lines


def clean_markdown_line(line: str) -> str:
    stripped = normalize_line(line)
    stripped = INLINE_IMAGE_RE.sub("", stripped)
    stripped = MARKDOWN_LINK_RE.sub(r"\1", stripped)
    stripped = HEADING_RE.sub("", stripped)
    stripped = stripped.replace("`", "")
    stripped = re.sub(r"\s+", " ", stripped).strip()
    return stripped


def first_non_empty(lines: List[str], fallback: str) -> str:
    for line in lines:
        if line.strip():
            return line.strip()
    return fallback


def parse_markdown(raw_text: str, path: Path) -> tuple[str, str]:
    lines = [normalize_line(line) for line in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    lines = strip_frontmatter(lines)
    cleaned_lines = [clean_markdown_line(line) for line in lines]
    cleaned_lines = collapse_blank_lines(cleaned_lines)
    title = first_non_empty(cleaned_lines, path.stem.replace("_", " ").strip())
    body_lines = cleaned_lines[1:] if cleaned_lines and cleaned_lines[0] == title else cleaned_lines
    body = "\n".join(body_lines).strip() or title
    return title, body


def parse_text(raw_text: str, path: Path) -> tuple[str, str]:
    lines = [re.sub(r"\s+", " ", normalize_line(line)).strip() for line in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    lines = collapse_blank_lines(lines)
    title = first_non_empty(lines, path.stem.replace("_", " ").strip())
    body_lines = lines[1:] if lines and lines[0] == title else lines
    body = "\n".join(body_lines).strip() or title
    return title, body
