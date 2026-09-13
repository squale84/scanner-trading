from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import os
from typing import List
from starlette.websockets import WebSocket, WebSocketDisconnect

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sert index.html directement depuis la racine web
@app.get("/")
async def get_index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

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
    print(f"🔄 [{sym}] Carte remise en STANDBY manuellement.")
    return {"status": "success", "symbol": sym}

@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        body = await request.body()
        data = json.loads(body.decode("utf-8"))
    
    symbol = data.get("symbol", "UNKNOWN")
    status = data.get("status", "INFO")
    
    if "RETEST" in status:
        print(f"⚠️ [{symbol}] {status} | Niveau: {data.get('level')} | Prix: {data.get('current_price')}")
    else:
        print(f"🚀 [{symbol}] {status} {data.get('direction')} | Entree: {data.get('entry_price')} | SL: {data.get('sl_price')} | TP: {data.get('tp_price')}")

    market_state[symbol] = data
    await manager.broadcast(json.dumps(data))
    return {"status": "success"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        for sym, item in market_state.items():
            await websocket.send_text(json.dumps(item))
        while True:
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception):
        manager.disconnect(websocket)