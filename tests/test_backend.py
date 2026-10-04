"""Tests ciblés du backend (webhook, calcul du R, admin). Aucune écriture réelle : voir fake_storage."""
import os
import sys
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tests.fake_storage as fake_storage  # noqa: E402

FAKE = fake_storage.install()
import server  # noqa: E402  (importe server avec le faux stockage)
from fastapi.testclient import TestClient  # noqa: E402


def entry(**over):
    data = {"symbol": "GOLD", "status": "SSL SWEEP", "direction": "BUY", "quality": "A+", "grade": "**",
            "entry_price": "100", "sl_price": "99", "tp_price": "103", "current_price": "100",
            "rr": "", "version": "R6.1", "trade_id": "T1", "targets": []}
    data.update(over)
    return data


class BackendTestCase(unittest.TestCase):
    def setUp(self):
        FAKE.JOURNAL.clear()
        FAKE.STATE.clear()
        FAKE.fail_writes = False
        server.journal_log.clear()
        server.open_positions.clear()
        server.market_state.clear()
        server.last_alerts.clear()
        server.card_resets.clear()
        server._admin_failures.clear()
        self.client = TestClient(server.app)

    def post(self, payload, headers=None):
        return self.client.post("/webhook", json=payload, headers=headers or {})

    def exits(self):
        return [r for r in server.journal_log if r.get("kind") == "exit"]


class RMultipleTests(BackendTestCase):
    def test_tp_sans_rr_se_calcule_depuis_les_niveaux(self):
        # TP à +3R (103 pour entrée 100 / SL 99) mais « rr » absent : le R doit venir des niveaux, pas d'un 2 inventé.
        self.post(entry(rr=""))
        self.post({"symbol": "GOLD", "status": "TP_HIT", "direction": "NONE", "current_price": "103"})
        self.assertEqual(self.exits()[-1]["r_multiple"], 3.0)

    def test_sl_touche_donne_moins_un_R(self):
        self.post(entry())
        self.post({"symbol": "GOLD", "status": "SL_HIT", "direction": "NONE", "current_price": "99"})
        self.assertEqual(self.exits()[-1]["r_multiple"], -1)

    def test_expired_donne_le_R_au_prix_de_cloture(self):
        self.post(entry())
        self.post({"symbol": "GOLD", "status": "EXPIRED", "direction": "NONE", "current_price": "100.5"})
        self.assertAlmostEqual(self.exits()[-1]["r_multiple"], 0.5)

    def test_niveaux_inexploitables_donnent_resultat_indisponible(self):
        # Entrée sans prix exploitable : aucun R ne doit être fabriqué (règle « résultat indisponible »).
        self.post(entry(entry_price="--", sl_price="--", tp_price="--"))
        self.post({"symbol": "GOLD", "status": "TP_HIT", "direction": "NONE", "current_price": "103"})
        self.assertIsNone(self.exits()[-1]["r_multiple"])


class JournalTests(BackendTestCase):
    def test_retry_webhook_ne_cree_pas_de_doublon(self):
        self.post(entry())
        self.post(entry())
        self.assertEqual(len([r for r in server.journal_log if r.get("kind") == "entry"]), 1)

    def test_price_update_ne_cree_aucune_ligne(self):
        self.post(entry())
        before = len(server.journal_log)
        self.post({"symbol": "GOLD", "status": "PRICE_UPDATE", "direction": "BUY", "current_price": "101"})
        self.assertEqual(len(server.journal_log), before)
        self.assertEqual(server.open_positions["GOLD"]["last_price"], "101")

    def test_persistance_en_panne_repond_500_sans_faux_succes(self):
        FAKE.fail_writes = True
        r = self.post(entry())
        self.assertEqual(r.status_code, 500)
        self.assertFalse(r.json()["persisted"])


class AdminTests(BackendTestCase):
    def setUp(self):
        super().setUp()
        self.env = mock.patch.dict(os.environ, {"RESET_SECRET": "code-de-test-123"})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def login(self, code, ip="10.0.0.1"):
        return self.client.post("/api/admin/login", json={"code": code}, headers={"X-Forwarded-For": ip})

    def test_mauvais_code_refuse(self):
        self.assertEqual(self.login("faux").status_code, 401)

    def test_cinq_echecs_bloquent_puis_429(self):
        for _ in range(5):
            self.login("faux")
        self.assertEqual(self.login("code-de-test-123").status_code, 429)

    def test_en_tete_x_forwarded_for_falsifie_ne_contourne_pas_le_verrou(self):
        # Le client peut écrire ce qu'il veut en TÊTE de X-Forwarded-For ; seule l'adresse ajoutée
        # par le proxy (en fin de liste) est fiable. Changer la tête ne doit pas réinitialiser le compteur.
        for i in range(5):
            self.login("faux", ip=f"1.1.1.{i}, 10.0.0.9")
        r = self.login("code-de-test-123", ip="9.9.9.9, 10.0.0.9")
        self.assertEqual(r.status_code, 429)

    def test_bon_code_pose_un_cookie_durci(self):
        r = self.login("code-de-test-123")
        self.assertEqual(r.status_code, 200)
        cookie = r.headers["set-cookie"].lower()
        for attr in ("httponly", "secure", "samesite=strict"):
            self.assertIn(attr, cookie)

    def test_reset_sans_session_refuse(self):
        r = self.client.post("/api/reset", json={"symbol": "GOLD"})
        self.assertEqual(r.status_code, 401)


if __name__ == "__main__":
    unittest.main()
