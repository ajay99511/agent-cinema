"""Central configuration, read from the environment.

Nothing here calls the cloud or fails at import time — so the module can be imported in
tests and tooling without credentials. Values are validated lazily by whoever uses them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Populates os.environ from a local .env before anything reads it — including the
# google-genai SDK's own internal lookups (GOOGLE_GENAI_USE_VERTEXAI etc.), which happen
# outside this module's control. A no-op (no error) when no .env file is present, e.g. in
# a deployed environment where real env vars are injected instead.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    # --- Vertex AI / Gemini (the ONLY permitted AI provider for this hackathon) ---
    project: str
    location: str
    model: str
    use_vertexai: bool

    # --- ClickHouse (queried at runtime via the ClickHouse MCP server) ---
    ch_host: str
    ch_port: str
    ch_user: str
    ch_password: str
    ch_secure: bool
    ch_database: str

    # --- ClickHouse MCP server launch command (stdio) ---
    mcp_command: str
    mcp_args: tuple[str, ...]

    def clickhouse_env(self) -> dict[str, str]:
        """Env vars the mcp-clickhouse server reads to connect to the cluster."""
        return {
            "CLICKHOUSE_HOST": self.ch_host,
            "CLICKHOUSE_PORT": self.ch_port,
            "CLICKHOUSE_USER": self.ch_user,
            "CLICKHOUSE_PASSWORD": self.ch_password,
            "CLICKHOUSE_SECURE": "true" if self.ch_secure else "false",
            "CLICKHOUSE_DATABASE": self.ch_database,
            # ClickHouse Cloud's cheapest tier auto-suspends when idle and can take
            # 20-30s to wake on the first query of a session. Default (30s) query
            # timeout cuts that off right at the edge; 60s gives it headroom.
            "CLICKHOUSE_MCP_QUERY_TIMEOUT": "60",
        }


def _bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    return Settings(
        project=os.getenv("GOOGLE_CLOUD_PROJECT", ""),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        model=os.getenv("MODEL", "gemini-2.5-flash"),
        use_vertexai=_bool(os.getenv("GOOGLE_GENAI_USE_VERTEXAI"), True),
        ch_host=os.getenv("CLICKHOUSE_HOST", ""),
        ch_port=os.getenv("CLICKHOUSE_PORT", "8443"),  # ClickHouse Cloud HTTPS (clickhouse-connect)
        ch_user=os.getenv("CLICKHOUSE_USER", "default"),
        ch_password=os.getenv("CLICKHOUSE_PASSWORD", ""),
        ch_secure=_bool(os.getenv("CLICKHOUSE_SECURE"), True),
        ch_database=os.getenv("CLICKHOUSE_DATABASE", "default"),
        # The ClickHouse MCP server runs as an isolated subprocess via `uvx`, so its
        # mcp-2/fastmcp stack never collides with the agent's mcp-1 client stack.
        mcp_command=os.getenv("MCP_CLICKHOUSE_CMD", "uvx"),
        mcp_args=tuple(os.getenv("MCP_CLICKHOUSE_ARGS", "mcp-clickhouse").split()),
    )
