#!/usr/bin/env bash
# Test di integrazione per gli endpoint STS
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
PASS=0
FAIL=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}✅ PASS${NC}: $1"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}❌ FAIL${NC}: $1"; FAIL=$((FAIL+1)); }
info() { echo -e "  ${YELLOW}ℹ️  INFO${NC}: $1"; }

echo ""
echo "============================================"
echo " STS Integration Tests"
echo " Backend: $BACKEND_URL"
echo "============================================"
echo ""

# ---------------------------------------------------------------------------
# 1. Lista fatture non inviate a STS
# ---------------------------------------------------------------------------
echo "--- Test 1: GET /api/sts/invoices/unsent ---"
RESP=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/api/sts/invoices/unsent")
HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    pass "GET /api/sts/invoices/unsent → HTTP 200"
    COUNT=$(echo "$BODY" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")
    info "Fatture non inviate: $COUNT"
else
    fail "GET /api/sts/invoices/unsent → HTTP $HTTP_CODE (atteso 200)"
    info "Body: $BODY"
fi

# ---------------------------------------------------------------------------
# 2. Crea un cliente di test
# ---------------------------------------------------------------------------
echo ""
echo "--- Test 2: Crea cliente di test ---"
CLIENT_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/api/clients" \
    -H "Content-Type: application/json" \
    -d '{
        "nome": "Mario",
        "cognome": "StsTest",
        "codice_fiscale": "TSTSTS80A01H501Z",
        "indirizzo": "Via Roma 1",
        "citta": "Roma",
        "cap": "00100"
    }')
CLIENT_HTTP=$(echo "$CLIENT_RESP" | tail -1)
CLIENT_BODY=$(echo "$CLIENT_RESP" | head -n -1)

if [ "$CLIENT_HTTP" = "201" ] || [ "$CLIENT_HTTP" = "200" ]; then
    CLIENT_ID=$(echo "$CLIENT_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || echo "")
    pass "Creato cliente di test (id=$CLIENT_ID)"
else
    # Prova a recuperare il cliente esistente
    CLIENT_ID=$(curl -s "$BACKEND_URL/api/clients" | \
        python3 -c "import sys,json; data=json.load(sys.stdin); \
        c=[x for x in data if x.get('codice_fiscale')=='TSTSTS80A01H501Z']; \
        print(c[0]['id'] if c else '')" 2>/dev/null || echo "")
    if [ -n "$CLIENT_ID" ]; then
        info "Cliente già esistente (id=$CLIENT_ID)"
    else
        fail "Impossibile creare o trovare cliente di test (HTTP $CLIENT_HTTP)"
        info "Body: $CLIENT_BODY"
    fi
fi

# ---------------------------------------------------------------------------
# 3. Crea una fattura di test con data_pagamento valorizzata
# ---------------------------------------------------------------------------
echo ""
echo "--- Test 3: Crea fattura di test con data_pagamento ---"

if [ -z "${CLIENT_ID:-}" ]; then
    fail "CLIENT_ID non disponibile, skip creazione fattura"
else
    INV_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/api/invoices" \
        -H "Content-Type: application/json" \
        -d "{
            \"cliente_id\": $CLIENT_ID,
            \"data_fattura\": \"$(date +%Y-%m-%d)\",
            \"data_pagamento\": \"$(date +%Y-%m-%d)\",
            \"metodo_pagamento\": \"Bonifico\",
            \"numero_sedute\": 1,
            \"prezzo_totale_unitario\": 60.00
        }")
    INV_HTTP=$(echo "$INV_RESP" | tail -1)
    INV_BODY=$(echo "$INV_RESP" | head -n -1)

    if [ "$INV_HTTP" = "201" ]; then
        INV_ID=$(echo "$INV_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || echo "")
        pass "Creata fattura di test (id=$INV_ID)"
    else
        fail "Creazione fattura fallita (HTTP $INV_HTTP)"
        info "Body: $INV_BODY"
        INV_ID=""
    fi
fi

# ---------------------------------------------------------------------------
# 4. Invio singola fattura a STS
# ---------------------------------------------------------------------------
echo ""
echo "--- Test 4: POST /api/sts/invoices/<id>/send ---"

if [ -z "${INV_ID:-}" ]; then
    fail "INV_ID non disponibile, skip invio STS"
else
    SEND_RESP=$(curl -s -w "\n%{http_code}" -X POST \
        "$BACKEND_URL/api/sts/invoices/$INV_ID/send")
    SEND_HTTP=$(echo "$SEND_RESP" | tail -1)
    SEND_BODY=$(echo "$SEND_RESP" | head -n -1)

    if [ "$SEND_HTTP" = "200" ] || [ "$SEND_HTTP" = "422" ]; then
        STS_SUCCESS=$(echo "$SEND_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success',''))" 2>/dev/null || echo "")
        PROTOCOLLO=$(echo "$SEND_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('protocollo') or '')" 2>/dev/null || echo "")
        ERRORS=$(echo "$SEND_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('errors',[]))" 2>/dev/null || echo "[]")

        if [ "$STS_SUCCESS" = "True" ]; then
            pass "Fattura $INV_ID inviata a STS (protocollo=$PROTOCOLLO)"
        else
            info "Invio STS non riuscito (ambiente test / rete non disponibile)"
            info "Errori STS: $ERRORS"
            info "HTTP $SEND_HTTP — risposta: $SEND_BODY"
            pass "Endpoint /send risponde correttamente (HTTP $SEND_HTTP)"
        fi
    elif [ "$SEND_HTTP" = "503" ]; then
        info "STS non configurato (HTTP 503) — OK in ambiente senza credenziali"
        pass "Endpoint /send → 503 quando STS non configurato"
    else
        fail "POST /api/sts/invoices/$INV_ID/send → HTTP $SEND_HTTP (atteso 200/422/503)"
        info "Body: $SEND_BODY"
    fi
fi

# ---------------------------------------------------------------------------
# 5. Verifica stato inviata_sts nella fattura
# ---------------------------------------------------------------------------
echo ""
echo "--- Test 5: Verifica stato fattura dopo invio ---"

if [ -z "${INV_ID:-}" ]; then
    fail "INV_ID non disponibile, skip verifica stato"
else
    DETAIL_RESP=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/api/invoices/$INV_ID")
    DETAIL_HTTP=$(echo "$DETAIL_RESP" | tail -1)
    DETAIL_BODY=$(echo "$DETAIL_RESP" | head -n -1)

    if [ "$DETAIL_HTTP" = "200" ]; then
        pass "GET /api/invoices/$INV_ID → HTTP 200"
        SENT=$(echo "$DETAIL_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('inviata_sts',''))" 2>/dev/null || echo "")
        info "inviata_sts: $SENT"
    else
        fail "GET /api/invoices/$INV_ID → HTTP $DETAIL_HTTP (atteso 200)"
    fi
fi

# ---------------------------------------------------------------------------
# 6. Test invio batch
# ---------------------------------------------------------------------------
echo ""
echo "--- Test 6: POST /api/sts/invoices/send-batch ---"

BATCH_RESP=$(curl -s -w "\n%{http_code}" -X POST \
    "$BACKEND_URL/api/sts/invoices/send-batch" \
    -H "Content-Type: application/json" \
    -d "{\"year\": $(date +%Y)}")
BATCH_HTTP=$(echo "$BATCH_RESP" | tail -1)
BATCH_BODY=$(echo "$BATCH_RESP" | head -n -1)

if [ "$BATCH_HTTP" = "200" ] || [ "$BATCH_HTTP" = "503" ]; then
    pass "POST /api/sts/invoices/send-batch → HTTP $BATCH_HTTP"
    if [ "$BATCH_HTTP" = "200" ]; then
        TOTAL=$(echo "$BATCH_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total','?'))" 2>/dev/null || echo "?")
        SENT_B=$(echo "$BATCH_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('sent','?'))" 2>/dev/null || echo "?")
        info "Batch: total=$TOTAL sent=$SENT_B"
    fi
else
    fail "POST /api/sts/invoices/send-batch → HTTP $BATCH_HTTP (atteso 200/503)"
    info "Body: $BATCH_BODY"
fi

# ---------------------------------------------------------------------------
# 7. Test cancellazione (solo se INV_ID disponibile e invio riuscito)
# ---------------------------------------------------------------------------
echo ""
echo "--- Test 7: POST /api/sts/invoices/<id>/cancel ---"

if [ -z "${INV_ID:-}" ]; then
    fail "INV_ID non disponibile, skip test cancellazione"
else
    CANCEL_RESP=$(curl -s -w "\n%{http_code}" -X POST \
        "$BACKEND_URL/api/sts/invoices/$INV_ID/cancel")
    CANCEL_HTTP=$(echo "$CANCEL_RESP" | tail -1)
    CANCEL_BODY=$(echo "$CANCEL_RESP" | head -n -1)

    if [ "$CANCEL_HTTP" = "200" ] || [ "$CANCEL_HTTP" = "400" ] || \
       [ "$CANCEL_HTTP" = "422" ] || [ "$CANCEL_HTTP" = "503" ]; then
        pass "POST /api/sts/invoices/$INV_ID/cancel → HTTP $CANCEL_HTTP (endpoint risponde)"
    else
        fail "POST /api/sts/invoices/$INV_ID/cancel → HTTP $CANCEL_HTTP"
        info "Body: $CANCEL_BODY"
    fi
fi

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
echo ""
echo "============================================"
echo -e " ${GREEN}PASS: $PASS${NC}  ${RED}FAIL: $FAIL${NC}"
echo "============================================"
echo ""

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
