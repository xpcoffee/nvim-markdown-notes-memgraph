# Project: nvim-markdown-notes-memgraph

Standalone CLI extracting Memgraph + MCP server from nvim-markdown-notes into a reusable package.

## Key Paths

- **Source package**: `src/nvim_markdown_notes_memgraph/`
- **Tests**: `tests/`
- **Docker files**: `Dockerfile`, `docker-compose.yml`
- **PRD**: `prd.json` (task tracker)
- **Architecture**: `ARCHITECTURE.md`
- **Source repo**: `/home/rick/code/personal/nvim-markdown-notes`

## PRD Task Format

Tasks in `prd.json` have fields: `id`, `category`, `phase`, `description`, `steps[]`, `passes`, `status`.

Status values: `pending` | `in-progress` | `done` | `failed`

## Task Workflow

1. Read the task from `prd.json`
2. Set status to `"in-progress"` in `prd.json`
3. Implement each step in the task's `steps` array
4. Verify: `python -m py_compile <file>` for new Python files; `pytest` if tests exist
5. Commit with message: `feat(<task-id>): <description>`
6. Set status to `"done"` in `prd.json`
7. Commit the `prd.json` update separately

If implementation fails, set status to `"failed"` with explanation.

## Quality Standards

- Production code - maintainable, tested
- Small commits - one logical change each
- Run feedback loops (py_compile, pytest) before every commit
- See `ARCHITECTURE.md` for graph schema, entity extraction patterns, and dependency list
