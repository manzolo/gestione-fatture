#!/bin/bash

set -eo pipefail # Exit immediately if a command exits with a non-zero status.

echo "Waiting for database to be ready..."

for i in $(seq 1 30); do
  # Use double quotes around variables to handle potential spaces or special characters,
  # though for these specific variables, it's mostly for good practice.
  if pg_isready -h localhost -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"; then
    echo "Database is ready!"
    break
  fi
  echo "Waiting for database... ($i/30)"
  sleep 2
done

echo "Initializing database schema and data..."
echo "API_KEY_HASH_BASE64 received: ${API_KEY_HASH_BASE64}"

# Decode the Base64 back to the original bcrypt hash
API_KEY_HASH=$(echo "${API_KEY_HASH_BASE64}" | base64 -d)
echo "Decoded API_KEY_HASH: ${API_KEY_HASH}"

# Verify the hash format
if [[ ! "${API_KEY_HASH}" =~ ^\$2[aby]\$[0-9]+\$ ]]; then
  echo "ERROR: Invalid bcrypt hash format!"
  exit 1
fi

psql -h localhost -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "
  CREATE TABLE IF NOT EXISTS api_keys (
      id SERIAL PRIMARY KEY,
      key_hash VARCHAR(255) NOT NULL UNIQUE,
      description VARCHAR(255),
      is_active BOOLEAN DEFAULT TRUE,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  
  -- Use dollar-quoting to properly handle the hash
  INSERT INTO api_keys (key_hash, description, is_active)
  VALUES (E'${API_KEY_HASH}', 'Test API Key from CI/CD', TRUE)
  ON CONFLICT (key_hash) DO NOTHING;

  -- ... rest of your SQL ...
"

echo "--- Verifying API Keys in Database ---"
psql -h localhost -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "
  SELECT id, 
         SUBSTRING(key_hash, 1, 10) || '...' || SUBSTRING(key_hash, LENGTH(key_hash)-9) AS key_hash_preview, 
         is_active, 
         description 
  FROM api_keys;"

echo "Database initialization complete."