#!/bin/bash

# NON usare set -e
# set -e

BASE_URL="http://localhost:8080"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

success_count=0
fail_count=0

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           🧪 FRONTEND PROXY TESTS                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}⏳ Attendo che frontend sia pronto...${NC}"
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
  if curl -s -f "$BASE_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend è pronto!${NC}"
    break
  fi
  attempt=$((attempt + 1))
  echo -e "${YELLOW}   Tentativo $attempt/$max_attempts...${NC}"
  sleep 2
done

if [ $attempt -eq $max_attempts ]; then
  echo -e "${RED}❌ Timeout: Frontend non disponibile${NC}"
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

  if [[ "$url" == *"/download_invoice_zip/"* ]]; then
    local tmpfile=$(mktemp /tmp/zip_XXXXXX.zip)
    local http_code=$(curl -s -w "%{http_code}" -o "$tmpfile" "$url" 2>&1 | tail -n1)
    
    if [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
      echo -e "${GREEN}   ✓ Status: $http_code - $(du -h $tmpfile 2>/dev/null | cut -f1)${NC}"
      ((success_count++))
    else
      echo -e "${RED}   ✗ Status: $http_code${NC}"
      ((fail_count++))
    fi
    rm -f "$tmpfile" 2>/dev/null
    return 0
  fi

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

  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | sed '$d')

  if [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
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
echo -e "${CYAN}  SEZIONE: Gestione Clienti (Proxy)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

curl_check POST "$BASE_URL/api/clients" '{"nome":"Test","cognome":"User","codice_fiscale":"TSTUSR80A01H501X"}' "Crea cliente Test"
curl_check GET "$BASE_URL/api/clients/1" "" "Dettaglio cliente 1"
#curl_check PUT "$BASE_URL/api/clients/1" '{"nome":"Test","cognome":"Updated","codice_fiscale":"TSTUSR80A01H501X","indirizzo":"Via Test 42"}' "Aggiorna cliente"
curl_check PUT "$BASE_URL/api/clients/1" '{"nome":"Test","cognome":"Updated","indirizzo":"Via Test 42"}' "Aggiorna cliente (nome e indirizzo)"

echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  SEZIONE: Gestione Fatture (Proxy)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

curl_check POST "$BASE_URL/api/invoices" '{"data_fattura":"2025-01-15","data_pagamento":"2025-01-20","metodo_pagamento":"Bonifico","cliente_id":1,"numero_sedute":1,"inviata_sns":false}' "Crea fattura"
curl_check GET "$BASE_URL/api/invoices/1" "" "Dettaglio fattura"
curl_check PUT "$BASE_URL/api/invoices/1" '{"data_fattura":"2025-02-01","data_pagamento":"2025-02-05","metodo_pagamento":"Contanti","cliente_id":1,"numero_sedute":2,"inviata_sns":true}' "Aggiorna fattura"
curl_check GET "$BASE_URL/download_invoice_zip/1" "" "Download ZIP fattura"

echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  SEZIONE: Gestione Costi (Proxy)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

curl_check GET "$BASE_URL/api/costs" "" "Lista costi vuota"
curl_check POST "$BASE_URL/api/costs" '{"descrizione":"Abbonamento","anno_riferimento":2025,"data_pagamento":"2025-08-12","totale":49.99,"pagato":false}' "Crea costo"
curl_check GET "$BASE_URL/api/costs" "" "Lista costi"
curl_check GET "$BASE_URL/api/costs/1" "" "Dettaglio costo"
curl_check PUT "$BASE_URL/api/costs/1" '{"descrizione":"Abbonamento (agg)","anno_riferimento":2025,"data_pagamento":"2025-08-12","totale":59.99,"pagato":true}' "Aggiorna costo"
curl_check DELETE "$BASE_URL/api/costs/1" "" "Elimina costo"

echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                 📊 RIEPILOGO TEST FRONTEND                 ║${NC}"
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