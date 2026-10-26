"""Test ciblé : alias de symbole « SOLU » -> « SOLUSD » dans le webhook. Fichiers d'état redirigés vers un dossier temporaire
(jamais le vrai journal ni les vraies positions), sans Neon, sans réseau."""
import json
import os
import sys
import tempfile

# Chaîne vide (et non pop) : server.py appelle load_dotenv() qui remettrait sinon la vraie DATABASE_URL du .env.
os.environ["DATABASE_URL"] = ""
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

import server  # noqa: E402
import storage  # noqa: E402

# Garde-fou : ce test écrit des positions et des lignes de journal, jamais dans la vraie base.
assert storage.BACKEND != "postgres", "BACKEND postgres : test interrompu avant toute écriture"

TMP = tempfile.mkdtemp(prefix="test_alias_symbole_")
storage.BASE_DIR = TMP
storage.JOURNAL_FILE = os.path.join(TMP, "journal_history.json")
storage.POSITIONS_FILE = os.path.join(TMP, "positions_state.json")

client = TestClient(server.app)


def vider_etat():
    server.open_positions.clear()
    server.journal_log.clear()
    server.market_state.clear()
    server.last_alerts.clear()


def alerte(symbol, status, **champs):
    base = {"symbol": symbol, "status": status, "direction": "SELL", "quality": "A", "rr": "3.41", "entry_price": "100.97",
            "sl_price": "101.41", "tp_price": "99.48", "current_price": "100.92", "trade_id": "SOLU-1792995600000",
            "version": "R6.3", "tf": "M5"}
    base.update(champs)
    return base


def main():
    vider_etat()

    # 1. Nouvelle entrée envoyée sous « SOLU » : tout est enregistré sous « SOLUSD ».
    assert client.post("/webhook", json=alerte("SOLU", "BSL SWEEP")).status_code == 200
    assert list(server.open_positions) == ["SOLUSD"], list(server.open_positions)
    assert server.open_positions["SOLUSD"]["symbol"] == "SOLUSD"
    assert server.market_state["SOLUSD"]["symbol"] == "SOLUSD" and "SOLU" not in server.market_state
    assert [r["symbol"] for r in server.journal_log] == ["SOLUSD"]
    assert "SOLUSD" in server.last_alerts and "SOLU" not in server.last_alerts

    # 2. Le nom déjà correct, ou en minuscules, ne change rien ; un autre actif n'est pas touché.
    assert client.post("/webhook", json=alerte("solusd", "PRICE_UPDATE", current_price="100.50")).status_code == 200
    assert server.open_positions["SOLUSD"]["last_price"] == "100.50"
    assert client.post("/webhook", json=alerte("GOLD", "BSL SWEEP", direction="BUY", trade_id="GOLD-1")).status_code == 200
    assert sorted(server.open_positions) == ["GOLD", "SOLUSD"]

    # 3. Trade ouvert AVANT l'alias (position stockée sous « SOLU ») : repris sous « SOLUSD » à la mise à jour suivante,
    #    puis clôturé normalement, sans position orpheline ni doublon d'entrée.
    vider_etat()
    server.open_positions["SOLU"] = server._new_position("SOLU", "BSL SWEEP", alerte("SOLU", "BSL SWEEP"), "2026-10-26T06:25:09")
    server.journal_log.append({"kind": "entry", "symbol": "SOLU", "trade_id": "SOLU-1792995600000", "status": "BSL SWEEP",
                               "direction": "SELL", "time": "2026-10-26T06:25:09"})
    assert client.post("/webhook", json=alerte("SOLU", "PRICE_UPDATE", current_price="100.60")).status_code == 200
    assert list(server.open_positions) == ["SOLUSD"], list(server.open_positions)
    pos = server.open_positions["SOLUSD"]
    assert pos["symbol"] == "SOLUSD" and pos["last_price"] == "100.60" and pos["trade_id"] == "SOLU-1792995600000"

    assert client.post("/webhook", json=alerte("SOLU", "TP_HIT", current_price="99.48")).status_code == 200
    assert server.open_positions == {}
    sorties = [r for r in server.journal_log if r.get("kind") == "exit"]
    assert len(sorties) == 1 and sorties[0]["symbol"] == "SOLUSD", sorties

    # 4. Une position « SOLUSD » déjà ouverte n'est jamais écrasée par une ancienne « SOLU ».
    vider_etat()
    server.open_positions["SOLUSD"] = server._new_position("SOLUSD", "BSL SWEEP", alerte("SOLUSD", "BSL SWEEP"), "2026-10-26T07:00:00")
    server.open_positions["SOLU"] = server._new_position("SOLU", "BSL SWEEP", alerte("SOLU", "BSL SWEEP"), "2026-10-26T06:00:00")
    server._reprendre_position_sous_alias("SOLU", "SOLUSD")
    assert sorted(server.open_positions) == ["SOLU", "SOLUSD"]
    assert server.open_positions["SOLUSD"]["opened_at"] == "2026-10-26T07:00:00"

    # 5. Rien n'a été écrit dans le dépôt : seuls les fichiers temporaires ont servi.
    assert os.path.dirname(storage.POSITIONS_FILE) == TMP
    print("OK : 5 contrôles d'alias de symbole SOLU -> SOLUSD")


if __name__ == "__main__":
    main()
