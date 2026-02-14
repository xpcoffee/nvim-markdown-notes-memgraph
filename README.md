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

## Volume Configuration

The Docker Compose setup uses two types of volumes for data persistence:

### Memgraph Data Volume (Named Volume)

A named volume `memgraph-data` is automatically created to persist the Memgraph database across container restarts. This ensures your graph data is not lost when stopping services.

The volume is mounted at `/var/lib/memgraph` inside the Memgraph container.

### Notes Directory (Bind Mount)

Your markdown notes directory is mounted read-only into the MCP server container at `/notes`.

**Default location**: `~/notes`

**Custom location**: Set the `NOTES_ROOT` environment variable before starting services:

```bash
# Using environment variable
export NOTES_ROOT=/path/to/my/notes
docker compose up -d

# Or inline
NOTES_ROOT=/path/to/my/notes docker compose up -d
```

The bind mount is read-only (`:ro`) to prevent accidental modifications to your notes from within the container.

### Managing Volumes

```bash
# List volumes
docker volume ls

# Inspect the Memgraph data volume
docker volume inspect nvim-markdown-notes-memgraph_memgraph-data

# Remove volume (WARNING: deletes all graph data)
docker compose down -v
```

## License

MIT
