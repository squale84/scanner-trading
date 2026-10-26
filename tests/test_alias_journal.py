"""Test ciblé : les lignes de journal enregistrées avant l'alias (« SOLU ») sont relues sous « SOLUSD », en mémoire seulement.
Entrée « SOLU » + sortie « SOLUSD » d'un même trade doivent se rapprocher (plus de trade fantôme « en cours », plus de sortie orpheline).
Fichiers d'état redirigés vers un dossier temporaire ; interrompu avant toute écriture si le mode « postgres » est actif."""
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

assert storage.BACKEND != "postgres", "BACKEND postgres : test interrompu avant toute écriture"

TMP = tempfile.mkdtemp(prefix="test_alias_journal_")
storage.BASE_DIR = TMP
storage.JOURNAL_FILE = os.path.join(TMP, "journal_history.json")
storage.POSITIONS_FILE = os.path.join(TMP, "positions_state.json")

LIGNES = [
    {"kind": "entry", "symbol": "SOLU", "direction": "SELL", "status": "BSL SWEEP", "trade_id": "SOLU-1", "time": "2026-10-26T06:25:09"},
    {"kind": "exit", "symbol": "SOLUSD", "direction": "SELL", "status": "EXPIRED", "trade_id": "SOLU-1", "time": "2026-10-26T08:55:20", "r_multiple": -0.43},
    {"kind": "entry", "symbol": "SOLU", "direction": "BUY", "status": "SSL SWEEP", "trade_id": "SOLU-0", "time": "2026-10-21T06:50:12"},
    {"kind": "exit", "symbol": "SOLU", "direction": "BUY", "status": "TP_HIT", "trade_id": "SOLU-0", "time": "2026-10-21T08:55:07", "r_multiple": 3.27},
    {"kind": "entry", "symbol": "GOLD", "direction": "BUY", "status": "SSL SWEEP", "trade_id": "GOLD-1", "time": "2026-10-20T10:00:00"},
]


def main():
    with open(storage.JOURNAL_FILE, "w", encoding="utf-8") as f:
        json.dump(LIGNES, f)
    with open(storage.POSITIONS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

    # relecture complète de l'état comme au démarrage du serveur
    storage.STATUS["loaded"] = False
    server.journal_log.clear()
    server.open_positions.clear()
    assert server._load_initial_state() is True
    assert [r["symbol"] for r in server.journal_log] == ["SOLUSD", "SOLUSD", "SOLUSD", "SOLUSD", "GOLD"], [r["symbol"] for r in server.journal_log]

    # ce que reçoit la page : entrée et sortie du même trade portent le même symbole
    rows = TestClient(server.app).get("/api/journal").json()
    par_trade = {}
    for r in rows:
        par_trade.setdefault(r["trade_id"], set()).add(r["symbol"])
    assert all(len(s) == 1 for s in par_trade.values()), par_trade

    # la base n'est pas modifiée : le fichier source garde l'ancien nom
    with open(storage.JOURNAL_FILE, encoding="utf-8") as f:
        assert json.load(f)[0]["symbol"] == "SOLU"
    # aucun autre actif touché, aucune ligne perdue ou ajoutée
    assert len(rows) == len(LIGNES)
    assert os.path.dirname(storage.JOURNAL_FILE) == TMP
    print("OK : 4 contrôles d'alias dans le journal relu")


if __name__ == "__main__":
    main()
