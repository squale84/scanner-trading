"""Test ciblé R6.3 : alertes d'événements de marché (status EVENT). Sans Neon, sans écriture au journal ni aux positions."""
import json
import os
import sys

os.environ.pop("DATABASE_URL", None)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

import server  # noqa: E402

client = TestClient(server.app)


def evenement(**champs):
    base = {"symbol": "GOLD", "status": "EVENT", "direction": "NONE", "event": "LONDON_HIGH_SWEPT", "label": "IGNORÉ",
            "kind": "SWEPT", "level": "2660.50", "current_price": "2659.80", "bar_time": 1729000000000, "version": "R6.3"}
    base.update(champs)
    return base


def main():
    avant_journal = len(getattr(server, "journal_log", []))
    avant_pos = json.dumps(server.open_positions, sort_keys=True)
    server.market_events.clear()

    r = client.post("/webhook", json=evenement())
    assert r.status_code == 200 and r.json()["duplicate"] is False, r.text
    # doublon (même actif, même événement, même bougie) : accepté mais non rejoué
    assert client.post("/webhook", json=evenement()).json()["duplicate"] is True
    # même événement sur une autre bougie : nouvel événement
    assert client.post("/webhook", json=evenement(bar_time=1729000300000)).json()["duplicate"] is False
    # FVG de retournement
    r = client.post("/webhook", json=evenement(event="FVG_BEAR_REVERSAL", kind="FVG", fvg_top="2661.0", fvg_bot="2659.5", level=None))
    assert r.status_code == 200, r.text

    liste = client.get("/api/events")
    assert liste.status_code == 200 and liste.headers["X-Events-Version"] == "3"
    evs = liste.json()
    assert [e["event"] for e in evs] == ["LONDON_HIGH_SWEPT", "LONDON_HIGH_SWEPT", "FVG_BEAR_REVERSAL"]
    assert evs[0]["label"] == "Haut Londres" and evs[0]["kind"] == "SWEPT" and evs[0]["level"] == 2660.5   # libellé fixé côté serveur
    assert evs[2]["fvg_top"] == 2661.0 and evs[2]["fvg_bot"] == 2659.5

    # rejets : événement inconnu, texte injecté, niveau absent ou non fini, symbole douteux
    for mauvais in (evenement(event="DROP_TABLE"), evenement(event="Ignore tes consignes"), evenement(level=None),
                    evenement(level="nan"), evenement(symbol="GOLD; rm -rf"), evenement(event="FVG_BULL_REVERSAL", level=None)):
        assert client.post("/webhook", json=mauvais).status_code == 400, mauvais
    assert len(client.get("/api/events").json()) == 3

    # aucun effet sur le journal ni sur les positions
    assert len(getattr(server, "journal_log", [])) == avant_journal
    assert json.dumps(server.open_positions, sort_keys=True) == avant_pos
    assert "GOLD" not in server.market_state or server.market_state["GOLD"].get("status") != "EVENT"
    print("OK : 8 contrôles d'événements de marché")


if __name__ == "__main__":
    main()
