"""CLI for nvim-markdown-notes-memgraph.

Provides commands for managing Memgraph and MCP server via Docker Compose.
"""

import json
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


@main.command()
@click.pass_context
def start(ctx):
    """Start Docker Compose services (Memgraph + MCP server)."""
    from .docker import start_services, DockerComposeError

    notes_root = ctx.obj['notes_root']

    click.echo(f"Starting services with notes root: {notes_root}")

    try:
        start_services(notes_root, wait_for_health=True, timeout=60)
        click.echo("Services are healthy and ready!")
        click.echo(f"Memgraph is running on localhost:7687")
        click.echo(f"MCP server is connected and monitoring: {notes_root}")
    except DockerComposeError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@main.command()
@click.pass_context
def stop(ctx):
    """Stop Docker Compose services (Memgraph + MCP server)."""
    from .docker import stop_services, DockerComposeError

    click.echo("Stopping services...")

    try:
        stop_services()
        click.echo("Services stopped successfully.")
    except DockerComposeError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@main.command()
@click.pass_context
def status(ctx):
    """Show status of Docker Compose services (Memgraph + MCP server)."""
    from .docker import get_status, DockerComposeError

    try:
        services = get_status()

        if not services:
            click.echo("No services are running.")
            click.echo("Run 'nvim-markdown-notes-memgraph start' to start services.")
            return

        # Print formatted output
        click.echo("Service Status:")
        click.echo("-" * 80)

        for service in services:
            name = service.get('Name', 'Unknown')
            service_name = service.get('Service', 'Unknown')
            state = service.get('State', 'Unknown')
            health = service.get('Health', 'N/A')
            ports = service.get('Publishers', [])

            # Format ports
            port_str = ""
            if ports:
                port_list = []
                for port in ports:
                    target = port.get('TargetPort', '')
                    published = port.get('PublishedPort', '')
                    if target and published:
                        port_list.append(f"{published}:{target}")
                    elif target:
                        port_list.append(str(target))
                port_str = ", ".join(port_list) if port_list else "N/A"
            else:
                port_str = "N/A"

            # Print service information
            click.echo(f"  Service: {service_name}")
            click.echo(f"  Name:    {name}")
            click.echo(f"  State:   {state}")
            click.echo(f"  Health:  {health}")
            click.echo(f"  Ports:   {port_str}")
            click.echo("-" * 80)

    except DockerComposeError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option(
    '--memgraph-host',
    default='localhost',
    help='Memgraph host (default: localhost)',
)
@click.option(
    '--memgraph-port',
    default=7687,
    type=int,
    help='Memgraph port (default: 7687)',
)
@click.pass_context
def config(ctx, memgraph_host, memgraph_port):
    """Output MCP JSON configuration for use with MCP clients.

    This configuration can be added to MCP client config files
    (e.g., Claude Desktop, Continue, etc.) to connect to the
    nvim-markdown-notes-memgraph MCP server.
    """
    from .config import generate_mcp_config

    notes_root = ctx.obj['notes_root']

    # Generate the MCP configuration
    mcp_config = generate_mcp_config(
        notes_root=notes_root,
        memgraph_host=memgraph_host,
        memgraph_port=memgraph_port
    )

    # Output as pretty-printed JSON
    click.echo(json.dumps(mcp_config, indent=2))


@main.command()
@click.option(
    '--memgraph-host',
    envvar='MEMGRAPH_HOST',
    default='localhost',
    help='Memgraph host (defaults to localhost or $MEMGRAPH_HOST)',
)
@click.option(
    '--memgraph-port',
    envvar='MEMGRAPH_PORT',
    default=7687,
    type=int,
    help='Memgraph port (defaults to 7687 or $MEMGRAPH_PORT)',
)
@click.pass_context
def serve(ctx, memgraph_host, memgraph_port):
    """Run the MCP server directly (for container use).

    This command starts the MCP server over stdio. It's intended for use
    as a Docker container entrypoint or for direct MCP client connections.

    Configuration is passed via environment variables:
    - MEMGRAPH_HOST: Memgraph host (default: localhost)
    - MEMGRAPH_PORT: Memgraph port (default: 7687)
    - NOTES_ROOT: Root directory for markdown notes
    """
    import asyncio

    # Set environment variables for the server
    os.environ['MEMGRAPH_HOST'] = memgraph_host
    os.environ['MEMGRAPH_PORT'] = str(memgraph_port)

    # notes_root is already set from the global option
    notes_root = ctx.obj['notes_root']
    os.environ['NOTES_ROOT'] = notes_root

    # Import and run the MCP server
    from . import server

    # Run the server's main function
    asyncio.run(server.main())


@main.command()
@click.option(
    '--memgraph-host',
    envvar='MEMGRAPH_HOST',
    default='localhost',
    help='Memgraph host (defaults to localhost or $MEMGRAPH_HOST)',
)
@click.option(
    '--memgraph-port',
    envvar='MEMGRAPH_PORT',
    default=7687,
    type=int,
    help='Memgraph port (defaults to 7687 or $MEMGRAPH_PORT)',
)
@click.pass_context
def bridge(ctx, memgraph_host, memgraph_port):
    """Run the Neovim bridge (stdin/stdout JSON).

    This command starts the Memgraph bridge for Neovim integration.
    It communicates via JSON over stdin/stdout and uses the Bolt protocol
    to connect to Memgraph.

    The bridge supports actions like:
    - connect: Establish connection to Memgraph
    - health_check: Check if connection is alive
    - update_note: Update a note and its relationships in the graph
    - delete_note: Remove a note from the graph
    - query: Execute a Cypher query
    - reindex: Rebuild the entire graph from scratch
    - stats: Get graph statistics

    Configuration is passed via environment variables:
    - MEMGRAPH_HOST: Memgraph host (default: localhost)
    - MEMGRAPH_PORT: Memgraph port (default: 7687)
    - NOTES_ROOT: Root directory for markdown notes
    """
    # Set environment variables for the bridge
    os.environ['MEMGRAPH_HOST'] = memgraph_host
    os.environ['MEMGRAPH_PORT'] = str(memgraph_port)

    # notes_root is already set from the global option
    notes_root = ctx.obj['notes_root']
    os.environ['NOTES_ROOT'] = notes_root

    # Import and run the bridge
    from .bridge import MemgraphBridge

    # Create and run the bridge
    bridge_instance = MemgraphBridge()
    bridge_instance.run()


if __name__ == '__main__':
    main()
