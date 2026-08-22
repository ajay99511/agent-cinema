"""Offline unit tests for the event-parsing contract. No cloud, no ClickHouse required.

We stand in for ADK event objects with SimpleNamespace, matching the documented shape:
    event.content.parts[] where a part may carry .function_call, .function_response, or .text
"""

from __future__ import annotations

from types import SimpleNamespace

from screenplay_agent.events import extract_reply


def _event(*parts):
    return SimpleNamespace(content=SimpleNamespace(parts=list(parts)))


def _call(name, args):
    return SimpleNamespace(
        function_call=SimpleNamespace(name=name, args=args),
        function_response=None,
        text=None,
    )


def _response(name, response):
    return SimpleNamespace(
        function_call=None,
        function_response=SimpleNamespace(name=name, response=response),
        text=None,
    )


def _text(value):
    return SimpleNamespace(function_call=None, function_response=None, text=value)


def test_extracts_sql_data_and_answer():
    events = [
        _event(_text("Let me check the data...")),
        _event(_call("run_query",{"query": "SELECT avg(conflict) FROM script_nodes WHERE level=0"})),
        _event(_response("run_query",{"rows": [[0.607]]})),
        _event(_text("The average conflict across scenes is 0.61.")),
    ]

    reply = extract_reply(events)

    assert reply.sql_shown == ["SELECT avg(conflict) FROM script_nodes WHERE level=0"]
    assert reply.data == [{"rows": [[0.607]]}]
    # The final answer wins over the intermediate "let me check" chatter.
    assert reply.answer == "The average conflict across scenes is 0.61."


def test_multiple_queries_are_all_captured():
    events = [
        _event(_call("run_query",{"query": "SELECT 1"})),
        _event(_call("run_query",{"sql": "SELECT 2"})),  # alt arg key
        _event(_text("done")),
    ]
    reply = extract_reply(events)
    assert reply.sql_shown == ["SELECT 1", "SELECT 2"]


def test_ignores_non_sql_tool_and_blank_text():
    events = [
        _event(_call("list_tables", {"database": "default"})),
        _event(_text("   ")),
        _event(_text("real answer")),
    ]
    reply = extract_reply(events)
    assert reply.sql_shown == []
    assert reply.answer == "real answer"


def test_empty_events_yield_empty_reply():
    reply = extract_reply([])
    assert reply.answer == ""
    assert reply.sql_shown == []
    assert reply.data == []
    assert reply.to_dict() == {"answer": "", "sql_shown": [], "data": []}
