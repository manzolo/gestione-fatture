#!/bin/bash
# ci-scripts/tests/calculation_tests.sh

if ! declare -f run_curl > /dev/null; then
  . "$(dirname "$0")/utils.sh"
fi

# Variabili per i test di calcolo
REQUEST_ID=""
DELETE_TEST_REQUEST_ID=""

echo "Testing /calculate endpoint (POST) for new request"
CALCULATE_RESPONSE=$(eval "curl -s -f \
  -X POST \
  -H \"Content-Type: application/json\" \
  ${AUTH_HEADER} \
  -d '{\"engine\": \"python\", \"operation\": \"simple_sum_py\", \"data\": {\"value1\": 10, \"value2\": 20}, \"email\": \"test@example.com\"}' \
  http://localhost:8000/calculate")

echo "Calculation response: ${CALCULATE_RESPONSE}"
REQUEST_ID=$(echo "${CALCULATE_RESPONSE}" | grep -oP '"request_id":\s*"\K[^"]+')

if [ -z "${REQUEST_ID}" ]; then
  echo "Test failed: Could not extract request_id from /calculate response."
  exit 1
fi
echo "Extracted request_id: ${REQUEST_ID}"
echo "Calculation endpoint (POST) test passed."

echo "Testing /status/{request_id} endpoint (GET) - Initial PENDING state"
# Qui ci aspettiamo PENDING. Se è già COMPLETED, significa che il worker è troppo veloce.
# Se è COMPLETED, il test del 200 per IN_PROGRESS fallirà e passerà al 409.
if run_curl "GET" "/status/${REQUEST_ID}" "" "" "PENDING" "200" "true"; then
  echo "Test passed: Request correctly handled PENDING transition (200 OK)."
else
  if run_curl "GET" "/status/${REQUEST_ID}" "" "" "COMPLETED" "200"; then
    echo "Test passed: Request correctly handled COMPLETED transition (200 OK)."
  else
    echo "Test failed: Request not in PENDING|COMPLETED transition."
    exit 1
  fi
fi

echo "--- Testing /status/processing/{request_id}/{worker} endpoint (POST) ---"
WORKER_NAME="python_worker_instance_1"
# La prima chiamata cerca di marcare come IN_PROGRESS.
# Accetta sia 200 OK (se lo stato è PENDING) sia 409 Conflict (se lo stato è già cambiato, es. COMPLETED)
# Modifichiamo la stringa attesa: "marked as IN_PROGRESS" per il 200, O "Cannot transition to IN_PROGRESS" per il 409
if run_curl "POST" "/status/processing/${REQUEST_ID}/${WORKER_NAME}" "" "" "marked as IN_PROGRESS|Cannot transition to IN_PROGRESS" "200|409" "true"; then
  echo "Test passed: Request correctly handled IN_PROGRESS transition (200 OK) or was already completed (409 Conflict)."
else
  echo "Test failed: Unexpected response for IN_PROGRESS update."
  exit 1
fi

echo "--- Verifying /status/{request_id} endpoint (GET after IN_PROGRESS/Conflict logic) ---"

run_curl "GET" "/status/${REQUEST_ID}" "" "" "IN_PROGRESS|COMPLETED" "200"

echo "Test Endpoint /results (POST) - Simulating Worker Completion"
WORKER_RESULT_PAYLOAD="{\"request_id\": \"${REQUEST_ID}\", \"status\": \"COMPLETED\", \"engine\": \"python\", \"operation\": \"simple_sum_py\", \"result\": {\"value\": 30, \"message\": \"Sum completed successfully\"}}"
run_curl "POST" "/results" "-H \"Content-Type: application/json\"" "${WORKER_RESULT_PAYLOAD}" "Result updated successfully" "200"

echo "Testing /status/{request_id} endpoint (GET after worker update)"
run_curl "GET" "/status/${REQUEST_ID}" "" "" "COMPLETED" "200"


## Combined Test: Create, Get Status, and Delete a Request (via /status)

echo "Combined Test: Create, Get Status, and Delete a Request (via /status)"

# 1. Crea una nuova richiesta
echo "1. Creating a new request for deletion test..."
DELETE_TEST_CALCULATE_RESPONSE=$(eval "curl -s -f \
  -X POST \
  -H \"Content-Type: application/json\" \
  ${AUTH_HEADER} \
  -d '{\"engine\": \"python\", \"operation\": \"simple_sum_py\", \"data\": {\"value1\": 1, \"value2\": 1}, \"email\": \"delete_test@example.com\"}' \
  http://localhost:8000/calculate")

DELETE_TEST_REQUEST_ID=$(echo "${DELETE_TEST_CALCULATE_RESPONSE}" | grep -oP '"request_id":\s*"\K[^"]+')

if [ -z "${DELETE_TEST_REQUEST_ID}" ]; then
  echo "Combined Test failed: Could not extract request_id for deletion test."
  exit 1
fi
echo "Created request_id for deletion test: ${DELETE_TEST_REQUEST_ID}"

echo "2. Getting status of the request for deletion test..."
run_curl "GET" "/status/${DELETE_TEST_REQUEST_ID}" "" "" "PENDING|COMPLETED" "200"

echo "--- Testing /status/processing/{request_id}/{worker} for deletion test request ---"
WORKER_NAME_DEL="python_worker_instance_2"
if run_curl "POST" "/status/processing/${DELETE_TEST_REQUEST_ID}/${WORKER_NAME_DEL}" "" "" "IN_PROGRESS|COMPLETED" "200|409" "true"; then
  echo "Test passed: Deletion test request correctly handled IN_PROGRESS transition (200 OK) or was already completed (409 Conflict)."
else
  echo "Test failed: Unexpected response for deletion test IN_PROGRESS update."
  exit 1
fi

echo "--- Verifying /status/{request_id} endpoint (GET after IN_PROGRESS/Conflict logic for deletion test) ---"
run_curl "GET" "/status/${DELETE_TEST_REQUEST_ID}" "" "" "IN_PROGRESS|COMPLETED" "200"


echo "3. Deleting the request via /status/${DELETE_TEST_REQUEST_ID} (DELETE)..."
run_curl "DELETE" "/status/${DELETE_TEST_REQUEST_ID}" "" "" "deleted successfully" "200"

echo "4. Verifying request ${DELETE_TEST_REQUEST_ID} is deleted (expecting 404 Not Found)..."
if run_curl "GET" "/status/${DELETE_TEST_REQUEST_ID}" "" "" "Request ID not found" "404" "true"; then
  echo "Combined Test passed: Request ${DELETE_TEST_REQUEST_ID} successfully deleted and not found."
else
  echo "Test failed: Request ${DELETE_TEST_REQUEST_ID} still found or deletion failed."
  exit 1
fi