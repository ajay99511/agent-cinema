"""Direct-SQL data endpoints for the interactive map UI (Slice 4) — deliberately NOT LLM
tools. The chart fires a request on every drill/brush interaction; routing that through the
agent's conversational loop would be slow, costly, and non-deterministic for what is just a
parameterized SELECT. `tools.py` is for the LLM; this module is for the UI, but both are
equally "ClickHouse queried at runtime" — the guardrail is about the query being live and
real, not about which caller issues it.

Every response includes the literal SQL text executed, so the UI's "show SQL" panel is never
fabricated — it renders exactly what ran.
"""

from __future__ import annotations

from .tools import _client


def list_films() -> dict:
    sql = (
        "SELECT script_id, title, genre, year FROM script_nodes "
        "WHERE level = 3 AND is_corpus = 1 ORDER BY title"
    )
    rows = _client().query(sql).result_rows
    return {
        "sql": sql,
        "films": [{"script_id": r[0], "title": r[1], "genre": r[2], "year": r[3]} for r in rows],
    }


def arc_data(script_id: int, level: int, parent_id: int | None = None) -> dict:
    if level not in (0, 1, 2, 3):
        return {"error": f"level must be 0-3, got {level}"}

    params: dict = {"script_id": script_id, "level": level}
    parent_clause = ""
    if parent_id is not None:
        parent_clause = "AND parent_id = {parent_id:UInt32} "
        params["parent_id"] = parent_id

    sql = (
        "SELECT node_id, seq_idx, pct_position, valence, conflict, title, slug, summary "
        "FROM script_nodes "
        "WHERE script_id = {script_id:UInt32} AND level = {level:UInt8} "
        f"{parent_clause}"
        "ORDER BY seq_idx"
    )
    try:
        rows = _client().query(sql, parameters=params).result_rows
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}", "sql": sql}

    return {
        "sql": sql,
        "level": level,
        "has_children": level > 0,  # by tree construction: only level=0 (scenes) are leaves
        "nodes": [
            {
                "node_id": r[0], "seq_idx": r[1], "pct_position": r[2],
                "valence": r[3], "conflict": r[4], "title": r[5], "slug": r[6], "summary": r[7],
            }
            for r in rows
        ],
    }
