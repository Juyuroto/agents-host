import uuid
from datetime import datetime, timedelta, timezone

import caldav
import requests
from requests.auth import HTTPBasicAuth
from config import APPLE_ID, APPLE_APP_PASSWORD, TIMEZONE

CALDAV_URL = "https://caldav.icloud.com"
ICAL_FORMAT = "%Y%m%dT%H%M%SZ"
RRULE_FREQ = {"quotidien": "DAILY", "hebdomadaire": "WEEKLY"}


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _ical(texte: str, debut: datetime, recurrence: str | None = None) -> str:
    fin = debut + timedelta(hours=1)
    now = datetime.now(timezone.utc)
    lignes = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//agent-assistant//FR",
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}@agent-assistant",
        f"DTSTAMP:{now.strftime(ICAL_FORMAT)}",
        f"DTSTART:{debut.strftime(ICAL_FORMAT)}",
        f"DTEND:{fin.strftime(ICAL_FORMAT)}",
        f"SUMMARY:{_escape(texte)}",
    ]
    if recurrence is not None:
        lignes.append(f"RRULE:FREQ={RRULE_FREQ[recurrence]}")
    lignes += ["END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(lignes)


def _client() -> caldav.DAVClient:
    return caldav.DAVClient(url=CALDAV_URL, username=APPLE_ID, password=APPLE_APP_PASSWORD)


def _calendar():
    return _client().principal().calendars()[0]


def add_event(texte: str, debut_utc: str, recurrence: str | None = None) -> None:
    debut = datetime.fromisoformat(debut_utc).astimezone(timezone.utc)
    _calendar().save_event(_ical(texte, debut, recurrence))


def list_events(debut_utc: str, fin_utc: str) -> list[dict]:
    debut = datetime.fromisoformat(debut_utc).astimezone(timezone.utc)
    fin = datetime.fromisoformat(fin_utc).astimezone(timezone.utc)
    events = []
    for event in _calendar().date_search(start=debut, end=fin):
        composant = event.icalendar_component
        events.append({
            "uid": str(composant["uid"]),
            "url": str(event.url),
            "texte": str(composant.get("summary", "")),
            "debut": composant["dtstart"].dt.astimezone(TIMEZONE).isoformat(timespec="minutes"),
        })
    return events


def update_event(url: str, texte: str | None, debut_utc: str | None) -> None:
    auth = HTTPBasicAuth(APPLE_ID, APPLE_APP_PASSWORD)
    r = requests.get(url, auth=auth, timeout=15)
    r.raise_for_status()
    lignes = r.text.replace("\r\n ", "").replace("\n ", "").replace("\r\n", "\n").split("\n")
    debut = datetime.fromisoformat(debut_utc).astimezone(timezone.utc) if debut_utc else None
    sortie = []
    for ligne in lignes:
        if texte is not None and ligne.startswith("SUMMARY"):
            ligne = f"SUMMARY:{_escape(texte)}"
        if debut is not None and ligne.startswith(("DTSTART", "DTEND")):
            continue
        if debut is not None and ligne == "END:VEVENT":
            sortie += [
                f"DTSTART:{debut.strftime(ICAL_FORMAT)}",
                f"DTEND:{(debut + timedelta(hours=1)).strftime(ICAL_FORMAT)}",
            ]
        if ligne:
            sortie.append(ligne)
    r = requests.put(
        url,
        data="\r\n".join(sortie).encode("utf-8"),
        auth=auth,
        headers={"Content-Type": "text/calendar; charset=utf-8"},
        timeout=15,
    )
    r.raise_for_status()


def delete_event(url: str) -> None:
    r = requests.delete(url, auth=HTTPBasicAuth(APPLE_ID, APPLE_APP_PASSWORD), timeout=15)
    r.raise_for_status()
