---
description: Release completa con bump versione automatico (tag → CI build/push → deploy in prod)
argument-hint: "[patch|minor|major | vX.Y.Z]  (default: patch)"
allowed-tools: Bash(git *), Bash(make *), Bash(ssh *), Bash(docker *), Bash(gh run:*)
---

Esegui il flusso completo di release & deploy dell'invoice-app. Il tipo di bump è: **$ARGUMENTS** (se vuoto, usa `patch`).

## Config di deploy (NON hardcodare dati personali)
I dettagli del server vivono in `.claude/deploy.local.env` (git-ignored), con `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_PATH`. All'inizio caricali:
```
set -a; . .claude/deploy.local.env; set +a
```
Se il file manca, FERMATI e dì all'utente di copiarlo da `.claude/deploy.env.example` e compilarlo. Non inventare host/path e non scriverli mai nei messaggi o nei commit.

## Regole di versionamento (SemVer, prefisso `v`)
- Nessuna versione in file: la fonte di verità è l'ultimo git tag.
- `patch` → z+1 (bugfix); `minor` → y+1, z=0 (nuova feature); `major` → x+1, y=0, z=0 (breaking).
- Se `$ARGUMENTS` è già una versione esplicita tipo `v2.7.0`, usala così com'è.
- Determina il prossimo tag da: `git tag --sort=-v:refname | head -1`.

## Precondizioni (verifica e FERMATI se falliscono)
1. `git status` pulito (nessuna modifica non committata). Se ci sono modifiche non committate, chiedi all'utente se committarle prima o abortire.
2. Sei su `main` e allineato: `git push origin main` non deve avere nulla in sospeso di imprevisto (ok se "up to date").
3. Il tag calcolato non deve già esistere.

## Passi (eseguire in ordine, fermarsi al primo errore)

1. **Calcola la versione**: leggi l'ultimo tag, applica il bump richiesto, mostra all'utente `vecchio → nuovo` e la lista dei commit inclusi (`git log <ultimo-tag>..HEAD --oneline`). Procedi.

2. **Tag + push**:
   ```
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

3. **Attendi la pubblicazione immagini in CI**: il push del tag fa scattare il workflow `Release` (`.github/workflows/release.yml`) che esegue i guard (unit test + check-backup) e poi builda e pusha le immagini (`manzolo/invoice_backend`, `manzolo/invoice_frontend`) con tag `vX.Y.Z` + `latest`. Individua il run del tag e attendine l'esito:
   ```
   # dai qualche secondo alla registrazione del run, poi elenca i run recenti di Release:
   gh run list --workflow=Release --limit 5 --json databaseId,headBranch,status,conclusion,event,createdAt
   # individua il run relativo al tag vX.Y.Z (event=push) e osservalo fino alla fine:
   gh run watch <run-id> --exit-status
   ```
   `--exit-status` restituisce non-zero se il workflow fallisce: in quel caso FERMATI (guarda `gh run view <run-id> --log-failed`). Cause tipiche: secret `DOCKERHUB_USERNAME`/`DOCKERHUB_TOKEN` mancanti o scaduti.
   **Fallback manuale** (solo se la CI è indisponibile): `make docker-push TAG=vX.Y.Z` — lancia in background e monitora fino a "Immagini pubblicate con successo".

4. **Deploy in produzione** (fa backup DB + pull + up -d). Il compose del server pinna le immagini a `${INVOICE_VERSION:-latest}`: imposta prima la versione appena pubblicata in `.env`, poi `make update`. Usa le variabili caricate da `.claude/deploy.local.env`:
   ```
   ssh -o BatchMode=yes "$DEPLOY_USER@$DEPLOY_HOST" "cd $DEPLOY_PATH && \
     ( grep -q '^INVOICE_VERSION=' .env && sed -i 's/^INVOICE_VERSION=.*/INVOICE_VERSION=vX.Y.Z/' .env || printf 'INVOICE_VERSION=vX.Y.Z\n' >> .env ) && \
     make update"
   ```
   Lancia in background e monitora fino a "Started"/"Healthy". Fermati su qualsiasi errore. Nota: senza aggiornare `INVOICE_VERSION` il deploy resterebbe pinnato alla versione precedente (il `pull` non prenderebbe la nuova).

5. **Smoke test in prod**: verifica che il codice nuovo sia effettivamente nel container. Almeno controlla lo stato dei container e che backend/frontend siano `healthy`/`Up`. Se la release tocca file frontend specifici, `grep` un marcatore noto dentro `docker exec invoice_frontend ...` (o backend).

6. **Riepilogo finale**: tabella con esito di ogni step (tag, immagini, deploy, smoke test) e la versione pubblicata.

## Note
- Il push immagini avviene in CI sul tag (`.github/workflows/release.yml`), non più con `make docker-push` manuale: quest'ultimo resta come fallback se la CI è indisponibile. NON eseguire entrambi (doppio build).
- Il deploy (passo 4) va fatto SOLO dopo che il run `Release` è concluso con successo, altrimenti il `pull` sul server non trova le nuove immagini.
- Il workflow `test.yml` (push/PR su `main`) fa solo test; è `release.yml` (tag `v*`) a pubblicare le immagini.
- Il server non usa git: gira su immagini Docker da registry (`manzolo/invoice_backend`, `manzolo/invoice_frontend`).
- Il compose del server pinna le immagini a `${INVOICE_VERSION:-latest}` (dal 2026-07-07): la versione live è in `.env` (`INVOICE_VERSION`), il pin dà rollback espliciti (basta cambiare la var e `make update`). Backup del compose in `docker-compose.yaml.bak` sul server.
- Solo i container con immagine cambiata vengono ricreati (normale che backend resti su se hai toccato solo il frontend).
- Non stampare né committare mai host/utente/path del server: provengono da `.claude/deploy.local.env` (git-ignored).
