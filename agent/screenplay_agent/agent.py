"""The screenplay analysis agent.

Slice 1 (walking skeleton): a Gemini agent (via Vertex AI) whose single capability is to
query the ClickHouse `script_nodes` table through the **ClickHouse MCP server**. It turns a
natural-language question into a read-only `SELECT`, runs it via the MCP `run_query`
tool, and answers from the returned rows.

Later slices add structured tools (percentiles, filter-first vector search) on top of this
same spine.
"""

from __future__ import annotations

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from google.genai import types
from mcp import StdioServerParameters

from .config import load_settings
from .tools import scene_percentiles, similar_scenes

# Explicit rather than implicit: Google's standard default threshold, declared rather than
# left to whatever the SDK/model defaults to. Screenplays legitimately discuss violence,
# abuse, and other dark themes (several corpus titles are crime/horror) — BLOCK_MEDIUM_AND_ABOVE
# (not a stricter level) avoids over-blocking legitimate plot analysis while still filtering
# genuinely harmful content; it is not loosened below Google's own recommended default.
_SAFETY_SETTINGS = [
    types.SafetySetting(category=cat, threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE)
    for cat in (
        types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
    )
]

INSTRUCTION = """
You are a screenplay structural analyst. You answer questions about a corpus of produced
films (and, later, a user's own draft) stored in a ClickHouse table named `script_nodes`.

The table is a tree of nodes. Key columns:
  script_id, node_id, parent_id   tree identity — a node's parent is the row where node_id = parent_id
  level        0=scene 1=sequence 2=act 3=film (a scene's act is its parent's parent)
  is_corpus    1=produced film, 0=user draft
  genre, year, title
  valence, conflict, arousal   emotional metrics (scene-level are measured; parents are averages)
  pct_position 0..1 position through the script
  seq_idx      order among siblings
  char_ids, line_count, summary, slug

If you're ever unsure of the exact schema, call `list_tables` first rather than guessing —
it reflects the real table, this description might drift from it.

`slug` is populated for scenes (level 0) ONLY — it is empty at every other level. When you
GROUP BY or otherwise need a unique key for a sequence/act/film node, use `node_id`, never
`slug` (grouping by an empty `slug` silently merges distinct acts/sequences/films together).

You also have two purpose-built comparison tools — prefer these over hand-writing SQL
whenever the question fits them, since their percentile/cohort math is fixed and tested:
- `scene_percentiles(script_id, node_id)` — how a scene's valence/conflict compares to
  same-genre, same-act-position scenes in the produced-film corpus, as a percentile. If the
  comparable corpus is too small, it returns `insufficient_corpus` instead of a percentile —
  report that honestly, never estimate one yourself.
- `similar_scenes(script_id, node_id, k, genre)` — the k most similar produced-film scenes
  to a given scene, by embedding distance.
Both require a scene's `node_id` — if the user names a film/moment rather than an ID, find
the row first with `run_query`, then call the tool with the `node_id` you found.

Rules you MUST follow:
- Every number you report MUST come from a `run_query` call or one of the two tools above.
  Never estimate or invent a number. If a query returns nothing, say so plainly.
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
            # Must exceed CLICKHOUSE_MCP_QUERY_TIMEOUT (60s, see config.py) so the ADK
            # side never gives up before the ClickHouse-side timeout would.
            timeout=90,
        )
    )


def build_agent() -> Agent:
    settings = load_settings()
    return Agent(
        name="screenplay_analyst",
        model=settings.model,
        instruction=INSTRUCTION,
        tools=[build_clickhouse_toolset(), scene_percentiles, similar_scenes],
        generate_content_config=types.GenerateContentConfig(safety_settings=_SAFETY_SETTINGS),
    )


# ADK / Agent Engine convention: expose a module-level `root_agent`.
root_agent = build_agent()
