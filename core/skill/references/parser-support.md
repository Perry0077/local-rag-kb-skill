# Parser Support

v1 supports only two parsers:

- `markdown`
- `txt`

Parser selection rules:

- `.md` / `.markdown` -> `markdown`
- `.txt` -> `txt`
- `--parser auto` follows the suffix

The markdown parser:

- strips leading frontmatter blocks
- removes markdown image syntax
- unwraps markdown links to anchor text
- uses the first non-empty cleaned line as the title

The txt parser:

- normalizes whitespace
- uses the first non-empty line as the title

Archive ingestion preserves the relative path inside the archive so references remain stable.
