import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Variable d'environnement manquante : {name}")
    return value


GITHUB_TOKEN = _require("GITHUB_TOKEN")
ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
DISCORD_GITHUB_WEBHOOK_URL = _require("DISCORD_GITHUB_WEBHOOK_URL")
