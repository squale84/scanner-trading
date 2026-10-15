"""Tests du moteur sur données SYNTHÉTIQUES uniquement (aucun CSV réel lu). Script autonome : python tests_lab.py"""
import math
import sys

import numpy as np

import lab


def serie_synth(n=2600, mu=0.0, sig=0.01, graine=1, actif="SPX500", debut="2010-01-04"):
    rng = np.random.default_rng(graine)
    # jours ouvrés
    d = np.arange(np.datetime64(debut, "D"), np.datetime64(debut, "D") + int(n * 1.5))
    d = d[(d.astype("datetime64[D]").astype(np.int64) + 4) % 7 < 5][:n]   # lundi..vendredi (1970-01-01 = jeudi)
    r = rng.normal(mu, sig, n)
    c = 100 * np.cumprod(1 + r)
    return lab.Serie(actif, d.astype("datetime64[D]"), c, 0)


def ok(cond, msg):
    print(("OK   " if cond else "ECHEC ") + msg)
    if not cond:
        ok.echecs += 1


ok.echecs = 0

# 1. position nulle -> rendement net nul
s = serie_synth()
net = lab.rendement_net(s, np.zeros(len(s.close)))
ok(np.allclose(net, 0), "position nulle -> rendement nul")

# 2. long permanent : le coût de swap sur n nuits = taux * nuits (spread d'entrée à part)
p = np.ones(len(s.close))
net, brut, swap, spread = lab.rendement_net(s, p, detail=True)
nuits_totales = (s.jours[-1] - s.jours[0])
attendu = lab.SWAP_LONG["SPX500"] * (nuits_totales - (s.jours[1] - s.jours[0]) * 0)   # entrée à t=0 : détention sur (0, n-1]
ok(abs(swap.sum() - lab.SWAP_LONG["SPX500"] * nuits_totales) < 1e-9, "swap long = taux × nuits calendaires")
ok(abs(spread.sum() - lab.SPREAD_RT["SPX500"] / 2) < 1e-12, "spread payé une fois à l'entrée (demi-spread)")

# 3. coûts : brut >= réel >= x2
p = lab.pos_tsmom(s)
t = {k: lab.rendement_net(s, p, m_spread=m[0], m_swap=m[1]).sum() for k, m in lab.SCENARIOS.items()}
ok(t["brut"] >= t["reel"] >= t["x2"], "monotonie des coûts brut >= réel >= ×2")

# 4. TSMOM sur tendance haussière forte : signe positif, Sharpe brut positif
s_up = serie_synth(mu=0.0006, sig=0.008, graine=3)
p_up = lab.pos_tsmom(s_up)
apres = p_up[300:]   # après l'échauffement de 12 mois
ok((apres > 0).mean() > 0.9 and (apres < 0).mean() < 0.1, "TSMOM : essentiellement long sur tendance haussière")
net_up = lab.rendement_net(s_up, p_up, m_spread=0, m_swap=0)
ok(lab.sharpe(net_up) > 0.5, "TSMOM : Sharpe brut > 0,5 sur tendance synthétique")

# 5. pas d'anticipation : changer le futur ne change pas la position passée
s2 = serie_synth(graine=7)
p_a = lab.pos_tsmom(s2)
c2 = s2.close.copy()
c2[1800:] *= 3.0       # modification du futur
s3 = lab.Serie("SPX500", s2.dates, c2, 0)
p_b = lab.pos_tsmom(s3)
ok(np.array_equal(p_a[:1799], p_b[:1799]), "TSMOM sans look-ahead : positions avant t=1800 inchangées")
p_a = lab.pos_sma(s2)
p_b = lab.pos_sma(s3)
ok(np.array_equal(p_a[:1799], p_b[:1799]), "SMA sans look-ahead")

# 6. TOM : indices d'entrée / sortie
d = np.array(["2020-01-29", "2020-01-30", "2020-01-31", "2020-02-03", "2020-02-04", "2020-02-05", "2020-02-06",
              "2020-02-27", "2020-02-28", "2020-03-02", "2020-03-03", "2020-03-04", "2020-03-05", "2020-03-31", "2020-04-01"],
             dtype="datetime64[D]")
w = lab.fenetres_tom(d, 1, 3)
# fin janvier = idx 2 ; entrée idx 1 (30/01) ; sortie = 3e jour de bourse de février = idx 5 (05/02)
ok((1, 5) in w, "TOM : janvier -> entrée 30/01, sortie 05/02")
# fin février = idx 8 ; entrée idx 7 ; sortie = 3e jour de mars = idx 11 (04/03)
ok((7, 11) in w, "TOM : février -> entrée 27/02, sortie 04/03")

# 7. épisodes : un seul épisode long de 3 jours
s4 = serie_synth(n=60, graine=2)
p = np.zeros(60)
p[10:13] = 1.0
net, brut, swap, spread = lab.rendement_net(s4, p, detail=True)
ep = lab.episodes(p, brut, swap, spread)
ok(len(ep) == 1 and abs(ep[0] - net[10:14].sum()) < 1e-9, "épisodes : PnL = somme des nets entrée..sortie")

# 8. règle d'erreur de données : prix négatif neutralisé
c = np.array([10.0, 10.5, -3.0, 10.2, 10.3, 10.4])
d = np.arange(np.datetime64("2020-04-15", "D"), np.datetime64("2020-04-15", "D") + 6)
s5 = lab.Serie("USOIL", d, c, 0)
ok(s5.r[2] == 0 and s5.r[3] == 0 and s5.erreurs >= 1, "données : prix négatif -> rendements neutralisés")

# 9. bootstrap : bruit pur -> Sharpe médian proche de 0
x = np.random.default_rng(5).normal(0, 0.01, 4000)
b = lab.bootstrap_sharpe(x, tirages=400)
ok(abs(b["p50"] - lab.sharpe(x)) < 0.15 and b["p5"] < b["p50"], "bootstrap : médiane ~ Sharpe de l'échantillon, p5 en dessous")
# bruit pur de moyenne nulle exacte : la médiane doit être proche de 0
x0 = x - x.mean()
b0 = lab.bootstrap_sharpe(x0, tirages=400)
ok(abs(b0["p50"]) < 0.15 and b0["p5"] < 0, "bootstrap : moyenne nulle -> médiane ~ 0 et p5 < 0")


# 10. RSI(2) : série strictement haussière -> 100 ; strictement baissière -> 0
c_up = np.arange(1.0, 50.0)
ok(abs(lab.rsi_wilder(c_up, 2)[-1] - 100.0) < 1e-9, "RSI(2) = 100 sur série haussière")
ok(abs(lab.rsi_wilder(c_up[::-1].copy(), 2)[-1]) < 1e-9, "RSI(2) = 0 sur série baissière")

# 11. SMA
ok(abs(lab.sma(np.array([1.0, 2.0, 3.0, 4.0]), 2)[-1] - 3.5) < 1e-12 and np.isnan(lab.sma(np.array([1.0, 2.0]), 3)).all(), "SMA correcte")

# 12. stratégie RSI(2) : tendance haussière, un trou brutal -> entrée ; sortie quand clôture > SMA5 ; pas de look-ahead
base = 100 * np.cumprod(1 + np.full(400, 0.002))
base[300] *= 0.93
base[301] *= 0.97 / 0.93 if False else 1.0
d = np.arange(np.datetime64("2015-01-05", "D"), np.datetime64("2015-01-05", "D") + np.timedelta64(700, "D"))
d = d[(d.astype("datetime64[D]").astype(np.int64) + 4) % 7 < 5][:400]
s6 = lab.Serie("SPX500", d.astype("datetime64[D]"), base, 0)
p6 = lab.pos_rsi2(s6, 5.0, 200, 5)
ok(p6[300] == 1.0 and p6[:300].sum() == 0, "RSI(2) : entrée sur le trou brutal, aucune avant")
x = np.where((p6[300:] == 0))[0]
ok(len(x) > 0 and base[300 + x[0]] > lab.sma(base, 5)[300 + x[0]], "RSI(2) : sortie quand clôture > SMA 5")
base2 = base.copy(); base2[350:] *= 2.0
p6b = lab.pos_rsi2(lab.Serie("SPX500", s6.dates, base2, 0), 5.0, 200, 5)
ok(np.array_equal(p6[:349], p6b[:349]), "RSI(2) sans look-ahead")
net6, br6, sw6, sp6 = lab.rendement_net(s6, p6, detail=True)
tr6 = lab.trades_longs(p6, br6, sw6, sp6)
ok(len(tr6) >= 1 and tr6[0][0] == 300, "trades_longs : première entrée au jour 300")

print("ECHECS :", ok.echecs)
sys.exit(1 if ok.echecs else 0)
