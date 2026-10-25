"""Contrôle de robustesse du journal de trades — LECTURE SEULE.

Mesure ce que le hasard seul peut produire à partir des trades déjà clos (drawdown, série de pertes,
profit factor, R total). Ce n'est PAS une prédiction : le rééchantillonnage ne crée aucune
information, il mesure l'incertitude de l'échantillon existant.

Trois couches séparées :
  1. lecture   : apparier_journal() transforme les lignes du journal en trades avec R ;
  2. calcul    : fonctions pures (statistiques, rééchantillonnage), sans entrée/sortie ;
  3. rapport   : rapport_markdown() met en forme le résultat en français.

Aucune écriture dans Neon ni dans le journal. Source : un export JSON de GET /api/journal
(liste de lignes). Usage :
    python outils/robustesse_journal.py journal_export.json [--graine 12345] [--tirages 10000] [--sortie rapport.md]
"""
import argparse
import json
import math
import random
import sys
from datetime import datetime

SEUIL_MIN = 30        # en dessous : aucun chiffre de simulation (critère déjà retenu par le projet)
SEUIL_STANDARD = 100  # entre SEUIL_MIN et ici : chiffres affichés comme « indicatifs »
GRAINE_DEFAUT = 12345
TIRAGES_DEFAUT = 10000


# --------------------------------------------------------------------------------------------
# 1. Lecture : appariement des lignes du journal (mêmes règles que buildJournalTrades, index.html)
# --------------------------------------------------------------------------------------------

def _r_valide(v):
    """Un R n'est utilisable que s'il est un nombre fini (jamais inventé, jamais estimé)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v) if math.isfinite(v) else None


def _propre(v):
    """Valeur texte utilisable, ou None (absente, vide ou « -- » du journal)."""
    return None if v in (None, "", "--") else v


def _duree_minutes(debut, fin):
    try:
        return (datetime.fromisoformat(fin) - datetime.fromisoformat(debut)).total_seconds() / 60.0
    except (TypeError, ValueError):
        return None


def _etiquette_htf(v):
    return "alignée H1" if v is True else ("non alignée H1" if v is False else "inconnue")


def _id_test_probable(trade_id):
    """Les trade_id réels se terminent par un horodatage en millisecondes (13 chiffres) ;
    un suffixe court (ex. GOLD-1729000000) ressemble à une ligne de test. Heuristique, jamais une certitude."""
    if not isinstance(trade_id, str) or "-" not in trade_id:
        return False
    suffixe = trade_id.rsplit("-", 1)[1]
    return suffixe.isdigit() and len(suffixe) < 12


def apparier_journal(lignes):
    """Apparie entrée + sortie suivante du même actif.

    Renvoie (trades, exclusions). Un trade = {symbole, entree, sortie, statut, r, version, session, jour}.
    exclusions = compteurs et listes à part : jamais comptées dans le bilan.
    """
    triees = sorted(lignes, key=lambda r: r.get("time") or "")
    ouvertes, trades = {}, []
    exclusions = {"remplacees": [], "sans_r": [], "orphelines": [], "sans_sortie": [],
                  "derniere_ligne": triees[-1].get("time") if triees else None}  # référence de date (pas l'horloge)

    for r in triees:
        sym = r.get("symbol")
        if r.get("kind") == "entry":
            if sym in ouvertes:  # nouvelle entrée avant la sortie : la précédente n'a pas de résultat
                exclusions["remplacees"].append(ouvertes[sym])
            ouvertes[sym] = r
        elif r.get("kind") == "exit":
            entree = ouvertes.pop(sym, None)
            if entree is None:
                exclusions["orphelines"].append(r)   # sortie sans entrée connue : résultat indisponible
            elif r.get("status") == "REPLACED":
                exclusions["remplacees"].append(entree)
            else:
                val = _r_valide(r.get("r_multiple"))
                if val is None:
                    exclusions["sans_r"].append(r)   # résultat indisponible : exclu, listé à part
                else:
                    trades.append({
                        "symbole": sym,
                        "entree": entree.get("time"),
                        "sortie": r.get("time"),
                        "statut": r.get("status"),
                        "r": val,
                        "version": r.get("version") or entree.get("version") or "inconnue",
                        "session": r.get("session_at_entry") or entree.get("session") or "inconnue",
                        "jour": (r.get("time") or "")[:10],  # jour de sortie (date UTC du journal)
                        "setup": _propre(entree.get("status")) or _propre(r.get("entry_status")) or "inconnu",
                        "qualite": _propre(r.get("quality")) or _propre(entree.get("quality")) or "inconnue",
                        "htf": _etiquette_htf(r.get("htf_aligned", entree.get("htf_aligned"))),
                        "best_r": _r_valide(r.get("best_r")),   # meilleur R atteint pendant le trade (absent avant R6.1)
                        "duree_min": _duree_minutes(entree.get("time"), r.get("time")),
                        "trade_id": r.get("trade_id") or entree.get("trade_id"),
                    })
    exclusions["sans_sortie"] = list(ouvertes.values())  # entrées encore ouvertes ou sortie manquante
    return trades, exclusions


def charger_journal(chemin):
    """Charge un export JSON de /api/journal (liste de lignes)."""
    with open(chemin, "r", encoding="utf-8") as f:
        donnees = json.load(f)
    if not isinstance(donnees, list):
        raise ValueError("Le fichier doit contenir une liste de lignes de journal.")
    return donnees


# --------------------------------------------------------------------------------------------
# 2. Calcul : fonctions pures
# --------------------------------------------------------------------------------------------

def niveau_confiance(n):
    if n < SEUIL_MIN:
        return "insuffisant"
    if n < SEUIL_STANDARD:
        return "indicatif"
    return "standard"


def profit_factor(rs):
    """Somme des R positifs / |somme des R négatifs|. inf s'il n'y a aucune perte, None sans gain ni perte."""
    gains = sum(r for r in rs if r > 0)
    pertes = -sum(r for r in rs if r < 0)
    if pertes == 0:
        return math.inf if gains > 0 else None
    return gains / pertes


def drawdown_max(rs):
    """Plus grande baisse du R cumulé depuis son sommet (le cumul part de 0). Valeur >= 0."""
    cumul = sommet = pire = 0.0
    for r in rs:
        cumul += r
        sommet = max(sommet, cumul)
        pire = max(pire, sommet - cumul)
    return pire


def serie_pertes_max(rs):
    plus_longue = courante = 0
    for r in rs:
        courante = courante + 1 if r < 0 else 0
        plus_longue = max(plus_longue, courante)
    return plus_longue


def statistiques(rs):
    n = len(rs)
    gagnants = sum(1 for r in rs if r > 0)
    perdants = sum(1 for r in rs if r < 0)
    return {
        "n": n,
        "gagnants": gagnants,
        "perdants": perdants,
        "nuls": n - gagnants - perdants,
        "r_total": sum(rs),
        "r_moyen": sum(rs) / n if n else None,
        "win_rate": gagnants / n if n else None,
        "profit_factor": profit_factor(rs),
        "drawdown_max": drawdown_max(rs),
        "serie_pertes_max": serie_pertes_max(rs),
    }


def percentile(valeurs, p):
    """Percentile p (0-100) par interpolation linéaire. Gère inf sans produire de nan."""
    if not valeurs:
        return None
    v = sorted(valeurs)
    pos = (len(v) - 1) * p / 100.0
    bas, haut = int(math.floor(pos)), int(math.ceil(pos))
    if bas == haut or v[bas] == v[haut]:
        return v[bas]
    return v[bas] + (v[haut] - v[bas]) * (pos - bas)


def _tirage_simple(rs, rng):
    return [rs[rng.randrange(len(rs))] for _ in range(len(rs))]


def _tirage_blocs_jour(blocs, n, rng):
    """Tire des jours entiers (avec remise) jusqu'à avoir n trades ; l'ordre dans le jour est conservé."""
    sortie = []
    while len(sortie) < n:
        sortie.extend(blocs[rng.randrange(len(blocs))])
    return sortie[:n]


def blocs_par_jour(trades):
    """Regroupe les R par jour de sortie, dans l'ordre chronologique des trades."""
    jours = {}
    for t in sorted(trades, key=lambda t: t["sortie"] or ""):
        jours.setdefault(t["jour"], []).append(t["r"])
    return list(jours.values())


def reechantillonner(trades, methode, tirages=TIRAGES_DEFAUT, graine=GRAINE_DEFAUT):
    """Rééchantillonne les R et résume la distribution. methode = « simple » ou « blocs_jour ».

    Même graine => mêmes résultats. Ne s'applique qu'à N >= SEUIL_MIN (sinon ValueError).
    """
    n = len(trades)
    if n < SEUIL_MIN:
        raise ValueError(f"Échantillon insuffisant (N={n} < {SEUIL_MIN}) : aucune simulation.")
    if methode not in ("simple", "blocs_jour"):
        raise ValueError("méthode inconnue : " + methode)
    rng = random.Random(graine)
    rs = [t["r"] for t in sorted(trades, key=lambda t: t["sortie"] or "")]
    blocs = blocs_par_jour(trades)

    totaux, drawdowns, series, pfs = [], [], [], []
    for _ in range(tirages):
        tirage = _tirage_simple(rs, rng) if methode == "simple" else _tirage_blocs_jour(blocs, n, rng)
        totaux.append(sum(tirage))
        drawdowns.append(drawdown_max(tirage))
        series.append(serie_pertes_max(tirage))
        pf = profit_factor(tirage)
        if pf is not None:
            pfs.append(pf)

    def resume(valeurs):
        return {"p5": percentile(valeurs, 5), "p50": percentile(valeurs, 50), "p95": percentile(valeurs, 95)}

    return {
        "methode": methode,
        "tirages": tirages,
        "graine": graine,
        "r_total": resume(totaux),
        "drawdown_max": resume(drawdowns),
        "serie_pertes_max": resume(series),
        "profit_factor": resume(pfs),
        "part_r_total_negatif_ou_nul": sum(1 for t in totaux if t <= 0) / tirages,
    }


def ventiler(trades, cle):
    """Évalue chaque groupe seulement s'il atteint SEUIL_MIN ; sinon « non évaluable » (N seul)."""
    groupes = {}
    for t in trades:
        groupes.setdefault(t.get(cle, "inconnu"), []).append(t)
    sortie = {}
    for nom, g in sorted(groupes.items(), key=lambda kv: -len(kv[1])):
        if len(g) < SEUIL_MIN:
            sortie[nom] = {"n": len(g), "evaluable": False}
        else:
            sortie[nom] = {"n": len(g), "evaluable": True, "stats": statistiques([t["r"] for t in g])}
    return sortie


DUREE_NORMALE_MAX_MIN = 180   # 30 bougies M5 = 150 min ; marge de 30 min avant de signaler
SL_RAPIDE_MIN = 30            # « SL touché très vite » = en 30 minutes ou moins
RETOUR_R = 1.0                # « retour » = a atteint au moins +1 R avant de finir en perte


def anomalies(trades, exclusions):
    """Signale ce qui peut fausser la mesure. Ne corrige rien, ne supprime rien : à vérifier à la main.

    La référence de date est la dernière ligne du journal (jamais l'horloge), donc le résultat est reproductible."""
    liste = []
    for t in trades:
        d = t.get("duree_min")
        if d is not None and d > DUREE_NORMALE_MAX_MIN:
            liste.append({"type": "durée anormale", "symbole": t["symbole"], "date": t["entree"],
                          "detail": f"{d / 60:.1f} h entre l'entrée et la sortie ({t['statut']}, R {t['r']:+.2f}) : "
                                    "le R peut ne pas correspondre à la 30e bougie M5"})
        if d is not None and d * 60 < 2:
            liste.append({"type": "entrée et sortie simultanées", "symbole": t["symbole"], "date": t["entree"],
                          "detail": f"sortie {t['statut']} moins de 2 s après l'entrée (R {t['r']:+.2f})"})
        if _id_test_probable(t.get("trade_id")):
            liste.append({"type": "identifiant de test probable", "symbole": t["symbole"], "date": t["entree"],
                          "detail": f"trade_id {t['trade_id']} (suffixe trop court pour un horodatage réel)"})
    for o in exclusions.get("orphelines", []):
        if _id_test_probable(o.get("trade_id")):
            liste.append({"type": "ligne de test probable", "symbole": o.get("symbol"), "date": o.get("time"),
                          "detail": f"sortie sans entrée, trade_id {o.get('trade_id')} : exclue du bilan"})
        else:
            liste.append({"type": "sortie orpheline", "symbole": o.get("symbol"), "date": o.get("time"),
                          "detail": f"{o.get('status')} sans entrée connue : résultat indisponible, exclue du bilan"})
    ref = exclusions.get("derniere_ligne")
    for e in exclusions.get("sans_sortie", []):
        age = _duree_minutes(e.get("time"), ref)
        if age is not None and age > DUREE_NORMALE_MAX_MIN:
            liste.append({"type": "entrée sans sortie", "symbole": e.get("symbol"), "date": e.get("time"),
                          "detail": f"aucune sortie depuis {age / 60:.0f} h (une expiration survient normalement à 2 h 30) : "
                                    "position probablement bloquée ou sortie perdue"})
    return liste


def motifs(trades):
    """Compte des motifs récurrents. DESCRIPTIF : des effectifs sur l'échantillon, jamais une preuve."""
    sl = [t for t in trades if t["statut"] == "SL_HIT"]
    sl_rapides = [t for t in sl if t.get("duree_min") is not None and t["duree_min"] <= SL_RAPIDE_MIN]
    avec_best = [t for t in trades if t.get("best_r") is not None]
    retours = [t for t in avec_best if t["best_r"] >= RETOUR_R and t["r"] < 0]
    par_sortie = {}
    for t in trades:
        s = par_sortie.setdefault(t["statut"], {"n": 0, "r_total": 0.0})
        s["n"] += 1
        s["r_total"] += t["r"]
    return {
        "sl_rapide": {"n": len(sl_rapides), "sur": len(sl), "cas": sl_rapides},
        "retour_apres_1r": {"n": len(retours), "sur": len(avec_best), "cas": retours,
                            "r_perdu": sum(-t["r"] for t in retours)},
        "par_sortie": par_sortie,
    }


# --------------------------------------------------------------------------------------------
# 3. Rapport
# --------------------------------------------------------------------------------------------

def _f(v, fmt="{:+.2f}"):
    if v is None:
        return "n/a"
    if isinstance(v, float) and math.isinf(v):
        return "∞"
    return fmt.format(v)


def _ligne_resume(nom, d, fmt="{:.2f}"):
    return f"| {nom} | {_f(d['p5'], fmt)} | {_f(d['p50'], fmt)} | {_f(d['p95'], fmt)} |"


LIMITES = [
    "Le R est théorique : TP au R prévu, SL à −1 exactement, sans glissement ni écart de prix ; "
    "les `EXPIRED` sont calculés au prix de clôture enregistré.",
    "Les trades futurs peuvent différer (régime de marché, nouvelle version du Radar).",
    "Mélanger des versions de script (`version`) mélange des logiques différentes.",
    "Le rééchantillonnage ne crée pas d'information : il mesure l'incertitude de l'échantillon existant. "
    "Ce n'est pas une prédiction et ne valide aucune stratégie.",
]


def rapport_markdown(trades, exclusions, source, date_rapport, tirages=TIRAGES_DEFAUT, graine=GRAINE_DEFAUT):
    n = len(trades)
    niveau = niveau_confiance(n)
    out = [f"# Contrôle de robustesse du journal — {date_rapport}", "",
           f"- Source : `{source}` (lecture seule)",
           f"- Trades avec R utilisés : **{n}**",
           f"- Exclus : {len(exclusions['sans_r'])} sans R, {len(exclusions['orphelines'])} sorties orphelines, "
           f"{len(exclusions['remplacees'])} remplacées, {len(exclusions['sans_sortie'])} entrées sans sortie",
           f"- Rééchantillonnage : {tirages} tirages, graine {graine}", ""]

    if n < SEUIL_MIN:
        out += [f"**Échantillon insuffisant (N={n} < {SEUIL_MIN}) : aucun chiffre de simulation n'est produit.**", ""]
    else:
        if niveau == "indicatif":
            out += [f"> Avertissement : N={n} (entre {SEUIL_MIN} et {SEUIL_STANDARD}). "
                    "Les intervalles sont très larges, résultats **indicatifs** seulement.", ""]
        s = statistiques([t["r"] for t in trades])
        out += ["## Résultat observé", "",
                f"- Gagnants / perdants / nuls : {s['gagnants']} / {s['perdants']} / {s['nuls']}",
                f"- R total : {_f(s['r_total'])} R — R moyen : {_f(s['r_moyen'], '{:+.3f}')} R",
                f"- Win rate : {_f(100 * s['win_rate'], '{:.0f}')} % — profit factor : {_f(s['profit_factor'], '{:.2f}')}",
                f"- Drawdown max : {_f(s['drawdown_max'], '{:.2f}')} R — plus longue série de pertes : {s['serie_pertes_max']}", ""]
        sim = {m: reechantillonner(trades, m, tirages, graine) for m in ("simple", "blocs_jour")}
        titres = {"simple": "Tirage simple (trades supposés indépendants)",
                  "blocs_jour": "Tirage par blocs d'un jour (référence : tient compte des trades corrélés d'un même jour)"}
        for m in ("blocs_jour", "simple"):
            d = sim[m]
            out += [f"## {titres[m]}", "", "| Mesure | 5 % | Médiane | 95 % |", "|---|---|---|---|",
                    _ligne_resume("R total", d["r_total"], "{:+.2f}"),
                    _ligne_resume("Drawdown max (R)", d["drawdown_max"]),
                    _ligne_resume("Plus longue série de pertes", d["serie_pertes_max"], "{:.0f}"),
                    _ligne_resume("Profit factor", d["profit_factor"]), "",
                    f"Part des tirages où le R total est ≤ 0 : **{100 * d['part_r_total_negatif_ou_nul']:.0f} %**", ""]
        ecart = abs(sim["simple"]["part_r_total_negatif_ou_nul"] - sim["blocs_jour"]["part_r_total_negatif_ou_nul"])
        if ecart > 0.05:
            out += ["> Les deux méthodes divergent de plus de 5 points : **la méthode par blocs d'un jour fait foi.**", ""]

        for cle, titre in (("version", "version du script"), ("symbole", "actif"), ("session", "session d'entrée"),
                           ("setup", "type de setup"), ("qualite", "qualité"), ("htf", "alignement H1")):
            groupes = ventiler(trades, cle)
            out += [f"## Ventilation par {titre}", ""]
            if not any(g["evaluable"] for g in groupes.values()):
                effectifs = ", ".join(f"{nom} {g['n']}" for nom, g in groupes.items())
                out += [f"Non évaluable : aucun groupe n'atteint {SEUIL_MIN} trades. Effectifs : {effectifs}.", ""]
                continue
            out += ["| Groupe | N | Évaluable | R total | Profit factor |", "|---|---|---|---|---|"]
            for nom, g in groupes.items():
                if g["evaluable"]:
                    st = g["stats"]
                    out.append(f"| {nom} | {g['n']} | oui | {_f(st['r_total'])} | {_f(st['profit_factor'], '{:.2f}')} |")
                else:
                    out.append(f"| {nom} | {g['n']} | non (N < {SEUIL_MIN}) | non évaluable | non évaluable |")
            out.append("")

    if n >= SEUIL_MIN:
        m = motifs(trades)
        out += ["## Motifs récurrents (descriptif : des effectifs, pas une preuve)", ""]
        sl = m["sl_rapide"]
        out.append(f"- SL touché en {SL_RAPIDE_MIN} min ou moins : **{sl['n']} sur {sl['sur']}** stops loss")
        rt = m["retour_apres_1r"]
        if rt["sur"]:
            out.append(f"- Trades ayant atteint au moins +{RETOUR_R:g} R avant de finir en perte : **{rt['n']} sur {rt['sur']}** "
                       f"(trades dont le meilleur R est connu) ; R perdu sur ces cas : {_f(rt['r_perdu'], '{:.2f}')} R. "
                       "Ce chiffre est un plafond pour une règle de type break-even : le R maximal ne dit pas dans quel ordre "
                       "le prix a bougé, il faut rejouer les bougies M5 pour conclure.")
            for t in rt["cas"]:
                out.append(f"  - {t['entree'][:16]} {t['symbole']} : meilleur R {t['best_r']:+.2f}, résultat {t['r']:+.2f} ({t['statut']})")
        else:
            out.append("- Retour après +1 R : non évaluable (le meilleur R n'est pas enregistré avant R6.1).")
        out += ["- Répartition par type de sortie :"]
        out += [f"  - {k} : {v['n']} trades, R total {_f(v['r_total'])}" for k, v in sorted(m["par_sortie"].items())]
        out.append("")
    ano = anomalies(trades, exclusions)
    if ano:
        out += ["## Qualité des données (à vérifier : rien n'a été modifié)", "",
                "| Type | Actif | Date | Détail |", "|---|---|---|---|"]
        out += [f"| {a['type']} | {a['symbole']} | {(a['date'] or '')[:16]} | {a['detail']} |" for a in ano]
        out.append("")

    if exclusions["sans_r"] or exclusions["orphelines"]:
        out += ["## Résultat indisponible (exclus du bilan, listés à part)", ""]
        for r in exclusions["sans_r"] + exclusions["orphelines"]:
            out.append(f"- {r.get('time')} — {r.get('symbol')} — {r.get('status')} : résultat indisponible")
        out.append("")
    if exclusions["sans_sortie"]:
        out += ["## Entrées sans sortie (exclues)", ""]
        out += [f"- {r.get('time')} — {r.get('symbol')} ({r.get('status')})" for r in exclusions["sans_sortie"]]
        out.append("")
    out += ["## Limites", ""] + [f"- {l}" for l in LIMITES] + [""]
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description="Contrôle de robustesse du journal (lecture seule).")
    p.add_argument("journal", help="export JSON de /api/journal")
    p.add_argument("--graine", type=int, default=GRAINE_DEFAUT)
    p.add_argument("--tirages", type=int, default=TIRAGES_DEFAUT)
    p.add_argument("--sortie", help="écrit aussi le rapport dans ce fichier Markdown")
    a = p.parse_args(argv)
    trades, exclusions = apparier_journal(charger_journal(a.journal))
    texte = rapport_markdown(trades, exclusions, a.journal, datetime.now().strftime("%d/%m/%Y"), a.tirages, a.graine)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(texte)
    if a.sortie:
        with open(a.sortie, "w", encoding="utf-8") as f:
            f.write(texte)


if __name__ == "__main__":
    main()
