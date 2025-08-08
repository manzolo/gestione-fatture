#!/bin/bash
# ci-scripts/tests/utils.sh

# Global variable for authorization header
AUTH_HEADER=""

# Function to perform initial health check
perform_health_check() {
  echo "Waiting for backend to be ready..."
  for i in $(seq 1 30); do
    if curl -s -f http://localhost:8000/health; then
      echo "backend is up!"
      break
    fi
    echo "Waiting for backend ($i/30)..."
    sleep 5
  done
  curl -s -f http://localhost:8000/health || { echo "Backend did not start in time\!"; exit 1; }
  echo "/health check passed."
}

# Function to execute curl commands for API tests
# Args: METHOD, URL, HEADERS, DATA, EXPECTED_STRING, EXPECTED_HTTP_CODE, ALLOW_FAILURE, CUSTOM_AUTH_HEADER
run_curl() {
  local METHOD="${1}"
  local URL="${2}"
  local HEADERS="${3:-}" # Optional, for Content-Type etc.
  local DATA="${4:-}"    # Optional, for -d
  local EXPECTED_STRING="${5:-}" # Optional, expected string in response (supports | for OR)
  local EXPECTED_HTTP_CODE="${6:-200}" # Optional, expected HTTP code (supports | for OR, e.g., "200|409")
  local ALLOW_FAILURE="${7:-false}" # Allow curl to fail without exiting script if true
  local CUSTOM_AUTH_HEADER="${8:-$AUTH_HEADER}" # Allows using a different auth header than global one

  # To capture both body and HTTP code
  local COMMAND="curl -s -o /tmp/curl_output.txt -w '%{http_code}' -X ${METHOD} ${HEADERS} ${DATA:+ -d '${DATA}'} ${CUSTOM_AUTH_HEADER} http://localhost:8000${URL}"
  
  # Log command without full payload for readability, ensuring proper quoting
  local LOG_DATA=""
  if [ -n "${DATA}" ]; then
    LOG_DATA="-d '...'"
  fi
  echo "Executing: curl -s -X ${METHOD} ${HEADERS} ${LOG_DATA} ${CUSTOM_AUTH_HEADER} http://localhost:8000${URL}"

  HTTP_CODE=$(eval "${COMMAND}") # Use eval to expand CUSTOM_AUTH_HEADER correctly
  RESPONSE=$(cat /tmp/curl_output.txt)
  
  echo "Response HTTP Code: ${HTTP_CODE}"
  echo "Response Body: ${RESPONSE}"

  # --- MODIFICA QUI PER LA GESTIONE DELL'OR NEI CODICI HTTP ---
  local HTTP_CODE_MATCH=false
  # Se EXPECTED_HTTP_CODE contiene un '|', significa che è un elenco di codici OR
  if [[ "${EXPECTED_HTTP_CODE}" == *"|"* ]]; then
    IFS='|' read -r -a expected_codes_array <<< "${EXPECTED_HTTP_CODE}"
    for code in "${expected_codes_array[@]}"; do
      if [ "${HTTP_CODE}" = "${code}" ]; then
        HTTP_CODE_MATCH=true
        break
      fi
    done
  else
    # Altrimenti, è un singolo codice atteso
    if [ "${HTTP_CODE}" = "${EXPECTED_HTTP_CODE}" ]; then
      HTTP_CODE_MATCH=true
    fi
  fi

  if [ "${HTTP_CODE_MATCH}" = "false" ]; then
    if [ "${ALLOW_FAILURE}" = "true" ]; then
      echo "Test warning: Expected HTTP code(s) '${EXPECTED_HTTP_CODE}', but got ${HTTP_CODE} for ${URL}. (Allowed failure)"
      return 1 # Return an error code but don't terminate the script
    else
      echo "Test failed: Expected HTTP code(s) '${EXPECTED_HTTP_CODE}', but got ${HTTP_CODE} for ${URL}."
      exit 1
    fi
  fi

  if [ -n "${EXPECTED_STRING}" ]; then
    if echo "${RESPONSE}" | grep -Eq "${EXPECTED_STRING}"; then # <--- AGGIUNTO -E QUI
      echo "Test passed: Found '${EXPECTED_STRING}' in response."
      return 0
    else
      if [ "${ALLOW_FAILURE}" = "true" ]; then
        echo "Test warning: '${EXPECTED_STRING}' not found in response for ${URL}. (Allowed failure)"
        return 1
      else
        echo "Test failed: '${EXPECTED_STRING}' not found in response for ${URL}."
        echo "Full response: ${RESPONSE}"
        exit 1
      fi
    fi
  else
    echo "Test passed (HTTP ${HTTP_CODE} received)."
    return 0
  fi
}