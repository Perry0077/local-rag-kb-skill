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

Important:

- `CHAT_BACKEND=host` means the host orchestration layer should call `kb_query.py --emit-host-bundle` and let the host model write the final answer
- `CHAT_BACKEND=openai-compatible` means `kb_query.py --answer` may call a remote chat API directly

If `EMBEDDING_API_KEY` is missing, the skill should not ingest files yet. It should ask the user for an OpenAI-compatible embedding key first, then retry ingestion after the environment is configured.
