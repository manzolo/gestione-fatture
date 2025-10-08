#!/bin/bash

# NON usare set -e perché vogliamo gestire gli errori manualmente
# set -e

BASE_URL="http://localhost:8000/api"
HEALTH_URL="http://localhost:8000/health"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

success_count=0
fail_count=0

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           🧪 BACKEND API TESTS                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}⏳ Attendo che i servizi siano pronti...${NC}"
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
  if curl -s -f "$HEALTH_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend è pronto!${NC}"
    break
  fi
  attempt=$((attempt + 1))
  echo -e "${YELLOW}   Tentativo $attempt/$max_attempts...${NC}"
  sleep 2
done

if [ $attempt -eq $max_attempts ]; then
  echo -e "${RED}❌ Timeout: Backend non disponibile${NC}"
  exit 1
fi

sleep 2

function curl_check() {
  local method=$1
  local url=$2
  local data=$3
  local description=$4

  if [ -n "$description" ]; then
    echo -e "\n${BLUE}🔧 $description${NC}"
  fi
  echo -e "${YELLOW}   [$method] $url${NC}"

  local response
  local http_code
  local body

  if [[ "$method" == "GET" ]]; then
    response=$(curl -s -w "\n%{http_code}" "$url" 2>&1) || true
  elif [[ "$method" == "DELETE" ]]; then
    response=$(curl -s -X DELETE -w "\n%{http_code}" "$url" 2>&1) || true
  elif [[ "$method" == "POST" ]]; then
    response=$(curl -s -X POST -H "Content-Type: application/json" -d "$data" -w "\n%{http_code}" "$url" 2>&1) || true
  elif [[ "$method" == "PUT" ]]; then
    response=$(curl -s -X PUT -H "Content-Type: application/json" -d "$data" -w "\n%{http_code}" "$url" 2>&1) || true
  else
    echo -e "${RED}   ✗ Metodo non supportato${NC}"
    ((fail_count++))
    return 0
  fi

  # Estrai il codice HTTP (ultima riga)
  http_code=$(echo "$response" | tail -n1)
  # Estrai il body (tutto tranne l'ultima riga)
  body=$(echo "$response" | sed '$d')

  if [[ "$http_code" == "400" ]] && [[ "$body" == *"fatture associate"* ]]; then
    echo -e "${GREEN}   ✓ Status: $http_code (EXPECTED)${NC}"
    ((success_count++))
  elif [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
    echo -e "${GREEN}   ✓ Status: $http_code${NC}"
    ((success_count++))
  else
    echo -e "${RED}   ✗ Status: $http_code${NC}"
    ((fail_count++))
  fi

  if [[ ${#body} -lt 500 ]] && [[ -n "$body" ]]; then
    echo -e "   Response: ${body:0:200}"
  fi
}

echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  SEZIONE: Health Check${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
curl_check GET "$HEALTH_URL" "" "Health Check"

echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  SEZIONE: Gestione Clienti${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

curl_check GET "$BASE_URL/clients" "" "Lista clienti vuota"
curl_check POST "$BASE_URL/clients" '{"nome":"Maria","cognome":"Rossi","codice_fiscale":"RSSMRA81A01H501Z","indirizzo":"Via Roma 123","citta":"Firenze","cap":"50100"}' "Crea cliente Mario Rossi"
curl_check GET "$BASE_URL/clients" "" "Lista clienti con Mario"
curl_check GET "$BASE_URL/clients/1" "" "Dettaglio cliente 1"
curl_check PUT "$BASE_URL/clients/1" '{"nome":"Mario","cognome":"Bianchi","indirizzo":"Via Milano 45"}' "Aggiorna cliente (nome e indirizzo)"
curl_check GET "$BASE_URL/clients/1" "" "Verifica aggiornamento"

echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  SEZIONE: Gestione Fatture${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

curl_check POST "$BASE_URL/invoices" '{"data_fattura":"2025-01-15","data_pagamento":"2025-01-20","metodo_pagamento":"Bonifico","cliente_id":1,"numero_sedute":1,"inviata_sns":false}' "Crea fattura"
curl_check DELETE "$BASE_URL/clients/1" "" "Elimina cliente con fatture (deve fallire)"
curl_check POST "$BASE_URL/clients" '{"nome":"Luigi","cognome":"Verdi","codice_fiscale":"VRDLGU80A01H501Y"}' "Crea cliente Luigi"
curl_check DELETE "$BASE_URL/clients/2" "" "Elimina cliente senza fatture"
curl_check GET "$BASE_URL/invoices" "" "Lista fatture"
curl_check GET "$BASE_URL/invoices/1" "" "Dettaglio fattura"
curl_check PUT "$BASE_URL/invoices/1" '{"data_fattura":"2025-02-01","data_pagamento":"2025-02-05","metodo_pagamento":"Contanti","cliente_id":1,"numero_sedute":2,"inviata_sns":true}' "Aggiorna fattura"

echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  SEZIONE: Gestione Costi${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

curl_check GET "$BASE_URL/costs" "" "Lista costi vuota"
curl_check POST "$BASE_URL/costs" '{"descrizione":"Abbonamento software","anno_riferimento":2025,"data_pagamento":"2025-08-12","totale":49.99,"pagato":false}' "Crea costo"
curl_check GET "$BASE_URL/costs" "" "Lista costi con abbonamento"
curl_check GET "$BASE_URL/costs/1" "" "Dettaglio costo"
curl_check PUT "$BASE_URL/costs/1" '{"descrizione":"Abbonamento (aggiornato)","anno_riferimento":2025,"data_pagamento":"2025-08-12","totale":59.99,"pagato":true}' "Aggiorna costo"
curl_check GET "$BASE_URL/costs/1" "" "Verifica aggiornamento costo"
curl_check DELETE "$BASE_URL/costs/1" "" "Elimina costo"
curl_check GET "$BASE_URL/costs" "" "Lista costi vuota dopo delete"

echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                 📊 RIEPILOGO TEST BACKEND                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo -e "\n${GREEN}  ✓ Successi: $success_count${NC}"
echo -e "${RED}  ✗ Falliti:  $fail_count${NC}"
echo ""

if ((fail_count > 0)); then
  echo -e "${RED}❌ ALCUNI TEST FALLITI${NC}\n"
  exit 1
else
  echo -e "${GREEN}✅ TUTTI I TEST PASSATI${NC}\n"
  exit 0
fi