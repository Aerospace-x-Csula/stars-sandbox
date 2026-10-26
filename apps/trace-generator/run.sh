#!/bin/sh
# Start one trace-generator run as a Kubernetes Job and print its UTC start time.
#
#   ./run.sh <scenario> <run_id> [duration_seconds]
#   ./run.sh normal trace01 300
#
# Scenarios: normal | slow-db | payment-errors
set -eu

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
  echo "Usage: $0 <normal|slow-db|payment-errors> <run_id> [duration_seconds]" >&2
  exit 2
fi

SCENARIO="$1"
RUN_ID="$2"
DURATION="${3:-300}"

case "$SCENARIO" in normal|slow-db|payment-errors) ;; *) echo "Unknown scenario: $SCENARIO" >&2; exit 2;; esac
case "$RUN_ID" in ''|*[!A-Za-z0-9_-]*) echo "RUN_ID must use letters, digits, underscores or hyphens" >&2; exit 2;; esac
[ "${#RUN_ID}" -le 64 ] || { echo "RUN_ID must be at most 64 characters" >&2; exit 2; }
case "$DURATION" in ''|*[!0-9]*) echo "duration must be whole seconds" >&2; exit 2;; esac

DIR=$(cd "$(dirname "$0")" && pwd)

# Kubernetes names must be lowercase with hyphens only.
JOB_NAME="trace-generator-$(printf '%s' "$RUN_ID" | tr 'A-Z_' 'a-z-' | cut -c1-40)"

# Stop early, with a clear message, if this run ID was already used.
if kubectl -n stars get job "$JOB_NAME" >/dev/null 2>&1; then
  echo "Job $JOB_NAME already exists. Use a new run ID, or remove the old one first:" >&2
  echo "  kubectl -n stars delete job $JOB_NAME" >&2
  exit 1
fi

# Refresh the script/requirements ConfigMap so the Job always runs the current code.
kubectl -n stars create configmap trace-generator \
  --from-file="$DIR/generator.py" --from-file="$DIR/requirements.txt" \
  --dry-run=client -o yaml | kubectl apply -f -

START=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
sed -e "s/__JOB_NAME__/$JOB_NAME/g" \
    -e "s/__SCENARIO__/$SCENARIO/g" \
    -e "s/__RUN_ID__/$RUN_ID/g" \
    -e "s/__DURATION__/$DURATION/g" \
    "$DIR/job.yaml" | kubectl create -f -

echo "Submitted job=$JOB_NAME scenario=$SCENARIO run_id=$RUN_ID duration_s=$DURATION submitted_utc=$START"
echo "Follow logs:  kubectl -n stars logs -f job/$JOB_NAME"
echo "The generator logs the exact 'Run started' / 'Run completed' times to record in your manifest."
