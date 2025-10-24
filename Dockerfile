# Use official Python image as base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy dependency files and README (required by hatchling build)
COPY pyproject.toml uv.lock README.md ./

# Copy application source code (needed before uv sync for editable install)
COPY src/ ./src/

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Create a non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port if needed (MCP servers typically use stdio, but keeping for flexibility)
EXPOSE 8000

# Entry point for the server
# Note: Users need to provide --url and authentication flags at runtime
ENTRYPOINT ["uv", "run", "python", "-m", "mm_mcp.server"]

# Default help output if no arguments provided
CMD ["--help"]
