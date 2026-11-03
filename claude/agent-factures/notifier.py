import logging
import requests
from config import DISCORD_FACTURES_WEBHOOK_URL

log = logging.getLogger("agent-factures")

MAX_DISCORD_LEN = 1900


def notify_discord(demande: str, reponse: str) -> None:
    content = f"**Demande de facture**\n{demande}\n\n**Réponse**\n{reponse}"
    content = content[:MAX_DISCORD_LEN]

    try:
        r = requests.post(DISCORD_FACTURES_WEBHOOK_URL, json={"content": content}, timeout=10)
        r.raise_for_status()
    except requests.RequestException:
        log.exception("Échec de l'envoi de la notification Discord")
