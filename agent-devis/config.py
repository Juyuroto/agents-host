import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Variable d'environnement manquante : {name}")
    return value


ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
ABBY_MCP_URL = _require("ABBY_MCP_URL")
ABBY_MCP_TOKEN = _require("ABBY_MCP_TOKEN")
KNOWLEDGE_DIR = str(Path(__file__).parent / "knowledge")
DISCORD_DEVIS_WEBHOOK_URL = _require("DISCORD_DEVIS_WEBHOOK_URL")
DISCORD_BOT_TOKEN = _require("DISCORD_BOT_TOKEN")
DISCORD_DEVIS_CHANNEL_ID = _require("DISCORD_DEVIS_CHANNEL_ID")
DISCORD_OWNER_ID = _require("DISCORD_OWNER_ID")