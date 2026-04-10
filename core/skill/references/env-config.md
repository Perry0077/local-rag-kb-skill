# Environment Configuration

Required for embeddings:

- `EMBEDDING_API_KEY`
- `EMBEDDING_BASE_URL`
- `EMBEDDING_MODEL`

Defaults:

- `EMBEDDING_BASE_URL=https://api.openai.com/v1`
- `EMBEDDING_MODEL=text-embedding-3-small`

Chat configuration:

- `CHAT_BACKEND=host` by default
- `CHAT_BACKEND=openai-compatible` to use a remote OpenAI-compatible chat API

Optional remote chat variables:

- `CHAT_API_KEY`
- `CHAT_BASE_URL`
- `CHAT_MODEL`

Host selection:

- `LOCAL_RAG_KB_HOST=codex|openclaw|claude-code`

Data root override:

- `LOCAL_RAG_KB_DATA_DIR=/absolute/path`

The bootstrap command creates a local `.venv` under the installed skill directory and installs dependencies from `requirements.txt`.

After bootstrap, the host should prefer `.venv/bin/python` for all runtime commands instead of the system Python.

If `.venv` cannot be created because `python3 -m venv` or `ensurepip` is unavailable, the host may fall back to system `python3`.

That fallback is valid only when system `python3` can import:

- `openai`
- `chromadb`
- `dotenv`
- `tqdm`

If those imports are missing and the host can install user-level packages, install:

- `python3 -m pip install --user openai chromadb python-dotenv tqdm`

Important:

- `CHAT_BACKEND=host` means the host orchestration layer should call `kb_query.py --emit-host-bundle` and let the host model write the final answer
- `CHAT_BACKEND=openai-compatible` means `kb_query.py --answer` may call a remote chat API directly

If `EMBEDDING_API_KEY` is missing, the skill should not ingest files yet. It should ask the user for an OpenAI-compatible embedding key first, then retry ingestion after the environment is configured.

For host-packaged installs, keep `LOCAL_RAG_KB_HOST` aligned with the installed host:

- Codex package: `LOCAL_RAG_KB_HOST=codex`
- OpenClaw package: `LOCAL_RAG_KB_HOST=openclaw`
- Claude Code package: `LOCAL_RAG_KB_HOST=claude-code`
