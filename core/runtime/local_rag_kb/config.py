from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .paths import PROJECT_ROOT
from .utils import slugify

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_RETRIEVE_K = 15
DEFAULT_TOP_K = 5
DEFAULT_CONTEXT_WINDOW = 3
DEFAULT_CLUSTER_GAP = 2
DEFAULT_MAX_CONTEXT_DOCS = 3
DEFAULT_MAX_FULL_DOCS = 1
DEFAULT_SHORT_DOC_CHARS = 6000
DEFAULT_TOTAL_CONTEXT_CHARS = 18000
DEFAULT_SUMMARY_FULL_DOC_CHARS = 18000
DEFAULT_EMBED_BATCH_SIZE = 100
DEFAULT_EMBED_LIMIT = 500
DEFAULT_EMBEDDING_BASE_URL = "https://api.openai.com/v1"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_CHAT_MODEL = "gpt-5.4"
DEFAULT_CHAT_BACKEND = "host"
DEFAULT_KB_NAME = "default"
DEFAULT_HOST = "codex"

HOST_DATA_ROOTS = {
    "codex": Path.home() / ".codex" / "data" / "local-rag-kb",
    "openclaw": Path.home() / ".agents" / "data" / "local-rag-kb",
    "claude-code": Path.home() / ".claude" / "data" / "local-rag-kb",
}


@dataclass
class RuntimeConfig:
    project_root: Path
    host: str
    data_root: Path
    default_kb_name: str
    chunk_size: int
    chunk_overlap: int
    retrieve_k: int
    top_k: int
    context_window: int
    cluster_gap: int
    max_context_docs: int
    max_full_docs: int
    short_doc_chars: int
    total_context_chars: int
    summary_full_doc_chars: int
    embed_limit: int
    embed_batch_size: int
    embedding_api_key: str
    embedding_base_url: str
    embedding_model: str
    chat_backend: str
    chat_api_key: str
    chat_base_url: str
    chat_model: str

    def collection_name(self, kb_name: str) -> str:
        return f"kb__{slugify(kb_name)}"


def load_environment(env_file: Optional[Path] = None) -> None:
    candidate = env_file or PROJECT_ROOT / ".env"
    if candidate.exists():
        load_dotenv(candidate, override=False)
    else:
        load_dotenv(override=False)


def resolve_host(explicit_host: Optional[str] = None) -> str:
    host = explicit_host or os.getenv("LOCAL_RAG_KB_HOST") or DEFAULT_HOST
    if host not in HOST_DATA_ROOTS:
        raise SystemExit(f"Unsupported host '{host}'. Use one of: {', '.join(sorted(HOST_DATA_ROOTS))}")
    return host


def resolve_data_root(host: str, explicit_data_root: Optional[str] = None) -> Path:
    if explicit_data_root:
        return Path(explicit_data_root).expanduser().resolve()
    env_value = os.getenv("LOCAL_RAG_KB_DATA_DIR")
    if env_value:
        return Path(env_value).expanduser().resolve()
    return HOST_DATA_ROOTS[host]


def load_config(
    *,
    host: Optional[str] = None,
    data_root: Optional[str] = None,
    env_file: Optional[str] = None,
) -> RuntimeConfig:
    load_environment(Path(env_file).expanduser().resolve() if env_file else None)
    resolved_host = resolve_host(host)
    resolved_root = resolve_data_root(resolved_host, data_root)
    resolved_root.mkdir(parents=True, exist_ok=True)
    return RuntimeConfig(
        project_root=PROJECT_ROOT,
        host=resolved_host,
        data_root=resolved_root,
        default_kb_name=os.getenv("DEFAULT_KB_NAME", DEFAULT_KB_NAME),
        chunk_size=int(os.getenv("CHUNK_SIZE", DEFAULT_CHUNK_SIZE)),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", DEFAULT_CHUNK_OVERLAP)),
        retrieve_k=int(os.getenv("RETRIEVE_K", DEFAULT_RETRIEVE_K)),
        top_k=int(os.getenv("TOP_K", DEFAULT_TOP_K)),
        context_window=int(os.getenv("CONTEXT_WINDOW", DEFAULT_CONTEXT_WINDOW)),
        cluster_gap=int(os.getenv("CLUSTER_GAP", DEFAULT_CLUSTER_GAP)),
        max_context_docs=int(os.getenv("MAX_CONTEXT_DOCS", DEFAULT_MAX_CONTEXT_DOCS)),
        max_full_docs=int(os.getenv("MAX_FULL_DOCS", DEFAULT_MAX_FULL_DOCS)),
        short_doc_chars=int(os.getenv("SHORT_DOC_CHARS", DEFAULT_SHORT_DOC_CHARS)),
        total_context_chars=int(os.getenv("TOTAL_CONTEXT_CHARS", DEFAULT_TOTAL_CONTEXT_CHARS)),
        summary_full_doc_chars=int(os.getenv("SUMMARY_FULL_DOC_CHARS", DEFAULT_SUMMARY_FULL_DOC_CHARS)),
        embed_limit=int(os.getenv("EMBED_LIMIT", DEFAULT_EMBED_LIMIT)),
        embed_batch_size=int(os.getenv("EMBED_BATCH_SIZE", DEFAULT_EMBED_BATCH_SIZE)),
        embedding_api_key=os.getenv("EMBEDDING_API_KEY", ""),
        embedding_base_url=os.getenv("EMBEDDING_BASE_URL", DEFAULT_EMBEDDING_BASE_URL),
        embedding_model=os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        chat_backend=os.getenv("CHAT_BACKEND", DEFAULT_CHAT_BACKEND),
        chat_api_key=os.getenv("CHAT_API_KEY", ""),
        chat_base_url=os.getenv("CHAT_BASE_URL", os.getenv("EMBEDDING_BASE_URL", DEFAULT_EMBEDDING_BASE_URL)),
        chat_model=os.getenv("CHAT_MODEL", DEFAULT_CHAT_MODEL),
    )
