"""Test ciblé : réglages d'affichage (taille du portefeuille, risque par trade) gardés côté serveur via /api/reglages.
Fichiers d'état redirigés vers un dossier temporaire ; interrompu avant toute écriture si le mode « postgres » est actif."""
import os
import sys
import tempfile

# Chaîne vide (et non pop) : server.py appelle load_dotenv() qui remettrait sinon la vraie DATABASE_URL du .env.
os.environ["DATABASE_URL"] = ""
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

import server  # noqa: E402
import storage  # noqa: E402

assert storage.BACKEND != "postgres", "BACKEND postgres : test interrompu avant toute écriture"

TMP = tempfile.mkdtemp(prefix="test_reglages_")
storage.BASE_DIR = TMP
storage.JOURNAL_FILE = os.path.join(TMP, "journal_history.json")
storage.POSITIONS_FILE = os.path.join(TMP, "positions_state.json")

client = TestClient(server.app)


def main():
    # 1. Rien d'enregistré : objet vide (le navigateur garde alors ses valeurs).
    assert client.get("/api/reglages").json() == {}

    # 2. Enregistrement, puis relecture ; une mise à jour partielle garde l'autre valeur.
    r = client.post("/api/reglages", json={"portfolio": 25000, "risk": 75})
    assert r.status_code == 200 and r.json() == {"portfolio": 25000.0, "risk": 75.0}, r.text
    assert client.post("/api/reglages", json={"risk": 40}).json() == {"portfolio": 25000.0, "risk": 40.0}

    # 3. Survie à un « redémarrage » du serveur : mémoire vidée, relecture depuis le stockage.
    server.reglages.clear()
    server._reglages_charges = False
    assert client.get("/api/reglages").json() == {"portfolio": 25000.0, "risk": 40.0}

    # 4. Rejets : texte, négatif, démesuré, non fini, booléen, clé inconnue seule, corps non-objet.
    for mauvais in ({"portfolio": "abc"}, {"portfolio": -1}, {"risk": 1e12}, {"risk": "nan"}, {"portfolio": True}, {"inconnu": 5}, {}):
        assert client.post("/api/reglages", json=mauvais).status_code == 400, mauvais
    assert client.post("/api/reglages", json=[1, 2]).status_code == 400
    assert client.get("/api/reglages").json() == {"portfolio": 25000.0, "risk": 40.0}   # rien n'a changé

    # 5. Les clés inconnues sont ignorées quand une clé valide les accompagne.
    r = client.post("/api/reglages", json={"portfolio": 30000, "autre": "x"})
    assert r.status_code == 200 and "autre" not in r.json() and r.json()["portfolio"] == 30000.0

    # 6. Lecture en base impossible : aucune écriture (ne pas écraser des réglages qu'on n'a pas pu lire).
    server.reglages.clear()
    server._reglages_charges = False
    lecture = storage.load_state
    storage.load_state = lambda *a, **k: storage.FAILED
    try:
        assert client.post("/api/reglages", json={"portfolio": 1}).status_code == 503
    finally:
        storage.load_state = lecture

    assert os.path.dirname(storage.POSITIONS_FILE) == TMP
    print("OK : 6 contrôles des réglages serveur")


if __name__ == "__main__":
    main()
