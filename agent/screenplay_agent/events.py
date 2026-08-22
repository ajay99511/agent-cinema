"""Extract what the UI needs from a run of ADK events.

The frontend contract is ``{answer, sql_shown, data}``:
  * ``answer``    — the agent's final natural-language text
  * ``sql_shown`` — every SQL string the agent sent to the ClickHouse MCP tool (the
                    "show the SQL" proof that numbers came from a live query)
  * ``data``      — the rows the MCP tool returned, so the UI can render them

This module is deliberately PURE and framework-agnostic: it reads the documented event
shape via ``getattr`` duck-typing, so it can be unit-tested with plain stand-in objects
and never needs the cloud. See ``tests/test_events.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

# The ClickHouse MCP server exposes its read-only query tool under this name.
SQL_TOOL_NAME = "run_select_query"
# The argument that carries the SQL text.
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

    - Collects SQL from every ``run_select_query`` function call.
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
            if response is not None and getattr(response, "name", None) == SQL_TOOL_NAME:
                payload = getattr(response, "response", None)
                if payload is not None:
                    reply.data.append(payload)

            text = getattr(part, "text", None)
            if isinstance(text, str) and text.strip():
                buffered.append(text.strip())

        if buffered:
            latest_text = "\n".join(buffered)

    if latest_text:
        reply.answer = latest_text
    return reply
