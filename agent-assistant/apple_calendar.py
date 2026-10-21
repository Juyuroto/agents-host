import uuid
from datetime import datetime, timedelta, timezone

import caldav
from config import APPLE_ID, APPLE_APP_PASSWORD

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


def add_event(texte: str, debut_utc: str) -> None:
    debut = datetime.fromisoformat(debut_utc).astimezone(timezone.utc)
    client = caldav.DAVClient(url=CALDAV_URL, username=APPLE_ID, password=APPLE_APP_PASSWORD)
    calendar = client.principal().calendars()[0]
    calendar.save_event(_ical(texte, debut))
