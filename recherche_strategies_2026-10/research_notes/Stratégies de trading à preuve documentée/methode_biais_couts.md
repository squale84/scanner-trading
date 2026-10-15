# Cadre méthodologique pour tester honnêtement des stratégies de trading CFD retail : sur-ajustement, réplication, coûts réels, performance des particuliers, taille d'échantillon

Date de rédaction : 14 octobre 2026. Contexte : CFD retail via TradingView/XTB (XAUUSD, GER40, FR40, SPX500, US100, EURUSD, USDJPY, USOIL, NATGAS, BTC). Critère interne actuel : PF > 1,2 sur réglage ET sur échantillon de contrôle, ≥ 30 trades, plusieurs actifs.

Convention : « Cited Findings » = fait lu dans la source citée (lien). « Inferences » = calcul ou raisonnement propre (les simulations sont décrites pour être reproductibles ; script utilisé : binomiale exacte + Monte-Carlo numpy, graine fixe). Les points non vérifiés ou secondaires sont signalés.

---

## 1. Biais de backtest : data snooping, sur-ajustement, et méthodes pratiques simples

### Takeaway
Le nombre de variantes essayées compte autant que le résultat : avec peu de données, il suffit d'une poignée d'essais pour obtenir un « bon » Sharpe sans aucun edge réel. La littérature impose soit un seuil de t-stat nettement plus haut que 2 (≈ 3), soit une correction explicite du nombre d'essais (Sharpe déflaté, MinBTL, PBO, Reality Check), soit — le plus simple — un échantillon de contrôle réellement vierge et un journal du nombre d'essais.

### Cited Findings

**Seuil de t-stat (Harvey, Liu, Zhu)**
- Harvey, Liu & Zhu, « … and the Cross-Section of Expected Returns », Review of Financial Studies 29(1), 2016, pp. 5-68 (NBER WP 20592, oct. 2014) : un facteur nouvellement découvert « needs to clear a much higher hurdle, with a t-ratio greater than 3.0 » ; les auteurs concluent que « most claimed research findings in financial economics are likely false ». Cadre de tests multiples avec série temporelle de seuils depuis 1967. — [NBER w20592](https://www.nber.org/papers/w20592)
- Le papier s'appuie sur au moins 316 facteurs testés (chiffre repris par Harvey & Liu 2015). — [Harvey & Liu, « Backtesting », JPM 2015](https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF)
- Une correction de Bonferroni stricte donnerait un seuil encore plus haut (≈ 3,75 cité par un commentaire de 2015 ; source secondaire, non vérifiée dans le papier) — [Advisor Perspectives](https://www.advisorperspectives.com/commentaries/2015/09/17/empirical-finance-meeting-fiduciary-standards-through-skepticism-not-cynicism)

**Haircut sur le Sharpe (Harvey & Liu 2015)**
- La pratique courante est de décoter les Sharpe de backtest de 50 % ; les auteurs montrent que c'est « only a rule of thumb » et que la décote est non linéaire : presque toujours > 50 % quand le Sharpe annualisé est < 0,4 ; au plus 25 % quand le Sharpe est > 1,0 ; exemple : avec 50 essais, décote d'environ 50 % pour la stratégie E/P la moins profitable, 7,9 % pour BAB. — [Harvey & Liu, JPM 41(1), 2015](https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF)
- Ils notent qu'un t-ratio de 3,0, très significatif en test unique, peut ne plus l'être après prise en compte des tests multiples. — même source.

**Longueur minimale de backtest (Bailey, Borwein, López de Prado, Zhu)**
- « Pseudo-Mathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance », Notices of the AMS 61(5), 2014, pp. 458-471. Résultat : l'espérance du maximum de N Sharpe i.i.d. N(0,1) ≈ (1−γ)Z⁻¹[1−1/N] + γ Z⁻¹[1−1/(N·e)] (γ ≈ 0,5772) ; borne supérieure √(2 ln N). Avec seulement N = 10 configurations, on s'attend à trouver un Sharpe IS de 1,57 alors que tous les Sharpe OOS sont nuls. — [Bailey et al. 2014 (PDF)](https://carmamaths.org/jon/backtest.pdf)
- MinBTL (théorème 3.1) : MinBTL (années) < 2 ln(N) / E[max_N]² ; « if only 5 years of data are available, no more than 45 independent model configurations should be tried » pour éviter un Sharpe IS de 1 avec Sharpe OOS attendu de 0 ; « after trying only 7 independent strategy configurations, the expected maximum SR IS is 1 for a 2-year long backtest, while the expected SR OOS is 0 ». MinBTL est « a necessary, non-sufficient condition ». Un backtest qui ne rapporte pas N rend le risque de sur-ajustement impossible à évaluer. — même PDF.
- Les auteurs disent que le hold-out ne tient pas compte du nombre d'essais avant sélection et ne peut donc pas évaluer la représentativité d'un backtest. — même PDF.

**Deflated Sharpe Ratio, PBO, Reality Check**
- Bailey & López de Prado, « The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality », Journal of Portfolio Management 40(5), 2014, pp. 94-107 : DSR = Probabilistic Sharpe Ratio évalué contre un seuil égal au meilleur Sharpe attendu de N essais sans compétence (corrige la sélection, la non-normalité, la longueur d'échantillon). — [SSRN 2460551](https://papers.ssrn.com/abstract=2460551) (page non lisible directement : 403 ; contenu de la formule tiré de sources secondaires)
- Formule telle que présentée en secondaire (à vérifier dans l'article) : DSR = Φ[(SR̂ − SR*)·√(T−1) / √(1 − g₃·SR̂ + ((g₄−1)/4)·SR̂²)], avec SR* = √V·[(1−γ)Φ⁻¹(1−1/N) + γ·Φ⁻¹(1−1/(N·e))], SR en base par période (non annualisé). — [Wikipédia, Deflated Sharpe ratio](https://en.wikipedia.org/wiki/Deflated_Sharpe_ratio), [LuxAlgo](https://www.luxalgo.com/library/concept/deflated-sharpe-ratio/)
- MinTRL (Bailey & López de Prado, « The Sharpe Ratio Efficient Frontier », Journal of Risk 2012) : longueur minimale de track record pour rejeter SR ≤ SR* avec un niveau de confiance donné ; la skewness négative et le kurtosis élevé l'allongent. Formule citée de mémoire par un outil de recherche, non vérifiée : MinTRL = 1 + [1 − γ₃SR + ((γ₄−1)/4)SR²]·(z_α/(SR−SR*))². — [IDEAS/RePEc](https://ideas.repec.org/a/rsk/journ4/2223785.html), [portfoliooptimizer.io](https://portfoliooptimizer.io/blog/the-probabilistic-sharpe-ratio-bias-adjustment-confidence-intervals-hypothesis-testing-and-minimum-track-record-length/)
- Bailey, Borwein, López de Prado, Zhu, « The Probability of Backtest Overfitting », Journal of Computational Finance 20(4), 2017 : cadre non paramétrique, « combinatorially symmetric cross-validation » (CSCV), qui estime la probabilité que la meilleure configuration IS soit sous la médiane OOS ; les auteurs jugent le hold-out peu fiable en backtest financier. Package R `pbo` disponible. — [SSRN 2326253](https://papers.ssrn.com/abstract=2326253), [scholarworks.wmich.edu](https://scholarworks.wmich.edu/math_pubs/42), [CRAN pbo](https://ftp.fau.de/cran/web/packages/pbo/readme/README.html)
- White (2000), « A Reality Check for Data Snooping », Econometrica 68(5), 1097-1126 : test (bootstrap stationnaire) de l'hypothèse nulle « la meilleure règle trouvée lors de la recherche n'a aucune supériorité sur le benchmark » ; Hansen (2005, JBES 23(4), 365-380) propose le test SPA, plus puissant. — [Econometrica](https://www.econometricsociety.org/publications/econometrica/2000/09/01/reality-check-data-snooping), [arch docs](https://arch.readthedocs.io/en/latest/multiple-comparison/multiple-comparison-reference.html)
- Sullivan, Timmermann & White (1999, Journal of Finance 54, 1647-1691) appliquent le Reality Check à l'univers de règles techniques de Brock-Lakonishok-LeBaron sur 100 ans de Dow Jones ; ils trouvent un effet significatif IS après correction, mais des sources secondaires rapportent que la meilleure règle n'est plus significative sur 1987-1996 hors échantillon (chiffre « 7 846 règles » et « 8,63 %/an » : secondaires, non vérifiés dans le texte). — [LSE](https://researchonline.lse.ac.uk/id/eprint/119144), [synthèse secondaire](https://c.mql5.com/forextsd/forum/211/Re-Examining%20the%20Profitability%20of%20Technical%20Analysis%20with%20Whitets%20Reality%20Check%20and%20Hansen9s%20SPA%20Tes.pdf)

**Méthodes pratiques (découpage, walk-forward, etc.)**
- Harvey & Liu proposent de combiner un test OOS et un ajustement de tests multiples sur l'échantillon complet (« promising » mais laissé à de futures recherches). — [Harvey & Liu 2015](https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF)
- Bailey et al. citent la « model sequestration » (annoncer la stratégie publiquement puis publier les résultats OOS six mois après) comme variante extrême du hold-out. — [Bailey et al. 2014](https://carmamaths.org/jon/backtest.pdf)

### Inferences
- Tableau (calculé avec la formule de Bailey et al., N essais indépendants, aucun edge réel) : Sharpe annualisé maximal attendu = E[max_N]/√années.

| N essais | E[max_N] (σ) | Sharpe max attendu à 2 ans | à 5 ans | à 10 ans | années pour que E[max]=1 |
|---|---|---|---|---|---|
| 5 | 1,19 | 0,84 | 0,53 | 0,38 | 1,4 |
| 10 | 1,57 | 1,11 | 0,70 | 0,50 | 2,5 |
| 20 | 1,90 | 1,34 | 0,85 | 0,60 | 3,6 |
| 50 | 2,28 | 1,61 | 1,02 | 0,72 | 5,2 |
| 100 | 2,53 | 1,79 | 1,13 | 0,80 | 6,4 |
| 500 | 3,05 | 2,16 | 1,37 | 0,97 | 9,3 |

  (N = 10 → 1,57 et « ≈ 45 configurations pour 5 ans » retrouvent les chiffres du papier.) Un scanner qui teste 50 combinaisons (indicateur × paramètres × actif × timeframe) sur 2 ans de données doit s'attendre à un « meilleur » Sharpe de ≈ 1,6 par pur hasard.
- Chaque combinaison paramètre × actif × timeframe × sens × filtre compte comme un essai ; les variantes corrélées comptent moins (N effectif plus petit) mais le journal de N doit exister, sinon le résultat est ininterprétable.
- Pour un usage simple et robuste par un particulier : (1) échantillon de contrôle chronologique tenu hors de vue, utilisé une seule fois ; (2) journal du nombre de variantes ; (3) t-stat ≥ 3 (ou DSR > 0,95 avec N déclaré) sur l'ensemble ; (4) walk-forward à règles figées ; (5) test sur plusieurs actifs ; (6) bootstrap par blocs / Monte-Carlo sur l'ordre des trades pour borne basse de PF et drawdown ; (7) plateau de paramètres (les voisins du réglage choisi doivent aussi être rentables).

### Gaps
- Texte intégral de l'article DSR (SSRN 403) et du Notices AMS non relus dans leur version éditeur ; formule DSR/MinTRL vérifiée seulement via sources secondaires. Le PDF carmamaths (working paper de l'article « Pseudo-Mathematics ») a été relu directement.
- Chiffre « 7 846 règles » (Sullivan et al.) non vérifié dans le papier source.
- Je n'ai pas retrouvé de source primaire donnant un nombre minimal de trades « consensuel » ; il n'existe pas de règle des « 30 trades » validée par la littérature citée (30 est une convention de t-test sur des données normales, pas une règle de trading).

---

## 2. Réplication et déclin post-publication : McLean & Pontiff 2016, Hou-Xue-Zhang 2020

### Takeaway
Les anomalies publiées perdent environ un quart de leur rendement hors de l'échantillon d'origine (borne haute de l'effet de data mining) et plus de la moitié après publication ; une majorité des 452 anomalies d'une grande bibliothèque ne passent même pas t > 1,96 une fois les micro-caps neutralisées. Il faut s'attendre à ce que l'edge « live » soit nettement inférieur au backtest.

### Cited Findings
- McLean & Pontiff, « Does Academic Research Destroy Stock Return Predictability? », Journal of Finance 71(1), 2016 : 97 variables ; rendements de portefeuille 26 % plus bas hors échantillon et 58 % plus bas après publication ; le déclin hors échantillon est une borne supérieure de l'effet de data mining ; effet de la publication estimé à 32 % (58 % − 26 %) ; déclin post-publication plus fort pour les prédicteurs à rendement IS élevé ; rendements plus élevés pour les portefeuilles concentrés sur actions à risque idiosyncratique élevé et faible liquidité ; hausse des corrélations avec les autres portefeuilles publiés. — [McLean & Pontiff (version working paper, PDF)](https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf)
- Les auteurs peuvent rejeter l'hypothèse que la prévisibilité disparaît entièrement ; 85 des 97 prédicteurs (88 %) ont un t-stat IS ≥ 1,50. — même PDF.
- Hou, Xue & Zhang, « Replicating Anomalies », Review of Financial Studies 33(5), 2020, pp. 2019-2133 : sur une bibliothèque de 452 anomalies, en réduisant l'influence des micro-caps (breakpoints NYSE, rendements pondérés par la capitalisation), 65 % échouent au seuil unique |t| ≥ 1,96 (dont 96 % de la catégorie « trading frictions ») ; avec le seuil de tests multiples 2,78 (5 %), 82 % échouent ; même les anomalies répliquées ont des magnitudes économiques bien inférieures à celles publiées ; les auteurs concluent que les marchés sont plus efficients qu'on ne le croyait. — [IDEAS/RePEc](https://ideas.repec.org/a/oup/rfinst/v33y2020i5p2019-2133..html)
- Nuance : une critique rapportée est que le résultat repose fortement sur les micro-caps (3,2 % de la capitalisation, 60,7 % du nombre d'actions) et que la fragilité des anomalies en micro-caps était connue. — [Alpha Architect](https://alphaarchitect.com/replicating-anomalies/) (source secondaire)
- Une revue de 2022 mentionne que les déclins hors échantillon sont retrouvés par Jacobs & Müller (2018) et Chen & Zimmermann (2020) et que les périodes éloignées de l'échantillon d'origine montrent des déclins ≈ 50 % (source secondaire). — [arXiv 2209.13623](https://arxiv.org/pdf/2209.13623)

### Inferences
- Ces travaux portent sur des anomalies d'actions en coupe transversale, pas sur des signaux intraday de CFD ; la transposition est un ordre de grandeur, pas une mesure. Cela dit, la direction est claire : si un signal de CFD paraît bon avec un PF de 1,2, prévoir un PF live plus proche de 1,0–1,1 est raisonnable avant même les coûts.
- Le fait que les signaux faibles à gros t-stat IS soient ceux qui se dégradent le plus (McLean-Pontiff) plaide pour exiger de la marge : un PF de 1,2 est précisément la zone où la dégradation attendue efface l'edge.

### Gaps
- Pas de réplication équivalente trouvée pour des stratégies purement techniques sur CFD/forex/indices retail (seulement Sullivan-Timmermann-White sur le Dow Jones, voir §1).
- Je n'ai pas vérifié si McLean-Pontiff publient un chiffre de déclin par catégorie « signaux techniques/momentum » ; non extrait.

---

## 3. Coûts réels des CFD retail en Europe (XTB et équivalents)

### Takeaway
Chez XTB (compte Standard), il n'y a pas de commission sur indices/forex/matières premières/crypto : le coût est dans le spread plus le financement overnight (swap). En ordre de grandeur de notionnel : ≈ 0,006-0,009 % par aller-retour sur EURUSD/US100/or, ≈ 0,07 % sur le WTI, ≈ 0,30 % sur BTC ; le swap long annualisé va de ≈ 3 % (EURUSD) à ≈ 8-9 % (indices US, or, pétrole) et ≈ 35 % (BTC). Pour une stratégie intraday à edge de ~0,1 R par trade, le spread peut absorber l'essentiel de l'edge ; pour une stratégie lente, c'est le swap qui pèse.

### Cited Findings

**Structure des coûts (primaire XTB)**
- Sur les comptes Standard XTB, la commission n'est prélevée que sur les actions ; pour les autres classes (forex, indices, matières premières) le coût est intégré au spread ; le compte PRO applique des spreads de marché plus une commission par lot ouvert/fermé. Les montants du swap dépendent du marché et du sens (long/short). — [XTB, Swaps and charges](https://www.xtb.com/en/education/swaps-and-charges)
- XTB indique que les swaps/financements sont débités ou crédités chaque jour à minuit au taux du jour ; XTB étant teneur de marché, la marge incluse dans le swap est plafonnée à 100 %. Formule FX : 100 000 × lots × taux de swap journalier (%) × conversion. Indices/matières premières : prix × multiplicateur × lots × taux journalier, avec taux long = −(taux de base + marge) / jour et taux short = (marge − taux de base) / jour ; taux de base ESTER (EUR), SOFR (USD), SONIA (GBP), TONAR (JPY). Pour les cryptos, le financement est un pourcentage fixe de la valeur. — [XTB, Table des points de swap (version du 13-04-2026, FR)](https://xas-new-cdn.xtb.com/file/0090/17/e10a90ed-c5cc-440e-bdfc-9197a1566372/swaps-fr.pdf)

**Coûts illustratifs publiés par XTB (document ex-ante, mise à jour juin 2026)**
Hypothèses XTB : compte Standard en EUR, 1 lot, swap supposé constant par jour ; « costs may be subject to potential jumps » (simulation avec expansion du spread de 400 % + 10 % de swap : coût total EURUSD passe de −8,50 € à −42,50 € à l'ouverture). — [XTB, Ex-ante information (EUR, CFD), juin 2026](https://xas-new-cdn.xtb.com/file/0104/62/dfaabb01-3b00-4594-bb9b-77fb4bbf70b4/ex-ante-eur-en-cfd.pdf)

| Instrument | Notionnel 1 lot | Spread XTB (illustratif) | Coût de spread à l'ouverture | Swap long /jour | Swap short /jour |
|---|---|---|---|---|---|
| EURUSD | 100 000 EUR | 0,9 pip (0,00009) | 8,50 EUR | −0,007595 % | +0,002041 % |
| US100 | 510 000 USD | 1,25 point | 26,38 EUR | −0,021278 % | +0,000944 % |
| OIL.WTI | 57 000 USD | 0,04 | 34,87 EUR | −0,022667 % | −0,002333 % |
| GOLD | 433 000 USD | 0,35 | 32,27 EUR | −0,024056 % | −0,003722 % |
| BITCOIN | 88 400 USD | 265,3 | 227,71 EUR | −0,097222 % | −0,027778 % |

  (Aussi dans le document : ITA40 spread 20 points, EURNOK 42 pips. Pas de cas illustratif publié pour GER40, FR40, SPX500, USDJPY, NATGAS dans ce document.)

**Taux de financement du tableau de swaps XTB au 13-04-2026 (valeurs par jour)** — extraction de PDF, colonnes à interpréter avec prudence ; les taux ont changé entre avril et juin :
- Indices (long / short) : US100 −0,017864 % / −0,001139 % ; US500 −0,022859 % / −0,001139 % ; FRA40 −0,022472 % / −0,007136 % ; DE40 short −0,007136 % (le long n'a pas pu être extrait proprement ; les indices EUR de même type sont à ≈ −0,0179 % en long).
- Matières premières (long / short) : GOLD −0,033306 % / −0,013361 % ; NATGAS −0,041639 % / −0,021694 % ; OIL.WTI −0,041639 % / −0,021694 %.
- Forex : EURUSD −0,003705 % / +0,008117 % (colonnes pas certaines) ; USDJPY +0,004478 % / −0,011416 %.
- Crypto : BITCOIN −0,097222 % (long) / −0,027778 % (short). — [XTB, swaps (13-04-2026)](https://xas-new-cdn.xtb.com/file/0090/17/e10a90ed-c5cc-440e-bdfc-9197a1566372/swaps-fr.pdf)
- Note : le tableau du 13-04-2026 énonce que le coût de financement d'une position short sur CFD ne peut pas être positif, alors que le document ex-ante de juin 2026 affiche +0,000944 %/jour sur US100 short : ne pas supposer que le short est crédité.

**Spreads moyens exécutés publiés par XTB (dernier fichier trouvé : 1T 2022, compte « STANDARD+ », 0-1 lot)** — [XTB, Informationen zum durchschnittlich ausgeführten Spread, 1Q2022](https://de.xtb.com/hubfs/Informationen-zum-durchschnittlich-ausgefuehrten-Spread-bei-XTB_1Q2022.pdf) : US.100 1,297 ; DE.30 1,840 ; US.500 0,515 ; FRA.40 1,391 ; GOLD 0,339 ; OIL.WTI 0,0346 ; NATGAS 0,008265 ; EURUSD 0,000108 (≈ 1,08 pip) ; USDJPY 0,016009 (≈ 1,6 pip). Le document précise que ces valeurs sont indicatives et historiques sans garantie pour les périodes suivantes. Pas de ligne BTC dans ce fichier. Les autres blocs du PDF (autres paliers de volume/compte) n'ont pas pu être attribués clairement.

**Spreads vus par des tiers en 2026**
- Test en direct (août 2026, rapporté par un comparateur britannique) : EURUSD 0,9 pip (affiché « à partir de 0,8 »), US100 0,9 point, US500 0,6 point, UK100 1,8 point, or 0,30 (publié) ; commission 0 sur ces marchés ; le même site affiche à la fois « tested May 2026 » et « août 2026 », donc date incertaine. Coût de swap long testé « par lot par nuit » : EURUSD 7,55 $, or 33,47 $, pétrole 2,79 $ (conditions non précisées). — [The Investors Centre, XTB spreads](https://www.theinvestorscentre.co.uk/reviews/xtb-review/xtb-spreads/)
- BTC : spread « à partir de 0,22 % » (au 16 avril 2026, d'après un comparateur) avec levier max 1:5 ; en avril 2025 XTB aurait réduit les spreads crypto jusqu'à 60 % (BTC ≈ −41 %). — [CoinPro](https://www.coinpro.ch/en/?p=39559), [Finance Magnates](https://www.financemagnates.com/forex/brokers/xtb-boosts-crypto-cfds-offerings-for-institutions-cuts-spreads-by-60)
- Page XTB DE40 : une valeur « 0,9 » non étiquetée dans le bloc d'informations (interprétation de l'outil de recherche : spread typique en points, non confirmée) ; levier 1:20. — [xtb.com/ae-en/indices/de40](https://www.xtb.com/ae-en/indices/de40)

**Cadre réglementaire des coûts**
- ESMA (mesures du 23 mars 2018, publiées le 27 mars 2018) : leviers max pour particuliers 30:1 (paires majeures), 20:1 (paires non majeures, or, indices majeurs), 10:1 (matières premières hors or, indices non majeurs), 5:1 (actions), 2:1 (crypto) ; clôture automatique à 50 % de la marge minimale ; protection contre le solde négatif ; avertissement standardisé avec % de comptes perdants. — [ESMA](https://www.esma.europa.eu/node/84933)

### Inferences
- Coût d'un aller-retour rapporté au notionnel (spread XTB ex-ante ÷ notionnel converti à 0,85131 EUR/USD donné par le document) : EURUSD ≈ 0,0085 % ; US100 ≈ 0,0061 % ; or ≈ 0,0088 % ; WTI ≈ 0,072 % ; BTC ≈ 0,30 %. Ce sont mes calculs à partir des chiffres XTB, avec des valeurs illustratives de spread ; le spread réel varie (voir simulation 400 % de XTB).
- Swap annualisé (taux journalier × 365) pour une position long gardée : EURUSD ≈ −2,8 %/an ; US100 ≈ −7,8 % ; or ≈ −8,8 % ; WTI ≈ −8,3 % ; BTC ≈ −35,5 % (short BTC ≈ −10,1 %). Un swap de −0,024 %/jour sur l'or équivaut à ≈ 0,024 % de notionnel par nuit, soit une fraction non négligeable d'un stop intraday de 0,3-0,5 %.
- Effet sur la fréquence : coût par trade en unités de risque (R) = spread ÷ distance du stop. Exemple (arithmétique illustrative) : spread 1,5 pt sur GER40 avec stop de 15 pts = 0,10 R/trade. Un PF de 1,2 avec 40 % de réussite correspond à une espérance de seulement +0,12 R/trade ; il faut donc un PF brut ≈ 1,37 (gain moyen 2,05 R) pour obtenir 1,2 net. Plus le stop est serré et plus la fréquence est haute, plus le coût mange l'edge ; pour une stratégie lente (quelques trades par mois, stops larges), le spread est négligeable mais le swap (nuits) et le gap/slippage dominent.
- Les spreads sont plus larges aux heures creuses, à l'ouverture, sur annonces macro ; un backtest à spread constant sous-estime les coûts exactement là où les stratégies d'ouverture/news opèrent. Recommandation : tester avec spread × 2 comme scénario de stress.

### Gaps
- Aucune grille actuelle (2025-2026) officielle XTB trouvée pour les spreads moyens exécutés de GER40, FR40, SPX500, USDJPY, NATGAS ni BTC (le dernier fichier « average executed spread » trouvé date de 1T 2022 ; les pages instrument de xtb.com renvoyaient 404 ou n'étaient pas lisibles). À vérifier dans xStation (spécification du contrat) avant de fixer les paramètres de coût du backtest.
- Pas de commission PRO XTB en chiffres (tableau des commissions non extrait) ; pas de comparaison chiffrée avec d'autres courtiers (IG, CMC, Pepperstone) : le tableau Pepperstone n'a pas été ouvert.
- Les taux de swap changent chaque semaine ; valeurs d'avril et de juin 2026 divergent.

---

## 4. Statistiques sur les traders particuliers en CFD et day trading

### Takeaway
Les chiffres convergent : 74-89 % des comptes CFD de particuliers perdent de l'argent (ESMA, FCA, AMF, XTB aujourd'hui 72-77 %) ; la perte augmente avec le nombre d'ordres ; il n'y a pas d'apprentissage observable ; la minorité gagnante (< 1 % des day traders à Taïwan, ≈ 3 % au Brésil) est étroite et ses profits très volatils, et ce qui la distingue est la performance passée persistante, l'expérience et le volume, pas un indicateur particulier.

### Cited Findings

**Régulateurs / courtiers**
- ESMA (mars 2018) : les analyses des autorités nationales montrent que 74-89 % des comptes de particuliers perdent typiquement de l'argent en CFD, avec des pertes moyennes par client de 1 600 € à 29 000 €. — [ESMA](https://www.esma.europa.eu/node/84933)
- FCA (consultation CP16/40, déc. 2016) : 82 % des clients d'un échantillon représentatif de comptes CFD ont perdu de l'argent sur un an, perte moyenne par client 2 200 £ (chiffre « over 80 % » dans le texte de CP16/40 ; 82 % dans le communiqué). — [FCA CP16/40](https://www.fca.org.uk/publication/consultation/cp16-40.pdf), [FCA communiqué](https://fca.org.uk/news/press-releases/fca-proposes-stricter-rules-contract-difference-products)
- AMF (La lettre de l'Observatoire de l'épargne n° 10, oct. 2014 ; 14 799 clients actifs, 2009-2012, forex et CFD) : sur un an, 75 % à 89 % de clients perdants selon prestataire et année, ≈ 84 % tous prestataires confondus ; sur 4 ans, plus de 89 % de perdants ; perte moyenne ≈ 10 900 € par client, médiane 1 843 € ; 13 224 clients perdants pour ≈ 175 M€ au total contre 13,8 M€ de gains pour 1 575 clients gagnants. — [AMF, Lettre de l'Observatoire n° 10](https://www.amf-france.org/sites/institutionnel/files/contenu_simple/lettre_ou_cahier/lettre_observatoire/La%20lettre%20de%20l%27Observatoire%20de%20l%27epargne%20de%20l%27AMF%20-%20ndeg%2010%20-%20Octobre%202014.pdf)
- AMF, même étude : plus de trades, plus de perte — les clients ayant passé ≥ 250 ordres sur 4 ans (52 % de la population) ont perdu en moyenne 18 741 € ; ≥ 1 000 ordres (23 %) : 31 349 € ; sur les ≈ 2 000 traders actifs chacune des 4 années, 82 % perdaient en 2009, plus de 85 % sur 2 ans, ≈ 88 % sur 4 ans (perte 26 745 €) — pas d'apprentissage dans le temps. — même PDF.
- XTB affiche aujourd'hui dans ses avertissements : 72 % (site XTB, non daté), 77 % (comparateur BrokerChooser, mise à jour août 2025 et mai 2026), 74 % pour l'entité chypriote XTB Online Investing CY. BrokerChooser précise que ce pourcentage n'est pas une probabilité de perte individuelle et ne dit rien du montant. — [XTB Help Center (IT)](https://www.xtb.com/it/help-center/costi-e-commissioni-3), [BrokerChooser](https://brokerchooser.com/nl/broker-reviews/xtb-review/cfd-risk-warning)

**Day trading (Taïwan, Brésil)**
- Barber, Lee, Liu, Odean (et Zhang), « Do Day Traders Rationally Learn About Their Ability? » (Taïwan 1992-2006) : la performance agrégée des day traders est négative ; la grande majorité est non rentable ; plus de 75 % arrêtent en deux ans (survie à 1, 2, 3 ans : 44 %, 24 %, 15 %) ; beaucoup persistent malgré des pertes ; seule une minorité (< 1 % de la population de day traders) gagne de façon prévisible (référence à l'étude de 2014) ; la fraction rentable (≥ 10 jours d'expérience, profit cumulé > 0) est d'environ 5 %, et plus des 2/3 sont non rentables. — [Barber et al., version oct. 2017 (PDF)](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/day%20trading%20and%20learning%20110217.pdf)
- Barber, Lee, Liu, Odean, « The Cross-Section of Speculator Skill: Evidence from Day Trading », Journal of Financial Markets 18, 2014, pp. 1-24 : classement sur l'année y, performance sur l'année y+1 — les 500 premiers gagnent 61,3 bps/jour avant frais (37,9 après frais) et les derniers −11,5 (−28,9) ; moins de 1 % des day traders gagnent de façon fiable et prévisible net de frais. — [IDEAS/RePEc](https://ideas.repec.org/a/eee/finmar/v18y2014icp1-24.html), [eScholarship](https://www.escholarship.org/uc/item/7k75v0qx)
- Dans la même étude (version mai 2011) : ce qui prédit la rentabilité future est, « by a large margin », la performance passée ; puis l'expérience, le volume de day trading passé, la volonté de vendre à découvert et la concentration sur peu de titres ; l'agressivité des ordres n'est qu'un faible prédicteur ; les profits ne s'expliquent pas par un rôle de fournisseur de liquidité ni par de l'information privilégiée avant résultats. — [Barber et al., version mai 2011 (PDF)](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf)
- Chague, De-Losso, Giovannetti, « Day Trading for a Living? » (FGV EESP, WP 525, 2020 ; futures sur indice brésilien, entrants 2013-2015 ayant persisté ≥ 300 jours) : presque tous perdent ; les auteurs concluent qu'un particulier a peu de chance réaliste de vivre du day trading ; aucun signe d'amélioration avec l'expérience ; le meilleur trader gagne ≈ 310 US$/jour avec un écart-type de 2 560 US$. — [EconPapers](https://econpapers.repec.org/RePEc:fgv:eesptd:525), [IDEAS](https://ideas.repec.org/p/spa/wpaper/2019wpecon47.html)
- Chiffres rapportés par des sources secondaires pour cette étude : 97 % de perdants parmi les persistants, 19 646 traders dont 3,0 % à rendement journalier net positif, 1,1 % gagnent plus que le salaire minimum et 0,5 % plus qu'un guichetier débutant (SSRN) contre 0,4 % dans la version FGV. — [CXO Advisory](https://www.cxoadvisory.com/investing-expertise/day-trading-a-bust/), [Quantpedia](https://quantpedia.com/?p=4771), [SSRN 3423101](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101). Les auteurs signalent que la période a pu être particulièrement difficile pour les futures d'indices brésiliens (CXO).

### Inferences
- Ces études portent sur actions taïwanaises et futures brésiliens, pas sur CFD par un courtier teneur de marché : dans le CFD, la contrepartie du client est le courtier (modèle teneur de marché, indiqué par XTB dans son tableau des swaps), ce qui n'améliore pas les perspectives du client.
- Ce qui sépare les rares gagnants, dans les données disponibles : persistance de la performance passée, expérience cumulée, volume/volonté de prendre des positions courtes et concentration — aucune étude trouvée n'identifie un indicateur technique gagnant. Il faut se méfier de l'interprétation causale : ce sont des corrélations de classement.
- Implication pour le protocole : le prior à appliquer à une stratégie « maison » est celui de la minorité < 3-5 % ; l'exigence de preuve doit être calibrée en conséquence.

### Gaps
- Pas trouvé de source primaire sur le taux de perdants parmi les clients XTB sur longue période ni de distribution des gains (seulement le % d'avertissement réglementaire, non daté de façon cohérente : 72 % / 77 %).
- Les chiffres 97 %/3 % de Chague et al. viennent de sources secondaires (CXO, Quantpedia) : le PDF de l'article n'a pas été lu intégralement.
- Aucune étude trouvée sur la performance de traders particuliers spécifiquement sur or, GER40, BTC en CFD avec contrôle du style de trading (swing vs scalping).

---

## 5. Règle pratique : combien de trades et de durée pour qu'un PF de 1,2 soit distinguable de 1 ; évaluation du critère interne

### Takeaway
Un PF réel de 1,2 correspond à une espérance de ≈ +0,07 à +0,13 R par trade selon le profil gain/perte ; pour le distinguer de 1 avec un t ≈ 1,65-2, il faut environ 330-540 trades ; avec un seuil t ≥ 3 (HLZ), 1 100-1 300 trades. Avec 30 trades, une stratégie sans aucun edge dépasse PF 1,2 environ 3 fois sur 10, et une stratégie réellement à 1,2 affiche PF < 1 environ 3 fois sur 10. Le critère actuel (PF > 1,2 sur deux fenêtres, ≥ 30 trades, plusieurs actifs) n'est pas suffisant seul.

### Cited Findings
- Formules de base (statistiques élémentaires, non propres à un article) : t = E·√n / σ ; n = (z·σ/E)². Le Sharpe par trade vaut E/σ. — [Bailey & López de Prado, MinTRL (même structure : n ∝ z²/(SR−SR*)²)](https://ideas.repec.org/a/rsk/journ4/2223785.html)
- Harvey, Liu, Zhu : seuil de t-stat 3,0 pour une découverte nouvelle ; Hou-Xue-Zhang : 2,78 comme seuil de tests multiples. — [NBER w20592](https://www.nber.org/papers/w20592), [IDEAS HXZ](https://ideas.repec.org/a/oup/rfinst/v33y2020i5p2019-2133..html)
- Harvey & Liu : un t-ratio de 3,0 n'est plus automatiquement significatif après correction des tests multiples ; Bailey et al. : MinBTL nécessaire mais non suffisante. — [Harvey & Liu](https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF), [Bailey et al.](https://carmamaths.org/jon/backtest.pdf)

### Inferences (calculs propres : binomiale exacte pour payoffs fixes + Monte-Carlo pour payoffs variables, 20 000 tirages, gains log-normaux σ = 0,6)

**A. Taille d'échantillon (t-test sur l'espérance par trade), 4 profils tous à PF = 1,2 (perte = 1 R)**

| Profil (taux de réussite p, gain moyen b en R) | Espérance E | σ par trade | n pour t = 1,645 | n pour t = 1,96 | n pour t = 3,0 | n pour puissance 80 % (unilatéral 5 %) |
|---|---|---|---|---|---|---|
| p = 0,50, b = 1,20 | +0,100 R | 1,10 R | 327 | 465 | 1 089 | 748 |
| p = 0,40, b = 1,80 | +0,120 R | 1,37 R | 354 | 502 | 1 176 | 808 |
| p = 0,35, b = 2,23 | +0,130 R | 1,54 R | 380 | 539 | 1 263 | 868 |
| p = 0,65, b = 0,65 | +0,070 R | 0,79 R | 340 | 483 | 1 131 | 778 |

Règle mémo : pour un PF réel de 1,2, le Sharpe par trade est ≈ 0,085-0,09, donc n ≈ (z/0,087)² ≈ 130·z². Le Sharpe annualisé ≈ 0,087·√(trades par an) : 100 trades/an → ≈ 0,87.

**B. Fausses alertes et puissance à petit n (profil gain fixe ; zéro edge : p = 0,40, b = 1,5 ; vrai PF 1,2 : p = 0,40, b = 1,8)**

| n trades | Sans edge : P(PF ≥ 1,2) | Sans edge : P(PF ≥ 1,5) | Vrai PF 1,2 : P(PF observé < 1,0) | Vrai PF 1,2 : P(PF ≥ 1,2) |
|---|---|---|---|---|
| 30 | 28,5 % | 17,5 % | 29 % | 57 % |
| 50 | 23,4 % | 9,8 % | 24 % | 55 % |
| 100 | 17,9 % | 2,7 % | 18 % | 54 % |
| 200 | 11,0 % | 0,3 % | 11 % | 53 % |
| 300 | 5,6 % | 0 % | 7 % | 52 % |
| 500 | 2,0 % | 0 % | 2 % | 52 % |
| 1 000 | 0,2 % | 0 % | 0,3 % | 51 % |

(Avec payoffs variables log-normaux : sans edge P(PF ≥ 1,2) = 31 % à n = 30, 21 % à n = 100, 8 % à n = 300 ; vrai PF 1,2 : intervalle 5-95 % du PF observé = [0,54 ; 2,31] à n = 30, [0,81 ; 1,72] à n = 100, [0,96 ; 1,48] à n = 300 ; P(PF < 1) = 35 %, 23 %, 9 %.)
Note : à seuil = vrai PF, on passe 50 % du temps ; PF ≥ 1,2 observé sur une fenêtre ne prouve rien.

**C. Évaluation du critère « PF > 1,2 sur réglage ET contrôle, ≥ 30 trades, plusieurs actifs » (stratégie sans edge, fenêtres de 30 trades)**
- Probabilité qu'UNE variante sans edge passe les deux fenêtres (n = 30 chacune) : ≈ 8,2 %. Si l'on teste K variantes indépendantes : K = 5 → 35 % ; K = 10 → 57 % ; K = 20 → 82 % ; K = 50 → 99 %. Avec n = 100 par fenêtre : K = 10 → 28 % ; K = 20 → 48 % ; K = 50 → 80 %. Avec n = 200 : K = 10 → 12 % ; K = 20 → 22 % ; K = 50 → 46 %.
- Exiger la réussite sur plusieurs actifs aide, mais seulement si les actifs sont indépendants : sur 8 actifs indépendants (n = 30 par fenêtre), P(≥ 1 réussite) = 49 % ; P(≥ 2) = 13 % ; P(≥ 3) = 2,2 % ; P(≥ 4) = 0,24 %. Sur 4 actifs : ≥ 2 → 3,6 % ; ≥ 3 → 0,2 %. Or GER40/FR40/SPX500/US100 sont très corrélés : leur N effectif est plus proche de 1-2 que de 4. Il faut donc des actifs de familles différentes (indice, or, FX, pétrole/gaz, crypto).
- Le critère est donc insuffisant : trop peu de trades (30 est inférieur à tout calcul de puissance ci-dessus), le nombre d'essais n'est pas pris en compte, et il ignore les coûts (§3) et la dégradation attendue (§2).

**D. Critère d'acceptation prudent proposé (graduel, à adapter)**
1. Journal figé avant test : liste des variantes (paramètres × actifs × timeframes × sens), N total déclaré ; échantillon de contrôle chronologique, jamais utilisé pour choisir, évalué une seule fois ; un échec n'autorise pas à « réessayer le contrôle ».
2. Données nettes de coûts : spread du compte réel, avec scénario de stress (spread × 2) et swap réel pour les positions gardées la nuit (§3). Le PF net — pas brut — doit être compté.
3. Taille minimale : ≥ 100 trades par fenêtre et ≥ 300 trades agrégés pour une présomption faible (t ≈ 1,65) ; ≥ 500 pour t ≈ 2 ; ≥ 1 000 pour viser t ≥ 3 sur un PF de 1,2. Si la fréquence ne le permet pas, soit chercher un edge plus gros (PF 1,5 : espérance +0,25 à +0,30 R, soit n ≈ 100-110 trades pour t ≈ 2 d'après la même formule, profils p = 0,5/b = 1,5 et p = 0,4/b = 2,25 ; à re-simuler pour le profil réel), soit accepter que 1,2 n'est pas démontrable avec les données disponibles.
4. Preuve statistique : borne basse du PF à 90-95 % (bootstrap par blocs sur les trades) > 1,0 net de coûts ; ou DSR > 0,95 avec N déclaré ; ou t ≥ 3 si l'on a exploré ≳ 20 variantes (HLZ, Harvey-Liu). Pour 50 variantes sur 5 ans, viser un Sharpe annualisé ≳ 1,0 (tableau §1) comme plancher du « hasard attendu ».
5. Robustesse : au moins 3 familles d'actifs non corrélées avec profil de même signe ; le même réglage fixe (pas ré-optimisé par actif) ; plateau de paramètres (± 20 % sur chaque paramètre ne fait pas passer le PF net sous 1,1) ; walk-forward à règles figées ; performance acceptable dans au moins deux régimes (haussier/baissier/range).
6. Haircut attendu avant mise en réel : appliquer au moins 25-50 % de décote sur l'edge (McLean-Pontiff : 26 % hors échantillon, 58 % après publication ; Harvey-Liu : décote plus forte pour les petits Sharpe) ; ne passer en réel que si l'edge décoté reste > 0 après coûts.
7. Phase papier/micro-lot de ≥ 100 trades avant toute exposition significative ; critère d'arrêt chiffré défini à l'avance (drawdown, PF glissant).

### Gaps
- Mes simulations supposent des trades indépendants et i.i.d. ; l'autocorrélation, la dépendance de volatilité et les clusters d'événements macro gonflent l'incertitude réelle (n effectif plus petit que le nombre de trades).
- Les profils gain/perte (p, b) sont illustratifs ; le calcul doit être refait avec la distribution réelle des R-multiples de la stratégie testée (bootstrap des trades) et les coûts par instrument.
- Le chiffre « PF 1,5 → n ≈ 100-110 pour t ≈ 2 » vient de la formule fermée, pas d'une simulation.
- Aucune source trouvée donnant un PF minimal « standard » reconnu ; PF n'est pas une statistique standard de la littérature académique (qui raisonne en Sharpe/t-stat) : la conversion PF → Sharpe dépend du taux de réussite.
