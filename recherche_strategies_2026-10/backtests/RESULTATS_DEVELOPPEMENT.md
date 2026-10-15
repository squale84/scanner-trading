# Résultats de la fenêtre de développement (01/01/1991 → 30/09/2023)

Exécution du 15/10/2026 avec `run_dev.py` et les règles de `PROTOCOLE_FIGE.md`. Coûts « ×2 » =
spread ×2, swap XTB actuel conservé. Valeurs complètes : `resultats_dev.json`.
**Le contrôle vierge n'a pas été ouvert** (aucune candidate n'a passé le développement).

## Verdict

| Candidate | Verdict | Règles échouées |
|---|---|---|
| 1. Tendance 12 mois, long/short | **REJETÉE** | R1 Sharpe, R2 actifs positifs, R4 bootstrap, R5 plateau |
| 2. Prix > SMA 10 mois, long/cash | **REJETÉE** | R1 Sharpe, R3 placebo, R4 bootstrap, R5 plateau |
| 3. Turn-of-the-month, indices | **REJETÉE** (de peu) | R3 t-stat mensuel 1,70 < 2 |

## Candidate 1 — Tendance 12 mois (9 actifs, vol cible 10 %)

| Coûts | Sharpe | CAGR | Drawdown max |
|---|---|---|---|
| Brut (aucun coût) | **+0,67** | +3,3 % | −11 % |
| Réel (spread ×1 + swap) | −0,06 | −0,4 % | −34 % |
| ×2 (spread ×2 + swap) | −0,06 | −0,4 % | −35 % |
| Swap ×2 (info) | −0,78 | −3,9 % | −74 % |

- Le signal existe (Sharpe brut 0,67, cohérent avec la littérature) ; **le financement XTB actuel
  l'annule** : spread négligeable (réel ≈ ×2), swap décisif.
- 378 trades, 26 % gagnants, PF 0,89. Net par actif : US100 +124 %, USDJPY +100 %, SPX500 +7 % ;
  XAUUSD −75 %, FR40 −58 %, USOIL −53 %, NATGAS −44 %, GER40 −30 %, EURUSD −35 % (3 actifs positifs sur 9).
- Plateau : lookback 10 mois −0,04 ; 14 mois −0,24 (net ×2).
- Placebo p = 0,00 (le placebo à signes aléatoires perd −0,88 de Sharpe en coûts) : le signal bat le
  hasard, mais pas le zéro.
- Bootstrap : 5e centile −0,34 ; P(Sharpe ≤ 0) = 63 %.

## Candidate 2 — Prix > SMA 10 mois, long ou cash (9 actifs, 1× sans levier)

| Coûts | Sharpe | CAGR | Drawdown max |
|---|---|---|---|
| Brut | **+0,72** | +5,7 % | −16 % |
| Réel | +0,08 | +0,3 % | −35 % |
| ×2 | +0,07 | +0,3 % | −35 % |
| Swap ×2 (info) | −0,56 | −4,8 % | −81 % |
| Acheter-et-garder, ×2 (comparateur) | 0,00 | −0,8 % | −66 % |

- 266 trades, 32 % gagnants, PF 1,13. Net par actif : US100 +719 %, SPX500 +54 %, GER40 +53 %, USDJPY +29 %,
  FR40 +11 % ; XAUUSD −78 %, EURUSD −21 %, USOIL −86 %, NATGAS −97 % (5 positifs sur 9).
- Le filtre réduit le drawdown (−35 % contre −66 %) mais le rendement net est ≈ 0.
- Placebo long/cash aléatoire de même exposition : p = 0,21 (non distinguable du hasard).
- Plateau : SMA 8 mois +0,05 ; 12 mois +0,10. Bootstrap : 5e centile −0,19 ; P(Sharpe ≤ 0) = 32 %.
- Acheter-et-garder net de swap perd presque tout (or −92 %, pétrole −97 %, gaz −99 %) : le swap long de
  8 à 15 %/an dépasse la hausse des actifs. Hypothèse prospective « coûts d'aujourd'hui sur 1991-2023 »,
  pénalisante pour les années de taux nuls.

## Candidate 3 — Turn-of-the-month, long seulement (SPX500, US100, GER40, FR40)

| Fenêtre | Fenêtres | Net moyen / mois | t (mensuel) |
|---|---|---|---|
| T−1 → T+3 (principal) | 1 568 | **+21,3 pb** | +1,70 |
| T−1 → T+2 (plateau) | 1 568 | +15,4 pb | +1,46 |
| T−1 → T+4 (plateau) | 1 568 | +17,5 pb | +1,33 |
| T−4 → T+3 (informatif) | 1 568 | +47,6 pb | +3,06 |

- Positif sur les 4 indices (SPX500 +10,8 pb, US100 +27,8, GER40 +27,3, FR40 +19,2 ; 53 à 59 % de
  fenêtres gagnantes). Placebo (fenêtres de 4 jours à date aléatoire) : **p = 0,003**.
- La règle R3 (t ≥ 2) échoue de peu : +21 pb par mois ≈ +2,6 %/an net, exposé environ 19 % du temps.
- La variante T−4 → T+3 (t 3,06) a été regardée après coup : elle n'est **pas** promue ; la promouvoir
  reviendrait à déplacer les règles après avoir vu les résultats. Le seul test propre qui lui reste est le
  contrôle vierge (≈ 36 fenêtres, moins de 60 trades : « non concluant » par construction du protocole).

## À retenir
1. Rien ne passe le protocole : aucun Pine à écrire pour l'instant.
2. Les signaux des candidates 1 et 2 sont réels en brut (Sharpe 0,7), mais **le swap des CFD XTB les
   consomme**. Ces stratégies sont adaptées à des instruments à financement faible (futures, ETF),
   pas à des CFD tenus plusieurs semaines.
3. Le turn-of-the-month est l'effet le plus proche du seuil : positif partout, bat le placebo, coût
   faible car détention de 4 jours ; il lui manque une confirmation statistique.
4. BTCUSD (informatif, 2011-2023) : tendance 12 mois Sharpe +0,61 net ×2, à ne pas surinterpréter
   (un actif, période de hausse exceptionnelle).
