#!/bin/bash

BASE_URL="http://localhost:8080"  # Cambia con la porta del tuo frontend
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

success_count=0
fail_count=0

make restoredb

function curl_check() {
  local method=$1
  local url=$2
  local data=$3

  echo -e "\n🔧 [$method] $url"

  # Se è un download ZIP (endpoint contenente /download_invoice_zip/)
  if [[ "$url" == *"/download_invoice_zip/"* ]]; then
    # Salva output in file temporaneo
    tmpfile=$(mktemp /tmp/download_zip_XXXXXX.zip)
    if [[ "$method" == "GET" ]]; then
      http_code=$(curl -s -w "%{http_code}" -o "$tmpfile" "$url")
    else
      echo "Metodo non supportato per download zip"
      rm "$tmpfile"
      return 1
    fi

    if [[ "$http_code" =~ ^2 ]]; then
      color=$GREEN
      status_text="SUCCESS"
      ((success_count++))
      echo -e "${color}Status: $http_code ($status_text)${NC}"
      echo -e "File scaricato correttamente: $tmpfile"
    else
      color=$RED
      status_text="FAIL"
      ((fail_count++))
      echo -e "${color}Status: $http_code ($status_text)${NC}"
      # Mostra eventualmente contenuto di errore testuale se presente (non binario)
      head -c 500 "$tmpfile" | cat
    fi
    # opzionale: rimuovere file dopo test
    rm "$tmpfile"
  else
    # comportamento normale per le altre chiamate
    if [[ "$method" == "GET" ]]; then
      response=$(curl -s -w "%{http_code}" "$url")
    elif [[ "$method" == "DELETE" ]]; then
      response=$(curl -s -X DELETE -w "%{http_code}" "$url")
    elif [[ "$method" == "POST" ]]; then
      response=$(curl -s -X POST -H "Content-Type: application/json" -d "$data" -w "%{http_code}" "$url")
    elif [[ "$method" == "PUT" ]]; then
      response=$(curl -s -X PUT -H "Content-Type: application/json" -d "$data" -w "%{http_code}" "$url")
    else
      echo "Metodo HTTP non supportato"
      return 1
    fi

    http_code="${response: -3}"
    body="${response:0:${#response}-3}"

    if [[ "$http_code" =~ ^2 ]]; then
      color=$GREEN
      status_text="SUCCESS"
      ((success_count++))
    else
      color=$RED
      status_text="FAIL"
      ((fail_count++))
    fi

    echo -e "${color}Status: $http_code ($status_text)${NC}"
    echo -e "$body"
  fi
}


# Test endpoint proxy frontend

# Aggiungi cliente (proxy)
curl_check POST "$BASE_URL/api/clients" '{
  "nome": "Test",
  "cognome": "User",
  "codice_fiscale": "TSTUSR80A01H501X"
}'

# Dettaglio cliente 1 (proxy)
curl_check GET "$BASE_URL/api/clients/1"

# Aggiorna cliente 1 (proxy)
curl_check PUT "$BASE_URL/api/clients/1" '{
  "nome": "Test",
  "cognome": "User Updated",
  "indirizzo": "Via Test 42"
}'

# Crea fattura per cliente 1 (proxy)
curl_check POST "$BASE_URL/api/invoices" '{
  "data_fattura": "2025-01-15",
  "data_pagamento": "2025-01-20",
  "metodo_pagamento": "Bonifico",
  "cliente_id": 1,
  "numero_sedute": 1,
  "inviata_sns": false
}'

# Cancellare cliente 2 senza fatture (prima crealo)
curl_check POST "$BASE_URL/api/clients" '{
  "nome": "Client",
  "cognome": "NoInvoices",
  "codice_fiscale": "CLNNVC80A01H501Z"
}'

# Dettaglio fattura 1
curl_check GET "$BASE_URL/api/invoices/1"

# Aggiorna fattura 1
curl_check PUT "$BASE_URL/api/invoices/1" '{
  "data_fattura": "2025-02-01",
  "data_pagamento": "2025-02-05",
  "metodo_pagamento": "Contanti",
  "cliente_id": 1,
  "numero_sedute": 2,
  "inviata_sns": true
}'

# Download ZIP fattura 1 (qui verifichiamo solo che risponda correttamente)
curl_check GET "$BASE_URL/download_invoice_zip/1"

# --- NUOVI TEST PER I COSTI FRONTEND ---
# COSTI - GET lista vuota iniziale (proxy)
curl_check GET "$BASE_URL/api/costs"

# COSTI - POST nuovo costo (proxy)
curl_check POST "$BASE_URL/api/costs" '{
  "descrizione": "Abbonamento software",
  "anno_riferimento": 2025,
  "data_pagamento": "2025-08-12",
  "totale": 49.99,
  "pagato": false
}'

# COSTI - GET lista con costo (proxy)
curl_check GET "$BASE_URL/api/costs"

# COSTI - GET dettaglio costo (proxy)
curl_check GET "$BASE_URL/api/costs/1"

# COSTI - PUT aggiornamento costo (proxy)
curl_check PUT "$BASE_URL/api/costs/1" '{
  "descrizione": "Abbonamento software (aggiornato)",
  "anno_riferimento": 2025,
  "data_pagamento": "2025-08-12",
  "totale": 59.99,
  "pagato": true
}'

# COSTI - GET dettaglio aggiornato (proxy)
curl_check GET "$BASE_URL/api/costs/1"

# COSTI - DELETE costo (proxy)
curl_check DELETE "$BASE_URL/api/costs/1"

# COSTI - GET lista dopo eliminazione (proxy)
curl_check GET "$BASE_URL/api/costs"
# --- FINE NUOVI TEST ---

echo -e "\n===== RIEPILOGO TEST ====="
echo -e "${GREEN}Successi: $success_count${NC}"
echo -e "${RED}Fallimenti: $fail_count${NC}"

if ((fail_count > 0)); then
  exit 1
else
  exit 0
fi
