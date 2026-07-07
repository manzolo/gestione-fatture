# Testing

La suite è organizzata a piramide: molti unit test veloci e deterministici alla base,
smoke test di integrazione HTTP sopra, verifica E2E manuale in cima.

## Livelli

| Livello | Cosa verifica | Dove | Serve un container? |
|---|---|---|---|
| **Unit** (pytest) | Logica pura: calcolo fattura (bollo/soglia 77,47€, sedute frazionarie), decode codice fiscale, mapping STS, helper timezone | `backend/tests/unit/` | No |
| **Smoke backend** (bash+curl) | Endpoint REST del backend (CRUD, giustificativo, costi) | `tests/run_backend_tests.sh` | Sì (stack up) |
| **Smoke frontend** (bash+curl) | Route proxy del frontend | `tests/run_frontend_tests.sh` | Sì (stack up) |
| **STS** (bash+curl) | Integrazione Tessera Sanitaria (7 test, tolleranti a 503) | `tests/run_sts_tests.sh` | Sì (stack up) |
| **E2E** (Playwright, manuale) | Interazioni UI reali (hover Chart.js, screenshot) | ad hoc | Sì |

## Come si eseguono

```bash
make test-unit      # solo unit test (pytest, secondi, nessun DB/container)
make check-backup   # verifica che backups/backup.sql sia allineato alla head Alembic
make test-all       # unit + backend + frontend + sts (richiede stack up per gli smoke)
make test-quick     # backend + frontend senza reset DB
```

Gli unit test girano da `backend/` (`cd backend && python3 -m pytest tests/unit`).
`app/` è un namespace package senza `__init__.py`: importare `app.utils` / `app.sts.mapper`
non ha side effect (niente Flask, DB o rete), quindi i test sono puri e deterministici.
Dipendenze test in `backend/requirements-dev.txt` (solo `pytest`, non incluse nell'immagine).

## Determinismo

- **Codice fiscale**: `decode_codice_fiscale(cf, oggi=...)` accetta la data di riferimento per
  l'euristica del secolo, così i test non dipendono dalla data reale.
- **Timezone**: `app/timezone.py` (`now_local`/`today_local`) usa `zoneinfo`, testabile
  iniettando la zona; la data fattura è corretta anche se il container gira in UTC.
- **STS mapper**: fatture/clienti sono fake (`SimpleNamespace`) e la cifratura CF è disattivata
  (`cert_path=None` → CF in chiaro), quindi il payload XML è deterministico.

## CI (GitHub Actions)

- `.github/workflows/test.yml`:
  - job **`unit`** — Python 3.12, `make check-backup` + `make test-unit` (veloce, senza Compose).
  - job **`test`** — `docker compose up -d --build`, attende health, poi
    `make test-backend`/`test-frontend`/`test-sts`.
  I due job girano in parallelo su push/PR verso `main`.
- `.github/workflows/release.yml` (su tag `v*`): rirun degli stessi guard, poi build & push
  immagini (vedi [RELEASE.md](RELEASE.md)).

## Nota su backup.sql

Gli smoke test ripristinano `backups/backup.sql` **senza** rieseguire le migration. Dopo aver
aggiunto una migration Alembic il dump va rigenerato, altrimenti i test girano su schema vecchio.
`make check-backup` (in CI) fallisce se il dump non è allineato alla head — vedi lo script
`scripts/check_backup_migration.py`.
