---
name: audit-journal
description: Audit du journal de trades du scanner — rapprochement des entrées et sorties, expirations, sorties orphelines, calcul du R, win rate et profit factor. À utiliser seulement quand l'utilisateur demande de vérifier le journal, le bilan ou les statistiques de trading du dashboard.
---

# Audit du journal

**Lecture seule.** Aucune écriture dans Neon, aucun secret affiché (lire `DATABASE_URL` depuis `.env` via `storage.py`, jamais l'imprimer).

## Sources de vérité (à relire à chaque audit, les chiffres changent)
- Lignes brutes : table `journal_rows` (Neon), exposée par `GET /api/journal`. Chaque ligne a `kind` = `entry` ou `exit`.
- Calcul du R à la sortie : `_compute_r_multiple`, `_r_at_price`, `_exit_price`, `_exit_row` dans `server.py`.
- Appariement et affichage : `buildJournalTrades`, `resultCellHtml`, `statusCellHtml`, `updateJournalStats` dans `index.html`.

## Règles métier
- Un trade commence à l'alerte d'entrée. Une entrée + la sortie suivante du **même actif** = un trade.
- `TP_HIT` / `SL_HIT` : R au niveau touché. `EXPIRED` (30 bougies M5) : **clôture au prix de la 30e bougie**, R calculé à ce prix ; il compte dans le bilan et le profit factor comme n'importe quel trade.
- R > 0 gagnant, R < 0 perdant, R = 0 nul.
- `REPLACED` (nouvelle entrée avant la sortie) : pas de R.
- Deux cas distincts, à ne pas confondre :
  - **Prix de sortie non enregistré** (anciennes lignes) mais **R enregistré** : afficher « non enregistré » pour le prix ; le trade **reste** dans le win rate et le profit factor avec son R.
  - **Résultat en R indisponible** (aucun R calculable, par exemple une sortie orpheline sans entrée connue) : afficher « résultat indisponible », lister à part, **exclure** du bilan.
- Ne jamais inventer ni déduire un prix ou un R manquant.

## Calculs
- Win rate = gagnants / trades avec R.
- Profit factor = somme des R positifs / |somme des R négatifs|.
- Ventiler si utile par actif, session d'entrée, qualité, type de sortie, version du script (`version`).
- Recouper : somme des R des lignes de trade = R cumulé affiché par le dashboard (à l'arrondi près).

## Compte rendu
En français : nombre de trades, gagnants / perdants / nuls, orphelines, sorties sans prix, R total, win rate, PF, et tout écart entre le calcul et l'affichage du dashboard. Avertir quand l'échantillon est trop petit pour conclure.
