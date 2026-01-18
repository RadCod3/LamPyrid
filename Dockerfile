# ============================================================================
# Builder Stage: Install dependencies and build the project
# ============================================================================
FROM ghcr.io/astral-sh/uv:bookworm-slim AS builder

# Set environment variables for UV optimizations
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Configure Python directory for consistency and use managed Python only
ENV UV_PYTHON_INSTALL_DIR=/python
ENV UV_PYTHON_PREFERENCE=only-managed

# Install Python before the project for better caching
RUN uv python install 3.14

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies with cache mount optimization
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable --no-install-project

# Copy application source code and README (required by pyproject.toml)
COPY src/ ./src/
COPY README.md ./

# Install the project with optimizations
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# Create data directory for OAuth token storage
RUN mkdir -p /app/data/oauth

# ============================================================================
# Runtime Stage: Minimal distroless image
# ============================================================================
FROM gcr.io/distroless/cc-debian13:nonroot AS runtime

# Copy the Python installation from builder
COPY --from=builder --chown=nonroot:nonroot /python /python

# Set working directory
WORKDIR /app

# Copy only the virtual environment from builder
COPY --from=builder --chown=nonroot:nonroot /app/.venv /app/.venv

# Copy data directory structure from builder (for OAuth token storage)
COPY --from=builder --chown=nonroot:nonroot /app/data /app/data

# Set up the virtual environment in PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set default environment variables for HTTP mode
ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=3000

# Expose the MCP server port
EXPOSE 3000

# Health check to verify the server can start
# Note: Distroless has no shell, so use exec form
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import lampyrid; print('Server can import successfully')"]

# Default command to run the MCP server in HTTP mode
CMD ["lampyrid"]
