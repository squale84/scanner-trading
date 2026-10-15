# Protocole figé — candidates 1, 2 et 3

Rédigé le 14/10/2026 **avant tout calcul de performance** (seules les dates et le nombre de barres
des données ont été regardés). Toute modification ultérieure doit être consignée dans
`JOURNAL_DES_ESSAIS.md` comme un essai supplémentaire.

## Données
- Bougies journalières TradingView (via le client MCP en lecture seule de Jarvis), depuis le 01/01/1990.
- Actifs, symbole retenu = celui à l'historique le plus long : voir `../donnees/SOURCES.json`.
  Ce sont les **sous-jacents** (indices cash, spot, contrats continus), pas les CFD eux-mêmes.
- Univers primaire (9) : XAUUSD, SPX500, US100, GER40, FR40, EURUSD, USDJPY, USOIL, NATGAS.
  BTCUSD : informatif seulement (historique court, swap long ≈ 35 %/an).
- Règle d'erreur de données (fixée d'avance) : un rendement journalier hors de [−50 %, +100 %] ou
  un prix ≤ 0 est traité comme une erreur : rendement mis à 0 ce jour-là et le lendemain, et compté.
  (Cas connu : pétrole CL1! le 20/04/2020, prix négatif.)

## Fenêtres
- **Développement** : 02/01/1990 → 30/09/2023. Les 12 premiers mois servent à l'échauffement.
- **Contrôle vierge** : 01/10/2023 → 13/10/2026 (les barres des 14 et 15/10 sont encore en
  formation et sont exclues). Le chargeur de développement coupe
  physiquement les données au 30/09/2023. `run_blind.py` pose un verrou
  (`controle_vierge_OUVERT.json`) avant de calculer et refuse de se relancer.
- Le contrôle vierge n'est ouvert que pour une candidate qui passe **toutes** les règles du
  développement, et une seule fois.

## Coûts (fixés d'avance, source : rapport de recherche, tableau XTB, [calcul])
- Spread aller-retour appliqué à chaque variation de position, proportionnel au nominal.
- Swap : coût par nuit calendaire détenue, côté long ou court, **aux taux actuels** appliqués à tout
  l'historique (hypothèse prospective : « combien ça coûterait aujourd'hui »). Aucun crédit de swap
  n'est retenu (conservateur).
- **Coûts « ×2 » = spread ×2, swap actuel conservé** (définition du rapport). Une sensibilité
  « swap ×2 » est affichée à titre informatif. Les règles d'acceptation portent sur « coûts ×2 ».
- Aucun intérêt sur le cash (0 %).

## Candidates (paramètres de la littérature, non optimisés)
1. **Tendance 12 mois, long/short** (Moskowitz-Ooi-Pedersen 2012) : à chaque fin de mois, signe du
   rendement sur 12 mois ; taille = 10 % / volatilité annualisée (EWMA, centre de masse 60 jours,
   plafond de levier 3) ; détention 1 mois. Plateau : 10 et 14 mois.
2. **Prix > SMA 10 mois, long ou cash** (Faber 2013) : à chaque fin de mois, long 1× si la clôture
   mensuelle est au-dessus de la moyenne des 10 dernières clôtures mensuelles, sinon cash.
   Plateau : SMA 8 et 12 mois. Comparateur : acheter-et-garder au même coût.
3. **Turn-of-the-month, long seulement** (McConnell & Xu 2008) sur SPX500, US100, GER40, FR40 :
   entrée à la clôture de T−1 (avant-dernier jour de bourse du mois), sortie à la clôture de T+3
   (3e jour de bourse du mois suivant). Plateau : sortie à T+2 et à T+4.
   Informatif (compté comme essai) : entrée à T−4.

## Règles d'acceptation (développement, nets de coûts ×2)
Candidates 1 et 2 — toutes doivent être vraies :
- R1 Sharpe net du portefeuille (moyenne égale des actifs) ≥ 0,30.
- R2 rendement net total > 0 sur au moins 5 des 9 actifs.
- R3 placebo : p-value ≤ 0,05 (1 000 tirages ; signes mensuels aléatoires pour 1, long/cash aléatoire
  avec la même fréquence d'exposition pour 2).
- R4 bootstrap par blocs de 21 jours (2 000 tirages) : 5e centile du Sharpe > 0.
- R5 plateau : Sharpe ≥ 0,15 aux deux paramètres voisins.
- R6 au moins 100 trades agrégés ; sinon verdict « non concluant », jamais « accepté ».

Candidate 3 — toutes doivent être vraies :
- R1 rendement net moyen par fenêtre > 0 sur au moins 3 des 4 indices.
- R2 placebo (fenêtres de 4 jours à date aléatoire dans le mois, 1 000 tirages) : p-value ≤ 0,05.
- R3 t-stat ≥ 2 sur le rendement net mensuel de l'indice équipondéré (une observation par mois).
- R4 plateau : rendement net moyen > 0 pour les sorties T+2 et T+4.
- R5 au moins 100 fenêtres agrégées.

## Contrôle vierge (une candidate qui a passé tout ce qui précède)
- Sharpe net > 0 (1 et 2) ou rendement net moyen par fenêtre > 0 (3), ET placebo non retourné.
- Moins de 60 trades agrégés : « non concluant » quel que soit le résultat.

## Addendum du 15/10/2026 — candidates 4 et 5 (rédigé avant tout calcul de la candidate 5)
Mêmes fenêtres (développement jusqu'au 30/09/2023, contrôle vierge scellé), mêmes coûts, même
journal des essais (N passe de 10 à 17 pour la candidate 5 ; < 20, le seuil « t ≥ 3 » reste inactif).

### Candidate 5 — RSI(2) de Connors, long seul, filtre SMA 200 (SPX500, US100, GER40, FR40)
- Données : journalières, déjà disponibles.
- Entrée à la clôture du jour t si clôture > SMA 200 jours ET RSI(2) de Wilder < 5, sans position.
- Sortie à la clôture du premier jour où la clôture repasse au-dessus de la SMA 5 jours.
- Pas de stop, pas de sortie sur durée, 1× sans levier, long seulement.
- Plateau (±20 %) : seuil RSI < 4 et < 6 ; filtre SMA 160 et SMA 240.
- Informatifs (comptés comme essais) : seuil RSI < 10 (valeur d'origine de Connors) ; sans filtre SMA 200.
- Règles d'acceptation (toutes vraies) :
  - R1 profit factor net ×2 des trades agrégés ≥ 1,2.
  - R2 gain net moyen par trade > 0 sur au moins 3 des 4 indices.
  - R3 placebo : mêmes nombres et durées de trades, entrées aléatoires parmi les jours « clôture > SMA 200 »
    (1 000 tirages) : p ≤ 0,05 sur le gain net moyen par trade.
  - R4 bootstrap sur les trades (2 000 tirages) : 5e centile du gain net moyen par trade > 0.
  - R5 plateau : PF net ×2 ≥ 1,1 pour les 4 voisins.
  - R6 au moins 100 trades agrégés ; sinon « non concluant ».
- Contrôle vierge si tout passe : PF net > 1,0 et placebo non retourné ; < 60 trades → « non concluant ».

### Candidate 4 — Momentum de fin de séance (Baltussen, Da, Lammers, Martens, JFE 2021)
- Règle : signe du rendement « clôture de la veille → 30 minutes avant la clôture » ; position longue
  (courte si négatif) sur la dernière demi-heure, sortie à la clôture ; SPX500, US100, GER40, FR40.
- Données nécessaires : barres 30 min (ou 5 min) avec bornes de séance, ≥ 10 ans (≈ 2 500 séances par
  indice, idéalement depuis 2010). Source disponible via TradingView : **30 min depuis janvier 2025
  seulement (≈ 450 séances), 1 h depuis 2023/2024** : insuffisant pour le protocole.
- Statut : **NON EXÉCUTÉE tant que la source de données n'est pas validée par l'utilisateur.**
- Règles d'acceptation prévues : R1 Sharpe net ×2 ≥ 0,30 (4 indices égal-poids), R2 ≥ 3 indices sur 4 nets
  positifs, R3 placebo à signe aléatoire p ≤ 0,05, R4 bootstrap p5 > 0, R6 ≥ 100 trades ; R5 non
  applicable (règle publiée sans paramètre libre).

## Limites déclarées d'avance
- Sous-jacents et non CFD réels : écarts de prix, rolls des contrats continus (CL1!, NG1!) et
  financement historique non reproduits.
- Swaps d'aujourd'hui appliqués à 1990-2023 : pénalise les positions longues des années à taux nuls.
- Corrélation forte entre indices : le nombre effectif d'actifs indépendants est bien inférieur à 9.
- Les seuils d'acceptation sont des propositions de travail du rapport, pas des valeurs de la littérature.
