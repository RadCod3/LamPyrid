# ============================================================================
# Builder Stage: Install dependencies and build the project
# ============================================================================
FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Set environment variables for UV optimizations
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1

# Install dependencies with cache mount optimization
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable --no-install-project

# Copy application source code and README (required by pyproject.toml)
COPY src/ ./src/
COPY README.md ./

# Install the project with optimizations
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# ============================================================================
# Runtime Stage: Minimal production image
# ============================================================================
FROM python:3.14-alpine AS runtime

# Set working directory
WORKDIR /app

# Copy only the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Create a non-root user for security (Alpine uses addgroup/adduser)
RUN addgroup -S lampyrid && adduser -S -G lampyrid -h /home/lampyrid lampyrid

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
    CMD python -c "import lampyrid; print('Server can import successfully')" || exit 1

# Default command to run the MCP server in HTTP mode
CMD ["lampyrid"]
