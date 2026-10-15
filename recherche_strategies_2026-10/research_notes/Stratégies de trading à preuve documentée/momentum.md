# Momentum cross-sectionnel et momentum dual (relatif + absolu) : preuves, règles exactes, limites

Notes rédigées le 14 octobre 2026. Les titres d'articles et citations sont conservés en anglais. Convention : « [secondaire] » signale un chiffre rapporté par un tiers (blog, vendeur, résumé automatique d'un PDF) et non lu directement dans le papier ; « [non vérifié] » signale une donnée que je n'ai pas pu confirmer via une source.

## 1. Règles EXACTES et reproductibles (formation, rebalancement, classement, filtre absolu)

### Takeaway
Quatre « recettes » documentées existent : (a) Jegadeesh & Titman 1993 (décile d'actions, J/K en mois, pas d'application directe à un panier d'indices) ; (b) Asness-Moskowitz-Pedersen 2013 (rendement 12 mois en sautant le dernier mois, classement par rang, tiers ou pondération par rang) ; (c) GEM d'Antonacci (12 mois, mensuel, 2 tests imbriqués : absolu puis relatif) ; (d) GTAA de Faber (prix > SMA 10 mois, mensuel, 5 classes d'actifs à 20 %). Le « 12-1 » est le standard académique, le « 12 mois total return » le standard dual momentum, la SMA 10 mois le standard trend.

### Cited Findings
- **Jegadeesh & Titman (1993), « Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency », Journal of Finance 48(1)** : échantillon janvier 1965 – décembre 1989 ; actions classées en déciles sur le rendement des J derniers mois (J = 1 à 4 trimestres), détenues K mois (K = 1 à 4 trimestres), achat du décile gagnant et vente du décile perdant, périodes de détention superposées ; une seconde série de stratégies saute une semaine entre formation et détention. — [papier (PDF)](https://www.bauer.uh.edu/rsusmel/phd/jegadeesh-titman93.pdf) [lu via extraction automatique du PDF], [abstract IDEAS/RePEc](https://ideas.repec.org/a/bla/jfinan/v48y1993i1p65-91.html)
- **JT93 – chiffres clés** : stratégie J=6/K=6 : 0,95 %/mois (t = 3,07) sans décalage, 1,10 %/mois (t = 3,61) avec une semaine de décalage ; la meilleure combinaison est formation 12 mois / détention 3 mois : 1,31 %/mois (sans décalage), 1,49 %/mois (avec une semaine de décalage). — [papier (PDF)](https://www.bauer.uh.edu/rsusmel/phd/jegadeesh-titman93.pdf) [extraction automatique]
- **JT93 – limites déjà dans le papier** : une partie du gain de la première année se dissipe dans les deux années suivantes (le portefeuille formé sur 6 mois rapporte 9,5 % sur 12 mois puis perd plus de la moitié sur les 24 mois suivants) ; la stratégie perd environ 7 % en moyenne chaque mois de janvier ; le sous-échantillon des plus grandes capitalisations génère des rendements anormaux plus faibles. — [papier (PDF)](https://www.bauer.uh.edu/rsusmel/phd/jegadeesh-titman93.pdf) [extraction automatique]
- **Asness, Moskowitz, Pedersen (2013), « Value and Momentum Everywhere », Journal of Finance 68(3), 929-985** : momentum = rendement cumulé brut des 12 derniers mois en sautant le dernier mois ; titres classés par signal et répartis en trois groupes égaux (P1, P2, P3 ; pondération par capitalisation pour les actions individuelles, égale pour les autres classes) ; en parallèle, un « facteur » à pondération proportionnelle au rang (rang moins rang moyen), neutre au marché. — [papier (PDF)](https://w4.stern.nyu.edu/facdir/lpederse/papers/ValMomEverywhere.pdf) [extraction automatique], [version CBS](https://research.cbs.dk/files/44523827/lasse_heje_pedersen_value_and_momentum_postprint.pdf)
- **AMP 2013 – univers** : 8 marchés : actions US, UK, Europe continentale, Japon (échantillons de janvier 1972/1974 à juillet 2011) ; indices actions pays via futures (18 marchés développés, min. 8 ; depuis janvier 1978) ; devises (10 monnaies, min. 7 ; depuis janvier 1979) ; obligations d'État (10 pays ; depuis janvier 1982) ; matières premières (27 futures, min. 10 ; depuis janvier 1972). — [papier (PDF)](https://w4.stern.nyu.edu/facdir/lpederse/papers/ValMomEverywhere.pdf) [extraction automatique]
- **GEM (Global Equities Momentum), Antonacci, *Dual Momentum Investing* (2014)** : une fois par mois, (1) test absolu : rendement 12 mois du S&P 500 > rendement 12 mois des T-bills ? Si non : obligations agrégées ; (2) si oui, test relatif : S&P 500 vs MSCI ACWI ex-US sur 12 mois, détenir le plus fort. Implémentation citée : IVV / ACWX / AGG, ~1,3 transaction par an en moyenne. — [Medium, L. Leong 2026](https://medium.com/gradient-growth/global-equities-momentum-beat-the-market-for-16-years-then-i-ran-the-honest-out-of-sample-test-7fb458fe9b3b), [optimalmomentum.com (Antonacci)](https://www.optimalmomentum.com/extended-backtest-of-global-equities-momentum/), [Concretum, entretien avec Antonacci (oct. 2026)](https://concretumgroup.substack.com/p/gary-antonacci-from-dual-momentum)
- **Antonacci précise** : « We use a 12-month lookback period for both types of momentum and rebalance monthly » ; l'indice non-US large est choisi pour éviter le biais de sélection. — [optimalmomentum.com](https://www.optimalmomentum.com/extended-backtest-of-global-equities-momentum/)
- **Faber (2007, mises à jour 2009, 2013), « A Quantitative Approach to Tactical Asset Allocation », Journal of Wealth Management** : achat si le prix mensuel est > SMA 10 mois, sinon liquidités ; 5 classes d'actifs à 20 % chacune (S&P 500, MSCI EAFE, obligations US 10 ans, GSCI, NAREIT) ; rebalancement mensuel ; l'auteur estime 3 à 4 aller-retours par an pour le portefeuille et moins d'un par classe d'actifs ; les baselines excluent taxes, commissions et slippage. — [papier (PDF)](https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf) [extraction automatique]
- **Faber, variante « GTAA Aggressive »** (13 classes d'actifs) : classer par la moyenne des rendements 1, 3, 6 et 12 mois, retenir le top 6 (ou top 3) et ne garder un actif que s'il est au-dessus de sa moyenne mobile, sinon cash. — [papier (PDF)](https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf) [extraction automatique]
- Faber, « Revisited 10 Years Later » : utilise « the monthly version of the popular 200-day SMA indicator, the 10-month simple moving average ». — [Faber 2016](https://allocatortraining.com/wp-content/uploads/2023/06/A-Quantitative-Approach-to-Tactical-Asset-Allocation.pdf)
- **Time-series momentum, Moskowitz, Ooi, Pedersen (2012), JFE 104(2)** : 58 instruments liquides (futures actions, devises, matières premières, obligations) ; taille de position = 40 % / σ ex ante ; signal = rendement 12 mois. — [IDEAS/RePEc](https://ideas.repec.org/a/eee/jfinec/v104y2012i2p228-250.html), [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0304405X11002613)

### Inferences
- Paramètres « standards » reproductibles sans ambiguïté : formation 12 mois (éventuellement en sautant le dernier mois), rebalancement mensuel à la clôture du dernier jour du mois, filtre absolu = rendement 12 mois > T-bills (ou prix > SMA 10 mois), poids égaux.
- Aucune de ces règles ne contient de stop, de levier ni de timing intra-journalier : elles sont conçues pour du mensuel sur ETF/indices. Les transposer à du 15 min (comme les tests déjà écartés) n'a aucune base documentaire.

### Gaps
- Le papier original d'Antonacci sur le momentum absolu (SSRN 2244633 environ) n'a pas été lu directement ; les règles sont issues de ses pages et de tiers.
- Je n'ai pas pu lire la version complète du livre ; les règles « cash » exactes (T-bills vs obligations agrégées selon la variante) ont été prises sur des résumés.

---

## 2. Résultats publiés (CAGR, Sharpe, max drawdown, avec/sans frais), 2010–2025, « momentum crashes »

### Takeaway
Les résultats historiques sont solides mais tous bruts (ou quasi) et surtout in-sample (1950-2018) ; la littérature sérieuse documente aussi des effondrements violents du facteur long-short (1932, 2009) et une période post-publication plus difficile pour GEM. Je n'ai trouvé aucune série GEM 2010-2025 indépendante, fiable et nette de frais.

### Cited Findings
- **Antonacci, GEM 1950–2018 (backtest hypothétique, sans frais)** : CAGR 15,8 %, écart-type 11,5 %, Sharpe 0,96, pire drawdown -17,8 %, vs S&P 500 : 11,4 % / 14,2 % / 0,52 / -51,0 % ; momentum relatif seul : 13,4 % / drawdown -54,6 % ; momentum absolu seul : 12,3 % / drawdown -29,6 %. Résultats « hypothetical… do NOT represent returns that any investor actually attained ». — [optimalmomentum.com](https://www.optimalmomentum.com/extended-backtest-of-global-equities-momentum/)
- **Réplication ReSolve (Butler)** : GEM 1950–2018, réplication avec proxies, résultats « tracked the author's results very closely » ; échantillon original 1974-2011 ; deux périodes hors échantillon 1950-1973 et 2012-2018. Toutes performances « gross of taxes and transaction costs ». Rendement composé de la spécification originale : 14,9 %, Sharpe 0,90, drawdown moyen max 16,5 %, vs médiane des 1 226 variantes : 14,1 % / 0,83 / 17,4 %. — [Advisor Perspectives, ReSolve 2019](https://www.advisorperspectives.com/articles/2019/05/06/global-equity-momentum-a-craftsmans-perspective)
- **Dualmomentumsystems.com (vendeur, 2026)** : GEM janvier 1980 – septembre 2026, net de frictions : CAGR 13,8 %, max drawdown -21,9 %, Ulcer Performance Index 1,40 ; « the years after the book were harder » : leadership des grandes capitalisations US, marchés baissiers courts, chaque sortie suivie d'un rebond coûte un aller-retour. — [dualmomentumsystems.com](https://dualmomentumsystems.com/strategies/global-equities-momentum) [source commerciale, [secondaire]]
- **Étude Medium (L. Leong, août 2026)** : exécution mécanique des règles GEM avec frais, première décennie hors échantillon : perd la course annuelle vs son benchmark et vs le comparateur d'Antonacci. Chiffres exacts derrière paywall. — [Medium](https://medium.com/gradient-growth/global-equities-momentum-beat-the-market-for-16-years-then-i-ran-the-honest-out-of-sample-test-7fb458fe9b3b) [non reproductible en détail ici]
- **TuringTrader (portefeuille dual momentum multi-actifs, ETF, 5 classes à 20 %)** : CAGR 6,08 % vs 7,99 % pour un 60/40, volatilité 7,53 % vs 9,88 %, max drawdown 20,00 % vs 35,69 %, Sharpe 0,57 vs 0,63 (période non précisée dans l'extrait). — [TuringTrader](https://www.turingtrader.com/portfolios/antonacci-dual-momentum/) [[secondaire]]
- **Faber GTAA 5, 1973-2012, sans frais ni taxes** : rendement 10,48 % vs 9,92 % buy & hold, volatilité 6,99 % vs 10,28 %, Sharpe 0,73 vs 0,44, MaxDD -9,54 % vs -46,00 % ; avec 13 classes : 12,04 % / Sharpe 0,94 / MaxDD -10,74 %. — [Faber (PDF)](https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf) [extraction automatique]
- **Faber, versions post-publication** : 1972-2005 : 11,51 % / vol 8,88 % / Sharpe 0,60 / MaxDD -19,62 % (échantillon du « revisited ») ; sur 2006-2016 une des lignes du tableau reporte 3,51 % / Sharpe 0,19 / MaxDD -46,00 % (ligne buy & hold sur certains actifs ; lecture du tableau incertaine). — [Faber 2016](https://allocatortraining.com/wp-content/uploads/2023/06/A-Quantitative-Approach-to-Tactical-Asset-Allocation.pdf) [lecture partielle, [secondaire]]
- **Concretum, mise à jour 2025 de la stratégie de Faber (200 jours SMA, 20 % par actif)** : période in-sample 1972-2005 : Sharpe 0,81, CAGR 11,7 %, MaxDD 9,5 % (mensuel) ; hors échantillon sur ~20 ans : Sharpe 0,68, CAGR 6,05 %, MaxDD 11,7 % ; écart de CAGR d'environ 220 points de base entre le meilleur et le pire jour de rebalancement. — [Concretum Substack](https://concretumgroup.substack.com/p/global-tactical-asset-allocation) [[secondaire]]
- **AMP 2013, momentum 12-1 par classe d'actifs (Table I, rendement moyen annualisé / Sharpe du portefeuille P3-P1 ; sample jusqu'à juillet 2011)** : actions US 5,4 % / 0,33 ; UK 6,0 % / 0,38 ; Europe 8,1 % / 0,55 ; Japon 0,6 % / 0,04 ; indices actions pays 7,4 % / 0,63 ; devises 3,0 % / 0,17 ; obligations 0,8 % / 0,20 ; matières premières 4,4 % / 0,62 ; combinaison 50/50 value + momentum toutes classes : Sharpe 1,45. — [AMP (PDF)](https://w4.stern.nyu.edu/facdir/lpederse/papers/ValMomEverywhere.pdf) [extraction automatique ; chiffres à re-vérifier dans le tableau original]
- **Momentum crashes, Daniel & Moskowitz (2016), JFE 122(2), 221-247** : échantillon 1927-2010 ; deux crashes : juin 1932 – décembre 1939 et mars 2009 – mars 2013 ; pires mois du facteur gagnant-moins-perdant : août 1932 (-74 % à -79 % selon version/pondération), juillet 1932 (-61 %), avril 2009 (-45 à -46 %), mars 2009 (-40 à -42 %) ; de mars à mai 2009 le décile perdant gagne 156-163 % ; les crashes surviennent après un marché baissier, en forte volatilité, au moment du rebond ; Sharpe WML 0,83 vs marché 0,52 (Table 1, 1947-2006). Mêmes patterns « option-like » dans devises, matières premières, indices actions pays. — [JFE, ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0304405X16301490), [version NYU Stern](https://www.stern.nyu.edu/sites/default/files/assets/documents/con_038332.pdf) [extraction automatique ; deux versions du papier divergent légèrement sur les chiffres]
- **Résultats récents du facteur actions** : 2024, le momentum est le facteur le mieux classé US / monde développé ex-US / émergents pour la quatrième fois en 20 ans ; en janvier 2025, un stratégiste de Jefferies recommande de « fade » le momentum ; MSCI : drawdown de 22,4 % du facteur pendant la crise 2008-2009. — [SSGA](https://ssga.com/us/en/individual/insights/what-drove-momentums-strong-2024-and-what-it-could-mean-for-2025), [Investing.com](https://investing.com/news/stock-market-news/time-to-fade-momentum-trade-jefferies-says-3802101), [MSCI](https://www.msci.com/research-and-insights/blog-post/is-momentum-crashing) [[secondaire]]

### Inferences
- Les chiffres « 15,8 % / -17,8 % » de GEM sont des moyennes de long terme sans frais ; la période 2010-2025 est dominée par un marché US haussier à corrections brèves, défavorable à un signal lent 12 mois.
- La différence entre les ~0,9 de Sharpe de GEM / ~0,7 de GTAA in-sample et le ~0,6-0,7 de Faber hors échantillon suggère une érosion d'un quart à un tiers (à confirmer, sources secondaires).
- Le momentum cross-sectionnel pur par classe d'actifs (hors combinaison avec la value) a des Sharpe faibles à modestes (0,2 à 0,6) ; le Sharpe >1 vient de la diversification sur plusieurs classes et marchés.

### Gaps
- Aucune série GEM / GTAA 2010-2025 net de frais, issue d'une source indépendante et vérifiable, n'a été trouvée (les chiffres de TuringTrader, Concretum et dualmomentumsystems.com sont commerciaux ou de blog, et leurs périodes/hypothèses ne sont pas harmonisées).
- Le détail chiffré de l'étude Medium d'août 2026 est derrière un paywall.
- Quantpedia (états « out-of-sample ») et Alpha Architect n'ont pas pu être consultés en profondeur (paywall / résumé court).

---

## 3. Réplications indépendantes, critiques (sur-ajustement, rebalance timing luck)

### Takeaway
Les critiques les plus solides portent sur la fragilité de spécification (lookback 9 vs 10 mois, jour du mois) : ReSolve ne rejette pas l'hypothèse que les 1 226 variantes de GEM aient la même espérance, et Newfound montre des écarts annuels de plusieurs centaines à milliers de points de base. La remédiation documentée est l'ensemble de spécifications et le tranching (rebalancer « un peu, souvent »).

### Cited Findings
- **ReSolve / Butler (2019), « Global Equity Momentum: A Craftsman's Perspective »** : 324 combinaisons (18 lookbacks de tendance × 18 lookbacks de momentum), 1 226 variantes au total ; la spécification originale est restée sous le 95e centile à tous les horizons ; elle ne bat les autres que 61 % du temps ; impossible de rejeter l'hypothèse que toutes les variantes ont les mêmes rendements composés et Sharpe attendus ; écart moyen de rendement cumulé sur 5 ans entre variantes « chanceuses » et « malchanceuses » : 64 points de pourcentage ; corrélation moyenne entre variantes 0,77 ; ensemble : drawdown moyen max 13,2 % vs 17,4 % pour la variante médiane, Sharpe 0,93 vs 0,83. — [Advisor Perspectives](https://www.advisorperspectives.com/articles/2019/05/06/global-equity-momentum-a-craftsmans-perspective)
- **Newfound Research (Hoffstein), « Fragility Case Study: Dual Momentum GEM » (2019)** : l'écart annuel entre implémentations peut atteindre « hundreds, if not thousands, of basis points » ; exemple : lookback 9 mois +43,1 % cumulé vs lookback 10 mois +146,1 % sur la période étudiée ; en 2010, +12,2 % (10 mois) vs -9,31 % (9 mois). — [Newfound](https://blog.thinknewfound.com/2019/01/fragility-case-study-dual-momentum-gem/)
- **Hoffstein, Faber, Braun, « Rebalance Timing Luck: The (Dumb) Luck of Smart Beta » (SSRN 3673910) ; « The Difference between Hired and Fired » (JII 10(1), 2020)** : la performance est très sensible au calendrier de rebalancement ; solution optimale : le tranching (par exemple 1/12 du portefeuille chaque mois), sans prendre en compte les coûts de transaction. — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3673910), [Newfound](https://blog.thinknewfound.com/2020/04/tranching-trend-and-mean-reversion/)
- **Concretum (2025), rebalance timing luck sur le GTAA de Faber** : ~220 pb de CAGR entre le meilleur et le pire jour de rebalancement ; le rebalancement hebdomadaire tranché réduit l'écart à moins de 130 pb (moins de 50 pb sans le lundi) ; réduction de turnover économisant ~35 pb de CAGR par an à 10 pb de coût par transaction. — [Concretum](https://concretumgroup.substack.com/p/global-tactical-asset-allocation) [[secondaire]]
- **Grzegorz Link (blog, backtest ETF)** : dual momentum CAGR 14,8 %, MaxDD -20,5 % avec IEF vs 11,2 % / -50,1 % en buy & hold ; CAGR varie de 12,0 % à 14,8 % selon le lookback (le 12 mois étant le meilleur : « a little over-tested »). — [grzegorz.link](https://grzegorz.link/momentum-enhanced) [[secondaire]], coûts de transaction négligés
- **Antonacci lui-même (2026)** : « GEM can be whipsawed in sideways markets and may re-enter equities late » ; réaction lente aux retournements brutaux (début 2020, -30 % en quelques semaines) ; ses modèles actuels passent aux données quotidiennes et combinent tendance et retour à la moyenne ; mise en garde que les LLM facilitent le sur-ajustement. — [Concretum](https://concretumgroup.substack.com/p/gary-antonacci-from-dual-momentum)

### Inferences
- Toute règle à un seul lookback (12 mois, 10 mois) est un point de la grille, pas un résultat structurel ; un « momentum 12-1 » ou « SMA 10 » sur 6-8 CFD doit être testé sur une grille 6/9/10/12 mois et plusieurs jours de rebalancement, en moyennant les spécifications (ensemble).
- Le sur-ajustement porte moins sur le principe (tendance de 12 mois bien documentée) que sur le choix précis des paramètres et de l'univers d'ETF.

### Gaps
- Je n'ai pas trouvé d'étude publiée chiffrant explicitement la sensibilité de GEM au jour du mois (les affirmations de dualmomentumsystems.com sont qualitatives).
- L'étude de Severian Asset Management (« Is Gary Antonacci's GEM robust? ») n'a pas pu être lue.

---

## 4. Transposabilité à 6-10 instruments CFD (or, SPX500, US100, GER40, FR40, EURUSD, USDJPY, pétrole)

### Takeaway
Le momentum relatif cross-sectionnel dépend de la largeur de l'univers ; avec 6-10 actifs très corrélés (4 indices actions), il n'existe pas, à ma connaissance, de résultat publié solide. Le momentum absolu / de tendance (time-series) se transpose mieux, mais avec un Sharpe attendu plus faible faute de diversification. Aucune des sources lues n'inclut les coûts réels des CFD.

### Cited Findings
- Le momentum cross-sectionnel est un portefeuille long-short classé sur un univers ; le momentum time-series est un signal par actif, net long ou short selon la tendance, et ne nécessite pas de classement entre actifs. — [Quantpedia (TSMOM)](https://quantpedia.com/strategies/time-series-momentum-effect/), [CXO Advisory](https://www.cxoadvisory.com/value-premium/when-carry-momentum-and-value-work) [[secondaire]]
- La recherche de Moskowitz, Ooi, Pedersen utilise 58 instruments ; Hurst, Ooi, Pedersen (« A Century of Evidence on Trend Following Investing ») 67 marchés (29 matières premières, 11 indices actions, 15 obligations, 12 paires de devises) de 1880 à 2016, Sharpe moyen net de 0,4. — [IDEAS](https://ideas.repec.org/a/eee/jfinec/v104y2012i2p228-250.html), [AQR](https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing?aqrPDF=1) [[secondaire] pour le résumé]
- AMP 2013 : pour les devises, seulement 10 monnaies, Sharpe momentum 0,17 ; pour les indices actions pays, 18 marchés, Sharpe 0,63 ; pour les matières premières 27 contrats, Sharpe 0,62. — [AMP (PDF)](https://w4.stern.nyu.edu/facdir/lpederse/papers/ValMomEverywhere.pdf) [extraction automatique]
- GEM lui-même est une stratégie à 3 actifs seulement (S&P 500, ACWI ex-US, obligations) avec T-bills comme référence : preuve qu'un petit panier fonctionne, mais la sélection est faite entre deux marchés actions et un refuge obligataire. — [optimalmomentum.com](https://www.optimalmomentum.com/extended-backtest-of-global-equities-momentum/)
- Faber : 5 classes d'actifs suffisent (Sharpe 0,73) ; passer à 13 classes améliore le Sharpe (0,94). — [Faber (PDF)](https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf) [extraction automatique]
- Faber, variante top 3 sur 13 actifs : Sharpe 0,92 vs 1,06 pour top 6 ; MaxDD -20,29 % vs -23,43 %. — [Faber (PDF)](https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf) [extraction automatique]

### Inferences
- Sur une liste de type « or, SPX500, US100, GER40, FR40, EURUSD, USDJPY, pétrole », les quatre indices actions sont fortement corrélés : le classement relatif entre eux est quasi du « beta US vs Europe » (comme la décision US/non-US de GEM) ; le vrai contenu de diversification vient d'or, devises et pétrole.
- La version la plus transposable est le time-series (prix > SMA 10 mois, ou rendement 12 mois > 0 par instrument, rebalancement mensuel, position égale ou à volatilité cible), éventuellement avec un filtre « top N » parmi 8 actifs ; elle est de type « tendance lente » et diffère donc fortement de toutes les stratégies écartées (intraday).
- Les fréquences en jeu (0,1 à 4 transactions par an et par actif) rendent les spreads CFD négligeables ; en revanche, les frais de financement overnight pour positions CFD tenues des mois (long ou short) ne sont documentés dans aucune des sources et pourraient changer le calcul net.
- Avec très peu de signaux par an (12 décisions mensuelles par instrument), la puissance statistique est faible : un backtest sur 10-20 ans donne peu de décisions indépendantes.

### Gaps
- Aucune étude publiée trouvée sur le momentum cross-sectionnel/dual avec précisément 6-10 CFD (indices + or + devises + pétrole).
- Aucune source sur les coûts de financement overnight XTB/CFD à intégrer.
- BTC et gaz naturel (NATGAS) : pas de source spécifique au momentum sur ces deux actifs dans cette recherche.

---

## 5. Fonctionne-t-il en marché baissier (long/short ou avec refuge) ?

### Takeaway
Le filtre absolu + refuge (obligations, cash) a historiquement réduit les drawdowns d'actions de manière nette, mais un crash rapide suivi d'un rebond (2020, 2009) punit les signaux lents ; la version long-short cross-sectionnelle souffre justement dans les rebonds de marchés baissiers (momentum crashes).

### Cited Findings
- **GEM** : pire drawdown -17,8 % (1950-2018) vs -51,0 % pour le S&P 500 ; le momentum relatif seul subit presque les mêmes pertes en marché baissier (-54,6 %) ; le gain vient de l'absolu. — [optimalmomentum.com](https://www.optimalmomentum.com/extended-backtest-of-global-equities-momentum/)
- **Daniel & Moskowitz** : les crashes du facteur long-short se produisent après des marchés baissiers, en forte volatilité, lors des rebonds (1932, 2009) ; le décile perdant se comporte comme une option d'achat. — [JFE](https://www.sciencedirect.com/science/article/pii/S0304405X16301490), [version NYU](https://www.stern.nyu.edu/sites/default/files/assets/documents/con_038332.pdf)
- **Hurst, Ooi, Pedersen** : la tendance time-series a été positive dans 8 des 10 pires drawdowns d'un 60/40 ; les marchés baissiers sont en général progressifs, ce qui laisse le temps de se positionner à la baisse ; 20 % d'allocation à la tendance font passer le Sharpe de 0,39 à 0,55 et le drawdown max de -62,3 % à -50,2 %. — [Alpha Architect](https://alphaarchitect.com/trend-following-is-everywhere/), [CXO](https://www.cxoadvisory.com/momentum-investing/trend-following-with-intrinsic-momentum-over-the-very-long-run) [[secondaire]]
- **Antonacci (2026)** : ses modèles publics ne prennent pas de positions short ; ils utilisent le refuge ; un modèle utilise parfois un ETF inverse. — [Concretum](https://concretumgroup.substack.com/p/gary-antonacci-from-dual-momentum)
- **Limites (Antonacci, dualmomentumsystems)** : retournements en V (début 2020) ; whipsaws dans les marchés latéraux. — [Concretum](https://concretumgroup.substack.com/p/gary-antonacci-from-dual-momentum), [dualmomentumsystems.com](https://dualmomentumsystems.com/strategies/global-equities-momentum)

### Inferences
- Pour un CFD, le « refuge » naturel est le cash (pas d'obligation dans la liste) : on se rapproche du GTAA de Faber (cash quand prix < SMA), documenté avec MaxDD -9,5 % à -10,7 % in-sample, mais -11,7 % hors échantillon récent selon la mise à jour Concretum.
- Une version CFD long/short time-series (short quand tendance négative) est possible techniquement mais n'est pas dans les règles de Antonacci ni Faber ; le short ajoute le risque de crash de rebond documenté par Daniel & Moskowitz et le coût de financement.

### Gaps
- Aucune source sur la performance de dual momentum à 6-10 CFD en 2022 (marché haussier-baissier simultané sur actions et obligations) ; non trouvé.
- Données 2020 (crash COVID) de GEM, chiffrées par une source indépendante : non trouvées.
