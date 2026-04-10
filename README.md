# local-rag-kb-skill

A reusable local RAG skill project for Codex, OpenClaw, and Claude Code.

It ingests markdown or text documents from single files or archives, stores vectors in a local ChromaDB, keeps a document registry for incremental updates, and returns answer-ready context with references.

中文说明: [README.zh-CN.md](/Users/perry/Projects/local-rag-kb-skill/README.zh-CN.md)

## What it does

- builds a local KB from `.md`, `.txt`, `.zip`, `.tar`, `.tar.gz`, `.tgz`
- stores all KB state in the skill's own data directory
- supports append-by-default ingestion into `default`
- deduplicates unchanged documents and rebuilds changed ones
- retrieves with chunk search + document regrouping + expanded spans
- supports two answer modes:
  - `CHAT_BACKEND=host`: runtime emits a structured context bundle and the host model writes the final answer
  - `CHAT_BACKEND=openai-compatible`: runtime calls a remote OpenAI-compatible chat API directly
- builds installable skill targets for:
  - Codex
  - OpenClaw
  - Claude Code

## Project layout

```text
local-rag-kb-skill/
├── core/
│   ├── runtime/
│   └── skill/
├── wrappers/
├── tools/
├── fixtures/
├── tests/
└── dist/
```

## Quick start

Create the project environment:

```bash
cd /Users/perry/Projects/local-rag-kb-skill
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Copy the environment template:

```bash
cp .env.example .env
```

For local test runs without a real embedding API, use `--local-test-embeddings`.

## Runtime usage

Ingest a single file:

```bash
.venv/bin/python core/skill/scripts/kb_ingest.py \
  --input /path/to/doc.md \
  --local-test-embeddings
```

Ingest an archive:

```bash
.venv/bin/python core/skill/scripts/kb_ingest.py \
  --input /path/to/docs.zip \
  --local-test-embeddings
```

Query and emit a host answer bundle:

```bash
.venv/bin/python core/skill/scripts/kb_query.py \
  --question "Why can one broken provider affect many products?" \
  --emit-host-bundle \
  --local-test-embeddings
```

Query with a remote OpenAI-compatible chat backend:

```bash
CHAT_BACKEND=openai-compatible \
CHAT_API_KEY=... \
CHAT_BASE_URL=https://api.openai.com/v1 \
CHAT_MODEL=gpt-5.4 \
.venv/bin/python core/skill/scripts/kb_query.py \
  --question "Why can one broken provider affect many products?" \
  --answer
```

List and inspect KBs:

```bash
.venv/bin/python core/skill/scripts/kb_list.py
.venv/bin/python core/skill/scripts/kb_status.py --kb default
```

## Build and sync skill targets

Build all host targets:

```bash
.venv/bin/python tools/build_targets.py --host all
```

Package GitHub release zips:

```bash
.venv/bin/python tools/package_releases.py --host all
```

Sync to local install directories:

```bash
.venv/bin/python tools/sync_targets.py --host all
```

The built payloads land under:

- [dist/codex/local-rag-kb](/Users/perry/Projects/local-rag-kb-skill/dist/codex/local-rag-kb)
- [dist/openclaw/local-rag-kb](/Users/perry/Projects/local-rag-kb-skill/dist/openclaw/local-rag-kb)
- [dist/claude-code/local-rag-kb](/Users/perry/Projects/local-rag-kb-skill/dist/claude-code/local-rag-kb)

Release archives land under:

- [release](/Users/perry/Projects/local-rag-kb-skill/release)

## Host-answer orchestration

For `CHAT_BACKEND=host`, the Python runtime is intentionally not the final answering layer.

The intended flow is:

1. run `kb_query.py --emit-host-bundle`
2. let the host model read that JSON bundle
3. have the host model answer from the bundle only
4. include bracket citations like `[1]`
5. render the `References:` section from the bundle references

This keeps answer generation aligned with each host's native main model.

## Distribute from GitHub

Recommended distribution flow:

1. push the full repository to GitHub
2. run `tools/build_targets.py --host all`
3. run `tools/package_releases.py --host all`
4. attach the generated zip files from `release/` to a GitHub Release

For technical users:

- they can clone the repo, create `.venv`, and run `tools/build_targets.py` + `tools/sync_targets.py`

For simpler distribution:

- they can download the host-specific zip from GitHub Releases
- unzip it
- copy or sync the unpacked `local-rag-kb` folder into the host skill directory

If you only want one host, publish just that host's release zip.

For OpenClaw users who want AI-conversation install instead of manual download:

- publish the full repository, not just partial files
- attach `local-rag-kb-openclaw.zip` in GitHub Releases
- integrate with an OpenClaw skill registry or install-from-GitHub flow when that distribution path is available

GitHub alone is the source of truth, but conversational installation still depends on the host supporting registry-based or repo-based skill install.

## Validation

Run the test suite:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

The tests cover:

- single-file ingestion
- zip and tar.gz ingestion
- incremental re-ingestion
- host-bundle query output
- multi-host build generation
