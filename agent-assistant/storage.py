import os
import sqlite3
from datetime import datetime, timedelta
from config import DB_PATH

RECURRENCES = {"quotidien": timedelta(days=1), "hebdomadaire": timedelta(weeks=1)}


def _query(sql: str, params: tuple = ()) -> list[dict]:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def _ensure_column(table: str, column: str, definition: str) -> None:
    columns = [row["name"] for row in _query(f"PRAGMA table_info({table})")]
    if column not in columns:
        _query(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db() -> None:
    _query(
        "CREATE TABLE IF NOT EXISTS reminders ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "texte TEXT NOT NULL, "
        "echeance TEXT NOT NULL, "
        "statut TEXT NOT NULL DEFAULT 'en_attente')"
    )
    _ensure_column("reminders", "recurrence", "TEXT")
    _query(
        "CREATE TABLE IF NOT EXISTS agenda ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "texte TEXT NOT NULL, "
        "date_heure TEXT NOT NULL)"
    )
    _query(
        "CREATE TABLE IF NOT EXISTS notes ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "texte TEXT NOT NULL, "
        "cree_le TEXT NOT NULL)"
    )


def add_reminder(texte: str, echeance: str, recurrence: str | None = None) -> None:
    _query(
        "INSERT INTO reminders (texte, echeance, recurrence) VALUES (?, ?, ?)",
        (texte, echeance, recurrence),
    )


def list_pending_reminders() -> list[dict]:
    return _query(
        "SELECT id, texte, echeance, recurrence FROM reminders WHERE statut = 'en_attente' ORDER BY echeance"
    )


def due_reminders(now: str) -> list[dict]:
    return _query(
        "SELECT id, texte FROM reminders WHERE statut = 'en_attente' AND echeance <= ?", (now,)
    )


def mark_sent(reminder_id: int, now: str) -> None:
    row = _query("SELECT echeance, recurrence FROM reminders WHERE id = ?", (reminder_id,))[0]
    if row["recurrence"] is None:
        _query("UPDATE reminders SET statut = 'envoye' WHERE id = ?", (reminder_id,))
        return
    delta = RECURRENCES[row["recurrence"]]
    echeance = datetime.fromisoformat(row["echeance"])
    now_dt = datetime.fromisoformat(now)
    while echeance <= now_dt:
        echeance += delta
    _query(
        "UPDATE reminders SET echeance = ? WHERE id = ?",
        (echeance.isoformat(timespec="seconds"), reminder_id),
    )


def cancel_reminder(reminder_id: int) -> bool:
    if not _query("SELECT id FROM reminders WHERE id = ? AND statut = 'en_attente'", (reminder_id,)):
        return False
    _query("UPDATE reminders SET statut = 'annule' WHERE id = ?", (reminder_id,))
    return True


def update_reminder(reminder_id: int, texte: str | None = None, echeance: str | None = None) -> bool:
    if not _query("SELECT id FROM reminders WHERE id = ? AND statut = 'en_attente'", (reminder_id,)):
        return False
    if texte is not None:
        _query("UPDATE reminders SET texte = ? WHERE id = ?", (texte, reminder_id))
    if echeance is not None:
        _query("UPDATE reminders SET echeance = ? WHERE id = ?", (echeance, reminder_id))
    return True


def add_agenda_item(texte: str, date_heure: str) -> None:
    _query("INSERT INTO agenda (texte, date_heure) VALUES (?, ?)", (texte, date_heure))


def add_note(texte: str, cree_le: str) -> None:
    _query("INSERT INTO notes (texte, cree_le) VALUES (?, ?)", (texte, cree_le))


def search_notes(mot: str) -> list[dict]:
    return _query(
        "SELECT texte, cree_le FROM notes WHERE texte LIKE ? ORDER BY cree_le DESC",
        (f"%{mot}%",),
    )
