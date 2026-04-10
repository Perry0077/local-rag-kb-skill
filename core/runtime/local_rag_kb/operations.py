from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import shutil
from typing import Iterable, List, Sequence

from .archives import extract_input
from .chunking import chunk_document
from .config import RuntimeConfig
from .embedding import delete_chunk_ids, embed_chunks, recreate_collection
from .models import CachedDocument, ChunkRecord, DocumentRow, IngestReport, ParsedDocument
from .parsers import parse_document
from .registry import Registry
from .storage import (
    cache_document,
    clear_staging,
    delete_kb,
    get_kb_paths,
    list_kbs,
    load_chunks,
    read_cached_document,
    remove_cached_document,
    rewrite_chunks,
    write_kb_metadata,
)
from .utils import now_utc


def ensure_kb_ready(config: RuntimeConfig, kb_name: str):
    paths = get_kb_paths(config, kb_name)
    write_kb_metadata(paths, config)
    registry = Registry(paths.registry_path)
    return paths, registry


def cached_to_parsed(document: CachedDocument) -> ParsedDocument:
    return ParsedDocument(
        doc_id=document.doc_id,
        source_rel_path=document.source_rel_path,
        source_type=document.source_type,
        parser=document.parser,
        title=document.title,
        body=document.body,
        content_hash=document.content_hash,
    )


def rebuild_chunks_snapshot(config: RuntimeConfig, kb_name: str, registry: Registry) -> List[ChunkRecord]:
    paths = get_kb_paths(config, kb_name)
    chunks: List[ChunkRecord] = []
    for row in registry.list_active_documents(kb_name):
        cached = read_cached_document(paths, row.cache_path)
        parsed = cached_to_parsed(cached)
        chunks.extend(chunk_document(parsed, kb_name=kb_name, chunk_size=config.chunk_size, overlap=config.chunk_overlap))
    rewrite_chunks(paths, chunks)
    return chunks


def ingest_input(
    config: RuntimeConfig,
    kb_name: str,
    input_path: Path,
    *,
    mode: str = "append",
    parser: str = "auto",
    local_test_embeddings: bool = False,
) -> IngestReport:
    paths, registry = ensure_kb_ready(config, kb_name)
    report = IngestReport(kb_name=kb_name, input_path=str(input_path), mode=mode)
    try:
        if mode == "replace-kb":
            registry.close()
            delete_kb(paths)
            paths, registry = ensure_kb_ready(config, kb_name)

        clear_staging(paths)
        extracted = extract_input(input_path, paths.staging_dir)
        report.skipped_files.extend(extracted.skipped_files)
        if not extracted.files:
            raise SystemExit("No supported .md or .txt files were found in the provided input.")

        changed_chunks: List[ChunkRecord] = []
        for source_file in extracted.files:
            parsed = parse_document(source_file, extracted.root_dir, explicit_parser=parser)
            report.supported_files.append(parsed.source_rel_path)
            existing = registry.get_active_document(kb_name, parsed.source_rel_path)
            if existing and existing.content_hash == parsed.content_hash:
                report.unchanged_docs.append(parsed.source_rel_path)
                continue

            if existing:
                old_chunk_ids = registry.get_chunk_ids(existing.doc_id)
                delete_chunk_ids(paths, config, old_chunk_ids)
                registry.mark_replaced(existing.doc_id)
                registry.delete_chunk_rows(existing.doc_id)
                remove_cached_document(paths, existing.cache_path)
                report.replaced_docs.append(existing.source_rel_path)

            cached = CachedDocument(
                doc_id=parsed.doc_id,
                source_rel_path=parsed.source_rel_path,
                source_type=parsed.source_type,
                parser=parsed.parser,
                title=parsed.title,
                body=parsed.body,
                content_hash=parsed.content_hash,
            )
            cache_name = cache_document(paths, cached)
            chunks = chunk_document(parsed, kb_name=kb_name, chunk_size=config.chunk_size, overlap=config.chunk_overlap)
            registry.insert_document(
                DocumentRow(
                    doc_id=parsed.doc_id,
                    kb_name=kb_name,
                    source_rel_path=parsed.source_rel_path,
                    source_type=parsed.source_type,
                    parser=parsed.parser,
                    title=parsed.title,
                    content_hash=parsed.content_hash,
                    status="active",
                    chunk_count=len(chunks),
                    cache_path=cache_name,
                    updated_at=now_utc(),
                ),
                chunks,
            )
            changed_chunks.extend(chunks)
            report.updated_docs.append(parsed.source_rel_path)

        if report.updated_docs:
            embed_chunks(
                paths,
                config,
                changed_chunks,
                local_test_embeddings=local_test_embeddings,
                batch_size=config.embed_batch_size,
            )

        snapshot = rebuild_chunks_snapshot(config, kb_name, registry)
        report.total_chunks = len(snapshot)
        return report
    finally:
        registry.close()
        if paths.staging_dir.exists():
            shutil.rmtree(paths.staging_dir, ignore_errors=True)


def rebuild_kb(
    config: RuntimeConfig,
    kb_name: str,
    *,
    local_test_embeddings: bool = False,
) -> int:
    paths, registry = ensure_kb_ready(config, kb_name)
    try:
        active_rows = registry.list_active_documents(kb_name)
        recreate_collection(paths, config)
        registry.connection.execute("DELETE FROM chunks")
        registry.connection.commit()
        rebuilt_chunks: List[ChunkRecord] = []
        for row in active_rows:
            cached = read_cached_document(paths, row.cache_path)
            parsed = cached_to_parsed(cached)
            chunks = chunk_document(parsed, kb_name=kb_name, chunk_size=config.chunk_size, overlap=config.chunk_overlap)
            registry.insert_document(
                DocumentRow(
                    doc_id=row.doc_id,
                    kb_name=row.kb_name,
                    source_rel_path=row.source_rel_path,
                    source_type=row.source_type,
                    parser=row.parser,
                    title=row.title,
                    content_hash=row.content_hash,
                    status="active",
                    chunk_count=len(chunks),
                    cache_path=row.cache_path,
                    updated_at=now_utc(),
                ),
                chunks,
            )
            rebuilt_chunks.extend(chunks)
        rewrite_chunks(paths, rebuilt_chunks)
        embed_chunks(paths, config, rebuilt_chunks, local_test_embeddings=local_test_embeddings, batch_size=config.embed_batch_size)
        return len(rebuilt_chunks)
    finally:
        registry.close()


def delete_named_kb(config: RuntimeConfig, kb_name: str) -> None:
    paths = get_kb_paths(config, kb_name)
    delete_kb(paths)


def resolve_query_kb_name(config: RuntimeConfig, requested_kb: str | None) -> str:
    if requested_kb:
        return requested_kb
    available = list_kbs(config)
    if not available:
        raise SystemExit("No knowledge bases exist yet. Ingest files first.")
    names = [item["kb_name"] for item in available]
    if config.default_kb_name in names:
        return config.default_kb_name
    if len(names) == 1:
        return names[0]
    raise SystemExit(
        "Multiple knowledge bases exist and the default KB is missing. "
        f"Choose one explicitly with --kb. Available: {', '.join(sorted(names))}"
    )
