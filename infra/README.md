# Infrastructure

## ClickHouse

`clickhouse/schema.sql` — the `script_nodes` table (the one-way-door data model).
`clickhouse/seed.sql` — 10-row skeleton dataset for Slice 1.

### Apply it

**Option A — ClickHouse Cloud SQL console (easiest):** paste `schema.sql`, run; paste `seed.sql`, run.

**Option B — clickhouse-client:**
```bash
clickhouse client --host "$CLICKHOUSE_HOST" --port 9440 --secure \
  --user "$CLICKHOUSE_USER" --password "$CLICKHOUSE_PASSWORD" \
  --queries-file infra/clickhouse/schema.sql

clickhouse client --host "$CLICKHOUSE_HOST" --port 9440 --secure \
  --user "$CLICKHOUSE_USER" --password "$CLICKHOUSE_PASSWORD" \
  --queries-file infra/clickhouse/seed.sql
```

### Verify
```sql
SELECT level, count() FROM script_nodes GROUP BY level ORDER BY level;
-- expect: level 0 -> 6, level 2 -> 3, level 3 -> 1
SELECT round(avg(conflict), 3) FROM script_nodes WHERE level = 0;
```

## Google Cloud (done once, by the account owner)

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable aiplatform.googleapis.com run.googleapis.com secretmanager.googleapis.com
gcloud auth application-default login    # so local agent can call Vertex AI
```

Set a **$50 budget alert**: Billing → Budgets & alerts. Scale the ClickHouse service down when idle to
preserve the trial credits.
