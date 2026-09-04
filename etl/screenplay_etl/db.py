"""ClickHouse client + insert/verify helpers. Reuses the agent's own .env (same ClickHouse
Cloud service) rather than duplicating credentials in a second file.
"""

from __future__ import annotations

import os
from pathlib import Path

import clickhouse_connect
from dotenv import load_dotenv

_COLUMNS = [
    "script_id", "node_id", "parent_id", "level", "seq_idx", "pct_position", "is_corpus",
    "genre", "year", "title", "valence", "conflict", "arousal", "char_ids", "line_count",
    "summary", "slug", "embedding",
]


def load_env() -> None:
    load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / "agent" / ".env")


def get_client():
    load_env()
    return clickhouse_connect.get_client(
        host=os.environ["CLICKHOUSE_HOST"],
        port=int(os.environ["CLICKHOUSE_PORT"]),
        username=os.environ["CLICKHOUSE_USER"],
        password=os.environ["CLICKHOUSE_PASSWORD"],
        secure=os.environ.get("CLICKHOUSE_SECURE", "true").lower() == "true",
        database=os.environ.get("CLICKHOUSE_DATABASE", "default"),
    )


def delete_film(client, script_id: int) -> None:
    """Makes re-running the ETL for one film idempotent (plan's Slice 2 acceptance criterion)."""
    client.command(f"ALTER TABLE script_nodes DELETE WHERE script_id = {int(script_id)}")


def insert_rows(client, rows: list[dict]) -> None:
    if not rows:
        return
    data = [[row[col] for col in _COLUMNS] for row in rows]
    client.insert("script_nodes", data, column_names=_COLUMNS)
