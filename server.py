from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import asyncio
import re
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
    _sync_storage()
    report = _storage_report()
    degraded = not report["healthy"] or report["unsaved_events"] > 0
    return {"status": "degraded" if degraded else "alive",
            "connections": len(manager.active_connections), "storage": report,
            "reset_protected": bool(_reset_secret())}

# --- Calendrier économique (source gratuite, sans clé API : flux FairEconomy/ForexFactory) ---
# Cache persisté (Postgres/Neon en production, voir storage.py) : la source refuse souvent les
# requêtes venant de Render, et un redéploiement efface disque et mémoire. Sans cache persistant,
# le calendrier restait vide après chaque déploiement (constaté le 23/09 : 502 en continu).
CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
# La tâche GitHub (update_calendar.py) est programmée toutes les 30 min, mais GitHub retarde souvent
# les tâches programmées (écarts de plusieurs heures constatés le 24/09). Les données restent donc
# « à jour » pendant 3 h : en deçà, le serveur ne sollicite pas la source (qui bloque Render en 429) ;
# au-delà, il tente lui-même la source et, s'il échoue, sert le cache marqué en retard (Stale=1).
CALENDAR_TASK_INTERVAL = 1800        # fréquence programmée de la tâche GitHub (information)
CALENDAR_CACHE_TTL = 3 * 3600        # durée pendant laquelle les données sont considérées à jour
CALENDAR_RETRY_AFTER_FAILURE = 900  # après un échec, pas de nouvel essai avant 15 min (évite d'aggraver le blocage)
_calendar_cache = {"data": None, "fetched_at": 0.0}
_calendar_last_failure = 0.0
_calendar_last_storage_check = 0.0

def _load_calendar_cache_from_disk():
    saved = storage.load_state("calendar_cache", "calendar_cache.json")
    if saved is storage.FAILED or not saved:
        return
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
        saved = storage.load_state("calendar_cache", "calendar_cache.json")
        if saved is storage.FAILED or not saved:
            saved = {}
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
# Rempli par _sync_storage() (plus bas) : tant que l'état en base n'a pas été lu (Neon injoignable
# au démarrage), storage.STATUS["loaded"] reste False et AUCUNE écriture susceptible d'écraser
# l'état distant (positions, dernières alertes) n'est faite.
journal_log: List[dict] = []
open_positions: dict = {}
pending_rows: List[dict] = []   # lignes de journal pas encore écrites en base (mémoire seulement)
touched_symbols: set = set()    # actifs modifiés en mémoire pendant que l'état distant était inconnu
# Version de l'état des positions (C5) : +1 à chaque modification. Envoyée avec chaque instantané
# (REST et WebSocket) pour que le dashboard garde toujours le plus récent, quel que soit l'ordre
# d'arrivée des réponses au chargement de la page.
positions_version = 0

def _bump_positions_version():
    global positions_version
    positions_version += 1

def _save_positions_to_disk(symbol=None):
    _bump_positions_version()
    if not storage.STATUS["loaded"]:
        if symbol:
            touched_symbols.add(symbol)
        return storage.blocked_write("des positions")
    return storage.save_positions(open_positions)

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
        return _r_at_price(entry, entry.get("tp_price"))
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
    # On garde l'ordre : les lignes en attente sont réécrites d'abord. Si elles ne passent pas,
    # celle-ci attend derrière elles et compte comme NON sauvegardée.
    if pending_rows and not _flush_pending():
        pending_rows.append(row)
        storage.deferred_write("du journal")
        return
    if not storage.append_journal_row(row, journal_log):
        pending_rows.append(row)

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
        _save_positions_to_disk(symbol)
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
        _save_positions_to_disk(symbol)
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
            _save_positions_to_disk(symbol)
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
    _sync_storage()
    return journal_log

@app.get("/api/positions")
async def get_positions():
    _sync_storage()
    return JSONResponse(content=open_positions, headers={"X-Positions-Version": str(positions_version)})

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
market_state = {}

def _seed_market_state():
    for sym, pos in open_positions.items():
        if sym not in market_state:
            market_state[sym] = {**{k: pos.get(k) for k in ("symbol", "direction", "quality", "grade", "rr", "entry_price", "sl_price", "tp_price")},
                                 "status": "PRICE_UPDATE", "current_price": pos.get("last_price")}

def _positions_message():
    return json.dumps({"type": "positions", "positions": open_positions, "version": positions_version})

# Dernière alerte reçue par actif (y compris PRICE_UPDATE), persistée : permet de voir sur chaque
# carte si l'alerte TradingView de cet actif envoie bien quelque chose, et depuis quand.
last_alerts: dict = {}

# C6 — état des cartes après redémarrage : il est RECONSTRUIT depuis le journal (dernière sortie
# par actif) au lieu d'enregistrer chaque message en base. Seule la date du dernier Reset par
# actif est persistée : une carte clôturée reste affichée tant qu'aucun Reset n'est venu après
# sa sortie.
card_resets: dict = {}   # actif -> date ISO (UTC) du dernier Reset

def _save_card_resets():
    if not storage.STATUS["loaded"]:
        return storage.blocked_write("des Reset de cartes")
    return storage.save_state("card_resets", "card_resets.json", card_resets)

def _rebuild_closed_cards():
    """Cartes clôturées après redémarrage : dernière sortie du journal, si postérieure au dernier
    Reset de l'actif et sans position ouverte ni état plus récent déjà en mémoire."""
    last_exit = {}
    for row in journal_log:
        if row.get("kind") == "exit" and row.get("status") in ("TP_HIT", "SL_HIT", "EXPIRED"):
            last_exit[row.get("symbol")] = row
    for sym, row in last_exit.items():
        if sym in market_state or sym in open_positions:
            continue
        if (row.get("time") or "") <= (card_resets.get(sym) or ""):
            continue
        market_state[sym] = {"symbol": sym, "status": row["status"], "direction": "NONE", "quality": "--", "grade": "--",
                             "entry_price": "0.0", "sl_price": "0.0", "tp_price": "0.0",
                             "current_price": row.get("last_price") or row.get("exit_price") or "--", "rr": "0.0"}

def _save_last_alerts(symbol):
    if not storage.STATUS["loaded"]:
        return storage.blocked_write("des dernières alertes")
    return storage.save_state("last_alerts", "last_alerts.json", last_alerts)

def _last_alerts_message():
    return json.dumps({"type": "last_alerts", "last_alerts": last_alerts})

_last_sync_attempt = 0.0

def _flush_pending():
    """Réécrit dans l'ordre les lignes de journal en attente. Renvoie True si toutes sont écrites."""
    while pending_rows:
        if not storage.append_journal_row(pending_rows[0], journal_log):
            return False
        pending_rows.pop(0)
    return True

def _load_initial_state():
    """Lit l'état en base et le FUSIONNE avec ce qui a été reçu en mémoire pendant la panne :
    positions : la base fait foi, sauf pour les actifs modifiés entre-temps (touched_symbols) ;
    dernières alertes : la plus récente par actif ; journal : lignes en attente réécrites puis
    historique relu. Renvoie True si la synchronisation est complète.

    Un échec au milieu du rattrapage laisse loaded=False (rien n'est fusionné ni écrasé) : les
    lignes déjà réécrites sont retirées de la file une par une, les suivantes restent en attente
    dans l'ordre, et la tentative suivante reprend là où celle-ci s'est arrêtée.

    LIMITE CONNUE (non corrigée, documentée) : si une alerte de SORTIE arrive alors que l'état en
    base n'a jamais pu être chargé depuis le démarrage, le serveur ne connaît pas la position :
    la sortie est journalisée sans résultat en R (sortie « orpheline ») et la position reste ouverte
    en base jusqu'à la prochaine entrée sur cet actif, qui la clôt en « REPLACED »."""
    if not storage.init():
        return False
    remote_pos = storage.load_positions()
    remote_alerts = storage.load_state("last_alerts", "last_alerts.json")
    remote_resets = storage.load_state("card_resets", "card_resets.json")
    if remote_pos is storage.FAILED or remote_alerts is storage.FAILED or remote_resets is storage.FAILED:
        return False
    if not _flush_pending():
        return False
    remote_journal = storage.load_journal(JOURNAL_MAX_ENTRIES)
    if remote_journal is storage.FAILED:
        return False

    merged = dict(remote_pos or {})
    for sym in touched_symbols:
        if sym in open_positions:
            merged[sym] = open_positions[sym]
        else:
            merged.pop(sym, None)
    open_positions.clear()
    open_positions.update(merged)
    for sym, a in (remote_alerts or {}).items():
        if sym not in last_alerts or (a.get("time") or "") > (last_alerts[sym].get("time") or ""):
            last_alerts[sym] = a
    resets_changed = bool(card_resets)
    for sym, t in (remote_resets or {}).items():
        if (t or "") > (card_resets.get(sym) or ""):
            card_resets[sym] = t
    journal_log[:] = remote_journal
    _seed_market_state()
    _rebuild_closed_cards()
    _bump_positions_version()

    storage.STATUS["loaded"] = True
    changed = bool(touched_symbols)
    touched_symbols.clear()
    ok = True
    if changed:
        ok = storage.save_positions(open_positions) and storage.save_state("last_alerts", "last_alerts.json", last_alerts)
    if resets_changed:
        ok = storage.save_state("card_resets", "card_resets.json", card_resets) and ok
    print(f"💾 Persistance : {storage.BACKEND} — {len(journal_log)} ligne(s) de journal, {len(open_positions)} position(s) ouverte(s)")
    return ok

def _sync_storage(force=False):
    """Appelée au démarrage puis au début des requêtes (au plus toutes les 5 s) : charge l'état si
    ce n'est pas encore fait, sinon réécrit les lignes de journal en attente."""
    global _last_sync_attempt
    now = time.time()
    if not force and now - _last_sync_attempt < 5:
        return
    if storage.STATUS["loaded"] and not pending_rows and not unsaved["count"]:
        return
    _last_sync_attempt = now
    was_pending = unsaved["count"]
    if not storage.STATUS["loaded"]:
        ok = _load_initial_state()
    else:
        # Base déjà chargée : réécrit le journal en attente, puis l'état courant (positions,
        # dernières alertes) qui a pu ne pas être écrit pendant la panne.
        ok = _flush_pending() and storage.save_positions(open_positions) \
            and storage.save_state("last_alerts", "last_alerts.json", last_alerts)
    if ok and not pending_rows and not touched_symbols and was_pending:
        # Tout ce qui avait échoué est maintenant en base : on le dit, sans l'oublier.
        unsaved["recovered"] += unsaved["count"]
        unsaved["recovered_at"] = now
        unsaved["count"] = 0
        unsaved["first_at"] = None

# Événements reçus dont l'écriture en base a échoué. Il n'existe PAS de file de réessai durable :
# ils ne vivent qu'en mémoire du serveur (perdus au prochain redémarrage) et ne sont donc jamais
# présentés comme sauvegardés. Le compteur reste affiché jusqu'au redémarrage du serveur.
unsaved = {"count": 0, "first_at": None, "last_at": None, "recovered": 0, "recovered_at": None}

def _note_unsaved():
    now = time.time()
    unsaved["count"] += 1
    unsaved["first_at"] = unsaved["first_at"] or now
    unsaved["last_at"] = now

def _storage_report():
    report = dict(storage.STATUS)
    report.update({"unsaved_events": unsaved["count"], "first_unsaved_at": unsaved["first_at"],
                   "last_unsaved_at": unsaved["last_at"], "pending_journal_rows": len(pending_rows),
                   "recovered_events": unsaved["recovered"], "recovered_at": unsaved["recovered_at"]})
    return report

def _storage_message():
    return json.dumps({"type": "storage", "storage": _storage_report()})

def _persistence_response(symbol, persisted):
    """Réponse honnête : succès seulement si toutes les écritures en base de la requête ont réussi."""
    if persisted:
        return {"status": "success", "symbol": symbol, "persisted": True}
    return JSONResponse(status_code=500, content={
        "status": "error", "symbol": symbol, "persisted": False,
        "error": "Écriture en base impossible : événement conservé en mémoire seulement (réécrit au retour de la base, perdu si le serveur redémarre avant).",
        "detail": storage.STATUS["last_error"],
    })

# Démarrage : l'état en base est considéré comme inconnu tant qu'il n'a pas été relu.
storage.STATUS["loaded"] = False
_sync_storage(force=True)

class ResetRequest(BaseModel):
    symbol: str

# --- Accès administrateur pour le Reset (C4) ---
# RESET_SECRET (variable d'environnement Render) = code administrateur choisi par l'utilisateur.
# Il n'est JAMAIS dans index.html, dans une URL ni dans les journaux : il est saisi une fois par
# appareil (corps d'une requête POST en HTTPS), puis le serveur remet un cookie de session
# HttpOnly + Secure + SameSite=Strict valable 30 jours. Le cookie ne contient pas le code : c'est
# une date d'expiration + un aléa, signés par HMAC avec le code (changer le code invalide toutes
# les sessions). Sans RESET_SECRET configuré, le Reset reste ouvert comme avant (transition).
ADMIN_COOKIE = "admin_session"
ADMIN_SESSION_SECONDS = 30 * 24 * 3600
ADMIN_MAX_FAILURES = 5
ADMIN_LOCK_SECONDS = 15 * 60
_admin_failures: dict = {}   # adresse IP -> {"count": n, "locked_until": ts}

def _reset_secret():
    return os.environ.get("RESET_SECRET", "").strip()

def _sign(payload, secret):
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

def _new_admin_token(secret):
    payload = f"{int(time.time()) + ADMIN_SESSION_SECONDS}.{secrets.token_hex(16)}"
    return base64.urlsafe_b64encode(f"{payload}.{_sign(payload, secret)}".encode()).decode()

def _admin_session_valid(request: Request):
    secret = _reset_secret()
    if not secret:
        return True  # protection non activée
    token = request.cookies.get(ADMIN_COOKIE, "")
    try:
        expiry, nonce, sig = base64.urlsafe_b64decode(token.encode()).decode().split(".")
    except Exception:
        return False
    return hmac.compare_digest(sig, _sign(f"{expiry}.{nonce}", secret)) and int(expiry) > time.time()

def _client_ip(request: Request):
    # Chaque proxy AJOUTE en fin de X-Forwarded-For l'adresse qu'il voit : la dernière valeur est la
    # sienne (fiable). La première est écrite par le client lui-même et peut être falsifiée à chaque essai.
    fwd = request.headers.get("x-forwarded-for", "")
    return fwd.split(",")[-1].strip() if fwd else (request.client.host if request.client else "?")

class AdminLogin(BaseModel):
    code: str

@app.get("/api/admin/status")
async def admin_status(request: Request):
    return {"protected": bool(_reset_secret()), "unlocked": _admin_session_valid(request)}

@app.post("/api/admin/login")
async def admin_login(data: AdminLogin, request: Request):
    secret = _reset_secret()
    if not secret:
        return {"status": "success", "protected": False}
    ip = _client_ip(request)
    now = time.time()
    fail = _admin_failures.get(ip, {"count": 0, "locked_until": 0})
    if fail["locked_until"] > now:
        wait = int((fail["locked_until"] - now) // 60) + 1
        return JSONResponse(status_code=429, content={"error": f"Trop d'essais : réessaie dans {wait} min."})
    if not hmac.compare_digest(data.code.encode(), secret.encode()):
        fail["count"] += 1
        if fail["count"] >= ADMIN_MAX_FAILURES:
            fail = {"count": 0, "locked_until": now + ADMIN_LOCK_SECONDS}
        _admin_failures[ip] = fail
        print(f"🔒 Code administrateur incorrect ({ip})")  # jamais le code saisi
        return JSONResponse(status_code=401, content={"error": "Code incorrect."})
    _admin_failures.pop(ip, None)
    resp = JSONResponse(content={"status": "success", "protected": True})
    resp.set_cookie(ADMIN_COOKIE, _new_admin_token(secret), max_age=ADMIN_SESSION_SECONDS, path="/",
                    httponly=True, secure=True, samesite="strict")
    print(f"🔓 Session administrateur ouverte ({ip})")
    return resp

@app.post("/api/admin/logout")
async def admin_logout():
    resp = JSONResponse(content={"status": "success"})
    resp.delete_cookie(ADMIN_COOKIE, path="/", httponly=True, secure=True, samesite="strict")
    return resp

@app.post("/api/reset")
async def reset_card(data: ResetRequest, request: Request):
    if not _admin_session_valid(request):
        return JSONResponse(status_code=401, content={"error": "auth_required"})
    _sync_storage()
    sym = data.symbol.upper()
    failures_before = storage.STATUS["write_failures"]
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
    card_resets[sym] = datetime.utcnow().isoformat()
    _save_card_resets()
    # Reset manuel = l'utilisateur abandonne le suivi : la position disparaît aussi de la jauge.
    # État en base pas encore chargé : la position peut exister en base sans être en mémoire. Le
    # Reset est alors noté (touched_symbols) pour être appliqué à la fusion au retour de la base, et
    # la réponse est persisted:false — jamais un succès sur un état distant inconnu.
    removed = open_positions.pop(sym, None) is not None
    if removed or not storage.STATUS["loaded"]:
        _save_positions_to_disk(sym)
    persisted = storage.STATUS["write_failures"] == failures_before
    if not persisted:
        _note_unsaved()
    await manager.broadcast(json.dumps(reset_data))
    await manager.broadcast(_positions_message())
    await manager.broadcast(_storage_message())
    print(f"🔄 [{sym}] Carte remise en STANDBY.")
    return _persistence_response(sym, persisted)

# Validation minimale des charges utiles du Radar : on refuse ce qui ne peut pas être un signal
# (objet non JSON, symbole hors format, champ démesuré) SANS restreindre les valeurs légitimes
# (statuts et noms de setup ne sont pas énumérés : le Radar peut en ajouter).
SYMBOL_RE = re.compile(r"^[A-Z0-9][A-Z0-9._:/!-]{0,19}$")  # ! : contrats continus (NQ1!), ticker TradingView
MAX_FIELD_LENGTH = 60

def _payload_error(data):
    """Renvoie le motif du refus, ou None si la charge utile est acceptable."""
    if not isinstance(data, dict):
        return "objet JSON attendu"
    if not SYMBOL_RE.match(str(data.get("symbol", "UNKNOWN")).upper()):
        return "symbole hors format"
    for key, value in data.items():
        if isinstance(value, str) and len(value) > MAX_FIELD_LENGTH:
            return f"champ « {key} » trop long"
    return None

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

    error = _payload_error(data)
    if error:
        print(f"⛔ Charge utile webhook refusée : {error}")
        return JSONResponse(status_code=400, content={"error": f"Charge utile refusée : {error}"})

    _sync_storage()
    symbol = data.get("symbol", "UNKNOWN").upper()
    status = data.get("status", "INFO")
    direction = data.get("direction", "NONE")

    print(f"⚡ [{symbol}] {status} | Dir: {direction} | Entree: {data.get('entry_price')} | SL: {data.get('sl_price')} | TP: {data.get('tp_price')}")

    # Aucune attente (await) entre ce relevé et la fin des écritures : le compteur d'échecs ne peut
    # pas être modifié par une autre requête entre-temps.
    failures_before = storage.STATUS["write_failures"]
    added_rows = _record_journal_event(symbol, status, direction, data)
    last_alerts[symbol] = {"time": datetime.utcnow().isoformat(), "status": status}
    _save_last_alerts(symbol)
    persisted = storage.STATUS["write_failures"] == failures_before
    if not persisted:
        _note_unsaved()
    market_state[symbol] = data
    await manager.broadcast(json.dumps(data))
    # Le journal et les jauges du front sont pilotés par l'état serveur (source unique) :
    # mêmes données en direct qu'après un F5, et les doublons filtrés ici n'apparaissent nulle part.
    for row in added_rows:
        await manager.broadcast(json.dumps({"type": "journal", "row": row}))
    await manager.broadcast(_positions_message())
    await manager.broadcast(_last_alerts_message())
    await manager.broadcast(_storage_message())
    return _persistence_response(symbol, persisted)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Envoi initial de l'état actuel de tous les actifs connus
        for sym, item in market_state.items():
            await websocket.send_text(json.dumps(item))
        await websocket.send_text(_positions_message())
        await websocket.send_text(_last_alerts_message())
        await websocket.send_text(_storage_message())
        # Signal de fin de synchro : le front sait qu'il peut réactiver son (audio/popups/log)
        await websocket.send_text(json.dumps({"type": "sync_complete"}))

        while True:
            # Écoute sans bloquer avec keep-alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except (WebSocketDisconnect, Exception):
        manager.disconnect(websocket)