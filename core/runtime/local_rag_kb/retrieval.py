from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
import re
from typing import Dict, Iterable, List, Sequence, Tuple

from .chunking import ChunkSlice, split_text
from .config import RuntimeConfig
from .embedding import embed_query_text, get_collection
from .models import CachedDocument, ContextCandidate, KBPaths, QueryHit, QueryResult, TextWindow
from .registry import Registry
from .storage import read_cached_document
from .utils import summarize_snippet


SUMMARY_HINTS = (
    "summary",
    "summarize",
    "overview",
    "gist",
    "main point",
    "what is this about",
    "总结",
    "概括",
    "摘要",
    "全文",
    "整篇",
    "主旨",
    "主要内容",
    "讲了什么",
    "说了什么",
    "核心观点",
)


def build_char_ngrams(text: str, size: int = 2) -> set[str]:
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", "", text.lower())
    if len(normalized) < size:
        return {normalized} if normalized else set()
    return {normalized[index : index + size] for index in range(len(normalized) - size + 1)}


def compute_title_overlap(question: str, title: str) -> float:
    question_ngrams = build_char_ngrams(question, size=2)
    title_ngrams = build_char_ngrams(title, size=2)
    if not question_ngrams or not title_ngrams:
        return 0.0
    intersection = len(question_ngrams & title_ngrams)
    return intersection / max(1, len(question_ngrams))


def is_summary_question(question: str) -> bool:
    lowered = question.strip().lower()
    return any(hint in lowered for hint in SUMMARY_HINTS)


def build_hits(result: Dict[str, object]) -> List[QueryHit]:
    hits: List[QueryHit] = []
    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    for index, chunk_id in enumerate(ids):
        metadata = metadatas[index] or {}
        distance = distances[index] if index < len(distances) else None
        score = 0.0 if distance is None else max(0.0, 1.0 - float(distance))
        hits.append(
            QueryHit(
                chunk_id=chunk_id,
                doc_id=str(metadata.get("doc_id", "")),
                text=documents[index] or "",
                score=score,
                metadata=metadata,
            )
        )
    return hits


def cluster_indices(indices: Sequence[int], gap: int) -> List[Tuple[int, int]]:
    if not indices:
        return []
    ordered = sorted(set(indices))
    clusters: List[Tuple[int, int]] = []
    start = ordered[0]
    end = ordered[0]
    for current in ordered[1:]:
        if current - end <= gap:
            end = current
            continue
        clusters.append((start, end))
        start = current
        end = current
    clusters.append((start, end))
    return clusters


@lru_cache(maxsize=1024)
def chunk_cached_body(body: str, chunk_size: int, overlap: int) -> List[ChunkSlice]:
    return split_text(body, chunk_size=chunk_size, overlap=overlap)


def build_expanded_spans(
    document: CachedDocument,
    doc_hits: Sequence[QueryHit],
    config: RuntimeConfig,
) -> List[TextWindow]:
    slices = chunk_cached_body(document.body, config.chunk_size, config.chunk_overlap)
    if not slices:
        return []

    hit_score_by_index: Dict[int, float] = defaultdict(float)
    for hit in doc_hits:
        raw_index = hit.metadata.get("chunk_index")
        try:
            chunk_index = int(raw_index)
        except (TypeError, ValueError):
            continue
        if chunk_index < 0 or chunk_index >= len(slices):
            continue
        hit_score_by_index[chunk_index] = max(hit_score_by_index[chunk_index], hit.score)

    if not hit_score_by_index:
        return []

    windows: List[TextWindow] = []
    for start_idx, end_idx in cluster_indices(list(hit_score_by_index.keys()), config.cluster_gap):
        expanded_start = max(0, start_idx - config.context_window)
        expanded_end = min(len(slices) - 1, end_idx + config.context_window)
        char_start = slices[expanded_start].char_start
        char_end = slices[expanded_end].char_end
        text = document.body[char_start:char_end].strip()
        if not text:
            continue
        cluster_score = sum(score for idx, score in hit_score_by_index.items() if start_idx <= idx <= end_idx)
        windows.append(
            TextWindow(
                text=text,
                score=cluster_score,
                start_idx=expanded_start,
                end_idx=expanded_end,
                hit_count=sum(1 for idx in hit_score_by_index if start_idx <= idx <= end_idx),
            )
        )
    windows.sort(key=lambda item: (-item.score, item.start_idx))
    return windows


def trim_windows_to_budget(windows: Sequence[TextWindow], budget_chars: int) -> str:
    selected: List[str] = []
    consumed = 0
    for window in windows:
        if consumed >= budget_chars:
            break
        text = window.text.strip()
        if not text:
            continue
        remaining = budget_chars - consumed
        if remaining <= 0:
            break
        if len(text) > remaining:
            text = text[:remaining].rstrip() + "..."
        selected.append(text)
        consumed += len(text)
    return "\n\n[...]\n\n".join(selected).strip()


def select_contexts(
    config: RuntimeConfig,
    paths: KBPaths,
    registry: Registry,
    question: str,
    hits: Sequence[QueryHit],
) -> List[ContextCandidate]:
    summary_question = is_summary_question(question)
    hits_by_doc: Dict[str, List[QueryHit]] = defaultdict(list)
    for hit in hits:
        if hit.doc_id:
            hits_by_doc[hit.doc_id].append(hit)

    candidates: List[ContextCandidate] = []
    rows_by_id = {row.doc_id: row for row in registry.list_active_documents(paths.kb_name)}
    for doc_id, doc_hits in hits_by_doc.items():
        row = rows_by_id.get(doc_id)
        if not row:
            continue
        cached = read_cached_document(paths, row.cache_path)
        windows = build_expanded_spans(cached, doc_hits, config)
        best_span = trim_windows_to_budget(windows, config.short_doc_chars)
        if not best_span:
            best_span = "\n\n".join(hit.text for hit in doc_hits[:2]).strip()

        hit_count = len(doc_hits)
        max_score = max((hit.score for hit in doc_hits), default=0.0)
        title_bonus = min(0.2, compute_title_overlap(question, cached.title) * 0.35)
        score = max_score + min(0.15, 0.05 * max(0, hit_count - 1)) + title_bonus

        prefer_full_document = (hit_count >= 2 and len(cached.body) <= config.short_doc_chars) or (
            summary_question and len(cached.body) <= config.summary_full_doc_chars
        )
        mode = "full_document" if prefer_full_document else "expanded_span"
        text = cached.body if prefer_full_document else best_span
        candidates.append(
            ContextCandidate(
                doc_id=doc_id,
                source_rel_path=cached.source_rel_path,
                title=cached.title,
                score=score,
                hit_count=hit_count,
                mode=mode,
                text=text,
            )
        )

    candidates.sort(key=lambda item: (-item.score, -item.hit_count, item.source_rel_path))

    selected: List[ContextCandidate] = []
    full_docs_used = 0
    consumed = 0
    for candidate in candidates:
        if len(selected) >= config.max_context_docs:
            break
        text = candidate.text
        mode = candidate.mode
        if mode == "full_document" and full_docs_used >= config.max_full_docs:
            mode = "expanded_span"
            row = rows_by_id.get(candidate.doc_id)
            if not row:
                continue
            cached = read_cached_document(paths, row.cache_path)
            windows = build_expanded_spans(cached, hits_by_doc[candidate.doc_id], config)
            text = trim_windows_to_budget(windows, config.short_doc_chars)
        if not text:
            continue
        remaining = config.total_context_chars - consumed
        if remaining <= 800:
            break
        if len(text) > remaining:
            text = text[:remaining].rstrip() + "..."
        selected.append(
            ContextCandidate(
                doc_id=candidate.doc_id,
                source_rel_path=candidate.source_rel_path,
                title=candidate.title,
                score=candidate.score,
                hit_count=candidate.hit_count,
                mode=mode,
                text=text,
            )
        )
        consumed += len(text)
        if mode == "full_document":
            full_docs_used += 1
    return selected


def query_kb(
    config: RuntimeConfig,
    paths: KBPaths,
    registry: Registry,
    question: str,
    *,
    top_k: int | None = None,
    retrieve_k: int | None = None,
    local_test_embeddings: bool = False,
) -> QueryResult:
    top_k = top_k or config.top_k
    retrieve_k = max(top_k, retrieve_k or config.retrieve_k)
    collection = get_collection(paths, config)
    query_embedding = embed_query_text(config, question, local_test_embeddings=local_test_embeddings)
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=retrieve_k,
        include=["documents", "metadatas", "distances"],
    )
    hits = build_hits(result)
    contexts = select_contexts(config, paths, registry, question, hits)
    return QueryResult(question=question, kb_name=paths.kb_name, hits=hits[:top_k], contexts=contexts)


def format_hits(hits: Sequence[QueryHit]) -> str:
    lines: List[str] = []
    for index, hit in enumerate(hits, start=1):
        lines.append(f"[{index}] {hit.metadata.get('title', '')}")
        lines.append(f"Source: {hit.metadata.get('source_rel_path', '')}")
        lines.append(f"Chunk: {hit.metadata.get('chunk_index', '')}")
        lines.append(f"Score: {hit.score:.4f}")
        lines.append(f"Summary: {summarize_snippet(hit.text)}")
        lines.append("")
    return "\n".join(lines).rstrip()
