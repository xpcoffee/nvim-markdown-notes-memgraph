"""CLI for nvim-markdown-notes-memgraph.

Provides commands for managing Memgraph and MCP server via Docker Compose.
"""

import os
from pathlib import Path

import click


@click.group()
@click.option(
    '--notes-root',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    envvar='NOTES_ROOT',
    default=lambda: str(Path.home() / 'notes'),
    help='Root directory for markdown notes (defaults to ~/notes or $NOTES_ROOT)',
)
@click.pass_context
def main(ctx, notes_root):
    """nvim-markdown-notes-memgraph CLI.

    Manage Memgraph and MCP server for markdown notes with graph capabilities.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store global options in context
    ctx.obj['notes_root'] = notes_root


if __name__ == '__main__':
    main()
