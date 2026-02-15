"""Docker Compose management for nvim-markdown-notes-memgraph.

This module provides functions to start, stop, and check the status of
Docker Compose services (Memgraph and MCP server).
"""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DockerComposeError(Exception):
    """Raised when Docker Compose operations fail."""
    pass


def _get_compose_file() -> Path:
    """Get the path to docker-compose.yml.

    Returns:
        Path to docker-compose.yml

    Raises:
        DockerComposeError: If docker-compose.yml is not found
    """
    from importlib.resources import files

    compose_file = files("nvim_markdown_notes_memgraph").joinpath("docker-compose.yml")
    path = Path(str(compose_file))

    if not path.exists():
        raise DockerComposeError(f"docker-compose.yml not found at {path}")

    return path


def start_services(notes_root: str, wait_for_health: bool = True, timeout: int = 60) -> None:
    """Start Docker Compose services (Memgraph + MCP server).

    Args:
        notes_root: Root directory for markdown notes
        wait_for_health: Whether to wait for health check to pass (default: True)
        timeout: Maximum time to wait for health check in seconds (default: 60)

    Raises:
        DockerComposeError: If starting services fails or timeout is reached
    """
    compose_file = _get_compose_file()
    project_root = compose_file.parent

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
    except subprocess.CalledProcessError as e:
        raise DockerComposeError(f"Failed to start services: {e.stderr}")
    except FileNotFoundError:
        raise DockerComposeError("docker or docker compose not found. Please install Docker.")

    # Wait for health check if requested
    if wait_for_health:
        _wait_for_health(compose_file, project_root, timeout)


def stop_services() -> None:
    """Stop Docker Compose services (Memgraph + MCP server).

    Raises:
        DockerComposeError: If stopping services fails
    """
    compose_file = _get_compose_file()
    project_root = compose_file.parent

    # Stop Docker Compose services
    try:
        result = subprocess.run(
            ['docker', 'compose', '-f', str(compose_file), 'down'],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise DockerComposeError(f"Failed to stop services: {e.stderr}")
    except FileNotFoundError:
        raise DockerComposeError("docker or docker compose not found. Please install Docker.")


def get_status() -> List[Dict[str, any]]:
    """Get status of Docker Compose services (Memgraph + MCP server).

    Returns:
        List of service status dictionaries with keys:
        - Name: Container name
        - Service: Service name
        - State: Service state (running, exited, etc.)
        - Health: Health status (healthy, unhealthy, N/A)
        - Publishers: List of port mappings

    Raises:
        DockerComposeError: If checking status fails
    """
    compose_file = _get_compose_file()
    project_root = compose_file.parent

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

        return services

    except subprocess.CalledProcessError as e:
        raise DockerComposeError(f"Failed to check service status: {e.stderr}")
    except FileNotFoundError:
        raise DockerComposeError("docker or docker compose not found. Please install Docker.")
    except json.JSONDecodeError as e:
        raise DockerComposeError(f"Failed to parse service status: {e}")


def is_healthy() -> Tuple[bool, Optional[str]]:
    """Check if services are running and healthy.

    Returns:
        Tuple of (is_healthy, message):
        - is_healthy: True if Memgraph service is healthy
        - message: Status message or error description
    """
    try:
        services = get_status()

        if not services:
            return False, "No services are running"

        # Check if memgraph is healthy
        for service in services:
            if 'memgraph' in service.get('Name', '') or 'memgraph' in service.get('Service', ''):
                health = service.get('Health', '')
                state = service.get('State', '')

                if health == 'healthy':
                    return True, "Services are healthy"
                elif state != 'running':
                    return False, f"Memgraph service is not running (state: {state})"
                else:
                    return False, f"Memgraph service is running but not healthy (health: {health})"

        return False, "Memgraph service not found"

    except DockerComposeError as e:
        return False, str(e)


def _wait_for_health(compose_file: Path, project_root: Path, timeout: int) -> None:
    """Wait for services to become healthy.

    Args:
        compose_file: Path to docker-compose.yml
        project_root: Path to project root directory
        timeout: Maximum time to wait in seconds

    Raises:
        DockerComposeError: If timeout is reached before services become healthy
    """
    max_attempts = timeout // 2  # Check every 2 seconds
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
            services = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    services.append(json.loads(line))

            # Check if memgraph is healthy (mcp-server depends on it)
            for service in services:
                if 'memgraph' in service.get('Name', '') or 'memgraph' in service.get('Service', ''):
                    health = service.get('Health', '')
                    if health == 'healthy':
                        return  # Services are healthy

            time.sleep(2)
            attempt += 1

        except subprocess.CalledProcessError as e:
            time.sleep(2)
            attempt += 1

    # Timeout reached
    raise DockerComposeError(
        f"Services started but health check did not pass within {timeout} seconds. "
        "Run 'docker compose ps' to check service status manually."
    )
