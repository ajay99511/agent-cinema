#!/usr/bin/env bash
# Deploys the agent to Cloud Run. Run from the agent/ directory (or via `bash agent/deploy.sh`).
# Requires: gcloud CLI authenticated as an account with access to $PROJECT_ID (see PROGRESS.md
# Session 4/5 notes on the gcloud-CLI-token-vs-ADC mismatch quirk — this must be fixed first,
# run `gcloud projects describe "$PROJECT_ID"` and confirm it succeeds before running this).
set -euo pipefail

PROJECT_ID="project-7acae5d3-1b92-4913-971"
REGION="us-central1"
SERVICE="screenplay-agent"
PROJECT_NUMBER="742393615246"
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

cd "$(dirname "$0")"

echo "== Enabling required APIs =="
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com aiplatform.googleapis.com cloudbuild.googleapis.com \
  --project="$PROJECT_ID"

echo "== Loading ClickHouse password from .env (value itself is never printed) =="
set -a
# shellcheck disable=SC1091
source .env
set +a

echo "== Creating/updating the clickhouse-password secret =="
if gcloud secrets describe clickhouse-password --project="$PROJECT_ID" >/dev/null 2>&1; then
  printf '%s' "$CLICKHOUSE_PASSWORD" | gcloud secrets versions add clickhouse-password \
    --project="$PROJECT_ID" --data-file=- >/dev/null
else
  printf '%s' "$CLICKHOUSE_PASSWORD" | gcloud secrets create clickhouse-password \
    --project="$PROJECT_ID" --data-file=- >/dev/null
fi

echo "== Granting the Cloud Run service account access to the secret + Vertex AI =="
gcloud secrets add-iam-policy-binding clickhouse-password \
  --project="$PROJECT_ID" \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/secretmanager.secretAccessor" >/dev/null

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/aiplatform.user" >/dev/null

echo "== Building + deploying to Cloud Run (this can take a few minutes) =="
gcloud run deploy "$SERVICE" \
  --source=. \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --allow-unauthenticated \
  --memory=1Gi \
  --timeout=300 \
  --min-instances=0 \
  --max-instances=3 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=TRUE,MODEL=${MODEL},CLICKHOUSE_HOST=${CLICKHOUSE_HOST},CLICKHOUSE_PORT=${CLICKHOUSE_PORT},CLICKHOUSE_USER=${CLICKHOUSE_USER},CLICKHOUSE_SECURE=${CLICKHOUSE_SECURE},CLICKHOUSE_DATABASE=${CLICKHOUSE_DATABASE}" \
  --set-secrets="CLICKHOUSE_PASSWORD=clickhouse-password:latest"

echo "== Service URL =="
gcloud run services describe "$SERVICE" --project="$PROJECT_ID" --region="$REGION" \
  --format="value(status.url)"
