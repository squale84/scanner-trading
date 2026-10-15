"""CONTRÔLE VIERGE de la candidate 5 (01/10/2023 → 13/10/2026). Ouvert UNE SEULE FOIS : un verrou est posé avant tout calcul."""
import json
import math
import os
import sys
import time

import numpy as np

import lab

ICI = os.path.dirname(os.path.abspath(__file__))
VERROU = os.path.join(ICI, "controle_vierge_OUVERT.json")
if os.path.exists(VERROU):
    print("REFUSÉ : le contrôle vierge a déjà été ouvert (voir controle_vierge_OUVERT.json).")
    sys.exit(2)
with open(VERROU, "w", encoding="utf-8") as f:
    json.dump({"ouvert_le": time.strftime("%Y-%m-%d %H:%M"), "candidate": "5 RSI(2) long seul, RSI<5, SMA200, sortie SMA5",
               "fenetre": [lab.BLIND_DEBUT, lab.FIN_DONNEES]}, f, ensure_ascii=False, indent=2)

GRAINE = 20261016
M_SPREAD, M_SWAP = 2.0, 1.0
d0 = np.datetime64(lab.BLIND_DEBUT, "D")
d1 = np.datetime64(lab.FIN_DONNEES, "D")
rng = np.random.default_rng(GRAINE)


def pf(x):
    x = np.asarray(x)
    g, l = x[x > 0].sum(), -x[x < 0].sum()
    return float(g / l) if l > 0 else float("inf")


series = {a: lab.charger(a, lab.FIN_DONNEES) for a in lab.INDICES}
tous, par, durees, pre = [], {}, {}, {}
for a in lab.INDICES:
    s = series[a]
    p = lab.pos_rsi2(s, 5.0, 200, 5)
    net, brut, swap, spread = lab.rendement_net(s, p, a, M_SPREAD, M_SWAP, detail=True)
    tr = [t for t in lab.trades_longs(p, brut, swap, spread) if d0 <= s.dates[t[0]] <= d1]
    pn = [t[2] for t in tr]
    par[a] = {"n": len(pn), "moy_pb": float(np.mean(pn) * 1e4) if pn else None, "pf": pf(pn) if pn else None}
    tous += pn
    durees[a] = [t[1] - t[0] for t in tr]
    nuits = np.diff(s.jours, prepend=s.jours[0]).astype(float)
    cum = np.cumsum(s.r - lab.SWAP_LONG[a] * nuits)
    i0 = int(np.searchsorted(s.dates, d0))
    mf = lab.sma(s.close, 200)
    cand = np.where((s.close > mf) & (np.arange(len(s.close)) >= i0))[0]
    pre[a] = (cum, cand, lab.SPREAD_RT[a] * M_SPREAD, len(s.close))

res = {"fenetre": [lab.BLIND_DEBUT, lab.FIN_DONNEES], "n_trades": len(tous), "par_indice": par}
if tous:
    obs = float(np.mean(tous))
    moy = []
    for _ in range(1000):
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
    boot = np.asarray(tous)[rng.integers(0, len(tous), size=(2000, len(tous)))].mean(axis=1)
    res.update({"pf_net_x2": pf(tous), "moy_pb": obs * 1e4, "gagnants": float(np.mean(np.array(tous) > 0)),
                "pire_pb": float(np.min(tous) * 1e4),
                "placebo": {"p_valeur": float((moy >= obs).mean()), "p50_pb": float(np.percentile(moy, 50) * 1e4)},
                "bootstrap_p5_pb": float(np.percentile(boot, 5) * 1e4)})
    regle = res["pf_net_x2"] > 1.0 and obs > np.percentile(moy, 50)
    if len(tous) < 60:
        res["verdict"] = "NON CONCLUANT (moins de 60 trades)" + (" — résultat favorable" if regle else " — résultat défavorable")
    else:
        res["verdict"] = "CONFIRMÉE sur le contrôle vierge" if regle else "NON CONFIRMÉE sur le contrôle vierge"
else:
    res["verdict"] = "NON CONCLUANT (aucun trade)"
with open(os.path.join(ICI, "resultats_controle_vierge_c5.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False, default=lambda o: None if isinstance(o, float) and (math.isnan(o) or math.isinf(o)) else o)
print(json.dumps(res, ensure_ascii=False, indent=2))
