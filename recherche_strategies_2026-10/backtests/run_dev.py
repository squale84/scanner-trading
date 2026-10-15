"""Exécution sur la fenêtre de DÉVELOPPEMENT (jusqu'au 30/09/2023 seulement). Applique les règles du PROTOCOLE_FIGE.md.
Écrit resultats_dev.json et complète JOURNAL_DES_ESSAIS.md. Ne lit JAMAIS au-delà de DEV_FIN.
"""
import json
import math
import os
import time

import numpy as np

import lab

ICI = os.path.dirname(os.path.abspath(__file__))
NB_PLACEBO = 1000
NB_BOOT = 2000
GRAINE = 20261014

JOURNAL_ENTETE = """# Journal des essais

Chaque configuration exécutée est consignée ici (N = nombre d'essais déclaré). Rien n'est retiré.

## Essais déclarés avant exécution (14/10/2026)
| # | Candidate | Configuration | Statut |
|---|---|---|---|
| 1 | 1 Tendance | lookback 12 mois (principal) | principal |
| 2 | 1 Tendance | lookback 10 mois | plateau |
| 3 | 1 Tendance | lookback 14 mois | plateau |
| 4 | 2 SMA | SMA 10 mois (principal) | principal |
| 5 | 2 SMA | SMA 8 mois | plateau |
| 6 | 2 SMA | SMA 12 mois | plateau |
| 7 | 3 TOM | T-1 -> T+3 (principal) | principal |
| 8 | 3 TOM | T-1 -> T+2 | plateau |
| 9 | 3 TOM | T-1 -> T+4 | plateau |
| 10 | 3 TOM | T-4 -> T+3 | informatif |

N = 10 (seuil « t >= 3 » du protocole non déclenché : N < 20). BTCUSD calculé à titre informatif sur
les mêmes configurations, sans compter comme essai.

"""


def charger_tout():
    series = {a: lab.charger(a, lab.DEV_FIN) for a in lab.UNIVERS + lab.INFO}
    for a, s in series.items():
        assert str(s.dates.max()) <= lab.DEV_FIN, f"{a}: données au-delà du développement"
    return series


def matrice(series, actifs, positions, m_spread, m_swap):
    objs = [series[a] for a in actifs]
    nets = [lab.rendement_net(series[a], positions[a], a, m_spread, m_swap) for a in actifs]
    return lab.aligner(nets, objs)


def evaluer_portefeuille(series, actifs, positions, debut, fin):
    sortie = {}
    for nom, (ms, mw) in lab.SCENARIOS.items():
        union, M = matrice(series, actifs, positions, ms, mw)
        m = lab.masque(union, debut, fin)
        port = lab.portefeuille(M)[m]
        sortie[nom] = lab.stats(port)
        if nom == "x2":
            sortie["_port_x2"] = port
            # total net par actif sur la fenêtre
            tot = {}
            for a, ligne in zip(actifs, M):
                x = ligne[m]
                x = x[np.isfinite(x)]
                tot[a] = float(np.prod(1 + x) - 1) if len(x) else float("nan")
            sortie["_total_actif_x2"] = tot
    return sortie


def trades_agreges(series, actifs, positions, debut, fin, m_spread=2.0, m_swap=1.0):
    pnl = []
    for a in actifs:
        s = series[a]
        i0 = int(np.searchsorted(s.dates.astype("datetime64[D]").astype(np.int64), np.datetime64(debut, "D").astype(np.int64)))
        net, brut, swap, spread = lab.rendement_net(s, positions[a], a, m_spread, m_swap, detail=True)
        pnl += lab.episodes(positions[a][i0:], brut[i0:], swap[i0:], spread[i0:])
    pnl = np.array(pnl)
    if len(pnl) == 0:
        return {"n": 0, "win": float("nan"), "pf": float("nan")}
    g, p = pnl[pnl > 0].sum(), -pnl[pnl < 0].sum()
    return {"n": int(len(pnl)), "win": float((pnl > 0).mean()), "pf": float(g / p) if p > 0 else float("inf")}


# ------------------------------------------------------------------------- candidates 1 et 2
def positions_cand(series, actifs, fabrique):
    return {a: fabrique(series[a]) for a in actifs}


def placebo_signes(series, actifs, composantes, tirages, debut, fin, rng, bernoulli=None):
    """Distribution du Sharpe portefeuille (coûts x2) avec signaux mensuels aléatoires."""
    objs = [series[a] for a in actifs]
    res = []
    for _ in range(tirages):
        nets = []
        for a in actifs:
            s = series[a]
            comp = composantes[a]
            me, idx = comp[0], comp[1]
            if bernoulli is None:
                sz = comp[3]
                signes = rng.choice([-1.0, 1.0], size=len(idx)) * sz
            else:
                signes = (rng.random(len(idx)) < bernoulli[a]).astype(float)
            p = lab.positions_mensuelles(len(s.close), me, idx, signes)
            nets.append(lab.rendement_net(s, p, a, 2.0, 1.0))
        union, M = lab.aligner(nets, objs)
        m = lab.masque(union, debut, fin)
        res.append(lab.sharpe(lab.portefeuille(M)[m]))
    return np.array(res)


def candidate_1_2(nom, series, actifs, fabrique, parametres, comp_fn, bern, debut, fin, rng):
    out = {"parametres": {}}
    principal = parametres[0]
    for prm in parametres:
        pos = positions_cand(series, actifs, lambda s, prm=prm: fabrique(s, prm))
        ev = evaluer_portefeuille(series, actifs, pos, debut, fin)
        tr = trades_agreges(series, actifs, pos, debut, fin)
        out["parametres"][str(prm)] = {
            "stats": {k: ev[k] for k in lab.SCENARIOS}, "total_actif_x2": ev["_total_actif_x2"], "trades_x2": tr}
        if prm == principal:
            port = ev["_port_x2"]
            out["bootstrap_x2"] = lab.bootstrap_sharpe(port, tirages=NB_BOOT, graine=GRAINE)
            comp = {a: comp_fn(series[a], prm) for a in actifs}
            bern_a = None
            if bern:
                bern_a = {a: float(comp[a][2].mean()) for a in actifs}
            pl = placebo_signes(series, actifs, comp, NB_PLACEBO, debut, fin, rng, bern_a)
            obs = ev["x2"]["sharpe"]
            out["placebo"] = {"sharpe_obs": obs, "p_valeur": float((pl >= obs).mean()),
                              "p50": float(np.nanpercentile(pl, 50)), "p95": float(np.nanpercentile(pl, 95))}
    return out


def regles_cand_1_2(out, parametres):
    p0 = out["parametres"][str(parametres[0])]
    sh = p0["stats"]["x2"]["sharpe"]
    positifs = sum(1 for v in p0["total_actif_x2"].values() if v > 0)
    voisins = [out["parametres"][str(p)]["stats"]["x2"]["sharpe"] for p in parametres[1:]]
    r = {
        "R1_sharpe>=0.30": sh >= 0.30,
        "R2_actifs_positifs>=5": positifs >= 5,
        "R3_placebo_p<=0.05": out["placebo"]["p_valeur"] <= 0.05,
        "R4_bootstrap_p5>0": out["bootstrap_x2"]["p5"] > 0,
        "R5_plateau_voisins>=0.15": all(v >= 0.15 for v in voisins),
    }
    r["R6_trades>=100"] = p0["trades_x2"]["n"] >= 100
    return r, {"sharpe_x2": sh, "actifs_positifs": positifs, "voisins_sharpe_x2": voisins}


# ------------------------------------------------------------------------- candidate 3
def net_fenetre(s, e, x, a, ms=2.0, mw=1.0):
    p = np.zeros(len(s.close))
    p[e:x] = 1.0
    net = lab.rendement_net(s, p, a, ms, mw)
    return float(net[e:x + 1].sum())


def candidate_3(series, debut, fin, rng):
    out = {"configs": {}}
    cfgs = {"T-1->T+3": (1, 3), "T-1->T+2": (1, 2), "T-1->T+4": (1, 4), "T-4->T+3": (4, 3)}
    d0 = np.datetime64(debut, "D")
    d1 = np.datetime64(fin, "D")
    for nom, (k, sa) in cfgs.items():
        par_indice, mensuel = {}, {}
        n_fen = 0
        for a in lab.INDICES:
            s = series[a]
            vals = []
            for e, x in lab.fenetres_tom(s.dates, k, sa):
                if s.dates[x] < d0 or s.dates[e] > d1:
                    continue
                v = net_fenetre(s, e, x, a)
                vals.append(v)
                ym = int(s.dates[x].astype("datetime64[M]").astype(np.int64))
                mensuel.setdefault(ym, []).append(v)
            par_indice[a] = {"n": len(vals), "moyenne_net": float(np.mean(vals)) if vals else float("nan"),
                             "positifs": float(np.mean(np.array(vals) > 0)) if vals else float("nan")}
            n_fen += len(vals)
        serie_m = np.array([np.mean(v) for _, v in sorted(mensuel.items())])
        t = float(serie_m.mean() / (serie_m.std(ddof=1) / math.sqrt(len(serie_m)))) if len(serie_m) > 2 else float("nan")
        out["configs"][nom] = {"par_indice": par_indice, "n_fenetres": n_fen, "t_mensuel": t,
                               "moyenne_mensuelle_net": float(serie_m.mean()), "nb_mois": int(len(serie_m))}
        if nom == "T-1->T+3":
            # placebo : fenêtres de même longueur à date aléatoire
            obs = float(np.mean([par_indice[a]["moyenne_net"] for a in lab.INDICES]))
            moy = []
            for _ in range(NB_PLACEBO):
                vals = []
                for a in lab.INDICES:
                    s = series[a]
                    wins = [w for w in lab.fenetres_tom(s.dates, k, sa) if s.dates[w[1]] >= d0 and s.dates[w[0]] <= d1]
                    if not wins:
                        continue
                    L = int(np.median([x - e for e, x in wins]))
                    lo = int(np.searchsorted(s.dates, d0))
                    hi = int(np.searchsorted(s.dates, d1, side="right")) - L - 1
                    starts = rng.integers(lo, hi, size=len(wins))
                    vals.append(np.mean([net_fenetre(s, int(e), int(e) + L, a) for e in starts]))
                moy.append(np.mean(vals))
            moy = np.array(moy)
            out["placebo"] = {"obs": obs, "p_valeur": float((moy >= obs).mean()),
                              "p50": float(np.percentile(moy, 50)), "p95": float(np.percentile(moy, 95))}
    return out


def regles_cand_3(out):
    c = out["configs"]["T-1->T+3"]
    pos = sum(1 for a in lab.INDICES if c["par_indice"][a]["moyenne_net"] > 0)
    r = {
        "R1_indices_positifs>=3": pos >= 3,
        "R2_placebo_p<=0.05": out["placebo"]["p_valeur"] <= 0.05,
        "R3_t_mensuel>=2": c["t_mensuel"] >= 2,
        "R4_plateau_T+2_et_T+4>0": all(out["configs"][n]["moyenne_mensuelle_net"] > 0 for n in ("T-1->T+2", "T-1->T+4")),
        "R5_fenetres>=100": c["n_fenetres"] >= 100,
    }
    return r, {"indices_positifs": pos, "t_mensuel": c["t_mensuel"], "moyenne_mensuelle_net": c["moyenne_mensuelle_net"]}


# ------------------------------------------------------------------------- principal
def verdict(regles):
    if not all(v for k, v in regles.items() if not k.startswith("R6") and not k.startswith("R5_fen")):
        return "REJETÉE"
    taille = regles.get("R6_trades>=100", regles.get("R5_fenetres>=100"))
    return "PASSE le développement" if taille else "NON CONCLUANT (taille)"


def main():
    t0 = time.time()
    rng = np.random.default_rng(GRAINE)
    series = charger_tout()
    debut, fin = lab.DEBUT_EVAL_DEV, lab.DEV_FIN
    resultat = {"fenetre": [debut, fin], "erreurs_donnees": {a: s.erreurs for a, s in series.items()}}

    # candidate 1
    prm1 = [12, 10, 14]
    c1 = candidate_1_2("tendance", series, lab.UNIVERS, lambda s, m: lab.pos_tsmom(s, m), prm1,
                       lambda s, m: lab.composantes_tsmom(s, m), False, debut, fin, rng)
    r1, d1 = regles_cand_1_2(c1, prm1)
    resultat["candidate_1"] = {"details": c1, "regles": r1, "mesures": d1, "verdict": verdict(r1)}
    # information : BTC
    pos_btc = {"BTCUSD": lab.pos_tsmom(series["BTCUSD"], 12)}
    ev = evaluer_portefeuille(series, ["BTCUSD"], pos_btc, debut, fin)
    resultat["candidate_1"]["btc_info_sharpe_x2"] = ev["x2"]["sharpe"]

    # candidate 2
    prm2 = [10, 8, 12]
    c2 = candidate_1_2("sma", series, lab.UNIVERS, lambda s, m: lab.pos_sma(s, m), prm2,
                       lambda s, m: lab.composantes_sma(s, m), True, debut, fin, rng)
    r2, d2 = regles_cand_1_2(c2, prm2)
    resultat["candidate_2"] = {"details": c2, "regles": r2, "mesures": d2, "verdict": verdict(r2)}
    # comparateur acheter-et-garder
    bh = {a: np.concatenate([[0.0], np.ones(len(series[a].close) - 1)]) for a in lab.UNIVERS}
    evbh = evaluer_portefeuille(series, lab.UNIVERS, bh, debut, fin)
    resultat["candidate_2"]["achat_et_garde_x2"] = evbh["x2"]
    resultat["candidate_2"]["achat_et_garde_total_actif"] = evbh["_total_actif_x2"]

    # candidate 3
    c3 = candidate_3(series, debut, fin, rng)
    r3, d3 = regles_cand_3(c3)
    resultat["candidate_3"] = {"details": c3, "regles": r3, "mesures": d3, "verdict": verdict(r3)}

    resultat["duree_s"] = round(time.time() - t0, 1)
    chemin = os.path.join(ICI, "resultats_dev.json")
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(resultat, f, indent=2, ensure_ascii=False, default=lambda o: None if isinstance(o, float) and math.isnan(o) else o)
    print(json.dumps({k: resultat[k]["verdict"] for k in ("candidate_1", "candidate_2", "candidate_3")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
