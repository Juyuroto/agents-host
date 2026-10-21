import asyncio
import logging
from datetime import datetime, timezone

import storage
from config import DISCORD_CHANNEL_ID

log = logging.getLogger("agent-assistant")


async def run_scheduler(client) -> None:
    await client.wait_until_ready()
    while True:
        try:
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            channel = client.get_channel(DISCORD_CHANNEL_ID)
            for rappel in storage.due_reminders(now):
                try:
                    await channel.send(f"Rappel : {rappel['texte']}")
                    storage.mark_sent(rappel["id"])
                except Exception:
                    log.exception("Échec de l'envoi du rappel %s", rappel["id"])
        except Exception:
            log.exception("Erreur dans le planificateur")
        await asyncio.sleep(60)
