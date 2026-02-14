#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "nvim-markdown-notes-memgraph installer"
echo "=========================================="
echo ""

# Check for Python 3.10+
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python 3.10+ is required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION detected"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Warning: docker is not installed${NC}"
    echo "Docker is required to run the Memgraph database and MCP server"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    echo ""
fi

# Check for Docker Compose
if ! docker compose version &> /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: docker compose is not available${NC}"
    echo "Docker Compose is required to run the services"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    echo ""
fi

# Detect package manager preference (uv preferred, fallback to pip)
if command -v uv &> /dev/null; then
    INSTALLER="uv"
    echo -e "${GREEN}✓${NC} uv detected"
elif command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
    INSTALLER="pip"
    echo -e "${GREEN}✓${NC} pip detected"
else
    echo -e "${RED}Error: Neither uv nor pip is available${NC}"
    echo "Please install uv (https://github.com/astral-sh/uv) or pip"
    exit 1
fi

echo ""
echo "Installing nvim-markdown-notes-memgraph..."
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Install the package
if [ "$INSTALLER" = "uv" ]; then
    echo "Using uv to install package..."
    if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
        # Local installation
        cd "$PROJECT_ROOT"
        uv pip install -e .
    else
        # Remote installation (if this script is downloaded standalone)
        uv pip install nvim-markdown-notes-memgraph
    fi
else
    echo "Using pip to install package..."
    if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
        # Local installation
        cd "$PROJECT_ROOT"
        pip install -e .
    else
        # Remote installation (if this script is downloaded standalone)
        pip install nvim-markdown-notes-memgraph
    fi
fi

echo ""
echo -e "${GREEN}✓ Installation complete!${NC}"
echo ""
echo "=========================================="
echo "Post-installation instructions"
echo "=========================================="
echo ""
echo "The 'nvim-markdown-notes-memgraph' CLI is now available."
echo ""
echo "Quick start:"
echo ""
echo "  1. Start the services:"
echo "     nvim-markdown-notes-memgraph start --notes-root /path/to/your/notes"
echo ""
echo "  2. Check status:"
echo "     nvim-markdown-notes-memgraph status"
echo ""
echo "  3. Get MCP configuration:"
echo "     nvim-markdown-notes-memgraph config"
echo ""
echo "  4. Stop the services:"
echo "     nvim-markdown-notes-memgraph stop"
echo ""
echo "Commands:"
echo "  start   - Start Memgraph and MCP server in Docker"
echo "  stop    - Stop all services"
echo "  status  - Check service status"
echo "  config  - Output MCP JSON configuration"
echo "  serve   - Run MCP server directly (container use)"
echo "  bridge  - Run Neovim bridge (stdin/stdout JSON)"
echo ""
echo "For more help:"
echo "  nvim-markdown-notes-memgraph --help"
echo ""
echo "Documentation: https://github.com/yourusername/nvim-markdown-notes-memgraph"
echo ""
