#!/bin/bash

BASE_URL="http://localhost:8000/api"
HEALTH_URL="http://localhost:8000/health"

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Contatori risultati
success_count=0
fail_count=0

make restoredb

# Funzione per fare curl e stampare risultato colorato e aggiornare contatori
function curl_check() {
  local method=$1
  local url=$2
  local data=$3
  local save_file=$4

  echo -e "\n🔧 [$method] $url"

  if [[ "$method" == "GET" ]] && [[ -n "$save_file" ]]; then
    http_code=$(curl -s -w "%{http_code}" -o "$save_file" "$url")
    if [[ "$http_code" =~ ^2 ]]; then
      echo -e "${GREEN}Status: $http_code (SUCCESS)${NC}"
      echo "File salvato in: $save_file"
      ((success_count++))
    else
      echo -e "${RED}Status: $http_code (FAIL)${NC}"
      ((fail_count++))
    fi
    return
  fi

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

  # Qui controllo se è un errore ma con messaggio previsto
  if [[ "$http_code" == "400" ]] && [[ "$body" == *"Impossibile eliminare un cliente con fatture associate."* ]]; then
    color=$GREEN
    status_text="EXPECTED FAILURE"
    ((success_count++))  # Non considerarlo fallito
  elif [[ "$http_code" =~ ^2 ]]; then
    color=$GREEN
    status_text="SUCCESS"
    ((success_count++))
  else
    color=$RED
    status_text="FAIL"
    ((fail_count++))
  fi

  echo -e "${color}Status: $http_code ($status_text)${NC}"

  if [[ ${#body} -lt 1000 ]]; then
    echo -e "$body"
  else
    echo "[Output lungo omesso]"
  fi
}

# Test API base e health
curl_check GET "$HEALTH_URL"

# CLIENTI - GET lista vuota iniziale
curl_check GET "$BASE_URL/clients"

# CLIENTI - POST nuovo cliente
curl_check POST "$BASE_URL/clients" '{
  "nome": "Mario",
  "cognome": "Rossi",
  "codice_fiscale": "RSSMRA80A01H501Z",
  "indirizzo": "Via Roma 123",
  "citta": "Firenze",
  "cap": "50100"
}'

# CLIENTI - GET lista con cliente
curl_check GET "$BASE_URL/clients"

# CLIENTI - GET dettaglio cliente
curl_check GET "$BASE_URL/clients/1"

# CLIENTI - PUT aggiornamento cliente
curl_check PUT "$BASE_URL/clients/1" '{
  "nome": "Mario",
  "cognome": "Bianchi",
  "indirizzo": "Via Milano 45"
}'

# CLIENTI - GET dettaglio aggiornato
curl_check GET "$BASE_URL/clients/1"

# CLIENTI - DELETE cliente con fatture associate (dovrebbe fallire se fatture esistono)
# Prima creiamo una fattura associata a cliente 1 (usando endpoint fatture)
curl_check POST "$BASE_URL/invoices" '{
  "data_fattura": "2025-01-15",
  "data_pagamento": "2025-01-20",
  "metodo_pagamento": "Bonifico",
  "cliente_id": 1,
  "numero_sedute": 1,
  "inviata_sns": false
}'

# Proviamo a cancellare cliente 1 (dovrebbe dare errore)
curl_check DELETE "$BASE_URL/clients/1"

# CLIENTI - DELETE cliente senza fatture
# Prima creiamo cliente 2 senza fatture
curl_check POST "$BASE_URL/clients" '{
  "nome": "Luigi",
  "cognome": "Verdi",
  "codice_fiscale": "VRDLGU80A01H501Y"
}'

curl_check DELETE "$BASE_URL/clients/2"

# FATTURE - GET lista
curl_check GET "$BASE_URL/invoices"

# FATTURE - GET dettaglio fattura 1
curl_check GET "$BASE_URL/invoices/1"

# FATTURE - PUT aggiornamento fattura
curl_check PUT "$BASE_URL/invoices/1" '{
  "data_fattura": "2025-02-01",
  "data_pagamento": "2025-02-05",
  "metodo_pagamento": "Contanti",
  "cliente_id": 1,
  "numero_sedute": 2,
  "inviata_sns": true
}'

# FATTURE - GET dettaglio aggiornato
curl_check GET "$BASE_URL/invoices/1"

# FATTURE - DOWNLOAD fattura ZIP (verifica il download e il file)
curl_check GET "$BASE_URL/invoices/1/download"

# --- NUOVI TEST PER I COSTI ---
# COSTI - GET lista vuota iniziale
curl_check GET "$BASE_URL/costs"

# COSTI - POST nuovo costo
curl_check POST "$BASE_URL/costs" '{
  "descrizione": "Abbonamento software",
  "anno_riferimento": 2025,
  "data_pagamento": "2025-08-12",
  "totale": 49.99,
  "pagato": false
}'

# COSTI - GET lista con costo
curl_check GET "$BASE_URL/costs"

# COSTI - GET dettaglio costo
curl_check GET "$BASE_URL/costs/1"

# COSTI - PUT aggiornamento costo
curl_check PUT "$BASE_URL/costs/1" '{
  "descrizione": "Abbonamento software (aggiornato)",
  "anno_riferimento": 2025,
  "data_pagamento": "2025-08-12",
  "totale": 59.99,
  "pagato": true
}'

# COSTI - GET dettaglio aggiornato
curl_check GET "$BASE_URL/costs/1"

# COSTI - DELETE costo
curl_check DELETE "$BASE_URL/costs/1"

# COSTI - GET lista dopo eliminazione (dovrebbe essere di nuovo vuota)
curl_check GET "$BASE_URL/costs"
# --- FINE NUOVI TEST ---


# Riepilogo finale
echo -e "\n===== RIEPILOGO TEST ====="
echo -e "${GREEN}Successi: $success_count${NC}"
echo -e "${RED}Fallimenti: $fail_count${NC}"

if ((fail_count > 0)); then
  exit 1
else
  exit 0
fi
