import logging
import requests
from config import DISCORD_PROSPECTS_WEBHOOK_URL

log = logging.getLogger("agent-prospects")

MAX_DISCORD_LEN = 1900


def _split(content: str) -> list[str]:
    chunks = []
    while len(content) > MAX_DISCORD_LEN:
        cut = content.rfind("\n", 0, MAX_DISCORD_LEN)
        if cut <= 0:
            cut = MAX_DISCORD_LEN
        chunks.append(content[:cut])
        content = content[cut:].lstrip("\n")
    if content:
        chunks.append(content)
    return chunks


def notify_discord(content: str) -> None:
    for chunk in _split(content):
        try:
            r = requests.post(DISCORD_PROSPECTS_WEBHOOK_URL, json={"content": chunk}, timeout=10)
            r.raise_for_status()
        except requests.RequestException:
            log.exception("Échec de l'envoi de la notification Discord")
