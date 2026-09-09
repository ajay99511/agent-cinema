#!/usr/bin/env bash
# Backs up the full corpus (script_nodes, is_corpus=1) to a local Parquet file BEFORE any
# teardown step touches ClickHouse. Tested 2026-09-07: produced a 5,153-row, 18-column,
# 23MB file matching the corpus exactly (4188 scenes + 865 sequences + 75 acts + 25 films).
#
# Run this again right before actually deleting the ClickHouse service, not just once now —
# if any more rows get added/changed between planning and teardown, this needs to be fresh.
#
# To restore later: load the schema (infra/clickhouse/schema.sql) into a new ClickHouse
# service, then:
#   clickhouse-client --host <new-host> --query "INSERT INTO script_nodes FORMAT Parquet" < corpus_backup.parquet
# (or the HTTP-interface equivalent, same auth pattern as this script's export call).
set -euo pipefail
cd "$(dirname "$0")/.."

source agent/.env
OUT="corpus_backup_$(date +%Y%m%d).parquet"

curl -sf -m 120 -u "${CLICKHOUSE_USER}:${CLICKHOUSE_PASSWORD}" \
  "https://${CLICKHOUSE_HOST}:${CLICKHOUSE_PORT}/?query=SELECT%20*%20FROM%20script_nodes%20WHERE%20is_corpus%3D1%20FORMAT%20Parquet" \
  -o "$OUT"

echo "Backed up to $OUT ($(du -h "$OUT" | cut -f1))"
echo "Verify before deleting anything: row count should be 5153 (or more, if the corpus grew)."
