import os
import sqlite3
from config import DB_PATH


def _query(sql: str, params: tuple = ()) -> list[dict]:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def init_db() -> None:
    _query(
        "CREATE TABLE IF NOT EXISTS reminders ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "texte TEXT NOT NULL, "
        "echeance TEXT NOT NULL, "
        "statut TEXT NOT NULL DEFAULT 'en_attente')"
    )
    _query(
        "CREATE TABLE IF NOT EXISTS agenda ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "texte TEXT NOT NULL, "
        "date_heure TEXT NOT NULL)"
    )


def add_reminder(texte: str, echeance: str) -> None:
    _query("INSERT INTO reminders (texte, echeance) VALUES (?, ?)", (texte, echeance))


def list_pending_reminders() -> list[dict]:
    return _query(
        "SELECT id, texte, echeance FROM reminders WHERE statut = 'en_attente' ORDER BY echeance"
    )


def due_reminders(now: str) -> list[dict]:
    return _query(
        "SELECT id, texte FROM reminders WHERE statut = 'en_attente' AND echeance <= ?", (now,)
    )


def mark_sent(reminder_id: int) -> None:
    _query("UPDATE reminders SET statut = 'envoye' WHERE id = ?", (reminder_id,))


def add_agenda_item(texte: str, date_heure: str) -> None:
    _query("INSERT INTO agenda (texte, date_heure) VALUES (?, ?)", (texte, date_heure))
