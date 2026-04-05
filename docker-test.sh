#!/usr/bin/env bash
#
# docker-test.sh — Quick Docker verification for Supply Chain OpenEnv
#
# Builds the image, runs container in background, tests API endpoints, prints results, stops container.
#

set -euo pipefail

IMAGE_NAME="supplychain-openenv-test"
CONTAINER_NAME="supplychain-test-container"
PORT=8000
HOST="localhost"

log() { echo "[$(date +%H:%M:%S)] $*" >&2; }

cleanup() {
  log "Cleaning up..."
  docker stop "$CONTAINER_NAME" 2>/dev/null || true
  docker rm "$CONTAINER_NAME" 2>/dev/null || true
  docker rmi "$IMAGE_NAME" 2>/dev/null || true
}
trap cleanup EXIT

wait_for_port() {
  local retries=15
  local delay=2
  for i in $(seq 1 "$retries"); do
    if curl -s "http://$HOST:$PORT/state" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
  done
  return 1
}

render_json() {
  if command -v jq >/dev/null 2>&1; then
    jq .
  else
    cat
  fi
}

log "Building Docker image: $IMAGE_NAME"
docker build -t "$IMAGE_NAME" .

log "Starting container in background on port $PORT"
docker run -d --name "$CONTAINER_NAME" -p "$PORT:$PORT" "$IMAGE_NAME"

log "Waiting for API to become available..."
if ! wait_for_port; then
  log "ERROR: Container did not respond in time."
  exit 1
fi

log "Testing /reset endpoint"
RESET_RESPONSE=$(curl -s "http://$HOST:$PORT/reset")
echo "RESET RESPONSE:"
echo "$RESET_RESPONSE" | render_json

log "Testing /step endpoint with reroute_order action"
STEP_RESPONSE=$(curl -s -X POST "http://$HOST:$PORT/step" -H "Content-Type: application/json" -d '{"action_type":"reroute_order","target_id":"O1","value":1.0,"parameters":{"supplier_id":"Alt1"}}')
echo "STEP RESPONSE:"
echo "$STEP_RESPONSE" | render_json

log "Testing /state endpoint"
STATE_RESPONSE=$(curl -s "http://$HOST:$PORT/state")
echo "STATE RESPONSE:"
echo "$STATE_RESPONSE" | render_json

log "Docker validation completed successfully!"
