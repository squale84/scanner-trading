# scanner-trading — règles du projet

Scanner ICT 2022 (M5, contexte H1) : Radar Pine → webhook → serveur FastAPI (Render) → base Neon → dashboard `index.html`.

## Langue
- Toutes les réponses, comptes rendus, messages intermédiaires, commentaires de code et **messages de commit** sont en **français**.

## Pine Script
- Deux fichiers qui partagent la même logique et restent **toujours synchronisés** : `scanner_mtf.pine` (Radar, alertes) et `scanner_mtf_backtest.pine` (Strategy Tester). La version courante est dans `SCRIPT_VERSION` et dans le titre `indicator(...)` / `strategy(...)`.
- **Versions protégées** : une version validée et commitée ne se modifie pas en place. Toute évolution de logique = nouvelle version (numéro dans `SCRIPT_VERSION` + titre court lisible dans la liste des scripts TradingView).
- Les fichiers de `C:\Users\stede\OneDrive\Documents\Projet_ECC_Test` (V48, V49) sont en **lecture seule** : on les copie, on ne les modifie jamais (empreintes SHA-256 dans leur propre `CLAUDE.md`).
- **Un seul script Pine actif par graphique** (pas deux versions du Radar empilées). XAUUSD M5 est le graphique de référence pour valider une version avant de la répandre sur les autres actifs.
- Une seule famille logique modifiée à la fois. **TradingView est seul juge** de la compilation : ne jamais annoncer qu'un Pine compile sans l'avoir vu compiler.
- Une alerte TradingView fige le script au moment de sa création : après toute mise à jour du Radar, les alertes doivent être recréées.

## Contrat JSON du webhook (`POST /webhook`)
Source de vérité : les charges `payload_entry`, `payload_update`, `payload_exit` de `scanner_mtf.pine` et `_record_journal_event` dans `server.py`. Champs : `symbol`, `status`, `direction`, `quality`, `grade`, `entry_price`, `sl_price`, `tp_price`, `current_price`, `rr`, `version`, `trade_id`, et `targets` (entrée uniquement). Les prix sont des chaînes, conservées telles quelles (décimales exactes).

Trois familles d'alertes à ne jamais confondre :
- **Entrée** : `status` = nom du setup, `direction` BUY/SELL, niveaux et `targets`. Ouvre une position (et clôt l'éventuelle précédente du même actif en `REPLACED`).
- **Mise à jour M5** : `status` = `PRICE_UPDATE`, une par bougie M5 tant que la position est ouverte. Ne crée **aucune** ligne de journal ; c'est normal d'en recevoir une toutes les 5 minutes.
- **Sortie** : `status` = `TP_HIT`, `SL_HIT` ou `EXPIRED` (30 bougies M5), `direction` NONE. Clôt la position et écrit la ligne de sortie avec son R.

Toute modification du contrat se fait des deux côtés (Pine et serveur) dans le même chantier.

## Données et secrets
- **Aucun secret dans Git**, dans une URL, dans `index.html` ni dans un journal ou une commande affichée (`DATABASE_URL`, `RESET_SECRET`, etc.). Ils vivent dans `.env` (ignoré) et dans les variables d'environnement Render.
- Les données Neon ne se modifient pas sans accord explicite. Les analyses se font en lecture seule.
- Ne jamais inventer un prix manquant ni estimer un résultat inconnu : afficher « résultat indisponible ».

## Git et mise en ligne
- **Commits locaux séparés**, un par sujet, après validation de l'utilisateur. **Aucun push ni déploiement sans « go » explicite.**
- Un Pine n'est commité qu'après validation réelle dans TradingView.

## Tests
- Tests **ciblés** sur ce qui a changé, sans effet de bord réel (faux Neon, `TestClient`, aucune écriture en production). Pas de sur-contrôles : on ne revérifie pas ce qui n'a pas bougé.

## Skills du dépôt
- `audit-signaux-ict` — alertes répétées, états ICT, cohérence Radar/Backtest.
- `audit-journal` — rapprochement entrée/sortie, R, win rate, profit factor.
- `mise-en-ligne-scanner` — GitHub → Render → contrôle du site → alertes TradingView.
