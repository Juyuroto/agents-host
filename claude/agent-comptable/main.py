import asyncio
import logging
import threading

import requests

import compta
import web
from classifier import handle_request
from config import DISCORD_OWNER_ID
from discord_inbox import download_attachments, fetch_messages, latest_message_id, new_requests
from notifier import notify_discord

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("agent-comptable")

POLL_SECONDS = 10


async def process_request(message: dict) -> None:
    log.info("Nouvelle demande compta")
    request = message.get("content", "")
    try:
        attachments = download_attachments(message)
    except requests.RequestException:
        log.exception("Échec du téléchargement des pièces jointes")
        attachments = {}
    reponse = await handle_request(request, attachments)
    notify_discord(request, reponse)


async def run() -> None:
    compta.init()
    last_id = latest_message_id()
    log.info("En écoute sur le salon")
    while True:
        try:
            messages = fetch_messages(last_id)
        except requests.RequestException:
            log.exception("Échec de la lecture du salon Discord")
            await asyncio.sleep(POLL_SECONDS)
            continue
        for message in new_requests(messages, DISCORD_OWNER_ID):
            await process_request(message)
        if messages:
            last_id = max((m["id"] for m in messages), key=int)
        await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    threading.Thread(target=web.serve, daemon=True).start()
    asyncio.run(run())
