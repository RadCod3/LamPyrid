# ============================================================================
# Builder Stage: Install dependencies and build the project
# ============================================================================
FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml ./
# Copy uv.lock if it exists (optional for now)
COPY uv.loc[k] ./

# Install dependencies with cache mount optimization
# Use UV_LINK_MODE=copy for compatibility with cache mounts
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_LINK_MODE=copy uv sync --frozen --no-dev --no-install-project || \
    UV_LINK_MODE=copy uv sync --no-dev --no-install-project

# Copy application source code, assets, and README (required by pyproject.toml)
COPY src/ ./src/
COPY assets/ ./assets/
COPY README.md ./

# Install the project with optimizations
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_LINK_MODE=copy uv sync --frozen --no-dev --compile-bytecode || \
    UV_LINK_MODE=copy uv sync --no-dev --compile-bytecode

# ============================================================================
# Runtime Stage: Minimal production image
# ============================================================================
FROM python:3.14-alpine AS runtime

# Set working directory
WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source code and assets
COPY --from=builder /app/src /app/src
COPY --from=builder /app/assets /app/assets

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
