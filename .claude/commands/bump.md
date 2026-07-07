---
description: Release completa con bump versione automatico (tag → docker-push → deploy in prod)
argument-hint: "[patch|minor|major | vX.Y.Z]  (default: patch)"
allowed-tools: Bash(git *), Bash(make *), Bash(ssh *), Bash(docker *)
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

3. **Build & push immagini Docker** (backend + frontend, tag specifico + latest):
   ```
   make docker-push TAG=vX.Y.Z
   ```
   Gira lungo: lancia in background e monitora fino a "Immagini pubblicate con successo". Fermati se compaiono `denied`/`unauthorized`/`error`.

4. **Deploy in produzione** (fa backup DB + pull + up -d). Usa le variabili caricate da `.claude/deploy.local.env`:
   ```
   ssh -o BatchMode=yes "$DEPLOY_USER@$DEPLOY_HOST" "cd $DEPLOY_PATH && make update"
   ```
   Lancia in background e monitora fino a "Started"/"Healthy". Fermati su qualsiasi errore.

5. **Smoke test in prod**: verifica che il codice nuovo sia effettivamente nel container. Almeno controlla lo stato dei container e che backend/frontend siano `healthy`/`Up`. Se la release tocca file frontend specifici, `grep` un marcatore noto dentro `docker exec invoice_frontend ...` (o backend).

6. **Riepilogo finale**: tabella con esito di ogni step (tag, immagini, deploy, smoke test) e la versione pubblicata.

## Note
- La pipeline CI GitHub fa solo test, NON pusha su Docker Hub: il `make docker-push` qui è l'unico canale verso il registry.
- Il server non usa git: gira su immagini Docker da registry (`manzolo/invoice_backend`, `manzolo/invoice_frontend`).
- Solo i container con immagine cambiata vengono ricreati (normale che backend resti su se hai toccato solo il frontend).
- Non stampare né committare mai host/utente/path del server: provengono da `.claude/deploy.local.env` (git-ignored).
