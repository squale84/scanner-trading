# Candidate 5 — RSI(2) long seul, filtre SMA 200 (SPX500, US100, GER40, FR40)

Règles : achat à la clôture si clôture > SMA 200 et RSI(2) < 5 ; sortie à la clôture quand clôture > SMA 5 ;
long seulement, 1×, sans stop. Coûts « ×2 » = spread ×2 + swap XTB actuel. Détail : `resultats_dev_c5.json`,
`resultats_controle_vierge_c5.json`.

## Développement (01/01/1991 → 30/09/2023) — PASSE les 6 règles
| Mesure | Valeur |
|---|---|
| Trades | 509 (SPX 141, US100 133, GER40 113, FR40 122) |
| PF net ×2 | **2,39** (brut 2,87 ; coûts réels 2,42 ; swap ×2 2,07) |
| Gain net moyen par trade | +63 pb ; 77 % gagnants ; durée moyenne 3,3 à 3,9 jours |
| Placebo (entrées aléatoires, mêmes durées) | +4 pb en médiane, 95e centile +19 pb ; p = 0,000 |
| Bootstrap sur les trades | 5e centile +47 pb |
| Plateau PF (RSI<4 / RSI<6 / SMA160 / SMA240) | 2,67 / 2,29 / 2,88 / 2,34 |
| Informatifs : RSI<10 ; sans filtre SMA 200 | PF 1,73 ; PF 2,23 |
| Sharpe du portefeuille 4 indices (exposition 5 à 6 %) | +0,67 net ×2 |

Contrôle de code : recalcul indépendant (pandas) sur SPX500 = mêmes 141 entrées, rendement brut moyen
67,8 pb (pandas) contre 69,0 pb (moteur).

### Stabilité par sous-période (diagnostic descriptif, non utilisé pour décider)
| Période | Trades | PF net ×2 | Gain moyen / trade | Gagnants | Pire trade |
|---|---|---|---|---|---|
| 1991-2007 | 275 | 3,57 | +85 pb | 80 % | −7,3 % |
| 2008-2016 | 126 | 1,75 | +45 pb | 76 % | −17,5 % |
| 2017 → 09/2023 | 108 | 1,46 | +27 pb | 71 % | −7,3 % |

Années à PnL négatif : 1994, 2006, 2008, 2011 (−18 %), 2016, 2018 (−18 %), 2020. Gain moyen des gagnants
+140 pb, perte moyenne des perdants −196 pb ; les 10 meilleurs trades pèsent 18 % du PnL.

## Contrôle vierge (01/10/2023 → 13/10/2026) — ouvert UNE fois
| Mesure | Valeur |
|---|---|
| Trades | **60** (SPX 17, US100 17, GER40 16, FR40 10) — exactement le seuil de 60 |
| PF net ×2 | **2,52** ; gain moyen +57 pb ; 77 % gagnants ; pire trade −8,7 % |
| Placebo | p = 0,003 (médiane +4 pb) |
| Bootstrap | 5e centile +17 pb |
| Par indice | SPX +135 pb (PF 42) ; US100 +77 ; GER40 +68 ; **FR40 −130 pb (PF 0,15, 10 trades)** |

Verdict du protocole : **CONFIRMÉE** (PF > 1 et placebo non retourné, 60 trades = seuil de « non
concluant » atteint tout juste).

## Réserves (à lire avant toute conclusion)
1. **Décroissance** : le PF net est passé de 3,6 à 1,5 en développement. Le contrôle (2,5) tombe sur une
   période haussière de 3 ans et ne contredit pas la tendance à l'érosion ; il ne l'infirme pas non plus.
2. **Échantillon indépendant bien plus petit que 60** : SPX, NDX, DAX, CAC sont très corrélés, leurs
   signaux tombent souvent les mêmes jours.
3. **Pas de stop** : pertes rares mais lourdes (−17,5 % du nominal sur un trade en 2008-2016).
4. **Exécution** : entrée et sortie « à la clôture » du jour du signal, avec un RSI calculé sur la
   clôture quasi finale ; le glissement réel à la clôture n'est pas mesuré.
5. **Sous-jacents, pas CFD** : les écarts de prix et de séance entre l'indice cash et le CFD ne sont pas
   modélisés.
6. **FR40 négatif sur le contrôle** (littérature : l'effet IBS est « U.S.-centric »).
7. Candidate retenue parmi 17 essais déclarés ; un seul contrôle vierge, désormais consommé : il ne
   peut plus servir à aucune autre hypothèse.

## Suite proposée par le protocole
Phase papier ou micro-lot d'au moins 100 trades avant tout capital réel, avec règle d'arrêt chiffrée
fixée à l'avance (drawdown, PF glissant).
