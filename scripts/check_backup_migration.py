#!/usr/bin/env python3
"""Verifica che backups/backup.sql sia allineato alla head delle migration Alembic.

I test (`make test-backend`/`test-frontend`) ripristinano il dump SENZA rieseguire
le migration: se il dump non è aggiornato all'ultima migration, i test girano su uno
schema vecchio e i bug passano inosservati. Questo script codifica il promemoria di
CLAUDE.md ("rigenerare backup.sql dopo ogni migration") in un controllo automatico.

Puro Python: nessun DB, nessun container.
  - la head Alembic si calcola dai file in backend/alembic/versions/
    (risolvendo la catena revision/down_revision);
  - la versione del dump si legge dal blocco COPY public.alembic_version di backup.sql.

Exit 0 se allineati, 1 altrimenti (o su errore di parsing).
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSIONS_DIR = REPO_ROOT / "backend" / "alembic" / "versions"
BACKUP_SQL = REPO_ROOT / "backups" / "backup.sql"

_REVISION_RE = re.compile(r"""^revision(?:\s*:\s*str)?\s*=\s*['"]([^'"]+)['"]""", re.M)
_DOWN_REVISION_RE = re.compile(
    r"""^down_revision(?:\s*:\s*[^=]+)?\s*=\s*(?:['"]([^'"]+)['"]|None)""", re.M
)


def compute_alembic_head() -> str:
    """Calcola l'unica head risolvendo la catena revision/down_revision."""
    if not VERSIONS_DIR.is_dir():
        raise SystemExit(f"ERRORE: directory migration non trovata: {VERSIONS_DIR}")

    revisions = set()
    down_revisions = set()
    for path in VERSIONS_DIR.glob("*.py"):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        rev_match = _REVISION_RE.search(text)
        if not rev_match:
            continue
        revisions.add(rev_match.group(1))
        down_match = _DOWN_REVISION_RE.search(text)
        if down_match and down_match.group(1):
            down_revisions.add(down_match.group(1))

    if not revisions:
        raise SystemExit(f"ERRORE: nessuna revision trovata in {VERSIONS_DIR}")

    heads = revisions - down_revisions
    if len(heads) != 1:
        raise SystemExit(
            f"ERRORE: catena migration non lineare, head multiple o assenti: {sorted(heads)}"
        )
    return heads.pop()


def read_dump_version() -> str:
    """Estrae version_num dal blocco COPY public.alembic_version del dump."""
    if not BACKUP_SQL.is_file():
        raise SystemExit(f"ERRORE: dump non trovato: {BACKUP_SQL}")

    lines = BACKUP_SQL.read_text(encoding="utf-8").splitlines()
    versions = []
    in_block = False
    for line in lines:
        if line.startswith("COPY public.alembic_version"):
            in_block = True
            continue
        if in_block:
            if line.strip() == r"\.":
                break
            if line.strip():
                versions.append(line.strip())

    if not versions:
        raise SystemExit(
            "ERRORE: blocco COPY public.alembic_version non trovato o vuoto in backup.sql"
        )
    if len(versions) != 1:
        raise SystemExit(
            f"ERRORE: attesa una sola alembic_version nel dump, trovate: {versions}"
        )
    return versions[0]


def main() -> int:
    head = compute_alembic_head()
    dump_version = read_dump_version()

    if head == dump_version:
        print(f"✅ backup.sql allineato: alembic head = dump = {head}")
        return 0

    print(
        "❌ backup.sql NON allineato alla head delle migration.\n"
        f"   head migration : {head}\n"
        f"   backup.sql     : {dump_version}\n"
        "\n"
        "   Rigenera il dump di test (come da CLAUDE.md):\n"
        "     1. make restoredb          # ripristina il dump attuale\n"
        "     2. make shell-backend && python -m alembic upgrade head\n"
        "     3. make backupdb           # e sostituisci backups/backup.sql\n",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
