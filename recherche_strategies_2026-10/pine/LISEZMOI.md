# RSI(2) long + SMA 200 — V0.1

Fichier : `rsi2_long_sma200_V0.1.pine`. **Non compilé** : à coller dans l'éditeur Pine de TradingView, qui est
seul juge de la compilation (règle de `AGENTS.md`). Ne pas le commiter avant validation réelle.

## Comment le vérifier dans TradingView
1. Graphique **1 jour**. Ajouter la stratégie, cocher « Limiter le test à une période » : début 01/01/1991,
   fin 30/09/2023 (valeurs par défaut) pour retrouver la fenêtre de développement du moteur Python.
2. Sur chacun des 4 indices, les nombres de trades doivent être proches de ceux du moteur (à quelques
   unités près : amorçage du RSI, jours fériés du graphique).

| Symbole | Trades attendus (1991 → 30/09/2023) | Gain net moyen par trade* | PF net* |
|---|---|---|---|
| SP:SPX | 141 | +56 pb | 2,70 |
| NASDAQ:NDX | 133 | +89 pb | 2,95 |
| XETR:DAX | 113 | +34 pb | 1,51 |
| TVC:CAC40 | 122 | +69 pb | 2,79 |

\* Moteur Python, coûts « ×2 » : spread ×2 **et swap XTB actuel inclus**. TradingView n'applique pas le
swap : attendre un gain par trade supérieur d'environ 8 pb (swap ≈ 2,3 pb par nuit × 3,5 nuits) et une
commission de 0,02 % par côté (≈ 4 pb par trade) un peu plus sévère que le spread ×2 du moteur.

## Ce que vaut cette stratégie (résumé des résultats, détail dans `../backtests/`)
- Développement 1991 → 09/2023 : 509 trades, PF 2,39 net ×2, 77 % gagnants, placebo p = 0,000.
- **Mais une décroissance nette** : PF 3,57 (1991-2007), 1,75 (2008-2016), 1,46 (2017-2023).
- Contrôle vierge 10/2023 → 10/2026 (ouvert une seule fois) : 60 trades, PF 2,52, +57 pb par trade,
  placebo p = 0,003. FR40 négatif (10 trades, −130 pb).
- Aucun stop : pire trade −17,5 % du nominal (2008-2016), −8,7 % sur le contrôle.
- Exposition de 5 à 6 % du temps : c'est une stratégie de petits rendements sur capital peu employé.
