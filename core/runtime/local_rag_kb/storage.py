from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Iterable, List

from .config import RuntimeConfig
from .models import CachedDocument, ChunkRecord, KBPaths
from .utils import ensure_directory, iter_jsonl, read_json, slugify, write_json, write_jsonl


def get_kb_paths(config: RuntimeConfig, kb_name: str) -> KBPaths:
    kb_slug = slugify(kb_name)
    root = ensure_directory(config.data_root / "kbs" / kb_slug)
    chroma_dir = ensure_directory(root / "chroma")
    staging_dir = ensure_directory(root / "ingest_staging")
    cache_dir = ensure_directory(root / "sources_cache")
    return KBPaths(
        kb_name=kb_name,
        kb_slug=kb_slug,
        root=root,
        chroma_dir=chroma_dir,
        registry_path=root / "registry.sqlite",
        chunks_path=root / "chunks.jsonl",
        metadata_path=root / "kb.json",
        staging_dir=staging_dir,
        cache_dir=cache_dir,
    )


def write_kb_metadata(paths: KBPaths, config: RuntimeConfig) -> None:
    payload = {
        "kb_name": paths.kb_name,
        "kb_slug": paths.kb_slug,
        "host": config.host,
        "collection_name": config.collection_name(paths.kb_name),
        "chunk_size": config.chunk_size,
        "chunk_overlap": config.chunk_overlap,
    }
    write_json(paths.metadata_path, payload)


def list_kb_roots(config: RuntimeConfig) -> List[Path]:
    kb_parent = config.data_root / "kbs"
    if not kb_parent.exists():
        return []
    return sorted(path for path in kb_parent.iterdir() if path.is_dir())


def list_kbs(config: RuntimeConfig) -> List[Dict[str, str]]:
    result: List[Dict[str, str]] = []
    for kb_root in list_kb_roots(config):
        metadata_path = kb_root / "kb.json"
        if not metadata_path.exists():
            continue
        payload = read_json(metadata_path)
        payload["root"] = str(kb_root)
        result.append(payload)
    return result


def delete_kb(paths: KBPaths) -> None:
    if paths.root.exists():
        shutil.rmtree(paths.root)


def clear_staging(paths: KBPaths) -> None:
    if paths.staging_dir.exists():
        shutil.rmtree(paths.staging_dir)
    paths.staging_dir.mkdir(parents=True, exist_ok=True)


def cache_document(paths: KBPaths, document: CachedDocument) -> str:
    cache_name = f"{document.doc_id}.json"
    cache_path = paths.cache_dir / cache_name
    cache_path.write_text(json.dumps(asdict(document), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cache_name


def read_cached_document(paths: KBPaths, cache_path: str) -> CachedDocument:
    payload = read_json(paths.cache_dir / cache_path)
    return CachedDocument(**payload)


def remove_cached_document(paths: KBPaths, cache_path: str) -> None:
    target = paths.cache_dir / cache_path
    if target.exists():
        target.unlink()


def load_chunks(paths: KBPaths) -> List[Dict[str, object]]:
    return list(iter_jsonl(paths.chunks_path))


def rewrite_chunks(paths: KBPaths, chunks: Iterable[ChunkRecord]) -> None:
    rows = [
        {
            "id": chunk.id,
            "doc_id": chunk.doc_id,
            "kb_name": chunk.kb_name,
            "source_rel_path": chunk.source_rel_path,
            "source_type": chunk.source_type,
            "parser": chunk.parser,
            "title": chunk.title,
            "text": chunk.text,
            "chunk_index": chunk.chunk_index,
            "char_start": chunk.char_start,
            "char_end": chunk.char_end,
        }
        for chunk in chunks
    ]
    write_jsonl(paths.chunks_path, rows)
