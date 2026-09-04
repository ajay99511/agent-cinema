"""Extract what the UI needs from a run of ADK events.

The frontend contract is ``{answer, sql_shown, data}``:
  * ``answer``    — the agent's final natural-language text
  * ``sql_shown`` — every SQL string the agent sent to the ClickHouse MCP tool (the
                    "show the SQL" proof that numbers came from a live query)
  * ``data``      — the rows the MCP tool returned, so the UI can render them

This module is deliberately PURE and framework-agnostic: it reads the documented event
shape via ``getattr`` duck-typing, so it can be unit-tested with plain stand-in objects
and never needs the cloud. See ``tests/test_events.py``.

Besides the MCP ``run_query`` tool, Slice 3 added native FunctionTools (``scene_percentiles``,
``similar_scenes`` — tools.py) that also run live ClickHouse queries but return a plain dict
rather than taking raw SQL as an argument. Rather than hardcode their names here, any tool
response that includes a ``"sql"`` key (a list of the statements it ran) has those folded into
``sql_shown`` too — so a future tool built the same way is picked up automatically, and the
"every number came from a visible live query" UI claim stays true as the tool surface grows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

# The ClickHouse MCP server (mcp-clickhouse) registers its query tool as "run_query"
# (see mcp_clickhouse/mcp_server.py: Tool.from_function(run_query_async, name="run_query")).
# It runs read-only by default unless CLICKHOUSE_ALLOW_WRITE_ACCESS is set, which we never set.
SQL_TOOL_NAME = "run_query"
# The argument that carries the SQL text (`def run_query(query: str)`).
SQL_ARG_KEYS = ("query", "sql")


@dataclass
class AgentReply:
    answer: str = ""
    sql_shown: list[str] = field(default_factory=list)
    data: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"answer": self.answer, "sql_shown": self.sql_shown, "data": self.data}


def _parts(event: Any) -> Iterable[Any]:
    content = getattr(event, "content", None)
    parts = getattr(content, "parts", None)
    return parts or []


def _sql_from_call(args: Any) -> str | None:
    if not isinstance(args, dict):
        return None
    for key in SQL_ARG_KEYS:
        value = args.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def extract_reply(events: Iterable[Any]) -> AgentReply:
    """Fold a sequence of ADK events into the UI contract.

    - Collects SQL from every ``run_query`` function call.
    - Collects the response payload from every matching function response.
    - Uses the last non-empty run of model text as the final answer, so intermediate
      "let me check..." chatter doesn't leak into the answer.
    """
    reply = AgentReply()
    latest_text: str | None = None

    for event in events:
        buffered: list[str] = []
        for part in _parts(event):
            call = getattr(part, "function_call", None)
            if call is not None and getattr(call, "name", None) == SQL_TOOL_NAME:
                sql = _sql_from_call(getattr(call, "args", None))
                if sql:
                    reply.sql_shown.append(sql)

            response = getattr(part, "function_response", None)
            if response is not None:
                name = getattr(response, "name", None)
                payload = getattr(response, "response", None)
                if name == SQL_TOOL_NAME and payload is not None:
                    reply.data.append(payload)
                elif isinstance(payload, dict) and isinstance(payload.get("sql"), list):
                    reply.sql_shown.extend(s for s in payload["sql"] if isinstance(s, str) and s.strip())
                    reply.data.append(payload)

            text = getattr(part, "text", None)
            if isinstance(text, str) and text.strip():
                buffered.append(text.strip())

        if buffered:
            latest_text = "\n".join(buffered)

    if latest_text:
        reply.answer = latest_text
    return reply
