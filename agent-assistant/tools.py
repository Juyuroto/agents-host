import json
import logging
from datetime import datetime, timezone

import storage
from config import TIMEZONE

log = logging.getLogger("agent-assistant")

TOOLS = [
    {
        "name": "set_reminder",
        "description": "Crée un rappel, posté sur Discord à l'échéance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "texte": {"type": "string"},
                "echeance": {
                    "type": "string",
                    "description": "Date et heure ISO 8601, ex. 2026-10-21T14:00:00 (heure de Paris si sans fuseau)",
                },
            },
            "required": ["texte", "echeance"],
        },
    },
    {
        "name": "add_agenda_item",
        "description": "Ajoute un élément à l'emploi du temps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "texte": {"type": "string"},
                "date_heure": {
                    "type": "string",
                    "description": "Date et heure ISO 8601, ex. 2026-10-21T14:00:00 (heure de Paris si sans fuseau)",
                },
            },
            "required": ["texte", "date_heure"],
        },
    },
    {
        "name": "list_reminders",
        "description": "Liste les rappels en attente.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _to_utc(value: str) -> str:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TIMEZONE)
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def execute(name: str, args: dict) -> str:
    try:
        if name == "set_reminder":
            storage.add_reminder(args["texte"], _to_utc(args["echeance"]))
            return "Rappel enregistré."
        if name == "add_agenda_item":
            storage.add_agenda_item(args["texte"], _to_utc(args["date_heure"]))
            return "Ajouté à l'agenda."
        if name == "list_reminders":
            rows = storage.list_pending_reminders()
            if not rows:
                return "Aucun rappel en attente."
            return json.dumps(
                [
                    {
                        "texte": r["texte"],
                        "echeance": datetime.fromisoformat(r["echeance"]).astimezone(TIMEZONE).isoformat(timespec="minutes"),
                    }
                    for r in rows
                ],
                ensure_ascii=False,
            )
        return f"Outil inconnu : {name}"
    except Exception as e:
        log.exception("Erreur dans l'outil %s", name)
        return f"Erreur : {e}"
