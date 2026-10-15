"""Version LENTE du téléchargeur Dukascopy (le script d'origine n'est pas modifié).

Usage : python telecharger_dukascopy_lent.py XAUUSD 2023-09-01 2026-09-24
Différences : pause de 4 s entre deux jours, recul progressif sur HTTP 429 (60 s, 120 s ... max 15 min),
nouvel essai court (15 s) sur erreur réseau, progression tous les 10 jours, Ctrl+C propre :
le CSV PARTIEL est écrit avec les jours déjà en cache. On peut relancer : le cache est réutilisé.
Sortie : data/XAUUSD_M5.csv
"""
import csv, datetime as dt, os, sys, time, urllib.error, urllib.request
import telecharger_dukascopy as base

PAUSE = 4.0          # secondes entre deux jours téléchargés
MAX_ESSAIS = 60
MAX_ECHECS_JOUR = 4   # échecs réseau/serveur avant d'abandonner un jour (le 429 attend sans limite de ce compteur)
SAUTES = []


def telecharger(sym, jour):
    """Remplit le cache du jour si absent. Retourne True si un téléchargement réseau a eu lieu."""
    cache = os.path.join(base.DATA, "cache", sym, jour.isoformat() + ".bi5")
    if os.path.exists(cache):
        return False
    url = base.URL.format(sym=sym, y=jour.year, m=jour.month - 1, d=jour.day)
    attente429 = 60
    attente_res = 15
    echecs = 0
    for essai in range(MAX_ESSAIS):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                brut = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                brut = b""
                break
            if e.code == 429:
                print(f"{jour} : 429, pause {attente429}s", flush=True)
                time.sleep(attente429)
                attente429 = min(attente429 * 2, 900)
            else:
                echecs += 1
                print(f"{jour} : HTTP {e.code} (échec {echecs}/{MAX_ECHECS_JOUR})", flush=True)
                if echecs >= MAX_ECHECS_JOUR:
                    SAUTES.append(jour)
                    print(f"{jour} : ABANDONNÉ, on passe au jour suivant", flush=True)
                    return False
                time.sleep(30)
        except OSError as e:
            cause = getattr(e, "reason", e)
            echecs += 1
            print(f"{jour} : {type(e).__name__} (échec {echecs}/{MAX_ECHECS_JOUR}), nouvel essai dans {attente_res}s", flush=True)
            if echecs >= MAX_ECHECS_JOUR:
                SAUTES.append(jour)
                print(f"{jour} : ABANDONNÉ, on passe au jour suivant", flush=True)
                return False
            time.sleep(attente_res)
            attente_res = min(attente_res * 2, 300)
    else:
        raise RuntimeError(f"abandon : {jour}")
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    with open(cache, "wb") as f:
        f.write(brut)
    return True


def ecrire_m5(sym, jours):
    m5 = {}
    for j in jours:
        if not os.path.exists(os.path.join(base.DATA, "cache", sym, j.isoformat() + ".bi5")):
            continue
        for t, o, h, l, c, v in base.jour_m1(sym, j):  # lit le cache, aucun réseau
            cle = t.replace(minute=t.minute - t.minute % 5, second=0)
            b = m5.get(cle)
            if b is None:
                m5[cle] = [o, h, l, c, v]
            else:
                b[1] = max(b[1], h); b[2] = min(b[2], l); b[3] = c; b[4] += v
    sortie = os.path.join(base.DATA, f"{sym}_M5.csv")
    with open(sortie, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_utc", "open", "high", "low", "close", "volume"])
        for cle in sorted(m5):
            o, h, l, c, v = m5[cle]
            w.writerow([cle.strftime("%Y-%m-%d %H:%M"), o, h, l, c, round(v, 4)])
    print(f"{sym} : {len(m5)} bougies M5 -> {sortie}", flush=True)


def main():
    sym, d0, d1 = sys.argv[1], dt.date.fromisoformat(sys.argv[2]), dt.date.fromisoformat(sys.argv[3])
    jours = [d0 + dt.timedelta(n) for n in range((d1 - d0).days + 1)]
    jours = [j for j in jours if j.weekday() != 5]
    try:
        for n, j in enumerate(jours, 1):
            if telecharger(sym, j):
                time.sleep(PAUSE)
            if n % 10 == 0:
                print(f"{n}/{len(jours)} jours (dernier : {j})", flush=True)
    except KeyboardInterrupt:
        print("Interrompu : écriture du CSV partiel.", flush=True)
    ecrire_m5(sym, jours)
    if SAUTES:
        print('Jours sautés (à retenter plus tard en relançant) :', ', '.join(str(j) for j in SAUTES), flush=True)


if __name__ == "__main__":
    main()
