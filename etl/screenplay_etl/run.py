"""CLI entrypoint. Usage (from etl/):
    uv run python -m screenplay_etl.run                 # load films not already in ClickHouse
    uv run python -m screenplay_etl.run --force          # reprocess every film, even ones already loaded
    uv run python -m screenplay_etl.run --limit 1        # load just the first (unloaded) film (smoke test)
    uv run python -m screenplay_etl.run --verify         # re-check the AVG invariant, no loading
    uv run python -m screenplay_etl.run --drop-seed-film  # remove Slice 1's placeholder script_id=1

Resumable by default: a multi-hour run getting killed by a session/process interruption is a
real failure mode we hit in practice (Session 5), not a hypothetical — each film that already
has rows in ClickHouse is skipped unless --force is passed.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from google import genai
from google.genai import types

from . import db
from .films import FILMS
from .pipeline import process_film


def build_genai_client() -> genai.Client:
    db.load_env()
    return genai.Client(
        vertexai=True,
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.environ["GOOGLE_CLOUD_LOCATION"],
        # Without an explicit timeout, a stalled request hangs indefinitely and never raises
        # — which means embed.py/summarize.py's retry-with-backoff never even triggers, since
        # retries only fire on an exception. Hit exactly this in practice (Session 5): the
        # full-corpus run silently stopped making progress for 20+ minutes on one film with no
        # error. 120s is generous for a single embed/generate call but still bounds the hang.
        http_options=types.HttpOptions(timeout=120_000),
    )


def verify_invariant(client) -> None:
    """Live SQL check: does every parent's stored valence match AVG(children.valence)?
    This — not the Python arithmetic in pipeline.py — is what actually proves the
    "numbers are aggregates" guardrail (see pipeline.py module docstring).
    """
    rows = client.query("""
        SELECT parent.script_id, parent.node_id, parent.valence AS stored,
               avg(child.valence) AS computed, count(*) AS n
        FROM script_nodes AS parent
        JOIN script_nodes AS child
          ON child.parent_id = parent.node_id AND child.script_id = parent.script_id
        WHERE parent.node_id != parent.parent_id AND parent.is_corpus = 1
        GROUP BY parent.script_id, parent.node_id, parent.valence
        HAVING abs(stored - computed) > 0.001
    """).result_rows
    if rows:
        print(f"INVARIANT VIOLATION on {len(rows)} nodes (stored != AVG(children)):")
        for r in rows[:10]:
            print(f"  script_id={r[0]} node_id={r[1]} stored={r[2]:.4f} computed={r[3]:.4f} n={r[4]}")
        sys.exit(1)
    print("Invariant holds: every parent.valence == AVG(children.valence) across the corpus.")

    counts = client.query(
        "SELECT level, count() FROM script_nodes WHERE is_corpus = 1 GROUP BY level ORDER BY level"
    ).result_rows
    print("Row counts by level (is_corpus=1):", dict(counts))

    orphans = client.query("""
        SELECT count() FROM script_nodes AS c
        LEFT JOIN script_nodes AS p ON c.parent_id = p.node_id AND c.script_id = p.script_id
        WHERE c.is_corpus = 1 AND c.node_id != c.parent_id AND p.node_id = 0
    """).result_rows[0][0]
    print(f"Orphan parent_id rows: {orphans}")

    dims = client.query(
        "SELECT DISTINCT length(embedding) FROM script_nodes WHERE is_corpus = 1"
    ).result_rows
    print(f"Distinct embedding dimensions present: {[d[0] for d in dims]} (expect exactly [768])")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="process only the first N (unloaded) films")
    parser.add_argument("--force", action="store_true", help="reprocess films even if already loaded")
    parser.add_argument("--verify", action="store_true", help="run the post-load invariant check and exit")
    parser.add_argument("--drop-seed-film", action="store_true", help="delete Slice 1's placeholder script_id=1 and exit")
    args = parser.parse_args()

    ch_client = db.get_client()

    if args.drop_seed_film:
        db.delete_film(ch_client, 1)
        print("Deleted placeholder script_id=1 (Slice 1 seed).")
        return

    if args.verify:
        verify_invariant(ch_client)
        return

    genai_client = build_genai_client()

    already_loaded: set[int] = set()
    if not args.force:
        rows = ch_client.query(
            "SELECT DISTINCT script_id FROM script_nodes WHERE is_corpus = 1"
        ).result_rows
        already_loaded = {r[0] for r in rows}

    pending = [f for f in FILMS if f.script_id not in already_loaded]
    if already_loaded:
        print(f"Skipping {len(FILMS) - len(pending)} already-loaded film(s) (use --force to reprocess).")
    films = pending[: args.limit] if args.limit else pending

    for i, film in enumerate(films, 1):
        start = time.time()
        try:
            rows = process_film(film, genai_client)
            db.delete_film(ch_client, film.script_id)  # idempotent re-run
            db.insert_rows(ch_client, rows)
            elapsed = time.time() - start
            print(f"[{i}/{len(films)}] OK   {film.title} ({len(rows)} rows, {elapsed:.1f}s)")
        except Exception as e:
            elapsed = time.time() - start
            print(f"[{i}/{len(films)}] FAIL {film.title} ({elapsed:.1f}s): {type(e).__name__}: {e}")

    print("\nDone. Run with --verify to check the AVG invariant, row counts, and embedding dims.")


if __name__ == "__main__":
    main()
