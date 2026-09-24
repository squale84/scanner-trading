"""Persistance du journal de trading et des positions ouvertes.

- Si la variable d'environnement DATABASE_URL est définie (Render + Neon Postgres) : tout est
  stocké dans Postgres, qui survit aux redéploiements et redémarrages Render (le disque de
  l'offre gratuite Render est effacé à chaque fois).
- Sinon (développement local) : fichiers JSON à côté du code, comme avant.

Chaque écriture renvoie True / False et met à jour STATUS (état de santé exposé par /health et
affiché par le dashboard). Il n'existe PAS de file de réessai durable : un événement dont
l'écriture a échoué n'existe qu'en mémoire du serveur et est perdu au prochain redémarrage — il
est donc compté comme « non sauvegardé », jamais présenté comme persisté.
"""
import json
import os
import time

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOURNAL_FILE = os.path.join(BASE_DIR, "journal_history.json")
POSITIONS_FILE = os.path.join(BASE_DIR, "positions_state.json")

BACKEND = "postgres" if DATABASE_URL else "fichiers"

# Valeur renvoyée par les lectures en cas d'échec (base injoignable) : distincte d'un état vide.
# Permet à server.py de savoir que l'état distant est INCONNU et qu'il ne doit pas l'écraser.
FAILED = object()

# État de santé de la persistance (lu par server.py : /health, réponse du webhook, dashboard).
STATUS = {
    "backend": BACKEND,
    "loaded": False,          # True quand l'état initial (journal, positions, dernières alertes) a été lu
    "last_read_error": None,
    "healthy": True,          # False dès qu'une écriture échoue, True à la prochaine écriture réussie
    "write_failures": 0,      # nombre total d'écritures échouées depuis le démarrage du serveur
    "last_error": None,
    "last_error_at": None,
    "last_write_ok_at": None,
}


def _write_ok():
    STATUS["healthy"] = True
    STATUS["last_write_ok_at"] = time.time()
    return True


def _read_failed(what, e):
    STATUS["healthy"] = False
    STATUS["last_read_error"] = f"{what} : {type(e).__name__}: {e}"[:300]
    STATUS["last_error"] = STATUS["last_read_error"]
    STATUS["last_error_at"] = time.time()
    print(f"❌ Lecture {what} impossible ({BACKEND}) : {e}")
    return FAILED


def blocked_write(what):
    """Écriture volontairement NON faite : l'état distant n'a pas pu être chargé, l'écraser avec
    l'état partiel en mémoire détruirait des données. Comptée comme un échec (jamais « persisté »)."""
    STATUS["healthy"] = False
    STATUS["write_failures"] += 1
    STATUS["last_error"] = f"écriture {what} bloquée : état en base pas encore chargé (protection anti-écrasement)"
    STATUS["last_error_at"] = time.time()
    print(f"⛔ {STATUS['last_error']}")
    return False


def deferred_write(what):
    """Écriture reportée : des lignes précédentes attendent encore d'être réécrites (ordre conservé).
    Comptée comme un échec tant qu'elle n'est pas réellement faite."""
    STATUS["healthy"] = False
    STATUS["write_failures"] += 1
    STATUS["last_error"] = f"écriture {what} reportée : des lignes précédentes attendent d'être réécrites"
    STATUS["last_error_at"] = time.time()
    return False


def _write_failed(what, e):
    STATUS["healthy"] = False
    STATUS["write_failures"] += 1
    STATUS["last_error"] = f"{what} : {type(e).__name__}: {e}"[:300]
    STATUS["last_error_at"] = time.time()
    print(f"❌ Écriture {what} impossible ({BACKEND}) : {e}")
    return False

_conn = None


def _connect():
    global _conn
    import psycopg  # importé seulement si Postgres est utilisé
    if _conn is None or _conn.closed:
        _conn = psycopg.connect(DATABASE_URL, autocommit=True, connect_timeout=10)
    return _conn


def _exec(sql, params=(), fetch=False):
    """Exécute une requête ; une connexion coupée (Neon suspend la base après inactivité) est
    rouverte une fois avant d'abandonner."""
    global _conn
    import psycopg
    for attempt in (1, 2):
        try:
            with _connect().cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall() if fetch else None
        except psycopg.OperationalError:
            _conn = None
            if attempt == 2:
                raise


def init():
    """Crée les tables si besoin. Renvoie True/False (base injoignable au démarrage : False)."""
    try:
        if BACKEND == "postgres":
            _exec("CREATE TABLE IF NOT EXISTS journal_rows (id BIGSERIAL PRIMARY KEY, row JSONB NOT NULL)")
            _exec("CREATE TABLE IF NOT EXISTS app_state (key TEXT PRIMARY KEY, value JSONB NOT NULL)")
        return True
    except Exception as e:
        _read_failed("(initialisation)", e)
        return False


def load_journal(limit):
    """Les `limit` dernières lignes du journal, de la plus ancienne à la plus récente (FAILED si erreur)."""
    try:
        if BACKEND == "postgres":
            rows = _exec("SELECT row FROM journal_rows ORDER BY id DESC LIMIT %s", (limit,), fetch=True)
            return [r[0] for r in reversed(rows)]
        with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)[-limit:]
    except FileNotFoundError:
        return []  # premier démarrage en local — normal
    except Exception as e:
        return _read_failed("du journal", e)


def append_journal_row(row, current_journal):
    """Ajoute une ligne. En Postgres, l'historique complet est conservé (la mémoire du serveur
    reste plafonnée) ; en fichiers, on réécrit la liste courante déjà plafonnée. Renvoie True/False."""
    try:
        if BACKEND == "postgres":
            from psycopg.types.json import Jsonb
            _exec("INSERT INTO journal_rows (row) VALUES (%s)", (Jsonb(row),))
        else:
            with open(JOURNAL_FILE, "w", encoding="utf-8") as f:
                json.dump(current_journal, f)
        return _write_ok()
    except Exception as e:
        return _write_failed("du journal", e)


def load_positions():
    """Positions ouvertes ({} si aucune, FAILED si erreur)."""
    try:
        if BACKEND == "postgres":
            rows = _exec("SELECT value FROM app_state WHERE key = 'open_positions'", fetch=True)
            return rows[0][0] if rows else {}
        with open(POSITIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        return _read_failed("des positions", e)


def load_state(key, filename):
    """Valeur JSON persistée sous `key` (Postgres) ou dans `filename` (fichiers) ; None si absente,
    FAILED si la lecture a échoué."""
    try:
        if BACKEND == "postgres":
            rows = _exec("SELECT value FROM app_state WHERE key = %s", (key,), fetch=True)
            return rows[0][0] if rows else None
        with open(os.path.join(BASE_DIR, filename), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        return _read_failed(f"de « {key} »", e)


def save_state(key, filename, value):
    """Enregistre une valeur JSON sous `key`. Renvoie True/False."""
    try:
        if BACKEND == "postgres":
            from psycopg.types.json import Jsonb
            _exec(
                "INSERT INTO app_state (key, value) VALUES (%s, %s) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                (key, Jsonb(value)),
            )
        else:
            with open(os.path.join(BASE_DIR, filename), "w", encoding="utf-8") as f:
                json.dump(value, f)
        return _write_ok()
    except Exception as e:
        return _write_failed(f"de « {key} »", e)


def save_positions(positions):
    """Enregistre les positions ouvertes. Renvoie True/False."""
    try:
        if BACKEND == "postgres":
            from psycopg.types.json import Jsonb
            _exec(
                "INSERT INTO app_state (key, value) VALUES ('open_positions', %s) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                (Jsonb(positions),),
            )
        else:
            with open(POSITIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(positions, f)
        return _write_ok()
    except Exception as e:
        return _write_failed("des positions", e)
