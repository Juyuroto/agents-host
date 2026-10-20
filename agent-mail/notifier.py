import logging
import requests
from config import DISCORD_MAIL_WEBHOOK_URL

log = logging.getLogger("agent-mail")

MAX_DISCORD_LEN = 1900


def notify_discord(sender: str, subject: str, summary: str) -> None:
    content = f"**Nouveau mail** de `{sender}`\n**Sujet :** {subject}\n\n{summary}"
    content = content[:MAX_DISCORD_LEN]

    try:
        r = requests.post(DISCORD_MAIL_WEBHOOK_URL, json={"content": content}, timeout=10)
        r.raise_for_status()
    except requests.RequestException:
        log.exception("Échec de l'envoi de la notification Discord")