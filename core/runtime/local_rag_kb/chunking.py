from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .models import ChunkRecord, ParsedDocument
from .utils import sha1_text


@dataclass
class ChunkSlice:
    chunk_index: int
    char_start: int
    char_end: int
    text: str


def make_chunk_id(doc_id: str, chunk_index: int, char_start: int, char_end: int, text: str) -> str:
    return sha1_text(f"{doc_id}|{chunk_index}|{char_start}|{char_end}|{text}")[:20]


def split_text(text: str, chunk_size: int, overlap: int) -> List[ChunkSlice]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")
    if not text:
        return []

    step = chunk_size - overlap
    result: List[ChunkSlice] = []
    chunk_index = 0
    for start in range(0, len(text), step):
        end = min(start + chunk_size, len(text))
        raw = text[start:end]
        left_trim = len(raw) - len(raw.lstrip())
        right_trim = len(raw) - len(raw.rstrip())
        actual_start = start + left_trim
        actual_end = end - right_trim
        chunk_text = text[actual_start:actual_end]
        if chunk_text:
            result.append(
                ChunkSlice(
                    chunk_index=chunk_index,
                    char_start=actual_start,
                    char_end=actual_end,
                    text=chunk_text,
                )
            )
        chunk_index += 1
        if end >= len(text):
            break
    return result


def chunk_document(document: ParsedDocument, kb_name: str, chunk_size: int, overlap: int) -> List[ChunkRecord]:
    chunks: List[ChunkRecord] = []
    for slice_ in split_text(document.body, chunk_size, overlap):
        chunks.append(
            ChunkRecord(
                id=make_chunk_id(document.doc_id, slice_.chunk_index, slice_.char_start, slice_.char_end, slice_.text),
                doc_id=document.doc_id,
                kb_name=kb_name,
                source_rel_path=document.source_rel_path,
                source_type=document.source_type,
                parser=document.parser,
                title=document.title,
                text=slice_.text,
                chunk_index=slice_.chunk_index,
                char_start=slice_.char_start,
                char_end=slice_.char_end,
            )
        )
    return chunks
