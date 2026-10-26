import requests

DISCORD_API = "https://discord.com/api/v10"


def new_requests(messages: list[dict], owner_id: str) -> list[dict]:
    valid = [
        m for m in messages
        if m["author"]["id"] == owner_id and not m["author"].get("bot") and m.get("content")
    ]
    return valid[::-1]


def fetch_messages(after: str | None, limit: int = 50) -> list[dict]:
    from config import DISCORD_BOT_TOKEN, DISCORD_GITHUB_CHANNEL_ID

    params = {"limit": limit}
    if after:
        params["after"] = after
    r = requests.get(
        f"{DISCORD_API}/channels/{DISCORD_GITHUB_CHANNEL_ID}/messages",
        headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
        params=params,
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def latest_message_id() -> str | None:
    messages = fetch_messages(None, limit=1)
    return messages[0]["id"] if messages else None
