"""Test ciblé : contrôle de robustesse du journal (outils/robustesse_journal.py). Données de test uniquement :
aucun accès à Neon, au réseau ni aux vraies données du journal."""
import contextlib
import io
import json
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from outils import robustesse_journal as rj  # noqa: E402


def entree(t, sym, **extra):
    return dict({"kind": "entry", "time": t, "symbol": sym, "status": "SSL SWEEP", "direction": "BUY"}, **extra)


def sortie(t, sym, status="EXPIRED", r=None, **extra):
    return dict({"kind": "exit", "time": t, "symbol": sym, "status": status, "r_multiple": r}, **extra)


def trades_test(rs, jours=None):
    """N trades fictifs ; `jours` = nombre de jours sur lesquels ils sont répartis (par défaut 1 trade par jour)."""
    out = []
    for i, r in enumerate(rs):
        j = (i % jours) if jours else i
        out.append({"symbole": "GOLD", "entree": "x", "sortie": f"2026-01-{j + 1:02d}T10:{i % 60:02d}:00", "statut": "EXPIRED",
                    "r": r, "version": "R6.3" if i % 2 else "R6.2", "session": "NY", "jour": f"2026-01-{j + 1:02d}"})
    return out


# --- Appariement -----------------------------------------------------------------------------

def test_appariement_cas_limites():
    lignes = [
        entree("2026-10-01T10:00:00", "GOLD"), sortie("2026-10-01T12:30:00", "GOLD", "TP_HIT", 2.0, version="R6.3"),
        entree("2026-10-01T11:00:00", "US100"),                                    # sans sortie
        sortie("2026-10-01T13:00:00", "USOIL", "TP_HIT", None),                    # orpheline, sans R
        entree("2026-10-02T09:00:00", "EURUSD"), entree("2026-10-02T09:30:00", "EURUSD"),  # la 1re est remplacée
        sortie("2026-10-02T12:00:00", "EURUSD", "SL_HIT", -1),
        entree("2026-10-03T09:00:00", "SPX500"), sortie("2026-10-03T10:00:00", "SPX500", "REPLACED", None),
        entree("2026-10-04T09:00:00", "FR40"), sortie("2026-10-04T10:00:00", "FR40", "EXPIRED", None),  # R indisponible
        entree("2026-10-05T09:00:00", "GER40"), sortie("2026-10-05T10:00:00", "GER40", "BE_HIT", 0.0),
        entree("2026-10-06T09:00:00", "NATGAS"), sortie("2026-10-06T10:00:00", "NATGAS", "EXPIRED", float("nan")),
        entree("2026-10-07T09:00:00", "USDJPY"), sortie("2026-10-07T10:00:00", "USDJPY", "EXPIRED", True),
    ]
    trades, ex = rj.apparier_journal(lignes)
    assert [t["symbole"] for t in trades] == ["GOLD", "EURUSD", "GER40"], trades
    assert [t["r"] for t in trades] == [2.0, -1.0, 0.0]                      # BE_HIT = nul, compté
    assert [r["symbol"] for r in ex["sans_sortie"]] == ["US100"]
    assert [r["symbol"] for r in ex["orphelines"]] == ["USOIL"]
    assert len(ex["remplacees"]) == 2                                        # entrée écrasée + REPLACED
    assert sorted(r["symbol"] for r in ex["sans_r"]) == ["FR40", "NATGAS", "USDJPY"]  # None, nan, booléen : exclus
    assert trades[0]["version"] == "R6.3" and trades[1]["version"] == "inconnue"


def test_ordre_des_lignes_sans_importance():
    lignes = [sortie("2026-10-01T12:00:00", "GOLD", "SL_HIT", -1), entree("2026-10-01T10:00:00", "GOLD")]
    trades, _ = rj.apparier_journal(lignes)
    assert len(trades) == 1 and trades[0]["r"] == -1.0


# --- Calcul ----------------------------------------------------------------------------------

def test_statistiques_sequence_connue():
    rs = [1, -1, -1, -1, 2, -1]       # cumul 1, 0, -1, -2, 0, -1 -> sommet 1, creux -2
    s = rj.statistiques(rs)
    assert s["n"] == 6 and s["gagnants"] == 2 and s["perdants"] == 4 and s["nuls"] == 0
    assert math.isclose(s["r_total"], -1) and math.isclose(s["drawdown_max"], 3.0)
    assert s["serie_pertes_max"] == 3 and math.isclose(s["profit_factor"], 3 / 4)
    assert math.isclose(s["win_rate"], 2 / 6)


def test_profit_factor_cas_limites():
    assert rj.profit_factor([1, 2]) == math.inf
    assert rj.profit_factor([0, 0]) is None
    assert rj.profit_factor([]) is None
    assert math.isclose(rj.profit_factor([2, -1]), 2.0)


def test_percentile():
    assert rj.percentile([], 50) is None
    assert rj.percentile([5], 5) == 5
    assert math.isclose(rj.percentile([0, 10], 50), 5)
    assert rj.percentile([1, math.inf], 95) == math.inf          # pas de nan avec inf


def test_reproductibilite_et_graine():
    t = trades_test([1.5, -1, -1, 0.5, -1, 2, -0.4, -1, 0.7, -1] * 4, jours=7)
    a = rj.reechantillonner(t, "blocs_jour", tirages=300, graine=1)
    b = rj.reechantillonner(t, "blocs_jour", tirages=300, graine=1)
    c = rj.reechantillonner(t, "blocs_jour", tirages=300, graine=2)
    assert a == b                                                # même graine, mêmes résultats
    assert a != c
    s = rj.reechantillonner(t, "simple", tirages=300, graine=1)
    assert s["tirages"] == 300 and s["graine"] == 1
    assert 0 <= s["part_r_total_negatif_ou_nul"] <= 1


def test_tirage_blocs_jour_conserve_n_et_les_jours():
    import random
    blocs = [[1, 2], [3], [4, 5, 6]]
    for graine in range(20):
        t = rj._tirage_blocs_jour(blocs, 7, random.Random(graine))
        assert len(t) == 7
    assert rj.blocs_par_jour(trades_test([1, 2, 3, 4], jours=2)) == [[1, 3], [2, 4]]


def test_tous_gagnants_donne_profit_factor_infini_sans_erreur():
    res = rj.reechantillonner(trades_test([1.0] * 30), "simple", tirages=50, graine=3)
    assert res["profit_factor"]["p50"] == math.inf and res["part_r_total_negatif_ou_nul"] == 0


# --- Seuils et garde-fous --------------------------------------------------------------------

def test_seuils_29_30_100():
    assert rj.niveau_confiance(29) == "insuffisant"
    assert rj.niveau_confiance(30) == "indicatif" and rj.niveau_confiance(99) == "indicatif"
    assert rj.niveau_confiance(100) == "standard"
    try:
        rj.reechantillonner(trades_test([1.0, -1.0] * 14 + [1.0]), "simple", tirages=10)   # N = 29
        raise AssertionError("N=29 aurait dû être refusé")
    except ValueError as e:
        assert "insuffisant" in str(e)
    rj.reechantillonner(trades_test([1.0, -1.0] * 15), "simple", tirages=10)               # N = 30 accepté


def test_ventilation_sous_le_seuil_non_evaluable():
    t = trades_test([1.0, -1.0] * 20)                             # 40 trades, 2 versions de 20
    v = rj.ventiler(t, "version")
    assert all(not g["evaluable"] and "stats" not in g for g in v.values())
    t2 = trades_test([1.0, -1.0, -1.0] * 24)                      # 72 trades, 2 versions de 36
    v2 = rj.ventiler(t2, "version")
    assert all(g["evaluable"] and g["stats"]["n"] == 36 for g in v2.values())


def test_rapport_refuse_de_simuler_sous_30():
    txt = rj.rapport_markdown(trades_test([1.0, -1.0] * 10), {"sans_r": [], "orphelines": [], "remplacees": [], "sans_sortie": []},
                              "test.json", "24/10/2026")
    assert "Échantillon insuffisant (N=20 < 30)" in txt and "| R total |" not in txt


def test_rapport_30_a_100_avertit_et_ventile():
    ex = {"sans_r": [sortie("2026-10-01T10:00:00", "USOIL", "TP_HIT", None)], "orphelines": [], "remplacees": [],
          "sans_sortie": [entree("2026-10-20T19:00:00", "SPX500")]}
    txt = rj.rapport_markdown(trades_test([1.5, -1, -1, 0.5, -1, 2] * 7, jours=5), ex, "test.json", "24/10/2026", tirages=200)
    assert "**indicatifs**" in txt and "Tirage par blocs d'un jour" in txt and "Tirage simple" in txt
    assert "Non évaluable : aucun groupe n'atteint 30 trades" in txt   # ventilation sous 30 : effectifs seuls
    assert "résultat indisponible" in txt and "SPX500" in txt         # exclusions listées à part
    assert "## Limites" in txt and "ne valide aucune stratégie" in txt
    assert "fiable" not in txt.lower()                              # jamais de formulation de fiabilité


# --- Aucun effet de bord ---------------------------------------------------------------------

def test_aucun_acces_neon_ni_ecriture():
    assert not hasattr(rj, "storage") and not hasattr(rj, "server") and not hasattr(rj, "psycopg")  # aucune base importée
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "journal.json")
        with open(src, "w", encoding="utf-8") as f:
            json.dump([entree("2026-10-01T10:00:00", "GOLD"), sortie("2026-10-01T12:30:00", "GOLD", "TP_HIT", 2.0)], f)
        avant = open(src, "rb").read()
        with contextlib.redirect_stdout(io.StringIO()):
            rj.main([src, "--tirages", "10", "--sortie", os.path.join(d, "rapport.md")])
        assert open(src, "rb").read() == avant                                # le journal source n'est pas modifié
        assert "Échantillon insuffisant" in open(os.path.join(d, "rapport.md"), encoding="utf-8").read()
        with open(os.path.join(d, "mauvais.json"), "w", encoding="utf-8") as f:
            json.dump({"pas": "une liste"}, f)
        try:
            rj.charger_journal(os.path.join(d, "mauvais.json"))
            raise AssertionError("un export qui n'est pas une liste aurait dû être refusé")
        except ValueError:
            pass


def main():
    tests = [(nom, f) for nom, f in sorted(globals().items()) if nom.startswith("test_") and callable(f)]
    for nom, f in tests:
        f()
        print(f"OK  {nom}")
    print(f"\n{len(tests)} tests réussis.")


if __name__ == "__main__":
    main()
