from fastapi import FastAPI, Request, Query
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
import time
import httpx
import math
import random
import re
from collections import deque
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import List, Optional, Dict, Any
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

def _tf_propre(v):
    """Unité de temps du graphique d'où part l'alerte (R6.3 : « M5 », « M15 », « H1 »…) ; None si absente ou douteuse (anciennes alertes)."""
    t = str(v).strip().upper() if v is not None else ""
    return t if re.fullmatch(r"[A-Z]{1,2}[0-9]{1,3}", t) else None

# Le Radar envoie le nom du graphique TradingView (syminfo.ticker), qui diffère parfois du symbole des cartes du
# site : sur le graphique Solana il vaut « SOLU » alors que la carte est « SOLUSD » (sans carte, le front ignore l'alerte).
SYMBOLES_ALIAS = {"SOLU": "SOLUSD"}

def _symbole_canonique(symbole):
    return SYMBOLES_ALIAS.get(symbole, symbole)

def _reprendre_position_sous_alias(ancien, nouveau):
    """Un trade ouvert avant l'alias reste sous l'ancien nom : on le renomme pour que ses mises à jour et sa clôture le retrouvent."""
    if ancien == nouveau or ancien not in open_positions or nouveau in open_positions:
        return
    pos = open_positions.pop(ancien)
    pos["symbol"] = nouveau
    open_positions[nouveau] = pos
    _save_positions_to_disk(nouveau)

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
    if status == "BE_HIT":
        return 0.0
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
    if entry and status == "BE_HIT":
        return entry.get("entry_price")
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
        "pd_zone": data.get("pd_zone", "--"),
        "pd_pct": data.get("pd_pct"),
        "sweep_lvl": data.get("sweep_lvl"),
        "sweep_type": data.get("sweep_type", "--"),
        "htf_aligned": data.get("htf_aligned"),
        "tf": _tf_propre(data.get("tf")),
        "auto_filtered": data.get("auto_filtered", False),
        "auto_reason": data.get("auto_reason"),
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
    if status in ("TP_HIT", "SL_HIT", "EXPIRED", "BE_HIT"):
        pos = open_positions.pop(symbol, None)
        trade_id = data.get("trade_id")
        if pos is None:
            # 1. Vérification anti-doublon si la sortie a déjà été enregistrée
            if trade_id:
                already_exited = any(
                    r.get("kind") == "exit" and r.get("trade_id") == trade_id
                    for r in reversed(journal_log)
                )
                if already_exited:
                    return []
            else:
                last = next((r for r in reversed(journal_log) if r.get("symbol") == symbol), None)
                if last is not None and last.get("kind") == "exit":
                    return []  # sortie déjà enregistrée, aucune position ouverte : doublon

            # 2. Cherche d'abord dans journal_log s'il existe une ligne kind == "entry"
            # correspondant au même trade_id (s'il est non vide) ou au même symbol
            candidate_entry = None
            for r in reversed(journal_log):
                if r.get("symbol") == symbol and r.get("kind") == "entry":
                    if trade_id and r.get("trade_id"):
                        if r.get("trade_id") == trade_id:
                            candidate_entry = r
                            break
                    elif not trade_id:
                        candidate_entry = r
                        break

            if candidate_entry:
                pos = {
                    "symbol": symbol,
                    "direction": candidate_entry.get("direction"),
                    "status": candidate_entry.get("status"),
                    "quality": candidate_entry.get("quality", "--"),
                    "grade": candidate_entry.get("grade", "--"),
                    "rr": candidate_entry.get("rr", "0.0"),
                    "entry_price": candidate_entry.get("entry_price"),
                    "sl_price": candidate_entry.get("sl_price"),
                    "tp_price": candidate_entry.get("tp_price"),
                    "last_price": data.get("current_price") or candidate_entry.get("entry_price"),
                    "best_r": candidate_entry.get("best_r") or 0.0,
                    "session": candidate_entry.get("session") or _session_label_now(),
                    "opened_at": candidate_entry.get("time"),
                    "last_update": now,
                    "recovered": True,
                    "version": candidate_entry.get("version"),
                    "trade_id": candidate_entry.get("trade_id"),
                    "pd_zone": candidate_entry.get("pd_zone", data.get("pd_zone", "--")),
                    "pd_pct": candidate_entry.get("pd_pct", data.get("pd_pct")),
                    "sweep_lvl": candidate_entry.get("sweep_lvl", data.get("sweep_lvl")),
                    "sweep_type": candidate_entry.get("sweep_type", data.get("sweep_type", "--")),
                    "htf_aligned": candidate_entry.get("htf_aligned", data.get("htf_aligned")),
                    "tf": _tf_propre(candidate_entry.get("tf", data.get("tf"))),
                    "auto_filtered": candidate_entry.get("auto_filtered", data.get("auto_filtered", False)),
                    "auto_reason": candidate_entry.get("auto_reason", data.get("auto_reason")),
                    "targets": candidate_entry.get("targets") or [],
                }
            else:
                # 3. Si aucune entrée dans journal_log, reconstruire à partir des champs du webhook
                ep = _parse_num(data.get("entry_price"))
                if ep is not None and ep > 0:
                    pos = {
                        "symbol": symbol,
                        "direction": data.get("direction") if data.get("direction") in ("BUY", "SELL") else None,
                        "status": "RECOVERED",
                        "quality": data.get("quality", "--"),
                        "grade": data.get("grade", "--"),
                        "rr": data.get("rr", "0.0"),
                        "entry_price": data.get("entry_price"),
                        "sl_price": data.get("sl_price"),
                        "tp_price": data.get("tp_price"),
                        "last_price": data.get("current_price") or data.get("entry_price"),
                        "best_r": 0.0,
                        "session": _session_label_now(),
                        "opened_at": None,
                        "last_update": now,
                        "recovered": True,
                        "version": data.get("version"),
                        "trade_id": trade_id,
                        "pd_zone": data.get("pd_zone", "--"),
                        "pd_pct": data.get("pd_pct"),
                        "sweep_lvl": data.get("sweep_lvl"),
                        "sweep_type": data.get("sweep_type", "--"),
                        "htf_aligned": data.get("htf_aligned"),
                        "tf": _tf_propre(data.get("tf")),
                        "auto_filtered": data.get("auto_filtered", False),
                        "auto_reason": data.get("auto_reason"),
                        "targets": _clean_targets(data),
                    }
        else:
            _save_positions_to_disk(symbol)
        row = _exit_row(symbol, status, pos, data, now)
        _append_journal(row)
        added.append(row)
    elif direction in ("BUY", "SELL"):
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
            "pd_zone": data.get("pd_zone", "--"),
            "pd_pct": data.get("pd_pct"),
            "sweep_lvl": data.get("sweep_lvl"),
            "sweep_type": data.get("sweep_type", "--"),
            "htf_aligned": data.get("htf_aligned"),
            "tf": _tf_propre(data.get("tf")),
            "auto_filtered": data.get("auto_filtered", False),
            "auto_reason": data.get("auto_reason"),
            "targets": open_positions[symbol]["targets"],
        }
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
        "pd_zone": (pos.get("pd_zone") if pos else None) or data.get("pd_zone", "--"),
        "pd_pct": (pos.get("pd_pct") if pos else None) or data.get("pd_pct"),
        "sweep_lvl": (pos.get("sweep_lvl") if pos else None) or data.get("sweep_lvl"),
        "sweep_type": (pos.get("sweep_type") if pos else None) or data.get("sweep_type", "--"),
        "htf_aligned": (pos.get("htf_aligned") if pos and pos.get("htf_aligned") is not None else None) if pos else data.get("htf_aligned"),
        "tf": _tf_propre((pos.get("tf") if pos else None) or data.get("tf")),
        "auto_filtered": (pos.get("auto_filtered") if pos else None) or data.get("auto_filtered", False),
        "auto_reason": (pos.get("auto_reason") if pos else None) or data.get("auto_reason"),
        "targets": pos.get("targets") if pos else [],
        "targets_reached": _targets_reached(pos, status) if pos else None,
    }

# --- Module d'Auto-Correction & Auto-Tuner ---
def _compute_autotune_rules():
    """Analyse journal_log par combinaison (symbol, pattern, session, pd_zone).
    Si une combinaison totalise >= 5 trades clôturés et présente Winrate < 35% ou R cumulé < -2.5R,
    marque cette règle comme pénalisée / auto-filtrée."""
    stats = {}
    for r in journal_log:
        if r.get("kind") != "exit":
            continue
        r_mult = r.get("r_multiple")
        if r_mult is None or r.get("status") == "REPLACED":
            continue
        sym = (r.get("symbol") or "UNKNOWN").upper()
        pat = r.get("entry_status") or r.get("status") or "UNKNOWN"
        sess = r.get("session_at_entry") or r.get("session") or "UNKNOWN"
        pdz = r.get("pd_zone") or "--"
        key = (sym, pat, sess, pdz)
        if key not in stats:
            stats[key] = []
        stats[key].append(float(r_mult))

    rules = []
    penalized_map = {}
    total_closed = sum(len(v) for v in stats.values())

    for (sym, pat, sess, pdz), r_list in stats.items():
        n = len(r_list)
        wins = sum(1 for x in r_list if x > 0)
        losses = sum(1 for x in r_list if x <= 0)
        wr = round((wins / n) * 100, 1) if n > 0 else 0.0
        r_sum = round(sum(r_list), 2)
        penalized = n >= 5 and (wr < 35.0 or r_sum < -2.5)
        reason = None
        if penalized:
            reasons = []
            if wr < 35.0:
                reasons.append(f"Winrate faible ({wr}% < 35%)")
            if r_sum < -2.5:
                reasons.append(f"R cumulé négatif ({r_sum:+.1f}R < -2.5R)")
            reason = " & ".join(reasons) + f" sur {n} trades"
            penalized_map[(sym, pat, sess, pdz)] = reason

        rules.append({
            "symbol": sym,
            "pattern": pat,
            "session": sess,
            "pd_zone": pdz,
            "trades_count": n,
            "wins": wins,
            "losses": losses,
            "win_rate": wr,
            "r_sum": r_sum,
            "penalized": penalized,
            "reason": reason
        })

    rules.sort(key=lambda x: (not x["penalized"], -x["trades_count"]))
    return {
        "total_closed_trades": total_closed,
        "penalized_rules_count": len(penalized_map),
        "rules": rules,
        "penalized_map": penalized_map
    }

@app.get("/api/autotune")
async def get_autotune():
    _sync_storage()
    tuning = _compute_autotune_rules()
    return {
        "total_closed_trades": tuning["total_closed_trades"],
        "penalized_rules_count": tuning["penalized_rules_count"],
        "rules": tuning["rules"]
    }

# --- Module Bougies Historiques (GET /api/candles) ---
YF_MAPPING = {
    "GOLD": "GC=F",
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    "USDCHF": "USDCHF=X",
    "NZDUSD": "NZDUSD=X",
    "BTCUSD": "BTC-USD",
    "BTC": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "ETH": "ETH-USD",
    "SOLUSD": "SOL-USD",
    "US100": "NQ=F",
    "NAS100": "NQ=F",
    "US500": "ES=F",
    "SPX500": "ES=F",
    "US30": "YM=F",
    "GER40": "^GDAXI",
    "DAX": "^GDAXI",
}

def _parse_ts(ts_val):
    if not ts_val:
        return None
    try:
        val = float(ts_val)
        if val > 1e11:
            val /= 1000.0
        return datetime.fromtimestamp(val, timezone.utc)
    except (ValueError, TypeError):
        pass
    try:
        clean_str = str(ts_val).replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None

def _generate_synthetic_candles(
    symbol: str,
    start_dt: datetime,
    end_dt: datetime,
    entry_dt: datetime,
    exit_dt: datetime,
    entry_price: Optional[float],
    sl_price: Optional[float],
    tp_price: Optional[float],
    exit_price: Optional[float],
    best_r: Optional[float],
    direction: str
) -> List[dict]:
    defaults = {
        "GOLD": (2650.0, 2),
        "XAUUSD": (2650.0, 2),
        "EURUSD": (1.0850, 5),
        "GBPUSD": (1.3050, 5),
        "USDJPY": (152.0, 3),
        "AUDUSD": (0.6650, 5),
        "USDCAD": (1.3850, 5),
        "BTCUSD": (67000.0, 2),
        "BTC": (67000.0, 2),
        "ETHUSD": (2600.0, 2),
        "ETH": (2600.0, 2),
        "US100": (20400.0, 2),
        "NAS100": (20400.0, 2),
        "US500": (5850.0, 2),
        "US30": (43000.0, 2),
        "GER40": (19500.0, 2),
    }
    default_price, decimals = defaults.get(symbol, (100.0, 2))
    ep = entry_price if (entry_price is not None and entry_price > 0) else default_price
    is_buy = (direction or "BUY").upper() == "BUY"

    if sl_price is not None and sl_price > 0:
        sl = sl_price
        risk = abs(ep - sl)
    else:
        risk = ep * 0.003
        sl = (ep - risk) if is_buy else (ep + risk)

    if risk <= 0:
        risk = ep * 0.003

    if tp_price is not None and tp_price > 0:
        tp = tp_price
    else:
        tp = (ep + 2.0 * risk) if is_buy else (ep - 2.0 * risk)

    if exit_price is not None and exit_price > 0:
        xp = exit_price
    else:
        if best_r is not None and best_r >= 1.8:
            xp = tp
        else:
            xp = sl

    b_r = best_r if (best_r is not None and best_r > 0) else (1.5 if xp == tp else 0.4)
    peak_price = (ep + b_r * risk) if is_buy else (ep - b_r * risk)

    # Seed basé sur le timestamp de l'entrée pour un rendu stable et reproductible
    seed_val = int(entry_dt.timestamp())
    rng = random.Random(seed_val)

    step = timedelta(minutes=5)
    cur_dt = start_dt
    cur_price = ep - (risk * rng.uniform(0.1, 0.4) if is_buy else -risk * rng.uniform(0.1, 0.4))
    candle_idx = 0

    candles = []
    trade_duration_sec = max(300.0, (exit_dt - entry_dt).total_seconds())

    while cur_dt <= end_dt:
        ts_sec = int(cur_dt.timestamp())
        open_p = cur_price

        # Trajectoire par phase ICT
        if cur_dt < entry_dt:
            # Consolidation pré-entrée avec balayage (sweep) avant l'entrée
            time_left_candles = (entry_dt - cur_dt).total_seconds() / 300.0
            if time_left_candles <= 3:
                target = (sl - risk * 0.1) if is_buy else (sl + risk * 0.1)
            else:
                target = ep + risk * 0.25 * math.sin(candle_idx * 0.4)
            drift_weight = 0.35
        elif cur_dt <= exit_dt:
            # Phase active du trade
            trade_progress = max(0.0, min(1.0, (cur_dt - entry_dt).total_seconds() / trade_duration_sec))
            if trade_progress <= 0.6:
                sub = trade_progress / 0.6
                target = ep + (peak_price - ep) * sub
            else:
                sub = (trade_progress - 0.6) / 0.4
                target = peak_price + (xp - peak_price) * sub
            drift_weight = 0.55
        else:
            # Post-sortie : dérive fluide de marché
            target = xp + risk * 0.2 * math.sin(candle_idx * 0.3)
            drift_weight = 0.30

        step_vol = risk * rng.uniform(0.08, 0.25)
        counter_bias = -1.0 if rng.random() < 0.28 else 1.0
        delta = (target - open_p) * drift_weight * counter_bias + rng.gauss(0, step_vol * 0.5)
        close_p = open_p + delta

        body = abs(close_p - open_p)
        upper_wick = body * rng.uniform(0.2, 0.8) + step_vol * rng.uniform(0.1, 0.4)
        lower_wick = body * rng.uniform(0.2, 0.8) + step_vol * rng.uniform(0.1, 0.4)

        high_p = max(open_p, close_p) + upper_wick
        low_p = min(open_p, close_p) - lower_wick

        if cur_dt == exit_dt:
            close_p = xp
            high_p = max(high_p, xp)
            low_p = min(low_p, xp)

        vol = int(rng.uniform(150, 1200))

        candles.append({
            "time": ts_sec,
            "open": round(open_p, decimals),
            "high": round(high_p, decimals),
            "low": round(low_p, decimals),
            "close": round(close_p, decimals),
            "volume": vol
        })

        cur_price = close_p
        cur_dt += step
        candle_idx += 1

    return candles

@app.get("/api/candles")
async def get_candles(
    symbol: str = Query(..., description="Symbole de l'actif (ex: GOLD, EURUSD, BTCUSD)"),
    entry_ts: str = Query(..., description="Date/heure ISO ou timestamp de l'entrée"),
    exit_ts: Optional[str] = Query(None, description="Date/heure ISO ou timestamp de la sortie"),
    entry_price: Optional[float] = Query(None),
    sl_price: Optional[float] = Query(None),
    tp_price: Optional[float] = Query(None),
    exit_price: Optional[float] = Query(None),
    best_r: Optional[float] = Query(None),
    direction: Optional[str] = Query(None)
):
    _sync_storage()
    sym = symbol.upper()
    entry_dt = _parse_ts(entry_ts) or datetime.now(timezone.utc)
    exit_dt = _parse_ts(exit_ts) or (entry_dt + timedelta(minutes=150))
    if exit_dt < entry_dt:
        exit_dt = entry_dt + timedelta(minutes=30)

    # Récupérer les prix manquants depuis le journal si possible
    if entry_price is None or exit_price is None:
        for r in reversed(journal_log):
            if (r.get("symbol") or "").upper() == sym:
                if entry_price is None and _parse_num(r.get("entry_price")) is not None:
                    entry_price = _parse_num(r.get("entry_price"))
                if sl_price is None and _parse_num(r.get("sl_price")) is not None:
                    sl_price = _parse_num(r.get("sl_price"))
                if tp_price is None and _parse_num(r.get("tp_price")) is not None:
                    tp_price = _parse_num(r.get("tp_price"))
                if exit_price is None and _parse_num(r.get("exit_price")) is not None:
                    exit_price = _parse_num(r.get("exit_price"))
                if best_r is None and _parse_num(r.get("best_r")) is not None:
                    best_r = _parse_num(r.get("best_r"))
                if direction is None and r.get("direction"):
                    direction = r.get("direction")
                if entry_price is not None and exit_price is not None:
                    break

    # Fenêtre : 30 bougies M5 avant entrée (150 min) à 15 bougies après sortie (75 min)
    start_dt = entry_dt - timedelta(minutes=150)
    end_dt = exit_dt + timedelta(minutes=75)

    candles = []
    source = "synthetic"

    yf_ticker = YF_MAPPING.get(sym, sym)
    try:
        import yfinance as yf
        df = yf.download(
            yf_ticker,
            start=start_dt.strftime("%Y-%m-%d"),
            end=(end_dt + timedelta(days=1)).strftime("%Y-%m-%d"),
            interval="5m",
            progress=False
        )
        if df is not None and not df.empty:
            if hasattr(df.columns, "levels") and len(df.columns.levels) > 1:
                df.columns = df.columns.get_level_values(0)
            df_filtered = df[(df.index >= start_dt) & (df.index <= end_dt)]
            if len(df_filtered) >= 10:
                for idx, row in df_filtered.iterrows():
                    candles.append({
                        "time": int(idx.timestamp()),
                        "open": round(float(row["Open"]), 5),
                        "high": round(float(row["High"]), 5),
                        "low": round(float(row["Low"]), 5),
                        "close": round(float(row["Close"]), 5),
                        "volume": int(row.get("Volume", 0) or 0)
                    })
                source = "yfinance"
    except Exception as e:
        print(f"ℹ️ [{sym}] yfinance non utilisé ({e}), passage en mode synthétique.")

    if not candles:
        candles = _generate_synthetic_candles(
            symbol=sym,
            start_dt=start_dt,
            end_dt=end_dt,
            entry_dt=entry_dt,
            exit_dt=exit_dt,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            exit_price=exit_price,
            best_r=best_r,
            direction=direction or "BUY"
        )
        source = "synthetic"

    return {
        "status": "success",
        "symbol": sym,
        "source": source,
        "count": len(candles),
        "candles": candles
    }

@app.get("/api/journal")
async def get_journal():
    _sync_storage()
    return journal_log

@app.get("/api/positions")
async def get_positions():
    _sync_storage()
    return JSONResponse(content=open_positions, headers={"X-Positions-Version": str(positions_version)})

# R6.3 — événements de marché (status "EVENT") : niveau de liquidité pris, FVG de retournement. Ils ne sont PAS des
# trades : jamais inscrits au journal, ni aux positions, ni aux cartes. Gardés en mémoire (petit tampon récent) et
# diffusés au front ; Jarvis les lit sur /api/events. Le webhook n'étant pas authentifié, seuls les événements connus
# sont acceptés, avec leur libellé fixé ICI (jamais le texte reçu) et des nombres finis.
EVENEMENTS_MARCHE = {
    "ASIA_HIGH_SWEPT": "Haut Asie", "ASIA_HIGH_BROKEN": "Haut Asie", "ASIA_LOW_SWEPT": "Bas Asie", "ASIA_LOW_BROKEN": "Bas Asie",
    "LONDON_HIGH_SWEPT": "Haut Londres", "LONDON_HIGH_BROKEN": "Haut Londres", "LONDON_LOW_SWEPT": "Bas Londres", "LONDON_LOW_BROKEN": "Bas Londres",
    "PDH_SWEPT": "PDH", "PDH_BROKEN": "PDH", "PDL_SWEPT": "PDL", "PDL_BROKEN": "PDL",
    "FVG_BEAR_REVERSAL": "FVG baissière de retournement", "FVG_BULL_REVERSAL": "FVG haussière de retournement",
}
market_events = deque(maxlen=200)
market_events_version = 0

def _finite(v):
    n = _parse_num(v)
    return n if n is not None and math.isfinite(n) else None

def _clean_market_event(symbol, data):
    """Événement nettoyé (dict) ou None s'il est inconnu / illisible."""
    ev = str(data.get("event", ""))
    if ev not in EVENEMENTS_MARCHE or not re.fullmatch(r"[A-Z0-9._:-]{1,20}", symbol or ""):
        return None
    bar_time = data.get("bar_time")
    bar_time = bar_time if isinstance(bar_time, int) and not isinstance(bar_time, bool) and bar_time > 0 else None
    out = {
        "type": "event", "symbol": symbol, "event": ev, "label": EVENEMENTS_MARCHE[ev],
        "kind": "FVG" if ev.startswith("FVG_") else ev.rsplit("_", 1)[1],
        "level": _finite(data.get("level")), "fvg_top": _finite(data.get("fvg_top")), "fvg_bot": _finite(data.get("fvg_bot")),
        "current_price": _finite(data.get("current_price")), "bar_time": bar_time, "tf": _tf_propre(data.get("tf")),
        "time": datetime.utcnow().isoformat(),
    }
    if ev.startswith("FVG_") and (out["fvg_top"] is None or out["fvg_bot"] is None):
        return None
    if not ev.startswith("FVG_") and out["level"] is None:
        return None
    return out

# Réglages d'affichage du tableau de bord (taille du portefeuille simulé, risque max par trade), gardés côté serveur : ils
# suivent l'utilisateur d'un navigateur / appareil / adresse à l'autre (le navigateur seul les oublie quand l'adresse change,
# p. ex. tunnel Cloudflare). Nombres finis entre 0 et 1e9 uniquement ; aucune autre clé acceptée.
REGLAGES_CLES = ("portfolio", "risk")
REGLAGES_MAX = 1e9
reglages: dict = {}
_reglages_charges = False

def _reglage_valide(v):
    if isinstance(v, bool):
        return None
    n = _finite(v)
    return n if n is not None and 0 <= n <= REGLAGES_MAX else None

def _charger_reglages():
    """Lit les réglages en base une seule fois. False si la lecture a échoué (on n'écrase alors rien)."""
    global _reglages_charges
    if _reglages_charges:
        return True
    stocke = storage.load_state("reglages", "reglages.json")
    if stocke is storage.FAILED:
        return False
    for cle in REGLAGES_CLES:
        n = _reglage_valide((stocke or {}).get(cle)) if isinstance(stocke, dict) else None
        if n is not None:
            reglages[cle] = n
    _reglages_charges = True
    return True

@app.get("/api/reglages")
async def get_reglages():
    _charger_reglages()
    return JSONResponse(content=reglages, headers={"Cache-Control": "no-store"})

@app.post("/api/reglages")
async def set_reglages(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "JSON invalide"})
    if not isinstance(data, dict):
        return JSONResponse(status_code=400, content={"error": "objet attendu"})
    propres = {}
    for cle in REGLAGES_CLES:
        if cle in data:
            n = _reglage_valide(data[cle])
            if n is None:
                return JSONResponse(status_code=400, content={"error": f"valeur invalide pour « {cle} »"})
            propres[cle] = n
    if not propres:
        return JSONResponse(status_code=400, content={"error": "aucun réglage reconnu"})
    if not _charger_reglages():
        return JSONResponse(status_code=503, content={"error": "réglages non lus en base : rien n'a été écrit"})
    avant = dict(reglages)
    reglages.update(propres)
    if not storage.save_state("reglages", "reglages.json", reglages):
        reglages.clear()
        reglages.update(avant)
        return JSONResponse(status_code=503, content={"error": "écriture en base impossible"})
    return JSONResponse(content=reglages)

@app.get("/api/events")
async def get_market_events():
    return JSONResponse(content=list(market_events), headers={"X-Events-Version": str(market_events_version)})

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
    # Derrière le proxy Render, l'adresse réelle est la première de X-Forwarded-For.
    fwd = request.headers.get("x-forwarded-for", "")
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "?")

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

    _sync_storage()
    symbol_recu = data.get("symbol", "UNKNOWN").upper()
    symbol = _symbole_canonique(symbol_recu)
    data["symbol"] = symbol
    status = data.get("status", "INFO")
    direction = data.get("direction", "NONE")
    _reprendre_position_sous_alias(symbol_recu, symbol)

    if status == "EVENT":
        global market_events_version
        event = _clean_market_event(symbol, data)
        if event is None:
            return JSONResponse(status_code=400, content={"error": "événement de marché invalide"})
        doublon = any(e["symbol"] == event["symbol"] and e["event"] == event["event"] and event["bar_time"] is not None
                      and e["bar_time"] == event["bar_time"] for e in market_events)
        if not doublon:
            market_events.append(event)
            market_events_version += 1
            print(f"📡 [{symbol}] Événement de marché : {event['label']} ({event['kind']})")
            await manager.broadcast(json.dumps(event))
        return {"status": "ok", "event": event["event"], "duplicate": doublon}

    # Moteur d'Auto-Correction si nouveau trade d'entrée
    if direction in ("BUY", "SELL"):
        tuning = _compute_autotune_rules()
        current_sess = _session_label_now()
        cand_key = (symbol, status, current_sess, data.get("pd_zone", "--"))
        penalized_reason = tuning["penalized_map"].get(cand_key)
        if penalized_reason:
            data["auto_filtered"] = True
            data["auto_reason"] = penalized_reason
            print(f"🛡️ [{symbol}] Signal auto-filtré par règle d'auto-tuner : {penalized_reason}")
        else:
            data["auto_filtered"] = False
            data["auto_reason"] = None

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