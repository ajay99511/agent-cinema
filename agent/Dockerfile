FROM python:3.12-slim

# uv + uvx: uv runs the agent's own deps; uvx launches the ClickHouse MCP server as an
# isolated subprocess (it needs mcp 2/fastmcp, which conflicts with the agent's mcp<2 — see
# screenplay_agent/config.py). Installed via pip/PyPI rather than COPY --from=ghcr.io/...:
# Cloud Build's sandboxed network proved unreliable pulling cross-registry OCI layers.
RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY README.md ./
COPY screenplay_agent ./screenplay_agent
COPY server.py ./
RUN uv sync --frozen --no-dev

# Pre-warm the uvx cache for mcp-clickhouse at build time, not at every cold start —
# otherwise the first request after every Cloud Run cold start pays a live PyPI resolve+install
# on top of ClickHouse Cloud's own wake-from-idle latency, which stacks badly for a live demo.
RUN uvx mcp-clickhouse --help > /dev/null 2>&1 || true

ENV PATH="/app/.venv/bin:$PATH"

# Cloud Run injects $PORT; default 8080 for local `docker run` parity.
CMD ["sh", "-c", "uv run uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]
