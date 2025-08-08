#!/bin/bash
# ci-scripts/tests/operations_tests.sh

# Source utility functions if not already sourced by the main script
# This check prevents re-sourcing if the main script already did it.
if ! declare -f run_curl > /dev/null; then
  . "$(dirname "$0")/utils.sh"
fi

echo "Testing /operations/ endpoint (GET)"
run_curl "GET" "/operations/" "" "" "simple_sum_py" "200"

echo "Testing /operations/ endpoint (POST - Create New Operation)"
NEW_OP_ENGINE="python"
NEW_OP_NAME="test_operation_ci"
NEW_OPERATION_PAYLOAD="{\"engine\": \"${NEW_OP_ENGINE}\", \"operation\": \"${NEW_OP_NAME}\", \"description\": \"Test operation created by CI/CD\"}"
run_curl "POST" "/operations/" "-H \"Content-Type: application/json\"" "${NEW_OPERATION_PAYLOAD}" "${NEW_OP_NAME}" "201" # Expect 201 Created

echo "Testing /operations/ endpoint (GET - Verify New Operation)"
run_curl "GET" "/operations/" "" "" "${NEW_OP_NAME}" "200"

echo "Testing /operations/{engine}/{operation} endpoint (DELETE - Delete Test Operation)"
run_curl "DELETE" "/operations/${NEW_OP_ENGINE}/${NEW_OP_NAME}" "" "" "" "204" # Expect 204 No Content

echo "Testing /operations/ endpoint (GET after DELETE - Verify Deletion)"
echo "Verifying '${NEW_OP_NAME}' is no longer listed..."
VERIFY_DELETE_RESPONSE=$(eval "curl -s -X GET ${AUTH_HEADER} http://localhost:8000/operations/")
if echo "${VERIFY_DELETE_RESPONSE}" | grep -q "${NEW_OP_NAME}"; then
  echo "Test failed: '${NEW_OP_NAME}' still found after deletion."
  exit 1
else
  echo "Test passed: '${NEW_OP_NAME}' not found after deletion, as expected."
fi