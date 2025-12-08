FROM python:3.13-slim

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install dependencies (production only)
RUN uv sync --frozen --no-dev

# Cloud Run uses PORT env var (default 8080)
ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8080

EXPOSE 8080

CMD ["uv", "run", "python", "-m", "exa_mcp"]
