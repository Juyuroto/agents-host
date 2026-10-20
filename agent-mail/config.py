import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Variable d'environnement manquante : {name}")
    return value


IMAP_SERVER = _require("IMAP_SERVER")
IMAP_USER = _require("IMAP_USER")
IMAP_PASSWORD = _require("IMAP_PASSWORD")
DISCORD_MAIL_WEBHOOK_URL = _require("DISCORD_MAIL_WEBHOOK_URL")
ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")