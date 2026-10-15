# Cahier des charges — Stratégie « MTF-POI V1.0 » — document v1.1

Statut : À VALIDER par Stéphane. Aucun code écrit. Ce document remplace la v1.0 du cahier des charges et consolide les décisions prises le 10/10/2026.
Légende : [DÉCIDÉ] = dit par Stéphane · [PROPOSÉ] = valeur par défaut réglable · [HYPOTHÈSE] = à vérifier.

## 1. Objectif
Stratégie ICT testable dans le Strategy Tester (`strategy()`, pas un indicateur). Une zone d'intérêt (POI) naît en H1, la confirmation et l'entrée se font en M5. Chaque règle est un réglage activable/désactivable pour mesurer son effet, un changement à la fois.

## 2. Règles

### Couche H1 — création du POI
- H1-0 [DÉCIDÉ] Biais par structure HH+HL (haussier) / LH+LL (baissier) sur pivots H1 confirmés. Aucune moyenne mobile.
- H1-1 [DÉCIDÉ, optionnel] Prise de liquidité H1 avant le MSS (balayage d'un swing H1) : réglage on/off.
- H1-2 [DÉCIDÉ] MSS H1 avec displacement dans le sens du biais.
- H1-3 [DÉCIDÉ] Le mouvement laisse un OB H1 et/ou une FVG H1 = POI. Réglage : OB / FVG / les deux [PROPOSÉ : les deux].
- H1-4 [PROPOSÉ] POI armé jusqu'au retour du prix ; expiration après 48 bougies H1 ou invalidation du POI.

### Couche M5 — active seulement quand le prix est dans/au contact du POI H1
- M5-1 [DÉCIDÉ] Prise de liquidité M5 par l'OB candidat, à l'intérieur du POI H1.
- M5-2 [DÉCIDÉ] Réaction immédiate : MSS M5 dans le sens du biais H1 (fenêtre max réglable, [PROPOSÉ] 5 bougies).
- M5-3 [DÉCIDÉ] Displacement qui laisse une FVG M5 : sans FVG, l'OB n'est pas validé. [PROPOSÉ] corps ≥ 1,2 × ATR, efficacité ≥ 0,65 (valeurs du fichier MEC).
- M5-4 [DÉCIDÉ] Mode d'entrée réglable : (a) OB, (b) 50 % de la FVG M5 si en discount (achat) / premium (vente), (c) comparaison : les deux ordres posés pour le même setup, étiquetés `OB` et `FVG50`.
- M5-5 [DÉCIDÉ] Stop loss : juste au-delà de la dernière liquidité prise (sous le plus bas du balayage M5 pour un achat, au-dessus du plus haut pour une vente), marge réglable.
- M5-6 [DÉCIDÉ] Invalidation : clôture M5 au-delà du stop, ou expiration de l'ordre sans retour ([PROPOSÉ] 30 bougies M5).

## 3. Cibles (take profit)
- [DÉCIDÉ] Deux modes sélectionnables : « Liquidité » (cibles de liquidité du scanner, affichées en R, R:R minimum réglable) et « R fixes » (1:2, 1:3, …). [PROPOSÉ] mode par défaut : Liquidité.
- [DÉCIDÉ] Plusieurs cibles pour l'étude de backtest. Chez XTB, une position n'a qu'un SL et un TP (d'après les pages XTB consultées) : un multi-cibles s'exécute en plusieurs positions. En réel à 200 €, une seule cible par trade.
- [PROPOSÉ] Déplacement du stop à l'entrée après la 1re cible : désactivé par défaut (modification manuelle chez XTB).

## 4. Taille de position et risque (XTB, compte de 200 €)
- [DÉCIDÉ] Perte maximale par trade : 20 € (soit 10 % de 200 €). Réglable.
- [DÉCIDÉ] Le lot est déduit de la distance du stop et réglé manuellement par Stéphane. La stratégie affiche le lot suggéré et la perte en € ; elle l'utilise aussi pour son backtest.
- Formule : lot = perte max (en $) / (distance du stop en $ × onces par lot). [HYPOTHÈSE] 1 lot = 100 onces, soit 0,01 lot = 1 once ; [HYPOTHÈSE] 1 $ ≈ 0,9 € (constante modifiable). À vérifier dans le calculateur xStation.
- [DÉCIDÉ] Volume minimum 0,01 lot (Stéphane peut ouvrir 0,01 lot sur l'or). Tout setup dont la perte avec 0,01 lot dépasse la perte max est refusé (avec les hypothèses : stop supérieur à environ 22 $).
- Coûts : pas de commission sur l'or chez XTB, coûts par spread et swap (pages XTB). Valeurs exactes du spread et du swap : à relever dans xStation. Le backtest se fait avec et sans coûts.

## 5. Contraintes techniques (non négociables)
- Aucun repaint : données H1 lues sans regard vers l'avenir, pivots utilisés seulement après confirmation.
- Un seul fichier propre. Il reprend les blocs sains audités du fichier MEC (couche H1, fonctions d'impulsion/OB/FVG, tableau de diagnostic) et laisse de côté le code hérité du Radar non utilisé.
- SCRIPT_VERSION et titre identiques et explicites. R6.1, B7.1, B7.2-LAB et V48 restent des références protégées.
- Aucune compilation annoncée tant que TradingView ne l'a pas affichée.

## 6. Données et protocole de test
- Connecteur TradingView testé le 10/10 : XAUUSD M5 environ 5520 bougies (environ 26 jours) ; H1 plus de 8000 bougies (depuis juin 2025). L'historique M5 restera donc court : les résultats serviront à valider la logique et à départager des variantes, pas à prouver la robustesse.
- Graphique de référence : XAUUSD M5. Prix TradingView et XTB légèrement différents : les résultats sont indicatifs.
- Période de réglage et période de contrôle séparées. Un seul réglage change par essai, noté avec version, période, actif.
- Relevés : nombre de setups validés, d'ordres exécutés, de trades, win rate, profit factor, R moyen, drawdown (en € et en %). Exports CSV du Strategy Tester envoyés pour analyse.

## 7. Risques
- Peu de trades (conditions empilées) et peu d'historique M5.
- Perte max de 20 € = 10 % du compte : avec une perte fixe de 20 € par trade, 3 pertes consécutives = -60 € (-30 %), 5 pertes = -100 € (-50 %).
- Écart entre backtest et exécution réelle (spread, glissement, prix XTB).

## 8. Hors périmètre V1.0
Alertes et webhook, intégration au dashboard/serveur, sessions et égaux hauts/bas comme liquidité d'entrée, autres actifs que XAUUSD.

## 9. Ordre de réalisation
1) Validation de ce document · 2) Sauvegarde des fichiers existants (sans commit) · 3) Fichier neuf : couche H1 seule, puis audit complet · 4) Couche M5 + entrées + stop · 5) Cibles + taille de position · 6) Premiers tests CSV sur XAUUSD M5 · 7) Variantes, une à la fois.
