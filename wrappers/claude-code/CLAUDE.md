# local-rag-kb-skill

Claude Code wrapper for the shared `local-rag-kb` skill.

## Structure

- `dist/claude-code/local-rag-kb/` is the installable Claude Code skill payload
- `core/skill/` contains shared scripts and references
- `core/runtime/` contains shared Python runtime code
- `wrappers/claude-code/` contains Claude Code specific wrapper metadata

## Sync

Build and sync with:

```bash
python3 tools/build_targets.py --host claude-code
python3 tools/sync_targets.py --host claude-code
```

The default Claude install path is `~/.claude/skills/local-rag-kb`.
