---
name: local-rag-kb
description: Build and query a local RAG knowledge base from local files, uploaded archives, or single documents. Use this skill to ingest markdown or text files, keep a local vector store, and answer questions with references.
metadata:
  host: {{HOST_NAME}}
---

# Local RAG KB

Use this skill when the user wants to:

- build a local knowledge base from files
- ingest a zip or tar archive into a local RAG
- add a single markdown or txt file to an existing KB
- query a local KB with references
- inspect, rebuild, or delete a local KB
- 把这些文件做成本地知识库
- 把这个 zip 导入本地 RAG
- 往已有知识库里追加一个文件
- 查询本地知识库并带引用回答

{{HOST_TRIGGER_SNIPPET}}

## What this skill supports

- input: `.md`, `.txt`, `.zip`, `.tar`, `.tar.gz`, `.tgz`
- ingestion: append by default, or replace a whole KB
- storage: keeps registry, chunks, and Chroma data in the skill's own data directory
- retrieval: chunk search, document regrouping, expanded spans, short-document full read
- answers: default answer plus references, optional detail mode

## Default KB behavior

- If the user uploads one file and does not name a KB, use `default`
- If the user uploads one archive and does not name a KB, use `default`
- If the user asks a question and only one KB exists, use it
- If multiple KBs exist, prefer `default`
- If `default` does not exist and multiple KBs exist, ask the user to choose one

## Runtime workflow

### Interpreter and host selection

- Prefer the skill-local interpreter for all runtime commands: `.venv/bin/python`
- If `.venv/bin/python` does not exist yet, run `python3 scripts/kb_bootstrap.py`
- After bootstrap completes, use `.venv/bin/python` for:
  - `scripts/kb_ingest.py`
  - `scripts/kb_query.py`
  - `scripts/kb_status.py`
  - `scripts/kb_list.py`
  - `scripts/kb_rebuild.py`
  - `scripts/kb_delete.py`
- Always pass `--host {{HOST_NAME}}` to runtime commands unless the environment already sets `LOCAL_RAG_KB_HOST={{HOST_NAME}}`

### First-run config

If `EMBEDDING_API_KEY` is missing:

1. Stop before ingestion
2. Tell the user that embeddings need an OpenAI-compatible embedding API key
3. Ask for:
   - `EMBEDDING_API_KEY`
   - optionally `EMBEDDING_BASE_URL`
   - optionally `EMBEDDING_MODEL`
4. If the user does not specify base URL or model, use:
   - `https://api.openai.com/v1`
   - `text-embedding-3-small`
5. If the environment allows writing config files, write the values to the installed skill `.env`
6. Ensure the installed skill `.env` also keeps `LOCAL_RAG_KB_HOST={{HOST_NAME}}`
7. Otherwise tell the user exactly which variables they need to set before retrying

### Ingest

1. Resolve the KB name
2. Run `scripts/kb_bootstrap.py` if the environment is missing
3. Run `.venv/bin/python scripts/kb_ingest.py --host {{HOST_NAME}} --input <path> [--kb <name>]`
4. Report updated docs, unchanged docs, and total chunks

### Query

1. Resolve the KB name
2. If the host model should answer, run `.venv/bin/python scripts/kb_query.py --host {{HOST_NAME}} --question "<question>" [--kb <name>] --emit-host-bundle`
3. Compose the final answer in the host model using only the returned bundle
4. If the user explicitly configured `CHAT_BACKEND=openai-compatible`, `.venv/bin/python scripts/kb_query.py --host {{HOST_NAME}} --answer` may generate the answer directly
5. Use `--show-details` only when the user asks for retrieval internals

### Admin

- `.venv/bin/python scripts/kb_status.py --host {{HOST_NAME}}`
- `.venv/bin/python scripts/kb_list.py --host {{HOST_NAME}}`
- `.venv/bin/python scripts/kb_rebuild.py --host {{HOST_NAME}}`
- `.venv/bin/python scripts/kb_delete.py --host {{HOST_NAME}}`

## Output rules

- Keep answers concise and grounded in retrieved documents
- Use bracket citations like `[1]`
- Default reference format: `[1] title | source_rel_path`
- Do not dump raw chunk text unless the user asks
- In host-orchestrated mode, treat the emitted JSON bundle as the only allowed evidence for answer generation

## Parser support

v1 supports only:

- markdown
- txt

Read `references/parser-support.md` if parser choice matters.

## Retrieval strategy

Read `references/retrieval-strategy.md` when the user asks why the skill retrieved certain documents or how the answer is constructed.

## Storage and configuration

Read:

- `references/kb-layout.md`
- `references/env-config.md`
- `references/host-orchestration.md`

These files describe the KB directory layout, environment variables, and host-specific data roots.
