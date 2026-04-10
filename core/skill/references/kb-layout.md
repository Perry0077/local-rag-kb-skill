# KB Layout

Each knowledge base lives under the skill data root:

```text
<skill_data_root>/
└── kbs/
    └── <kb_slug>/
        ├── kb.json
        ├── registry.sqlite
        ├── chunks.jsonl
        ├── chroma/
        ├── ingest_staging/
        └── sources_cache/
```

- `kb.json`: KB metadata and collection name
- `registry.sqlite`: active document registry plus chunk registry
- `chunks.jsonl`: current active chunk snapshot
- `chroma/`: per-KB local vector storage
- `ingest_staging/`: temporary extraction directory for archives
- `sources_cache/`: cached normalized documents used for rebuilds and answer-time context expansion

Default data roots:

- Codex: `~/.codex/data/local-rag-kb`
- OpenClaw: `~/.agents/data/local-rag-kb`
- Claude Code: `~/.claude/data/local-rag-kb`

Override with `LOCAL_RAG_KB_DATA_DIR`.
