# Use Python 3.14 slim image for smaller footprint
FROM python:3.14-slim

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml ./
# Copy uv.lock if it exists (optional for now)
COPY uv.loc[k] ./

# Install dependencies with cache mount optimization
# Use UV_LINK_MODE=copy for compatibility with cache mounts
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_LINK_MODE=copy uv sync --frozen --no-install-project || \
    UV_LINK_MODE=copy uv sync --no-install-project

# Copy application source code, assets, and README (required by pyproject.toml)
COPY src/ ./src/
COPY assets/ ./assets/
COPY README.md ./

# Install the project with optimizations
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_LINK_MODE=copy uv sync --frozen --compile-bytecode || \
    UV_LINK_MODE=copy uv sync --compile-bytecode

# Create a non-root user for security
RUN groupadd -r lampyrid && useradd -r -g lampyrid lampyrid

# Create cache directory for uv and set permissions
RUN mkdir -p /home/lampyrid/.cache/uv && chown -R lampyrid:lampyrid /home/lampyrid

# Set up the virtual environment in PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set default environment variables for HTTP mode
ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=3000

# Change ownership of the app directory
RUN chown -R lampyrid:lampyrid /app

# Switch to non-root user
USER lampyrid

# Expose the MCP server port
EXPOSE 3000

# Health check to verify the server can start
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD uv run python -c "import lampyrid; print('Server can import successfully')" || exit 1

# Default command to run the MCP server in HTTP mode
CMD ["uv", "run", "lampyrid"]
