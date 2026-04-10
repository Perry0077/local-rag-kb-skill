from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ParsedDocument:
    doc_id: str
    source_rel_path: str
    source_type: str
    parser: str
    title: str
    body: str
    content_hash: str


@dataclass
class ChunkRecord:
    id: str
    doc_id: str
    kb_name: str
    source_rel_path: str
    source_type: str
    parser: str
    title: str
    text: str
    chunk_index: int
    char_start: int
    char_end: int


@dataclass
class CachedDocument:
    doc_id: str
    source_rel_path: str
    source_type: str
    parser: str
    title: str
    body: str
    content_hash: str


@dataclass
class DocumentRow:
    doc_id: str
    kb_name: str
    source_rel_path: str
    source_type: str
    parser: str
    title: str
    content_hash: str
    status: str
    chunk_count: int
    cache_path: str
    updated_at: str


@dataclass
class KBPaths:
    kb_name: str
    kb_slug: str
    root: Path
    chroma_dir: Path
    registry_path: Path
    chunks_path: Path
    metadata_path: Path
    staging_dir: Path
    cache_dir: Path


@dataclass
class IngestReport:
    kb_name: str
    input_path: str
    mode: str
    supported_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    unchanged_docs: List[str] = field(default_factory=list)
    updated_docs: List[str] = field(default_factory=list)
    replaced_docs: List[str] = field(default_factory=list)
    total_chunks: int = 0


@dataclass
class QueryHit:
    chunk_id: str
    doc_id: str
    text: str
    score: float
    metadata: Dict[str, Any]


@dataclass
class TextWindow:
    text: str
    score: float
    start_idx: int
    end_idx: int
    hit_count: int


@dataclass
class ContextCandidate:
    doc_id: str
    source_rel_path: str
    title: str
    score: float
    hit_count: int
    mode: str
    text: str


@dataclass
class QueryResult:
    question: str
    kb_name: str
    hits: List[QueryHit]
    contexts: List[ContextCandidate]
    answer: str = ""
    cited_indices: List[int] = field(default_factory=list)


@dataclass
class HostAnswerBundle:
    question: str
    kb_name: str
    instructions: str
    contexts: List[Dict[str, Any]]
    references: List[Dict[str, Any]]
    hits: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ExtractedInput:
    root_dir: Path
    files: List[Path]
    extracted: bool
    cleanup_dir: Optional[Path] = None
    skipped_files: List[str] = field(default_factory=list)
