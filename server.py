from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import json
import os
import sys
import asyncio
import time
import httpx
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List
from starlette.websockets import WebSocket, WebSocketDisconnect
from dotenv import load_dotenv

load_dotenv()  # en local : lit DATABASE_URL dans .env (sur Render, variable d'environnement du service)
import storage  # après load_dotenv : storage lit DATABASE_URL à l'import

# Evite un crash (UnicodeEncodeError) sur la console Windows (cp1252) quand on
# print() des emojis dans les logs du webhook.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

app = FastAPI(title="ICT Radar Engine Pro Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sert le dashboard index.html à la racine
# headers anti-cache : évite qu'un navigateur/proxy serve une version périmée après un déploiement
@app.get("/")
async def get_index():
    return FileResponse(
        os.path.join(os.path.dirname(__file__), "index.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )

# Route santé pour ping automatique anti-sommeil Render (UptimeRobot / Cron)
@app.get("/health")
async def health_check():
    return {"status": "alive", "connections": len(manager.active_connections)}

# --- Calendrier économique (source gratuite, sans clé API : flux FairEconomy/ForexFactory) ---
# Cache persisté (Postgres/Neon en production, voir storage.py) : la source refuse souvent les
# requêtes venant de Render, et un redéploiement efface disque et mémoire. Sans cache persistant,
# le calendrier restait vide après chaque déploiement (constaté le 23/09 : 502 en continu).
CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
CALENDAR_CACHE_TTL = 900  # 15 minutes : on évite de solliciter la source gratuite à chaque requête
CALENDAR_RETRY_AFTER_FAILURE = 900  # après un échec, pas de nouvel essai avant 15 min (évite d'aggraver le blocage)
_calendar_cache = {"data": None, "fetched_at": 0.0}
_calendar_last_failure = 0.0
_calendar_last_storage_check = 0.0

def _load_calendar_cache_from_disk():
    saved = storage.load_state("calendar_cache", "calendar_cache.json") or {}
    _calendar_cache["data"] = saved.get("data")
    _calendar_cache["fetched_at"] = saved.get("fetched_at", 0.0)

def _save_calendar_cache_to_disk():
    storage.save_state("calendar_cache", "calendar_cache.json", _calendar_cache)

storage.init()
_load_calendar_cache_from_disk()

def _calendar_response(stale):
    # En-têtes lus par le dashboard pour distinguer « source indisponible, données du JJ/MM HH:MM »
    # de « aucune annonce ».
    return JSONResponse(content=_calendar_cache["data"], headers={
        "X-Calendar-Fetched-At": str(int(_calendar_cache["fetched_at"] or 0)),
        "X-Calendar-Stale": "1" if stale else "0",
    })

@app.get("/api/calendar")
async def get_calendar():
    global _calendar_last_failure, _calendar_last_storage_check
    now = time.time()
    # La tâche GitHub (update_calendar.py) écrit le calendrier dans la base : on relit au plus une
    # fois par minute pour adopter sa version si elle est plus récente que celle en mémoire.
    if now - _calendar_last_storage_check > 60:
        _calendar_last_storage_check = now
        saved = storage.load_state("calendar_cache", "calendar_cache.json") or {}
        if saved.get("data") and saved.get("fetched_at", 0) > (_calendar_cache["fetched_at"] or 0):
            _calendar_cache["data"] = saved["data"]
            _calendar_cache["fetched_at"] = saved["fetched_at"]
    if _calendar_cache["data"] is not None and (now - _calendar_cache["fetched_at"]) < CALENDAR_CACHE_TTL:
        return _calendar_response(stale=False)
    if (now - _calendar_last_failure) < CALENDAR_RETRY_AFTER_FAILURE:
        if _calendar_cache["data"] is not None:
            return _calendar_response(stale=True)
        return JSONResponse(status_code=502, content={"error": "Calendrier indisponible"})
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }
        async with httpx.AsyncClient(timeout=20, headers=headers, follow_redirects=True) as client:
            resp = await client.get(CALENDAR_URL)
            resp.raise_for_status()
            data = resp.json()
            _calendar_cache["data"] = data
            _calendar_cache["fetched_at"] = now
            _save_calendar_cache_to_disk()
            return _calendar_response(stale=False)
    except Exception as e:
        print(f"⚠️ Erreur récupération calendrier économique : {e}")
        _calendar_last_failure = now
        if _calendar_cache["data"] is not None:
            # On sert le cache existant même périmé (mieux qu'une page vide), qu'il vienne
            # de cette session ou qu'il ait été rechargé depuis le disque au démarrage.
            return _calendar_response(stale=True)
        return JSONResponse(status_code=502, content={"error": "Calendrier indisponible"})

# --- Journal de trading et positions ouvertes (persistance : voir storage.py) ---
# La table HTML du journal est reconstruite depuis cet historique (/api/journal) au chargement
# et à chaque reconnexion, puis complétée en direct par les messages WebSocket {"type":"journal"}
# émis uniquement quand une ligne est réellement ajoutée ici (doublons déjà filtrés).
# Positions ouvertes par actif (niveaux figés à l'entrée + dernier prix reçu) : persistées pour
# qu'un redémarrage entre l'entrée et la sortie ne produise plus de sortie "orpheline" sans R.
JOURNAL_MAX_ENTRIES = 500
storage.init()
journal_log: List[dict] = storage.load_journal(JOURNAL_MAX_ENTRIES)
open_positions: dict = storage.load_positions()
print(f"💾 Persistance : {storage.BACKEND} — {len(journal_log)} ligne(s) de journal, {len(open_positions)} position(s) ouverte(s)")

def _save_positions_to_disk():
    storage.save_positions(open_positions)

def _session_label_now():
    ny_hour = datetime.now(ZoneInfo("America/New_York")).hour
    if 2 <= ny_hour < 5:
        return "🇬🇧 Londres"
    if 8 <= ny_hour < 12:
        return "🇺🇸 NY AM"
    return "⏱ Hors killzone"

def _parse_num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def _r_at_price(pos, price):
    """Résultat latent en multiples de R si on sortait à `price` (None si niveaux inexploitables)."""
    ep = _parse_num(pos.get("entry_price"))
    slp = _parse_num(pos.get("sl_price"))
    px = _parse_num(price)
    if ep is None or slp is None or px is None or ep == slp:
        return None
    risk = abs(ep - slp)
    return (px - ep) / risk if pos.get("direction") == "BUY" else (ep - px) / risk

# Miroir de computeRMultiple() côté JS (index.html) : la sortie ne contient que le prix
# courant, pas entry/sl/tp, donc on a besoin de la position mémorisée pour calculer le résultat.
def _compute_r_multiple(entry, exit_data):
    if not entry:
        return None
    status = exit_data.get("status")
    if status == "TP_HIT":
        return _parse_num(entry.get("rr")) or 2
    if status == "SL_HIT":
        return -1
    if status == "EXPIRED":
        return _r_at_price(entry, exit_data.get("current_price"))
    return None

# Prix de sortie retenu pour le R : le niveau touché pour TP/SL (le Radar renvoie la clôture de
# la bougie, qui a pu dépasser le niveau), la clôture pour EXPIRED.
def _exit_price(entry, status, exit_data):
    if entry and status == "TP_HIT":
        return entry.get("tp_price")
    if entry and status == "SL_HIT":
        return entry.get("sl_price")
    return exit_data.get("current_price")

def _levels_valid(data):
    return all(_parse_num(data.get(k)) not in (None, 0) for k in ("entry_price", "sl_price", "tp_price"))

def _same_levels(pos, data):
    # Depuis le R6, chaque trade a un identifiant : c'est lui qui fait foi pour repérer un doublon.
    if pos.get("trade_id") and data.get("trade_id"):
        return pos.get("trade_id") == data.get("trade_id")
    return pos.get("direction") == data.get("direction") and all(
        _parse_num(pos.get(k)) == _parse_num(data.get(k)) for k in ("entry_price", "sl_price", "tp_price")
    )

def _clean_targets(data):
    """Cibles de liquidité envoyées par le Radar R6 : [{"p": prix, "r": R, "t": type}, ...]
    (liste vide pour les alertes R5, qui n'en envoient pas)."""
    out = []
    targets = data.get("targets")
    if isinstance(targets, list):
        for t in targets:
            if isinstance(t, dict) and _parse_num(t.get("p")) is not None and _parse_num(t.get("r")) is not None:
                out.append({"p": t.get("p"), "r": t.get("r"), "t": str(t.get("t") or "")[:40]})
    return out

def _targets_reached(pos, status):
    """Nombre de cibles atteintes pendant le trade (toutes si le TP final est touché)."""
    targets = (pos or {}).get("targets") or []
    if status == "TP_HIT":
        return len(targets)
    best = (pos or {}).get("best_r") or 0.0
    return sum(1 for t in targets if (_parse_num(t.get("r")) or 0) <= best + 1e-9)

def _new_position(symbol, status, data, now, recovered=False):
    return {
        "symbol": symbol,
        "direction": data.get("direction"),
        "status": status,
        "quality": data.get("quality", "--"),
        "grade": data.get("grade", "--"),
        "rr": data.get("rr", "0.0"),
        "entry_price": data.get("entry_price"),
        "sl_price": data.get("sl_price"),
        "tp_price": data.get("tp_price"),
        "last_price": data.get("current_price") or data.get("entry_price"),
        "best_r": 0.0,
        "session": _session_label_now(),
        "opened_at": None if recovered else now,
        "last_update": now,
        "recovered": recovered,
        "version": data.get("version"),
        "trade_id": data.get("trade_id"),
        "targets": _clean_targets(data),
    }

def _append_journal(row):
    journal_log.append(row)
    del journal_log[: max(0, len(journal_log) - JOURNAL_MAX_ENTRIES)]
    storage.append_journal_row(row, journal_log)

def _record_journal_event(symbol, status, direction, data):
    """Met à jour les positions ouvertes et le journal. Renvoie la liste des lignes de journal
    ajoutées (vide si doublon ou simple mise à jour de prix), pour diffusion WebSocket."""
    if status in ("STANDBY", "INFO"):
        return []
    now = datetime.utcnow().isoformat()

    if status == "PRICE_UPDATE":
        pos = open_positions.get(symbol)
        if pos is None:
            # Entrée manquée (serveur redémarré, alerte créée en cours de position…) : le payload
            # R5 contient les niveaux, on reconstruit la position sans inventer de ligne d'entrée.
            if direction not in ("BUY", "SELL") or not _levels_valid(data):
                return []
            pos = _new_position(symbol, "--", data, now, recovered=True)
            open_positions[symbol] = pos
        pos["last_price"] = data.get("current_price", pos.get("last_price"))
        pos["last_update"] = now
        r_now = _r_at_price(pos, pos["last_price"])
        if r_now is not None:
            pos["best_r"] = max(pos.get("best_r") or 0.0, r_now)
        _save_positions_to_disk()
        return []

    added = []
    if direction in ("BUY", "SELL"):
        pos = open_positions.get(symbol)
        if pos is not None and _same_levels(pos, data):
            return []  # même entrée renvoyée deux fois (retry webhook) : pas de doublon
        if pos is not None:
            # Nouvelle entrée alors que la précédente n'a jamais reçu de sortie : on la clôt
            # explicitement sans résultat plutôt que de l'écraser silencieusement.
            row = _exit_row(symbol, "REPLACED", pos, {"current_price": pos.get("last_price")}, now)
            _append_journal(row)
            added.append(row)
        open_positions[symbol] = _new_position(symbol, status, data, now)
        _save_positions_to_disk()
        row = {
            "kind": "entry",
            "time": now,
            "symbol": symbol,
            "direction": direction,
            "status": status,
            "session": open_positions[symbol]["session"],
            "quality": data.get("quality", "--"),
            "grade": data.get("grade", "--"),
            "rr": data.get("rr", "0.0"),
            "entry_price": data.get("entry_price", "--"),
            "sl_price": data.get("sl_price"),
            "tp_price": data.get("tp_price"),
            "version": data.get("version"),
            "trade_id": data.get("trade_id"),
            "targets": open_positions[symbol]["targets"],
        }
        _append_journal(row)
        added.append(row)
    elif status in ("TP_HIT", "SL_HIT", "EXPIRED"):
        pos = open_positions.pop(symbol, None)
        if pos is None:
            last = next((r for r in reversed(journal_log) if r.get("symbol") == symbol), None)
            if last is not None and last.get("kind") == "exit":
                return []  # sortie déjà enregistrée, aucune position ouverte : doublon
        else:
            _save_positions_to_disk()
        row = _exit_row(symbol, status, pos, data, now)
        _append_journal(row)
        added.append(row)
    return added

def _exit_row(symbol, status, pos, data, now):
    return {
        "kind": "exit",
        "time": now,
        "symbol": symbol,
        "direction": pos.get("direction") if pos else data.get("direction"),
        "status": status,
        "entry_status": pos.get("status") if pos else None,
        "session_at_entry": pos.get("session") if pos else None,
        "quality": pos.get("quality") if pos else "--",
        "grade": pos.get("grade") if pos else "--",
        "rr": pos.get("rr") if pos else "0.0",
        "entry_price": pos.get("entry_price") if pos else "--",
        "sl_price": pos.get("sl_price") if pos else None,
        "tp_price": pos.get("tp_price") if pos else None,
        "exit_price": _exit_price(pos, status, data),
        "last_price": data.get("current_price"),
        "best_r": pos.get("best_r") if pos else None,
        "r_multiple": _compute_r_multiple(pos, data) if status != "REPLACED" else None,
        "version": (pos.get("version") if pos else None) or data.get("version"),
        "trade_id": (pos.get("trade_id") if pos else None) or data.get("trade_id"),
        "targets": pos.get("targets") if pos else [],
        "targets_reached": _targets_reached(pos, status) if pos else None,
    }

@app.get("/api/journal")
async def get_journal():
    return journal_log

@app.get("/api/positions")
async def get_positions():
    return open_positions

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

# Après un redémarrage, market_state (mémoire) est vide : on le réamorce depuis les positions
# persistées pour que les cartes du dashboard retrouvent leur position active à la reconnexion.
market_state = {
    sym: {**{k: pos.get(k) for k in ("symbol", "direction", "quality", "grade", "rr", "entry_price", "sl_price", "tp_price")},
          "status": "PRICE_UPDATE", "current_price": pos.get("last_price")}
    for sym, pos in open_positions.items()
}

def _positions_message():
    return json.dumps({"type": "positions", "positions": open_positions})

# Dernière alerte reçue par actif (y compris PRICE_UPDATE), persistée : permet de voir sur chaque
# carte si l'alerte TradingView de cet actif envoie bien quelque chose, et depuis quand.
last_alerts: dict = storage.load_state("last_alerts", "last_alerts.json") or {}

def _last_alerts_message():
    return json.dumps({"type": "last_alerts", "last_alerts": last_alerts})

class ResetRequest(BaseModel):
    symbol: str

@app.post("/api/reset")
async def reset_card(data: ResetRequest):
    sym = data.symbol.upper()
    reset_data = {
        "symbol": sym,
        "status": "STANDBY",
        "direction": "NONE",
        "entry_price": "--",
        "sl_price": "--",
        "tp_price": "--",
        "current_price": market_state.get(sym, {}).get("current_price", "--"),
        "progress": 0
    }
    market_state[sym] = reset_data
    # Reset manuel = l'utilisateur abandonne le suivi : la position disparaît aussi de la jauge.
    if open_positions.pop(sym, None) is not None:
        _save_positions_to_disk()
    await manager.broadcast(json.dumps(reset_data))
    await manager.broadcast(_positions_message())
    print(f"🔄 [{sym}] Carte remise en STANDBY.")
    return {"status": "success", "symbol": sym}

@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        try:
            body = await request.body()
            body_str = body.decode("utf-8").strip()
            data = json.loads(body_str)
        except Exception as e:
            print(f"❌ Erreur lecture payload webhook : {e}")
            return JSONResponse(status_code=400, content={"error": "JSON invalide"})

    symbol = data.get("symbol", "UNKNOWN").upper()
    status = data.get("status", "INFO")
    direction = data.get("direction", "NONE")

    print(f"⚡ [{symbol}] {status} | Dir: {direction} | Entree: {data.get('entry_price')} | SL: {data.get('sl_price')} | TP: {data.get('tp_price')}")

    added_rows = _record_journal_event(symbol, status, direction, data)
    last_alerts[symbol] = {"time": datetime.utcnow().isoformat(), "status": status}
    storage.save_state("last_alerts", "last_alerts.json", last_alerts)
    market_state[symbol] = data
    await manager.broadcast(json.dumps(data))
    # Le journal et les jauges du front sont pilotés par l'état serveur (source unique) :
    # mêmes données en direct qu'après un F5, et les doublons filtrés ici n'apparaissent nulle part.
    for row in added_rows:
        await manager.broadcast(json.dumps({"type": "journal", "row": row}))
    await manager.broadcast(_positions_message())
    await manager.broadcast(_last_alerts_message())
    return {"status": "success", "symbol": symbol}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Envoi initial de l'état actuel de tous les actifs connus
        for sym, item in market_state.items():
            await websocket.send_text(json.dumps(item))
        await websocket.send_text(_positions_message())
        await websocket.send_text(_last_alerts_message())
        # Signal de fin de synchro : le front sait qu'il peut réactiver son (audio/popups/log)
        await websocket.send_text(json.dumps({"type": "sync_complete"}))

        while True:
            # Écoute sans bloquer avec keep-alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except (WebSocketDisconnect, Exception):
        manager.disconnect(websocket)