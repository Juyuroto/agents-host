import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Variable d'environnement manquante : {name}")
    return value


ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
DISCORD_COMPTA_WEBHOOK_URL = _require("DISCORD_COMPTA_WEBHOOK_URL")
DISCORD_BOT_TOKEN = _require("DISCORD_BOT_TOKEN")
DISCORD_COMPTA_CHANNEL_ID = _require("DISCORD_COMPTA_CHANNEL_ID")
DISCORD_OWNER_ID = _require("DISCORD_OWNER_ID")
COMPTA_DIR = os.environ.get("COMPTA_DIR", "/app/data")
COMPTA_WEB_USER = _require("COMPTA_WEB_USER")
COMPTA_WEB_PASSWORD = _require("COMPTA_WEB_PASSWORD")
