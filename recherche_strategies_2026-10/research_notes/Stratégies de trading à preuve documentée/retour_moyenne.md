# Retour à la moyenne à court terme (short-term mean reversion) : preuves, règles exactes, limites

Date de rédaction des notes : 14 octobre 2026. Méthode : recherche web + lecture intégrale de plusieurs PDF/pages. Plusieurs pages clés de Quantified Strategies (QS) sont bloquées par une vérification anti-bot ou payantes (Substack) : leurs chiffres ne sont donc cités que lorsque j'ai pu les lire ou lorsqu'ils proviennent d'un résumé de moteur de recherche (signalé « non vérifié »). Titres d'articles et citations laissés en anglais.

Légende de fiabilité utilisée plus bas : **[ACAD]** = article évalué par des pairs / working paper académique ; **[PRAT-TRANSPARENT]** = praticien qui publie règles + données + période ; **[VENDEUR/BLOG]** = site commercial ou blog, non audité.

---

## 1. Règles EXACTES et reproductibles (RSI(2) Connors/Alvarez, IBS, N baisses consécutives, Bollinger) et paramètres standards de la littérature

### Takeaway
La version « canonique » du RSI(2) est : clôture > SMA 200 jours, RSI(2) < 5 (à l'origine < 10), achat à la clôture, sortie dès que la clôture repasse au-dessus de la SMA 5 jours, sans stop. L'IBS est (Close − Low)/(High − Low) avec seuils usuels 0,2 (achat) / 0,8 (vente). Il n'existe pas UNE version standard : seuils, sorties et filtres varient selon les sources, et plusieurs seuils ont été choisis sur les données (10→5, 90→95).

### Cited Findings

**RSI(2) — règles de base (version simple)**
- Long : clôture > SMA 200 jours ET RSI(2) ≤ 5 ; Connors note que le seuil d'origine était 10 mais que les rendements étaient meilleurs à 5. Short miroir : clôture < SMA 200 ET RSI(2) ≥ 95 (seuil d'origine 90, 95 donne de meilleurs rendements). Sortie long : clôture au-dessus de la SMA 5 jours ; sortie short : sous la SMA 5. Filtre optionnel : attendre que RSI(2) repasse > 50 après une lecture survendue. Connors ne préconise pas de stops et dit qu'ils dégradent la performance sur actions et indices (« stops hurt performance »). Achat « juste avant la clôture » privilégié par Connors vs ouverture suivante. — [StockCharts ChartSchool, RSI(2)](https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2)
- Résumé du livre *Short Term Trading Strategies That Work* (Connors & Alvarez, 2008) par l'évaluateur CXO : règles « buy pullbacks, not breakouts », « buy above, not below, the 200-day MA », « buy fear, not greed », « do not use stops », « hold overnight », RSI 2 périodes, signaux VIX ; données quotidiennes 1995–2007, « 8 million trades of stocks ». — [CXO Advisory, "A Few Notes on Short Term Trading Strategies That Work"](https://www.cxoadvisory.com/technical-trading/a-few-notes-on-short-term-trading-strategies-that-work/)
- Test reproduit sur S&P 500 (indice) : indice > SMA 200, RSI(2) < 5, achat à la clôture, sortie quand l'indice clôture > SMA 5. — [Stocks & Research, "Testing The RSI 2 Trading Strategy On US Stocks"](https://stocksoftresearch.com/rsi-2-trading-strategy/)
- Variante « cumulative RSI » : somme des deux dernières valeurs RSI(2) < 35 (indices/SPY) ou < 10 (actions), prix > SMA 200, sortie quand RSI(2) clôture > 65. Univers actions : volume moyen 100 j > 250 000 titres, prix > 5 $, max 10 positions, classement par RSI le plus bas. — [Stocks & Research](https://stocksoftresearch.com/rsi-2-trading-strategy/)
- Autre version publiée (Trading Time Machine, mars 2026) : achat à l'ouverture suivante si clôture > SMA 200 ET clôture < SMA 5 ET RSI(2) < 10 ; sortie à l'ouverture suivante si clôture > SMA 5 ; aucun stop ; 4 positions max, le RSI(2) le plus bas prioritaire. — [Trading Time Machine, "The 2-Period RSI"](https://backtest.substack.com/p/the-2-period-rsi-a-simple-system)
- Variante « R3 » (livre *High Probability ETF Trading*, 2009) telle que décrite par un résumé de moteur de recherche d'une page QS payante : clôture > SMA 200, RSI(2) baisse 3 jours de suite (première baisse partant de < 60), RSI(2) < 10 le jour du signal, sortie quand RSI(2) > 70 ; testée sur 20 ETF liquides. **Règles exactes non vérifiées : page payante**. — [Quantified Strategies, "Larry Connors R3 strategy"](https://quantifiedstrategies.substack.com/p/larry-connors-r3-strategy-it-still-795) (partie visible : livre, 20 ETF liquides, 21 sept. 2024)
- Version testée par Backtrex (mêmes règles que ci-dessus, avec côté short) : RSI(2) < 5 & clôture > SMA 200 → long ; RSI(2) > 95 & clôture < SMA 200 → short ; sortie = clôture repasse de l'autre côté de la SMA 5 OU de la SMA 200 ; stop « large » ; pas de take-profit. — [Backtrex S&P 500](https://backtrex.com/en/backtests/connors-rsi-2-sp-500)

**IBS (Internal Bar Strength)**
- Formule : IBS_t = (Close_t − Low_t) / (High_t − Low_t), de 0 (clôture au plus bas) à 1 (au plus haut) ; « 1-period Stochastic Oscillator ». Distribution en U ; 54,5 % des valeurs > 0,5. — [Pagonidis, *The IBS Effect: Mean Reversion in Equity ETFs* (NAAIM, 2013/2014)](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf)
- Règle « simple IBS » de Pagonidis : long à la clôture si IBS ≤ 0,2, short si IBS ≥ 0,8 ; entrée à la clôture, sortie à la clôture suivante (holding 1 jour). La relation n'est pas linéaire : seuils d'efficacité approximatifs 0,4 (en dessous) et 0,9 (au dessus). — [Pagonidis](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf)
- Filtre IBS démontré par l'auteur : stratégie long-only « Cutler's RSI(3) < 10 à la clôture, conserver tant que RSI(3) reste sous un seuil de 40 (symbole de comparaison illisible dans l'extraction PDF) », avec condition supplémentaire « n'entrer/ne conserver que si IBS ≤ 0,5 ». — [Pagonidis](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf)
- Réplication arXiv 2023 : IBS sur 15 ETF pays, 2009–2019 ; IBS_n avec n = 1 par défaut ; règles de Pagonidis citées (long IBS < 0,2, short IBS > 0,8) ; stratégie « Min-Max » : long l'ETF à l'IBS minimum et short celui à l'IBS maximum du jour, entrée à la clôture, sortie à la clôture suivante. — [arXiv 2306.12434, "Using Internal Bar Strength as a Key Indicator for Trading Country ETFs"](https://arxiv.org/html/2306.12434v1)
- Version QS « IBS + RSI » : IBS < 0,25 (barres quotidiennes) ET RSI(21) < 45, achat à la clôture, sortie quand la clôture dépasse la clôture précédente ; données depuis janv. 2000 ; 100 % du capital par trade ; taxes ignorées. **Chiffres de résultats non lisibles (payant)**. — [Quantified Strategies, "S&P 500 Mean Reversion Using IBS and RSI"](https://quantifiedstrategies.substack.com/p/s-and-p-500-mean-reversion-using-19a) (via résumé de recherche, non vérifié)

**Autres règles « N baisses consécutives »**
- « 3 jours de baisse » : SPY baisse 3 jours de suite en clôture ; entrée à la clôture du 3e jour ; sortie à l'ouverture du lendemain (variante : à la clôture du lendemain) ; données 1993–aujourd'hui (Amibroker). Règles complètes derrière paywall. — [Quantified Strategies, "3 days down overnight trading strategy"](https://quantifiedstrategies.substack.com/p/3-days-down-overnight-trading-strategy-942)
- Version indépendante : SPY avec Open, High ET Close tous plus bas 3 jours de suite ; achat à la clôture du 3e jour, vente 1 jour plus tard ; données dès 1995. — [R-bloggers, "3 weak days in a row" (2010)](https://www.r-bloggers.com/2010/12/3-weak-days-in-a-row/)

**Bollinger / « clôture sous la bande »**
- Je n'ai trouvé aucune source avec règles complètes ET résultats chiffrés et vérifiables pour « acheter une clôture sous la bande de Bollinger inférieure » sur indice. Les occurrences trouvées sont des scripts TradingView/PineForge sans statistiques indépendantes, et un test Backtrex « Bollinger + stochastique » sur USD/CAD 1 h qui perd −42,5 %. — [Backtrex, liste des backtests](https://backtrex.com/en/backtests)

**Sensibilité des « paramètres standards »**
- Les seuils 10→5 et 90→95 ont été choisis par Connors parce que les rendements « étaient meilleurs » : sélection en échantillon. — [StockCharts ChartSchool](https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2)
- Arthur Hill (StockCharts) a choisi RSI(5) 30/70 parce qu'il franchit 30/70 « plus souvent » que RSI(10)/(14), et 30/70 plutôt que 25/75 ou 20/80 pour la même raison — critère de fréquence de signaux, pas de robustesse. — [StockCharts SystemTrader 2016](https://articles.stockcharts.com/article/articles-arthurhill-2016-12-systemtrader---testing-and-tweaking-an-rsi-mean-reversion-system-for-spy-qqq-and-ijr/)
- Les sorties diffèrent d'une source à l'autre : clôture > SMA 5 (Connors/StockCharts/Backtrex), RSI(2) > 65 (cumulative RSI), RSI(2) > 70 (R3), RSI(3) > 40 (Pagonidis), clôture > clôture précédente (QS IBS+RSI). — sources ci-dessus.

### Inferences
- Pour un test local sur CFD, la définition de référence la plus défendable est celle de Backtrex/StockCharts (RSI(2) < 5 ou < 10 ; clôture > SMA 200 ; sortie clôture > SMA 5 ; pas de stop ou stop très large), mais il faut la traiter comme UNE hypothèse parmi plusieurs et tester explicitement 5 vs 10 et la sortie SMA 5 vs RSI > 65.
- Le RSI de Cutler (moyenne simple) utilisé par Pagonidis n'est pas le RSI de Wilder : un RSI(2) de TradingView (Wilder) donnera des valeurs légèrement différentes — à vérifier à l'implémentation (non documenté dans les sources lues).
- L'IBS dépend de la définition de la « barre quotidienne » : Pagonidis exige des OHLC fiables d'ETF cotés (séance cash US) ; sur un CFD coté ~24 h, l'OHLC quotidien dépend de l'heure de coupure du broker et n'est pas équivalent.

### Gaps
- Tableaux chiffrés originaux du livre de Connors/Alvarez (rendement moyen à 1/2/5 jours par seuil RSI) : non trouvés (livre non accessible).
- Résultats QS (trades, % gagnants, gain moyen, drawdown) pour IBS, IBS+RSI, R3, Bollinger : paywall / anti-bot, non lisibles.
- Aucune source rigoureuse sur la règle « clôture sous bande de Bollinger » (voir plus haut).
- Page RSI-2 de QuantifiedStrategies.com et blog Alvarez Quant Trading : inaccessibles (anti-bot) / non trouvés par la recherche.

---

## 2. Résultats publiés (avec ou sans frais) et dégradation depuis 2010 puis 2020

### Takeaway
Les résultats d'origine (1995–2008) sont très flatteurs en % de trades gagnants (80–88 %) mais sans frais ni correction de data-mining. Les réplications indépendantes montrent une érosion nette après 2008 (rendement annualisé divisé, drawdown doublé) et, sur 2016–2026, un profit factor ~1,3–1,6 sur indices actions mais un rendement bien inférieur au buy & hold et une perte sur EUR/USD. Aucune étude indépendante, auditée et récente (2020–2026) n'existe à ma connaissance.

### Cited Findings

**Chiffres d'origine (livre) et réplication par Stocks & Research [PRAT-TRANSPARENT, sans frais pour l'indice]**
- Test 1 (S&P 500, RSI(2) < 5, > SMA 200, sortie > SMA 5) : livre 1995–2008 = 49 trades, 83,6 % gagnants, 522,92 points, tenue moyenne 3 j. Réplication de l'auteur 1/1/1995–1/1/2008 : 49 trades, 83,7 %, +3,91 %/an, drawdown max −6,48 %, CAR/MDD 0,60 (sans frais). 1/1/2008–1/1/2016 : 30 trades, 80 % gagnants, +1,35 %/an, drawdown max −13,19 %, CAR/MDD 0,10. — [Stocks & Research](https://stocksoftresearch.com/rsi-2-trading-strategy/)
- Test 2 (SPY, RSI cumulatif < 35) : livre mi-janv. 1993–1/1/2008 = 50 trades, 88 % gagnants, 65,53 points ; réplication de l'auteur sur la même période = 127 trades, 74 % gagnants, 42,56 points, drawdown −7,25 % (l'auteur ne sait pas expliquer l'écart avec le livre). 2008–2016 : 58 trades, 72,4 %, +1,76 %/an, drawdown −19,38 % (plus que doublé), perte de −11,5 % en 2011. — [Stocks & Research](https://stocksoftresearch.com/rsi-2-trading-strategy/)
- Test 3 (actions S&P 1500, 1995–2016, commission 0,01 $/action, sans slippage) : 8 711 trades, 64,7 % gagnants, +23,86 %/an, drawdown −21,36 % ; meilleures années au début (> 80 % en 1997, 1999, 2000), les années récentes « nowhere near as well » ; l'auteur : « hard to say whether the strategy is broken or not ». Livre : 77 068 signaux 1995–2008, 69 % gagnants. — [Stocks & Research](https://stocksoftresearch.com/rsi-2-trading-strategy/)

**Tests récents 2016–2026 [VENDEUR/BLOG transparent : Backtrex, Oct 2026]** — mêmes règles pour tous, long ET short, 10 000 $ de départ, 100 % du capital par trade, commission 0,02 %/côté (pas de slippage ni swap mentionnés), bougies fermées :

| Marché (D1) | Rdt total | CAGR | Max DD | Profit factor | Trades | % gagnants | Gain moy. / perte moy. | Buy & hold (CAGR / DD) |
|---|---|---|---|---|---|---|---|---|
| Nasdaq 100 | +26,9 % | +2,4 % | −25,0 % | 1,55 | 65 | 75,4 % | +1,58 % / −3,11 % | +20,2 % / −35,7 % |
| S&P 500 | +18,1 % | +1,7 % | −21,5 % | 1,43 | 73 | 71,2 % | +1,22 % / −2,10 % | +13,5 % / −35,0 % |
| DAX | +14,4 % | +1,4 % | −12,9 % | 1,30 | 72 | 66,7 % | +1,30 % / −2,00 % | +9 % / −40 % |
| EUR/USD | −4,5 % | −0,5 % | −6,6 % | 0,78 | 75 | 54,7 % | +0,41 % / −0,62 % | 0 % / −23,3 % |

— sources : [Nasdaq 100](https://backtrex.com/en/backtests/connors-rsi-2-nasdaq-100), [S&P 500](https://backtrex.com/en/backtests/connors-rsi-2-sp-500), [DAX](https://backtrex.com/en/backtests/connors-rsi-2-dax), [EUR/USD](https://backtrex.com/en/backtests/connors-rsi-2-eur-usd)
- Taux de réussite d'équilibre : ≈ 63 % (S&P), ≈ 61 % (DAX), ≈ 66 % (Nasdaq), ≈ 60 % (EUR/USD) ; la marge sur 10 ans est mince (DAX : 6 points au dessus). — mêmes pages.
- Détail annuel S&P 500 : 2018 −9,8 % (7 trades, 3 gagnants : « pullbacks above the 200-day average turned into deeper sell-offs »), 2019 −3,0 %, 2020 −1,3 %, 2022 +0,9 %, 2023 −1,1 %, 2024 +8,6 %, 2025 +6,4 %. Nasdaq 100 : 2020 −12,2 % (2 trades, perdants), 2022 +10,4 %. DAX : 2021 −4,0 %, 2022 +8,5 %, « roughly flat since 2023 ». — mêmes pages.
- Le stop large n'a été touché que 1 à 3 fois sur 65–73 trades (EUR/USD : stop de 400 pips jamais touché). — mêmes pages.

**Autres résultats chiffrés**
- Actions Nasdaq 100, déc. 2006–fin 2025 (RSI(2) < 10, > SMA 200, < SMA 5, sans stop, 4 positions) : rendement annuel 17,84 %, 64,33 % gagnants, gain moy. +2,33 % / perte moy. −3,02 %, profit factor 1,45, drawdown max 29,15 %, Sharpe 1,10 ; commissions, slippage et taxes non mentionnés ; nombre de trades non indiqué. L'auteur juge le profit factor mince (cible 1,65+). — [Trading Time Machine](https://backtest.substack.com/p/the-2-period-rsi-a-simple-system)
- RSI(5) 30/70 sur SPY/QQQ/IJR, déc. 2000–déc. 2016, filtre golden cross S&P (SMA50 > SMA200), exécution à l'ouverture suivante, 10 $/trade : % gagnants moyen 78 %, exposition 20–35 %, CAR IJR > 10 %/an ; SPY buy & hold ≈ 5,22 %/an avec 55 % de drawdown, le « golden cross » seul ≈ 7 %/an et ≈ 20 % de drawdown ; pas de profit factor ni nombre de trades. — [StockCharts SystemTrader](https://articles.stockcharts.com/article/articles-arthurhill-2016-12-systemtrader---testing-and-tweaking-an-rsi-mean-reversion-system-for-spy-qqq-and-ijr/)
- RSI(2) avec taille de position progressive, S&P 500 depuis 2000-01-01 (fin non indiquée, billet de 2009), long RSI(2) < 20/15/10/5 (tailles 0,25 → 1), short miroir 80/85/90/95, sans filtre de tendance : 516 trades long / 607 short ; % gagnants long 53–63 %, short 49–58 % ; ratio gain/perte moyen long pleine taille 0,95 (médian 0,71) ; drawdown max −15,7 % (oct. 2008), −9,1 % en 2001–2002 ; conclusion de l'auteur : creux rapides mais « months to recover ». — [R-bloggers, "RSI(2) Evaluation"](https://www.r-bloggers.com/2009/06/rsi2-evaluation/)
- « 3 jours de baisse » SPY 1995–2010 (Open/High/Close tous en baisse), avec frais 0,03 %/trade + 6 $ : +2,65 %/an, écart-type 4,94 %, Sharpe 0,54, 57 % gagnants, profit factor ≈ 1,55 ; l'auteur : « not impressive » seul. — [R-bloggers](https://www.r-bloggers.com/2010/12/3-weak-days-in-a-row/)
- « 3 jours de baisse » SPY depuis 1993 selon un résumé de moteur de recherche d'une page QS (**non vérifié, page bloquée**) : 643 trades, gain moyen 0,13 %/trade, 65 % gagnants, drawdown max 8 % (sortie à l'ouverture) ; sortie à la clôture : 0,24 %, 60 %, drawdown 17 %. — [Quantified Strategies](https://www.quantifiedstrategies.com/3-days-down-overnight-trading-strategy/)

**Preuve IBS [PRAT / préprint]**
- Pagonidis (ETF actions, de la création de chaque ETF au 5 déc. 2013) : rendement moyen close-to-close du lendemain = +0,35 % quand IBS < 0,20 et −0,13 % quand IBS > 0,80 (résumé) ; dans le corps du texte : +38 pb (bucket bas) et −14 pb (bucket haut) — légère incohérence interne. Différence de probabilité de jour haussier entre buckets extrêmes ≈ 11,2 points. Rendement annuel « de plus de 30 % avant coûts » sur 19 ans. Les coûts de transaction : l'auteur affirme qu'ils ne sont « pas un facteur limitant » en liquidité mais écrit aussi que « commissions will greatly decrease the returns and increase the maximum drawdowns », rendant l'IBS seul « problematic in the real world ». — [Pagonidis](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf)
- Réplication 2009–2019 sur 15 ETF pays : stratégie Min-Max Sharpe 2,91 (100 % du temps investi) ; meilleur panier Sharpe 3,90 (N=2, sélectionné parmi des combinaisons aléatoires → biais de sélection) ; long-only 1,71, short-only 0,84 ; la performance diminue quand la durée de détention passe de 1 à 4 jours ; entrée à l'ouverture suivante au lieu de la clôture : Sharpe du meilleur panier 3,73 → −0,25 ; coûts : emprunt 0,01 %/jour, commissions exclues, slippage non chiffré. — [arXiv 2306.12434](https://arxiv.org/html/2306.12434v1)

**Dégradation / sens de l'autocorrélation**
- Autocorrélation d'ordre 1 des rendements quotidiens d'indices : autour de +0,05 depuis 1951, en baisse continue depuis les années 1980, changement de signe dans les années 2000, négative depuis ; 20 indices, 15 pays ; lié à la montée de l'indexation (futures, ETF, fonds indiciels). Une stratégie contre MAC(5) sur tous les indices donnerait un Sharpe annuel de 0,63 (0,67 pour le S&P 500 seul) après le 2 mars 1999 ; Sharpe similaires sur futures et ETF. Coûts non évoqués dans le passage lu. — [Baltussen, van Bekkum & Da (2019), JFE](https://academicweb.nd.edu/~zda/Indexing.pdf)
- Résumé (non vérifié, SSRN bloqué) d'un working paper Hu, Jin & Wang : autocorrélation quotidienne des rendements US 1897–2024, positive et maximale dans les années 1970, durablement négative après 2000, quelques pertes extrêmes expliquant une grande part du négatif. — [SSRN 5314371](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5314371)
- Mean-Reversion Is Waning (Price Action Lab, sept. 2021) : titre confirmé, **corps payant et éditeur vendeur de signaux** — non utilisable. — [Price Action Lab](https://www.priceactionlab.com/Blog/2021/09/mean-reversion-waning/)

### Inferences
- Ordre de grandeur cohérent entre sources indépendantes : sur indices, RSI(2) long/short avec filtre SMA 200 → profit factor 1,3–1,6, 65–75 % de gagnants, gain moyen ≈ 0,5× la perte moyenne, exposition faible (≈ 7–10 trades/an), CAGR 1,4–2,4 % sur 2016–2026 (Backtrex) — soit un résultat positif mais très inférieur au buy & hold, et pouvant être inférieur au drawdown cumulé.
- L'espérance par trade du test S&P Backtrex ≈ 0,712×1,22 − 0,288×2,10 ≈ +0,26 % (frais 0,04 % aller-retour inclus) : c'est de cet ordre de grandeur que les swaps et spreads CFD (voir Q5) doivent être déduits.
- Une partie de la baisse post-2008 est cohérente avec le basculement de signe de l'autocorrélation (indexation) : le retour à la moyenne quotidien d'indice a augmenté en intensité mais le nombre de signaux « filtrés par SMA 200 » reste faible ; attention, c'est une interprétation, non démontrée dans les sources.
- Le grand écart entre « 80–88 % de gagnants » du livre et ≈ 55–75 % en réplication indépendante illustre l'effet data-mining/seuils choisis in-sample.

### Gaps
- Aucune réplication indépendante à frais réalistes, couvrant 2020–2026, sur CFD indices/or/FX, publiée par un tiers non commercial.
- Aucun chiffre vérifiable de QS (PF, trades) : pages bloquées.
- Résultats Alvarez Quant Trading post-2008 : introuvables (recherche sans résultat).
- Aucune étude trouvée du RSI(2) sur matières premières (or, pétrole, gaz) avec chiffres.

---

## 3. Comportement en marché baissier durable (2000–2002, 2008, 2022) : pertes de la version long-only ? Version short/hedgée solide ?

### Takeaway
Les sources ne montrent pas de pertes catastrophiques de la version long-only avec filtre SMA 200 (le filtre l'écarte des phases baissières), mais des séries de pertes lors des retournements/« faux rebonds » (2018, 2020, 2021) et des drawdowns qui doublent après 2008. Il n'existe pas de preuve solide, longue et indépendante d'une version short/hedgée robuste : seulement des signes positifs en 2022 (côté short du même système) sur échantillons de 5 à 9 trades.

### Cited Findings
- Version sans filtre de tendance, long + short, S&P 500 depuis 2000 : drawdown max −15,7 % en octobre 2008 (récupéré en quelques semaines) et −9,1 % en 2001–2002 (≈ 96 jours pour creux + récupération) ; auteur : « prone to drawdowns that trough quickly but take months to recover from ». Taille progressive limitant l'exposition. — [R-bloggers, "RSI(2) Evaluation"](https://www.r-bloggers.com/2009/06/rsi2-evaluation/)
- Version long-only avec SMA 200, S&P 500 : max DD −13,19 % (2008–2016) vs −6,48 % (1995–2008), CAR/MDD 0,60 → 0,10. — [Stocks & Research](https://stocksoftresearch.com/rsi-2-trading-strategy/)
- 2022 (version long + short, SMA 200, 2016–2026) : Nasdaq 100 +10,4 % (5 gagnants/7), DAX +8,5 %, EUR/USD +4,8 %, S&P 500 +0,9 % (8 trades) ; l'auteur Backtrex attribue 2022 au fait que l'indice est resté sous sa SMA 200 (seul le côté short actif). 2020 : Nasdaq −12,2 % (deux trades perdants, « pullback that kept going »). — [Backtrex Nasdaq 100](https://backtrex.com/en/backtests/connors-rsi-2-nasdaq-100), [S&P 500](https://backtrex.com/en/backtests/connors-rsi-2-sp-500), [DAX](https://backtrex.com/en/backtests/connors-rsi-2-dax), [EUR/USD](https://backtrex.com/en/backtests/connors-rsi-2-eur-usd)
- Actions Nasdaq 100 : l'auteur dit « noticeably shallower drawdowns » en 2008 et 2022 mais ne donne aucun chiffre annuel (max DD global 29,15 %). — [Trading Time Machine](https://backtest.substack.com/p/the-2-period-rsi-a-simple-system)
- Effet IBS en marché baissier (rendement 200 jours négatif) : « roughly similar in each environment (slightly larger in bear markets) », plus fort dans le sens de la tendance : les IBS hauts sont suivis de baisses plus fortes en bear market ; le côté short n'a « no predictive ability » en faible volatilité ; l'effet est plus fort en forte volatilité et après journées de grande amplitude ; échantillon jusqu'à décembre 2013, ETF US. — [Pagonidis](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf)
- Rendement de la liquidité (reversal) : espérance et Sharpe conditionnels augmentent fortement avec le VIX (crise 2007–09) ; interprétation = les fournisseurs de liquidité se retirent en période de stress. — [Nagel (2012), "Evaporating Liquidity", RFS / NBER w17653](https://www.nber.org/papers/w17653)
- Côté short du reversal d'actions : le profit vient du sentiment (contraintes de vente à découvert), côté long de chocs de liquidité (fire sales). — [Da, Liu & Schaumburg (2014), Management Science](https://academicweb.nd.edu/~zda/Reversal.pdf)
- Évaluateur CXO sur le livre : les analyses « do not examine variability, drawdowns, or "Black Swan" wipeouts » ; pas de test par sous-périodes. — [CXO Advisory](https://www.cxoadvisory.com/technical-trading/a-few-notes-on-short-term-trading-strategies-that-work/)
- StockCharts : Connors ne met pas de stop ; l'article avertit que cela peut conduire à des pertes « outsized » et de gros drawdowns ; les signaux sont souvent précoces (le prix continue dans le sens du signal avant de revenir). — [StockCharts ChartSchool](https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2)
- Un forum StockCharts (anecdotique, non vérifié) rapporte que Connors tiendrait la position jusqu'à RSI(2) > 50 « même si c'est un énorme perdant » (résumé de recherche). — [StockCharts forum](https://scan.stockcharts.com/discussion/comment/5401)

### Inferences
- Le filtre SMA 200 déplace le risque : en 2008 et 2022 il évite l'essentiel du long, mais l'entrée suit des rebonds dans des marchés encore fragiles, et sort mal après un choc rapide (2020 : les entrées « au-dessus de la SMA 200 » précèdent le krach de février–mars 2020 avec une SMA encore haussière). C'est un déduction à partir du cas Nasdaq 2020 de Backtrex, pas une démonstration.
- Les phases à forte volatilité sont à la fois celles où le reversal paie le plus (Nagel, IBS) et celles où un long « sans stop » prend les plus grosses pertes en cas de tendance (2008, 2020). Le filtre SMA 200 exclut une grande partie de ce gisement de rendement ; d'où une exposition faible.
- La preuve sur le côté short/hedgé est mince : < 10 trades par an, une année favorable (2022). Rien dans les sources ne démontre une version short robuste sur plusieurs bear markets (2000–02, 2008). À traiter comme non démontrée.

### Gaps
- Aucune série annuelle fiable 2000–2002, 2008 pour la version canonique long-only avec SMA 200 sur indice ; le seul chiffre est le drawdown max global (−6,48 % 1995–2008, qui inclut 2000–2002, pour 49 trades).
- Aucune source donnant la perte maximale par trade ou la distribution des pertes sans stop (risque de queue chiffré) pour RSI(2).
- Version short/hedgée « solide » : introuvable ; Backtrex n'isole pas long et short (l'auteur recommande lui-même de tester les côtés séparément).

---

## 4. Qualité de la preuve : académique vs blogosphère ; sensibilité aux paramètres ; risques de queue

### Takeaway
Le fait stylisé « les rendements à très court terme se retournent » est académiquement établi (actions individuelles, depuis Lehmann/Jegadeesh 1990 ; indices depuis les années 2000), mais aucune étude évaluée par des pairs n'a testé RSI(2) ou IBS en tant que tels : ces règles reposent sur des livres, newsletters et blogs. Les effets mesurés sont petits (autocorrélation d'ordre 1 ≈ −0,08 selon un préprint non vérifié ; Sharpe 0,6 dans le papier JFE), concentrés sur actifs illiquides pour les actions, et sensibles aux coûts.

### Cited Findings

**Académique [ACAD]**
- Lehmann (1990, QJE, « Fads, Martingales, and Market Efficiency ») : les gagnants/perdants d'une semaine inversent la semaine suivante, des profits d'arbitrage apparents persistant après corrections pour écarts bid-ask et coûts plausibles ; attribué à un marché de la liquidité autour des gros mouvements. — [NBER w2533](https://www.nber.org/papers/w2533)
- Jegadeesh (1990, JF) : profits d'environ 2 %/mois sur 1934–1987 pour une stratégie de reversal mensuelle (tenue 1 mois), selon Da et al. ; profits « not readily explainable by direct transaction costs ». (Un résumé secondaire donne 1965–1989 : écart d'échantillon non résolu.) — [Da, Liu & Schaumburg](https://academicweb.nd.edu/~zda/Reversal.pdf)
- Avramov et al. (2006) cité par Da et al. : les profits du reversal standard viennent principalement de petites capitalisations, à fort turnover, illiquides. Da et al. 2014 : un reversal « amélioré » (en utilisant des révisions d'analystes) génère un rendement ajusté du risque 4× le standard ; l'effet persiste chez les grandes valeurs sur les années récentes (résumé de moteur de recherche). — [Da, Liu & Schaumburg](https://academicweb.nd.edu/~zda/Reversal.pdf)
- Lo & MacKinlay (1990) contestent : une large part des profits serait due à des réactions retardées aux facteurs communs plutôt qu'à la sur-réaction (résumé secondaire, non vérifié). — [résumé via recherche web sur Lehmann/Jegadeesh](https://www.nber.org/papers/w2533)
- Baltussen, van Bekkum & Da (JFE 2019) : changement de signe de la dépendance sérielle des indices dans les années 2000, lié à l'indexation (voir Q2). — [Baltussen et al.](https://academicweb.nd.edu/~zda/Indexing.pdf)
- Un préprint arXiv 2026 sur SPY donne une autocorrélation lag-1 ≈ −0,081 (soit environ −0,08 % le lendemain d'un mouvement de +1 %) et soutient que la prévisibilité est surtout dans l'amplitude, pas la direction ; **préprint non vérifié, chiffres provisoires**. — [arXiv 2606.29591](https://arxiv.org/html/2606.29591v1)

**Évaluation critique du livre RSI(2) [PRAT]**
- Cinq critiques de l'évaluateur CXO : (1) data snooping non corrigé, pas d'out-of-sample ; (2) variabilité/drawdowns/« Black Swan » non examinés ; (3) pas de sous-périodes (anomalies pouvant disparaître avec la publication) ; (4) capacité et concentration des signaux non explorées ; (5) sensibilité aux frictions non explorée. Conclusion : extraire une valeur économique fiable après frictions est difficile en gestion continue. — [CXO Advisory](https://www.cxoadvisory.com/technical-trading/a-few-notes-on-short-term-trading-strategies-that-work/)
- L'auteur de la réplication Stocks & Research suspecte que le marché soit devenu plus efficient ou que la stratégie soit trop connue ; il relève l'impossibilité de répliquer exactement le livre sur SPY. — [Stocks & Research](https://stocksoftresearch.com/rsi-2-trading-strategy/)
- Évaluation de l'édge FX pour règles techniques simples : profits réels dans les années 1970–1980, disparus au début des années 1990 pour règles filtre/MM ; moins nette pour des règles moins étudiées (compatible avec une érosion adaptative). — [Neely, Weller & Ulrich (2009), JFQA](https://econpapers.repec.org/paper/fipfedlwp/2006-046.htm)

**Sensibilité / robustesse des stratégies**
- IBS : l'effet existe surtout les jours à fort volume pour les ETF US (« completely disappears on low volume days »), plus fort le lundi, le plus faible le vendredi ; basculement du résultat selon l'heure d'entrée (clôture vs ouverture suivante : Sharpe 3,73 → −0,25 dans la réplication arXiv). — [Pagonidis](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf), [arXiv 2306.12434](https://arxiv.org/html/2306.12434v1)
- Backtrex : le pourcentage de gagnants (55–75 %) reste proche du seuil de rentabilité (60–66 %) car perte moyenne ≈ 1,5–2× gain moyen. — [Backtrex](https://backtrex.com/en/backtests/connors-rsi-2-sp-500)
- Un article ProRealCode note la sensibilité : essais RSI(2) sur graphique 30 min « mostly unprofitable » ; résultats D1 mixtes (retours d'utilisateurs, anecdotique). — [ProRealCode, RSI-2 Strategy](https://www.prorealcode.com/prorealtime-trading-strategies/rsi-2-strategy-larry-connors/?pnum=2)

**Risque de queue**
- Pas de stop (règle d'origine) : perte moyenne ≈ 1,5–2× gain moyen sur 10 ans même avec stop large rarement touché (1–3 fois) ; suite maximale de pertes 2–5 trades. — [Backtrex](https://backtrex.com/en/backtests/connors-rsi-2-nasdaq-100)
- Skewness du rendement du lendemain d'un IBS bas : +0,65 (bucket bas) vs +0,03 (bucket haut) — c'est un biais haussier de la queue de droite après un IBS bas, pas une preuve d'absence de queue gauche. — [Pagonidis](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf)

### Inferences
- Aucun résultat des sources ne permet de distinguer, pour RSI(2) sur indices, un véritable alpha d'un échantillon favorable ; la littérature académique soutient le principe, pas la règle.
- Le très faible nombre de trades (≈ 5–10/an) rend l'intervalle de confiance du profit factor très large : 65–75 trades suffisent à peine à distinguer un PF de 1,3 d'un PF de 1,0 (inférence statistique générale, non chiffrée dans les sources).
- Un test fiable pour un usage CFD devrait contrôler : (1) dérive haussière (comparer à « long quand clôture > SMA 200 » sans signal RSI) ; (2) découpage 2010/2020 ; (3) variation 5/10 et sorties ; (4) coûts CFD réels (Q5).

### Gaps
- Aucune étude peer-reviewed isolant RSI(2) ou IBS sur indices ; l'article de Pagonidis est une newsletter NAAIM, non évaluée par des pairs, et le préprint arXiv 2023 n'a pas de t-stats.
- Les chiffres de dégradation « post-publication » de McLean & Pontiff ou de Quantpedia sur le short-term reversal n'ont pas été retrouvés dans cette session.
- Distribution complète des pertes (pire trade) non publiée dans les sources lues.

---

## 5. Applicabilité aux CFD (SPX500/US100/GER40/FR40, or, FX) avec frais/swaps retail, positions 1–5 jours

### Takeaway
Le reversal quotidien est documenté pour les indices US, beaucoup moins pour GER40/FR40, très peu pour FX et matières premières (où la littérature trouve plutôt du momentum hebdomadaire). Pour un CFD retail, le coût de portage nocturne (≈ 0,017–0,023 %/nuit sur indices en long, 0,033 %/nuit sur l'or, 0,10 %/nuit sur BTC en long) consomme une part significative d'un gain moyen de 0,3–1,2 % par trade.

### Cited Findings

**Coûts XTB (table du 13 avril 2026, en % par jour du nominal, débit chaque nuit à minuit)**
- Indices (colonnes Long / Short ; position courte : le coût ne peut pas être positif) : US500 −0,022859 % / −0,001139 % ; US100 −0,017864 % / −0,001139 % ; FRA40 −0,022472 % / −0,007136 % ; DE40 : seule la valeur courte (−0,007136 %) est lisible sans ambiguïté dans mon extraction ; EU50 −0,017864 % / −0,007136 %. — [XTB, Table des points de swap, taux et coûts de financement (13-04-2026)](https://xas-new-cdn.xtb.com/file/0090/17/e10a90ed-c5cc-440e-bdfc-9197a1566372/swaps-fr.pdf)
- Matières premières : GOLD −0,033306 % (long) / −0,013361 % (short) ; OIL, OIL.WTI, NATGAS −0,041639 % / −0,021694 %. Crypto : BITCOIN −0,097222 % (long) / −0,027778 % (short). — même document.
- FX : valeurs très faibles, p. ex. EURUSD −0,003705 % / +0,008117 % et USDJPY +0,004478 % / −0,011416 % (l'attribution long/short des colonnes est ambiguë dans l'extraction, à vérifier dans xStation) ; formule FX basée sur les différentiels de taux (ESTER, SOFR, TONAR…). — même document.
- XTB précise que, étant teneur de marché, la marge incluse dans les points de swap et coûts de financement peut aller jusqu'à 100 % ; le taux de base est ESTER (EUR) / SOFR (USD) / etc. — même document.
- Un classement tiers (BrokerChooser, mai 2026, via résumé de recherche, non vérifié) donne un coût de financement long de −8,0 % (S&P 500) et −6,5 % (EU 50) annualisés, « high compared with other brokers ». — [BrokerChooser, XTB CFD financing rate](https://brokerchooser.com/broker-reviews/xtb-review/cfd-financing-rate)
- Spreads XTB : valeurs indicatives (comparatif XTB janvier 2026) US100 0,9, GOLD 0,30, EURUSD 0,8 (unités non précisées) ; minimums FRA40 ≈ 0,8–1,1, DE30 0,9 ; spreads exécutés moyens historiques (branche allemande 2021–2022) US.500 ≈ 0,5, DE.30 ≈ 1,2–1,8, FRA.40 ≈ 1,1, GOLD ≈ 0,17–0,35 en points de prix. Valeurs indicatives, non garanties. — [XTB indices](https://xtb.com/en/indices), [XTB, spread moyen exécuté 1T 2022 (PDF)](https://de.xtb.com/hubfs/Informationen-zum-durchschnittlich-ausgefuehrten-Spread-bei-XTB_1Q2022.pdf) (via résumé de recherche, non vérifié)

**Applicabilité par marché**
- Indices US : meilleur cas (IBS et RSI(2) documentés ; PF 1,4–1,6 sur 2016–2026 chez Backtrex ; Sharpe 0,67 du reversal d'indice S&P 500 après 1999 chez Baltussen et al.). — [Backtrex](https://backtrex.com/en/backtests/connors-rsi-2-sp-500), [Baltussen et al.](https://academicweb.nd.edu/~zda/Indexing.pdf)
- Indices européens : Pagonidis constate que l'effet IBS n'existe pas (ou beaucoup moins) sur les ETF France, Autriche, Allemagne, Espagne, Suisse, Taïwan, Royaume-Uni ; « for the German DAX ETF, the effect is even inversed » ; effet « U.S.-centric » ; après 2008, l'effet sur ETF internationaux dépend de l'IBS de SPY ; le trading sur futures locaux « not viable » car l'effet n'apparaît qu'à la clôture US. Échantillon jusqu'en 2013 et ETF cotés aux US (non les futures DAX/CAC). — [Pagonidis](https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf)
- DAX (RSI(2), pas IBS) 2016–2026 : PF 1,30, 66,7 % gagnants, CAGR 1,4 %, 72 trades ; marge de gagnants la plus mince des trois indices testés. — [Backtrex DAX](https://backtrex.com/en/backtests/connors-rsi-2-dax)
- FX : RSI(2) sur EUR/USD 2016–2026 perd (PF 0,78, −4,5 %) ; l'auteur attribue cela à l'absence de dérive haussière de long terme sur une paire de devises. — [Backtrex EUR/USD](https://backtrex.com/en/backtests/connors-rsi-2-eur-usd). Plus largement, les règles techniques simples en FX ont perdu leur profit dès le début des années 1990. — [Neely, Weller & Ulrich](https://econpapers.repec.org/paper/fipfedlwp/2006-046.htm)
- Matières premières / futures : Kwon, Kang & Yun (2020, Finance Research Letters) trouvent du « strong short-term momentum, instead of short-term reversal » en hebdomadaire sur futures de matières premières, lié à l'activité spéculative (résumé de catalogue, texte complet non lu). — [KAIST, "Weekly momentum in the commodity futures market"](https://koasas.kaist.ac.kr/handle/10203/276677). À l'inverse, Quantpedia résume un reversal hebdomadaire sur 24 futures US (1983–2000), conditionné à volume élevé / open interest bas : +0,57 %/semaine (≈ 29,6 %/an arithmétique), Sharpe 0,82, avant coûts ; profits éliminés vers 0,16 % de coûts par dollar négocié. — [Quantpedia, Short Term Reversal with Futures](https://quantpedia.com/strategies/short-term-reversal-with-futures)
- Momentum intraday : sur plus de 60 futures (actions, obligations, matières, devises, 1974–2020), le rendement des 30 dernières minutes est prédit par le reste de la séance, puis l'effet s'inverse les jours suivants (résumé de dépôt institutionnel, non vérifié). Sur le S&P 500, le rendement de la première demi-heure prédit celui de la dernière (R² ≈ 0,02 dans une version). — [Baltussen, Da, Lammers & Martens, JFE](https://repub.eur.nl/pub/131621), [Gao, Han, Li & Zhou (2018), JFE](https://profiles.wustl.edu/en/publications/market-intraday-momentum/)

**Contraintes d'exécution**
- Les signaux (RSI, IBS) se calculent à la clôture : l'entrée « à la clôture » demande de prévoir la clôture ; « may prove difficult », et le slippage peut varier. — [Stocks & Research](https://stocksoftresearch.com/rsi-2-trading-strategy/). Entrée à l'ouverture suivante : l'edge IBS s'effondre (Sharpe 3,73 → −0,25). — [arXiv 2306.12434](https://arxiv.org/html/2306.12434v1)
- Le mode de calcul du financement CFD : prix × multiplicateur × lots × taux journalier ; débité à minuit chaque jour. — [XTB, table des swaps](https://xas-new-cdn.xtb.com/file/0090/17/e10a90ed-c5cc-440e-bdfc-9197a1566372/swaps-fr.pdf)

### Inferences
- Coût de financement long pour une durée de 3 à 5 nuits (calcul à partir de la table XTB) : US500 ≈ 0,069–0,114 % ; US100 ≈ 0,054–0,089 % ; FRA40 ≈ 0,067–0,112 % ; or ≈ 0,10–0,17 % ; pétrole/gaz ≈ 0,12–0,21 % ; Bitcoin ≈ 0,29–0,49 %. Annualisé : US500 long ≈ 8,3 %, or long ≈ 12,2 %, or short ≈ 4,9 %, pétrole long ≈ 15,2 %, BTC long ≈ 35,5 %. (Je ne sais pas si la nuit de week-end est triplée pour les indices : la table ne l'indique que pour quelques paires FX.)
- Pour comparaison : le gain moyen par trade du RSI(2) sur le S&P chez Backtrex est ≈ 1,2 % ; le gain moyen IBS d'une journée est de l'ordre de 0,35 % (brut, ETF, 1996–2013). Après swap 0,02 %/nuit + spread aller-retour, l'IBS 1 jour reste positif mais mince ; l'IBS multi-jours perd rapidement de l'edge (déclin de 1 à 4 jours dans arXiv 2306.12434) tandis que le portage s'accumule. Sur BTC, un long de 3 jours coûte ≈ 0,3 % de swap : peu compatible avec un reversal de l'ordre de 0,3 %.
- Les CFD indices US suivent les futures et cotent ~24 h : la « clôture quotidienne » IBS/RSI n'est pas celle des ETF cash utilisés dans la littérature. Il faudra choisir une heure de coupure fixe (clôture cash US 22:00 CET, par exemple) et tester la sensibilité.
- Pour GER40/FR40, la meilleure hypothèse de travail est RSI(2)-SMA 200 (PF ~1,3 sur DAX chez Backtrex) plutôt qu'IBS, et avec un attendu d'edge faible ; sur FX, matières premières et BTC, il n'y a pas de preuve et plutôt des indices contraires.
- Compatibilité avec le contexte : les stratégies déjà écartées (ICT sweep/MSS/FVG, cassure de range 5 j à 15 min, MACD+EMA200 1 h) sont des horizons intraday ; le RSI(2)/IBS est un signal D1 avec peu de trades (≈ 5–10 par an par actif), ce qui implique de longues périodes sans signal et un faible nombre de trades pour juger.

### Gaps
- Spreads XTB actuels pour US500, GER40, FR40, XAUUSD, EURUSD, USDJPY, USOIL, NATGAS, BTC : non trouvés de façon fiable (valeurs indicatives uniquement ; unités ambiguës).
- Colonne long/short exacte de DE40 dans la table XTB, et règle du triple swap pour indices/or : non établies à partir de l'extraction.
- Aucune étude chiffrée de RSI(2)/IBS sur XAUUSD, USOIL, NATGAS, USDJPY ou BTC en D1 (hormis EUR/USD et DAX chez Backtrex) ; la liste Backtrex contient un test « stochastic oversold, gold 4 h » (+104,5 % vs +217,9 % buy & hold) mais les détails n'ont pas été lus. — [Backtrex, liste](https://backtrex.com/en/backtests)
- Effet réel des CFD (écart entre prix CFD XTB et futures, gaps de week-end) non documenté dans les sources.
