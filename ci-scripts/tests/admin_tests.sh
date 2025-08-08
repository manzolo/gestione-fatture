#!/bin/bash
# ci-scripts/tests/admin_tests.sh

if ! declare -f run_curl > /dev/null; then
  . "$(dirname "$0")/utils.sh"
fi

if [ "${TEST_MODE}" = "protected" ]; then
  echo "=== Testing /admin/generate-api-key-hash endpoint ==="

  # Test 1: Generazione hash con chiave valida e descrizione
  echo "Test 1.1: Generating hash for a valid API Key with description..."
  VALID_KEY="aStrongTestApiKey12345" # Min_length 16 characters
  DESCRIPTION="TestKeyForCI"
  run_curl "GET" "/admin/generate-api-key-hash?api_key_plain_string=${VALID_KEY}&description=${DESCRIPTION}" "" "" "hashed_key" "200"
  # Commento: Test perfetto. Copre il caso di successo con tutti i parametri validi.

#   # Test 2: Generazione hash con chiave valida senza descrizione (optional field)
#   echo "Test 1.2: Generating hash for a valid API Key without description..."
#   run_curl "GET" "/admin/generate-api-key-hash?api_key_plain_string=${VALID_KEY}" "" "" "hashed_key" "200"
#   # Commento: Ottimo per verificare il comportamento dell'argomento opzionale `description`.

#   # Test 3: Chiave troppo corta (dovrebbe fallire con 422 Unprocessable Entity)
#   echo "Test 1.3: Attempting to generate hash with a TOO SHORT API Key (expecting 422 Unprocessable Entity)..."
#   SHORT_KEY="shortkey" # Less than min_length 16
#   # FastAPI genererà un 422 per errori di validazione Pydantic/Query parameters
#   if run_curl "GET" "/admin/generate-api-key-hash?api_key_plain_string=${SHORT_KEY}" "" "" "ensure this value has at least 16 characters" "422" "true"; then
#     echo "Test passed: Correctly rejected too short API Key."
#   else
#     echo "Test failed: Did NOT reject too short API Key as expected."
#     exit 1
#   fi
#   # Commento: Indispensabile per testare la validazione dei parametri (min_length=16).
#   # L'uso di `422` e il messaggio d'errore specifico (`"ensure this value has at least 16 characters"`)
#   # sono corretti per FastAPI.

#   # Test 4: Accesso non autorizzato (senza API Key admin)
#   echo "Test 1.4: Attempting to access without API Key (expecting 401 Unauthorized)..."
#   if run_curl "GET" "/admin/generate-api-key-hash?api_key_plain_string=${VALID_KEY}" "" "" "Missing API Key in Authorization header" "401" "true" ""; then
#     echo "Test passed: Correctly rejected request without API Key."
#   else
#     echo "Test failed: Did NOT reject request without API Key as expected."
#     exit 1
#   fi
else
  echo "Skipping /admin/generate-api-key-hash tests in unprotected mode (they require an API Key)."
fi