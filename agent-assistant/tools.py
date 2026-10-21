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
        "description": "Crée un rappel. Il est posté sur Discord à l'échéance, puis relancé (10 min, 30 min, 2 h…) tant que l'utilisateur n'a pas dit « fait N ».",
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
        "name": "list_reminders",
        "description": "Liste les rappels en attente, avec leur identifiant.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "mark_reminder_done",
        "description": "Marque un rappel comme fait : il ne sera plus envoyé ni relancé. À utiliser quand l'utilisateur écrit « fait N ».",
        "input_schema": {
            "type": "object",
            "properties": {"id": {"type": "integer"}},
            "required": ["id"],
        },
    },
    {
        "name": "add_agenda_item",
        "description": "Ajoute un événement d'une heure à l'agenda Apple. Pour « tous les lundis », donne le prochain lundi et recurrence hebdomadaire.",
        "input_schema": {
            "type": "object",
            "properties": {
                "texte": {"type": "string"},
                "date_heure": {
                    "type": "string",
                    "description": "Date et heure ISO 8601, ex. 2026-10-21T14:00:00 (heure de Paris si sans fuseau)",
                },
                "recurrence": {
                    "type": "string",
                    "enum": list(apple_calendar.RRULE_FREQ),
                    "description": "Optionnel : répétition de l'événement",
                },
            },
            "required": ["texte", "date_heure"],
        },
    },
    {
        "name": "update_agenda_item",
        "description": "Modifie le texte et/ou la date d'un événement de l'agenda Apple à partir de son url (obtenue avec list_agenda_items).",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "texte": {"type": "string"},
                "date_heure": {
                    "type": "string",
                    "description": "Date et heure ISO 8601 (heure de Paris si sans fuseau)",
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "list_agenda_items",
        "description": "Liste les événements de l'agenda Apple entre deux dates. Renvoie leur url, nécessaire pour les modifier ou les supprimer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "debut": {"type": "string", "description": "Date et heure ISO 8601 de début (heure de Paris si sans fuseau)"},
                "fin": {"type": "string", "description": "Date et heure ISO 8601 de fin (heure de Paris si sans fuseau)"},
            },
            "required": ["debut", "fin"],
        },
    },
    {
        "name": "delete_agenda_item",
        "description": "Supprime un événement de l'agenda Apple à partir de son url (obtenue avec list_agenda_items).",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
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
                        "relances": r["relances"],
                    }
                    for r in rows
                ],
                ensure_ascii=False,
            )
        if name == "mark_reminder_done":
            if storage.complete_reminder(int(args["id"])):
                return "Rappel marqué comme fait."
            return "Rappel introuvable ou déjà fait."
        if name == "add_agenda_item":
            recurrence = args.get("recurrence")
            if recurrence is not None and recurrence not in apple_calendar.RRULE_FREQ:
                return f"Récurrence inconnue : {recurrence}"
            apple_calendar.add_event(args["texte"], _to_utc(args["date_heure"]), recurrence)
            return "Ajouté à l'agenda Apple."
        if name == "update_agenda_item":
            date_heure = _to_utc(args["date_heure"]) if "date_heure" in args else None
            apple_calendar.update_event(args["url"], args.get("texte"), date_heure)
            return "Événement modifié."
        if name == "list_agenda_items":
            events = apple_calendar.list_events(_to_utc(args["debut"]), _to_utc(args["fin"]))
            if not events:
                return "Aucun événement sur cette période."
            return json.dumps(events, ensure_ascii=False)
        if name == "delete_agenda_item":
            apple_calendar.delete_event(args["url"])
            return "Événement supprimé."
        return f"Outil inconnu : {name}"
    except Exception as e:
        log.exception("Erreur dans l'outil %s", name)
        return f"Erreur : {e}"
