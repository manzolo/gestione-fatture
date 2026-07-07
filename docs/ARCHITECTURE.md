# Architettura

Sistema di gestione fatture per consulenze psicologiche: clienti, fatture (con calcolo bollo),
costi, generazione PDF fattura/giustificativo e invio a Sistema Tessera Sanitaria (STS).

## Stack

- **Backend**: Flask + SQLAlchemy (Python 3.12), API REST.
- **Frontend**: Flask + Jinja2 + JS vanilla (jQuery, Chart.js, Select2), fa da proxy al backend.
- **DB**: PostgreSQL 13, migrazioni Alembic (eseguite all'avvio del backend via `entrypoint.sh`).
- **PDF**: Gotenberg (converte DOCX → PDF).
- **Deploy**: Docker Compose.

## Servizi (docker-compose.yaml)

| Servizio | Porta | Ruolo |
|---|---|---|
| `invoice_backend` | 8000 | API REST |
| `invoice_frontend` | 80 → 8080 | UI + proxy |
| `invoice_postgres_db` | 5432 | DB |
| `invoice_pgadmin` | — | admin DB |
| `invoice_gotenberg` | 3000 | DOCX→PDF |

Config e timezone vivono in `.env` + compose (non nell'immagine): i Dockerfile installano
`tzdata` ma non fissano `ENV TZ`. Il codice usa `app/timezone.py` (zoneinfo) per la data locale,
quindi la data fattura è corretta anche se il container gira in UTC.

## Modello dati

- **Cliente**: `id, nome, cognome, codice_fiscale (unique), luogo_nascita?, data_nascita?, indirizzo, citta, cap, flag_opposizione`.
- **Fattura**: `id, anno, progressivo, data_fattura, data_pagamento?, metodo_pagamento, cliente_id, importo_prestazione, bollo, descrizione, totale, numero_sedute (float), inviata_sts, protocollo_sts?, data_invio_sts?`.
- **FatturaProgressivo**: `anno (PK), last_progressivo` — numerazione progressiva per anno.
- **Costo** / **CostoRicorrente**: costi puntuali e ricorrenti (generazione automatica).

## Logica fiscale (`backend/app/utils.py`)

```
PRESTAZIONE_BASE       = 58.82   # prezzo base per seduta
CONTRIBUTO_PERCENTUALE = 0.02    # 2% sul prezzo base
BOLLO_COSTO            = 2.00
BOLLO_SOGLIA           = 77.47   # bollo se totale imponibile > soglia (strict >)
```
- `calculate_invoice_totals(numero_sedute, prezzo_base_unitario=None)` — supporta sedute
  frazionarie (1.5, 2.5); il bollo si applica se `totale_imponibile > 77.47`.
- `decode_codice_fiscale(cf, oggi=None)` — decodifica sesso e data di nascita (no luogo);
  gestisce l'omocodia; `oggi` iniettabile per l'euristica del secolo.
- Funzioni pure e coperte da unit test — vedi [TESTING.md](TESTING.md).

## Generazione PDF

Il backend riempie un template DOCX (`invoice_template.docx` / `giustificativo_template.docx`)
con docxtpl, lo invia a Gotenberg per la conversione in PDF, salva e restituisce il file. Il
template custom con logo può essere montato via volume in `custom_template/`.

## STS (Sistema Tessera Sanitaria)

Modulo `backend/app/sts/` (encryption, mapper, client) + blueprint `sts_api.py` (`/api/sts`).
`mapper.py` costruisce gli envelope SOAP di inserimento/cancellazione; il CF del cittadino è
cifrato RSA PKCS#1 v1.5 col certificato SanitelCF (in test resta in chiaro). Config via env
`STS_*`.

## Documentazione correlata

- [TESTING.md](TESTING.md) — strategia e comandi di test.
- [RELEASE.md](RELEASE.md) — versionamento, CI di release, deploy.
- `CLAUDE.md` — guida operativa dettagliata per lavorare sul repo.
