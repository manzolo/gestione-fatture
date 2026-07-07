# Invoice App

Sistema di gestione fatture per consulenze psicologiche: clienti, fatture con calcolo
automatico del bollo, costi, generazione PDF (fattura + giustificativo di presenza) e invio a
Sistema Tessera Sanitaria (STS). Stack Docker Compose: Flask + SQLAlchemy, PostgreSQL, Gotenberg.

## Avvio rapido

```bash
cp .env.production.template .env   # e compila i valori
make start                         # avvia tutti i container
make health                        # verifica lo stato dei servizi
```

Frontend su `http://localhost:8080`, backend su `http://localhost:8000`.

## Comandi principali

```bash
make dev            # rebuild + start + logs (sviluppo)
make test-unit      # unit test deterministici (pytest, no DB/container)
make test-all       # suite completa (unit + smoke backend/frontend/sts)
make check-backup   # verifica allineamento backup.sql ↔ migration
make backupdb       # backup PostgreSQL
```

Elenco completo: `make help`.

## Documentazione

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — stack, servizi, modello dati, logica fiscale.
- [docs/TESTING.md](docs/TESTING.md) — piramide di test, come girano in locale e in CI.
- [docs/RELEASE.md](docs/RELEASE.md) — versionamento, CI di release, deploy.
- [CLAUDE.md](CLAUDE.md) — guida operativa dettagliata.
