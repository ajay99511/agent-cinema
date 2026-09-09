# Teardown plan — decommission everything, without losing work

**Do not run any of this before the hackathon deadline (Sept 7, 2:00pm PT) and judging window
have passed.** The live URLs are what the submission points judges at.

## Philosophy

Ordered cheapest/most-reversible → most destructive, with a mandatory backup before the one
genuinely irreversible step. Nothing here deletes your local code, your git history, or your
GitHub repo — those cost nothing to keep and are what let you rebuild everything else.

## What actually costs money right now

| Resource | Cost at rest | Reversibility |
|---|---|---|
| Cloud Run services (`screenplay-agent`, `agent-cinema-web`) | Near-zero — both scale to 0 instances when idle; you only pay for actual request time | Fully reversible: redeploy from the same committed source with `agent/deploy.sh` / the README's web deploy command |
| Artifact Registry (`cloud-run-source-deploy`, ~435MB) | Small, ongoing storage fee, scales with accumulated image size | Reversible: rebuilt automatically on the next deploy |
| Secret Manager (`clickhouse-password`) | Negligible (~$0.06/version/month) | Reversible: recreate from `agent/.env` |
| **ClickHouse Cloud service** | The real cost driver — compute + storage, likely still covered by the ~30-day trial credit (service created ~2026-08-21, so check the ClickHouse console for the actual trial end date rather than trusting this estimate) | **NOT reversible** — deleting it destroys the 25-film corpus (hours of real Vertex AI embedding/summarization work). Back it up first. |
| GCP project itself | $0 just for existing, once the above are cleaned up | N/A |

## Step 0 — Back up the corpus (do this immediately before Step 4, not just once now)

```bash
bash infra/export_corpus.sh
```

Already tested (2026-09-07): produces a ~23MB Parquet file with all 5,153 rows (4188 scenes +
865 sequences + 75 acts + 25 films) and all 18 columns including embeddings. To restore later:
load `infra/clickhouse/schema.sql` into a fresh ClickHouse service, then `INSERT INTO
script_nodes FORMAT Parquet` from the backup file (see the script's own comments for the exact
command). Keep this file somewhere durable (not just this repo's working directory) — it's the
one piece of this teardown you cannot regenerate without re-running the ETL and paying for
Vertex AI calls again.

## Step 1 — Cloud Run (cheap, fully reversible)

```bash
bash infra/teardown.sh cloud_run
```

Deletes both services. Bringing them back is exactly `bash agent/deploy.sh` plus the `gcloud
run deploy agent-cinema-web ...` command already documented in the README's Deployment section
— no new decisions needed, just re-running what's already written down.

## Step 2 — Artifact Registry (cheap, fully reversible)

```bash
bash infra/teardown.sh artifact_registry
```

Removes the accumulated container images. The next deploy recreates the repo automatically
(same as it did the first time), so this is pure cleanup, not a risk.

## Step 3 — Secret Manager (cheap, fully reversible)

```bash
bash infra/teardown.sh secret_manager
```

## Step 4 — ClickHouse Cloud (⚠️ the irreversible one — manual, via their web console)

There's no CLI for this because the project was only ever given database connection
credentials, not a ClickHouse Cloud control-plane API key (nothing to fix — this was a
reasonable choice at the time, it just means this one step isn't scriptable).

1. **Confirm Step 0's backup file exists and is recent.**
2. Log into console.clickhouse.cloud, open the service, and either:
   - **Stop** it (pauses compute billing; you can decide about storage/deletion later), or
   - **Delete** it outright (removes both compute and storage billing entirely).
3. If you want zero doubt about billing, check the trial/credit balance on that same page
   before deciding between stop vs. delete.

## Step 5 (optional) — IAM cleanup

```bash
bash infra/teardown.sh iam
```

Costs nothing either way — purely tidies up the IAM grants made for Cloud Build/Cloud Run to
work on this project. Skip if you're going to delete the whole project anyway (Step 6 makes
this moot).

## Step 6 (optional, "nuclear") — delete the whole GCP project

Only worth doing if you want zero trace of the project in your GCP console, not just zero
cost. Google gives a 30-day undo window before a deleted project is permanently purged, so
this is safer than it sounds:

```bash
gcloud projects delete project-7acae5d3-1b92-4913-971
```

Not required for the cost goal — an empty project (after Steps 1-3) costs nothing just for
existing.

## What NOT to touch

- **The GitHub repo.** Free to host, and the hackathon submission points to it — deleting or
  privating it after judging is a separate decision from cost, not something this plan does.
- **Local code, `.env` files, `agent/uv.lock`/`etl/uv.lock`.** These cost nothing and are what
  let you redeploy in five minutes if you ever want to revive this.
- **The corpus backup from Step 0.** Keep it outside this repo's working directory (it's
  large and not meant to be committed) — a separate drive, cloud storage, wherever you keep
  things you don't want to lose.
