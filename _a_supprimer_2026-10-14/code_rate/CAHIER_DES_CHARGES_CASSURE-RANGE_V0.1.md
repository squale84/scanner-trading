# Cahier des charges — Stratégie « CASSURE-RANGE V0.1 » — document v0.1

Statut : À VALIDER par Stéphane. Aucun code écrit.
Légende : [DÉCIDÉ] = dit par Stéphane · [PROPOSÉ] = valeur par défaut réglable · [HYPOTHÈSE] = à vérifier.

## 1. Objectif
Tester une idée simple, isolée du Radar : **quand le prix casse le haut d'un range, on achète ; quand il casse le bas, on vend** [DÉCIDÉ].
Le moteur du Radar (B7.1) n'entre presque jamais sur une cassure : sur 78 trades du backtest (range de 10 jours), seulement 3 étaient des cassures. Cette idée n'a donc jamais été mesurée. Cette stratégie sert à la mesurer, sans toucher à B7.1 ni au Radar.

Question à laquelle le test doit répondre : *une entrée sur cassure de range a-t-elle un meilleur résultat par trade que le moteur actuel (B7.1 : −0,56 % par trade en 5 min, −0,49 % en 15 min) ?*

## 2. Règles (version minimale, un seul réglage change à la fois)

### Le range
- R-1 [PROPOSÉ] Range = plus haut et plus bas des **N dernières bougies journalières terminées** (N = 5 par défaut ; réglage 3 / 5 / 10).
- R-2 [PROPOSÉ] Variantes du range, testées une par une : (a) plus haut/plus bas de la veille (PDH/PDL) ; (b) range de la session asiatique ; (c) range des N jours.
- R-3 Le range est figé à l'ouverture de la séance : aucun repaint, aucune donnée du futur.

### L'entrée
- E-1 [DÉCIDÉ] Cassure par le haut → **achat** ; cassure par le bas → **vente**.
- E-2 [PROPOSÉ] Une cassure est valide quand une bougie du graphique de travail (M5 ou M15) **clôture** au-delà du niveau, d'au moins 0,1 × ATR (filtre des mèches). Variante : cassure par la mèche seule.
- E-3 [PROPOSÉ] Entrée immédiate à la clôture de la bougie de cassure. Variante : attendre le **retest** du niveau cassé, puis entrer.
- E-4 [PROPOSÉ] Un seul trade par niveau cassé et par jour ; pas de réentrée tant que le prix n'est pas revenu dans le range.

### Le stop
- S-1 [PROPOSÉ] Stop juste de l'autre côté du niveau cassé, à 0,5 × ATR (comme le plancher du Radar). Variante : au milieu du range.
- S-2 Distance de stop plafonnée à 2,5 × ATR (même plafond que B7.1).

### La sortie
- T-1 [PROPOSÉ] Take-profit à **2 R** (même ratio par défaut que B7.1, pour comparer).
- T-2 [PROPOSÉ] Expiration après 30 bougies, comme le Radar.
- T-3 Variante : cible = hauteur du range projetée depuis la cassure.

## 3. Taille de position et coûts (identiques à B7.1, pour que la comparaison soit juste)
- Risque par trade : 1,0 % du capital [DÉCIDÉ ; à passer à 0,5 % en réel après l'étude].
- Capital initial 10 000, commission 0,02 %, glissement 2 ticks (mêmes constantes que B7.1).

## 4. Protocole de test
- Actifs : les 9 déjà testés (XAUUSD, EURUSD, USDJPY, US100, SPX500, GER40, FR40, USOIL, NATGAS).
- Intervalles : M5 et M15 (le 1 h est abandonné).
- **Période de réglage** : du 28/07 au 25/09 ; **période de contrôle** : après le 25/09 et avant le 28/07 (le 15 min remonte à avril). Aucun réglage n'est choisi sur la période de contrôle.
- **Critère de réussite fixé à l'avance** : facteur de profit > 1,2 et résultat par trade > 0 sur la période de réglage **et** sur la période de contrôle, avec au moins 30 trades dans chacune. Sinon, l'idée est écartée telle quelle.
- Relevés : trades, gagnants, gain/perte moyens, résultat par trade, facteur de profit, drawdown, durée. Mêmes outils que l'étude des intervalles (dossier `backtest_exports`).

## 5. Contraintes techniques
- `strategy()` dans un **fichier neuf** ; `SCRIPT_VERSION` et titre explicites. R6.1, R6.2, B7.1, B7.2-LAB restent des références protégées, non modifiées.
- Aucun repaint : valeurs journalières lues sans regarder vers l'avenir (`lookahead_off`, barres terminées).
- Aucune compilation annoncée tant que TradingView ne l'a pas affichée. Aucune alerte ni webhook dans cette version.

## 6. Risques
- Les fausses cassures sont fréquentes : le résultat dépend fortement du filtre de confirmation (E-2).
- Peu de trades par actif en M5 sur l'historique disponible (environ 1 mois) : le M15 offre plus de recul.
- Un test unique ne prouve rien : seuls comptent les deux périodes (réglage et contrôle).

## 7. Hors périmètre V0.1
Alertes et webhook, journal et serveur, filtres de séance, multi-cibles, combinaison avec les signaux du Radar.

## 8. Ordre de réalisation
1) Validation de ce document · 2) Écriture du fichier Pine neuf (range journalier, entrée immédiate, stop, TP 2 R) · 3) Compilation par Stéphane dans TradingView · 4) Exports CSV M5 puis M15 sur les 9 actifs · 5) Analyse sur la période de réglage, puis de contrôle · 6) Variantes, une à la fois.
