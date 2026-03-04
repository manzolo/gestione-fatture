# Integrazione STS — Sistema Tessera Sanitaria

## Stato

| Branch | Versione | Stato |
|--------|----------|-------|
| `main` | `v2.1.2` | ✅ In produzione |

---

## Cosa fa

Trasmette i dati delle spese sanitarie al Sistema Tessera Sanitaria (MEF/Agenzia delle Entrate) per la precompilazione del modello 730 dei pazienti. Usa il web service sincrono SOAP `DocumentoSpesa730p` (kit `WS_SincronoSingoloDato730`).

---

## Endpoint API

Base URL: `http://localhost:8000/api/sts`

| Metodo | Path | Descrizione |
|--------|------|-------------|
| GET | `/invoices/unsent` | Lista fatture con `data_pagamento` valorizzata e non ancora inviate |
| POST | `/invoices/<id>/send` | Invia singola fattura (`?force=true` per reinvio) |
| POST | `/invoices/send-batch` | Invio batch: `{"year": 2025}` oppure `{"ids": [1,2,3]}` |
| POST | `/invoices/<id>/cancel` | Cancella invio precedente su STS |

### Esempio risposta `/send`
```json
{
  "success": true,
  "fattura_id": 42,
  "protocollo": "730P-2025-XXXXXX",
  "errors": []
}
```

---

## Variabili d'ambiente

```env
# Ambiente (test | production)
STS_ENVIRONMENT=test

# Credenziali HTTP Basic Auth
STS_USERNAME=MTOMRA66A41G224M
STS_PASSWORD=Salve123

# Credenziali già cifrate RSA (fornite dal kit ufficiale per test)
STS_PINCODE_ENCRYPTED=W+cy4...
STS_CF_PROPRIETARIO_ENCRYPTED=SsFrZ...

# Dati professionista
STS_PARTITA_IVA=65498732105
STS_DISPOSITIVO=1

# Certificati
STS_CERTIFICATE_PATH=/app/certs/sts_cert.pem     # cifratura CF paziente (SanitelCF)
STS_CA_BUNDLE=/app/certs/CAAgenziadelleEntrateTest.pem  # CA per verifica TLS
STS_SSL_VERIFY=false   # SOLO in test (CA Sogei non pubblica)
```

> **Produzione:** sostituire username/password/pincode/cfProprietario con le credenziali reali, impostare `STS_ENVIRONMENT=production` e `STS_SSL_VERIFY=true`.

---

## Nuovi campi DB

### Tabella `fattura`
| Campo | Tipo | Default | Descrizione |
|-------|------|---------|-------------|
| `inviata_sts` | BOOLEAN | false | Fattura inviata a STS |
| `protocollo_sts` | VARCHAR(100) | NULL | Protocollo restituito da STS |
| `data_invio_sts` | TIMESTAMP | NULL | Data/ora ultimo invio |

### Tabella `cliente`
| Campo | Tipo | Default | Descrizione |
|-------|------|---------|-------------|
| `flag_opposizione` | BOOLEAN | false | Paziente ha esercitato diritto di opposizione |

Migrazione: `backend/alembic/versions/a1b2c3d4e5f6_sts_fields.py`

---

## Struttura file

```
backend/app/sts/
├── __init__.py
├── client.py       # STSClient: SOAP over HTTPS, retry, SSL adapter
├── encryption.py   # encrypt_cf(): placeholder → upgrade con SanitelCF.cer
└── mapper.py       # build_inserimento_payload() / build_cancellazione_payload()

backend/app/api/
└── sts_api.py      # Blueprint Flask /api/sts

backend/alembic/versions/
└── a1b2c3d4e5f6_sts_fields.py

certs/
├── .gitkeep
├── CAAgenziadelleEntrateTest.pem    # CA Agenzia Entrate test (versionata)
├── CAAgenziadelleEntrateProd.pem    # Catena CA Sectigo produzione (versionata)
└── sts_cert.pem                     # SanitelCF per cifratura CF (git-ignored, scade gen 2027)

tests/
└── run_sts_tests.sh
```

---

## Note tecniche

### SSL / TLS
- I server STS (`invioSS730pTest.sanita.finanze.it`, `invioSS730p.sanita.finanze.it`) usano cipher suite legacy.
- Fix: `_STSSSLAdapter` con `DEFAULT@SECLEVEL=1` (risolve `SSLV3_ALERT_HANDSHAKE_FAILURE`).
- Il server di test usa una CA interna Sogei non pubblica → `STS_SSL_VERIFY=false` in test.
- In produzione il server usa CA pubblica Sectigo/USERTrust (nel trust store di sistema). Il client carica automaticamente i certificati di sistema con `set_default_verify_paths()`, più eventuali CA aggiuntive da `STS_CA_BUNDLE`.

### Cifratura CF paziente
- **Implementata:** RSA PKCS#1 v1.5 con il certificato pubblico `SanitelCF.cer` di Agenzia delle Entrate.
- Il certificato è in `certs/sts_cert.pem` (copiato da `kit730P_ver_20240214/SanitelCF.cer`, valido fino a gen 2027).
- `cryptography>=42.0.0` è in `requirements.txt`.
- Lo stesso certificato vale per test e produzione (è il certificato pubblico AE per cifrare il CF paziente).
- **Deploy:** `certs/sts_cert.pem` è gitignored — va copiato manualmente sul server di produzione.

### Rinnovo certificati

#### 1. Certificato SanitelCF (`certs/sts_cert.pem`) — scadenza: gennaio 2027

Usato per cifrare il CF del paziente (RSA PKCS#1 v1.5). Quando scade:

```bash
# Scaricare il nuovo certificato dal portale STS o dal kit aggiornato
# Se è in formato DER (.cer), convertirlo in PEM:
openssl x509 -inform DER -in SanitelCF.cer -out certs/sts_cert.pem

# Verificare subject e scadenza:
openssl x509 -in certs/sts_cert.pem -noout -subject -dates

# Output atteso:
#   subject=C = IT, O = Agenzia delle Entrate, OU = Servizi Telematici, CN = SanitelCF
#   notBefore=...
#   notAfter=...

# Copiare sul server di produzione:
scp certs/sts_cert.pem utente@server:/percorso/invoice-app/certs/

# Rigenerare i valori cifrati (pincode e CF proprietario):
python3 scripts/sts_encrypt.py --cf <CODICE_FISCALE> --pincode <PINCODE>

# Aggiornare STS_PINCODE_ENCRYPTED e STS_CF_PROPRIETARIO_ENCRYPTED nel .env di produzione
# poi riavviare:
make restart
```

> **Importante:** dopo il rinnovo del certificato SanitelCF bisogna **rigenerare** anche `STS_PINCODE_ENCRYPTED` e `STS_CF_PROPRIETARIO_ENCRYPTED` perché sono cifrati con la chiave pubblica del certificato.

#### 2. CA bundle produzione (`certs/CAAgenziadelleEntrateProd.pem`)

Catena CA del server STS di produzione (Sectigo). Normalmente non serve rinnovarla perché il client carica anche il trust store di sistema. Se necessario aggiornarla:

```bash
# Estrarre la catena dal server di produzione:
echo | openssl s_client -showcerts \
  -connect invioss730p.sanita.finanze.it:443 \
  -servername invioss730p.sanita.finanze.it 2>/dev/null \
  | awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/{print}' \
  > certs/CAAgenziadelleEntrateProd.pem

# Verificare:
openssl x509 -in certs/CAAgenziadelleEntrateProd.pem -noout -subject -issuer

# Copiare sul server:
scp certs/CAAgenziadelleEntrateProd.pem utente@server:/percorso/invoice-app/certs/
```

#### 3. Verifica rapida della configurazione SSL dal container

```bash
# Test connessione SSL dal container:
docker exec invoice_backend python3 -c "
import ssl, socket
from urllib3.util.ssl_ import create_urllib3_context
ctx = create_urllib3_context(ciphers='DEFAULT@SECLEVEL=1')
ctx.set_default_verify_paths()
with ctx.wrap_socket(socket.socket(), server_hostname='invioss730p.sanita.finanze.it') as s:
    s.connect(('invioss730p.sanita.finanze.it', 443))
    cert = s.getpeercert()
    print('SSL OK')
    print('Server:', dict(x[0] for x in cert['subject']))
    print('Scadenza:', cert['notAfter'])
"

# Verifica scadenza certificato SanitelCF nel container:
docker exec invoice_backend \
  openssl x509 -in /app/certs/sts_cert.pem -noout -subject -enddate
```

### Formato numero documento
`F{anno}{progressivo:04d}` → es. `F20250042` (max 20 caratteri, conforme XSD `numDocType`)

### Tipo spesa
`SP` — Prestazioni di psicologia (conforme XSD `tipoSpesa`)

### IVA
`aliquotaIVA: 0.00` — prestazioni esenti IVA art. 10 DPR 633/72

---

## Stato completamento

- [x] Merge `feature/sts-integration` → `main`
- [x] Certificato SanitelCF: `certs/sts_cert.pem` (da kit ufficiale, stesso per test e prod)
- [x] `cryptography>=42.0.0` aggiunto a `requirements.txt`
- [x] `encrypt_cf()` implementata in `backend/app/sts/encryption.py`
- [x] Frontend: colonna stato STS + pulsante "Invia a STS" per riga
- [x] Credenziali di produzione configurate
- [x] Deploy e primo invio reale completato (v2.1.2)
