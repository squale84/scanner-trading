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
# Cache persisté sur disque (en plus de la mémoire) : un redéploiement Render (déclenché par
# n'importe quel push, même sans rapport) efface la mémoire du process. Sans persistance sur
# disque, un redémarrage pile au moment où la source bloque/rate-limite Render laisse le
# calendrier vide côté site, sans aucun secours.
CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
CALENDAR_CACHE_TTL = 900  # 15 minutes : on évite de solliciter la source gratuite à chaque requête
CALENDAR_CACHE_FILE = os.path.join(os.path.dirname(__file__), "calendar_cache.json")
_calendar_cache = {"data": None, "fetched_at": 0.0}

def _load_calendar_cache_from_disk():
    try:
        with open(CALENDAR_CACHE_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        _calendar_cache["data"] = saved.get("data")
        _calendar_cache["fetched_at"] = saved.get("fetched_at", 0.0)
    except Exception:
        pass  # pas de cache disque disponible (premier démarrage) — normal, pas une erreur

def _save_calendar_cache_to_disk():
    try:
        with open(CALENDAR_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_calendar_cache, f)
    except Exception as e:
        print(f"⚠️ Impossible d'écrire le cache calendrier sur disque : {e}")

_load_calendar_cache_from_disk()

@app.get("/api/calendar")
async def get_calendar():
    now = time.time()
    if _calendar_cache["data"] is not None and (now - _calendar_cache["fetched_at"]) < CALENDAR_CACHE_TTL:
        return _calendar_cache["data"]
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
            return data
    except Exception as e:
        print(f"⚠️ Erreur récupération calendrier économique : {e}")
        if _calendar_cache["data"] is not None:
            # On sert le cache existant même périmé (mieux qu'une page vide), qu'il vienne
            # de cette session ou qu'il ait été rechargé depuis le disque au démarrage.
            return _calendar_cache["data"]
        return JSONResponse(status_code=502, content={"error": "Calendrier indisponible"})

# --- Journal de trading (historique persistant, survit au F5 ET aux redéploiements Render) ---
# La table HTML du journal est reconstruite au chargement de la page à partir de cet historique
# serveur (voir /api/journal), en plus des mises à jour temps réel par WebSocket. Les deux
# chemins ne se recoupent jamais : l'hydratation REST n'a lieu qu'une fois au chargement, et le
# rejeu WebSocket à la reconnexion est déjà "silencieux" côté front (ne touche pas le journal) —
# donc aucun doublon possible.
JOURNAL_FILE = os.path.join(os.path.dirname(__file__), "journal_history.json")
JOURNAL_MAX_ENTRIES = 500
journal_log: List[dict] = []
last_entry_by_symbol = {}

def _load_journal_from_disk():
    global journal_log
    try:
        with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
            journal_log = json.load(f)
    except Exception:
        journal_log = []  # pas d'historique disponible (premier démarrage) — normal, pas une erreur

def _save_journal_to_disk():
    try:
        with open(JOURNAL_FILE, "w", encoding="utf-8") as f:
            json.dump(journal_log, f)
    except Exception as e:
        print(f"⚠️ Impossible d'écrire le journal sur disque : {e}")

_load_journal_from_disk()

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

# Miroir exact de computeRMultiple() côté JS (index.html) : la sortie ne contient que le prix
# courant, pas entry/sl/tp, donc on a besoin de l'entrée mémorisée pour calculer le résultat.
def _compute_r_multiple(entry, exit_data):
    if not entry:
        return None
    status = exit_data.get("status")
    if status == "TP_HIT":
        return _parse_num(entry.get("rr")) or 2
    if status == "SL_HIT":
        return -1
    if status == "EXPIRED":
        ep = _parse_num(entry.get("entry_price"))
        slp = _parse_num(entry.get("sl_price"))
        xp = _parse_num(exit_data.get("current_price"))
        if ep is None or slp is None or xp is None:
            return None
        risk = abs(ep - slp)
        if risk == 0:
            return None
        return (xp - ep) / risk if entry.get("direction") == "BUY" else (ep - xp) / risk
    return None

def _record_journal_event(symbol, status, direction, data):
    if status in ("PRICE_UPDATE", "STANDBY", "INFO"):
        return
    if direction in ("BUY", "SELL"):
        entry_record = dict(data)
        entry_record["session"] = _session_label_now()
        last_entry_by_symbol[symbol] = entry_record
        journal_log.append({
            "kind": "entry",
            "time": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "direction": direction,
            "status": status,
            "session": entry_record["session"],
            "quality": data.get("quality", "--"),
            "grade": data.get("grade", "--"),
            "rr": data.get("rr", "0.0"),
            "entry_price": data.get("entry_price", "--"),
        })
    elif status in ("TP_HIT", "SL_HIT", "EXPIRED"):
        entry = last_entry_by_symbol.get(symbol)
        journal_log.append({
            "kind": "exit",
            "time": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "direction": entry.get("direction") if entry else data.get("direction"),
            "status": status,
            "entry_status": entry.get("status") if entry else None,
            "session_at_entry": entry.get("session") if entry else None,
            "quality": entry.get("quality") if entry else "--",
            "grade": entry.get("grade") if entry else "--",
            "rr": entry.get("rr") if entry else "0.0",
            "entry_price": entry.get("entry_price") if entry else "--",
            "r_multiple": _compute_r_multiple(entry, data),
        })
    else:
        return
    del journal_log[: max(0, len(journal_log) - JOURNAL_MAX_ENTRIES)]
    _save_journal_to_disk()

@app.get("/api/journal")
async def get_journal():
    return journal_log

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
market_state = {}

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
    await manager.broadcast(json.dumps(reset_data))
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

    _record_journal_event(symbol, status, direction, data)
    market_state[symbol] = data
    await manager.broadcast(json.dumps(data))
    return {"status": "success", "symbol": symbol}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Envoi initial de l'état actuel de tous les actifs connus
        for sym, item in market_state.items():
            await websocket.send_text(json.dumps(item))
        # Signal de fin de synchro : le front sait qu'il peut réactiver son (audio/popups/log)
        await websocket.send_text(json.dumps({"type": "sync_complete"}))

        while True:
            # Écoute sans bloquer avec keep-alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except (WebSocketDisconnect, Exception):
        manager.disconnect(websocket)