#!/usr/bin/env bash
# Decommissions every GCP resource this project created, in order from cheapest/most-
# reversible to most destructive. Nothing here should run before:
#   1. The hackathon deadline + judging window has passed.
#   2. ./export_corpus.sh has been run FRESH (not an old backup) — Step 4 below destroys
#      the corpus, which took real time and real Vertex AI cost to build.
#
# Each step is its own function so you can run just one (e.g. `bash teardown.sh cloud_run`)
# instead of everything at once. Run with no argument to do all GCP-side steps in order.
# ClickHouse Cloud (Step 4) is NOT included here — it has no CLI configured for this project
# (only DB connection creds, not a control-plane API key), so it's a manual web-console step.
# See teardown.md for that step and for the full explanation/risk of each one.
set -euo pipefail

PROJECT_ID="project-7acae5d3-1b92-4913-971"
REGION="us-central1"
PROJECT_NUMBER="742393615246"

cloud_run() {
  echo "== Deleting Cloud Run services (reversible: redeploy with agent/deploy.sh + the web deploy command in README) =="
  gcloud run services delete screenplay-agent --project="$PROJECT_ID" --region="$REGION" --quiet
  gcloud run services delete agent-cinema-web --project="$PROJECT_ID" --region="$REGION" --quiet
}

artifact_registry() {
  echo "== Deleting the Artifact Registry repo holding built container images (~435MB as of 2026-09-07; reversible: rebuilt automatically on next deploy) =="
  gcloud artifacts repositories delete cloud-run-source-deploy --project="$PROJECT_ID" --location="$REGION" --quiet
}

secret_manager() {
  echo "== Deleting the ClickHouse password secret (reversible: recreate from agent/.env, see agent/deploy.sh's secret-creation step) =="
  gcloud secrets delete clickhouse-password --project="$PROJECT_ID" --quiet
}

iam_cleanup() {
  echo "== Optional: revoking the IAM grants made for this project (no cost either way, pure hygiene) =="
  gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/aiplatform.user" --quiet || true
  gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/storage.objectViewer" --quiet || true
  gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/artifactregistry.writer" --quiet || true
  gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/artifactregistry.writer" --quiet || true
}

case "${1:-all}" in
  cloud_run) cloud_run ;;
  artifact_registry) artifact_registry ;;
  secret_manager) secret_manager ;;
  iam) iam_cleanup ;;
  all)
    cloud_run
    artifact_registry
    secret_manager
    iam_cleanup
    echo
    echo "GCP-side teardown done. Remaining manual steps (see teardown.md):"
    echo "  1. Delete or stop the ClickHouse Cloud service via the web console."
    echo "  2. Optionally delete the whole GCP project (30-day undo window) if you want zero footprint."
    ;;
  *) echo "Unknown step: $1" >&2; exit 1 ;;
esac
