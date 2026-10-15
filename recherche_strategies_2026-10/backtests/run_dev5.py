"""Candidate 5 (RSI(2) long seul, filtre SMA 200) sur la fenêtre de DÉVELOPPEMENT uniquement (voir PROTOCOLE_FIGE.md, addendum)."""
import json
import math
import os

import numpy as np

import lab

ICI = os.path.dirname(os.path.abspath(__file__))
GRAINE = 20261015
NB_PLACEBO = 1000
NB_BOOT = 2000
DEBUT, FIN = lab.DEBUT_EVAL_DEV, lab.DEV_FIN
M_SPREAD, M_SWAP = 2.0, 1.0   # coûts ×2 du protocole

CONFIGS = {
    "RSI<5 SMA200 (principal)": (5.0, 200),
    "RSI<4 (plateau)": (4.0, 200),
    "RSI<6 (plateau)": (6.0, 200),
    "SMA160 (plateau)": (5.0, 160),
    "SMA240 (plateau)": (5.0, 240),
    "RSI<10 (info, valeur d'origine)": (10.0, 200),
    "sans filtre SMA200 (info)": (5.0, None),
}


def pf(pnls):
    pnls = np.asarray(pnls, dtype=float)
    g, p = pnls[pnls > 0].sum(), -pnls[pnls < 0].sum()
    return float(g / p) if p > 0 else float("inf")


def executer(series, seuil, filtre, m_spread=M_SPREAD, m_swap=M_SWAP):
    d0 = np.datetime64(DEBUT, "D")
    par, tous, nets, durees, exposition = {}, [], [], {}, {}
    for a in lab.INDICES:
        s = series[a]
        p = lab.pos_rsi2(s, seuil, filtre, 5)
        net, brut, swap, spread = lab.rendement_net(s, p, a, m_spread, m_swap, detail=True)
        tr = [t for t in lab.trades_longs(p, brut, swap, spread) if s.dates[t[0]] >= d0]
        pn = [t[2] for t in tr]
        par[a] = {"n": len(tr), "moy_pb": float(np.mean(pn) * 1e4) if pn else float("nan"),
                  "gagnants": float(np.mean(np.array(pn) > 0)) if pn else float("nan"),
                  "pf": pf(pn) if pn else float("nan"),
                  "duree_moy": float(np.mean([t[1] - t[0] for t in tr])) if tr else float("nan")}
        tous += pn
        durees[a] = [t[1] - t[0] for t in tr]
        nets.append(net)
        exposition[a] = float((p[np.searchsorted(s.dates, d0):] > 0).mean())
    union, M = lab.aligner(nets, [series[a] for a in lab.INDICES])
    m = lab.masque(union, DEBUT, FIN)
    port = lab.portefeuille(M)[m]
    return {"par_indice": par, "n": len(tous), "pf": pf(tous) if tous else float("nan"),
            "moy_pb": float(np.mean(tous) * 1e4) if tous else float("nan"),
            "gagnants": float(np.mean(np.array(tous) > 0)) if tous else float("nan"),
            "sharpe_port": lab.sharpe(port), "stats_port": lab.stats(port), "exposition": exposition,
            "durees": durees, "pnl": tous}


def placebo(series, seuil, filtre, durees, obs_moy, rng):
    d0 = np.datetime64(DEBUT, "D")
    pre = {}
    for a in lab.INDICES:
        s = series[a]
        nuits = np.diff(s.jours, prepend=s.jours[0]).astype(float)
        cum = np.cumsum(s.r - lab.SWAP_LONG[a] * nuits)
        i0 = int(np.searchsorted(s.dates, d0))
        if filtre:
            mf = lab.sma(s.close, filtre)
            cand = np.where((s.close > mf) & (np.arange(len(s.close)) >= i0))[0]
        else:
            cand = np.arange(i0, len(s.close))
        pre[a] = (cum, cand, lab.SPREAD_RT[a] * M_SPREAD, len(s.close))
    moy = []
    for _ in range(NB_PLACEBO):
        vals = []
        for a in lab.INDICES:
            d = durees[a]
            if not d:
                continue
            cum, cand, sp, n = pre[a]
            e = rng.choice(cand, size=len(d))
            x = np.minimum(e + rng.choice(d, size=len(d)), n - 1)
            vals += list(cum[x] - cum[e] - sp)
        moy.append(np.mean(vals))
    moy = np.array(moy)
    return {"obs_pb": obs_moy * 1e4, "p_valeur": float((moy >= obs_moy).mean()),
            "p50_pb": float(np.percentile(moy, 50) * 1e4), "p95_pb": float(np.percentile(moy, 95) * 1e4)}


def bootstrap(pnl, rng):
    x = np.asarray(pnl)
    m = x[rng.integers(0, len(x), size=(NB_BOOT, len(x)))].mean(axis=1)
    return {"p5_pb": float(np.percentile(m, 5) * 1e4), "p50_pb": float(np.percentile(m, 50) * 1e4)}


def main():
    rng = np.random.default_rng(GRAINE)
    series = {a: lab.charger(a, lab.DEV_FIN) for a in lab.INDICES}
    for a, s in series.items():
        assert str(s.dates.max()) <= lab.DEV_FIN
    res = {"fenetre": [DEBUT, FIN], "configs": {}}
    for nom, (seuil, filtre) in CONFIGS.items():
        e = executer(series, seuil, filtre)
        e2 = {k: v for k, v in e.items() if k not in ("durees", "pnl")}
        if nom.startswith("RSI<5 SMA200"):
            e2["placebo"] = placebo(series, seuil, filtre, e["durees"], e["moy_pb"] / 1e4, rng)
            e2["bootstrap"] = bootstrap(e["pnl"], rng)
            for lbl, (ms, mw) in lab.SCENARIOS.items():
                r = executer(series, seuil, filtre, ms, mw)
                e2.setdefault("scenarios", {})[lbl] = {"pf": r["pf"], "moy_pb": r["moy_pb"], "n": r["n"], "sharpe_port": r["sharpe_port"]}
        res["configs"][nom] = e2
    c = res["configs"]
    p0 = c["RSI<5 SMA200 (principal)"]
    voisins = [c[k]["pf"] for k in ("RSI<4 (plateau)", "RSI<6 (plateau)", "SMA160 (plateau)", "SMA240 (plateau)")]
    regles = {
        "R1_PF>=1.2": p0["pf"] >= 1.2,
        "R2_indices_positifs>=3": sum(1 for a in lab.INDICES if p0["par_indice"][a]["moy_pb"] > 0) >= 3,
        "R3_placebo_p<=0.05": p0["placebo"]["p_valeur"] <= 0.05,
        "R4_bootstrap_p5>0": p0["bootstrap"]["p5_pb"] > 0,
        "R5_plateau_PF>=1.1": all(v >= 1.1 for v in voisins),
        "R6_trades>=100": p0["n"] >= 100,
    }
    res["regles"] = regles
    res["voisins_pf"] = voisins
    echec = [k for k, v in regles.items() if not v and not k.startswith("R6")]
    res["verdict"] = "REJETÉE" if echec else ("PASSE le développement" if regles["R6_trades>=100"] else "NON CONCLUANT (taille)")
    with open(os.path.join(ICI, "resultats_dev_c5.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False,
                  default=lambda o: None if isinstance(o, float) and (math.isnan(o) or math.isinf(o)) else o)
    print(res["verdict"])


if __name__ == "__main__":
    main()
