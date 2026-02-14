# Architecture: nvim-markdown-notes-memgraph

## Purpose

Standalone CLI package that extracts Memgraph + MCP server functionality from nvim-markdown-notes into a reusable tool.

## Source Repository

`/home/rick/code/personal/nvim-markdown-notes`

Key source files:
- `mcp/memgraph_notes_server.py` (898 lines) - MCP server with graph queries
- `scripts/memgraph_bridge.py` (520 lines) - JSON-over-stdin/stdout bridge for Neovim

## Architecture

```
┌─────────────────────────────────────────────┐
│           User / AI Assistant               │
└─────────────────┬───────────────────────────┘
                  │
    ┌─────────────┴─────────────┐
    │                           │
    ▼                           ▼
┌─────────────┐          ┌─────────────┐
│ CLI         │          │ Neovim      │
│ (config,    │          │ (bridge     │
│  start,     │          │  command)   │
│  stop)      │          │             │
└─────────────┘          └─────────────┘
    │                           │
    │   docker compose          │ stdin/stdout JSON
    ▼                           ▼
┌─────────────────────────────────────────────┐
│              Docker Compose                  │
│  ┌─────────────┐    ┌─────────────────────┐ │
│  │ Memgraph    │◄───│ MCP Server          │ │
│  │ (7687)      │    │ (stdio)             │ │
│  └─────────────┘    └─────────────────────┘ │
└─────────────────────────────────────────────┘
```

## Graph Schema

```cypher
(:Note {path, title, filename, last_modified, content_hash})
(:Person {name, display_name})
(:Tag {name})

(:Note)-[:LINKS_TO {line_number}]->(:Note)
(:Note)-[:MENTIONS {line_number}]->(:Person)
(:Note)-[:HAS_TAG {line_number}]->(:Tag)
(:Person)-[:HAS_NOTE]->(:Note)
```

## Entity Extraction (Regex)

- Wikilinks: `\[\[([^\]|]+)(?:\|[^\]]+)?\]\]`
- Mentions: `@([a-zA-Z][a-zA-Z0-9_-]*)`
- Hashtags: `(?<![/=])#([a-zA-Z][a-zA-Z0-9_-]*)`

## Dependencies

- Python 3.10+
- Docker & Docker Compose
- pymgclient (Memgraph client)
- mcp (Model Context Protocol SDK)
- click (CLI framework)

## Quality Standards

- Production code - maintainable, tested
- Small commits - one logical change each
- Run feedback loops before every commit
