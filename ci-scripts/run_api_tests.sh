#!/bin/bash
# ci-scripts/run_api_tests.sh
# Questo script viene eseguito all'interno del container invoice_backend.
# Richiede API_KEY_PLAIN come variabile d'ambiente.
# Accetta un argomento: "protected" o "unprotected".

set -eo pipefail # Exit immediately if a command exits with a non-zero status.

TEST_MODE="${1:-protected}" # Default a "protected" se non specificato
echo "Running API tests in ${TEST_MODE} mode..."
echo "Using API_KEY_PLAIN ${API_KEY_PLAIN}..."

# Source utilities
. "$(dirname "$0")/tests/utils.sh" # Usa '.' per fare lo sourcing, così le funzioni sono disponibili

# Esegui l'health check iniziale
perform_health_check

# Esporta le variabili per gli script successivi
export TEST_MODE
export AUTH_HEADER # Già impostato dalla funzione in utils.sh
export API_KEY_PLAIN # Utile se altri script ne hanno bisogno per API key sbagliate

# Esegui i gruppi di test
echo ""
echo "#######################################"
echo "### Starting Operations API Tests ###"
echo "#######################################"
. "$(dirname "$0")/tests/operations_tests.sh"

echo ""
echo "##########################################"
echo "### Starting Calculation API Tests ###"
echo "##########################################"
. "$(dirname "$0")/tests/calculation_tests.sh"

echo ""
echo "####################################"
echo "### Starting Admin API Tests ###"
echo "####################################"
. "$(dirname "$0")/tests/admin_tests.sh"

echo ""
echo "All API tests for ${TEST_MODE} mode completed successfully!"