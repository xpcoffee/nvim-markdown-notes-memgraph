"""CLI for nvim-markdown-notes-memgraph.

Provides commands for managing Memgraph and MCP server via Docker Compose.
"""

import json
import os
import subprocess
import time
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
    notes_root = ctx.obj['notes_root']

    # Find the project root (where docker-compose.yml is located)
    # The CLI is in src/nvim_markdown_notes_memgraph/cli.py, so go up to project root
    cli_file = Path(__file__).resolve()
    project_root = cli_file.parent.parent.parent
    compose_file = project_root / 'docker-compose.yml'

    if not compose_file.exists():
        click.echo(f"Error: docker-compose.yml not found at {compose_file}", err=True)
        raise click.Abort()

    click.echo(f"Starting services with notes root: {notes_root}")

    # Set environment variable for NOTES_ROOT
    env = os.environ.copy()
    env['NOTES_ROOT'] = notes_root

    # Start Docker Compose services in background
    try:
        result = subprocess.run(
            ['docker', 'compose', '-f', str(compose_file), 'up', '-d'],
            cwd=str(project_root),
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        click.echo(result.stdout)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error starting services: {e.stderr}", err=True)
        raise click.Abort()
    except FileNotFoundError:
        click.echo("Error: docker or docker compose not found. Please install Docker.", err=True)
        raise click.Abort()

    # Wait for health check to pass
    click.echo("Waiting for services to be healthy...")
    max_attempts = 30  # 30 attempts * 2 seconds = 60 seconds max
    attempt = 0

    while attempt < max_attempts:
        try:
            result = subprocess.run(
                ['docker', 'compose', '-f', str(compose_file), 'ps', '--format', 'json'],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                check=True
            )

            # Parse the JSON output to check service health
            import json
            services = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    services.append(json.loads(line))

            # Check if memgraph is healthy (mcp-server depends on it)
            memgraph_healthy = False
            for service in services:
                if 'memgraph' in service.get('Name', '') or 'memgraph' in service.get('Service', ''):
                    health = service.get('Health', '')
                    if health == 'healthy':
                        memgraph_healthy = True
                        break

            if memgraph_healthy:
                click.echo("Services are healthy and ready!")
                click.echo(f"Memgraph is running on localhost:7687")
                click.echo(f"MCP server is connected and monitoring: {notes_root}")
                return

            time.sleep(2)
            attempt += 1

        except subprocess.CalledProcessError as e:
            click.echo(f"Error checking service status: {e.stderr}", err=True)
            time.sleep(2)
            attempt += 1

    click.echo("Warning: Services started but health check did not pass within timeout.", err=True)
    click.echo("Run 'docker compose ps' to check service status manually.")


@main.command()
@click.pass_context
def stop(ctx):
    """Stop Docker Compose services (Memgraph + MCP server)."""
    # Find the project root (where docker-compose.yml is located)
    # The CLI is in src/nvim_markdown_notes_memgraph/cli.py, so go up to project root
    cli_file = Path(__file__).resolve()
    project_root = cli_file.parent.parent.parent
    compose_file = project_root / 'docker-compose.yml'

    if not compose_file.exists():
        click.echo(f"Error: docker-compose.yml not found at {compose_file}", err=True)
        raise click.Abort()

    click.echo("Stopping services...")

    # Stop Docker Compose services
    try:
        result = subprocess.run(
            ['docker', 'compose', '-f', str(compose_file), 'down'],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            check=True
        )
        click.echo(result.stdout)
        click.echo("Services stopped successfully.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Error stopping services: {e.stderr}", err=True)
        raise click.Abort()
    except FileNotFoundError:
        click.echo("Error: docker or docker compose not found. Please install Docker.", err=True)
        raise click.Abort()


@main.command()
@click.pass_context
def status(ctx):
    """Show status of Docker Compose services (Memgraph + MCP server)."""
    # Find the project root (where docker-compose.yml is located)
    # The CLI is in src/nvim_markdown_notes_memgraph/cli.py, so go up to project root
    cli_file = Path(__file__).resolve()
    project_root = cli_file.parent.parent.parent
    compose_file = project_root / 'docker-compose.yml'

    if not compose_file.exists():
        click.echo(f"Error: docker-compose.yml not found at {compose_file}", err=True)
        raise click.Abort()

    # Check if Docker Compose services are running
    try:
        result = subprocess.run(
            ['docker', 'compose', '-f', str(compose_file), 'ps', '--format', 'json'],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            check=True
        )

        # Parse the JSON output
        services = []
        for line in result.stdout.strip().split('\n'):
            if line:
                services.append(json.loads(line))

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

    except subprocess.CalledProcessError as e:
        click.echo(f"Error checking service status: {e.stderr}", err=True)
        raise click.Abort()
    except FileNotFoundError:
        click.echo("Error: docker or docker compose not found. Please install Docker.", err=True)
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
