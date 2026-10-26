"""Test ciblé : notifications Telegram du serveur (entrée, objectifs TP1-TP3 avec conseil de stop suiveur, sortie).
Aucun envoi réel : l'envoi est remplacé par une doublure ; le jeton utilisé est factice. Fichiers d'état redirigés vers un dossier
temporaire ; interrompu avant toute écriture si le mode « postgres » est actif."""
import asyncio
import json
import os
import sys
import tempfile

# Chaîne vide (et non pop) : server.py appelle load_dotenv() qui remettrait sinon la vraie DATABASE_URL du .env.
os.environ["DATABASE_URL"] = ""
for cle in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
    os.environ.pop(cle, None)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import server  # noqa: E402
import storage  # noqa: E402

assert storage.BACKEND != "postgres", "BACKEND postgres : test interrompu avant toute écriture"

TMP = tempfile.mkdtemp(prefix="test_telegram_")
storage.BASE_DIR = TMP
storage.JOURNAL_FILE = os.path.join(TMP, "journal_history.json")
storage.POSITIONS_FILE = os.path.join(TMP, "positions_state.json")

client = TestClient(server.app)
JETON_FACTICE = "123456:JETON-FACTICE-POUR-LE-TEST"


def vider_etat():
    for d in (server.open_positions, server.market_state, server.last_alerts):
        d.clear()
    server.journal_log.clear()
    server._notifs_en_attente.clear()


def trade(tid, **champs):
    base = {"symbol": "GOLD", "direction": "BUY", "quality": "A", "rr": "3", "entry_price": "4300", "sl_price": "4290", "tp_price": "4330",
            "trade_id": tid, "version": "R6.3", "tf": "M5",
            "targets": [{"p": "4310", "r": "1", "t": "x"}, {"p": "4320", "r": "2", "t": "x"}, {"p": "4330", "r": "3", "t": "x"}]}
    base.update(champs)
    return base


def main():
    envoyes = []
    server._lancer_notifications = lambda textes: envoyes.extend(textes)    # doublure : on capte, on n'envoie rien

    # 1. Pas de réglage : fonction désactivée, aucun appel réseau.
    assert server._telegram_config() is None
    assert asyncio.run(server._telegram_envoyer("x")) == (False, "non_configure")
    assert client.post("/api/notifications/test").json() == {"ok": False, "raison": "non_configure"}

    os.environ["TELEGRAM_BOT_TOKEN"] = JETON_FACTICE
    os.environ["TELEGRAM_CHAT_ID"] = "42"
    vider_etat()

    # 2. Entrée : un message ; la même entrée renvoyée (retry du webhook) n'en fait pas un second.
    client.post("/webhook", json={**trade("T1"), "status": "SSL SWEEP", "current_price": "4300"})
    assert len(envoyes) == 1 and "ACHAT GOLD" in envoyes[0] and "Entrée 4300" in envoyes[0] and "Stop 4290" in envoyes[0], envoyes
    client.post("/webhook", json={**trade("T1"), "status": "SSL SWEEP", "current_price": "4300"})
    assert len(envoyes) == 1, envoyes

    # 3. Mises à jour de prix : rien sous TP1 ; un message au franchissement de TP1 ; rien si répété.
    client.post("/webhook", json={**trade("T1"), "status": "PRICE_UPDATE", "current_price": "4305"})
    assert len(envoyes) == 1
    client.post("/webhook", json={**trade("T1"), "status": "PRICE_UPDATE", "current_price": "4312"})
    assert len(envoyes) == 2 and "TP1 atteint" in envoyes[1] and "à l'entrée (4300)" in envoyes[1], envoyes[1]
    client.post("/webhook", json={**trade("T1"), "status": "PRICE_UPDATE", "current_price": "4313"})
    assert len(envoyes) == 2

    # 4. TP2 : conseil « stop sur le TP1 » ; le dernier objectif (TP final) ne donne pas de message de progression.
    client.post("/webhook", json={**trade("T1"), "status": "PRICE_UPDATE", "current_price": "4322"})
    assert len(envoyes) == 3 and "TP2 atteint" in envoyes[2] and "sur le TP1 (4310)" in envoyes[2], envoyes[2]
    client.post("/webhook", json={**trade("T1"), "status": "PRICE_UPDATE", "current_price": "4329"})
    assert len(envoyes) == 3

    # 5. La mémoire est enregistrée avec la position (pas de doublon après un redémarrage).
    assert server.open_positions["GOLD"]["tp_notifie"] == 2
    with open(storage.POSITIONS_FILE, encoding="utf-8") as f:
        assert json.load(f)["GOLD"]["tp_notifie"] == 2

    # 6. Sortie : un message avec le résultat ; la même sortie renvoyée n'en fait pas un second.
    client.post("/webhook", json={**trade("T1"), "status": "TP_HIT", "current_price": "4330"})
    assert len(envoyes) == 4 and "TP touché" in envoyes[3] and "+3,00 R" in envoyes[3], envoyes[3]
    client.post("/webhook", json={**trade("T1"), "status": "TP_HIT", "current_price": "4330"})
    assert len(envoyes) == 4

    # 7. Plusieurs objectifs franchis d'un coup : un seul message, pour le plus haut (4 objectifs, TP3 intermédiaire).
    vider_etat(); envoyes.clear()
    quatre = [{"p": "4310", "r": "1", "t": "x"}, {"p": "4320", "r": "2", "t": "x"}, {"p": "4330", "r": "3", "t": "x"}, {"p": "4340", "r": "4", "t": "x"}]
    client.post("/webhook", json={**trade("T2", targets=quatre, tp_price="4340"), "status": "SSL SWEEP", "current_price": "4300"})
    client.post("/webhook", json={**trade("T2", targets=quatre, tp_price="4340"), "status": "PRICE_UPDATE", "current_price": "4333"})
    objectifs = [t for t in envoyes if "atteint" in t]
    assert len(objectifs) == 1 and "TP3 atteint" in objectifs[0] and "sur le TP2 (4320)" in objectifs[0], envoyes

    # 8. Position reprise (aucune entrée vue) déjà au-delà de TP1 : notée sans message ; le franchissement suivant est notifié.
    vider_etat(); envoyes.clear()
    client.post("/webhook", json={**trade("T3"), "status": "PRICE_UPDATE", "current_price": "4312"})
    assert envoyes == [], envoyes
    client.post("/webhook", json={**trade("T3"), "status": "PRICE_UPDATE", "current_price": "4322"})
    assert len(envoyes) == 1 and "TP2 atteint" in envoyes[0], envoyes

    # 9. Un événement de marché ne donne aucun message.
    envoyes.clear()
    client.post("/webhook", json={"symbol": "GOLD", "status": "EVENT", "direction": "NONE", "event": "LONDON_HIGH_SWEPT", "level": "4310",
                                  "current_price": "4309", "bar_time": 1729000000000, "version": "R6.3"})
    assert envoyes == []

    # 10. Envoi réel remplacé par un faux client : le jeton ne sort jamais, même quand l'erreur contient l'adresse.
    class FauxClient:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def post(self, url, json=None):
            raise httpx.ConnectError(f"échec vers {url}")
    vrai = httpx.AsyncClient
    httpx.AsyncClient = FauxClient
    try:
        ok, motif = asyncio.run(server._telegram_envoyer("bonjour"))
    finally:
        httpx.AsyncClient = vrai
    assert ok is False and motif == "ConnectError" and JETON_FACTICE not in motif

    # 11. Un envoi qui échoue ne lève rien (le webhook n'est jamais bloqué).
    async def sender_en_echec(texte):
        return False, "http_401"
    server._telegram_envoyer = sender_en_echec
    asyncio.run(server._envoyer_notifications(["a", "b"]))

    # 12. Le message de test reste fixe et limité à un toutes les 30 s.
    async def sender_ok(texte):
        sender_ok.recus.append(texte)
        return True, "ok"
    sender_ok.recus = []
    server._telegram_envoyer = sender_ok
    server._dernier_test_telegram = 0.0
    r1 = client.post("/api/notifications/test")
    r2 = client.post("/api/notifications/test")
    assert r1.json() == {"ok": True, "raison": "ok"} and r2.status_code == 429 and len(sender_ok.recus) == 1

    assert os.path.dirname(storage.POSITIONS_FILE) == TMP
    for cle in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        os.environ.pop(cle, None)
    print("OK : 12 contrôles des notifications Telegram")


if __name__ == "__main__":
    main()
