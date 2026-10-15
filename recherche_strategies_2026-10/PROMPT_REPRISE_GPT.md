# Prompt de reprise (à coller dans GPT)

Tu reprends un chantier de recherche de stratégies de trading pour Stéphane. Réponds toujours **en français**.
Avant d'agir, lis les fichiers cités ci-dessous (je ne te les recopie pas).

## Contexte
- Dépôt de travail : `C:\Users\stede\OneDrive\Bureau\scanner_trading` (branche `lab/b72`, dépôt séparé de JARVIS).
  Règles du dépôt dans `AGENTS.md` : réponses et commits en français ; versions Pine validées protégées
  (nouvelle version = nouveau fichier) ; **TradingView est seul juge de la compilation** (ne jamais
  affirmer qu'un Pine compile sans l'avoir vu compiler) ; aucun commit sans validation, **aucun push ni
  déploiement sans « go » explicite** ; aucun secret (clé, webhook) dans Git, URL, journal ou message.
- Objectif de Stéphane : une stratégie simple qui marche en marché haussier comme baissier, retenue
  uniquement si elle passe un critère fixé d'avance. Il trade des CFD XTB (or, indices, FX, pétrole, gaz).

## État au 15/10/2026
- Ont échoué (PF < 1, résultats rangés dans `etude_backtests_2026-10\`) : Radar ICT en backtest (B7.1/B7.2-LAB),
  cassure de range 5 jours, MACD+EMA200 (or puis 8 autres actifs). Tout le code correspondant est dans
  `_a_supprimer_2026-10-14\` (rien supprimé ; à vider par Stéphane ; **ne pas vider**
  `code_rate\_archive_MEC_2026-10-10` tant que les 725 lignes non commitées de
  `scanner_mtf_backtest_lab.pine` ne sont pas commitées ou abandonnées).
- Recherche approfondie sourcée : `recherche_strategies_2026-10\reports\Stratégies de trading à preuve documentée.md`.
  Conclusions : seule la tendance lente a une preuve longue ; le swap long XTB (≈ 8 à 12 %/an) consomme
  l'avantage des stratégies lentes ; l'ancien critère « PF > 1,2, ≥ 30 trades » est insuffisant.
- Backtests Python (protocole figé avant calcul, journal des essais N = 17, contrôle vierge
  01/10/2023 → 13/10/2026) dans `recherche_strategies_2026-10\backtests\` :
  - Candidate 1 tendance 12 mois : REJETÉE (Sharpe brut +0,67, net −0,06).
  - Candidate 2 SMA 10 mois : REJETÉE (net +0,07, placebo p = 0,21).
  - Candidate 3 turn-of-the-month : REJETÉE de peu (t = 1,70 < 2). La variante T−4→T+3 (t = 3,06) a été vue
    après coup et **n'est pas promue**.
  - Candidate 4 momentum de fin de séance : ABANDONNÉE (données intraday insuffisantes, Stéphane refuse
    tout téléchargement externe).
  - **Candidate 5 RSI(2) long seul + SMA 200 (SPX500, US100, GER40, FR40) : seule survivante.**
    Développement 1991→09/2023 : 509 trades, PF net ×2 = 2,39 ; décroissance : PF 3,57 (1991-2007),
    1,75 (2008-2016), 1,46 (2017-2023). Contrôle vierge **ouvert une seule fois, consommé** : 60 trades,
    PF 2,52, FR40 négatif. Détails : `backtests\RESULTATS_CANDIDATE_5.md`.
- Pine de la candidate 5 (**non compilé**, non commité) :
  `C:\Users\stede\OneDrive\Bureau\scanner_trading\recherche_strategies_2026-10\pine\rsi2_long_sma200_V0.1.pine`
  avec `pine\LISEZMOI.md`.
- Alertes TradingView : l'alerte GER40 du 14/10 (23h01, SELL « BSL SWEEP ») vient d'une alerte créée en
  **60 min** ; FR40, USDJPY, SPX500 et XAUUSD sont aussi en 60 min et n'ont jamais tiré. Le Radar ne
  filtre ni session (mode continu par défaut) ni biais H1, et « Grade min A » ne filtre rien.

## À faire, dans l'ordre
1. Stéphane colle le Pine dans TradingView (graphique 1 jour, période 01/01/1991 → 30/09/2023) sur
   SP:SPX, NASDAQ:NDX, XETR:DAX, TVC:CAC40. Trades attendus : 141 / 133 / 113 / 122 (quelques unités
   d'écart normales). TradingView n'applique pas le swap (≈ +8 pb par trade). Corriger le Pine selon
   l'erreur de compilation éventuelle, puis comparer les nombres de trades et le PF au moteur.
2. Décider avec lui des 4 alertes en 60 min : les garder ou les recréer en M5 (une alerte fige le script ;
   la recréation se fait dans TradingView, par lui).
3. Phase papier ou micro-lot d'au moins 100 trades de la candidate 5, avec une règle d'arrêt chiffrée
   fixée à l'avance (drawdown, PF glissant), avant tout capital réel.

## Interdits
- Ne rouvre pas, ne rejoue pas le contrôle vierge (verrou `backtests\controle_vierge_OUVERT.json`).
- Ne modifie pas les règles de `backtests\PROTOCOLE_FIGE.md` après avoir vu des résultats ; toute nouvelle
  variante = un essai de plus dans `JOURNAL_DES_ESSAIS.md`.
- Ne présente jamais un bon résultat sur un actif ou une courte période comme une preuve.
- Aucun conseil d'investissement personnalisé : ce sont des résultats de backtest.
