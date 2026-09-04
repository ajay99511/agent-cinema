"""Slice 3: the comparative query tools — the actual differentiating capability of the
product ("this scene is in the bottom 8% for conflict among Act II scenes in produced
thrillers"), not just ad-hoc NL-to-SQL.

These are hand-written parameterized queries, not LLM-generated SQL: percentile/cohort
correctness (and the filter-before-vector-scan ordering for similar_scenes) matters enough
here that a reliable Python implementation beats hoping the model writes correct SQL for it
every time. The general-purpose `run_query` MCP tool (agent.py) remains available for
everything else.
"""

from __future__ import annotations

import functools
import os

import clickhouse_connect

# Mirrors etl/screenplay_etl/build_tree.py's _ACT_BOUNDARIES — kept as a local constant
# rather than a cross-package import (agent/ and etl/ are separate uv projects). Using the
# same breakpoints means "percentile among Act II scenes" means the same thing on both sides.
_ACT_BOUNDARIES = (0.25, 0.75)
MIN_COHORT_N = 20  # Q5: below this, a percentile claim looks fake — degrade honestly instead


@functools.lru_cache(maxsize=1)
def _client():
    return clickhouse_connect.get_client(
        host=os.environ["CLICKHOUSE_HOST"],
        port=int(os.environ["CLICKHOUSE_PORT"]),
        username=os.environ["CLICKHOUSE_USER"],
        password=os.environ["CLICKHOUSE_PASSWORD"],
        secure=os.environ.get("CLICKHOUSE_SECURE", "true").lower() == "true",
        database=os.environ.get("CLICKHOUSE_DATABASE", "default"),
    )


def _position_bucket(pct_position: float) -> tuple[float, float]:
    if pct_position < _ACT_BOUNDARIES[0]:
        return (0.0, _ACT_BOUNDARIES[0])
    if pct_position < _ACT_BOUNDARIES[1]:
        return (_ACT_BOUNDARIES[0], _ACT_BOUNDARIES[1])
    return (_ACT_BOUNDARIES[1], 1.0)


def scene_percentiles(script_id: int, node_id: int) -> dict:
    """Compare one scene's valence and conflict to same-genre, same-act-position scenes
    from the produced-film corpus, returning each as a percentile (0-100) plus the cohort
    size actually used.

    Args:
        script_id: the script_id of the scene to look up.
        node_id: the node_id of the scene (must be a level=0 row).

    Returns:
        On success: {"valence_percentile", "conflict_percentile", "cohort_n", "genre",
        "act_position_bucket": [lo, hi]}. If the cohort is too small to be meaningful
        (cohort_n < 20), returns {"insufficient_corpus": True, "cohort_n": n} instead of a
        fabricated percentile — never guess.
    """
    target_sql = (
        "SELECT level, genre, pct_position, valence, conflict FROM script_nodes "
        "WHERE script_id = {script_id:UInt32} AND node_id = {node_id:UInt32} LIMIT 1"
    )
    try:
        client = _client()
        target = client.query(
            target_sql, parameters={"script_id": script_id, "node_id": node_id}
        ).result_rows
        if not target:
            return {"error": f"no row found for script_id={script_id}, node_id={node_id}", "sql": [target_sql]}
        level, genre, pct_position, valence, conflict = target[0]
        if level != 0:
            return {"error": f"node_id={node_id} is level={level}, not a scene (level=0)", "sql": [target_sql]}

        lo, hi = _position_bucket(pct_position)
        cohort_sql = (
            "SELECT valence, conflict FROM script_nodes "
            "WHERE level = 0 AND is_corpus = 1 AND genre = {genre:String} "
            "AND pct_position >= {lo:Float32} AND pct_position < {hi:Float32} "
            "AND NOT (script_id = {script_id:UInt32} AND node_id = {node_id:UInt32})"
        )
        cohort = client.query(
            cohort_sql,
            parameters={"genre": genre, "lo": lo, "hi": hi, "script_id": script_id, "node_id": node_id},
        ).result_rows
        sql = [target_sql, cohort_sql]

        cohort_n = len(cohort)
        if cohort_n < MIN_COHORT_N:
            return {"insufficient_corpus": True, "cohort_n": cohort_n, "genre": genre,
                     "act_position_bucket": [lo, hi], "sql": sql}

        valence_percentile = 100.0 * sum(1 for v, _ in cohort if v <= valence) / cohort_n
        conflict_percentile = 100.0 * sum(1 for _, c in cohort if c <= conflict) / cohort_n
        return {
            "valence_percentile": round(valence_percentile, 1),
            "conflict_percentile": round(conflict_percentile, 1),
            "cohort_n": cohort_n,
            "genre": genre,
            "act_position_bucket": [lo, hi],
            "sql": sql,
        }
    except Exception as e:
        return {"error": f"could not compute percentiles: {type(e).__name__}: {e}", "sql": [target_sql]}


def similar_scenes(script_id: int, node_id: int, k: int = 5, genre: str | None = None) -> dict:
    """Find the k most similar produced-film scenes to a given scene, by embedding distance.

    Filter-first: genre/level/is_corpus narrow the candidate set via WHERE *before* the
    (exact, not approximate) cosineDistance scan — never the other way around.

    Args:
        script_id: the script_id of the reference scene.
        node_id: the node_id of the reference scene (must be a level=0 row).
        k: how many similar scenes to return (default 5).
        genre: optionally restrict candidates to one genre; omit to search the whole corpus.

    Returns:
        {"results": [{"title", "year", "genre", "slug", "summary", "valence", "conflict",
        "distance"}, ...]} ordered by increasing distance (most similar first).
    """
    target_sql = (
        "SELECT level, embedding FROM script_nodes "
        "WHERE script_id = {script_id:UInt32} AND node_id = {node_id:UInt32} LIMIT 1"
    )
    try:
        client = _client()
        target = client.query(
            target_sql, parameters={"script_id": script_id, "node_id": node_id}
        ).result_rows
        if not target:
            return {"error": f"no row found for script_id={script_id}, node_id={node_id}", "sql": [target_sql]}
        level, embedding = target[0]
        if level != 0:
            return {"error": f"node_id={node_id} is level={level}, not a scene (level=0)", "sql": [target_sql]}

        genre_clause = "AND genre = {genre:String} " if genre else ""
        params = {"script_id": script_id, "node_id": node_id, "vec": embedding, "k": k}
        if genre:
            params["genre"] = genre

        similar_sql = (
            "SELECT title, year, genre, slug, summary, valence, conflict, "
            "cosineDistance(embedding, {vec:Array(Float32)}) AS distance "
            "FROM script_nodes "
            "WHERE level = 0 AND is_corpus = 1 "
            f"{genre_clause}"
            "AND NOT (script_id = {script_id:UInt32} AND node_id = {node_id:UInt32}) "
            "ORDER BY distance ASC LIMIT {k:UInt32}"
        )
        rows = client.query(similar_sql, parameters=params).result_rows

        return {
            "results": [
                {"title": r[0], "year": r[1], "genre": r[2], "slug": r[3], "summary": r[4],
                 "valence": r[5], "conflict": r[6], "distance": round(r[7], 4)}
                for r in rows
            ],
            "sql": [target_sql, similar_sql],
        }
    except Exception as e:
        return {"error": f"could not find similar scenes: {type(e).__name__}: {e}", "sql": [target_sql]}
