# Installation

This project is distributed as a buildable multi-host skill. Build from the repo, then sync the generated target to the host you want to use.

## 1. Install dependencies

```bash
cd /Users/perry/Projects/local-rag-kb-skill
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 2. Configure environment

```bash
cp .env.example .env
```

Minimum embedding config:

```env
EMBEDDING_API_KEY=your_key
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
CHAT_BACKEND=host
```

If you want the Python runtime to call a remote OpenAI-compatible chat API directly:

```env
CHAT_BACKEND=openai-compatible
CHAT_API_KEY=your_key
CHAT_BASE_URL=https://api.openai.com/v1
CHAT_MODEL=gpt-5.4
```

## 3. Build targets

```bash
.venv/bin/python tools/build_targets.py --host all
```

Optional: package zip artifacts for GitHub Releases:

```bash
.venv/bin/python tools/package_releases.py --host all
```

Or build one target only:

```bash
.venv/bin/python tools/build_targets.py --host codex
.venv/bin/python tools/build_targets.py --host openclaw
.venv/bin/python tools/build_targets.py --host claude-code
```

## 4. Sync targets into host install paths

```bash
.venv/bin/python tools/sync_targets.py --host all
```

Default install paths:

- Codex: `~/.codex/skills/local-rag-kb`
- OpenClaw: `~/.agents/skills/local-rag-kb`
- Claude Code: `~/.claude/skills/local-rag-kb`

Override install directories if needed:

```bash
.venv/bin/python tools/sync_targets.py \
  --host all \
  --codex-dir /custom/codex/local-rag-kb \
  --openclaw-dir /custom/openclaw/local-rag-kb \
  --claude-dir /custom/claude/local-rag-kb
```

## 5. Verify the install

Run a local fixture ingestion:

```bash
.venv/bin/python dist/codex/local-rag-kb/scripts/kb_ingest.py \
  --input fixtures/input/nested_docs.zip \
  --local-test-embeddings
```

Emit a host answer bundle:

```bash
.venv/bin/python dist/codex/local-rag-kb/scripts/kb_query.py \
  --question "Why can one broken provider affect many sites?" \
  --emit-host-bundle \
  --local-test-embeddings
```

If this returns JSON with `instructions`, `contexts`, and `references`, the install is working.

## GitHub distribution

For distribution through GitHub, the recommended approach is:

1. push the full repo to GitHub
2. build the host targets
3. package release zips
4. upload those zips to GitHub Releases

That gives users two options:

- source install: clone the repo and run the build/sync steps
- binary-like install: download the host zip from Releases and copy the unpacked skill folder into the host skill directory

Recommended release assets:

- `local-rag-kb-openclaw.zip`
- `local-rag-kb-codex.zip`
- `local-rag-kb-claude-code.zip`
