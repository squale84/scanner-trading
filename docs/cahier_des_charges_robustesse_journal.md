# Cahier des charges — Contrôle de robustesse du journal (lecture seule)

Statut : **brouillon à valider par Stéphane**. Aucun code écrit, aucun fichier du dépôt modifié.
Date : 24/10/2026.

## 1. Objectif et non-objectifs

**Objectif** : à partir des trades clos du journal live, estimer ce que le hasard seul peut produire
(drawdown, série de pertes, dispersion du profit factor) pour savoir si le bilan affiché est
solide ou compatible avec la chance.

**Non-objectifs** (volontairement exclus) :
- ne prédit rien sur les prochains trades ;
- n'écrit rien dans Neon, ne touche ni au Pine, ni au contrat du webhook, ni à `server.py` ;
- ne génère aucun signal, aucun ordre, aucune modification de stratégie ;
- pas d'affichage dans le dashboard dans cette phase (rapport séparé uniquement).

## 2. Prérequis et faisabilité

| Élément | État constaté | À vérifier |
|---|---|---|
| Taille de l'échantillon | `etude_backtests_2026-10/LISEZMOI.md` : 49 sorties / 48 trades avec R (20/09 → 13/10), +1,15 R. **Stéphane (24/10) : 70 signaux affichés sur le site Render au 23/10** | Parmi ces 70 : combien de trades **clos avec R** (hors entrées encore ouvertes, `REPLACED`, filtrées, sorties orphelines) ? Non relu : pas d'accès Neon dans cette session |
| `journal_history.json` local | 13 lignes de **jeu de test** (GOLD-1729000000, EURUSD-loss-0…) | À **ne pas utiliser** comme source |
| Plafond `/api/journal` | `JOURNAL_MAX_ENTRIES = 500` lignes (entrées + sorties, soit ~250 trades) | Au-delà, lire `journal_rows` complet (lecture seule) |
| Seuil d'exploitabilité | Critère déjà fixé dans le projet : **≥ 30 trades** | Appliqué tel quel |

Verdict : faisable avec ~48 trades, mais l'intervalle sur le profit factor sera très large. C'est
normal et c'est précisément ce que l'outil doit montrer.

## 3. Données d'entrée

Source (au choix, par ordre de préférence) :
1. Neon, table `journal_rows` (colonne `row` JSONB), requête `SELECT` uniquement, `DATABASE_URL` lu
   depuis `.env` via `storage.py`, jamais affiché ;
2. export JSON de `GET /api/journal` (limité à 500 lignes) ;
3. fixtures de test (jamais de données de production dans le dépôt).

Champs utilisés : `kind`, `time`, `symbol`, `status`, `r_multiple`, `trade_id`, `version`.

Règles d'appariement (identiques à `audit-journal`, pas de nouvelle logique métier) :
- une entrée + la sortie suivante du même `trade_id` = un trade ;
- `r_multiple` absent ou `None` → trade **exclu** et listé à part (« résultat indisponible ») ;
- `REPLACED` → pas de R, exclu ;
- aucun R ni prix n'est jamais inventé, estimé ou déduit.

Point à confirmer : `_compute_r_multiple` (server.py) gère aussi `BE_HIT` (R = 0), absent de la
liste du `CLAUDE.md`. À traiter comme un trade nul ou à exclure ? **Décision à prendre.**

## 4. Métriques et méthode

Fixées **avant** tout calcul sur les vrais chiffres (même principe que `PROTOCOLE_FIGE.md`).

**Rééchantillonnage** (graine fixe, 10 000 tirages, reproductible ; même esprit que `bootstrap_sharpe`
de `lab.py`) :
- **A. Tirage avec remise des R** (hypothèse : trades indépendants) ;
- **B. Tirage par blocs d'un jour** (les trades du même jour, sur plusieurs actifs, sont corrélés ;
  A seul sous-estimerait le risque). **B fait foi si A et B divergent.**

**Sorties** (chacune avec médiane, intervalle 5 %–95 %) :
- R total sur N trades ;
- drawdown maximal en R ;
- plus longue série de trades perdants ;
- profit factor ;
- probabilité que le R moyen soit ≤ 0 (« le bilan positif est-il compatible avec zéro ? »).

**Garde-fous de lecture** :
- N < 30 : aucun chiffre de simulation, message « échantillon insuffisant » ;
- 30 ≤ N < 100 : chiffres affichés avec l'avertissement « intervalle très large, indicatif » ;
- ventilation par actif, par version de script ou par session : seulement si ≥ 30 trades **dans
  la ventilation**, sinon « non évaluable » ;
- jamais de formulation « fiable », « validé » ou « prédit ».

## 5. Limites à écrire dans chaque rapport
- Le R est **théorique** : TP = R prévu, SL = −1 exactement, sans glissement ni écart de prix ;
- Les trades futurs peuvent différer (régime de marché, nouvelle version du Radar) ;
- Mélanger des versions de script (`version`) mélange des logiques différentes ;
- Le rééchantillonnage ne crée pas d'information : il mesure l'incertitude de l'échantillon existant.

## 6. Architecture (séparation des responsabilités)

Dans un dossier d'outils dédié (emplacement à valider, par exemple `outils/`), hors serveur :
1. **Lecture** : charge et apparie les lignes → liste de R + métadonnées (seul module qui touche
   aux données) ;
2. **Calcul** : fonctions pures (R en entrée, statistiques en sortie), aucune entrée/sortie ;
3. **Rapport** : texte Markdown + JSON, en français, avec date, N, graine et limites.

Aucune dépendance à FastAPI. Dépendance numérique : `numpy` seulement s'il est déjà dans
`requirements.txt` ; sinon bibliothèque standard (`random`), largement suffisante pour N < 500.

## 7. Tests (ciblés, sans effet de bord)
- Appariement : entrée sans sortie, sortie orpheline, `REPLACED`, R manquant, `trade_id` dupliqué ;
- Calcul : séquence connue (ex. 3 pertes consécutives) → drawdown et série attendus ;
- Reproductibilité : même graine ⇒ mêmes résultats ;
- Seuils : N = 29 → refus ; N = 30 → avertissement ; ventilation sous 30 → « non évaluable » ;
- Aucun accès réseau ni Neon (faux Neon / fichiers de fixtures).

## 8. Livrables
Indispensables : cahier des charges validé, module de calcul + tests, rapport type.
Recommandés : définition des métriques dans un `LISEZMOI` court, journal des changements.
Optionnels : intégration au skill `audit-journal`, affichage dashboard (phase 2, après validation).

## 9. Ordre de réalisation conseillé
1. Valider ce document (décisions en §10).
2. Relire le nombre actuel de trades (Neon en lecture seule, **avec ton accord**).
3. Écrire calcul + tests sur fixtures.
4. Exécuter sur le vrai journal, produire le rapport.
5. Commit local séparé, après ta validation. Aucun push sans « go ».

## 10. Décisions attendues de Stéphane
1. Traitement de `BE_HIT` (nul ou exclu).
2. Emplacement des fichiers dans le dépôt.
3. Accord pour une lecture seule de Neon (ou export manuel de `/api/journal`).
4. Méthode B (blocs d'un jour) comme référence : d'accord ?
5. Rapport seulement, ou aussi intégré à `audit-journal` plus tard.
