---
name: audit-signaux-ict
description: Diagnostic des signaux du scanner ICT — alertes TradingView répétées ou manquantes, état de la machine ICT (sweep, MSS, FVG, retest), écarts entre le Radar et le Backtest. À utiliser seulement quand l'utilisateur signale un comportement anormal des alertes ou des signaux, ou demande de vérifier la cohérence des deux Pine.
---

# Audit des signaux ICT

Lecture seule : ce skill diagnostique, il ne modifie aucun Pine. Toute correction suit ensuite les règles Pine du `CLAUDE.md`.

## 1. Identifier la version réellement en service
- `SCRIPT_VERSION` et titre dans `scanner_mtf.pine` / `scanner_mtf_backtest.pine`.
- Le champ `version` des dernières alertes reçues (`/api/journal`, lignes récentes) : s'il diffère, les alertes TradingView n'ont pas été recréées après la mise à jour.

## 2. Alertes répétées
Classer chaque alerte selon le contrat du `CLAUDE.md` (entrée / `PRICE_UPDATE` / sortie) avant de conclure :
- `PRICE_UPDATE` toutes les 5 min pendant une position ouverte = **normal**.
- E-mails ou notifications en double : vérifier dans l'alerte TradingView que seules les cases voulues sont cochées (webhook), pas « Envoyer du texte brut » / e-mail.
- Plusieurs entrées identiques : comparer `trade_id` ; le serveur dédoublonne par `trade_id` (`_same_levels` dans `server.py`).
- Deux versions du Radar sur le même graphique ou deux alertes sur le même actif : en garder une seule.

## 3. États ICT
- Machine à états du Radar : IDLE → SWEEP_ARMED → MSS_CONFIRMED → CAUSAL_FVG_CONFIRMED → WAIT_RETEST → READY. Le tableau de diagnostic du Backtest (compteurs de l'entonnoir, abandons faute de cible) indique où les setups se perdent.
- Pine évalue les deux côtés d'un `and` : une garde d'index doit être dans un `if` séparé.

## 4. Cohérence Radar / Backtest
- Comparer bloc par bloc la logique de détection et de cibles (sections identiques dans les deux fichiers) ; seules les sorties diffèrent (`alert()` contre `strategy.entry/exit`).
- Vérifier sur un même graphique que les entrées du Backtest tombent sur les mêmes bougies que les alertes du Radar.
- Les frais du Backtest doivent être réalistes pour l'actif testé, sinon les R sont faussés.

## Compte rendu
En français : version en service, cause identifiée, preuve (capture, ligne de code, ligne de journal), correction proposée — sans l'appliquer avant accord.
