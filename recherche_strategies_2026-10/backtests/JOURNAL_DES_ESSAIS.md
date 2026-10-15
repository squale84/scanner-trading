# Journal des essais

Chaque configuration exécutée est consignée ici (N = nombre d'essais déclaré). Rien n'est retiré.

## Essais déclarés avant exécution (14/10/2026)
| # | Candidate | Configuration | Statut |
|---|---|---|---|
| 1 | 1 Tendance | lookback 12 mois (principal) | principal |
| 2 | 1 Tendance | lookback 10 mois | plateau |
| 3 | 1 Tendance | lookback 14 mois | plateau |
| 4 | 2 SMA | SMA 10 mois (principal) | principal |
| 5 | 2 SMA | SMA 8 mois | plateau |
| 6 | 2 SMA | SMA 12 mois | plateau |
| 7 | 3 TOM | T-1 -> T+3 (principal) | principal |
| 8 | 3 TOM | T-1 -> T+2 | plateau |
| 9 | 3 TOM | T-1 -> T+4 | plateau |
| 10 | 3 TOM | T-4 -> T+3 | informatif |

N = 10 (le seuil « t >= 3 » du protocole n'est pas déclenché : N < 20). BTCUSD est calculé à titre
informatif sur les mêmes configurations, sans compter comme essai.

## Essais déclarés le 15/10/2026 avant exécution (candidate 5)
| # | Candidate | Configuration | Statut |
|---|---|---|---|
| 11 | 5 RSI(2) | RSI<5, filtre SMA 200, sortie SMA 5 (principal) | principal |
| 12 | 5 RSI(2) | RSI<4 | plateau |
| 13 | 5 RSI(2) | RSI<6 | plateau |
| 14 | 5 RSI(2) | filtre SMA 160 | plateau |
| 15 | 5 RSI(2) | filtre SMA 240 | plateau |
| 16 | 5 RSI(2) | RSI<10 (valeur d'origine) | informatif |
| 17 | 5 RSI(2) | sans filtre SMA 200 | informatif |

N = 17 au total à ce stade (< 20). La candidate 4 n'est pas exécutée (données insuffisantes).

## Résultats candidate 5 (15/10/2026) — essais 11 à 17 exécutés
Principal : PASSE les 6 règles du développement (PF net ×2 2,39 ; 509 trades). Voisins PF 2,29 à 2,88.
Informatifs : RSI<10 PF 1,73 ; sans filtre SMA 200 PF 2,23. Détail : `RESULTATS_CANDIDATE_5.md`.
Candidate 4 : non exécutée (barres 30 min disponibles depuis janvier 2025 seulement).
**Candidate 4 ABANDONNÉE le 15/10/2026** sur décision de l'utilisateur (pas de téléchargement de
données externes). Aucun essai consommé pour elle.

## Essai déclaré le 15/10/2026 avant exécution (candidate 6 intraday)
| # | Candidate | Configuration | Statut |
|---|---|---|---|
| 18 | 6 Rebond VWAP | M15, SMA 200, rebond VWAP, Londres et New York, stop 1 ATR(14), cible 1,5 R | principal |

Règles figées avant le premier résultat : achat au-dessus de la SMA 200 lorsqu'une bougie touche le
VWAP depuis le dessus puis clôture au-dessus ; vente symétrique sous la SMA 200. Une seule entrée par
session et par actif. Sessions : Londres 08:00-11:00 heure locale et New York 09:30-12:00 heure locale.
Toute position encore ouverte est clôturée sur la dernière bougie de la session. Univers primaire :
SPX500, US100, GER40 et FR40. Commission TradingView 0,02 % par côté et glissement de 2 ticks.

Critères de présélection, tous requis : au moins 250 trades agrégés ; PF net ≥ 1,20 ; résultat net
positif sur au moins 3 des 4 indices ; PF ≥ 1,05 avec commission doublée. Faute d'un historique M15
long et indépendant, un passage éventuel constitue seulement une présélection avant 100 trades en
papier ou micro-lot, jamais une preuve. Toute modification d'horaire, d'ATR, de cible ou de définition
du rebond comptera comme un nouvel essai.

N = 18 au total après déclaration de cette candidate.

Contrôle technique avant résultat : la V0.1 n'a exécuté aucun trade sur les indices et matières
premières essayés dans TradingView. La V0.2 réduit la taille de test de 100 % à 10 % du capital,
explicite une marge de 100 % et ajoute des compteurs de diagnostic (VWAP, bougies de session,
rebonds et signaux autorisés). La logique du signal, les horaires, le stop et la cible ne changent
pas ; cette correction technique ne constitue donc pas un nouvel essai de paramètres.

## État du contrôle vierge
**OUVERT le 15/10/2026, une seule fois, pour la candidate 5** (verrou `controle_vierge_OUVERT.json`).
Résultat : 60 trades, PF net ×2 2,52, placebo p = 0,003 → « CONFIRMÉE » au sens du protocole.
Le contrôle est **consommé** : il ne peut plus servir à tester une autre hypothèse.
Avant l'ouverture : recalcul indépendant (pandas) du moteur sur SPX500, mêmes 141 entrées ; diagnostic
par sous-périodes sur le développement uniquement (décroissance PF 3,57 → 1,75 → 1,46).

## Résultats du développement (15/10/2026) — essais 1 à 10 exécutés
| Candidate | Verdict | Mesure clé (net, coûts ×2) |
|---|---|---|
| 1 Tendance 12 m | REJETÉE | Sharpe −0,06 (brut +0,67), 3/9 actifs positifs |
| 2 SMA 10 m | REJETÉE | Sharpe +0,07 (brut +0,72), placebo p = 0,21 |
| 3 TOM T−1→T+3 | REJETÉE | t mensuel 1,70 (< 2), placebo p = 0,003 |
Détail : `RESULTATS_DEVELOPPEMENT.md`. Le contrôle vierge reste **scellé et non ouvert**.
Variante T−4→T+3 (t 3,06) : observée, NON promue (règles non déplacées après résultats).

## Journal des exécutions
- 15/10/2026 : première exécution de `run_dev.py` interrompue par une erreur de code (dépaquetage d'un
  tuple de 3 éléments pour la SMA) avant toute sortie de résultat ; corrigée puis relancée. Aucun
  paramètre ni règle modifiés.
- 14/10/2026 : moteur testé sur données synthétiques (`tests_lab.py`, 14 contrôles OK). Deux tests
  corrigés avant toute donnée réelle (échauffement compté comme « pas long » ; bruit de tirage dans
  le test du bootstrap) : défauts des tests, pas du moteur. Aucune donnée réelle utilisée à ce stade.
