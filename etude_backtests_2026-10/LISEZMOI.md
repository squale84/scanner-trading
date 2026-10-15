# Étude des stratégies testées — septembre / octobre 2026

Rangement du 14/10/2026. Ce dossier garde **les résultats** (exports TradingView) des stratégies
testées ; le code des stratégies ratées est dans `_a_supprimer_2026-10-14\code_rate\` (voir
`A_LIRE.txt` là-bas) en attendant suppression.

## Critère retenu (fixé avant les tests)

PF (profit factor) **> 1,2** sur le réglage **et** sur un échantillon de contrôle, avec **au moins
30 trades**, et pas sur un seul actif ni sur une courte période.
Conventions B7.1 quand elles sont applicables : capital 10 000, risque 1 %, commission 0,02 % par
côté, glissement 2 ticks.

## Bilan : aucune stratégie n'a fait ses preuves

Chiffres relus directement dans les CSV (lignes « Sortir », P&L net par trade, PF = gains / pertes).

| Dossier | Ce que c'est | Résultat | Verdict |
|---|---|---|---|
| `radar_B7.1` | Radar ICT en backtest (B7.1) : 9 actifs, 5/15 min | 15 min (14/10) : 6 à 24 trades par actif, PF de 0,01 à 1,04 (seul l'or ≥ 1 : 1,04 sur 11 trades). Exports du 26/09 : PF de 0,03 à 0,83. Or, versions anciennes : 31–44 trades, PF 0,56–0,69. | Échec |
| `radar_B7.2-LAB` | Variante laboratoire (continuation, killzones) | Indices (FR40, GER40, SPX500) le plus souvent PF 1,16 à 1,56 (un export FR40 à 0,95), mais 4 à 17 trades par fichier ; or PF 0,00–0,07, NATGAS, USOIL, US100 sous 0,6. **Aucun fichier n'atteint 30 trades.** | Non validé : la seule piste (indices) est sur des échantillons trop faibles |
| `cassure` | Cassure de range 5 j, 15 min, 9 actifs | 47 à 61 trades par actif, PF 0,19 à 0,86 ; **467 trades, PF 0,53** | Échec net : aucun actif ≥ 1 |
| `macd` | MACD + EMA200, or | V0.3 1 h (modèle de frais B7.1) : 141 trades sur 20 mois, **PF 0,93**. Anciens exports du 10/10, autre modèle de frais (lots XTB, frais en dollars) : V0.1 PF 1,23 et V0.2 PF 1,13 sur 148 trades, un autre export V0.2 à 0,89 sur 68 trades. | Échec : le PF > 1 des anciens exports ne tient pas avec les frais B7.1 ni sur d'autres actifs |
| `V48` | Stratégie V48 S1 (copie de Projet_ECC_Test), 8 actifs | 26 à 60 trades par actif ; PF ≥ 1 seulement sur FR40 (1,22 sur 41 trades) ; USDJPY −8 404 USD, NATGAS −9 999 USD, USOIL −3 718 USD | Échec |
| `fvg-rsidiv` | FVG + divergence RSI V0.1 | Or : 24 trades PF 0,54 ; USDJPY : 24 trades, PF 0,00 | Échec |
| `mtf-poi` | MTF-POI V1.0 M5, or | 5 trades, PF 0,00 | Non concluant (échantillon) |
| `banc` | Banc de test V0.1, or | 3 exports, réglages non identifiés dans les noms : 198 trades PF 1,08 ; 72 trades PF 0,97 ; 50 trades PF 0,81 | Échec : aucun ≥ 1,2 |

### À retenir
- **MACD sur les 8 autres actifs en 1 h** : Stéphane a constaté le 14/10 que le PF ne dépasse 1 sur
  aucun. Ces exports ne sont **pas** dans ce dossier (seul l'or l'est), le constat repose sur son
  observation.
- Les PF supérieurs à 1 qui apparaissent (anciens MACD sur l'or, indices en B7.2-LAB, FR40 en V48)
  viennent chaque fois d'**un actif ou de moins de 30 trades** : ce n'est pas une preuve.
- Le journal live du Radar (49 sorties, 20/09 → 13/10) est à +1,15 R sur 48 trades : trop court pour
  contredire les backtests.

## Organisation du dossier

| Dossier | Contenu |
|---|---|
| `radar_B7.1\` | exports B7.1 du 26/09 et 04/10 ; `15min\` (14/10) ; `anciens_2026-09\` (premiers exports et B7.1-DEBUG) |
| `radar_B7.2-LAB\` | exports du 26/09 ; `Test1_W1_V2\` (CONT, KZ, analyse TradingView en zip) ; `Test1_W1_2026-09-27\` |
| `cassure\15min\` | Cassure V0.1, 9 actifs |
| `macd\` | `60min\` (V0.3, or) ; `anciens_2026-10-10\` (V0.1 et V0.2, or) |
| `V48\`, `fvg-rsidiv\`, `mtf-poi\`, `banc\` | exports d'origine, non modifiés |

Les fichiers « (1) », « (2) » qui restent ne sont **pas** des copies : leur contenu diffère (autre
réglage ou autre version). Les copies exactes ont été écartées dans
`_a_supprimer_2026-10-14\doublons\csv\` (voir `DOUBLONS.txt`).

## Ce qui n'est pas dans Git

Les CSV sont ignorés par `.gitignore` (`*.csv`) : **ce dossier n'est sauvegardé nulle part
ailleurs que sur OneDrive**. Ne le supprime pas sans l'avoir copié.

## Avant de retester une idée

1. Écrire le critère et le protocole **avant** de lancer le test (actifs, période, frais, contrôle).
2. Ne pas découper un échantillon jusqu'à trouver un sous-ensemble qui marche (sur-ajustement).
3. Relire ce tableau : une idée déjà passée ici ne se retest qu'avec un changement de fond.
