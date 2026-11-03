import requests

DISCORD_API = "https://discord.com/api/v10"


def new_requests(messages: list[dict], owner_id: str) -> list[dict]:
    valid = [
        m for m in messages
        if m["author"]["id"] == owner_id and not m["author"].get("bot")
        and (m.get("content") or m.get("attachments"))
    ]
    return valid[::-1]


def fetch_messages(after: str | None, limit: int = 50) -> list[dict]:
    from config import DISCORD_BOT_TOKEN, DISCORD_COMPTA_CHANNEL_ID

    params = {"limit": limit}
    if after:
        params["after"] = after
    r = requests.get(
        f"{DISCORD_API}/channels/{DISCORD_COMPTA_CHANNEL_ID}/messages",
        headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
        params=params,
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def latest_message_id() -> str | None:
    messages = fetch_messages(None, limit=1)
    return messages[0]["id"] if messages else None


MAX_ATTACHMENT = 10 * 1024 * 1024


def download_attachments(message: dict) -> dict[str, bytes]:
    out = {}
    for a in message.get("attachments", []):
        url = a.get("url", "")
        if not url.startswith("https://cdn.discordapp.com/") or a.get("size", 0) > MAX_ATTACHMENT:
            continue
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        out[a["filename"]] = r.content
    return out
