"""CLI for nvim-markdown-notes-memgraph.

Provides commands for managing Memgraph and MCP server via Docker Compose.
"""

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


if __name__ == '__main__':
    main()
