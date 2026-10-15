"""Récupération des bougies JOURNALIÈRES (lecture seule) via le client MCP TradingView de Jarvis, vers des CSV locaux.

- Utilise ClientMCP de C:\\JARVIS\\tradingview_mcp.py (liste blanche d'outils de lecture, jeton interne, jamais affiché).
- Pour chaque actif, essaie plusieurs symboles et garde celui dont l'historique est le plus long.
- N'affiche et n'enregistre AUCUNE performance : seulement dates, nombre de barres, symbole retenu.
Usage : python recuperer_donnees.py  (depuis n'importe quel dossier ; exécuter avec le Python système)
"""
import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, r"C:\JARVIS")
os.chdir(r"C:\JARVIS")
from tradingview_mcp import ClientMCP  # noqa: E402
from tradingview_oauth import ErreurTradingView  # noqa: E402

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "donnees")
DOSSIER = os.path.normpath(DOSSIER)
os.makedirs(DOSSIER, exist_ok=True)

CANDIDATS = {
    "XAUUSD": ["FOREXCOM:XAUUSD", "OANDA:XAUUSD", "TVC:GOLD"],
    "SPX500": ["SP:SPX", "TVC:SPX"],
    "US100": ["NASDAQ:NDX", "TVC:NDX"],
    "GER40": ["XETR:DAX", "TVC:DAX"],
    "FR40": ["TVC:CAC40", "EURONEXT:PX1"],
    "EURUSD": ["FX:EURUSD", "FX_IDC:EURUSD", "OANDA:EURUSD"],
    "USDJPY": ["FX:USDJPY", "FX_IDC:USDJPY", "OANDA:USDJPY"],
    "USOIL": ["TVC:USOIL", "NYMEX:CL1!"],
    "NATGAS": ["NYMEX:NG1!"],
    "BTCUSD": ["BITSTAMP:BTCUSD", "BINANCE:BTCUSDT"],
}


def colonnes(reponse):
    """Trouve t,o,h,l,c,v dans la réponse (colonnes ou lignes)."""
    for cle in ("bars", "data", "columns"):
        b = reponse.get(cle)
        if isinstance(b, dict) and "t" in b and "c" in b:
            return {k: list(b[k]) for k in ("t", "o", "h", "l", "c", "v") if k in b}
        if isinstance(b, list) and b and isinstance(b[0], dict) and "t" in b[0]:
            return {k: [x.get(k) for x in b] for k in ("t", "o", "h", "l", "c", "v")}
    if "t" in reponse and "c" in reponse:
        return {k: list(reponse[k]) for k in ("t", "o", "h", "l", "c", "v") if k in reponse}
    raise ValueError("format de réponse inattendu : clés " + ",".join(sorted(reponse.keys())))


DEBUT = "1990-01-01"  # début commun des données (choix fixé avant tout calcul de performance)


def jour(t):
    """Date calendaire de la barre. Les barres FX/matières commencent la veille à 22:00 UTC : +3 h les ramène au bon jour."""
    return (datetime(1970, 1, 1) + timedelta(seconds=int(t) + 3 * 3600)).strftime("%Y-%m-%d")


def appeler_avec_pause(client, args):
    for essai in range(8):
        try:
            time.sleep(1.2)
            return client.appeler("get_ohlcv", args)
        except ErreurTradingView as e:
            if essai == 7 or not ("limite" in str(e) or "reseau" in str(e)):
                raise
            time.sleep(25)


def tout_historique(client, symbole):
    toutes = {}
    date_to = None
    for _ in range(40):
        args = {"symbol": symbole, "interval": "1D", "count": 8000, "format": "columns", "date_from": DEBUT}
        if date_to:
            args["date_to"] = date_to
        r = appeler_avec_pause(client, args)
        if r.get("success") is False:
            raise RuntimeError(str(r.get("error"))[:150])
        col = colonnes(r)
        for i, t in enumerate(col["t"]):
            toutes[int(t)] = tuple(col[k][i] if k in col else None for k in ("o", "h", "l", "c", "v"))
        if not r.get("has_more") or not r.get("next_date_to"):
            break
        date_to = r["next_date_to"]
        time.sleep(0.4)
    return toutes


def main():
    client = ClientMCP()
    bilan = {}
    seulement = set(sys.argv[1:])  # ex. : python recuperer_donnees.py NATGAS BTCUSD
    for actif, symboles in CANDIDATS.items():
        if seulement and actif not in seulement:
            continue
        meilleur = None
        for s in symboles:
            try:
                bars = tout_historique(client, s)
            except Exception as e:  # noqa: BLE001
                print(f"{actif:7s} {s:18s} ERREUR {type(e).__name__}: {str(e)[:100]}")
                continue
            if not bars:
                continue
            ts = sorted(bars)
            print(f"{actif:7s} {s:18s} {len(ts):6d} barres  {jour(ts[0])} -> {jour(ts[-1])}", flush=True)
            if meilleur is None or len(ts) > len(meilleur[1]):
                meilleur = (s, bars)
        if meilleur is None:
            bilan[actif] = None
            continue
        s, bars = meilleur
        nom = os.path.join(DOSSIER, f"{actif}.csv")
        with open(nom, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date", "open", "high", "low", "close", "volume", "symbole"])
            for t in sorted(bars):
                o, h, l, c, v = bars[t]
                w.writerow([jour(t), o, h, l, c, v, s])
        bilan[actif] = {"symbole": s, "barres": len(bars)}
    chemin = os.path.join(DOSSIER, "SOURCES.json")
    ancien = {}
    if os.path.exists(chemin):
        with open(chemin, encoding="utf-8") as f:
            ancien = json.load(f).get("actifs", {})
    ancien.update({k: v for k, v in bilan.items() if v})
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({"recupere_le": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "actifs": ancien}, f, indent=2, ensure_ascii=False)
    print("fini")


if __name__ == "__main__":
    main()
