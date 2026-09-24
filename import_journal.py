"""Importe un historique de journal dans la base Postgres (DATABASE_URL, lue dans .env).

Usage :
    python import_journal.py https://scanner-trading-g7r7.onrender.com/api/journal
    python import_journal.py backtest_exports/journal_live_backup_2026-09-23.json

Plusieurs sources possibles. Relançable sans risque : une ligne déjà présente (même type,
heure, actif et statut) n'est jamais réinsérée.
"""
import json
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()
import storage  # noqa: E402 (après load_dotenv)


def key(row):
    return (row.get("kind"), row.get("time"), row.get("symbol"), row.get("status"))


def read_source(src):
    if src.startswith("http"):
        return httpx.get(src, timeout=90).json()
    with open(src, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def main(sources):
    if storage.BACKEND != "postgres":
        sys.exit("DATABASE_URL absente : ajoute-la dans le fichier .env avant d'importer.")
    if not storage.init():
        sys.exit(f"Base injoignable : {storage.STATUS['last_error']}")
    current = storage.load_journal(10**9)
    if current is storage.FAILED:
        sys.exit(f"Lecture du journal impossible : {storage.STATUS['last_error']}")
    existing = {key(r) for r in current}
    rows = []
    for src in sources:
        data = read_source(src)
        print(f"{src} : {len(data)} ligne(s)")
        rows.extend(data)
    new_rows = []
    for row in sorted(rows, key=lambda r: r.get("time") or ""):
        if key(row) not in existing:
            existing.add(key(row))
            new_rows.append(row)
    written = 0
    for row in new_rows:
        if not storage.append_journal_row(row, None):
            sys.exit(f"Arrêt : {written} ligne(s) importée(s), échec ensuite : {storage.STATUS['last_error']}")
        written += 1
    print(f"{written} ligne(s) importée(s), {len(rows) - len(new_rows)} déjà présente(s).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
