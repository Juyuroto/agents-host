import asyncio
import logging

import requests

from classifier import build_facture
from config import DISCORD_OWNER_ID
from discord_inbox import fetch_messages, latest_message_id, new_requests
from notifier import notify_discord

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("agent-factures")

POLL_SECONDS = 10


async def process_request(request: str) -> None:
    log.info("Nouvelle demande de facture")
    reponse = await build_facture(request)
    notify_discord(request, reponse)


async def run() -> None:
    last_id = latest_message_id()
    log.info("En écoute sur le salon")
    while True:
        try:
            messages = fetch_messages(last_id)
        except requests.RequestException:
            log.exception("Échec de la lecture du salon Discord")
            await asyncio.sleep(POLL_SECONDS)
            continue
        for demande in new_requests(messages, DISCORD_OWNER_ID):
            await process_request(demande["content"])
        if messages:
            last_id = max((m["id"] for m in messages), key=int)
        await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    asyncio.run(run())
