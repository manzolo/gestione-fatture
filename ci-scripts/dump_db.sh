#!/bin/bash

set -eo pipefail # Exit immediately if a command exits with a non-zero status.

echo "--- Verifying Logs table in Database ---"
psql -h localhost -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -AtF'|' -c "SELECT timestamp, level, source, request_id, api_key_id, message, details FROM logs ORDER BY timestamp DESC;" "${POSTGRES_DB}" || {
    echo "Error export logs."
    exit 1
}

echo "Database initialization complete."