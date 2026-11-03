import asyncio
import logging

import storage
from bot import client
from config import DISCORD_BOT_TOKEN
from scheduler import run_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


async def main() -> None:
    storage.init_db()
    await asyncio.gather(client.start(DISCORD_BOT_TOKEN), run_scheduler(client))


if __name__ == "__main__":
    asyncio.run(main())
