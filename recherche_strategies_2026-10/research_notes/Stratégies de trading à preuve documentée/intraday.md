# Stratégies intraday à preuve documentée : ORB, momentum intraday, effets de session (état au 14/10/2026)

Méthode : textes lus directement (extraction `pdftotext`) pour Zarattini-Aziz 2023 (QQQ), Zarattini-Barbon-Aziz 2024 (Stocks in Play) et « Beat the Market » (SPY, version 2025 avec FAQ), et Baltussen-Da-Lammers-Martens (JFE 2021). Les autres sources (Gao et al. 2018, Crabel, réplications) ne sont connues que par résumés/pages secondaires : signalé à chaque fois. Les tableaux extraits des PDF sont parfois mal alignés ; les chiffres retenus sont ceux que le texte confirme.

## 1. Règles exactes, reproductibles, et paramètres standards

### Takeaway
Trois familles ont des règles entièrement spécifiées dans des papiers publics : (a) ORB 5 min sur QQQ/actions (entrée à la cassure de la 1re bougie, stop à l'autre extrémité ou 10 % ATR, sortie à la clôture), (b) « Noise Area » sur SPY (bandes dépendant de l'heure, trade à HH:00/HH:30, stop VWAP, taille à volatilité cible 2 %), (c) momentum « dernière demi-heure » (signe du rendement du reste de la journée → position sur les 30 dernières minutes). Les « effets de session » (Londres, Francfort, fixing or, gaps) n'ont pas de règle standardisée avec preuve académique trouvée.

### Cited Findings

**A. ORB 5 min sur QQQ — Zarattini & Aziz (SSRN 4416622, avril 2023)**
- Entrée : direction de la 1re bougie de 5 min (à la hausse → long, à la baisse → short ; pas de position si ouverture ≈ clôture de la bougie), ordre exécuté à l'ouverture de la 2e bougie de 5 min ; stop = bas de la 1re bougie (long) / haut (short) ; cible = 10 × le risque R ; sinon sortie à la clôture 16:00 ET — [Concretum PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Can-Day-Trading-Really-Be-Profitable.pdf) (texte lu) ; [CXO Advisory](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy)
- Taille : risque 1 % du capital par trade ; formule `Shares = int(min(A×0,01/$R ; 4×A/P))` avec levier max 4x ; capital initial 25 000 $ ; commission 0,0005 $/action ; « We assumed no slippage in fills » ; données agrégées Interactive Brokers, backtest MATLAB ; période 1er janv. 2016 – 17 févr. 2023 — [Concretum PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Can-Day-Trading-Really-Be-Profitable.pdf)
- Variante TQQQ : stop = 5 % de l'ATR 14 jours, pas de cible, sortie EoD — [CXO Advisory](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy)
- Les auteurs disent avoir « deliberately kept the model very simple and did not try to optimize » — [Concretum PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Can-Day-Trading-Really-Be-Profitable.pdf)

**B. ORB sur « Stocks in Play » — Zarattini, Barbon, Aziz (SFI RP 24-98 ; SSRN 4729284, 2024)**
- Univers : prix d'ouverture > 5 $, volume moyen 14 j ≥ 1 000 000 actions, ATR 14 j > 0,50 $ — [SSRN/SFI PDF](https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content) (texte lu)
- Entrée : ordre stop (buy stop au plus haut de la 1re bougie 5 min si haussière, sell stop au plus bas si baissière ; doji = pas d'ordre). Stop loss à 10 % de l'ATR 14 j depuis le prix d'entrée ; pas de cible, sortie à 16:00 ET ; risque 1 % par trade, levier max 4x ; commission 0,0035 $/action (tarif IB Pro Tiered) ; 25 000 $ ; 2016–2023 — même source
- Filtre « Stocks in Play » : volume relatif ≥ 100 % dans l'opening range (volume des n premières minutes vs moyenne des 14 jours précédents) ET top 20 par volume relatif — même source
- Comparaison des opening ranges 5/15/30/60 min ; le 5 min domine ; les auteurs écrivent que la raison est « unclear » — même source

**C. « Noise Area » intraday momentum sur SPY — Zarattini, Barbon, Aziz, « Beat the Market » (SFI WP 24-97, nov. 2024 ; révisions 2025)**
- Bande : pour chaque heure HH:MM, moyenne sur 14 jours du mouvement absolu |Close(HH:MM)/Open − 1| depuis l'ouverture 9:30 → σ(t, HH:MM). Upper = max(Open_t, Close_{t−1}) × (1+σ) ; Lower = min(Open_t, Close_{t−1}) × (1−σ) (ajustement du gap overnight). Multiplicateur de volatilité = 1 dans l'article — [SFI PDF](https://www.alexandria.unisg.ch/entities/publication/71ef0a23-34e3-4b37-a8d7-d98285579662) (texte lu via le PDF SFI)
- Entrée : long si le prix sort au-dessus de la bande haute, short sous la bande basse ; décisions seulement à HH:00 et HH:30 (ex. exécution à 10:30 même si la sortie de bande a eu lieu avant) ; sortie à la clôture ou au croisement de la bande opposée (retournement) — même source
- Stop : bande opposée (version de base), puis trailing stop Long = max(bande haute, VWAP), Short = min(bande basse, VWAP) évalué par demi-heure — même source ; le VWAP est calculé seulement sur les heures de marché — même source
- Taille : `Shares = AUM_{t−1} × min(4 ; 2 % / σ_SPY,t) / Open_t`, σ = volatilité des rendements journaliers sur 14 j ; levier plafonné à 4x — même source
- Coûts modélisés : commission 0,0035 $/action + slippage 0,001 $/action ; capital initial 100 000 $ — même source
- Paramètres « standard » : lookback 14 j, multiplicateur 1. Les auteurs affirment que les optimums seraient 90 j (Sharpe 1,35 → 1,50) et multiplicateur 1,5 (1,35 → 1,55) : ils ne sont donc pas choisis par optimisation — FAQ Q14 du même PDF

**D. Momentum « première demi-heure prédit la dernière » — Gao, Han, Li, Zhou (JFE 129, 2018, pp. 394-414)**
- Prédicteur : rendement du close de la veille jusqu'à la 1re demi-heure (r_ONFH) ; cible : rendement de la dernière demi-heure ; SPY 1993–2013, plus dix autres ETF liquides — [WUSTL profile](https://profiles.wustl.edu/en/publications/market-intraday-momentum/) ; [Alpha Architect](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/) (sources secondaires ; texte original non lu)
- Version « futures » étendue : Baltussen, Da, Lammers, Martens (JFE 142, 2021) : r_ROD = rendement de la veille-close jusqu'à 30 min avant la clôture ; position long si r_ROD > 0, short sinon, tenue sur les 30 dernières minutes ; 60+ futures (17 indices actions dont 8 européens, DAX, Euro Stoxx 50, FTSE…), 1974–2020, données tick Tick Data LLC — [papier JFE (PDF)](https://www3.nd.edu/~zda/intramom.pdf) (texte lu)

**E. Session de Londres / Francfort, gaps, heure du jour**
- London breakout testé par Backtrex (règles publiées par QuantifiedStrategies) : range asiatique 00:00-06:00 UTC, entrée sur clôture H1 au-dessus/au-dessous du range entre 07:00 et 10:00 UTC, stop 35 pips, TP 70 pips ; sizing 100 % du capital — [Backtrex](https://backtrex.com/en/backtests/london-breakout-eur-usd)
- ORB DAX « maison » (forum ProRealCode) : range 09:00-09:30 en M15, stop de l'autre côté, TP = stop ; aucune règle standard académique — [ProRealCode](https://prorealcode.com/prorealtime-trading-strategies/simple-dax-breakout-trading-strategy-code)
- Gap fade : aucune règle standard sourcée trouvée (voir Gaps)

### Inferences
- Les seules règles « standard » avec paramètres figés et code public sont A, B, C, D ; E n'est que de la littérature de forum/vendeurs.
- C est la plus adaptable aux indices CFD : elle ne dépend ni d'un filtre de volume relatif d'action individuelle ni d'une 1re bougie unique, seulement d'Open, Close veille, VWAP et σ.
- La règle D est un signal à n'exécuter qu'une demi-heure par jour : peu de trades mais exposition très brève (voir coûts, §2).

### Gaps
- Crabel (« Day Trading with Short-Term Price Patterns and Opening Range Breakout », 1990) : règles originales (stretch, NR4/NR7, etc.) non retrouvées en source primaire ; seulement cité comme « volatility breakout » dans la bibliographie de « Beat the Market ». Aucun test indépendant de Crabel sur DAX/or trouvé.
- Texte intégral de Gao et al. 2018 non lu (seul le résumé et des synthèses) : spécification exacte, R² (secondaire : jusqu'à 1,8 %, selon [CXO](https://www.cxoadvisory.com/?p=25481)) non vérifiés dans la source.
- Article « Stocks in Play » : le titre exact dans la littérature est « A Profitable Day Trading Strategy For The U.S. Equity Market » ; aucun papier distinct intitulé « Stocks in Play » n'a été trouvé (recherche : seulement un webinaire d'Aziz).

---

## 2. Résultats publiés, frais/glissement inclus, robustesse retail et post-2020

### Takeaway
Les chiffres de tête sont brillants mais dépendent de coûts en dollars par action quasi nuls (US ETF/actions). Le filtre « Stocks in Play » est ce qui fait passer l'ORB de 3,2 %/an (Sharpe 0,48) à 41,6 %/an (Sharpe 2,81) ; la variante SPY passe de Sharpe 0,61 à 1,33 grâce au VWAP et au dimensionnement à volatilité cible, ajustements introduits après observation de l'échantillon. Aucun de ces chiffres n'est un résultat CFD retail ni une vraie hors-échantillon indépendante.

### Cited Findings

**ORB 5 min QQQ (2016 – fév. 2023, brut de spread/slippage, commission 0,0005 $)**
- 1 795 trades, 51 % longs / 49 % shorts, win rate 24 %, PnL moyen 0,13 R/trade ; ORB QQQ : +676 % total, 33 %/an, vol 29 %, Sharpe 1,13 (1,12 dans le texte), MDD 22 % ; buy & hold QQQ : 169 %, Sharpe 0,73, MDD 36 % ; alpha annualisé 33 % (p = 0,0025), bêta non significatif — [Concretum PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Can-Day-Trading-Really-Be-Profitable.pdf)
- ORB TQQQ : +1 484 %, 48 %/an, vol 39 %, Sharpe 1,19, MDD 28 % ; alpha 48 % ; variante stop 5 % ATR : alpha 93 % et 25 000 $ → 6,4 M$, que les auteurs qualifient eux-mêmes de potentiellement irréaliste car « no slippage » — même source
- Le chiffre « 33 % d'alpha / +1 484 % » repris par la presse mélange donc QQQ (alpha 33 %) et TQQQ (rendement 1 484 %) — même source

**ORB sur toutes les actions US (sans filtre) vs Stocks in Play (2016–2023, commission 0,0035 $/action)**
- ORB de base (7 000+ actions) : +30 % total, 3,2 %/an, vol 6,6 %, Sharpe 0,48 vs S&P 500 0,78, MDD 13 %, alpha 3,26 %/an — [SSRN/SFI PDF](https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- ORB + volume relatif ≥ 100 % + top 20 : +1 637 % total (25 000 $ → ≈ 435 000 $), 41,6 %/an, vol 14,8 %, Sharpe 2,81, MDD 12 %, pire jour −1,61 %, alpha 35,8 %, bêta ≈ 0 ; S&P 500 : +198 %, 14,2 %/an, Sharpe 0,78, MDD 34 % — même source
- Autres opening ranges (lecture approximative du tableau 3, alignement PDF dégradé) : 15 min Sharpe ≈ 1,43 ; 30 min ≈ 0,21 ; 60 min ≈ 0,40 ; combo ≈ 1,99 ; le 5 min est présenté comme nettement supérieur — même source
- Pas de slippage ni de spread explicite dans les chiffres de tête ; coûts = commissions seulement — même source (texte lu : seule la commission est mentionnée dans les hypothèses du backtest)
- Résultat par action : les 25 pires titres du tableau 5 perdent de −80 à −266 R cumulés ; la performance repose sur la sélection quotidienne de titres (TSLA, NVDA, AMD cités en tête) — même source

**Noise Area SPY (mai 2007 – déc. 2024 ; commission 0,0035 $ + slippage 0,001 $/action)**
- Version de base (stop bande opposée) : +178 %, 6,2 %/an, vol 10,9 %, Sharpe 0,61 vs buy & hold SPY 0,45 (+227 %) ; pire rendement journalier −10,33 % et asymétrie négative — [SFI PDF](https://www.alexandria.unisg.ch/entities/publication/71ef0a23-34e3-4b37-a8d7-d98285579662)
- Stop bande courante + VWAP : 9,7 %/an, vol 7,7 %, Sharpe ≈ 1,24 (le texte dit « le Sharpe double »), MDD 12 % ; + taille dynamique (vol cible 2 %, levier ≤ 4) : +1 985 %, 19,6 %/an, vol 14,3 %, Sharpe 1,33, MDD 25 %, hit ratio quotidien ≈ 43 %, meilleur trade +9,1 %, pire −2,9 % — même source
- Slippage mesuré : expérience réelle IBKR en avril 2024, > 1 000 ordres au marché, > 50 M$ de notionnel, glissement moyen ≈ 0,001 $/action, médiane 0,0005 $ ; avec le modèle d'impact I-Star (Kissell-Malamut, paramètres grandes capitalisations) le Sharpe passe de 1,33 à 1,17 — même source (FAQ Q15)
- ≈ 7 964 trades (version VWAP + bande courante) sur la période ; stop VWAP seul : Sharpe 1,17 vs 1,35 — même source (FAQ Q22)
- Sharpe conditionnel à la VIX : ≈ 1,5 si VIX > 6 ; ≈ 3,5 si VIX > 40 — même source
- Observation Quantified Strategies : la page ne mentionne pas de slippage (« No slippage was modeled ») — probablement une version antérieure de l'article ; elle indique aussi n'avoir pas fait son propre backtest — [Quantified Strategies](https://quantifiedstrategies.substack.com/p/systematic-intraday-trend-following) ; contredit par la version PDF 2025 qui modélise 0,001 $/action

**Momentum « dernière demi-heure » (Baltussen et al. 2021 ; Gao et al. 2018)**
- Sharpe annualisé de la stratégie « r_ROD → dernière demi-heure » : 0,87 à 1,73 par classe d'actifs selon l'abstract ; futures sur indices actions : r_ROD ≈ 1,73 (7 % de rendement/an, vol 4 %), r_ONFH ≈ 1,07 ; échantillon 1974–2020 — [JFE PDF](https://www3.nd.edu/~zda/intramom.pdf)
- Dans l'échantillon étendu de futures sur indices, r_ONFH (le prédicteur de Gao et al.) a un R² hors-échantillon négatif (−1,71 %) ; r_ROD obtient R²_OOS 2,88 % (t = 7,29) ; pour 14 contrats actions sur 17, r_ROD a un R²_OOS positif et significatif — même source
- Coûts : le tableau 6 ne les inclut pas ; les auteurs notent que la stratégie « might not be exploitable to many investors after accounting for transaction costs » et qu'avec un coût d'un tick sur futures S&P 500 le Sharpe net reste positif — même source
- L'effet est présent dans les sous-périodes 1974-1999 et 2000-2020 (texte de la section 3.4) et « reverts over the next days » — même source
- Gao et al. : effet plus fort les jours volatils, à fort volume, en récession et les jours de publications macro majeures — [WUSTL](https://profiles.wustl.edu/en/publications/market-intraday-momentum/)

**Robustesse post-2020 et retail**
- Réplication indépendante (blog MQL5, 25/09/2026, données minute CFD, 2015 – juin 2026) : voir §3. Résultat : brut reproduit, net ≈ 0, hors-échantillon 2021-2026 « +0,06 R sur NQ au mieux » — [MQL5](https://www.mql5.com/en/blogs/post/776235)
- Les périodes des papiers s'arrêtent en fév. 2023 (QQQ), déc. 2023 (Stocks in Play) et début/fin 2024 (SPY) ; les auteurs affirment une performance hors-échantillon « depuis 2024 » non vérifiée de façon indépendante — [Quantified Strategies](https://quantifiedstrategies.substack.com/p/systematic-intraday-trend-following)

### Inferences
- Illustration (ordre de grandeur, à vérifier avec les spreads réels XTB, que je n'ai pas sourcés) : 0,0045 $/action sur SPY ≈ 400 $ est de l'ordre du dixième de point de base par côté ; un spread CFD de quelques points de base aller-retour est de un à deux ordres de grandeur plus élevé. Les chiffres de « Beat the Market » ne se transposent donc pas tels quels à un CFD retail.
- Le saut de 0,48 à 2,81 de Sharpe montre que l'ORB « brut » sur toutes les actions n'a pas d'edge net fiable ; l'edge est censé venir de la sélection (volume relatif/news), mécanisme absent sur un indice unique ou l'or.
- Le choix du stop VWAP et du sizing à volatilité cible a été fait dans l'échantillon complet (« base model » analysé sur un cas du 20/01/2022 puis amélioré) : risque de sur-ajustement de forme, même avec peu de paramètres.
- Pour l'ORB QQQ, la différence « règle − direction aléatoire » est ≈ +0,1 R (voir §3) : l'edge brut est du même ordre que le coût d'exécution d'un CFD.

### Gaps
- Aucun chiffre PF (profit factor) publié par les auteurs : non retrouvé dans les trois papiers lus.
- Aucune étude à partir de coûts CFD/spread retail sur ces règles (hors le blog MQL5).
- Pas de test indépendant de la Noise Area sur DAX, FR40 ou or retrouvé.

---

## 3. Réplications indépendantes, critiques, applicabilité GER40 / FR40 / or

### Takeaway
La seule réplication indépendante de l'ORB QQQ trouvée (blog, non évaluée par des pairs) reproduit le brut (+0,13 R, 23 % de win rate) mais obtient un net ≈ 0 à négatif sur NQ, SPX, Dow, DAX et FTSE une fois spread/slippage inclus. Pour la Noise Area, seules les critiques de la FAQ des auteurs et un script TradingView informel existent. Pour le momentum de fin de séance, la littérature (JFE, 60+ futures dont DAX/Euro Stoxx) est solide en brut mais sans coûts.

### Cited Findings
- Réplication ORB 5 min, NQ/SPX/Dow/DAX/FTSE (CFD, cash session, janv. 2015 – juin 2026, 2 899 à 2 937 séances, données minute, règle du papier inchangée, coûts par trade : NQ 2,5 pts, SPX 0,8, Dow 4, DAX 2,5, FTSE 1,5, aller-retour, rapportés au risque initial ; trades dont le risque < 2× le coût exclus) — [MQL5, T. Krueger](https://www.mql5.com/en/blogs/post/776235)
- Résultats bruts : NQ +0,131 R (t +2,9, hit 23,2 %), SPX +0,119 R (t +2,4), DAX +0,116 R (t +2,4, hit 20,8 %, 10R atteint 3,7 % du temps), Dow +0,048, FTSE +0,050 — même source
- Résultats nets : NQ +0,002 R (t 0,0), SPX −0,081 R (t −1,6), Dow −0,081 (t −1,9), **DAX −0,038 R (t −0,8, n = 2 835)**, FTSE −0,079 (t −1,8) ; « rule minus random direction » net : NQ +0,124, DAX +0,128 (t +2,5), FTSE +0,106 — même source
- Époques : 2015-2017 négatif sur tous les marchés (significatif sur NQ et SPX) ; aucun marché/époque significativement positif net ; hors-échantillon 2021-2026 ≈ +0,06 R sur NQ au mieux — même source
- Biais notés par l'auteur : simulation de brackets en M1 = biais de discrétisation ; futures avec commission seule non testés ; données CFD — même source
- Critique sur le papier QQQ : commission mais « no spread and no slippage », pas de période hors-échantillon — même source ; les auteurs de l'article reconnaissent « no slippage » dans leur propre tableau 1 — [Concretum PDF](https://concretumgroup.com/wp-content/uploads/2026/02/Can-Day-Trading-Really-Be-Profitable.pdf)
- Noise Area : replication TradingView informelle sur barres M30 : « good, but not as good », rendement plus faible, Sharpe « très bas », appels de marge si le contrôle de marge est activé — [TradingView script](https://in.tradingview.com/script/gJeM3LZ5-Out-of-the-Noise-Intraday-Strategy-with-VWAP-YuL) (selon la synthèse de recherche ; page non ouverte directement)
- Biais/auto-critique côté auteurs : la FAQ répond à « the strategy seems over-optimized » et « the slippage model seems inaccurate » ; ils ne fournissent pas de test hors-échantillon indépendant — [SFI PDF](https://www.alexandria.unisg.ch/entities/publication/71ef0a23-34e3-4b37-a8d7-d98285579662)
- Les auteurs sont des praticiens (Concretum Research, Bear Bull Traders pour Aziz) qui proposent des « Live Experiment », newsletters et formation ; la page Concretum est promotionnelle — [Concretum](https://concretumgroup.com/can-day-trading-really-be-profitable/) ; conflit d'intérêts potentiel à pondérer
- DAX ORB 09:00-09:30 M15 (forum) : rapporte +51,8 %/an avec drawdown 6 548 € sur 10 000 € ; un commentateur note que ce n'est rentable que depuis 2014 et rappelle d'inclure le spread — [ProRealCode](https://prorealcode.com/prorealtime-trading-strategies/simple-dax-breakout-trading-strategy-code) (anecdote non vérifiée)
- Momentum de fin de séance, indices européens : l'échantillon de Baltussen et al. inclut DAX (1997-2020), Euro Stoxx 50 (1998-2020), FTSE 100, FTSE MIB ; rapport pooled par région USA/Europe/Asie-Pacifique en annexe B ; effet significatif pour 14 contrats actions sur 17 (R²_OOS) — [JFE PDF](https://www3.nd.edu/~zda/intramom.pdf)
- Or : le papier inclut 5 futures sur métaux dans les 21 futures de matières premières ; l'effet y est « un peu plus faible » que pour les indices (R²_OOS positif et significatif pour 40-50 % des contrats commodités/devises) — même source ; aucun résultat or isolé extrait
- Mécanisme (couverture gamma des teneurs de marché d'options et ETF à effet de levier) → l'effet est lié à des produits très liquides ; il « reverts » dans les jours suivants — même source ; [Alpha Architect](https://alphaarchitect.com/hot-topic-does-gamma-hedging-actually-affect-stock-prices/)
- Limite des tests post-publication : on n'a trouvé ni étude mesurant un affaiblissement après 2013 ni étude montrant que l'effet persiste en 2021-2026 sur SPY ; une recherche de synthèse conclut que « weaker after 2013 » reste une hypothèse non testée ; indication d'un effet plus faible en période COVID sur des marchés Asie-Pacifique — résultat de recherche web (Monash, étude APAC), non lu

### Inferences
- La preuve la plus propre pour GER40 est le momentum fin de séance (futures, JFE) : brut, sans coûts, 30 min de tenue ; pas pour l'ORB 5 min (net ≈ −0,04 R en CFD DAX).
- Un edge brut ≈ +0,1 R/trade contre un coût de 2,5 pts sur un stop de 25 pts (cas DAX/NQ du blog) laisse peu de marge ; plus le stop est large relatif au spread (ex. ORB sur range 30-60 min), plus le ratio coût/risque s'améliore, mais les auteurs trouvent que 30/60 min sont moins bons sur actions US.
- L'or n'est pas couvert par les papiers ORB/Noise Area lus ; toute application est une extrapolation.

### Gaps
- Pas de test indépendant publié de la Noise Area sur DAX/CAC/or.
- Spreads XTB réels (GER40, FR40, XAUUSD, US500) non sourcés ; indispensables pour trancher.
- Pas de résultats hors-échantillon indépendants 2024-2026 de « Beat the Market ».

---

## 4. Ce qui échoue, et ce qui distingue les stratégies à preuve

### Takeaway
Les stratégies intraday vendues (ICT/SMC, range breakouts « maison », London breakout) n'ont aucune preuve primaire retrouvée ; les tests quantifiés trouvés sont négatifs. Celles qui ont des preuves partagent : rationnel économique identifiable, échantillon long multi-actifs, règles figées, coûts explicites, et une condition d'activation (volume/volatilité/imbalance).

### Cited Findings
- London breakout EUR/USD H1 (oct. 2016 – oct. 2026, 1 230 trades, commission 0,02 %/côté, slippage non mentionné) : −28 %, CAGR −3,2 %, MDD −31,4 %, win rate 36,26 %, PF 0,87 ; seules 2018, 2021, 2023 positives ; variante GBP/USD M15 (stop 20 pips/TP 40 pips, 07:00-11:00 UTC) −60 % — [Backtrex](https://backtrex.com/en/backtests/london-breakout-eur-usd) (vendeur d'outils, source de données non nommée ; une source unique)
- ORB brut sur toutes les actions US : 3,2 %/an vs S&P 14,2 %/an, après commissions — [SSRN/SFI PDF](https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- ORB sur indices CFD : net ≈ 0 à négatif (§3) — [MQL5](https://www.mql5.com/en/blogs/post/776235)
- Baltussen et al. : le prédicteur r_ONFH de Gao et al. a un R²_OOS négatif sur le panel étendu d'index futures — le résultat académique le plus cité est donc moins robuste que sa version r_ROD — [JFE PDF](https://www3.nd.edu/~zda/intramom.pdf)
- Lou, Polk, Skouras (JFE 134, 2019) : décomposition overnight vs intraday des anomalies sur actions individuelles ; profits de signes opposés (tug of war) ; ne teste pas le gap fade sur indices — [LSE](https://researchonline.lse.ac.uk/id/eprint/119010) ; Alpha Architect rappelle une critique (Cooper, Cliff, Gulen) et note ne pas avoir trouvé d'évidence en test maison — [Alpha Architect](https://alphaarchitect.com/2015/02/overnight-momentum-vs-intraday-momentum/)
- Gap fade futures : aucune preuve rigoureuse retrouvée ; contenu NexusFi/TradingView non vérifié (probabilités de remplissage de gap sans méthode) — [NexusFi](https://nexusfi.com/a/strategies/gap-trading-futures)
- Or intraday : une thèse de master (CBS, non évaluée) décrit un motif « en chapeau » (or en hausse aux heures asiatiques, baisse ensuite) et des baisses autour du fixing Londres les années de manipulation alléguée — [CBS thesis](https://research.cbs.dk/en/studentProjects/gold-price-dynamics-around-the-clock/) ; un papier 2025 Global Finance Journal sur l'« effet de nuit » des futures chinois or/argent existe, mais résultats non lus — [IDEAS](https://ideas.repec.org/a/eee/glofin/v64y2025ics1044028325000110.html)
- Saisonnalité horaire FX : travail arXiv sur des motifs de volume/volatilité par heure (pas de rendement directionnel net de coûts) — [arXiv 1103.5664](https://arxiv.org/pdf/1103.5664)
- Motif en U de la volatilité au DAX, pics après les enchères : étude 2019 sur l'impact de prix — [WPF 1914 (SFI)](https://ux-tauri.unisg.ch/RePEc/usg/sfwpfi/WPF-1914.pdf) (via recherche ; non lu)

### Inferences
- Ce qui distingue les stratégies avec preuve (par comparaison des sources) : (1) lien causal plausible avec un flux (couverture gamma, réaction à une nouvelle, déséquilibre offre/demande) ; (2) testées sur des centaines d'actifs ou 40-45 ans (Baltussen) et pas sur un seul instrument ; (3) peu de paramètres, non optimisés ; (4) conditionnement sur volume ou volatilité ; (5) volatilité cible plutôt que taille fixe.
- ICT/SMC (sweeps, MSS, FVG) : aucune étude à preuve retrouvée dans cette recherche ; le résultat PF < 1 déjà observé par l'utilisateur est cohérent avec l'absence de preuve (je n'ai toutefois pas cherché spécifiquement « ICT » dans la littérature : à ne pas présenter comme une conclusion de recherche).
- Les ORB à stop serré sur un indice très liquide ont un hit rate ≈ 20-24 % : l'edge dépend des rares jours de tendance (10R atteint 2-4 % du temps), donc très sensible au coût et à la variance de l'échantillon.

### Gaps
- Aucune source académique sur ICT/SMC retrouvée (non cherchée de manière ciblée).
- Pas de test de rejet statistique de type « deflated Sharpe » ou correction pour tests multiples dans les trois papiers lus.
- Pas de données de longévité post-publication (decay) vérifiables.

---

## 5. Données nécessaires et disponibilité via TradingView

### Takeaway
Les papiers utilisent des barres 1 à 5 min (ORB 5 min, Noise Area minute/semi-heure, tick Tick Data). Sur TradingView Plus, un graphique ne dispose que de 10 000 barres intraday, et le Bar Replay remonte à 1 an en 1 min et 5 ans en 5 min : insuffisant pour des backtests multi-années en 1 min sans le Deep Backtesting.

### Cited Findings
- Limites de barres intraday par graphique : 5 000 (Free), 10 000 (Essential/Plus), 20 000 (Premium), 25 000 (Expert), 40 000 (Ultimate) ; limites « fixes pour le moment » — [TradingView support](https://www.tradingview.com/support/solutions/43000480679)
- Bar Replay (Plus) : 1 min = 1 an, 5 min = 5 ans ; Essential : 1 min = 6 mois, 5 min = 30 mois ; Premium+ : tout l'historique disponible — [TradingView support](https://www.tradingview.com/support/solutions/43000692816) (selon synthèse de recherche)
- Deep Backtesting : maximum 2 millions de barres par calcul — [TradingView support](https://tr.tradingview.com/support/solutions/43000668210/) (selon synthèse ; l'éligibilité par forfait n'a pas été confirmée)
- Données des papiers : IB (QQQ), Tick Data LLC 1-minute (futures), Matlab ; code Matlab/Python de la Noise Area lié dans une présentation Bear Bull Traders — [BearBull deck](https://bearbulltraders.com/wp-content/uploads/2024/08/Money_Show_Final.pdf)
- Indicateurs TradingView open source qui reproduisent les bandes : « Concretum Bands » et « Out of the Noise Intraday Strategy with VWAP » — [Concretum Bands](https://in.tradingview.com/script/CUpWCZhe-Concretum-Bands) ; [Out of the Noise](https://in.tradingview.com/script/gJeM3LZ5-Out-of-the-Noise-Intraday-Strategy-with-VWAP-YuL)
- Pour des tests de fiabilité, le blog MQL5 signale un biais de discrétisation du bracket en M1 et que les vraies exécutions intrabarre ne sont pas visibles — [MQL5](https://www.mql5.com/en/blogs/post/776235)

### Inferences
- Calcul simple (non sourcé ailleurs) : 10 000 barres M5 sur un marché 24 h ≈ 35 jours de calendrier ; M1 ≈ 7 jours ; sur une session cash DAX de 8,5 h (≈ 102 barres M5/jour), ≈ 98 jours. La Noise Area (lookback 14 j) est reproductible, mais un backtest 2007-2025 exige une source externe ou le Deep Backtesting.
- Les CFD XTB/TradingView ont leurs propres sessions et spreads ; la qualité des barres CFD (heures de roll, gaps) diffère des futures utilisés dans la littérature.

### Gaps
- Profondeur historique réelle des CFD GER40/FR40/XAUUSD sur TradingView en M1/M5 pour le forfait de l'utilisateur : non vérifiée dans cette recherche.
- Disponibilité du Deep Backtesting par forfait : non confirmée.
- Coût/spread XTB : non sourcé.
