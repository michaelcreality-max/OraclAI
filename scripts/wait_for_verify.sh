#!/usr/bin/env bash
# Re-run ./scripts/verify.sh every INTERVAL seconds until it passes (Ctrl+C to stop).
# Use while other agents or editors are applying changes; exit 0 when the project is green.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
INTERVAL="${VERIFY_INTERVAL:-5}"
ARGS=("$@")
if [[ ${#ARGS[@]} -eq 0 ]]; then
  ARGS=()
fi
echo "[wait_for_verify] interval=${INTERVAL}s  root=$ROOT"
while true; do
  if "$ROOT/scripts/verify.sh" "${ARGS[@]}"; then
    echo "[wait_for_verify] verify passed — exiting 0"
    exit 0
  fi
  echo "[wait_for_verify] verify failed — retrying in ${INTERVAL}s …"
  sleep "$INTERVAL"
done
