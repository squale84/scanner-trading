"""Télécharge l'historique M1 gratuit de Dukascopy (bougies BID, UTC) et l'agrège en M5.

Usage : python telecharger_dukascopy.py XAUUSD 2023-09-01 2026-09-24
Sortie : data/XAUUSD_M5.csv (time_utc, open, high, low, close, volume)
Les jours déjà téléchargés sont gardés en cache dans data/cache/, on peut relancer sans tout refaire.
"""
import csv, datetime as dt, lzma, os, struct, sys, time, urllib.error, urllib.request


ICI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ICI, "data")
URL = "https://datafeed.dukascopy.com/datafeed/{sym}/{y}/{m:02d}/{d:02d}/BID_candles_min_1.bi5"
ECHELLE = {"XAUUSD": 1000, "EURUSD": 100000, "USDJPY": 1000}  # diviseur des prix entiers


def jour_m1(sym, jour):
    """Bougies M1 d'un jour UTC : liste de (datetime, o, h, l, c, v). Cache local."""
    cache = os.path.join(DATA, "cache", sym, jour.isoformat() + ".bi5")
    if not os.path.exists(cache):
        url = URL.format(sym=sym, y=jour.year, m=jour.month - 1, d=jour.day)  # mois indexé à 0
        # Dukascopy bloque temporairement les clients trop rapides : on attend et on réessaie
        # (5 min entre deux tentatives, abandon après 3 h de blocage continu).
        for essai in range(36):
            try:
                with urllib.request.urlopen(url, timeout=30) as r:
                    brut = r.read()
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    brut = b""
                    break
                print(f"{jour} : HTTP {e.code}, nouvel essai dans 5 min", flush=True)
            except OSError as e:
                print(f"{jour} : {type(e).__name__}, nouvel essai dans 5 min", flush=True)
            time.sleep(300)
        else:
            raise RuntimeError(f"échec du téléchargement : {jour}")
        time.sleep(1.0)  # rythme modéré entre deux jours
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "wb") as f:
            f.write(brut)
    brut = open(cache, "rb").read()
    if not brut:
        return []
    donnees = lzma.decompress(brut)
    ech = ECHELLE[sym]
    debut = dt.datetime(jour.year, jour.month, jour.day, tzinfo=dt.timezone.utc)
    res = []
    for i in range(0, len(donnees), 24):
        t, o, c, l, h, v = struct.unpack(">5if", donnees[i:i + 24])
        if v <= 0:
            continue  # minute sans cotation (marché fermé) : ignorée
        res.append((debut + dt.timedelta(seconds=t), o / ech, h / ech, l / ech, c / ech, v))
    return res


def main():
    sym, d0, d1 = sys.argv[1], dt.date.fromisoformat(sys.argv[2]), dt.date.fromisoformat(sys.argv[3])
    jours = [d0 + dt.timedelta(n) for n in range((d1 - d0).days + 1)]
    jours = [j for j in jours if j.weekday() != 5]  # samedi : marché fermé
    par_jour = []
    for n, j in enumerate(jours, 1):
        par_jour.append(jour_m1(sym, j))
        if n % 50 == 0:
            print(f"{n}/{len(jours)} jours", flush=True)
    m5 = {}
    for bougies in par_jour:
        for t, o, h, l, c, v in bougies:
            cle = t.replace(minute=t.minute - t.minute % 5, second=0)
            b = m5.get(cle)
            if b is None:
                m5[cle] = [o, h, l, c, v]
            else:
                b[1] = max(b[1], h); b[2] = min(b[2], l); b[3] = c; b[4] += v
    sortie = os.path.join(DATA, f"{sym}_M5.csv")
    with open(sortie, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_utc", "open", "high", "low", "close", "volume"])
        for cle in sorted(m5):
            o, h, l, c, v = m5[cle]
            w.writerow([cle.strftime("%Y-%m-%d %H:%M"), o, h, l, c, round(v, 4)])
    print(f"{sym} : {len(jours)} jours, {len(m5)} bougies M5 -> {sortie}")


if __name__ == "__main__":
    main()
