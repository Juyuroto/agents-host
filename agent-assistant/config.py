import os
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Variable d'environnement manquante : {name}")
    return value


DISCORD_BOT_TOKEN = _require("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(_require("DISCORD_CHANNEL_ID"))
ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
DB_PATH = str(Path(__file__).parent / "data" / "assistant.db")
TIMEZONE = ZoneInfo("Europe/Paris")
