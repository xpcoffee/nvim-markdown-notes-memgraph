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
- Docker
- Docker Compose

Docker and Docker Compose must be installed and running before using this package. The CLI manages Docker Compose services, so these are hard prerequisites.

To verify Docker is installed:

```bash
docker --version
docker compose version
```

## Installation

### Using pip

```bash
pip install nvim-markdown-notes-memgraph
```

### Using uv

```bash
uv pip install nvim-markdown-notes-memgraph
```

### From source

```bash
git clone https://github.com/username/nvim-markdown-notes-memgraph.git
cd nvim-markdown-notes-memgraph
pip install -e .
```

### Verify installation

```bash
nvim-markdown-notes-memgraph --help
```

## Usage

The CLI provides several commands for managing the Memgraph database and MCP server.

### Global Options

All commands support the following global option:

- `--notes-root PATH`: Root directory for markdown notes (defaults to `~/notes` or `$NOTES_ROOT` environment variable)

Example:

```bash
nvim-markdown-notes-memgraph --notes-root /path/to/notes start
```

Or set the environment variable:

```bash
export NOTES_ROOT=/path/to/notes
nvim-markdown-notes-memgraph start
```

### Commands

#### start

Start Docker Compose services (Memgraph + MCP server).

```bash
nvim-markdown-notes-memgraph start
```

With custom notes directory:

```bash
nvim-markdown-notes-memgraph --notes-root ~/Documents/notes start
```

This command:
- Starts the Memgraph database container
- Starts the MCP server container
- Waits for services to be healthy (up to 60 seconds)
- Mounts your notes directory read-only into the MCP server container

Output:

```
Starting services with notes root: /home/user/notes
Services are healthy and ready!
Memgraph is running on localhost:7687
MCP server is connected and monitoring: /home/user/notes
```

#### stop

Stop Docker Compose services (Memgraph + MCP server).

```bash
nvim-markdown-notes-memgraph stop
```

This command stops all running containers but preserves the Memgraph data volume.

Output:

```
Stopping services...
Services stopped successfully.
```

#### status

Show status of Docker Compose services (Memgraph + MCP server).

```bash
nvim-markdown-notes-memgraph status
```

Output:

```
Service Status:
--------------------------------------------------------------------------------
  Service: memgraph
  Name:    nvim-markdown-notes-memgraph-memgraph-1
  State:   running
  Health:  healthy
  Ports:   7687:7687
--------------------------------------------------------------------------------
  Service: mcp-server
  Name:    nvim-markdown-notes-memgraph-mcp-server-1
  State:   running
  Health:  N/A
  Ports:   N/A
--------------------------------------------------------------------------------
```

If no services are running:

```
No services are running.
Run 'nvim-markdown-notes-memgraph start' to start services.
```

#### config

Output MCP JSON configuration for use with MCP clients.

```bash
nvim-markdown-notes-memgraph config
```

With custom Memgraph host/port:

```bash
nvim-markdown-notes-memgraph config --memgraph-host localhost --memgraph-port 7687
```

Output (example):

```json
{
  "mcpServers": {
    "nvim-markdown-notes-memgraph": {
      "command": "nvim-markdown-notes-memgraph",
      "args": [
        "serve"
      ],
      "env": {
        "MEMGRAPH_HOST": "localhost",
        "MEMGRAPH_PORT": "7687",
        "NOTES_ROOT": "/home/user/notes"
      }
    }
  }
}
```

This configuration can be added to MCP client config files (e.g., Claude Desktop, Continue, etc.).

#### serve

Run the MCP server directly (for container use or direct MCP client connections).

```bash
nvim-markdown-notes-memgraph serve
```

With custom configuration:

```bash
nvim-markdown-notes-memgraph --notes-root ~/notes serve --memgraph-host localhost --memgraph-port 7687
```

Or using environment variables:

```bash
export MEMGRAPH_HOST=localhost
export MEMGRAPH_PORT=7687
export NOTES_ROOT=~/notes
nvim-markdown-notes-memgraph serve
```

This command starts the MCP server over stdio. It's intended for use as a Docker container entrypoint or for direct MCP client connections.

#### bridge

Run the Neovim bridge (stdin/stdout JSON).

```bash
nvim-markdown-notes-memgraph bridge
```

With custom configuration:

```bash
nvim-markdown-notes-memgraph --notes-root ~/notes bridge --memgraph-host localhost --memgraph-port 7687
```

Or using environment variables:

```bash
export MEMGRAPH_HOST=localhost
export MEMGRAPH_PORT=7687
export NOTES_ROOT=~/notes
nvim-markdown-notes-memgraph bridge
```

This command starts the Memgraph bridge for Neovim integration. It communicates via JSON over stdin/stdout and uses the Bolt protocol to connect to Memgraph.

The bridge supports actions like:
- `connect`: Establish connection to Memgraph
- `health_check`: Check if connection is alive
- `update_note`: Update a note and its relationships in the graph
- `delete_note`: Remove a note from the graph
- `query`: Execute a Cypher query
- `reindex`: Rebuild the entire graph from scratch
- `stats`: Get graph statistics

## Docker Configuration

### Services

The Docker Compose setup includes two services:

1. **memgraph**: The Memgraph graph database (port 7687)
2. **mcp-server**: The MCP server that connects to Memgraph and monitors your notes

### Volumes

The Docker Compose setup uses two types of volumes for data persistence:

#### Memgraph Data Volume (Named Volume)

A named volume `memgraph-data` is automatically created to persist the Memgraph database across container restarts. This ensures your graph data is not lost when stopping services.

The volume is mounted at `/var/lib/memgraph` inside the Memgraph container.

#### Notes Directory (Bind Mount)

Your markdown notes directory is mounted read-only into the MCP server container at `/notes`.

**Default location**: `~/notes`

**Custom location**: Use the `--notes-root` option or set the `NOTES_ROOT` environment variable:

```bash
# Using environment variable
export NOTES_ROOT=/path/to/my/notes
nvim-markdown-notes-memgraph start

# Or with CLI option
nvim-markdown-notes-memgraph --notes-root /path/to/my/notes start
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

## Graph Schema

The system extracts entities from your markdown notes and stores them in Memgraph with the following schema:

### Nodes

- `(:Note {path, title, filename, last_modified, content_hash})` - Markdown notes
- `(:Person {name, display_name})` - People mentioned with `@username`
- `(:Tag {name})` - Hashtags like `#project`

### Relationships

- `(:Note)-[:LINKS_TO {line_number}]->(:Note)` - Wikilinks between notes
- `(:Note)-[:MENTIONS {line_number}]->(:Person)` - Mentions of people
- `(:Note)-[:HAS_TAG {line_number}]->(:Tag)` - Tags in notes
- `(:Person)-[:HAS_NOTE]->(:Note)` - Person nodes link to notes about them

### Entity Extraction

The system uses regex patterns to extract entities:

- **Wikilinks**: `[[note-name]]` or `[[note-name|display text]]`
- **Mentions**: `@username` (alphanumeric with hyphens/underscores)
- **Hashtags**: `#tagname` (alphanumeric with hyphens/underscores)

## MCP Integration

The MCP (Model Context Protocol) server provides tools for AI assistants to query and interact with your note graph.

### Available MCP Tools

The server exposes several tools that AI assistants can call:

- **find_notes_by_tag**: Find all notes containing a specific tag
- **find_notes_mentioning_person**: Find notes that mention a person
- **find_linked_notes**: Find notes linked to/from a specific note
- **search_notes_content**: Full-text search across note content
- **get_note_stats**: Get statistics about a note (links, mentions, tags)
- **list_all_tags**: List all tags used across all notes
- **list_all_people**: List all people mentioned in notes

### Using with Claude Desktop

Add the configuration to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```bash
# Generate the config
nvim-markdown-notes-memgraph config >> claude_desktop_config.json
```

Then restart Claude Desktop.

### Using with Continue

Add to your Continue configuration file:

```bash
nvim-markdown-notes-memgraph config
```

Copy the output to your Continue MCP servers configuration.

## Troubleshooting

### Services won't start

**Problem**: `docker compose` command fails or services won't start.

**Solutions**:

1. Check that Docker is running:

   ```bash
   docker ps
   ```

2. Check that Docker Compose is installed:

   ```bash
   docker compose version
   ```

3. Check for port conflicts (Memgraph uses port 7687):

   ```bash
   lsof -i :7687
   ```

4. Check Docker logs:

   ```bash
   docker compose logs memgraph
   docker compose logs mcp-server
   ```

5. Try stopping and removing all containers:

   ```bash
   docker compose down
   nvim-markdown-notes-memgraph start
   ```

### Services are unhealthy

**Problem**: `start` command times out waiting for services to be healthy.

**Solutions**:

1. Check service logs:

   ```bash
   docker compose logs memgraph
   ```

2. Wait longer - the healthcheck can take up to 60 seconds.

3. Restart the Memgraph service:

   ```bash
   docker compose restart memgraph
   ```

### Notes directory not found

**Problem**: Error about notes directory not existing.

**Solutions**:

1. Verify the path exists:

   ```bash
   ls ~/notes
   # or
   ls /path/to/notes
   ```

2. Create the directory:

   ```bash
   mkdir -p ~/notes
   ```

3. Set the correct path:

   ```bash
   nvim-markdown-notes-memgraph --notes-root /correct/path start
   ```

### Connection refused to Memgraph

**Problem**: Cannot connect to Memgraph on `localhost:7687`.

**Solutions**:

1. Check that Memgraph is running:

   ```bash
   nvim-markdown-notes-memgraph status
   ```

2. Check that the port is exposed:

   ```bash
   docker compose ps
   ```

3. Try connecting directly:

   ```bash
   docker exec -it nvim-markdown-notes-memgraph-memgraph-1 mgconsole
   ```

### MCP server not responding

**Problem**: MCP server doesn't respond to requests.

**Solutions**:

1. Check server logs:

   ```bash
   docker compose logs mcp-server
   ```

2. Restart the MCP server:

   ```bash
   docker compose restart mcp-server
   ```

3. Verify environment variables are set correctly:

   ```bash
   docker compose config
   ```

### Graph data lost after restart

**Problem**: Graph data disappears after stopping services.

**Solutions**:

1. Make sure you're using `stop` instead of `down`:

   ```bash
   nvim-markdown-notes-memgraph stop  # Preserves data
   ```

2. Avoid using `docker compose down -v` which deletes volumes.

3. Check that the volume exists:

   ```bash
   docker volume ls | grep memgraph-data
   ```

### Permission errors in Docker

**Problem**: Permission denied errors when mounting notes directory.

**Solutions**:

1. Check file permissions on your notes directory:

   ```bash
   ls -la ~/notes
   ```

2. Make sure Docker has permission to access the directory (especially on macOS - check Docker Desktop settings).

3. On Linux, check SELinux/AppArmor settings if applicable.

## Development

### Running tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/nvim_markdown_notes_memgraph
```

### Building from source

```bash
# Install in development mode
pip install -e .

# Build wheel
pip install build
python -m build
```

## License

MIT
