"""Moteur de backtest des candidates 1, 2 et 3 (voir PROTOCOLE_FIGE.md). Lecture seule des CSV de ../donnees.

Conventions :
- p[t] = position (en multiple du nominal, signée) établie à la CLÔTURE du jour t, détenue sur (t, t+1].
- r[t] = clôture[t] / clôture[t-1] - 1 ; le gain brut du jour t est p[t-1] * r[t].
- Spread : demi-spread aller-retour × |p[t] - p[t-1]|, payé à la clôture t.
- Swap : taux/nuit (côté long ou court) × |p[t-1]| × nombre de nuits calendaires entre les barres t-1 et t.
"""
import csv
import math
import os

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
DONNEES = os.path.normpath(os.path.join(BASE, "..", "donnees"))

DEBUT_EVAL_DEV = "1991-01-01"   # 12 mois d'échauffement après le 01/01/1990
DEV_FIN = "2023-09-30"
BLIND_DEBUT = "2023-10-01"
FIN_DONNEES = "2026-10-13"      # les barres du 14 et 15/10 sont encore en formation

UNIVERS = ["XAUUSD", "SPX500", "US100", "GER40", "FR40", "EURUSD", "USDJPY", "USOIL", "NATGAS"]
INFO = ["BTCUSD"]
INDICES = ["SPX500", "US100", "GER40", "FR40"]

# Spread aller-retour, fraction du nominal [calcul à partir des spreads XTB cités dans le rapport]
SPREAD_RT = {"XAUUSD": 0.00009, "SPX500": 0.00010, "US100": 0.00006, "GER40": 0.00008, "FR40": 0.00017,
             "EURUSD": 0.000085, "USDJPY": 0.00011, "USOIL": 0.0007, "NATGAS": 0.0028, "BTCUSD": 0.0030}
# Swap par nuit, fraction du nominal (coût positif). Aucun crédit retenu (conservateur).
SWAP_LONG = {"XAUUSD": 0.000344, "SPX500": 0.000219, "US100": 0.000229, "GER40": 0.000233, "FR40": 0.000179,
             "EURUSD": 0.000076, "USDJPY": 0.0, "USOIL": 0.000427, "NATGAS": 0.000427, "BTCUSD": 0.000972}
SWAP_SHORT = {"XAUUSD": 0.000128, "SPX500": 0.000003, "US100": 0.000003, "GER40": 0.000043, "FR40": 0.000057,
              "EURUSD": 0.0, "USDJPY": 0.000114, "USOIL": 0.000212, "NATGAS": 0.000212, "BTCUSD": 0.000278}

SCENARIOS = {  # nom -> (multiplicateur spread, multiplicateur swap)
    "brut": (0.0, 0.0),
    "reel": (1.0, 1.0),
    "x2": (2.0, 1.0),          # coûts ×2 du protocole : spread ×2, swap actuel
    "swap_x2": (1.0, 2.0),     # sensibilité informative
}


# ----------------------------------------------------------------------------------- données
class Serie:
    def __init__(self, actif, dates, close, erreurs):
        self.actif = actif
        self.dates = dates                    # datetime64[D]
        self.close = close
        self.erreurs = erreurs
        self.jours = dates.astype("datetime64[D]").astype(np.int64)
        r = np.zeros(len(close))
        invalide = np.zeros(len(close), dtype=bool)
        with np.errstate(divide="ignore", invalid="ignore"):
            r[1:] = close[1:] / close[:-1] - 1.0
        hors = (close <= 0) | ~np.isfinite(r) | (r < -0.5) | (r > 1.0)
        hors[0] = False
        n_err = int(hors.sum())
        for i in np.where(hors)[0]:
            invalide[i] = True
            if i + 1 < len(close):
                invalide[i + 1] = True
        r[invalide] = 0.0
        r[~np.isfinite(r)] = 0.0
        self.r = r
        self.erreurs = n_err


def charger(actif, fin=DEV_FIN):
    """Charge ../donnees/<actif>.csv ; coupe PHYSIQUEMENT au-delà de `fin` (jamais de lecture au-delà)."""
    chemin = os.path.join(DONNEES, f"{actif}.csv")
    dates, close = [], []
    with open(chemin, encoding="utf-8", newline="") as f:
        for ligne in csv.DictReader(f):
            d = ligne["date"]
            if d > fin:
                break
            try:
                c = float(ligne["close"])
            except (TypeError, ValueError):
                continue
            dates.append(d)
            close.append(c)
    return Serie(actif, np.array(dates, dtype="datetime64[D]"), np.array(close, dtype=float), 0)


def fins_de_mois(dates):
    ym = dates.astype("datetime64[M]").astype(np.int64)
    return np.where(ym[:-1] != ym[1:])[0]


# ----------------------------------------------------------------------------------- positions
def ewma_var(r, com=60):
    a = 1.0 / (1.0 + com)
    v = np.zeros(len(r))
    v0 = float(np.var(r[1:21])) if len(r) > 21 else 1e-4
    cur = v0
    for i in range(len(r)):
        cur = (1 - a) * cur + a * r[i] * r[i]
        v[i] = cur
    return v


def composantes_tsmom(s, lookback=12):
    """Retourne (indices de fin de mois utilisés, signes, tailles) pour la candidate 1."""
    me = fins_de_mois(s.dates)
    var = ewma_var(s.r)
    idx, sg, sz = [], [], []
    for k in range(lookback, len(me)):
        i, j = me[k], me[k - lookback]
        if s.close[j] <= 0 or s.close[i] <= 0:
            continue
        sig = math.sqrt(var[i] * 252.0)
        taille = min(3.0, 0.10 / sig) if sig > 0 else 0.0
        idx.append(i)
        sg.append(float(np.sign(s.close[i] / s.close[j] - 1.0)))
        sz.append(taille)
    return me, np.array(idx, dtype=int), np.array(sg), np.array(sz)


def positions_mensuelles(n, me, idx_signal, valeurs):
    """Pose valeurs[k] de la clôture idx_signal[k] jusqu'à la fin de mois suivante (exclue)."""
    p = np.zeros(n)
    pos_me = {int(i): k for k, i in enumerate(me)}
    for i, v in zip(idx_signal, valeurs):
        k = pos_me[int(i)]
        fin = int(me[k + 1]) if k + 1 < len(me) else n
        p[int(i):fin] = v
    return p


def pos_tsmom(s, lookback=12):
    me, idx, sg, sz = composantes_tsmom(s, lookback)
    return positions_mensuelles(len(s.close), me, idx, sg * sz)


def composantes_sma(s, mois=10):
    me = fins_de_mois(s.dates)
    cm = s.close[me]
    idx, sig = [], []
    for k in range(mois - 1, len(me)):
        moy = cm[k - mois + 1:k + 1].mean()
        idx.append(me[k])
        sig.append(1.0 if cm[k] > moy else 0.0)
    return me, np.array(idx, dtype=int), np.array(sig)


def pos_sma(s, mois=10):
    me, idx, sig = composantes_sma(s, mois)
    return positions_mensuelles(len(s.close), me, idx, sig)


def fenetres_tom(dates, entree_avant=1, sortie_apres=3):
    """Liste (e, x) : entrée à la clôture de T-entree_avant, sortie à la clôture de T+sortie_apres (T = dernier jour de bourse du mois)."""
    ym = dates.astype("datetime64[M]").astype(np.int64)
    bornes = np.where(ym[:-1] != ym[1:])[0]      # dernier indice de chaque mois complet
    res = []
    for k in range(len(bornes) - 1):
        T = int(bornes[k])
        debut_suivant = T + 1
        fin_suivant = int(bornes[k + 1])
        e = T - entree_avant
        x = debut_suivant + sortie_apres - 1
        if e < 0 or x > fin_suivant:
            continue
        res.append((e, x))
    return res


def pos_tom(s, entree_avant=1, sortie_apres=3):
    p = np.zeros(len(s.close))
    for e, x in fenetres_tom(s.dates, entree_avant, sortie_apres):
        p[e:x] = 1.0
    return p


# ----------------------------------------------------------------------------------- rendements nets
def rendement_net(s, p, actif=None, m_spread=1.0, m_swap=1.0, detail=False):
    actif = actif or s.actif
    n = len(p)
    pp = np.concatenate([[0.0], p[:-1]])
    nuits = np.diff(s.jours, prepend=s.jours[0]).astype(float)
    brut = pp * s.r
    taux = np.where(pp > 0, SWAP_LONG[actif], SWAP_SHORT[actif])
    swap = taux * np.abs(pp) * nuits * m_swap
    spread = SPREAD_RT[actif] / 2.0 * np.abs(p - pp) * m_spread
    net = brut - swap - spread
    if detail:
        return net, brut, swap, spread
    return net


def episodes(p, brut, swap, spread):
    """PnL net par épisode de position (même signe, ininterrompu). Retourne la liste des PnL."""
    n = len(p)
    pnl = []
    cur = None
    sgn = 0.0
    pp = np.concatenate([[0.0], p[:-1]])
    for t in range(n):
        sp = np.sign(p[t])
        spp = np.sign(pp[t])
        if spp != 0:
            cur = (cur or 0.0) + brut[t] - swap[t] - spread[t]
        elif sp != 0:
            cur = (cur or 0.0) - spread[t]
        if sp != spp:   # fin d'épisode (retour à 0 ou inversion)
            if spp != 0 and cur is not None:
                pnl.append(cur)
                cur = None
            if sp != 0:
                cur = (cur or 0.0) - (spread[t] if spp != 0 else 0.0) * 0.0
        sgn = sp
    if cur is not None and sgn != 0:
        pnl.append(cur)
    return pnl


# ----------------------------------------------------------------------------------- portefeuille
def aligner(series_nets, series_obj):
    """Matrice (actifs × jours de l'union) NaN-remplie ; retourne (jours_union, matrice)."""
    union = np.unique(np.concatenate([s.jours for s in series_obj]))
    M = np.full((len(series_obj), len(union)), np.nan)
    for a, (s, net) in enumerate(zip(series_obj, series_nets)):
        M[a, np.searchsorted(union, s.jours)] = net
    return union, M


def portefeuille(M):
    with np.errstate(invalid="ignore"):
        return np.nanmean(M, axis=0)


def masque(union, debut, fin):
    d0 = np.datetime64(debut, "D").astype(np.int64)
    d1 = np.datetime64(fin, "D").astype(np.int64)
    return (union >= d0) & (union <= d1)


def sharpe(x):
    x = x[np.isfinite(x)]
    if len(x) < 30 or x.std(ddof=1) == 0:
        return float("nan")
    return float(x.mean() / x.std(ddof=1) * math.sqrt(252))


def stats(x):
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {"sharpe": float("nan"), "cagr": float("nan"), "maxdd": float("nan"), "jours": 0}
    eq = np.cumprod(1.0 + x)
    cagr = eq[-1] ** (252.0 / len(x)) - 1.0 if eq[-1] > 0 else -1.0
    dd = (eq / np.maximum.accumulate(eq) - 1.0).min()
    return {"sharpe": sharpe(x), "cagr": float(cagr), "maxdd": float(dd), "jours": int(len(x))}


def bootstrap_sharpe(x, blocs=21, tirages=2000, graine=12345):
    x = x[np.isfinite(x)]
    n = len(x)
    rng = np.random.default_rng(graine)
    nb = int(math.ceil(n / blocs))
    res = []
    fait = 0
    while fait < tirages:
        b = min(250, tirages - fait)
        starts = rng.integers(0, n, size=(b, nb))
        idx = (starts[:, :, None] + np.arange(blocs)[None, None, :]) % n
        ech = x[idx.reshape(b, -1)[:, :n]]
        m = ech.mean(axis=1)
        sd = ech.std(axis=1, ddof=1)
        res.append(m / sd * math.sqrt(252))
        fait += b
    res = np.concatenate(res)
    return {"p5": float(np.percentile(res, 5)), "p50": float(np.percentile(res, 50)),
            "p_inf0": float((res <= 0).mean())}


# ----------------------------------------------------------------------------------- candidate 5 (RSI(2))
def rsi_wilder(close, n=2):
    c = np.asarray(close, dtype=float)
    d = np.diff(c, prepend=c[0])
    g, l = np.maximum(d, 0.0), np.maximum(-d, 0.0)
    rsi = np.full(len(c), np.nan)
    if len(c) <= n:
        return rsi
    ag = np.zeros(len(c))
    al = np.zeros(len(c))
    ag[n], al[n] = g[1:n + 1].mean(), l[1:n + 1].mean()
    for i in range(n + 1, len(c)):
        ag[i] = (ag[i - 1] * (n - 1) + g[i]) / n
        al[i] = (al[i - 1] * (n - 1) + l[i]) / n
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = ag[n:] / al[n:]
        rsi[n:] = np.where(al[n:] == 0, 100.0, 100.0 - 100.0 / (1.0 + rs))
    return rsi


def sma(x, n):
    x = np.asarray(x, dtype=float)
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        c = np.cumsum(np.insert(x, 0, 0.0))
        out[n - 1:] = (c[n:] - c[:-n]) / n
    return out


def pos_rsi2(s, seuil=5.0, filtre=200, sortie=5):
    """Long à la clôture si RSI(2) < seuil (et clôture > SMA filtre) ; sortie à la clôture quand clôture > SMA sortie."""
    c = s.close
    rsi = rsi_wilder(c, 2)
    mf = sma(c, filtre) if filtre else None
    ms = sma(c, sortie)
    p = np.zeros(len(c))
    en = False
    for t in range(len(c)):
        if en:
            if c[t] > ms[t]:
                en = False
            else:
                p[t] = 1.0
        else:
            ok = bool(rsi[t] < seuil)
            if filtre:
                ok = ok and bool(c[t] > mf[t])
            if ok:
                en = True
                p[t] = 1.0
    return p


def trades_longs(p, brut, swap, spread):
    """[(entrée, sortie, pnl net)] ; PnL = gains/swap sur (e, x] moins spread à l'entrée et à la sortie. Trade ouvert en fin de série ignoré."""
    res, e = [], None
    for t in range(len(p)):
        if p[t] > 0 and (t == 0 or p[t - 1] == 0):
            e = t
        if e is not None and p[t] == 0 and t > 0 and p[t - 1] > 0:
            pnl = float((brut[e + 1:t + 1] - swap[e + 1:t + 1]).sum() - spread[e] - spread[t])
            res.append((e, t, pnl))
            e = None
    return res
