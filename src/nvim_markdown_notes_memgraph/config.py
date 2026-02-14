"""Configuration generation for nvim-markdown-notes-memgraph.

Provides functions to generate MCP JSON configuration for connecting
to the nvim-markdown-notes-memgraph MCP server.
"""


def generate_mcp_config(
    notes_root: str,
    memgraph_host: str = "localhost",
    memgraph_port: int = 7687
) -> dict:
    """Generate MCP JSON configuration for the notes server.

    Args:
        notes_root: Root directory for markdown notes
        memgraph_host: Memgraph host (default: localhost)
        memgraph_port: Memgraph port (default: 7687)

    Returns:
        Dictionary containing MCP configuration that can be serialized to JSON.
        The configuration includes the command, args, and environment variables
        needed to connect MCP clients to the server.

    Example:
        >>> config = generate_mcp_config("/home/user/notes")
        >>> import json
        >>> print(json.dumps(config, indent=2))
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
    """
    return {
        "mcpServers": {
            "nvim-markdown-notes-memgraph": {
                "command": "nvim-markdown-notes-memgraph",
                "args": ["serve"],
                "env": {
                    "MEMGRAPH_HOST": memgraph_host,
                    "MEMGRAPH_PORT": str(memgraph_port),
                    "NOTES_ROOT": notes_root
                }
            }
        }
    }
