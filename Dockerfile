# Multi-stage build to keep final image small
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

# Install build dependencies for pymgclient
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy package files
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

# Install the package and dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Stage 2: Runtime image
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Environment variables for Memgraph connection
ENV MEMGRAPH_HOST=memgraph
ENV MEMGRAPH_PORT=7687
ENV NOTES_ROOT=/notes

# Create notes directory
RUN mkdir -p /notes

# Set entrypoint to run MCP server via CLI
ENTRYPOINT ["nvim-markdown-notes-memgraph", "serve"]
