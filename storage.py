"""Persistance du journal de trading et des positions ouvertes.

- Si la variable d'environnement DATABASE_URL est définie (Render + Neon Postgres) : tout est
  stocké dans Postgres, qui survit aux redéploiements et redémarrages Render (le disque de
  l'offre gratuite Render est effacé à chaque fois).
- Sinon (développement local) : fichiers JSON à côté du code, comme avant.

Une erreur d'écriture est journalisée mais ne fait jamais échouer le webhook : l'état reste en
mémoire et la prochaine écriture réussie des positions le rattrape.
"""
import json
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOURNAL_FILE = os.path.join(BASE_DIR, "journal_history.json")
POSITIONS_FILE = os.path.join(BASE_DIR, "positions_state.json")

BACKEND = "postgres" if DATABASE_URL else "fichiers"

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
    if BACKEND == "postgres":
        _exec("CREATE TABLE IF NOT EXISTS journal_rows (id BIGSERIAL PRIMARY KEY, row JSONB NOT NULL)")
        _exec("CREATE TABLE IF NOT EXISTS app_state (key TEXT PRIMARY KEY, value JSONB NOT NULL)")


def load_journal(limit):
    """Les `limit` dernières lignes du journal, de la plus ancienne à la plus récente."""
    try:
        if BACKEND == "postgres":
            rows = _exec("SELECT row FROM journal_rows ORDER BY id DESC LIMIT %s", (limit,), fetch=True)
            return [r[0] for r in reversed(rows)]
        with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)[-limit:]
    except FileNotFoundError:
        return []  # premier démarrage en local — normal
    except Exception as e:
        print(f"⚠️ Lecture du journal impossible ({BACKEND}) : {e}")
        return []


def append_journal_row(row, current_journal):
    """Ajoute une ligne. En Postgres, l'historique complet est conservé (la mémoire du serveur
    reste plafonnée) ; en fichiers, on réécrit la liste courante déjà plafonnée."""
    try:
        if BACKEND == "postgres":
            from psycopg.types.json import Jsonb
            _exec("INSERT INTO journal_rows (row) VALUES (%s)", (Jsonb(row),))
        else:
            with open(JOURNAL_FILE, "w", encoding="utf-8") as f:
                json.dump(current_journal, f)
    except Exception as e:
        print(f"⚠️ Écriture du journal impossible ({BACKEND}) : {e}")


def load_positions():
    try:
        if BACKEND == "postgres":
            rows = _exec("SELECT value FROM app_state WHERE key = 'open_positions'", fetch=True)
            return rows[0][0] if rows else {}
        with open(POSITIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"⚠️ Lecture des positions impossible ({BACKEND}) : {e}")
        return {}


def load_state(key, filename):
    """Valeur JSON persistée sous `key` (Postgres) ou dans `filename` (fichiers) ; None si absente."""
    try:
        if BACKEND == "postgres":
            rows = _exec("SELECT value FROM app_state WHERE key = %s", (key,), fetch=True)
            return rows[0][0] if rows else None
        with open(os.path.join(BASE_DIR, filename), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"⚠️ Lecture de « {key} » impossible ({BACKEND}) : {e}")
        return None


def save_state(key, filename, value):
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
    except Exception as e:
        print(f"⚠️ Écriture de « {key} » impossible ({BACKEND}) : {e}")


def save_positions(positions):
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
    except Exception as e:
        print(f"⚠️ Écriture des positions impossible ({BACKEND}) : {e}")
