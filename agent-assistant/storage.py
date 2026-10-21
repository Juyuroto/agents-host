import os
import sqlite3
from datetime import datetime, timedelta
from config import DB_PATH

DELAIS_RELANCE = [timedelta(minutes=10), timedelta(minutes=30), timedelta(hours=2)]


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
    _ensure_column("reminders", "relances", "INTEGER NOT NULL DEFAULT 0")


def add_reminder(texte: str, echeance: str) -> None:
    _query("INSERT INTO reminders (texte, echeance) VALUES (?, ?)", (texte, echeance))


def list_pending_reminders() -> list[dict]:
    return _query(
        "SELECT id, texte, echeance, relances FROM reminders WHERE statut = 'en_attente' ORDER BY echeance"
    )


def due_reminders(now: str) -> list[dict]:
    return _query(
        "SELECT id, texte FROM reminders WHERE statut = 'en_attente' AND echeance <= ?", (now,)
    )


def mark_sent(reminder_id: int, now: str) -> None:
    relances = _query("SELECT relances FROM reminders WHERE id = ?", (reminder_id,))[0]["relances"] + 1
    delai = DELAIS_RELANCE[min(relances - 1, len(DELAIS_RELANCE) - 1)]
    prochaine = datetime.fromisoformat(now) + delai
    _query(
        "UPDATE reminders SET echeance = ?, relances = ? WHERE id = ?",
        (prochaine.isoformat(timespec="seconds"), relances, reminder_id),
    )


def complete_reminder(reminder_id: int) -> bool:
    if not _query("SELECT id FROM reminders WHERE id = ? AND statut = 'en_attente'", (reminder_id,)):
        return False
    _query("UPDATE reminders SET statut = 'fait' WHERE id = ?", (reminder_id,))
    return True
