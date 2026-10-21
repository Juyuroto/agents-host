import json
import logging
from datetime import datetime, timezone

import apple_calendar
import storage
from config import TIMEZONE

log = logging.getLogger("agent-assistant")

TOOLS = [
    {
        "name": "set_reminder",
        "description": "Crée un rappel, posté sur Discord à l'échéance. Pour « tous les lundis », donne l'échéance du prochain lundi et recurrence hebdomadaire.",
        "input_schema": {
            "type": "object",
            "properties": {
                "texte": {"type": "string"},
                "echeance": {
                    "type": "string",
                    "description": "Date et heure ISO 8601, ex. 2026-10-21T14:00:00 (heure de Paris si sans fuseau)",
                },
                "recurrence": {
                    "type": "string",
                    "enum": list(storage.RECURRENCES),
                    "description": "Optionnel : répétition du rappel",
                },
            },
            "required": ["texte", "echeance"],
        },
    },
    {
        "name": "list_reminders",
        "description": "Liste les rappels en attente, avec leur identifiant.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "cancel_reminder",
        "description": "Annule un rappel en attente à partir de son identifiant.",
        "input_schema": {
            "type": "object",
            "properties": {"id": {"type": "integer"}},
            "required": ["id"],
        },
    },
    {
        "name": "update_reminder",
        "description": "Modifie le texte et/ou l'échéance d'un rappel en attente à partir de son identifiant.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "texte": {"type": "string"},
                "echeance": {
                    "type": "string",
                    "description": "Date et heure ISO 8601 (heure de Paris si sans fuseau)",
                },
            },
            "required": ["id"],
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
        "name": "add_note",
        "description": "Enregistre une note rapide.",
        "input_schema": {
            "type": "object",
            "properties": {"texte": {"type": "string"}},
            "required": ["texte"],
        },
    },
    {
        "name": "search_notes",
        "description": "Cherche les notes contenant un mot.",
        "input_schema": {
            "type": "object",
            "properties": {"mot": {"type": "string"}},
            "required": ["mot"],
        },
    },
]


def _to_utc(value: str) -> str:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TIMEZONE)
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def execute(name: str, args: dict) -> str:
    try:
        if name == "set_reminder":
            recurrence = args.get("recurrence")
            if recurrence is not None and recurrence not in storage.RECURRENCES:
                return f"Récurrence inconnue : {recurrence}"
            storage.add_reminder(args["texte"], _to_utc(args["echeance"]), recurrence)
            return "Rappel enregistré."
        if name == "list_reminders":
            rows = storage.list_pending_reminders()
            if not rows:
                return "Aucun rappel en attente."
            return json.dumps(
                [
                    {
                        "id": r["id"],
                        "texte": r["texte"],
                        "echeance": datetime.fromisoformat(r["echeance"]).astimezone(TIMEZONE).isoformat(timespec="minutes"),
                        "recurrence": r["recurrence"],
                    }
                    for r in rows
                ],
                ensure_ascii=False,
            )
        if name == "cancel_reminder":
            if storage.cancel_reminder(int(args["id"])):
                return "Rappel annulé."
            return "Rappel introuvable ou déjà envoyé."
        if name == "update_reminder":
            echeance = _to_utc(args["echeance"]) if "echeance" in args else None
            if storage.update_reminder(int(args["id"]), args.get("texte"), echeance):
                return "Rappel modifié."
            return "Rappel introuvable ou déjà envoyé."
        if name == "add_agenda_item":
            debut = _to_utc(args["date_heure"])
            storage.add_agenda_item(args["texte"], debut)
            try:
                apple_calendar.add_event(args["texte"], debut)
            except Exception:
                log.exception("Échec de l'envoi vers Apple Agenda")
                return "Ajouté à la base, mais échec de l'envoi vers Apple Agenda."
            return "Ajouté à l'agenda et à Apple Agenda."
        if name == "add_note":
            storage.add_note(args["texte"], _now_utc())
            return "Note enregistrée."
        if name == "search_notes":
            rows = storage.search_notes(args["mot"])
            if not rows:
                return "Aucune note trouvée."
            return json.dumps(
                [{"texte": r["texte"], "date": r["cree_le"]} for r in rows],
                ensure_ascii=False,
            )
        return f"Outil inconnu : {name}"
    except Exception as e:
        log.exception("Erreur dans l'outil %s", name)
        return f"Erreur : {e}"
