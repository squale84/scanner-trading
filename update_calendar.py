"""Met à jour le calendrier économique dans la base (Neon) — lancé automatiquement par GitHub Actions.

La source gratuite (ForexFactory / FairEconomy) bloque souvent le serveur Render (limite d'appels
par adresse IP). Cette tâche tourne depuis GitHub, récupère le calendrier de la semaine et
l'enregistre dans Postgres ; le serveur Render le relit depuis la base (voir server.py).

Usage : DATABASE_URL=... python update_calendar.py
"""
import os
import sys
import time

import httpx
from dotenv import load_dotenv

load_dotenv()
if not os.environ.get("DATABASE_URL", "").strip():
    # Secret pas encore configuré dans GitHub : on sort proprement (pas d'échec à chaque exécution).
    print("DATABASE_URL absente : rien à faire.")
    sys.exit(0)

import storage  # noqa: E402 (après load_dotenv)

CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}


def main():
    if not storage.init():
        sys.exit(f"Base injoignable : {storage.STATUS['last_error']}")
    resp = httpx.get(CALENDAR_URL, headers=HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list) or not data:
        sys.exit(f"Réponse inattendue de la source : {str(data)[:200]}")
    # Échec d'écriture = échec de la tâche (croix rouge dans l'onglet Actions de GitHub), jamais un faux succès.
    if not storage.save_state("calendar_cache", "calendar_cache.json", {"data": data, "fetched_at": time.time()}):
        sys.exit(f"Écriture en base impossible : {storage.STATUS['last_error']}")
    print(f"Calendrier enregistré : {len(data)} événements.")


if __name__ == "__main__":
    main()
