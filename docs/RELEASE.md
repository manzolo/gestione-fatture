# Release & Deploy

## Versionamento

SemVer con prefisso `v`. **La fonte di verità è l'ultimo git tag** (nessun file di versione).
- `patch` → `z+1` (bugfix), `minor` → `y+1, z=0` (feature), `major` → `x+1, y=0, z=0` (breaking).
- Prossimo tag calcolato da `git tag --sort=-v:refname | head -1`.

## Flusso automatizzato: `/bump`

Lo slash command `/bump` (in `.claude/commands/bump.md`) esegue l'intero flusso:
1. verifica precondizioni (working tree pulito, su `main`, allineato, tag libero);
2. calcola la versione e crea/pusha il tag;
3. build & push immagini Docker;
4. deploy in produzione (`ssh … make update`: backup DB + pull + `up -d`);
5. smoke test in prod (stato/health container).

I dati del server vivono in `.claude/deploy.local.env` (git-ignored) — mai hardcodati.

## Push immagini: due canali

1. **CI su tag** (preferito) — `.github/workflows/release.yml` scatta su push di un tag `v*`,
   esegue i guard (unit test + `check-backup`), poi builda e pusha
   `manzolo/invoice_backend` e `manzolo/invoice_frontend` con tag `vX.Y.Z` **e** `latest`.
   Richiede i secret repo `DOCKERHUB_USERNAME` e `DOCKERHUB_TOKEN`.
2. **Manuale** (fallback) — `make docker-push [TAG=vX.Y.Z]` dalla propria macchina.

> Prima l'unico canale era `make docker-push` manuale: dipendeva dalla macchina e dalla memoria
> del comando. Ora il tag di release scatena la pubblicazione in CI.

## Deploy in produzione

Il server **non usa git**: gira su immagini Docker dal registry. Il deploy fa `make update`
(backup DB + pull nuove immagini + `up -d`). La configurazione (host, path, TZ) vive fuori da questo repo.

### Pinning delle immagini + rollback
Il compose di produzione pinna le immagini alla versione via env:
```yaml
image: manzolo/invoice_backend:${INVOICE_VERSION:-latest}
image: manzolo/invoice_frontend:${INVOICE_VERSION:-latest}
```
La versione live sta in `INVOICE_VERSION` nel `.env` del server. Lo step di deploy di `/bump`
aggiorna `INVOICE_VERSION` (replace-or-append) prima di `make update`, così il `pull` prende il
tag giusto. **Rollback**: imposta `INVOICE_VERSION=vX.Y.Z` (versione precedente) e `make update`;
il fallback `:-latest` evita rotture se la var manca. Backup del compose: `docker-compose.yaml.bak`.

### Versione visibile in UI
Il frontend legge `INVOICE_VERSION` (Jinja `{{ app_version }}`) e la mostra nel footer della
sidebar — la versione deployata è verificabile a colpo d'occhio. In locale è `dev`.

## Guard `backup.sql`

Dopo ogni migration Alembic, rigenerare `backups/backup.sql` (gli smoke test lo ripristinano
senza rieseguire le migration). `make check-backup` — eseguito anche in CI — fallisce se il dump
non è allineato alla head. Rigenerazione:
```bash
make restoredb                                   # ripristina il dump attuale
make shell-backend && python -m alembic upgrade head
make backupdb                                    # sostituisci backups/backup.sql
```
