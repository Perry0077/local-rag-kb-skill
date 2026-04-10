# Retrieval Strategy

The runtime uses a two-stage answer pipeline:

1. retrieve chunks from Chroma
2. regroup hits by document
3. cluster nearby chunk indices
4. expand each hit cluster with neighboring windows
5. prefer the full document when the document is short and the same document was hit multiple times
6. select a small number of final contexts within a total character budget

Defaults:

- chunk size: `500`
- chunk overlap: `100`
- retrieve candidates: `15`
- default result count: `5`
- context window: `3`
- cluster gap: `2`
- max answer documents: `3`
- max full documents: `1`

By default the answer view shows:

- `Answer`
- `References`

In `CHAT_BACKEND=host` mode, the runtime emits a structured host bundle instead of composing the answer itself.

Use `--show-details` to inspect raw hits and answer contexts.
