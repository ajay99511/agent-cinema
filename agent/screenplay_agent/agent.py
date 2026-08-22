"""The screenplay analysis agent.

Slice 1 (walking skeleton): a Gemini agent (via Vertex AI) whose single capability is to
query the ClickHouse `script_nodes` table through the **ClickHouse MCP server**. It turns a
natural-language question into a read-only `SELECT`, runs it via the MCP `run_select_query`
tool, and answers from the returned rows.

Later slices add structured tools (percentiles, filter-first vector search) on top of this
same spine.
"""

from __future__ import annotations

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters

from .config import load_settings

INSTRUCTION = """
You are a screenplay structural analyst. You answer questions about a corpus of produced
films (and, later, a user's own draft) stored in a ClickHouse table named `script_nodes`.

The table is a tree of nodes. Key columns:
  level        0=scene 1=sequence 2=act 3=film
  is_corpus    1=produced film, 0=user draft
  genre, year, title
  valence, conflict, arousal   emotional metrics (scene-level are measured; parents are averages)
  pct_position 0..1 position through the script
  seq_idx      order among siblings
  summary, slug

Rules you MUST follow:
- Every number you report MUST come from a `run_select_query` call. Never estimate or invent a
  number. If a query returns nothing, say so plainly.
- Only issue read-only SELECT statements.
- Prefer one focused query. Explain the answer in plain language a screenwriter understands.
- If the data can't be reached, say you couldn't reach the data — do not fabricate a result.
""".strip()


def build_clickhouse_toolset() -> MCPToolset:
    """Launch the ClickHouse MCP server over stdio, wired to the configured cluster."""
    settings = load_settings()
    return MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=settings.mcp_command,
                args=list(settings.mcp_args),
                env=settings.clickhouse_env(),
            ),
            timeout=60,
        )
    )


def build_agent() -> Agent:
    settings = load_settings()
    return Agent(
        name="screenplay_analyst",
        model=settings.model,
        instruction=INSTRUCTION,
        tools=[build_clickhouse_toolset()],
    )


# ADK / Agent Engine convention: expose a module-level `root_agent`.
root_agent = build_agent()
