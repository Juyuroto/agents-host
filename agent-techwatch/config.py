import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Variable d'environnement manquante : {name}")
    return value


ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
DISCORD_TECHWATCH_WEBHOOK_URL = _require("DISCORD_TECHWATCH_WEBHOOK_URL")
