import uuid
from datetime import datetime, timedelta, timezone

import caldav
from config import APPLE_ID, APPLE_APP_PASSWORD, TIMEZONE

CALDAV_URL = "https://caldav.icloud.com"
ICAL_FORMAT = "%Y%m%dT%H%M%SZ"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _ical(texte: str, debut: datetime) -> str:
    fin = debut + timedelta(hours=1)
    now = datetime.now(timezone.utc)
    return "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//agent-assistant//FR",
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}@agent-assistant",
        f"DTSTAMP:{now.strftime(ICAL_FORMAT)}",
        f"DTSTART:{debut.strftime(ICAL_FORMAT)}",
        f"DTEND:{fin.strftime(ICAL_FORMAT)}",
        f"SUMMARY:{_escape(texte)}",
        "END:VEVENT",
        "END:VCALENDAR",
    ])


def _calendar():
    client = caldav.DAVClient(url=CALDAV_URL, username=APPLE_ID, password=APPLE_APP_PASSWORD)
    return client.principal().calendars()[0]


def add_event(texte: str, debut_utc: str) -> None:
    debut = datetime.fromisoformat(debut_utc).astimezone(timezone.utc)
    _calendar().save_event(_ical(texte, debut))


def list_events(debut_utc: str, fin_utc: str) -> list[dict]:
    debut = datetime.fromisoformat(debut_utc).astimezone(timezone.utc)
    fin = datetime.fromisoformat(fin_utc).astimezone(timezone.utc)
    events = []
    for event in _calendar().date_search(start=debut, end=fin, expand=True):
        composant = event.icalendar_component
        events.append({
            "uid": str(composant["uid"]),
            "texte": str(composant.get("summary", "")),
            "debut": composant["dtstart"].dt.astimezone(TIMEZONE).isoformat(timespec="minutes"),
        })
    return events


def delete_event(uid: str) -> None:
    _calendar().event_by_uid(uid).delete()
