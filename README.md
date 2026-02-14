# nvim-markdown-notes-memgraph

Standalone CLI for Memgraph + MCP server with Docker Compose orchestration.

Extracts the Memgraph graph database functionality from [nvim-markdown-notes](https://github.com/username/nvim-markdown-notes) into a reusable, independently installable package.

## Features

- Docker Compose orchestration for Memgraph and MCP server
- CLI commands for managing services (start, stop, status)
- MCP server for AI assistant integration
- Neovim bridge for editor integration
- Automatic entity extraction (wikilinks, mentions, hashtags)

## Requirements

- Python 3.10+
- Docker & Docker Compose

## Installation

```bash
pip install nvim-markdown-notes-memgraph
```

Or with uv:

```bash
uv pip install nvim-markdown-notes-memgraph
```

## Usage

```bash
# Start services
nvim-markdown-notes-memgraph start --notes-root ~/notes

# Check status
nvim-markdown-notes-memgraph status

# Stop services
nvim-markdown-notes-memgraph stop

# Get MCP configuration
nvim-markdown-notes-memgraph config
```

## License

MIT
