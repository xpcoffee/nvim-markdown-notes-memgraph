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
- **Build tools** (needed to compile the Memgraph client):
  - Ubuntu/Debian: `sudo apt install cmake build-essential libssl-dev`
  - macOS: `brew install cmake openssl`
  - Arch: `sudo pacman -S cmake base-devel openssl`

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

### Auto-install from Neovim

If you use the [nvim-markdown-notes](https://github.com/username/nvim-markdown-notes) plugin with `memgraph.enabled = true`, the plugin will detect the missing CLI and offer to install it for you automatically. See [Auto-install from Neovim](#auto-install-from-neovim-1) for details.

### Verify installation

```bash
nvim-markdown-notes-memgraph --help
```

### Updating

To update to the latest version:

```bash
uv tool install --force git+https://github.com/xpcoffee/nvim-markdown-notes-memgraph.git
```

Or if installed via pip:

```bash
pip install --upgrade git+https://github.com/xpcoffee/nvim-markdown-notes-memgraph.git
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
      "args": ["serve"],
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

## Neovim Integration

The CLI provides a `bridge` command that enables Neovim plugins to communicate with Memgraph via a JSON-over-stdin/stdout protocol.

### Auto-install from Neovim

When `memgraph.enabled = true` in your plugin config and the CLI is not on PATH, the plugin will prompt you to install it. The install uses whichever tool is available: `uv tool install` (preferred), `pip3 install`, or `pip install`.

**Configuration options** (passed via `opts.memgraph`):

| Option | Default | Description |
|--------|---------|-------------|
| `install_prompt` | `true` | Set to `false` to never prompt for installation |
| `install_source` | `"git+https://github.com/xpcoffee/nvim-markdown-notes-memgraph.git"` | Package specifier passed to pip/uv. Override with a PyPI name or local path. |

Example configuration:

```lua
require("nvim-markdown-notes").setup({
  notes_root_path = "~/notes",
  memgraph = {
    enabled = true,
    -- Disable auto-install prompt
    install_prompt = false,
    -- Or point to a local checkout
    install_source = "/path/to/nvim-markdown-notes-memgraph",
  },
})
```

**Behaviour:**

- If the CLI is already on PATH, no prompt is shown.
- If the user declines the prompt, it won't appear again until Neovim restarts.
- If `python3` is not available, or neither `uv` nor `pip` is found, the prompt is silently skipped and the plugin falls back to bundled scripts.
- Run `:MemgraphInstallCLI` at any time to trigger the install prompt manually (resets any prior decline).

### Bridge Protocol

The bridge command runs a persistent process that reads JSON requests from stdin and writes JSON responses to stdout. Each request/response is a single line of JSON.

**Request format:**

```json
{
  "action": "action_name",
  "params": {
    "key": "value"
  }
}
```

**Response format:**

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

### Supported Actions

The bridge supports the following actions:

- **connect**: Establish connection to Memgraph

  ```json
  { "action": "connect", "params": { "host": "localhost", "port": 7687 } }
  ```

- **health_check**: Check if connection is alive

  ```json
  { "action": "health_check", "params": {} }
  ```

- **update_note**: Update a note and its relationships in the graph

  ```json
  {
    "action": "update_note",
    "params": {
      "path": "/path/to/note.md",
      "title": "Note Title",
      "content": "Note content...",
      "wikilinks": [{ "target_path": "/path/to/other.md", "line_number": 5 }],
      "mentions": [{ "name": "username", "line_number": 10 }],
      "hashtags": [{ "name": "tagname", "line_number": 15 }]
    }
  }
  ```

- **delete_note**: Remove a note from the graph

  ```json
  { "action": "delete_note", "params": { "path": "/path/to/note.md" } }
  ```

- **query**: Execute a Cypher query

  ```json
  {
    "action": "query",
    "params": {
      "cypher": "MATCH (n:Note) RETURN n.title LIMIT 5",
      "params": {}
    }
  }
  ```

- **reindex**: Rebuild the entire graph from scratch

  ```json
  {
    "action": "reindex",
    "params": {
      "notes": [
        {
          "path": "/path/to/note.md",
          "title": "Note Title",
          "content": "Content...",
          "wikilinks": [],
          "mentions": [],
          "hashtags": []
        }
      ]
    }
  }
  ```

- **stats**: Get graph statistics

  ```json
  { "action": "stats", "params": {} }
  ```

- **quit**: Gracefully shut down the bridge
  ```json
  { "action": "quit", "params": {} }
  ```

### Example: Neovim Lua Integration

Here's an example of how to integrate the CLI bridge into a Neovim plugin:

```lua
local M = {}

-- Job ID for the bridge process
local job_id = nil
local is_connected = false

-- Callback management
local pending_callbacks = {}
local callback_counter = 0
local response_buffer = ""

-- Parse JSON response
local function parse_response(line)
  local ok, result = pcall(vim.json.decode, line)
  if ok then
    return result
  end
  return nil
end

-- Send a request to the bridge
local function send_request(action, params, callback)
  if not job_id then
    if callback then
      callback(false, nil, "Bridge not started")
    end
    return
  end

  local request = vim.json.encode({
    action = action,
    params = params or {}
  })

  if callback then
    callback_counter = callback_counter + 1
    pending_callbacks[callback_counter] = callback
  end

  vim.fn.chansend(job_id, request .. "\n")
end

-- Handle stdout from bridge
local function on_stdout(_, data, _)
  for _, line in ipairs(data) do
    if line and line ~= "" then
      response_buffer = response_buffer .. line

      local response = parse_response(response_buffer)
      if response then
        response_buffer = ""

        -- Find oldest pending callback
        local oldest_key = nil
        for key, _ in pairs(pending_callbacks) do
          if oldest_key == nil or key < oldest_key then
            oldest_key = key
          end
        end

        if oldest_key and pending_callbacks[oldest_key] then
          local cb = pending_callbacks[oldest_key]
          pending_callbacks[oldest_key] = nil
          cb(response.success, response.data, response.error)
        end

        -- Update connection state
        if type(response.data) == "table" then
          if response.data.status == "healthy" then
            is_connected = true
          elseif response.data.message and response.data.message:match("^Connected") then
            is_connected = true
          end
        end
      end
    end
  end
end

-- Start the bridge process
function M.start_bridge(callback)
  if job_id then
    if callback then
      callback(true, "Bridge already running")
    end
    return
  end

  -- Start the bridge command
  local cmd = { "nvim-markdown-notes-memgraph", "bridge" }

  job_id = vim.fn.jobstart(cmd, {
    on_stdout = on_stdout,
    on_exit = function(_, exit_code, _)
      job_id = nil
      is_connected = false
      for key, cb in pairs(pending_callbacks) do
        cb(false, nil, "Bridge exited with code " .. exit_code)
        pending_callbacks[key] = nil
      end
    end,
    stdout_buffered = false,
  })

  if job_id <= 0 then
    job_id = nil
    if callback then
      callback(false, "Failed to start bridge")
    end
    return
  end

  -- Connect to Memgraph
  vim.defer_fn(function()
    send_request("connect", { host = "localhost", port = 7687 }, callback)
  end, 100)
end

-- Ensure services are running and connected
function M.ensure_services(callback)
  -- Check if CLI is installed
  if vim.fn.executable("nvim-markdown-notes-memgraph") == 0 then
    if callback then
      callback(false, nil, "nvim-markdown-notes-memgraph CLI not installed")
    end
    return
  end

  -- Start services if not running
  vim.fn.jobstart(
    { "nvim-markdown-notes-memgraph", "start" },
    {
      on_exit = function(_, exit_code, _)
        if exit_code == 0 then
          -- Services started, now start bridge
          M.start_bridge(callback)
        else
          if callback then
            callback(false, nil, "Failed to start services")
          end
        end
      end
    }
  )
end

-- Update a note in the graph
function M.update_note(path, title, content, entities, callback)
  send_request("update_note", {
    path = path,
    title = title,
    content = content,
    wikilinks = entities.wikilinks or {},
    mentions = entities.mentions or {},
    hashtags = entities.hashtags or {}
  }, callback)
end

-- Get graph statistics
function M.get_stats(callback)
  send_request("stats", {}, callback)
end

return M
```

### Usage in Your Plugin

```lua
local graph = require("your_plugin.graph")

-- Ensure services are running and connect
graph.ensure_services(function(success, data, err)
  if success then
    print("Connected to Memgraph!")

    -- Update a note
    graph.update_note(
      "/home/user/notes/example.md",
      "Example Note",
      "This is the content...",
      {
        wikilinks = {
          { target_path = "/home/user/notes/other.md", line_number = 5 }
        },
        mentions = {
          { name = "alice", line_number = 10 }
        },
        hashtags = {
          { name = "project", line_number = 15 }
        }
      },
      function(success, data, err)
        if success then
          print("Note updated!")
        else
          print("Error: " .. (err or "unknown"))
        end
      end
    )
  else
    print("Failed to connect: " .. (err or "unknown"))
  end
end)
```

### ensure_services() Pattern

The `ensure_services()` pattern is the recommended way to integrate the CLI with your Neovim plugin:

1. **Check if CLI is installed**: Verify that `nvim-markdown-notes-memgraph` is in PATH
2. **Start services**: Run `nvim-markdown-notes-memgraph start` to ensure Memgraph and MCP server are running
3. **Start bridge**: Launch the bridge command and connect to Memgraph
4. **Handle errors gracefully**: Provide helpful error messages if any step fails

This pattern ensures that:

- Services are automatically started when needed
- Users don't need to manually start Docker containers
- The plugin works out of the box after installing the CLI
- Service management is transparent to the user

### Environment Variables

The bridge command respects the following environment variables:

- `NOTES_ROOT`: Root directory for markdown notes (default: `~/notes`)
- `MEMGRAPH_HOST`: Memgraph host (default: `localhost`)
- `MEMGRAPH_PORT`: Memgraph port (default: `7687`)

You can set these in your Neovim configuration:

```lua
vim.env.NOTES_ROOT = vim.fn.expand("~/Documents/notes")
vim.env.MEMGRAPH_HOST = "localhost"
vim.env.MEMGRAPH_PORT = "7687"
```

Or pass them when starting the bridge:

```bash
NOTES_ROOT=~/Documents/notes nvim-markdown-notes-memgraph bridge
```

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

### CLI not installed

**Problem**: The plugin falls back to bundled scripts or reports the CLI is missing.

**Solutions**:

1. Run `:MemgraphInstallCLI` inside Neovim to trigger the auto-install prompt.

2. Or install manually:

   ```bash
   pip install git+https://github.com/xpcoffee/nvim-markdown-notes-memgraph.git
   ```

3. Verify the CLI is on PATH:

   ```bash
   nvim-markdown-notes-memgraph --help
   ```

### Installation fails with cmake error

**Problem**: `pip install` or `uv tool install` fails with a long error trace mentioning cmake or CMakeLists.txt.

**Solution**: The `pymgclient` dependency requires cmake and a C compiler to build from source. Install the build prerequisites:

```
Ubuntu/Debian: sudo apt install cmake build-essential libssl-dev
macOS:         brew install cmake openssl
```

Then retry the installation.

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
