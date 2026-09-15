from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import json
import os
import sys
import asyncio
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
@app.get("/")
async def get_index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

# Route santé pour ping automatique anti-sommeil Render (UptimeRobot / Cron)
@app.get("/health")
async def health_check():
    return {"status": "alive", "connections": len(manager.active_connections)}

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