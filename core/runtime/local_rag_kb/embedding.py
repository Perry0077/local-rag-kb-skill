from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Iterable, List, Sequence

import chromadb
from openai import OpenAI

from .config import RuntimeConfig
from .models import ChunkRecord, KBPaths
from .utils import batch_iterable

LOCAL_TEST_EMBED_DIMENSIONS = 256


def require_embedding_api_key(config: RuntimeConfig) -> str:
    if config.embedding_api_key:
        return config.embedding_api_key
    raise SystemExit(
        "Missing EMBEDDING_API_KEY. Provide an OpenAI-compatible embedding API key before ingestion. "
        "Optional overrides: EMBEDDING_BASE_URL and EMBEDDING_MODEL. "
        "Set them in the environment or the skill .env file, then retry."
    )


def chunk_to_embedding_input(chunk: ChunkRecord) -> str:
    return "\n".join(
        [
            f"Title: {chunk.title}",
            f"Source: {chunk.source_rel_path}",
            f"Content: {chunk.text}",
        ]
    )


def pseudo_embedding(text: str, dimensions: int = LOCAL_TEST_EMBED_DIMENSIONS) -> List[float]:
    vector = [0.0] * dimensions
    normalized = "".join(text.lower().split())
    if not normalized:
        return vector
    for index in range(len(normalized)):
        gram = normalized[max(0, index - 1) : index + 2]
        digest = hashlib.sha1(gram.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:2], "big") % dimensions
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[bucket] += sign * (1.0 + digest[3] / 255.0)
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def get_collection(paths: KBPaths, config: RuntimeConfig) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(paths.chroma_dir))
    return client.get_or_create_collection(
        name=config.collection_name(paths.kb_name),
        metadata={"hnsw:space": "cosine"},
    )


def recreate_collection(paths: KBPaths, config: RuntimeConfig) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(paths.chroma_dir))
    name = config.collection_name(paths.kb_name)
    existing = {collection.name for collection in client.list_collections()}
    if name in existing:
        client.delete_collection(name)
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def delete_chunk_ids(paths: KBPaths, config: RuntimeConfig, chunk_ids: Sequence[str]) -> None:
    if not chunk_ids:
        return
    collection = get_collection(paths, config)
    collection.delete(ids=list(chunk_ids))


def embed_chunks(
    paths: KBPaths,
    config: RuntimeConfig,
    chunks: Sequence[ChunkRecord],
    *,
    local_test_embeddings: bool = False,
    batch_size: int | None = None,
) -> int:
    if not chunks:
        return 0
    collection = get_collection(paths, config)
    payloads = [chunk_to_embedding_input(chunk) for chunk in chunks]
    batch_size = batch_size or config.embed_batch_size
    client = None
    if not local_test_embeddings:
        client = OpenAI(
            api_key=require_embedding_api_key(config),
            base_url=config.embedding_base_url,
        )

    processed = 0
    for batch in batch_iterable(list(enumerate(chunks)), batch_size):
        indices = [item[0] for item in batch]
        batch_chunks = [item[1] for item in batch]
        batch_payloads = [payloads[index] for index in indices]
        if local_test_embeddings:
            embeddings = [pseudo_embedding(text) for text in batch_payloads]
        else:
            response = client.embeddings.create(model=config.embedding_model, input=batch_payloads)
            embeddings = [item.embedding for item in response.data]

        collection.upsert(
            ids=[chunk.id for chunk in batch_chunks],
            documents=[chunk.text for chunk in batch_chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "doc_id": chunk.doc_id,
                    "source_rel_path": chunk.source_rel_path,
                    "source_type": chunk.source_type,
                    "parser": chunk.parser,
                    "title": chunk.title,
                    "chunk_index": chunk.chunk_index,
                    "char_start": chunk.char_start,
                    "char_end": chunk.char_end,
                }
                for chunk in batch_chunks
            ],
        )
        processed += len(batch_chunks)
    return processed


def embed_query_text(config: RuntimeConfig, text: str, *, local_test_embeddings: bool = False) -> List[float]:
    if local_test_embeddings:
        return pseudo_embedding(text)
    client = OpenAI(
        api_key=require_embedding_api_key(config),
        base_url=config.embedding_base_url,
    )
    response = client.embeddings.create(model=config.embedding_model, input=[text])
    return response.data[0].embedding
