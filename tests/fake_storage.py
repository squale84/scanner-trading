"""Faux module `storage` en mémoire : remplace le vrai avant l'import de server.py, pour que les tests
n'écrivent ni dans Neon ni dans les fichiers JSON du dépôt. Même interface et mêmes compteurs d'échec."""
import json
import sys
import types


def install():
    m = types.ModuleType("storage")
    m.FAILED = object()
    m.BACKEND = "fake"
    m.STATUS = {"backend": "fake", "loaded": False, "last_read_error": None, "healthy": True,
                "write_failures": 0, "last_error": None, "last_error_at": None, "last_write_ok_at": None}
    m.JOURNAL = []
    m.STATE = {}
    m.fail_writes = False  # bascule pour simuler une base en panne

    def _copy(v):
        return json.loads(json.dumps(v))

    def _fail(what):
        m.STATUS["healthy"] = False
        m.STATUS["write_failures"] += 1
        m.STATUS["last_error"] = f"{what} : panne simulée"
        return False

    def _ok():
        m.STATUS["healthy"] = True
        return True

    m.init = lambda: True
    m.load_journal = lambda limit: _copy(m.JOURNAL[-limit:])
    m.load_positions = lambda: _copy(m.STATE.get("open_positions", {}))
    m.load_state = lambda key, filename: _copy(m.STATE.get(key))

    def append_journal_row(row, current_journal):
        if m.fail_writes:
            return _fail("du journal")
        m.JOURNAL.append(_copy(row))
        return _ok()

    def save_state(key, filename, value):
        if m.fail_writes:
            return _fail(f"de « {key} »")
        m.STATE[key] = _copy(value)
        return _ok()

    def save_positions(positions):
        if m.fail_writes:
            return _fail("des positions")
        m.STATE["open_positions"] = _copy(positions)
        return _ok()

    m.append_journal_row = append_journal_row
    m.save_state = save_state
    m.save_positions = save_positions

    def blocked_write(what):
        m.STATUS["healthy"] = False
        m.STATUS["write_failures"] += 1
        return False

    m.blocked_write = blocked_write
    m.deferred_write = blocked_write
    sys.modules["storage"] = m
    return m
